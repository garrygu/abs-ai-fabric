from fastapi import APIRouter, HTTPException, WebSocket
from typing import List, Optional
import time
import psutil
import asyncio
import httpx
from pydantic import BaseModel

from services.autowake import (
    SERVICE_REGISTRY, 
    start_service, 
    stop_service, 
    ensure_multiple_services_ready, 
    resolve_service_dependencies, 
    start_idle_monitor, 
    stop_idle_monitor, 
    check_service_status,
    IDLE_MONITOR_TASK
)
from services.docker_service import docker_service
from config import AUTO_WAKE_SETTINGS, SERVICE_DEPENDENCIES, SERVICE_STARTUP_ORDER, CONTAINER_MAP, MODEL_REGISTRY, OLLAMA_BASE

router = APIRouter()

# Pydantic Models
class KeepWarmRequest(BaseModel):
    duration_minutes: int = 30

class AutoSleepRequest(BaseModel):
    enabled: bool = True
    idle_timeout_minutes: Optional[int] = None

class ClearCacheRequest(BaseModel):
    documents: bool = True
    embeddings: bool = True
    cache: bool = True

@router.get("/v1/admin/services/status")
async def get_all_services_status():
    """Get status of all known services."""
    results = {}
    for svc_name in SERVICE_REGISTRY.keys():
        # Gateway is always running (it's this service itself)
        if svc_name == "gateway":
            results[svc_name] = {
                "status": "online",
                "running": True,
                "version": "v1.0.0",
                "last_used": SERVICE_REGISTRY[svc_name].get("last_used", 0)
            }
        else:
            status = await check_service_status(svc_name)
            results[svc_name] = {
                "status": "online" if status == "running" else "offline",
                "running": status == "running",
                "version": "v1.0.0",
                "last_used": SERVICE_REGISTRY[svc_name].get("last_used", 0)
            }
    return results

@router.get("/v1/admin/models")
async def get_admin_models():
    """Admin-specific model list with more metadata."""
    # Use existing chat router logic but wrapper for admin needs
    from .chat import list_models
    return await list_models()

@router.get("/v1/admin/models/list")
async def list_ollama_models():
    """List all models from Ollama with detailed information."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_BASE.rstrip('/')}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                # Format models with additional details
                formatted_models = []
                for model in models:
                    formatted_models.append({
                        "name": model.get("name", ""),
                        "size": model.get("size", 0),
                        "modified_at": model.get("modified_at", ""),
                        "details": {
                            "parameter_size": model.get("details", {}).get("parameter_size", ""),
                            "quantization_level": model.get("details", {}).get("quantization_level", ""),
                            "format": model.get("details", {}).get("format", "")
                        }
                    })
                return {"models": formatted_models}
            else:
                raise HTTPException(500, f"Ollama API returned {response.status_code}")
    except httpx.TimeoutException:
        raise HTTPException(504, "Timeout connecting to Ollama")
    except Exception as e:
        raise HTTPException(500, f"Failed to list models: {str(e)}")

@router.post("/v1/admin/models/pull")
async def pull_model(request: dict):
    """Pull a model from Ollama."""
    model_name = request.get("name")
    if not model_name:
        raise HTTPException(400, "Model name is required")
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:  # Long timeout for large models
            response = await client.post(
                f"{OLLAMA_BASE.rstrip('/')}/api/pull",
                json={"name": model_name},
                timeout=300.0
            )
            if response.status_code == 200:
                return {"status": "success", "message": f"Model {model_name} pulled successfully"}
            else:
                error_text = response.text
                raise HTTPException(response.status_code, f"Failed to pull model: {error_text}")
    except httpx.TimeoutException:
        raise HTTPException(504, "Timeout pulling model (this may take several minutes for large models)")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to pull model: {str(e)}")

@router.post("/v1/admin/models/{model_name}/load")
async def load_model(model_name: str):
    """Load a model into Ollama memory."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Use generate endpoint with keep_alive to load model
            response = await client.post(
                f"{OLLAMA_BASE.rstrip('/')}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "test",
                    "stream": False,
                    "keep_alive": "30m"  # Keep model loaded for 30 minutes
                }
            )
            if response.status_code == 200:
                return {"status": "success", "message": f"Model {model_name} loaded successfully"}
            else:
                error_text = response.text
                raise HTTPException(response.status_code, f"Failed to load model: {error_text}")
    except httpx.TimeoutException:
        raise HTTPException(504, "Timeout loading model")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to load model: {str(e)}")

