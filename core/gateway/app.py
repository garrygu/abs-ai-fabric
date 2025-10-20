import os, json, hashlib, time, subprocess, asyncio
from typing import Optional, List, Dict, Any

import httpx
from fastapi import FastAPI, Header, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
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
APPS_REGISTRY_PATH = os.getenv("APPS_REGISTRY_PATH", os.path.join("..", "abs-ai-hub", "apps-registry.json"))
CATALOG_PATH = os.getenv("CATALOG_PATH", os.path.join("catalog.json"))

# Redis cache (optional but recommended)
rds = None
try:
    rds = redislib.from_url(REDIS_URL)
    rds.ping()
except Exception:
    rds = None

with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
    REG = json.load(f)

# Best-effort load of Apps registry (for unified catalog)
APPS_REG: Dict[str, Any] = {}
try:
    with open(APPS_REGISTRY_PATH, "r", encoding="utf-8") as f:
        APPS_REG = json.load(f)
except Exception as e:
    # Not fatal; unified catalog will omit apps if missing
    APPS_REG = {}

# Load Catalog file (policies & broader assets)
CATALOG: Dict[str, Any] = {}
try:
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        CATALOG = json.load(f)
except Exception:
    CATALOG = {"version": "1.0", "assets": [], "tools": [], "datasets": [], "secrets": []}

app = FastAPI(title="ABS Hub Gateway")
# Enable CORS so the Hub UI (different port) can call POST/OPTIONS endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add CORS middleware for Admin UI and Onyx Suite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "http://localhost:3001", "http://localhost:8150"],
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
    "onyx": {"desired": "on", "actual": "unknown", "last_used": 0, "idle_sleep_enabled": True},
    "postgresql": {"desired": "on", "actual": "unknown", "last_used": 0, "idle_sleep_enabled": False}  # PostgreSQL should stay running
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
    "onyx": "abs-onyx",
    "postgresql": "document-hub-postgres"
}
 
# Supported default LLM models (logical names as seen by Ollama)
SUPPORTED_DEFAULT_MODELS = [
    "llama3.2:3b",
    "llama3.2:latest",
    "llama3:8b",
]

# Service dependencies - defines what services must be running before starting a service
SERVICE_DEPENDENCIES = {
    "ollama": [],  # Ollama has no dependencies
    "qdrant": [],  # Qdrant has no dependencies
    "redis": [],   # Redis has no dependencies
    "postgresql": [],  # PostgreSQL has no dependencies
    "hub-gateway": ["redis"],  # Hub Gateway depends on Redis
    "onyx": ["redis", "qdrant"],  # Onyx depends on Redis and Qdrant
    # Future services can be added here
    "whisper": [],
    "minio": [],
    "parser": []
}

# Service startup order - defines the order services should be started
SERVICE_STARTUP_ORDER = ["redis", "postgresql", "qdrant", "ollama", "onyx", "hub-gateway"]

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
    """Get app configuration from catalog first, then fallback to registry defaults"""
    # First try to get from catalog
    for asset in CATALOG.get("assets", []):
        if asset.get("class") == "app" and asset.get("id") == (app_id or ""):
            policy = asset.get("policy", {})
            defaults = policy.get("defaults", {})
            if defaults:
                return defaults
    
    # Fallback to global catalog defaults
    catalog_defaults = CATALOG.get("defaults", {})
    if catalog_defaults:
        return catalog_defaults
    
    # Last resort: registry defaults (for backward compatibility)
    return REG.get("defaults", {})

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
            elif service_name == "postgresql":
                # Check PostgreSQL health by attempting to connect
                try:
                    import psycopg2
                    conn = psycopg2.connect(
                        host='localhost',
                        port=5432,
                        database='document_hub',
                        user='hub_user',
                        password='secure_password',
                        connect_timeout=5
                    )
                    conn.close()
                    return True
                except Exception:
                    pass
        except Exception:
            pass
        
        await asyncio.sleep(2)
    
    return False

async def ensure_service_ready(service_name: str) -> bool:
    """Ensure a service is running and ready, auto-start if needed (with dependencies)"""
    return await ensure_service_ready_with_dependencies(service_name)

