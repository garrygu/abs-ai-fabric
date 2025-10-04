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
ONYX_BASE = os.getenv("ONYX_BASE_URL", "http://onyx:8000")
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

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup"""
    if AUTO_WAKE_SETTINGS["idle_sleep_enabled"]:
        await start_idle_monitor()
        print("ABS Hub Gateway started with idle sleep monitoring enabled")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop background tasks on application shutdown"""
    await stop_idle_monitor()
    print("ABS Hub Gateway shutdown - idle monitor stopped")

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

# Auto-wake settings and service registry
AUTO_WAKE_SETTINGS = {
    "enabled": True,
    "idle_timeout_minutes": 60,
    "model_keep_alive_hours": 2,
    "idle_sleep_enabled": True,
    "idle_check_interval_minutes": 5
}

# Service registry tracking desired vs actual state
SERVICE_REGISTRY = {
    "ollama": {"desired": "on", "actual": "unknown", "last_used": 0, "idle_sleep_enabled": True},
    "qdrant": {"desired": "on", "actual": "unknown", "last_used": 0, "idle_sleep_enabled": True},
    "redis": {"desired": "on", "actual": "unknown", "last_used": 0, "idle_sleep_enabled": False},  # Redis should stay running
    "onyx": {"desired": "on", "actual": "unknown", "last_used": 0, "idle_sleep_enabled": True}
}

# Model registry for tracking loaded models and their usage
MODEL_REGISTRY = {}  # Will track: {"model_name": {"last_used": timestamp, "keep_alive_until": timestamp}}

# Background task management
IDLE_MONITOR_TASK = None

# Container name mapping
CONTAINER_MAP = {
    "ollama": "abs-ollama",
    "qdrant": "abs-qdrant", 
    "redis": "abs-redis",
    "hub-gateway": "abs-hub-gateway",
    "onyx": "abs-onyx"
}

# Service dependencies - defines what services must be running before starting a service
SERVICE_DEPENDENCIES = {
    "ollama": [],  # Ollama has no dependencies
    "qdrant": [],  # Qdrant has no dependencies
    "redis": [],   # Redis has no dependencies
    "hub-gateway": ["redis"],  # Hub Gateway depends on Redis
    "onyx": ["redis", "qdrant"],  # Onyx depends on Redis and Qdrant
    # Future services can be added here
    "whisper": [],
    "minio": [],
    "parser": []
}

# Service startup order - defines the order services should be started
SERVICE_STARTUP_ORDER = ["redis", "qdrant", "ollama", "onyx", "hub-gateway"]

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

