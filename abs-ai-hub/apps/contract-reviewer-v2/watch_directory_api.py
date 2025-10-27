"""
API endpoints for managing watch directories
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path as PathParam
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from watch_directory_service import WatchDirectoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/watch-directories", tags=["Watch Directories"])


# ==================== Pydantic Models ====================

class WatchDirectoryCreate(BaseModel):
    path: str
    path_type: str = "local"  # local, network, cloud
    enabled: bool = True
    recursive: bool = True
    file_patterns: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class WatchDirectoryResponse(BaseModel):
    id: str
    path: str
    path_type: str
    enabled: bool
    recursive: bool
    file_patterns: List[str]
    metadata: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str
    last_scan_at: Optional[str]
    last_error: Optional[str]


class WatchDirectoryUpdate(BaseModel):
    enabled: Optional[bool] = None
    recursive: Optional[bool] = None
    file_patterns: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


# ==================== API Endpoints ====================

@router.post("/", response_model=WatchDirectoryResponse)
async def create_watch_directory(
    watch_dir: WatchDirectoryCreate,
    service: WatchDirectoryService = Depends()
):
    """Add a new watch directory"""
    try:
        watch_id = await service.add_watch_directory(
            path=watch_dir.path,
            path_type=watch_dir.path_type,
            enabled=watch_dir.enabled,
            recursive=watch_dir.recursive,
            file_patterns=watch_dir.file_patterns,
            metadata=watch_dir.metadata
        )
        
        # Fetch the created directory
        watch_dirs = await service.get_watch_directories()
        for wd in watch_dirs:
            if wd['id'] == watch_id:
                return WatchDirectoryResponse(**wd)
        
        raise HTTPException(status_code=404, detail="Watch directory created but not found")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating watch directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[WatchDirectoryResponse])
async def list_watch_directories(
    enabled_only: bool = Query(False, description="Show only enabled directories"),
    service: WatchDirectoryService = Depends()
):
    """List all watch directories"""
    try:
        watch_dirs = await service.get_watch_directories(enabled_only=enabled_only)
        return [WatchDirectoryResponse(**wd) for wd in watch_dirs]
    except Exception as e:
        logger.error(f"Error listing watch directories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{watch_id}", response_model=WatchDirectoryResponse)
async def get_watch_directory(
    watch_id: str,
    service: WatchDirectoryService = Depends()
):
    """Get a specific watch directory"""
    try:
        watch_dirs = await service.get_watch_directories()
        for wd in watch_dirs:
            if wd['id'] == watch_id:
                return WatchDirectoryResponse(**wd)
        
        raise HTTPException(status_code=404, detail="Watch directory not found")
    except Exception as e:
        logger.error(f"Error getting watch directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{watch_id}")
async def delete_watch_directory(
    watch_id: str,
    service: WatchDirectoryService = Depends()
):
    """Remove a watch directory"""
    try:
        result = await service.remove_watch_directory(watch_id)
        return {"success": result, "message": "Watch directory removed"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting watch directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{watch_id}/toggle")
async def toggle_watch_directory(
    watch_id: str,
    enabled: bool = Query(..., description="Enable or disable"),
    service: WatchDirectoryService = Depends()
):
    """Enable or disable a watch directory"""
    try:
        result = await service.toggle_watch_directory(watch_id, enabled)
        return {"success": result, "message": f"Watch directory {'enabled' if enabled else 'disabled'}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error toggling watch directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{watch_id}/scan")
async def scan_watch_directory(
    watch_id: str,
    service: WatchDirectoryService = Depends()
):
    """Manually scan a watch directory for new files"""
    try:
        result = await service.manual_scan(watch_id)
        return {
            "success": True,
            "message": f"Scanned {result['files_found']} files, processed {result['processed']}",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error scanning watch directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{watch_id}/stats")
async def get_watch_directory_stats(
    watch_id: str,
    service: WatchDirectoryService = Depends()
):
    """Get statistics for a watch directory"""
    try:
        # This would need to be implemented in the service
        # For now, return basic info
        watch_dirs = await service.get_watch_directories()
        for wd in watch_dirs:
            if wd['id'] == watch_id:
                return {
                    "watch_id": watch_id,
                    "path": wd['path'],
                    "enabled": wd['enabled'],
                    "last_scan_at": wd.get('last_scan_at'),
                    "processed_files_count": len(wd.get('processed_files', [])),
                    "last_error": wd.get('last_error')
                }
        
        raise HTTPException(status_code=404, detail="Watch directory not found")
    except Exception as e:
        logger.error(f"Error getting watch directory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Helper Functions ====================

def get_watch_directory_service() -> WatchDirectoryService:
    """Dependency to get watch directory service"""
    # This should be initialized in app_integrated.py
    # For now, this is a placeholder
    pass