async def preload_model_if_needed(model_name: str, provider: str) -> bool:
    """Pre-load a model into VRAM if using Ollama. If model is not available, pull it first."""
    if provider != "ollama":
        return True
    
    try:
        # First check if model is available by trying to list it
        r_tags = await HTTP.get(f"{OLLAMA_BASE.rstrip('/')}/api/tags")
        available_models = []
        if r_tags.is_success:
            available_models = [m.get("name") for m in r_tags.json().get("models", []) if m.get("name")]
        
        # If model is not available, pull it first
        if model_name not in available_models:
            print(f"Model {model_name} not available, pulling from Ollama...")
            pull_payload = {"name": model_name, "stream": False}
            r_pull = await HTTP.post(f"{OLLAMA_BASE.rstrip('/')}/api/pull", json=pull_payload, timeout=300)
            if not r_pull.is_success:
                print(f"Failed to pull model {model_name}: {r_pull.text}")
                return False
            print(f"Successfully pulled model {model_name}")
        
        # Now try to load the model into VRAM
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
    print(f"DEBUG: unload_model called with model_name: {model_name}")
    try:
        # Try multiple approaches to unload the model
        # Normalize helper for X vs X:latest comparisons
        def _variants(name: str) -> set:
            bases = set()
            if not name:
                return bases
            bases.add(name)
            if name.endswith(":latest"):
                bases.add(name[:-7])
            else:
                bases.add(f"{name}:latest")
            return bases

        # Resolve to provider-specific alias if present (e.g., logical all-minilm -> ollama all-minilm:latest)
        aliases = (REG or {}).get("aliases", {}) if isinstance(REG, dict) else {}
        provider_map = aliases.get(model_name, {}) if isinstance(aliases, dict) else {}
        ollama_alias = provider_map.get("ollama", model_name)
        candidates = set()
        candidates |= _variants(model_name)
        candidates |= _variants(ollama_alias)

        # Approach 1: Set keep_alive to 0 with a minimal request (LLM)
        # Try both LLM and Embeddings unload across all variants
        success = False
        for candidate in list(candidates):
            try:
                payload = {"model": candidate, "prompt": "test", "stream": False, "options": {"keep_alive": 0}}
                r = await HTTP.post(f"{OLLAMA_BASE.rstrip('/')}/api/generate", json=payload, timeout=10)
            except Exception:
                r = None
        
        if r is not None and r.is_success:
            # Wait a moment for Ollama to process the unload
            await asyncio.sleep(3)
            
            # Check if model is actually unloaded
            ps_r = await HTTP.get(f"{OLLAMA_BASE.rstrip('/')}/api/ps")
            if ps_r.is_success:
                running_models = [m.get("name") for m in ps_r.json().get("models", [])]
                present = False
                for cand in candidates:
                    if cand in running_models:
                        present = True
                        break
                if not present:
                    print(f"Model {model_name} successfully unloaded using keep_alive=0")
                    return True
            
            # Approach 2: Try with keep_alive as "0s" (string format)
            print(f"Model {model_name} still running, trying alternative unload method...")
            last_r2 = None
            for candidate in list(candidates):
                try:
                    payload2 = {"model": candidate, "prompt": "test", "stream": False, "options": {"keep_alive": "0s"}}
                    last_r2 = await HTTP.post(f"{OLLAMA_BASE.rstrip('/')}/api/generate", json=payload2, timeout=10)
                except Exception:
                    last_r2 = None

            # Try embedding warm/unload path as well (always attempt once)
            for candidate in list(candidates):
                payload_e = {"model": candidate, "input": "warm", "options": {"keep_alive": 0}}
                try:
                    _ = await HTTP.post(f"{OLLAMA_BASE.rstrip('/')}/api/embeddings", json=payload_e, timeout=10)
                except Exception:
                    continue
            
            if last_r2 is not None and last_r2.is_success:
                await asyncio.sleep(3)
                ps_r2 = await HTTP.get(f"{OLLAMA_BASE.rstrip('/')}/api/ps")
                if ps_r2.is_success:
                    running_models2 = [m.get("name") for m in ps_r2.json().get("models", [])]
                    if not any(c in running_models2 for c in candidates):
                        print(f"Model {model_name} successfully unloaded using keep_alive='0s'")
                        return True
            
            # If still running, check when it will auto-unload and provide that info
            ps_r3 = await HTTP.get(f"{OLLAMA_BASE.rstrip('/')}/api/ps")
            if ps_r3.is_success:
                running_models3 = ps_r3.json().get("models", [])
                # Success if none of the variants remain
                if not any((m.get("name") in candidates) for m in running_models3):
                    return True
                for model in running_models3:
                    if model.get("name") in candidates:
                        expires_at = model.get("expires_at")
                        if expires_at:
                            # Calculate time until auto-unload
                            try:
                                from datetime import datetime
                                expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                                now_dt = datetime.now(expires_dt.tzinfo)
                                time_until_unload = expires_dt - now_dt
                                hours = int(time_until_unload.total_seconds() // 3600)
                                minutes = int((time_until_unload.total_seconds() % 3600) // 60)
                                print(f"Warning: Could not force unload model {model_name}. It will auto-unload in {hours}h {minutes}m")
                            except:
                                print(f"Warning: Could not force unload model {model_name}. It will auto-unload at {expires_at}")
                        else:
                            print(f"Warning: Could not unload model {model_name} - no expiration time available")
                        break
                else:
                    print(f"Warning: Could not unload model {model_name} - model not found in running list")
            return False
        
        return False
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
        "qdrant": "http://qdrant:6333",
        "onyx": "http://onyx:8000",
        "whisper-server": "http://whisper-server:8001",
        "catalog": "/catalog"
    }

def build_unified_catalog() -> Dict[str, Any]:
    """Aggregate models (REG) and applications (APPS_REG) into a unified catalog."""
    # Start from catalog file (authoritative for assets and policy)
    assets: List[Dict[str, Any]] = list((CATALOG or {}).get("assets", []))

    # Merge in Apps registry entries that are not present in catalog
    existing_ids = {a.get("id") for a in assets}
    apps = (APPS_REG or {}).get("applications", [])
    for app in apps:
        if app.get("id") not in existing_ids:
            assets.append({
                "id": app.get("id"),
                "class": "app",
                "name": app.get("name"),
                "version": None,
                "owner": None,
                "lifecycle": {"desired": "running", "actual": None},
                "policy": {},
                "health": {"url": (app.get("healthcheck") or {}).get("url")},
                "metadata": {
                    "category": app.get("category"),
                    "icon": app.get("icon"),
                    "path": app.get("path"),
                    "port": app.get("port"),
                }
            })

    # Models (logical aliases and defaults) - only add if not already in catalog
    aliases = (REG or {}).get("aliases", {})
    for logical, providers in aliases.items():
        if logical not in existing_ids:  # Only add if not already in catalog
            assets.append({
                "id": logical,
                "class": "model",
                "name": logical,
                "version": None,
                "owner": None,
                "policy": {},
                "health": {"status": "unknown"},
                "metadata": {"providers": providers}
            })

    # Services (from hardcoded registry map)
    for svc in SERVICE_REGISTRY.keys():
        assets.append({
            "id": svc,
            "class": "service",
            "name": svc,
            "version": None,
            "owner": None,
            "lifecycle": {
                "desired": SERVICE_REGISTRY[svc].get("desired"),
                "actual": SERVICE_REGISTRY[svc].get("actual")
            },
            "policy": {},
            "health": {"status": SERVICE_REGISTRY[svc].get("actual")},
            "metadata": {"container": CONTAINER_MAP.get(svc)}
        })

    return {
        "version": CATALOG.get("version", "1.0"),
        "defaults": CATALOG.get("defaults", {}),
        # Return current in-memory REG to reflect any runtime alias syncs
        "aliases": (REG or {}).get("aliases", {}),
        "assets": assets,
        "tools": CATALOG.get("tools", []),
        "datasets": CATALOG.get("datasets", []),
        "secrets": CATALOG.get("secrets", [])
    }

@app.get("/catalog")
async def catalog():
    return build_unified_catalog()

@app.get("/assets")
async def list_assets():
    return build_unified_catalog().get("assets", [])

# ---- Admin: Registry/Catalog Diagnostics ----
@app.get("/admin/config/paths")
async def get_config_paths():
    """Expose effective file paths used by the gateway for troubleshooting mounts."""
    return {
        "REGISTRY_PATH": REGISTRY_PATH,
        "CATALOG_PATH": CATALOG_PATH,
        "APPS_REGISTRY_PATH": APPS_REGISTRY_PATH
    }

@app.post("/admin/registry/flush")
async def flush_registry(reg: Optional[dict] = None):
    """Force-write the in-memory registry (or provided 'reg') to REGISTRY_PATH and report errors."""
    try:
        payload = reg if isinstance(reg, dict) else REG
        if not isinstance(payload, dict):
            raise HTTPException(400, "Invalid registry payload")
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return {"status": "ok", "path": REGISTRY_PATH, "size": len(json.dumps(payload))}
    except Exception as e:
        raise HTTPException(500, f"Failed to write registry: {str(e)}")

@app.post("/admin/registry/alias")
async def upsert_registry_alias(alias: dict):
    """Upsert a logical alias mapping: {"id":"llama4:scout", "providers": {"ollama":"llama4:scout"}}"""
    try:
        logical = alias.get("id") or alias.get("name")
        providers = alias.get("providers")
        if not logical or not isinstance(providers, dict):
            raise HTTPException(400, "Provide 'id' and 'providers' map")
        if REG.get("aliases") is None:
            REG["aliases"] = {}
        REG["aliases"][logical] = providers
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(REG, f, indent=2)
        return {"status": "upserted", "id": logical, "providers": providers}
    except Exception as e:
        raise HTTPException(500, f"Failed to upsert alias: {str(e)}")

@app.get("/assets/{asset_id}")
async def get_asset(asset_id: str):
    for a in build_unified_catalog().get("assets", []):
        if a.get("id") == asset_id:
            return a
    raise HTTPException(404, f"Asset not found: {asset_id}")

# ---- Asset Management Endpoints ----
@app.post("/admin/assets")
async def create_asset(asset: dict):
    """Add a new asset to the catalog"""
    try:
        # Validate required fields
        if not asset.get("id") or not asset.get("class") or not asset.get("name"):
            raise HTTPException(400, "Missing required fields: id, class, name")
        
        # Check if asset already exists
        existing_ids = {a.get("id") for a in CATALOG.get("assets", [])}
        if asset.get("id") in existing_ids:
            raise HTTPException(409, f"Asset with id '{asset['id']}' already exists")
        
        # Add to catalog
        CATALOG["assets"].append(asset)
        
        # Write back to file
        with open(CATALOG_PATH, "w", encoding="utf-8") as f:
            json.dump(CATALOG, f, indent=2)

        # If this is a model asset, auto-sync registry aliases so it appears under Models
        try:
            if (asset.get("class") == "model"):
                logical_name = asset.get("id") or asset.get("name")
                meta = asset.get("metadata") or {}
                providers = meta.get("providers") if isinstance(meta.get("providers"), dict) else None

                # Heuristics: if explicit providers mapping not supplied, derive a minimal one
                if not providers:
                    single_provider = meta.get("provider")  # e.g. "ollama" | "openai" | "huggingface"
                    if single_provider:
                        providers = {str(single_provider): logical_name}
                    else:
                        providers = {"ollama": logical_name}

                # Initialize REG structure if missing
                if REG.get("aliases") is None:
                    REG["aliases"] = {}

                REG["aliases"][logical_name] = providers

                # Persist registry
                with open(REGISTRY_PATH, "w", encoding="utf-8") as rf:
                    json.dump(REG, rf, indent=2)
        except Exception:
            # Do not fail the asset creation if registry sync fails; catalog remains the source of truth for assets
            pass
        
        return {"status": "created", "asset": asset}
    except Exception as e:
        raise HTTPException(500, f"Error creating asset: {str(e)}")

@app.put("/admin/assets/{asset_id}")
async def update_asset(asset_id: str, asset_update: dict):
    """Update an existing asset in the catalog"""
    try:
        # Find and update asset
        for i, asset in enumerate(CATALOG.get("assets", [])):
            if asset.get("id") == asset_id:
                updated = {**asset, **asset_update}
                CATALOG["assets"][i] = updated
                
                # Write back to file
                with open(CATALOG_PATH, "w", encoding="utf-8") as f:
                    json.dump(CATALOG, f, indent=2)

                # Keep registry aliases in sync for model assets
                try:
                    if (updated.get("class") == "model"):
                        old_logical = asset.get("id") or asset.get("name")
                        new_logical = updated.get("id") or updated.get("name") or old_logical
                        meta = (updated.get("metadata") or {})
                        providers = meta.get("providers") if isinstance(meta.get("providers"), dict) else None
                        if not providers:
                            single_provider = meta.get("provider")
                            if single_provider:
                                providers = {str(single_provider): new_logical}
                            else:
                                providers = {"ollama": new_logical}

                        if REG.get("aliases") is None:
                            REG["aliases"] = {}

                        # Handle id rename: remove old key if changed
                        if new_logical != old_logical and old_logical in REG["aliases"]:
                            REG["aliases"].pop(old_logical, None)

                        REG["aliases"][new_logical] = providers

                        with open(REGISTRY_PATH, "w", encoding="utf-8") as rf:
                            json.dump(REG, rf, indent=2)
                except Exception:
                    pass

                return {"status": "updated", "asset": CATALOG["assets"][i]}
        
        raise HTTPException(404, f"Asset not found: {asset_id}")
    except Exception as e:
        raise HTTPException(500, f"Error updating asset: {str(e)}")

@app.delete("/admin/assets/{asset_id}")
async def delete_asset(asset_id: str):
    """Delete an asset from the catalog"""
    try:
        # Find and remove asset
        for i, asset in enumerate(CATALOG.get("assets", [])):
            if asset.get("id") == asset_id:
                deleted_asset = CATALOG["assets"].pop(i)
                
                # Write back to file
                with open(CATALOG_PATH, "w", encoding="utf-8") as f:
                    json.dump(CATALOG, f, indent=2)

                # If this was a model, also remove from registry aliases
                try:
                    if deleted_asset.get("class") == "model":
                        logical = deleted_asset.get("id") or deleted_asset.get("name")
                        if REG.get("aliases") and logical in REG["aliases"]:
                            REG["aliases"].pop(logical, None)
                            with open(REGISTRY_PATH, "w", encoding="utf-8") as rf:
                                json.dump(REG, rf, indent=2)
                except Exception:
                    pass
                
                return {"status": "deleted", "asset": deleted_asset}
        
        raise HTTPException(404, f"Asset not found: {asset_id}")
    except Exception as e:
        raise HTTPException(500, f"Error deleting asset: {str(e)}")

@app.post("/admin/assets/{asset_id}/lifecycle")
async def set_asset_lifecycle(asset_id: str, lifecycle: dict):
    """Set desired lifecycle state for an asset"""
    try:
        desired_state = lifecycle.get("desired")
        if desired_state not in ["running", "stopped", "paused"]:
            raise HTTPException(400, "Invalid desired state. Must be: running, stopped, or paused")
        
        # Find and update asset lifecycle
        for i, asset in enumerate(CATALOG.get("assets", [])):
            if asset.get("id") == asset_id:
                if "lifecycle" not in CATALOG["assets"][i]:
                    CATALOG["assets"][i]["lifecycle"] = {}
                CATALOG["assets"][i]["lifecycle"]["desired"] = desired_state
                
                # Write back to file
                with open(CATALOG_PATH, "w", encoding="utf-8") as f:
                    json.dump(CATALOG, f, indent=2)
                
                return {"status": "updated", "asset": CATALOG["assets"][i]}
        
        raise HTTPException(404, f"Asset not found: {asset_id}")
    except Exception as e:
        raise HTTPException(500, f"Error updating lifecycle: {str(e)}")

# ---- Models List (OpenAI-compatible) ----
@app.get("/v1/models")
async def list_models_openai():
    """OpenAI-compatible /v1/models endpoint for client discovery"""
    try:
        # Get all models from catalog and registry
        all_models = set()
        
        # From catalog defaults
        defaults = CATALOG.get("defaults", {})
        if defaults.get("chat_model"):
            all_models.add(defaults["chat_model"])
        if defaults.get("embed_model"):
            all_models.add(defaults["embed_model"])
        
        # From app policies
        for asset in CATALOG.get("assets", []):
            if asset.get("class") == "app":
                policy = asset.get("policy", {})
                all_models.update(policy.get("allowed_models", []))
                all_models.update(policy.get("allowed_embeddings", []))
        
        # From registry aliases
        aliases = (REG or {}).get("aliases", {})
        all_models.update(aliases.keys())
        
        # Format as OpenAI-compatible response
        models_data = []
        for model_name in sorted(all_models):
            models_data.append({
                "id": model_name,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "abs-hub",
                "permission": [],
                "root": model_name,
                "parent": None
            })
        
        return {
            "object": "list",
            "data": models_data
        }
    except Exception as e:
        raise HTTPException(500, f"Error listing models: {str(e)}")

# ---- Chat ----
@app.post("/v1/chat/completions")
async def chat(req: ChatReq, request: Request, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    t0 = time.time()
    cfg = pick_app_cfg(app_id)
    provider = cfg.get("provider", "auto")
    if provider == "auto":
        provider = await detect_provider()

    model_logical = req.model or cfg.get("chat_model", "contract-default")

    # Policy enforcement via Catalog (preferred), fallback to per-app cfg
    allowed_models: Optional[List[str]] = None
    for a in CATALOG.get("assets", []):
        if a.get("class") == "app" and a.get("id") == (app_id or ""):
            allowed_models = ((a.get("policy") or {}).get("allowed_models"))
            break
    if allowed_models is None:
        allowed_models = cfg.get("allowed_models")
    if allowed_models is not None and model_logical not in allowed_models:
        raise HTTPException(403, f"Model '{model_logical}' is not allowed for this app")

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

    # Policy enforcement via Catalog (preferred), fallback to per-app cfg
    allowed_embeddings: Optional[List[str]] = None
    for a in CATALOG.get("assets", []):
        if a.get("class") == "app" and a.get("id") == (app_id or ""):
            allowed_embeddings = ((a.get("policy") or {}).get("allowed_embeddings"))
            break
    if allowed_embeddings is None:
        allowed_embeddings = cfg.get("allowed_embeddings")
    if allowed_embeddings is not None and logical not in allowed_embeddings:
        raise HTTPException(403, f"Embedding model '{logical}' is not allowed for this app")

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
    """Get real-time system metrics including GPU"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Network I/O
        network = psutil.net_io_counters()
        
        # GPU metrics
        gpu_info = []
        gpu_debug = {"pynvml_available": False, "gputil_available": False, "error": None}
        
        try:
            import pynvml
            gpu_debug["pynvml_available"] = True
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            print(f"Found {device_count} NVIDIA GPUs")
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # GPU name
                name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                
                # GPU utilization
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                
                # GPU memory
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                # GPU temperature
                try:
                    temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                except:
                    temp = None
                
                # GPU power usage
                try:
                    power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
                except:
                    power = None
                
                gpu_info.append({
                    "id": i,
                    "name": name,
                    "utilization": util.gpu,
                    "memory_utilization": util.memory,
                    "memory_total": mem_info.total,
                    "memory_used": mem_info.used,
                    "memory_free": mem_info.free,
                    "temperature": temp,
                    "power_usage": power
                })
                
        except ImportError as e:
            gpu_debug["error"] = f"pynvml ImportError: {e}"
            print(f"pynvml not available: {e}")
            # Fallback to GPUtil if pynvml not available
            try:
                import GPUtil
                gpu_debug["gputil_available"] = True
                gpus = GPUtil.getGPUs()
                print(f"Found {len(gpus)} GPUs via GPUtil")
                for i, gpu in enumerate(gpus):
                    gpu_info.append({
                        "id": i,
                        "name": gpu.name,
                        "utilization": gpu.load * 100,
                        "memory_utilization": gpu.memoryUtil * 100,
                        "memory_total": gpu.memoryTotal * 1024 * 1024 * 1024,  # Convert to bytes
                        "memory_used": gpu.memoryUsed * 1024 * 1024 * 1024,
                        "memory_free": gpu.memoryFree * 1024 * 1024 * 1024,
                        "temperature": gpu.temperature,
                        "power_usage": None
                    })
            except ImportError as e2:
                gpu_debug["error"] = f"Both pynvml and GPUtil failed: {e}, {e2}"
                print(f"GPUtil also not available: {e2}")
                gpu_info = []
        except Exception as gpu_error:
            gpu_debug["error"] = str(gpu_error)
            print(f"GPU monitoring error: {gpu_error}")
            gpu_info = []
        
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
            "gpu": gpu_info,
            "gpu_debug": gpu_debug,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(500, f"Error getting system metrics: {str(e)}")

@app.get("/api/health/postgresql")
async def health_postgresql():
    """Check PostgreSQL service health"""
    try:
        # Check if PostgreSQL container is running
        container_name = CONTAINER_MAP.get("postgresql")
        if not container_name:
            return {"status": "error", "service": "postgresql", "error": "Container mapping not found"}, 500
        
        if docker_client == "subprocess":
            result = subprocess.run([
                'docker', 'ps', '--filter', f'name={container_name}',
                '--format', '{{.Status}}'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                container_status = result.stdout.strip()
                if 'Up' in container_status:
                    # Container is running, check database connectivity
                    try:
                        import psycopg2
                        conn = psycopg2.connect(
                            host='localhost',
                            port=5432,
                            database='document_hub',
                            user='hub_user',
                            password='secure_password',
                            connect_timeout=5
                        )
                        cursor = conn.cursor()
                        cursor.execute("SELECT 1")
                        cursor.close()
                        conn.close()
                        
                        return {
                            'status': 'healthy',
                            'service': 'postgresql',
                            'container_status': container_status,
                            'database_connectivity': 'ok'
                        }
                    except Exception as db_error:
                        return {
                            'status': 'unhealthy',
                            'service': 'postgresql',
                            'container_status': container_status,
                            'database_connectivity': 'failed',
                            'error': str(db_error)
                        }, 503
                else:
                    return {
                        'status': 'unhealthy',
                        'service': 'postgresql',
                        'container_status': container_status,
                        'error': 'Container not running'
                    }, 503
            else:
                return {
                    'status': 'unhealthy',
                    'service': 'postgresql',
                    'error': 'Container not found'
                }, 503
        else:
            # Use docker library
            container = docker_client.containers.get(container_name)
            if container.status == "running":
                # Check database connectivity
                try:
                    import psycopg2
                    conn = psycopg2.connect(
                        host='localhost',
                        port=5432,
                        database='document_hub',
                        user='hub_user',
                        password='secure_password',
                        connect_timeout=5
                    )
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    conn.close()
                    
                    return {
                        'status': 'healthy',
                        'service': 'postgresql',
                        'container_status': container.status,
                        'database_connectivity': 'ok'
                    }
                except Exception as db_error:
                    return {
                        'status': 'unhealthy',
                        'service': 'postgresql',
                        'container_status': container.status,
                        'database_connectivity': 'failed',
                        'error': str(db_error)
                    }, 503
            else:
                return {
                    'status': 'unhealthy',
                    'service': 'postgresql',
                    'container_status': container.status,
                    'error': 'Container not running'
                }, 503
                
    except Exception as e:
        return {
            'status': 'error',
            'service': 'postgresql',
            'error': str(e)
        }, 500

@app.post("/api/manage/postgresql")
async def manage_postgresql(request: Request):
    """Manage PostgreSQL service (start/stop/restart)"""
    try:
        payload = await request.json()
        action = payload.get('action')
        
        if action not in ['start', 'stop', 'restart']:
            return {"error": "Invalid action. Must be: start, stop, or restart"}, 400
        
        container_name = CONTAINER_MAP.get("postgresql")
        if not container_name:
            return {"error": "PostgreSQL container mapping not found"}, 500
        
        if docker_client == "subprocess":
            cmd = ["docker", action, container_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Update service registry
                SERVICE_REGISTRY["postgresql"]["actual"] = "running" if action == "start" else "stopped"
                return {
                    "action": action,
                    "status": "success",
                    "message": f"PostgreSQL {action}ed successfully",
                    "output": result.stdout
                }
            else:
                return {
                    "action": action,
                    "status": "error",
                    "message": f"Failed to {action} PostgreSQL",
                    "error": result.stderr
                }, 500
        else:
            # Use docker library
            container = docker_client.containers.get(container_name)
            
            if action == "start":
                container.start()
            elif action == "stop":
                container.stop()
            elif action == "restart":
                container.restart()
            
            # Update service registry
            SERVICE_REGISTRY["postgresql"]["actual"] = "running" if action == "start" else "stopped"
            
            return {
                "action": action,
                "status": "success",
                "message": f"PostgreSQL {action}ed successfully"
            }
            
    except Exception as e:
        return {"error": str(e)}, 500

@app.get("/api/metrics/postgresql")
async def metrics_postgresql():
    """Get PostgreSQL performance metrics"""
    try:
        # Get container stats
        container_name = CONTAINER_MAP.get("postgresql")
        if not container_name:
            return {"error": "PostgreSQL container mapping not found"}, 500
        
        container_stats = {}
        if docker_client == "subprocess":
            result = subprocess.run([
                'docker', 'stats', container_name, '--no-stream', '--format',
                '{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}}'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                stats_parts = result.stdout.strip().split(',')
                if len(stats_parts) >= 5:
                    container_stats = {
                        "cpu_percent": stats_parts[0],
                        "memory_usage": stats_parts[1],
                        "memory_percent": stats_parts[2],
                        "network_io": stats_parts[3],
                        "block_io": stats_parts[4]
                    }
        else:
            # Use docker library for stats
            container = docker_client.containers.get(container_name)
            stats = container.stats(stream=False)
            
            # Calculate CPU percentage
            cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
            system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
            cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100.0
            
            # Memory usage
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            memory_percent = (memory_usage / memory_limit) * 100.0
            
            container_stats = {
                "cpu_percent": f"{cpu_percent:.2f}%",
                "memory_usage": f"{memory_usage / 1024 / 1024:.2f}MB",
                "memory_percent": f"{memory_percent:.2f}%",
                "network_io": f"{stats['networks']['eth0']['rx_bytes']} / {stats['networks']['eth0']['tx_bytes']}",
                "block_io": f"{stats['blkio_stats']['io_service_bytes'][0]['value']} / {stats['blkio_stats']['io_service_bytes'][1]['value']}"
            }
        
        # Get database metrics
        db_metrics = {}
        try:
            import psycopg2
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='document_hub',
                user='hub_user',
                password='secure_password',
                connect_timeout=5
            )
            cursor = conn.cursor()
            
            # Get database size
            cursor.execute("SELECT pg_size_pretty(pg_database_size('document_hub'))")
            db_size = cursor.fetchone()[0]
            
            # Get connection count
            cursor.execute("SELECT count(*) FROM pg_stat_activity")
            connections = cursor.fetchone()[0]
            
            # Get table statistics
            cursor.execute("""
                SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
                FROM pg_stat_user_tables
            """)
            table_stats = cursor.fetchall()
            
            # Get database uptime
            cursor.execute("SELECT pg_postmaster_start_time()")
            start_time = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            db_metrics = {
                'database_size': db_size,
                'active_connections': connections,
                'table_statistics': [{"schema": row[0], "table": row[1], "inserts": row[2], "updates": row[3], "deletes": row[4]} for row in table_stats],
                'uptime_since': start_time.isoformat() if start_time else None
            }
            
        except Exception as db_error:
            db_metrics = {'error': str(db_error)}
        
        return {
            'container': container_stats,
            'database': db_metrics,
            'timestamp': time.time()
        }
        
    except Exception as e:
        return {'error': str(e)}, 500

def discover_postgresql_service():
    """Discover and register PostgreSQL service"""
    try:
        # Check if PostgreSQL container exists
        container_name = CONTAINER_MAP.get("postgresql")
        if not container_name:
            return None
        
        if docker_client == "subprocess":
            result = subprocess.run([
                'docker', 'ps', '-a', '--filter', f'name={container_name}',
                '--format', '{{.Names}},{{.Status}},{{.Ports}}'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                name, status, ports = result.stdout.strip().split(',')
                
                service_info = {
                    'name': 'postgresql',
                    'container_name': name,
                    'status': 'running' if 'Up' in status else 'stopped',
                    'ports': ports,
                    'health_endpoint': '/api/health/postgresql',
                    'management_endpoint': '/api/manage/postgresql',
                    'metrics_endpoint': '/api/metrics/postgresql'
                }
                
                # Register in service registry
                SERVICE_REGISTRY["postgresql"]["actual"] = service_info['status']
                
                return service_info
            else:
                return None
        else:
            # Use docker library
            try:
                container = docker_client.containers.get(container_name)
                service_info = {
                    'name': 'postgresql',
                    'container_name': container.name,
                    'status': container.status,
                    'ports': str(container.ports),
                    'health_endpoint': '/api/health/postgresql',
                    'management_endpoint': '/api/manage/postgresql',
                    'metrics_endpoint': '/api/metrics/postgresql'
                }
                
                # Register in service registry
                SERVICE_REGISTRY["postgresql"]["actual"] = service_info['status']
                
                return service_info
            except docker.errors.NotFound:
                return None
                
    except Exception as e:
        print(f"Error discovering PostgreSQL service: {e}")
        return None

@app.get("/admin/services/discovery")
async def discover_services():
    """Discover all services and return their information"""
    discovered_services = {}
    
    # Discover PostgreSQL
    postgresql_info = discover_postgresql_service()
    if postgresql_info:
        discovered_services["postgresql"] = postgresql_info
    
    # Discover other services (existing logic can be added here)
    for service_name in ["ollama", "qdrant", "redis", "onyx"]:
        try:
            container_name = CONTAINER_MAP.get(service_name)
            if container_name:
                if docker_client == "subprocess":
                    result = subprocess.run([
                        'docker', 'ps', '-a', '--filter', f'name={container_name}',
                        '--format', '{{.Names}},{{.Status}},{{.Ports}}'
                    ], capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        name, status, ports = result.stdout.strip().split(',')
                        discovered_services[service_name] = {
                            'name': service_name,
                            'container_name': name,
                            'status': 'running' if 'Up' in status else 'stopped',
                            'ports': ports
                        }
                else:
                    try:
                        container = docker_client.containers.get(container_name)
                        discovered_services[service_name] = {
                            'name': service_name,
                            'container_name': container.name,
                            'status': container.status,
                            'ports': str(container.ports)
                        }
                    except docker.errors.NotFound:
                        pass
        except Exception as e:
            print(f"Error discovering {service_name}: {e}")
    
    return {
        "discovered_services": discovered_services,
        "service_registry": SERVICE_REGISTRY,
        "timestamp": time.time()
    }

@app.get("/admin/services/status")
async def get_services_status():
    """Get status of all services"""
    services = {}
    
    # Check Ollama
    try:
        r = await HTTP.get(f"{OLLAMA_BASE.rstrip('/')}/api/tags")
        if r.is_success:
            models = r.json().get("models", [])
            # Try to get Ollama version
            ollama_version = "unknown"
            try:
                r_ver = await HTTP.get(f"{OLLAMA_BASE.rstrip('/')}/api/version")
                if r_ver.is_success:
                    ollama_version = (r_ver.json() or {}).get("version", "unknown")
            except Exception:
                pass
            # Get running models
            try:
                r_ps = await HTTP.get(f"{OLLAMA_BASE.rstrip('/')}/api/ps")
                running_models = []
                if r_ps.is_success:
                    running_models = [m.get("name", "") for m in r_ps.json().get("models", [])]
            except:
                running_models = []
            
            services["ollama"] = {
                "status": "online",
                "models": [m.get("name", "") for m in models],
                "running_models": running_models,
                "model_count": len(models),
                "running_count": len(running_models),
                "version": ollama_version
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
            total_vectors = 0
            for collection in collections:
                try:
                    # Get collection info to count vectors
                    coll_info = await HTTP.get(f"http://qdrant:6333/collections/{collection.get('name', '')}")
                    if coll_info.is_success:
                        vectors_count = coll_info.json().get("result", {}).get("vectors_count", 0)
                        total_vectors += vectors_count
                except:
                    pass
            
            # Try to get Qdrant version
            qdrant_version = "unknown"
            try:
                r_root = await HTTP.get("http://qdrant:6333/")
                if r_root.is_success:
                    body = r_root.json() or {}
                    qdrant_version = body.get("version") or body.get("status", {}).get("version", "unknown")
            except Exception:
                pass

            services["qdrant"] = {
                "status": "online",
                "collections": [c.get("name", "") for c in collections],
                "collection_count": len(collections),
                "total_vectors": total_vectors,
                "version": qdrant_version
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
    
    # Check PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='document_hub',
            user='hub_user',
            password='secure_password',
            connect_timeout=5
        )
        cursor = conn.cursor()
        
        # Get PostgreSQL version
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        
        # Get database size
        cursor.execute("SELECT pg_size_pretty(pg_database_size('document_hub'))")
        db_size = cursor.fetchone()[0]
        
        # Get connection count
        cursor.execute("SELECT count(*) FROM pg_stat_activity")
        connections = cursor.fetchone()[0]
        
        # Get table count
        cursor.execute("""
            SELECT count(*) FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        services["postgresql"] = {
            "status": "online",
            "version": version.split()[1] if len(version.split()) > 1 else "unknown",
            "database_size": db_size,
            "active_connections": connections,
            "table_count": table_count
        }
    except Exception as e:
        services["postgresql"] = {"status": "offline", "error": str(e)}
    
    # Check Gateway (self)
    try:
        services["gateway"] = {
            "status": "online",
            "version": "1.0.0",
            "uptime": "running"
        }
    except Exception as e:
        services["gateway"] = {"status": "offline", "error": str(e)}
    
    return services

@app.get("/admin/models")
async def get_models(app_id: Optional[str] = None):
    """Unified model catalog for Hub UI: availability (pulled) and running (in VRAM).
    If app_id is provided, filter models by catalog policy. Includes usage tracking and catalog info."""
    try:
        # Get Ollama status
        available: List[str] = []
        running: List[str] = []
        try:
            r_tags = await HTTP.get(f"{OLLAMA_BASE.rstrip('/')}/api/tags")
            if r_tags.is_success:
                raw = [m.get("name") for m in r_tags.json().get("models", []) if m.get("name")]
                # Normalize X and X:latest to be equivalent
                norm = set()
                for n in raw:
                    norm.add(n)
                    if n.endswith(":latest"):
                        norm.add(n[:-7])
                    else:
                        norm.add(f"{n}:latest")
                available = list(norm)
        except Exception:
            pass

        try:
            r_ps = await HTTP.get(f"{OLLAMA_BASE.rstrip('/')}/api/ps")
            running_models_info = {}
            if r_ps.is_success:
                running_models_data = r_ps.json().get("models", [])
                # Normalize running names similarly (X and X:latest)
                running = []
                for m in running_models_data:
                    n = m.get("name")
                    if not n:
                        continue
                    running.append(n)
                    if n.endswith(":latest"):
                        running.append(n[:-7])
                    else:
                        running.append(f"{n}:latest")
                # Store detailed info for countdown calculation
                for model in running_models_data:
                    running_models_info[model.get("name")] = model
        except Exception:
            running_models_info = {}

        # Collect all models from catalog
        all_models = set()
        
        # From app policies
        for asset in CATALOG.get("assets", []):
            if asset.get("class") == "app":
                policy = asset.get("policy", {})
                allowed_models = policy.get("allowed_models", [])
                allowed_embeddings = policy.get("allowed_embeddings", [])
                all_models.update(allowed_models)
                all_models.update(allowed_embeddings)
        
        # From registry aliases
        aliases = (REG or {}).get("aliases", {})
        all_models.update(aliases.keys())
        
        # From defaults
        defaults = CATALOG.get("defaults", {})
        if defaults.get("chat_model"):
            all_models.add(defaults["chat_model"])
        if defaults.get("embed_model"):
            all_models.add(defaults["embed_model"])

        # Get allowed models from catalog if app_id provided
        allowed_models: Optional[List[str]] = None
        if app_id:
            for asset in CATALOG.get("assets", []):
                if asset.get("class") == "app" and asset.get("id") == app_id:
                    policy = asset.get("policy", {})
                    allowed_models = policy.get("allowed_models", []) + policy.get("allowed_embeddings", [])
                    break

        # Normalize model names: collapse X and X:latest to X for display
        def _base(name: str) -> str:
            return name[:-7] if isinstance(name, str) and name.endswith(":latest") else name

        all_models = { _base(n) for n in all_models }
        if allowed_models is not None:
            allowed_models = [ _base(n) for n in (allowed_models or []) ]
        
        # Build comprehensive model information (dedupe by logical base name)
        models = []
        seen: set = set()
        for model_name in sorted(all_models):
            logical_name = model_name[:-7] if isinstance(model_name, str) and model_name.endswith(":latest") else model_name
            if logical_name in seen:
                continue
            seen.add(logical_name)
            # Determine model type
            is_embedding = any(keyword in logical_name.lower() for keyword in 
                              ['embedding', 'bert', 'bge', 'minilm', 'sentence', 'all-mini'])
            
            # Find usage by apps
            used_by = []
            for asset in CATALOG.get("assets", []):
                if asset.get("class") == "app":
                    policy = asset.get("policy", {})
                    if logical_name in policy.get("allowed_models", []) or logical_name in policy.get("allowed_embeddings", []):
                        used_by.append({
                            "id": asset.get("id"),
                            "name": asset.get("name"),
                            "type": "chat" if logical_name in policy.get("allowed_models", []) else "embedding"
                        })
            
            # Check if it's a default model
            is_default_chat = defaults.get("chat_model") == logical_name
            is_default_embed = defaults.get("embed_model") == logical_name
            
            # Apply filtering if app_id provided
            if allowed_models and logical_name not in allowed_models:
                continue
            
            # Map logical name to provider-specific names for Ollama checks
            model_aliases = aliases.get(logical_name, {})
            ollama_name = model_aliases.get("ollama", logical_name)
            
            # Calculate auto-unload countdown if model is running
            auto_unload_countdown = None
            if ollama_name in running and ollama_name in running_models_info:
                model_info = running_models_info[ollama_name]
                expires_at = model_info.get("expires_at")
                if expires_at:
                    try:
                        from datetime import datetime
                        expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        now_dt = datetime.now(expires_dt.tzinfo)
                        time_until_unload = expires_dt - now_dt
                        if time_until_unload.total_seconds() > 0:
                            hours = int(time_until_unload.total_seconds() // 3600)
                            minutes = int((time_until_unload.total_seconds() % 3600) // 60)
                            auto_unload_countdown = f"{hours}h {minutes}m"
                    except:
                        auto_unload_countdown = expires_at
            
            models.append({
                "name": logical_name,
                "type": "embedding" if is_embedding else "llm",
                "available": ollama_name in available,
                "running": ollama_name in running,
                "used_by": used_by,
                "is_default_chat": is_default_chat,
                "is_default_embed": is_default_embed,
                "aliases": aliases.get(logical_name, {}),
                "status": "running" if ollama_name in running else ("available" if ollama_name in available else "unavailable"),
                "allowed": allowed_models is None or logical_name in (allowed_models or []),
                "auto_unload_countdown": auto_unload_countdown
            })

        # Note: we intentionally do NOT append extra running-only names to avoid duplicates

        return {
            "models": models, 
            "app_id": app_id, 
            "policy_applied": allowed_models is not None,
            "summary": {
                "total": len(models),
                "llm_models": len([m for m in models if m["type"] == "llm"]),
                "embedding_models": len([m for m in models if m["type"] == "embedding"]),
                "running": len([m for m in models if m["running"]]),
                "available": len([m for m in models if m["available"]]),
                "unavailable": len([m for m in models if not m["available"]])
            }
        }
    except Exception as e:
        raise HTTPException(500, f"Error listing models: {str(e)}")

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
        result = await unload_model(model_name)
        if result:
            # Remove from model registry
            if model_name in MODEL_REGISTRY:
                MODEL_REGISTRY[model_name]["keep_alive_until"] = 0
            
            return {"status": "unloaded", "model": model_name}
        else:
            # Get countdown info for better error message
            countdown_info = ""
            try:
                ps_r = await HTTP.get(f"{OLLAMA_BASE.rstrip('/')}/api/ps")
                if ps_r.is_success:
                    running_models = ps_r.json().get("models", [])
                    for model in running_models:
                        if model.get("name") == model_name:
                            expires_at = model.get("expires_at")
                            if expires_at:
                                try:
                                    from datetime import datetime
                                    expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                                    now_dt = datetime.now(expires_dt.tzinfo)
                                    time_until_unload = expires_dt - now_dt
                                    if time_until_unload.total_seconds() > 0:
                                        hours = int(time_until_unload.total_seconds() // 3600)
                                        minutes = int((time_until_unload.total_seconds() % 3600) // 60)
                                        countdown_info = f" Model will auto-unload in {hours}h {minutes}m."
                                except:
                                    countdown_info = f" Model will auto-unload at {expires_at}."
                            break
            except:
                pass
            
            raise HTTPException(500, f"Failed to unload model {model_name}.{countdown_info}")
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

@app.post("/admin/models/{model_name}/pull")
async def pull_model(model_name: str):
    """Pull a model from Ollama registry"""
    try:
        payload = {"name": model_name, "stream": False}
        r = await HTTP.post(f"{OLLAMA_BASE.rstrip('/')}/api/pull", json=payload, timeout=300)
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        
        return {"status": "pulling", "model": model_name}
    except Exception as e:
        raise HTTPException(500, f"Error pulling model: {str(e)}")

@app.post("/admin/models/{model_name}/load")
async def load_model(model_name: str):
    """Load a model (LLM or embedding) into VRAM in Ollama.
    For embeddings, we warm by calling /api/embeddings; for LLMs we call /api/generate.
    """
    try:
        # First ensure model is available (pull if needed)
        await preload_model_if_needed(model_name, "ollama")
        
        # Detect if this is likely an embedding model by checking registry aliases
        aliases = (REG or {}).get("aliases", {})
        providers = aliases.get(model_name, {}) if isinstance(aliases, dict) else {}
        # simple heuristic: embedding models we track are non-llama families like bge/all-minilm/legal-bert
        is_embedding = any(k in model_name.lower() for k in ["bge", "minilm", "bert", "embedding"]) or providers.get("type") == "embedding"

        if is_embedding:
            # Warm embeddings by issuing a tiny embedding request with keep_alive
            payload = {
                "model": model_name,
                "input": "warm",
                "options": {"keep_alive": f"{AUTO_WAKE_SETTINGS['model_keep_alive_hours']}h"}
            }
            r = await HTTP.post(f"{OLLAMA_BASE.rstrip('/')}/api/embeddings", json=payload, timeout=30)
        else:
            # LLM warm via generate
            payload = {"model": model_name, "prompt": "test", "stream": False, "options": {"keep_alive": f"{AUTO_WAKE_SETTINGS['model_keep_alive_hours']}h"}}
            r = await HTTP.post(f"{OLLAMA_BASE.rstrip('/')}/api/generate", json=payload, timeout=30)
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        
        return {"status": "loaded", "model": model_name}
    except Exception as e:
        raise HTTPException(500, f"Error loading model: {str(e)}")

@app.delete("/admin/models/{model_name}")
async def delete_model(model_name: str):
    """Delete a model from Ollama storage (handles aliases and :latest)."""
    try:
        # Build candidate names from alias and :latest normalization
        def variants(name: str) -> set:
            out = {name}
            if name.endswith(":latest"):
                out.add(name[:-7])
            else:
                out.add(f"{name}:latest")
            return out

        aliases = (REG or {}).get("aliases", {}) if isinstance(REG, dict) else {}
        provider_map = aliases.get(model_name, {}) if isinstance(aliases, dict) else {}
        oll_name = provider_map.get("ollama", model_name)
        cands = set()
        cands |= variants(model_name)
        cands |= variants(oll_name)

        last_error = None
        for cand in cands:
            try:
                payload = {"name": cand}
                r = await HTTP.request("DELETE", f"{OLLAMA_BASE.rstrip('/')}/api/delete", json=payload)
                if r.is_success:
                    return {"status": "deleted", "model": cand}
                # Treat not found as success (already deleted)
                if "not found" in (r.text or "").lower():
                    return {"status": "deleted", "model": cand, "note": "model not found (already deleted)"}
                last_error = f"{r.status_code}: {r.text}"
            except Exception as ex:
                last_error = str(ex)
                continue
        raise HTTPException(500, f"Failed to delete model {model_name}: {last_error}")
    except Exception as e:
        raise HTTPException(500, f"Error deleting model: {str(e)}")

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