"""
Assets Router

Provides API endpoints for asset discovery and management.
Uses both legacy catalog.json and new YAML-based asset registry.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional, List
from .common import get_catalog, get_registry, save_catalog
from services.asset_manager import get_asset_manager

router = APIRouter()

# ============================================================
# Legacy Catalog Endpoints (backward compatibility)
# ============================================================

@router.get("/v1/catalog")
async def catalog():
    """Get the full legacy catalog."""
    return get_catalog()

@router.get("/assets")
async def list_assets_legacy():
    """Legacy endpoint for listing assets from catalog.json."""
    return get_catalog().get("assets", [])

# ============================================================
# New Asset Registry API (uses AssetManager + YAML definitions)
# ============================================================

@router.get("/v1/assets")
async def list_assets():
    """
    List all assets from the new YAML-based registry.
    Returns asset definitions with interface and binding info.
    """
    manager = await get_asset_manager()
    assets = manager.get_all_assets()
    
    return [asset.to_dict() for asset in assets]

@router.get("/v1/assets/summary")
async def assets_summary():
    """Get a summary of assets by interface type."""
    manager = await get_asset_manager()
    assets = manager.get_all_assets()
    
    # Count by interface
    by_interface = {}
    for asset in assets.values():
        interface = asset.interface
        if interface not in by_interface:
            by_interface[interface] = []
        by_interface[interface].append(asset.asset_id)
    
    return {
        "total": len(assets),
        "by_interface": {k: {"count": len(v), "ids": v} for k, v in by_interface.items()}
    }

@router.get("/v1/assets/{asset_id}")
async def get_asset(asset_id: str):
    """Get a specific asset by ID."""
    manager = await get_asset_manager()
    asset = manager.get_asset(asset_id)
    
    if not asset:
        raise HTTPException(404, f"Asset not found: {asset_id}")
    
    return asset.to_dict()

@router.get("/v1/assets/interface/{interface}")
async def get_assets_by_interface(interface: str):
    """Get all assets implementing a specific interface."""
    manager = await get_asset_manager()
    assets = manager.get_assets_by_interface(interface)
    
    return [asset.to_dict() for asset in assets]

@router.get("/v1/bindings")
async def get_bindings():
    """Get current interface bindings configuration."""
    manager = await get_asset_manager()
    bindings = manager.get_bindings()
    
    # Add resolved asset info
    result = {}
    for interface, config in bindings.items():
        bound_id = config.get("implementation") if isinstance(config, dict) else config
        bound_asset = manager.get_asset(bound_id) if bound_id else None
        
        result[interface] = {
            "bound_to": bound_id,
            "asset": bound_asset.to_dict() if bound_asset else None
        }
    
    return result

@router.get("/v1/registry")
async def get_registry_index():
    """Get the assets registry index (assets.json)."""
    return get_registry()

# ============================================================
# Asset CRUD operations
# ============================================================

@router.post("/v1/assets")
async def create_asset(asset: dict):
    """Create a new asset in the legacy catalog."""
    cat = get_catalog()
    if asset.get("id") in [a.get("id") for a in cat.get("assets", [])]:
        raise HTTPException(409, "Asset id exists")
    
    cat.setdefault("assets", []).append(asset)
    save_catalog(cat)
    return {"status": "created", "asset": asset}

# ============================================================
# Asset Lifecycle Control (v1.0.1)
# ============================================================

@router.post("/v1/assets/{asset_id}/start")
async def start_asset(asset_id: str):
    """
    Start an asset (container).
    
    For containerized assets, this starts the Docker container.
    """
    manager = await get_asset_manager()
    
    # Try AssetManager first
    try:
        result = await manager.start_asset(asset_id)
        if result.get("success"):
            return result
    except Exception:
        pass
        
    # Fallback to System Services
    from services.autowake import SERVICE_REGISTRY, start_service
    if asset_id in SERVICE_REGISTRY:
        if await start_service(asset_id):
            return {"success": True, "message": f"Service {asset_id} started"}
        raise HTTPException(500, f"Failed to start service {asset_id}")

    raise HTTPException(400, "Start failed: Asset not found")

@router.post("/v1/assets/{asset_id}/stop")
async def stop_asset(asset_id: str):
    """
    Stop an asset (container).
    
    For containerized assets, this stops the Docker container gracefully.
    """
    manager = await get_asset_manager()
    
    # Try AssetManager first
    try:
        result = await manager.stop_asset(asset_id)
        if result.get("success"):
            return result
    except Exception:
        pass

    # Fallback to System Services
    from services.autowake import SERVICE_REGISTRY, stop_service
    if asset_id in SERVICE_REGISTRY:
        if await stop_service(asset_id):
            return {"success": True, "message": f"Service {asset_id} stopped"}
        raise HTTPException(500, f"Failed to stop service {asset_id}")
        
    raise HTTPException(400, "Stop failed: Asset not found")

@router.post("/v1/assets/{asset_id}/restart")
async def restart_asset(asset_id: str):
    """
    Restart an asset (container).
    
    For containerized assets, this restarts the Docker container.
    """
    manager = await get_asset_manager()
    
    # Try AssetManager first
    try:
        result = await manager.restart_asset(asset_id)
        if result.get("success"):
            return result
    except Exception:
        pass

    # Fallback to System Services
    from services.autowake import SERVICE_REGISTRY, stop_service, start_service
    if asset_id in SERVICE_REGISTRY:
        # Simple stop/start for restart
        await stop_service(asset_id)
        if await start_service(asset_id):
            return {"success": True, "message": f"Service {asset_id} restarted"}
        raise HTTPException(500, f"Failed to restart service {asset_id}")
        
    raise HTTPException(400, "Restart failed: Asset not found")

@router.get("/v1/assets/{asset_id}/status")
async def get_asset_status(asset_id: str):
    """
    Get real-time status of an asset.
    
    Returns container status for containerized assets.
    """
    manager = await get_asset_manager()
    status = await manager.get_asset_status(asset_id)
    
    if status != "unknown":
        return {"status": status}
        
    # Fallback to System Services
    from services.autowake import SERVICE_REGISTRY, check_service_status
    if asset_id in SERVICE_REGISTRY:
        svc_status = await check_service_status(asset_id)
        return {"status": svc_status}
        
    return {"status": "unknown"}

