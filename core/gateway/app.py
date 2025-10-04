import os, json, hashlib, time, subprocess, asyncio
from typing import Optional, List, Dict, Any

import httpx
from fastapi import FastAPI, Header, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis as redislib
from sentence_transformers import SentenceTransformer
import psutil
import docker

# ---- Config ----
PORT = int(os.getenv("GATEWAY_PORT", "8081"))
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "http://vllm:8000/v1")
OPENAI_KEY  = os.getenv("OPENAI_API_KEY", "abs-local")
REGISTRY_PATH = os.getenv("REGISTRY_PATH", "registry.json")

# Redis cache (optional but recommended)
rds = None
try:
    rds = redislib.from_url(REDIS_URL)
    rds.ping()
except Exception:
    rds = None

with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
    REG = json.load(f)

app = FastAPI(title="ABS Hub Gateway")

# Add CORS middleware for Admin UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTTP = httpx.AsyncClient(timeout=60)

# Docker client for container management
docker_client = None
try:
    # Try using APIClient directly
    docker_client = docker.APIClient(base_url='unix:///var/run/docker.sock')
    # Test the connection
    docker_client.ping()
    print("Docker client initialized successfully")
except Exception as e:
    print(f"Docker client initialization failed: {e}")
    try:
        # Fallback to DockerClient
        docker_client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
        docker_client.ping()
        print("Docker client initialized successfully (fallback)")
    except Exception as e2:
        print(f"Docker client fallback also failed: {e2}")
        # Try subprocess approach as last resort
        try:
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("Docker subprocess access available")
                docker_client = "subprocess"  # Use subprocess instead of docker library
            else:
                docker_client = None
        except Exception as e3:
            print(f"Docker subprocess also failed: {e3}")
            docker_client = None

# Global model cache for Hugging Face models
MODEL_CACHE = {}

# ---- Schemas ----
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatReq(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = None

class EmbedReq(BaseModel):
    input: List[str]
    override_model: Optional[str] = None

# ---- Helpers ----
async def detect_provider() -> str:
    # Prefer OpenAI/vLLM if reachable
    try:
        r = await HTTP.get(f"{OPENAI_BASE.rstrip('/')}/models")
        if r.is_success:
            return "openai"
    except Exception:
        pass
    try:
        r = await HTTP.get(f"{OLLAMA_BASE.rstrip('/')}/api/tags")
        if r.is_success:
            return "ollama"
    except Exception:
        pass
    raise HTTPException(503, "No LLM provider reachable")

def logical_to_provider_id(logical: str, provider: str) -> str:
    return REG.get("aliases", {}).get(logical, {}).get(provider, logical)

def pick_app_cfg(app_id: Optional[str]):
    dfl = REG.get("defaults", {})
    app_cfg = REG.get("apps", {}).get(app_id or "", {})
    return {**dfl, **app_cfg}

# ---- Discovery & Catalog ----
@app.get("/.well-known/abs-services")
async def services():
    return {
        "llm_openai": OPENAI_BASE,
        "llm_ollama": OLLAMA_BASE,
        "redis": REDIS_URL,
        "catalog": "/catalog"
    }

@app.get("/catalog")
async def catalog():
    return REG

# ---- Chat ----
@app.post("/v1/chat/completions")
async def chat(req: ChatReq, request: Request, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    t0 = time.time()
    cfg = pick_app_cfg(app_id)
    provider = cfg.get("provider", "auto")
    if provider == "auto":
        provider = await detect_provider()

    model_logical = req.model or cfg.get("chat_model", "contract-default")
    model = logical_to_provider_id(model_logical, provider)

    if provider == "openai":
        payload = {
            "model": model,
            "messages": [m.model_dump() for m in req.messages],
            "temperature": req.temperature,
            "max_tokens": req.max_tokens,
        }
        r = await HTTP.post(f"{OPENAI_BASE.rstrip('/')}/chat/completions",
                            headers={"Authorization": f"Bearer {OPENAI_KEY}"},
                            json=payload)
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        out = r.json()
    else:
        # Ollama chat → normalize to OpenAI-like response
        payload = {
            "model": model,
            "messages": [m.model_dump() for m in req.messages],
            "stream": False,
            "options": {"temperature": req.temperature}
        }
        r = await HTTP.post(f"{OLLAMA_BASE.rstrip('/')}/api/chat", json=payload)
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        data = r.json()
        text = data.get("message", {}).get("content", data.get("response", ""))
        out = {
            "id": "chatcmpl_abs",
            "object": "chat.completion",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}}],
            "usage": {
                "prompt_tokens": data.get("prompt_eval_count"),
                "completion_tokens": data.get("eval_count"),
                "total_tokens": None
            },
            "model": model,
            "provider": "ollama"
        }
    dt = time.time() - t0
    print(json.dumps({"event":"chat","app_id":app_id,"provider":provider,"model":model,"ms":int(dt*1000)}))
    return out

