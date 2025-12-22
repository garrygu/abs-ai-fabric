import asyncio
import time
import subprocess
import httpx
from typing import List, Optional

# Constants from config (using relative import or assuming config in path)
try:
    from config import AUTO_WAKE_SETTINGS, SERVICE_DEPENDENCIES, CONTAINER_MAP, SERVICE_STARTUP_ORDER, OLLAMA_BASE, REDIS_URL, MODEL_REGISTRY
except ImportError:
    # Fallback for dev/testing when not run as package
    from config import AUTO_WAKE_SETTINGS, SERVICE_DEPENDENCIES, CONTAINER_MAP, SERVICE_STARTUP_ORDER, OLLAMA_BASE, REDIS_URL, MODEL_REGISTRY

from .docker_service import docker_service

# Service registry tracking desired vs actual state
SERVICE_REGISTRY = {
    "ollama": {"desired": "on", "actual": "unknown", "last_used": 0, "idle_sleep_enabled": True},
    "qdrant": {"desired": "on", "actual": "unknown", "last_used": 0, "idle_sleep_enabled": True},
    "redis": {"desired": "on", "actual": "unknown", "last_used": 0, "idle_sleep_enabled": False},  # Redis should stay running
    "onyx": {"desired": "on", "actual": "unknown", "last_used": 0, "idle_sleep_enabled": True},
    "postgresql": {"desired": "on", "actual": "unknown", "last_used": 0, "idle_sleep_enabled": False}, # PostgreSQL should stay running
    "whisper-server": {"desired": "on", "actual": "unknown", "last_used": 0, "idle_sleep_enabled": True},
    "gateway": {"desired": "on", "actual": "online", "last_used": 0, "idle_sleep_enabled": False}
}

# Background task management
IDLE_MONITOR_TASK = None