@router.delete("/v1/admin/models/{model_name}")
async def delete_model(model_name: str):
    """Delete a model from Ollama."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{OLLAMA_BASE.rstrip('/')}/api/delete",
                json={"name": model_name}
            )
            if response.status_code == 200:
                return {"status": "success", "message": f"Model {model_name} deleted successfully"}
            else:
                error_text = response.text
                raise HTTPException(response.status_code, f"Failed to delete model: {error_text}")
    except httpx.TimeoutException:
        raise HTTPException(504, "Timeout deleting model")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to delete model: {str(e)}")


@router.get("/v1/admin/idle-status")
async def get_settings():
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

@router.post("/v1/admin/services/{service_name}/idle-sleep")
async def control_service(service_name: str, action: str):
    try:
        if action == "start":
            res = await start_service(service_name)
        elif action == "stop":
            res = await stop_service(service_name)
        elif action == "restart":
            # Restart is stop then start
            await stop_service(service_name)
            res = await start_service(service_name)
        else:
            raise HTTPException(400, f"Invalid action: {action}")
        
        if res:
            SERVICE_REGISTRY[service_name]["actual"] = action if action == "start" else "stopped"
            return {"status": "success", "message": f"Service {service_name} {action}ed successfully"}
        else:
            raise HTTPException(500, f"Failed to {action} {service_name}")
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/v1/admin/services/{service_name}/suspend")
async def suspend_service(service_name: str):
    """Suspend (stop) a service immediately."""
    try:
        if service_name not in SERVICE_REGISTRY:
            raise HTTPException(404, f"Service {service_name} not found")
        res = await stop_service(service_name)
        if res:
            SERVICE_REGISTRY[service_name]["actual"] = "stopped"
            SERVICE_REGISTRY[service_name]["desired"] = "off"
            return {"status": "success", "message": f"Service {service_name} suspended"}
        else:
            raise HTTPException(500, f"Failed to suspend {service_name}")
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/v1/admin/services/{service_name}/keep-warm")
async def keep_service_warm(service_name: str, request: KeepWarmRequest = KeepWarmRequest()):
    """Keep a service warm by updating last_used timestamp."""
    try:
        if service_name not in SERVICE_REGISTRY:
            raise HTTPException(404, f"Service {service_name} not found")
        # Update last_used to current time + keep-alive duration
        SERVICE_REGISTRY[service_name]["last_used"] = time.time() + (request.duration_minutes * 60)
        return {
            "status": "success", 
            "message": f"Service {service_name} will stay warm for {request.duration_minutes} minutes",
            "keep_warm_until": SERVICE_REGISTRY[service_name]["last_used"]
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.put("/v1/admin/services/{service_name}/auto-sleep")
async def update_service_auto_sleep(service_name: str, request: AutoSleepRequest):
    """Update per-service auto-sleep settings."""
    try:
        if service_name not in SERVICE_REGISTRY:
            raise HTTPException(404, f"Service {service_name} not found")
        SERVICE_REGISTRY[service_name]["idle_sleep_enabled"] = request.enabled
        if request.idle_timeout_minutes is not None:
            # Store per-service timeout if needed (currently using global)
            SERVICE_REGISTRY[service_name]["idle_timeout_minutes"] = request.idle_timeout_minutes
        return {
            "status": "success",
            "message": f"Auto-sleep for {service_name} {'enabled' if request.enabled else 'disabled'}",
            "idle_sleep_enabled": request.enabled
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/v1/admin/settings")
async def update_settings(settings: dict):
    try:
        if "autoWakeEnabled" in settings:
            AUTO_WAKE_SETTINGS["enabled"] = bool(settings["autoWakeEnabled"])
        if "idleTimeout" in settings:
            AUTO_WAKE_SETTINGS["idle_timeout_minutes"] = int(settings["idleTimeout"])
        if "modelKeepAlive" in settings:
            AUTO_WAKE_SETTINGS["model_keep_alive_hours"] = float(settings["modelKeepAlive"])
        if "idleSleepEnabled" in settings:
            AUTO_WAKE_SETTINGS["idle_sleep_enabled"] = bool(settings["idleSleepEnabled"])
            if AUTO_WAKE_SETTINGS["idle_sleep_enabled"]:
                await start_idle_monitor()
            else:
                await stop_idle_monitor()
        if "idleCheckInterval" in settings:
            AUTO_WAKE_SETTINGS["idle_check_interval_minutes"] = int(settings["idleCheckInterval"])
        return {"status": "success", "message": "Settings updated successfully"}
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/v1/admin/system/metrics")
async def get_system_metrics():
    """Get real-time system metrics including GPU via nvidia-smi fallback."""
    try:
        import subprocess
        
        cpu_percent = psutil.cpu_percent(interval=None)  # Non-blocking, use cached value
        memory = psutil.virtual_memory()
        
        gpu_info = []
        
        # First try GPUtil
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            for i, gpu in enumerate(gpus):
                gpu_info.append({
                    "id": i,
                    "name": gpu.name,
                    "utilization": gpu.load * 100,
                    "memory_utilization": gpu.memoryUtil * 100,
                    "temperature": gpu.temperature
                })
        except Exception:
            pass
        
        # Fallback: Use nvidia-smi if GPUtil didn't find any GPUs
        if not gpu_info:
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu", 
                     "--format=csv,noheader,nounits"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0 and result.stdout.strip():
                    for line in result.stdout.strip().split('\n'):
                        parts = [p.strip() for p in line.split(',')]
                        if len(parts) >= 6:
                            idx = int(parts[0])
                            name = parts[1]
                            util = float(parts[2]) if parts[2] else 0
                            mem_used = float(parts[3]) if parts[3] else 0
                            mem_total = float(parts[4]) if parts[4] else 1
                            temp = float(parts[5]) if parts[5] else 0
                            
                            gpu_info.append({
                                "id": idx,
                                "name": name,
                                "utilization": util,
                                "memory_utilization": (mem_used / mem_total) * 100 if mem_total > 0 else 0,
                                "memory_used_mb": mem_used,
                                "memory_total_mb": mem_total,
                                "temperature": temp
                            })
            except Exception as e:
                pass  # nvidia-smi not available

        return {
            "cpu": {"usage_percent": cpu_percent},
            "memory": {"usage_percent": memory.percent},
            "gpu": gpu_info,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/v1/admin/services/{service_name}/metrics")
async def get_service_metrics(service_name: str):
    """Get runtime metrics for a specific service."""
    try:
        import subprocess
        import json
        
        # Get container name
        container_name = CONTAINER_MAP.get(service_name, f"abs-{service_name}")
        
        # Try to get Docker stats
        try:
            result = subprocess.run(
                ["docker", "stats", container_name, "--no-stream", "--format", "{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}}"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(',')
                if len(parts) >= 3:
                    cpu_str = parts[0].replace('%', '')
                    mem_usage = parts[1]
                    mem_percent = parts[2].replace('%', '')
                    
                    return {
                        "cpu_percent": float(cpu_str) if cpu_str else 0,
                        "memory_percent": float(mem_percent) if mem_percent else 0,
                        "memory_usage": mem_usage,
                        "gpu_vram_percent": None,  # Would need nvidia-smi or similar
                        "requests_per_min": 0,  # Would need request tracking
                        "timestamp": time.time()
                    }
        except Exception as e:
            pass  # Docker not available or container not running
        
        # Fallback: return system-wide metrics if container stats unavailable
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_usage": f"{memory.used / (1024**3):.2f}GB / {memory.total / (1024**3):.2f}GB",
            "gpu_vram_percent": None,
            "requests_per_min": 0,
            "timestamp": time.time(),
            "note": "System-wide metrics (container stats unavailable)"
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/v1/admin/cache/clear")
async def clear_cache(request: ClearCacheRequest = ClearCacheRequest()):
    """Clear document and embedding cache from Redis."""
    try:
        from adapters.cache_queue import get_cache_queue_adapter
        adapter = await get_cache_queue_adapter()
        
        cleared_count = 0
        
        if adapter.is_initialized() and adapter._client:
            keys_to_delete = []
            
            # Get document keys if requested
            doc_keys = []
            if request.documents:
                doc_keys = await adapter._client.keys("document:*")
                keys_to_delete.extend(doc_keys)
                
            # Get embedding keys if requested
            embed_keys = []
            if request.embeddings:
                embed_keys = await adapter._client.keys("embedding:*")
                keys_to_delete.extend(embed_keys)
                
            # Get response cache keys if requested
            cache_keys = []
            if request.cache:
                cache_keys = await adapter._client.keys("cache:*")
                keys_to_delete.extend(cache_keys)
            
            cleared_count = len(keys_to_delete)
            
            # Delete matched keys
            if keys_to_delete:
                await adapter._client.delete(*keys_to_delete)
            
            return {
                "success": True,
                "message": f"Cache cleared successfully",
                "cleared": {
                    "documents": len(doc_keys),
                    "embeddings": len(embed_keys),
                    "cache": len(cache_keys),
                    "total": cleared_count
                }
            }
        else:
            return {
                "success": False,
                "message": "Redis not available",
                "cleared": {"total": 0}
            }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/v1/admin/health")
async def health_check():
    """Run system health diagnostics."""
    try:
        results = {
            "overall": "healthy",
            "timestamp": time.time(),
            "services": {},
            "resources": {}
        }
        
        from services.autowake import check_service_health

        # Check all services
        services_healthy = True
        for svc_name in SERVICE_REGISTRY.keys():
            # Gateway is always healthy and running (it's this service itself)
            if svc_name == "gateway":
                results["services"][svc_name] = {
                    "status": "healthy",
                    "running": True
                }
            else:
                health_status = await check_service_health(svc_name)
                results["services"][svc_name] = {
                    "status": health_status,
                    "running": health_status != "stopped"
                }
                if health_status in ["unhealthy", "degraded"]:
                    services_healthy = False
        
        # Get resource status
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        results["resources"] = {
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2)
        }
        
        # Determine overall health
        if not services_healthy:
            results["overall"] = "degraded"
        if cpu_percent > 90 or memory.percent > 90:
            results["overall"] = "warning"
            
        return results
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/v1/admin/assets/reload")
async def reload_assets():
    """Force reload all assets from registry."""
    try:
        from services.asset_manager import get_asset_manager
        asset_manager = await get_asset_manager()
        # Clear existing assets and reload from disk
        asset_manager._assets = {}
        asset_manager._load_assets()
        return {
            "success": True,
            "message": "Assets reloaded successfully",
            "asset_count": len(asset_manager.get_all_assets())
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/v1/admin/services/{service_name}/inspect")
async def inspect_service(service_name: str):
    """
    Inspect service dependencies and consumers.
    
    Returns:
    - dependencies: Services this service depends on (from SERVICE_DEPENDENCIES)
    - consumers: Apps/assets that use this service
    """
    try:
        # Get declared dependencies from config
        dependencies = SERVICE_DEPENDENCIES.get(service_name, [])
        
        # Find consumers - apps/assets that use this service
        consumers = []
        try:
            from services.asset_manager import get_asset_manager
            asset_manager = await get_asset_manager()
            all_assets = asset_manager.get_all_assets()
            
            # Map service name to possible asset identifiers
            service_identifiers = [service_name]
            # Add container name mapping if exists
            container_name = CONTAINER_MAP.get(service_name)
            if container_name:
                service_identifiers.append(container_name.replace("abs-", ""))
            
            # Check each asset to see if it uses this service
            for asset in all_assets.values():
                asset_dict = asset.to_dict()
                asset_class = asset_dict.get("class", "")
                policy = asset_dict.get("policy", {})
                required_models = policy.get("required_models", [])
                served_models = policy.get("served_models", [])
                interface = asset_dict.get("interface", "")
                runtime = asset_dict.get("runtime", {})
                container = runtime.get("container", {})
                container_name_asset = container.get("name", "")
                
                # Check if this service is referenced
                is_consumer = False
                
                # Check interface match
                if interface and any(sid in interface for sid in service_identifiers):
                    is_consumer = True
                
                # Check container name match
                if container_name_asset and any(sid in container_name_asset for sid in service_identifiers):
                    is_consumer = True
                
                # Check required_models (for apps)
                if asset_class == "app" and required_models:
                    for model in required_models:
                        if any(sid in model for sid in service_identifiers):
                            is_consumer = True
                            break
                
                # Check served_models (for runtimes)
                if asset_class == "service" and served_models:
                    for model in served_models:
                        if any(sid in model for sid in service_identifiers):
                            is_consumer = True
                            break
                
                if is_consumer:
                    consumers.append({
                        "id": asset_dict.get("asset_id", ""),
                        "name": asset_dict.get("display_name") or asset_dict.get("name") or asset_dict.get("asset_id", ""),
                        "class": asset_class
                    })
        except Exception as e:
            # Log but don't fail - consumers are optional
            print(f"Warning: Failed to load consumers for {service_name}: {e}")
        
        return {
            "dependencies": dependencies,
            "consumers": consumers
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to inspect service: {str(e)}")