# ---- Auto-Wake Helpers ----
async def check_service_status(service_name: str) -> str:
    """Check if a service is running"""
    try:
        container_name = CONTAINER_MAP.get(service_name)
        if not container_name:
            return "unknown"
        
        if docker_client == "subprocess":
            result = subprocess.run(['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Status}}'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return "running" if "Up" in result.stdout else "stopped"
            return "stopped"
        else:
            container = docker_client.containers.get(container_name)
            return "running" if container.status == "running" else "stopped"
    except Exception:
        return "unknown"

async def start_service_with_dependencies(service_name: str) -> bool:
    """Start a service and all its dependencies in the correct order"""
    if not AUTO_WAKE_SETTINGS["enabled"]:
        return True
    
    # Get dependencies for this service
    dependencies = SERVICE_DEPENDENCIES.get(service_name, [])
    
    # Start dependencies first
    for dep in dependencies:
        dep_status = await check_service_status(dep)
        if dep_status != "running":
            print(f"Starting dependency {dep} for {service_name}...")
            if not await start_service(dep):
                print(f"Failed to start dependency {dep}")
                return False
            # Wait for dependency to be ready
            if not await wait_for_service_ready(dep):
                print(f"Dependency {dep} started but not ready")
                return False
    
    # Now start the main service
    return await start_service(service_name)

async def ensure_service_ready_with_dependencies(service_name: str) -> bool:
    """Ensure a service and all its dependencies are running and ready"""
    if not AUTO_WAKE_SETTINGS["enabled"]:
        return True
    
    # Update last used timestamp
    SERVICE_REGISTRY[service_name]["last_used"] = time.time()
    
    # Check current status
    current_status = await check_service_status(service_name)
    SERVICE_REGISTRY[service_name]["actual"] = current_status
    
    if current_status == "running":
        # Service is running, but check if dependencies are also running
        dependencies = SERVICE_DEPENDENCIES.get(service_name, [])
        for dep in dependencies:
            dep_status = await check_service_status(dep)
            if dep_status != "running":
                print(f"Dependency {dep} is not running, restarting {service_name}...")
                if not await start_service_with_dependencies(service_name):
                    return False
                break
        return True
    
    # Service is not running, try to start it with dependencies
    print(f"Auto-waking {service_name} with dependencies...")
    if await start_service_with_dependencies(service_name):
        # Wait for service to be ready
        if await wait_for_service_ready(service_name):
            SERVICE_REGISTRY[service_name]["actual"] = "running"
            print(f"Successfully auto-waked {service_name} with dependencies")
            return True
        else:
            print(f"Service {service_name} started but not ready")
            return False
    else:
        print(f"Failed to start {service_name} with dependencies")
        return False

async def start_service(service_name: str) -> bool:
    """Start a service container"""
    try:
        container_name = CONTAINER_MAP.get(service_name)
        if not container_name:
            return False
        
        if docker_client == "subprocess":
            cmd = ["docker", "start", container_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        else:
            container = docker_client.containers.get(container_name)
            container.start()
            return True
    except Exception as e:
        print(f"Error starting {service_name}: {e}")
        return False

async def wait_for_service_ready(service_name: str, timeout: int = 60) -> bool:
    """Wait for a service to be ready by checking its health endpoint"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            if service_name == "ollama":
                r = await HTTP.get(f"{OLLAMA_BASE.rstrip('/')}/api/tags", timeout=5)
                if r.is_success:
                    return True
            elif service_name == "qdrant":
                r = await HTTP.get("http://qdrant:6333/collections", timeout=5)
                if r.is_success:
                    return True
            elif service_name == "redis":
                if rds is not None:
                    rds.ping()
                    return True
        except Exception:
            pass
        
        await asyncio.sleep(2)
    
    return False

async def ensure_service_ready(service_name: str) -> bool:
    """Ensure a service is running and ready, auto-start if needed (with dependencies)"""
    return await ensure_service_ready_with_dependencies(service_name)

async def preload_model_if_needed(model_name: str, provider: str) -> bool:
    """Pre-load a model into VRAM if using Ollama"""
    if provider != "ollama":
        return True
    
    try:
        # Check if model is already loaded by making a test request
        test_payload = {
            "model": model_name,
            "prompt": "test",
            "stream": False,
            "options": {"keep_alive": f"{AUTO_WAKE_SETTINGS['model_keep_alive_hours']}h"}
        }
        r = await HTTP.post(f"{OLLAMA_BASE.rstrip('/')}/api/generate", json=test_payload, timeout=30)
        
        if r.is_success:
            # Track model usage and keep-alive
            current_time = time.time()
            keep_alive_until = current_time + (AUTO_WAKE_SETTINGS['model_keep_alive_hours'] * 3600)
            
            MODEL_REGISTRY[model_name] = {
                "last_used": current_time,
                "keep_alive_until": keep_alive_until,
                "provider": provider
            }
            print(f"Model {model_name} loaded and tracked for keep-alive until {keep_alive_until}")
        
        return r.is_success
    except Exception as e:
        print(f"Error pre-loading model {model_name}: {e}")
        return False

async def resolve_service_dependencies(required_services: List[str]) -> List[str]:
    """Resolve all dependencies for a list of required services"""
    resolved = set()
    to_resolve = set(required_services)
    
    while to_resolve:
        service = to_resolve.pop()
        if service in resolved:
            continue
            
        # Add dependencies
        dependencies = SERVICE_DEPENDENCIES.get(service, [])
        for dep in dependencies:
            if dep not in resolved:
                to_resolve.add(dep)
        
        resolved.add(service)
    
    # Return in startup order
    ordered_services = []
    for service in SERVICE_STARTUP_ORDER:
        if service in resolved:
            ordered_services.append(service)
    
    # Add any services not in the startup order
    for service in resolved:
        if service not in ordered_services:
            ordered_services.append(service)
    
    return ordered_services

async def ensure_multiple_services_ready(required_services: List[str]) -> bool:
    """Ensure multiple services and their dependencies are running"""
    if not AUTO_WAKE_SETTINGS["enabled"]:
        return True
    
    # Resolve all dependencies
    all_services = await resolve_service_dependencies(required_services)
    
    print(f"Resolved service dependencies: {all_services}")
    
    # Start services in dependency order
    for service in all_services:
        if not await ensure_service_ready_with_dependencies(service):
            print(f"Failed to ensure {service} is ready")
            return False
    
    return True

# ---- Idle Sleep Management ----
async def stop_service(service_name: str) -> bool:
    """Stop a service container"""
    try:
        container_name = CONTAINER_MAP.get(service_name)
        if not container_name:
            return False
        
        if docker_client == "subprocess":
            cmd = ["docker", "stop", container_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        else:
            container = docker_client.containers.get(container_name)
            container.stop()
            return True
    except Exception as e:
        print(f"Error stopping {service_name}: {e}")
        return False

async def unload_model(model_name: str) -> bool:
    """Unload a model from Ollama to free VRAM"""
    try:
        # Send a request to Ollama to unload the model
        payload = {"name": model_name}
        r = await HTTP.post(f"{OLLAMA_BASE.rstrip('/')}/api/generate", 
                           json={"model": model_name, "prompt": "", "stream": False}, 
                           timeout=10)
        # This will trigger model unloading after the request
        return True
    except Exception as e:
        print(f"Error unloading model {model_name}: {e}")
        return False

async def check_and_handle_idle_services():
    """Check for idle services and stop them if configured"""
    if not AUTO_WAKE_SETTINGS["idle_sleep_enabled"]:
        return
    
    current_time = time.time()
    idle_timeout_seconds = AUTO_WAKE_SETTINGS["idle_timeout_minutes"] * 60
    
    for service_name, service_info in SERVICE_REGISTRY.items():
        # Skip if idle sleep is disabled for this service
        if not service_info.get("idle_sleep_enabled", True):
            continue
        
        # Skip if service is desired to be on
        if service_info.get("desired") == "on":
            continue
        
        # Check if service has been idle too long
        last_used = service_info.get("last_used", 0)
        if last_used > 0 and (current_time - last_used) > idle_timeout_seconds:
            current_status = await check_service_status(service_name)
            if current_status == "running":
                print(f"Service {service_name} has been idle for {idle_timeout_seconds/60} minutes, stopping...")
                if await stop_service(service_name):
                    SERVICE_REGISTRY[service_name]["actual"] = "stopped"
                    print(f"Successfully stopped idle service {service_name}")
                else:
                    print(f"Failed to stop idle service {service_name}")

async def check_and_handle_idle_models():
    """Check for idle models and unload them if configured"""
    if not AUTO_WAKE_SETTINGS["idle_sleep_enabled"]:
        return
    
    current_time = time.time()
    model_keep_alive_seconds = AUTO_WAKE_SETTINGS["model_keep_alive_hours"] * 3600
    
    for model_name, model_info in MODEL_REGISTRY.items():
        keep_alive_until = model_info.get("keep_alive_until", 0)
        if keep_alive_until > 0 and current_time > keep_alive_until:
            print(f"Model {model_name} keep-alive expired, unloading...")
            if await unload_model(model_name):
                MODEL_REGISTRY[model_name]["keep_alive_until"] = 0
                print(f"Successfully unloaded idle model {model_name}")
            else:
                print(f"Failed to unload idle model {model_name}")

async def idle_monitor_task():
    """Background task to monitor and handle idle services and models"""
    while True:
        try:
            await check_and_handle_idle_services()
            await check_and_handle_idle_models()
            
            # Sleep for the configured interval
            sleep_seconds = AUTO_WAKE_SETTINGS["idle_check_interval_minutes"] * 60
            await asyncio.sleep(sleep_seconds)
        except Exception as e:
            print(f"Error in idle monitor task: {e}")
            await asyncio.sleep(60)  # Sleep for 1 minute on error

async def start_idle_monitor():
    """Start the idle monitor background task"""
    global IDLE_MONITOR_TASK
    if IDLE_MONITOR_TASK is None or IDLE_MONITOR_TASK.done():
        IDLE_MONITOR_TASK = asyncio.create_task(idle_monitor_task())
        print("Idle monitor task started")

async def stop_idle_monitor():
    """Stop the idle monitor background task"""
    global IDLE_MONITOR_TASK
    if IDLE_MONITOR_TASK and not IDLE_MONITOR_TASK.done():
        IDLE_MONITOR_TASK.cancel()
        try:
            await IDLE_MONITOR_TASK
        except asyncio.CancelledError:
            pass
        print("Idle monitor task stopped")

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
    
    # Auto-wake: Ensure required services are running
    if provider == "ollama":
        if not await ensure_service_ready("ollama"):
            raise HTTPException(503, "Ollama service unavailable and auto-wake failed")
        # Pre-load model if needed
        await preload_model_if_needed(model, provider)
    elif provider == "openai":
        # For OpenAI/vLLM, we might need different service management
        pass

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
    
    # Auto-wake: Ensure required services are running
    if provider == "ollama":
        if not await ensure_service_ready("ollama"):
            raise HTTPException(503, "Ollama service unavailable and auto-wake failed")
        # Pre-load embedding model if needed
        await preload_model_if_needed(model, provider)
    elif provider == "huggingface":
        # Hugging Face models are loaded locally, no service needed
        pass

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
        # Auto-wake: Ensure Qdrant is running
        if not await ensure_service_ready("qdrant"):
            raise HTTPException(503, "Qdrant service unavailable and auto-wake failed")
        
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
        # Auto-wake: Ensure Qdrant is running
        if not await ensure_service_ready("qdrant"):
            raise HTTPException(503, "Qdrant service unavailable and auto-wake failed")
        
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
        # Auto-wake: Ensure Qdrant is running
        if not await ensure_service_ready("qdrant"):
            raise HTTPException(503, "Qdrant service unavailable and auto-wake failed")
        
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
        # Auto-wake: Ensure Qdrant is running
        if not await ensure_service_ready("qdrant"):
            raise HTTPException(503, "Qdrant service unavailable and auto-wake failed")
        
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
        container_name = CONTAINER_MAP.get(service_name)
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
        
        # Update service registry
        SERVICE_REGISTRY[service_name]["actual"] = action if action == "start" else "stopped"
        
        return {"status": "success", "message": f"Service {service_name} {action}ed successfully"}
            
    except docker.errors.NotFound:
        raise HTTPException(404, f"Container not found for service: {service_name}")
    except Exception as e:
        raise HTTPException(500, f"Error controlling service: {str(e)}")

@app.get("/admin/settings")
async def get_settings():
    """Get auto-wake settings"""
    return {
        "autoWakeEnabled": AUTO_WAKE_SETTINGS["enabled"],
        "idleTimeout": AUTO_WAKE_SETTINGS["idle_timeout_minutes"],
        "modelKeepAlive": AUTO_WAKE_SETTINGS["model_keep_alive_hours"],
        "idleSleepEnabled": AUTO_WAKE_SETTINGS["idle_sleep_enabled"],
        "idleCheckInterval": AUTO_WAKE_SETTINGS["idle_check_interval_minutes"],
        "serviceRegistry": SERVICE_REGISTRY,
        "modelRegistry": MODEL_REGISTRY,
        "serviceDependencies": SERVICE_DEPENDENCIES,
        "startupOrder": SERVICE_STARTUP_ORDER
    }

@app.post("/admin/services/ensure-ready")
async def ensure_services_ready(required_services: List[str]):
    """Ensure multiple services and their dependencies are running"""
    try:
        success = await ensure_multiple_services_ready(required_services)
        if success:
            return {
                "status": "success", 
                "message": f"All required services are ready: {required_services}",
                "resolved_services": await resolve_service_dependencies(required_services)
            }
        else:
            raise HTTPException(503, "Failed to ensure all services are ready")
    except Exception as e:
        raise HTTPException(500, f"Error ensuring services ready: {str(e)}")

@app.get("/admin/services/dependencies")
async def get_service_dependencies():
    """Get service dependency information"""
    return {
        "dependencies": SERVICE_DEPENDENCIES,
        "startupOrder": SERVICE_STARTUP_ORDER,
        "containerMap": CONTAINER_MAP
    }

@app.post("/admin/settings")
async def update_settings(settings: dict):
    """Update auto-wake settings"""
    try:
        if "autoWakeEnabled" in settings:
            AUTO_WAKE_SETTINGS["enabled"] = bool(settings["autoWakeEnabled"])
        if "idleTimeout" in settings:
            AUTO_WAKE_SETTINGS["idle_timeout_minutes"] = int(settings["idleTimeout"])
        if "modelKeepAlive" in settings:
            AUTO_WAKE_SETTINGS["model_keep_alive_hours"] = float(settings["modelKeepAlive"])
        if "idleSleepEnabled" in settings:
            AUTO_WAKE_SETTINGS["idle_sleep_enabled"] = bool(settings["idleSleepEnabled"])
            # Start or stop idle monitor based on setting
            if AUTO_WAKE_SETTINGS["idle_sleep_enabled"]:
                await start_idle_monitor()
            else:
                await stop_idle_monitor()
        if "idleCheckInterval" in settings:
            AUTO_WAKE_SETTINGS["idle_check_interval_minutes"] = int(settings["idleCheckInterval"])
        
        return {"status": "success", "message": "Settings updated successfully"}
    except Exception as e:
        raise HTTPException(500, f"Error updating settings: {str(e)}")

@app.post("/admin/services/{service_name}/idle-sleep")
async def toggle_service_idle_sleep(service_name: str, enabled: bool):
    """Enable or disable idle sleep for a specific service"""
    try:
        if service_name not in SERVICE_REGISTRY:
            raise HTTPException(400, f"Unknown service: {service_name}")
        
        SERVICE_REGISTRY[service_name]["idle_sleep_enabled"] = enabled
        
        return {
            "status": "success", 
            "message": f"Idle sleep {'enabled' if enabled else 'disabled'} for {service_name}",
            "service": service_name,
            "idle_sleep_enabled": enabled
        }
    except Exception as e:
        raise HTTPException(500, f"Error updating service idle sleep: {str(e)}")

@app.post("/admin/models/{model_name}/unload")
async def force_unload_model(model_name: str):
    """Force unload a model from memory"""
    try:
        if await unload_model(model_name):
            # Remove from model registry
            if model_name in MODEL_REGISTRY:
                MODEL_REGISTRY[model_name]["keep_alive_until"] = 0
            
            return {"status": "unloaded", "model": model_name}
        else:
            raise HTTPException(500, f"Failed to unload model {model_name}")
    except Exception as e:
        raise HTTPException(500, f"Error unloading model: {str(e)}")

@app.get("/admin/idle-status")
async def get_idle_status():
    """Get current idle status of all services and models"""
    try:
        current_time = time.time()
        idle_timeout_seconds = AUTO_WAKE_SETTINGS["idle_timeout_minutes"] * 60
        model_keep_alive_seconds = AUTO_WAKE_SETTINGS["model_keep_alive_hours"] * 3600
        
        service_status = {}
        for service_name, service_info in SERVICE_REGISTRY.items():
            last_used = service_info.get("last_used", 0)
            idle_for_seconds = current_time - last_used if last_used > 0 else 0
            
            service_status[service_name] = {
                "last_used": last_used,
                "idle_for_minutes": idle_for_seconds / 60,
                "idle_sleep_enabled": service_info.get("idle_sleep_enabled", True),
                "desired": service_info.get("desired", "unknown"),
                "actual": service_info.get("actual", "unknown"),
                "will_sleep_in_minutes": max(0, (idle_timeout_seconds - idle_for_seconds) / 60) if service_info.get("idle_sleep_enabled", True) and service_info.get("desired") != "on" else None
            }
        
        model_status = {}
        for model_name, model_info in MODEL_REGISTRY.items():
            keep_alive_until = model_info.get("keep_alive_until", 0)
            time_until_unload = keep_alive_until - current_time if keep_alive_until > 0 else 0
            
            model_status[model_name] = {
                "last_used": model_info.get("last_used", 0),
                "keep_alive_until": keep_alive_until,
                "will_unload_in_minutes": max(0, time_until_unload / 60) if time_until_unload > 0 else 0,
                "provider": model_info.get("provider", "unknown")
            }
        
        return {
            "idle_sleep_enabled": AUTO_WAKE_SETTINGS["idle_sleep_enabled"],
            "idle_timeout_minutes": AUTO_WAKE_SETTINGS["idle_timeout_minutes"],
            "model_keep_alive_hours": AUTO_WAKE_SETTINGS["model_keep_alive_hours"],
            "services": service_status,
            "models": model_status,
            "monitor_task_running": IDLE_MONITOR_TASK is not None and not IDLE_MONITOR_TASK.done()
        }
    except Exception as e:
        raise HTTPException(500, f"Error getting idle status: {str(e)}")

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
        container_name = CONTAINER_MAP.get(service_name)
        if not container_name:
            raise HTTPException(400, f"Unknown service: {service_name}")
        
        container = docker_client.containers.get(container_name)
        logs = container.logs(tail=lines).decode('utf-8')
        
        return {"service": service_name, "logs": logs}
    except docker.errors.NotFound:
        raise HTTPException(404, f"Container not found for service: {service_name}")
    except Exception as e:
        raise HTTPException(500, f"Error getting logs: {str(e)}")

# ---- Onyx RAG/Agent Endpoints ----

@app.post("/v1/onyx/chat")
async def onyx_chat(req: ChatReq, request: Request, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """Chat with Onyx AI assistant"""
    try:
        # Auto-wake: Ensure Onyx is running
        if not await ensure_service_ready("onyx"):
            raise HTTPException(503, "Onyx service unavailable and auto-wake failed")
        
        # Prepare payload for Onyx
        payload = {
            "messages": [m.model_dump() for m in req.messages],
            "model": req.model,
            "temperature": req.temperature,
            "max_tokens": req.max_tokens,
            "app_id": app_id
        }
        
        # Route to Onyx
        r = await HTTP.post(f"{ONYX_BASE.rstrip('/')}/chat", json=payload)
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        
        return r.json()
    except Exception as e:
        raise HTTPException(500, f"Error with Onyx chat: {str(e)}")

@app.post("/v1/onyx/rag")
async def onyx_rag(request: Request, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """RAG query through Onyx"""
    try:
        # Auto-wake: Ensure Onyx is running
        if not await ensure_service_ready("onyx"):
            raise HTTPException(503, "Onyx service unavailable and auto-wake failed")
        
        # Get request body
        payload = await request.json()
        
        # Add app context
        payload["app_id"] = app_id
        
        # Route to Onyx RAG endpoint
        r = await HTTP.post(f"{ONYX_BASE.rstrip('/')}/rag", json=payload)
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        
        return r.json()
    except Exception as e:
        raise HTTPException(500, f"Error with Onyx RAG: {str(e)}")

@app.post("/v1/onyx/ingest")
async def onyx_ingest(request: Request, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """Ingest documents through Onyx"""
    try:
        # Auto-wake: Ensure Onyx is running
        if not await ensure_service_ready("onyx"):
            raise HTTPException(503, "Onyx service unavailable and auto-wake failed")
        
        # Get request body
        payload = await request.json()
        
        # Add app context
        payload["app_id"] = app_id
        
        # Route to Onyx ingest endpoint
        r = await HTTP.post(f"{ONYX_BASE.rstrip('/')}/ingest", json=payload)
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        
        return r.json()
    except Exception as e:
        raise HTTPException(500, f"Error with Onyx ingest: {str(e)}")

@app.get("/v1/onyx/agents")
async def list_onyx_agents(app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """List available Onyx agents"""
    try:
        # Auto-wake: Ensure Onyx is running
        if not await ensure_service_ready("onyx"):
            raise HTTPException(503, "Onyx service unavailable and auto-wake failed")
        
        # Route to Onyx agents endpoint
        r = await HTTP.get(f"{ONYX_BASE.rstrip('/')}/agents", params={"app_id": app_id})
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        
        return r.json()
    except Exception as e:
        raise HTTPException(500, f"Error listing Onyx agents: {str(e)}")

@app.post("/v1/onyx/agents/{agent_id}/execute")
async def execute_onyx_agent(agent_id: str, request: Request, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """Execute a specific Onyx agent"""
    try:
        # Auto-wake: Ensure Onyx is running
        if not await ensure_service_ready("onyx"):
            raise HTTPException(503, "Onyx service unavailable and auto-wake failed")
        
        # Get request body
        payload = await request.json()
        
        # Add app context
        payload["app_id"] = app_id
        
        # Route to Onyx agent execution endpoint
        r = await HTTP.post(f"{ONYX_BASE.rstrip('/')}/agents/{agent_id}/execute", json=payload)
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        
        return r.json()
    except Exception as e:
        raise HTTPException(500, f"Error executing Onyx agent: {str(e)}")

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