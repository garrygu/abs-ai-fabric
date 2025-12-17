from fastapi import APIRouter, HTTPException, Query
from typing import Optional

# Import the existing store_service logic
# We need to adapt it because store_service.py is a module in the parent directory
# But app.py imported it as 'from store_service import StoreService'
# We should probably import it similarly
try:
    from store_service import StoreService
except ImportError:
    import sys
    sys.path.append("..")
    from store_service import StoreService

router = APIRouter()
store_service = None
try:
    store_service = StoreService()
except:
    pass

@router.get("/v1/store/apps")
async def get_store_apps(
    source: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    if not store_service:
        raise HTTPException(503, "Store service unavailable")
    
    apps = store_service.aggregate_store_apps()
    # ... filters (simplified) ...
    if category:
        apps = [a for a in apps if a.get("category", "").lower() == category.lower()]
    
    return {"apps": apps, "total": len(apps)}

@router.post("/v1/store/apps/{app_id}/install")
async def install_app(app_id: str, install_dependencies: bool = False):
    if not store_service:
        raise HTTPException(503, "Store service unavailable")
    return store_service.install_app(app_id, install_dependencies=install_dependencies)