# ---- Embeddings ----
@app.post("/v1/embeddings")
async def embeddings(req: EmbedReq, request: Request, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    t0 = time.time()
    cfg = pick_app_cfg(app_id)
    provider = cfg.get("provider", "auto")
    if provider == "auto":
        provider = await detect_provider()

    logical = req.override_model or cfg.get("embed_model") or REG.get("defaults", {}).get("embed_model")
    model = logical_to_provider_id(logical, provider)

    # Cache key
    hasher = hashlib.sha256()
    for t in req.input:
        hasher.update(t.encode("utf-8"))
    key = f"emb:{app_id or 'unknown'}:{provider}:{model}:{hasher.hexdigest()}"

    if rds is not None:
        cached = rds.get(key)
        if cached:
            return json.loads(cached)

    if provider == "openai":
        r = await HTTP.post(f"{OPENAI_BASE.rstrip('/')}/embeddings",
                            headers={"Authorization": f"Bearer {OPENAI_KEY}"},
                            json={"model": model, "input": req.input})
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        out = r.json()
    elif provider == "huggingface":
        # Hugging Face: use sentence-transformers
        if model not in MODEL_CACHE:
            MODEL_CACHE[model] = SentenceTransformer(model)
        transformer = MODEL_CACHE[model]
        embeddings = transformer.encode(req.input)
        data = []
        for i, emb in enumerate(embeddings):
            data.append({"index": i, "embedding": emb.tolist()})
        out = {"data": data, "model": model, "object": "list"}
    else:
        # Ollama: call per text
        data = []
        for i, t in enumerate(req.input):
            r = await HTTP.post(f"{OLLAMA_BASE.rstrip('/')}/api/embeddings", json={"model": model, "prompt": t})
            if not r.is_success:
                raise HTTPException(r.status_code, r.text)
            emb = r.json()["embedding"]
            data.append({"index": i, "embedding": emb})
        out = {"data": data, "model": model, "object": "list"}

    if rds is not None:
        rds.setex(key, 86400, json.dumps(out))  # 1 day

    dt = time.time() - t0
    print(json.dumps({"event":"embed","app_id":app_id,"provider":provider,"model":model,"n":len(req.input),"ms":int(dt*1000)}))
    return out

# ---- Qdrant Collection Management ----
@app.put("/v1/collections/{collection_name}")
async def create_collection(collection_name: str, payload: dict, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """Create a collection for a specific embedding model"""
    try:
        cfg = pick_app_cfg(app_id)
        embed_model = cfg.get("embed_model") or REG.get("defaults", {}).get("embed_model")
        
        # Generate collection name based on embedding model
        model_collection = f"{embed_model}_vectors"
        
        # Route to Qdrant
        r = await HTTP.put(f"http://qdrant:6333/collections/{model_collection}", json=payload)
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        
        return r.json()
    except Exception as e:
        raise HTTPException(500, f"Error creating collection: {str(e)}")

@app.get("/v1/collections/{collection_name}")
async def get_collection_info(collection_name: str, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """Get collection information for a specific embedding model"""
    try:
        cfg = pick_app_cfg(app_id)
        embed_model = cfg.get("embed_model") or REG.get("defaults", {}).get("embed_model")
        
        # Generate collection name based on embedding model
        model_collection = f"{embed_model}_vectors"
        
        # Route to Qdrant
        r = await HTTP.get(f"http://qdrant:6333/collections/{model_collection}")
        
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        
        return r.json()
    except Exception as e:
        raise HTTPException(500, f"Error getting collection info: {str(e)}")

@app.put("/v1/collections/{collection_name}/points")
async def upsert_points(collection_name: str, payload: dict, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """Upsert points to the correct collection based on embedding model"""
    try:
        cfg = pick_app_cfg(app_id)
        embed_model = cfg.get("embed_model") or REG.get("defaults", {}).get("embed_model")
        
        # Generate collection name based on embedding model
        model_collection = f"{embed_model}_vectors"
        
        # Route to Qdrant
        r = await HTTP.put(f"http://qdrant:6333/collections/{model_collection}/points", json=payload)
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        
        return r.json()
    except Exception as e:
        raise HTTPException(500, f"Error upserting points: {str(e)}")

@app.post("/v1/collections/{collection_name}/points/search")
async def search_points(collection_name: str, payload: dict, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """Search points in the correct collection based on embedding model"""
    try:
        cfg = pick_app_cfg(app_id)
        embed_model = cfg.get("embed_model") or REG.get("defaults", {}).get("embed_model")
        
        # Generate collection name based on embedding model
        model_collection = f"{embed_model}_vectors"
        
        # Route to Qdrant
        r = await HTTP.post(f"http://qdrant:6333/collections/{model_collection}/points/search", json=payload)
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        
        return r.json()
    except Exception as e:
        raise HTTPException(500, f"Error searching points: {str(e)}")

def get_collection_name_for_model(embed_model: str) -> str:
    """Generate collection name based on embedding model"""
    # Clean model name for collection naming
    clean_name = embed_model.replace(":", "_").replace("/", "_").replace("-", "_").lower()
    return f"{clean_name}_vectors"

# ---- Admin API Endpoints ----

@app.get("/admin/system/metrics")
async def get_system_metrics():
    """Get real-time system metrics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Network I/O
        network = psutil.net_io_counters()
        
        return {
            "cpu": {
                "usage_percent": cpu_percent,
                "cores": psutil.cpu_count()
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "usage_percent": memory.percent
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "usage_percent": (disk.used / disk.total) * 100
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            },
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(500, f"Error getting system metrics: {str(e)}")

@app.get("/admin/services/status")
async def get_services_status():
    """Get status of all services"""
    services = {}
    
    # Check Ollama
    try:
        r = await HTTP.get(f"{OLLAMA_BASE.rstrip('/')}/api/tags")
        if r.is_success:
            models = r.json().get("models", [])
            services["ollama"] = {
                "status": "online",
                "models": [m.get("name", "") for m in models],
                "version": "unknown"
            }
        else:
            services["ollama"] = {"status": "offline", "error": r.text}
    except Exception as e:
        services["ollama"] = {"status": "offline", "error": str(e)}
    
    # Check Qdrant
    try:
        r = await HTTP.get("http://qdrant:6333/collections")
        if r.is_success:
            collections = r.json().get("result", {}).get("collections", [])
            services["qdrant"] = {
                "status": "online",
                "collections": [c.get("name", "") for c in collections],
                "version": "unknown"
            }
        else:
            services["qdrant"] = {"status": "offline", "error": r.text}
    except Exception as e:
        services["qdrant"] = {"status": "offline", "error": str(e)}
    
    # Check Redis
    try:
        if rds is not None:
            rds.ping()
            info = rds.info()
            services["redis"] = {
                "status": "online",
                "version": info.get("redis_version", "unknown"),
                "memory_used": info.get("used_memory_human", "unknown"),
                "keys": info.get("db0", {}).get("keys", 0)
            }
        else:
            services["redis"] = {"status": "offline", "error": "Redis client not initialized"}
    except Exception as e:
        services["redis"] = {"status": "offline", "error": str(e)}
    
    return services

@app.post("/admin/services/{service_name}/control")
async def control_service(service_name: str, action: str):
    """Start/stop services"""
    if not docker_client:
        raise HTTPException(500, "Docker client not available")
    
    try:
        # Map service names to container names
        container_map = {
            "ollama": "abs-ollama",
            "qdrant": "abs-qdrant", 
            "redis": "abs-redis",
            "hub-gateway": "abs-hub-gateway",
            "contract-reviewer": "abs-app-contract-reviewer-reviewer-1"
        }
        
        container_name = container_map.get(service_name)
        if not container_name:
            raise HTTPException(400, f"Unknown service: {service_name}")
        
        if docker_client == "subprocess":
            # Use subprocess to control containers
            cmd = ["docker", action, container_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                raise Exception(f"Docker command failed: {result.stderr}")
        else:
            # Use docker library
            container = docker_client.containers.get(container_name)
            
            if action == "start":
                container.start()
            elif action == "stop":
                container.stop()
            elif action == "restart":
                container.restart()
            else:
                raise HTTPException(400, f"Invalid action: {action}")
        
        return {"status": "success", "message": f"Service {service_name} {action}ed successfully"}
            
    except docker.errors.NotFound:
        raise HTTPException(404, f"Container not found for service: {service_name}")
    except Exception as e:
        raise HTTPException(500, f"Error controlling service: {str(e)}")

@app.post("/admin/models/{model_name}/load")
async def load_model(model_name: str):
    """Load a model in Ollama"""
    try:
        payload = {"name": model_name, "stream": False}
        r = await HTTP.post(f"{OLLAMA_BASE.rstrip('/')}/api/pull", json=payload)
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        
        return {"status": "loading", "model": model_name}
    except Exception as e:
        raise HTTPException(500, f"Error loading model: {str(e)}")

@app.delete("/admin/models/{model_name}")
async def unload_model(model_name: str):
    """Unload a model from Ollama"""
    try:
        payload = {"name": model_name}
        r = await HTTP.delete(f"{OLLAMA_BASE.rstrip('/')}/api/delete", json=payload)
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        
        return {"status": "unloaded", "model": model_name}
    except Exception as e:
        raise HTTPException(500, f"Error unloading model: {str(e)}")

@app.delete("/admin/collections/{collection_name}")
async def delete_collection(collection_name: str):
    """Delete a Qdrant collection"""
    try:
        r = await HTTP.delete(f"http://qdrant:6333/collections/{collection_name}")
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        
        return {"status": "deleted", "collection": collection_name}
    except Exception as e:
        raise HTTPException(500, f"Error deleting collection: {str(e)}")

@app.get("/admin/logs/{service_name}")
async def get_service_logs(service_name: str, lines: int = 100):
    """Get logs for a service"""
    if not docker_client:
        raise HTTPException(500, "Docker client not available")
    
    try:
        container_map = {
            "ollama": "abs-ollama",
            "qdrant": "abs-qdrant",
            "redis": "abs-redis", 
            "hub-gateway": "abs-hub-gateway",
            "contract-reviewer": "abs-app-contract-reviewer-reviewer-1"
        }
        
        container_name = container_map.get(service_name)
        if not container_name:
            raise HTTPException(400, f"Unknown service: {service_name}")
        
        container = docker_client.containers.get(container_name)
        logs = container.logs(tail=lines).decode('utf-8')
        
        return {"service": service_name, "logs": logs}
    except docker.errors.NotFound:
        raise HTTPException(404, f"Container not found for service: {service_name}")
    except Exception as e:
        raise HTTPException(500, f"Error getting logs: {str(e)}")

@app.websocket("/admin/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics"""
    await websocket.accept()
    
    try:
        while True:
            # Get current metrics
            metrics = await get_system_metrics()
            services = await get_services_status()
            
            data = {
                "type": "metrics",
                "system": metrics,
                "services": services,
                "timestamp": time.time()
            }
            
            await websocket.send_json(data)
            await asyncio.sleep(5)  # Update every 5 seconds
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()