async def check_service_status(service_name: str) -> str:
    """Check if a service is running"""
    try:
        if service_name == "gateway":
            return "running"

        container_name = CONTAINER_MAP.get(service_name)
        if not container_name:
            return "unknown"
        
        client = docker_service.client
        if client == "subprocess":
            result = subprocess.run(['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Status}}'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return "running" if "Up" in result.stdout else "stopped"
            return "stopped"
        else:
            if not client:
                return "unknown"
            # Assuming DockerClient/APIClient wrapper usage
            # Retrieve fresh status
            try:
                import docker
                if isinstance(client, docker.DockerClient):
                    container = client.containers.get(container_name)
                    return "running" if container.status == "running" else "stopped"
                else:
                    # APIClient
                    info = client.inspect_container(container_name)
                    return "running" if info['State']['Running'] else "stopped"
            except Exception:
                return "stopped"
    except Exception:
        return "unknown"

async def check_service_health(service_name: str) -> str:
    """
    Check detailed health status of a service.
    Returns: 'healthy', 'degraded', 'unhealthy', 'stopped', 'unknown'
    """
    # 1. Check Container Status
    status = await check_service_status(service_name)
    if status != "running":
        return "stopped"

    # 2. Check Dependencies (Degraded check)
    dependencies = SERVICE_DEPENDENCIES.get(service_name, [])
    for dep in dependencies:
        dep_status = await check_service_status(dep)
        if dep_status != "running":
            return "degraded"

    # 3. Application Readiness Check
    try:
        async with httpx.AsyncClient(timeout=2.0) as http:
            if service_name == "ollama":
                r = await http.get(f"{OLLAMA_BASE.rstrip('/')}/api/tags")
                return "healthy" if r.is_success else "unhealthy"
            
            elif service_name == "qdrant":
                r = await http.get("http://qdrant:6333/collections")
                return "healthy" if r.is_success else "unhealthy"
            
            elif service_name == "gateway":
                # Self check - if we are running this code, we are likely healthy, 
                # but could check internal state if needed.
                return "healthy"
                
            # For Redis/Postgres, we assume healthy if running for now 
            # as strict checks require auth/libs which might be heavy here.
            # Could implement specific TCP socket checks later.
            return "healthy"
            
    except Exception:
        return "unhealthy"
        
    return "healthy"

async def start_service(service_name: str) -> bool:
    """Start a service container"""
    try:
        container_name = CONTAINER_MAP.get(service_name)
        if not container_name:
            return False
        
        client = docker_service.client
        if client == "subprocess":
            cmd = ["docker", "start", container_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        else:
            if not client:
                return False
            import docker
            if isinstance(client, docker.DockerClient):
                container = client.containers.get(container_name)
                container.start()
            else:
                client.start(container_name)
            return True
    except Exception as e:
        print(f"Error starting {service_name}: {e}")
        return False

async def stop_service(service_name: str) -> bool:
    """Stop a service container"""
    try:
        container_name = CONTAINER_MAP.get(service_name)
        if not container_name:
            return False
        
        client = docker_service.client
        if client == "subprocess":
            cmd = ["docker", "stop", container_name]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        else:
            if not client:
                return False
            import docker
            if isinstance(client, docker.DockerClient):
                container = client.containers.get(container_name)
                container.stop()
            else:
                client.stop(container_name)
            return True
    except Exception as e:
        print(f"Error stopping {service_name}: {e}")
        return False

async def wait_for_service_ready(service_name: str, timeout: int = 60) -> bool:
    """Wait for a service to be ready by checking its health endpoint"""
    start_time = time.time()
    async with httpx.AsyncClient(timeout=5.0) as http:
        while time.time() - start_time < timeout:
            try:
                if service_name == "ollama":
                    r = await http.get(f"{OLLAMA_BASE.rstrip('/')}/api/tags")
                    if r.is_success:
                        return True
                elif service_name == "qdrant":
                    r = await http.get("http://qdrant:6333/collections")
                    if r.is_success:
                        return True
                elif service_name == "redis":
                    # Simple check if redis URL is reachable via another way or assume up if container runs
                    # For strict check we need redis lib, but avoiding circular dep here.
                    # Start service returns true if container started.
                    # We can do a quick connection check if needed.
                    pass 
                elif service_name == "postgresql":
                    pass # Similar to redis, specialized check
                
                # Generic fallback: if status is running, assume ready after a few secs
                status = await check_service_status(service_name)
                if status == "running" and service_name not in ["ollama", "qdrant"]:
                    return True

            except Exception:
                pass
            
            await asyncio.sleep(2)
    
    return False

async def start_service_with_dependencies(service_name: str) -> bool:
    """Start a service and all its dependencies in the correct order"""
    if not AUTO_WAKE_SETTINGS["enabled"]:
        return True
    
    dependencies = SERVICE_DEPENDENCIES.get(service_name, [])
    
    for dep in dependencies:
        dep_status = await check_service_status(dep)
        if dep_status != "running":
            print(f"Starting dependency {dep} for {service_name}...")
            if not await start_service(dep):
                return False
            if not await wait_for_service_ready(dep):
                return False
    
    return await start_service(service_name)

async def ensure_service_ready_with_dependencies(service_name: str) -> bool:
    """Ensure a service and all its dependencies are running and ready"""
    if not AUTO_WAKE_SETTINGS["enabled"]:
        return True
    
    SERVICE_REGISTRY[service_name]["last_used"] = time.time()
    current_status = await check_service_status(service_name)
    SERVICE_REGISTRY[service_name]["actual"] = current_status
    
    if current_status == "running":
        dependencies = SERVICE_DEPENDENCIES.get(service_name, [])
        for dep in dependencies:
            dep_status = await check_service_status(dep)
            if dep_status != "running":
                print(f"Dependency {dep} is not running, restarting {service_name}...")
                if not await start_service_with_dependencies(service_name):
                    return False
                break
        return True
    
    print(f"Auto-waking {service_name} with dependencies...")
    if await start_service_with_dependencies(service_name):
        if await wait_for_service_ready(service_name):
            SERVICE_REGISTRY[service_name]["actual"] = "running"
            return True
    return False

async def ensure_service_ready(service_name: str) -> bool:
    return await ensure_service_ready_with_dependencies(service_name)

async def resolve_service_dependencies(required_services: List[str]) -> List[str]:
    """Resolve all dependencies for a list of required services"""
    resolved = set()
    to_resolve = set(required_services)
    
    while to_resolve:
        service = to_resolve.pop()
        if service in resolved:
            continue
        dependencies = SERVICE_DEPENDENCIES.get(service, [])
        for dep in dependencies:
            if dep not in resolved:
                to_resolve.add(dep)
        resolved.add(service)
    
    ordered_services = []
    for service in SERVICE_STARTUP_ORDER:
        if service in resolved:
            ordered_services.append(service)
    
    for service in resolved:
        if service not in ordered_services:
            ordered_services.append(service)
    
    return ordered_services

async def ensure_multiple_services_ready(required_services: List[str]) -> bool:
    if not AUTO_WAKE_SETTINGS["enabled"]:
        return True
    all_services = await resolve_service_dependencies(required_services)
    print(f"Resolved service dependencies: {all_services}")
    for service in all_services:
        if not await ensure_service_ready_with_dependencies(service):
            return False
    return True


async def unload_model(model_name: str) -> bool:
    """Unload a model from Ollama"""
    try:
        # Try different keep_alive values to force unload
        for ka in [0, "0s", "0m"]:
            try:
                payload = {"name": model_name, "keep_alive": ka}
                async with httpx.AsyncClient(timeout=10.0) as client:
                    r = await client.post(f"{OLLAMA_BASE.rstrip('/')}/api/generate", json=payload)
                    if r.status_code == 200:
                        return True
            except Exception:
                pass
        return False
    except Exception as e:
        print(f"Error unloading model {model_name}: {e}")
        return False

async def check_and_handle_idle_models():
    if not AUTO_WAKE_SETTINGS.get("idle_sleep_enabled", True):
        return
    
    current_time = time.time()
    for model_name, info in list(MODEL_REGISTRY.items()):
        keep_alive_until = info.get("keep_alive_until", 0)
        if keep_alive_until > 0 and current_time > keep_alive_until:
            print(f"Model {model_name} keep-alive expired, unloading...")
            if await unload_model(model_name):
                info["keep_alive_until"] = 0
                print(f"Successfully unloaded idle model {model_name}")

async def check_and_handle_idle_services():
    if not AUTO_WAKE_SETTINGS["idle_sleep_enabled"]:
        return
    current_time = time.time()
    idle_timeout = AUTO_WAKE_SETTINGS["idle_timeout_minutes"] * 60
    
    for service_name, service_info in SERVICE_REGISTRY.items():
        if not service_info.get("idle_sleep_enabled", True):
            continue
        if service_info.get("desired") == "on":
            continue
        last_used = service_info.get("last_used", 0)
        if last_used > 0 and (current_time - last_used) > idle_timeout:
            status = await check_service_status(service_name)
            if status == "running":
                print(f"Service {service_name} idle for {idle_timeout/60}m, stopping...")
                if await stop_service(service_name):
                    SERVICE_REGISTRY[service_name]["actual"] = "stopped"

async def idle_monitor_task():
    while True:
        try:
            await check_and_handle_idle_services()
            await check_and_handle_idle_models()
            await asyncio.sleep(AUTO_WAKE_SETTINGS["idle_check_interval_minutes"] * 60)
        except Exception as e:
            print(f"Error in idle monitor: {e}")
            await asyncio.sleep(60)

async def start_idle_monitor():
    global IDLE_MONITOR_TASK
    if IDLE_MONITOR_TASK is None or IDLE_MONITOR_TASK.done():
        IDLE_MONITOR_TASK = asyncio.create_task(idle_monitor_task())
        print("Idle monitor started")

async def stop_idle_monitor():
    global IDLE_MONITOR_TASK
    if IDLE_MONITOR_TASK and not IDLE_MONITOR_TASK.done():
        IDLE_MONITOR_TASK.cancel()
        try:
            await IDLE_MONITOR_TASK
        except asyncio.CancelledError:
            pass
        print("Idle monitor stopped")
