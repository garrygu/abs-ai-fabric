from fastapi import APIRouter, HTTPException
from typing import Optional
from .common import get_catalog, get_registry, save_catalog

router = APIRouter()

@router.get("/v1/catalog")
async def catalog():
    return get_catalog()

@router.get("/v1/assets")
async def list_assets():
    return get_catalog().get("assets", [])

@router.get("/v1/assets/{asset_id}")
async def get_asset(asset_id: str):
    cat = get_catalog()
    for a in cat.get("assets", []):
        if a.get("id") == asset_id:
            return a
    raise HTTPException(404, f"Asset not found: {asset_id}")

@router.post("/v1/assets")
async def create_asset(asset: dict):
    cat = get_catalog()
    if asset.get("id") in [a.get("id") for a in cat.get("assets", [])]:
        raise HTTPException(409, "Asset id exists")
    
    cat.setdefault("assets", []).append(asset)
    save_catalog(cat)
    return {"status": "created", "asset": asset}
