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
    
    return [asset.to_dict() for asset in assets.values()]

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
