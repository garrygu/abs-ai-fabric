"""
Attract Mode Router

Provides API endpoints for Attract Mode telemetry, Scene C control,
and real-time system state monitoring.

Implements the contracts defined in:
- Attract Mode Technical Requirements & Control Specification
- Attract Mode 1-Page Technical Architecture
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import time
import psutil
import httpx

from config import OLLAMA_BASE
from services.asset_manager import get_asset_manager

router = APIRouter(prefix="/v1/attract", tags=["attract"])


# =============================================================================
# Pydantic Models (matching spec contracts)
# =============================================================================

class SceneCRequest(BaseModel):
    """Scene C activity request from Scene Controller."""
    scene_id: str = "sceneC"
    requested_intent: str = "LOAD_ACTIVITY"
    visual_context: Optional[Dict[str, Any]] = None


class SceneCResponse(BaseModel):
    """Control Plane decision response."""
    approved: bool
    mode: str  # AUTO, LIVE, SHOWCASE
    constraints: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None


class ActionProgress(BaseModel):
    """Backend action progress update."""
    action_id: str
    status: str  # IN_PROGRESS, COMPLETED, ABORTED
    progress_pct: int = 0
    fallback: Optional[str] = None
    reason: Optional[str] = None
    telemetry_hint: Optional[Dict[str, Any]] = None


# =============================================================================
# Telemetry Endpoint (Phase 1)
# =============================================================================

@router.get("/telemetry")
async def get_attract_telemetry():
    """
    Get unified telemetry snapshot for Attract Mode.
    
    Aggregates GPU, system, and model state into a single response.
    Spec: Update rate ≥5 Hz, missing fields allowed, never blocks UI.
    """
    try:
        # Get GPU metrics
        gpu_data = await _get_gpu_metrics()
        
        # Get system metrics
        system_data = _get_system_metrics()
        
        # Get model states
        models_data = await _get_model_states()
        
        return {
            "timestamp": int(time.time()),
            "gpu": gpu_data,
            "system": system_data,
            "models": models_data
        }
    except Exception as e:
        # Spec: Never fail visibly - return partial data
        return {
            "timestamp": int(time.time()),
            "gpu": {"utilization_pct": 0, "temperature_c": 0, "vram": {"used_mb": 0, "total_mb": 1}},
            "system": {"ram_used_mb": 0, "ram_total_mb": 1, "uptime_seconds": 0},
            "models": [],
            "_error": str(e)
        }


async def _get_gpu_metrics() -> Dict[str, Any]:
    """Fetch GPU metrics from gpu_metrics_server or nvidia-smi fallback."""
    try:
        # Try gpu_metrics_server first (running on host at :8083)
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.get("http://localhost:8083/gpu-metrics")
            if response.status_code == 200:
                data = response.json()
                gpus = data.get("gpus", [])
                if gpus:
                    gpu = gpus[0]  # Primary GPU for Attract Mode
                    return {
                        "utilization_pct": gpu.get("utilization", 0),
                        "temperature_c": gpu.get("temperature", 0),
                        "vram": {
                            "used_mb": gpu.get("memory_used_mb", 0),
                            "total_mb": gpu.get("memory_total_mb", 1)
                        }
                    }
    except Exception:
        pass
    
    # Fallback: nvidia-smi
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = [p.strip() for p in result.stdout.strip().split('\n')[0].split(',')]
            if len(parts) >= 4:
                return {
                    "utilization_pct": float(parts[0]) if parts[0] else 0,
                    "temperature_c": float(parts[3]) if parts[3] else 0,
                    "vram": {
                        "used_mb": float(parts[1]) if parts[1] else 0,
                        "total_mb": float(parts[2]) if parts[2] else 1
                    }
                }
    except Exception:
        pass
    
    return {"utilization_pct": 0, "temperature_c": 0, "vram": {"used_mb": 0, "total_mb": 1}}


def _get_system_metrics() -> Dict[str, Any]:
    """Get system RAM and uptime."""
    try:
        memory = psutil.virtual_memory()
        boot_time = psutil.boot_time()
        uptime = int(time.time() - boot_time)
        
        return {
            "ram_used_mb": int(memory.used / (1024 * 1024)),
            "ram_total_mb": int(memory.total / (1024 * 1024)),
            "uptime_seconds": uptime
        }
    except Exception:
        return {"ram_used_mb": 0, "ram_total_mb": 1, "uptime_seconds": 0}


async def _get_model_states() -> List[Dict[str, Any]]:
    """Get installed models and their current states."""
    models = []
    
    try:
        # Get registered models from asset manager
        manager = await get_asset_manager()
        llm_assets = manager.get_assets_by_interface("llm-runtime")
        
        # Get running models from Ollama
        running_models = set()
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{OLLAMA_BASE.rstrip('/')}/api/ps")
                if response.status_code == 200:
                    data = response.json()
                    for m in data.get("models", []):
                        name = m.get("name", "")
                        running_models.add(name)
                        if ":" in name:
                            running_models.add(name.split(":")[0])
        except Exception:
            pass
        
        # Build model list with states
        for asset in llm_assets:
            model_id = asset.asset_id
            model_class = "llm" if asset.interface == "llm-runtime" else "auxiliary"
            
            # Determine state
            is_running = any(
                model_id.lower().replace("_", "-") in rm.lower().replace("_", "-")
                for rm in running_models
            )
            state = "RUNNING" if is_running else "READY"
            
            models.append({
                "model_id": model_id,
                "class": model_class,
                "state": state
            })
    except Exception:
        pass
    
    return models


# =============================================================================
# Scene C Control Endpoints (Phase 2)
# =============================================================================

# In-memory state (simple for now - could be Redis-backed later)
_scene_c_state = {
    "current_mode": "AUTO",
    "active_action": None,
    "last_request_time": 0
}

# Safety thresholds
THERMAL_THRESHOLD_C = 80
VRAM_THRESHOLD_PCT = 90


@router.post("/sceneC/request", response_model=SceneCResponse)
async def request_scene_c_activity(request: SceneCRequest):
    """
    Request Scene C backend activity.
    
    Control Plane evaluates policy and returns approved mode.
    This is a REQUEST, not a command - may be downgraded or rejected.
    """
    global _scene_c_state
    
    _scene_c_state["last_request_time"] = time.time()
    
    # Get current system state
    gpu = await _get_gpu_metrics()
    
    # Safety checks
    temperature = gpu.get("temperature_c", 0)
    vram = gpu.get("vram", {})
    vram_used_pct = (vram.get("used_mb", 0) / max(vram.get("total_mb", 1), 1)) * 100
    
    # Thermal gate
    if temperature > THERMAL_THRESHOLD_C:
        _scene_c_state["current_mode"] = "AUTO"
        return SceneCResponse(
            approved=False,
            mode="AUTO",
            reason=f"GPU temperature above threshold ({temperature}°C > {THERMAL_THRESHOLD_C}°C)"
        )
    
    # VRAM gate
    if vram_used_pct > VRAM_THRESHOLD_PCT:
        _scene_c_state["current_mode"] = "AUTO"
        return SceneCResponse(
            approved=False,
            mode="AUTO",
            reason=f"VRAM usage above threshold ({vram_used_pct:.0f}% > {VRAM_THRESHOLD_PCT}%)"
        )
    
    # Determine approved mode based on request and conditions
    desired_intensity = request.visual_context.get("desired_intensity", "LOW") if request.visual_context else "LOW"
    
    if desired_intensity == "HIGH":
        # Could approve LIVE mode if conditions are good
        _scene_c_state["current_mode"] = "LIVE"
        return SceneCResponse(
            approved=True,
            mode="LIVE",
            constraints={
                "max_duration_seconds": 12,
                "max_vram_mb": int(vram.get("total_mb", 98304) * 0.7)
            },
            reason="Thermal and memory conditions nominal"
        )
    else:
        # Default to AUTO (telemetry-only)
        _scene_c_state["current_mode"] = "AUTO"
        return SceneCResponse(
            approved=True,
            mode="AUTO",
            reason="Telemetry-driven mode active"
        )


@router.get("/sceneC/status")
async def get_scene_c_status():
    """
    Get current Scene C mode and any active action status.
    """
    return {
        "current_mode": _scene_c_state["current_mode"],
        "active_action": _scene_c_state["active_action"],
        "last_request_time": _scene_c_state["last_request_time"],
        "thresholds": {
            "thermal_c": THERMAL_THRESHOLD_C,
            "vram_pct": VRAM_THRESHOLD_PCT
        }
    }


@router.post("/sceneC/showcase/enable")
async def enable_showcase_mode():
    """
    Manually enable SHOWCASE mode (staff-initiated only).
    
    Per spec: Manual enablement only, staff supervision required.
    """
    global _scene_c_state
    
    # Pre-flight health checks
    gpu = await _get_gpu_metrics()
    temperature = gpu.get("temperature_c", 0)
    
    if temperature > THERMAL_THRESHOLD_C - 10:  # Stricter for SHOWCASE
        raise HTTPException(
            status_code=400,
            detail=f"GPU temperature too high for SHOWCASE mode ({temperature}°C)"
        )
    
    _scene_c_state["current_mode"] = "SHOWCASE"
    
    return {
        "success": True,
        "mode": "SHOWCASE",
        "message": "SHOWCASE mode enabled - staff supervision required"
    }


@router.post("/sceneC/reset")
async def reset_scene_c():
    """
    Reset Scene C to AUTO mode.
    """
    global _scene_c_state
    
    _scene_c_state["current_mode"] = "AUTO"
    _scene_c_state["active_action"] = None
    
    return {"success": True, "mode": "AUTO"}
