"""
API endpoints for Document Library functionality
"""

from fastapi import APIRouter, HTTPException, Query, Path as PathParam
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from typing import TYPE_CHECKING
import logging

# Import only for type hints, not at module level
if TYPE_CHECKING:
    from library_files_service import LibraryFilesService
    from watch_directory_service import WatchDirectoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/library", tags=["Document Library"])


# ==================== Pydantic Models ====================

class LibraryFileResponse(BaseModel):
    id: str
    watch_directory_id: Optional[str]
    file_path: str
    filename: str
    file_size: Optional[int]
    file_type: Optional[str]
    mime_type: Optional[str]
    file_hash: Optional[str]
    indexed_at: str
    indexed_status: str
    analyzed: bool
    document_id: Optional[str]
    metadata: Optional[Dict[str, Any]]


class LibraryStatsResponse(BaseModel):
    total_files: int
    analyzed_files: int
    pending_files: int
    files_by_directory: List[Dict[str, Any]]


class LibraryIndexResponse(BaseModel):
    watch_directory_id: str
    files_found: int
    files_indexed: int
    index_time: str


# ==================== API Endpoints ====================

@router.get("/files", response_model=List[LibraryFileResponse])
async def get_library_files(
    watch_directory_id: Optional[str] = Query(None, description="Filter by watch directory ID"),
    analyzed: Optional[bool] = Query(None, description="Filter by analyzed status"),
    limit: int = Query(100, description="Maximum number of results"),
    offset: int = Query(0, description="Offset for pagination")
):
    """Get library files (indexed documents)"""
    from app_integrated import library_files_service
    
    if not library_files_service:
        raise HTTPException(status_code=500, detail="Library service not initialized")
    
    try:
        files = await library_files_service.get_library_files(
            watch_directory_id=watch_directory_id,
            analyzed=analyzed,
            limit=limit,
            offset=offset
        )
        return [LibraryFileResponse(**f) for f in files]
    except Exception as e:
        logger.error(f"Error getting library files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/{watch_directory_id}")
async def index_library_directory(
    watch_directory_id: str,
    recursive: bool = Query(True, description="Search recursively")
):
    """Index files in a watch directory"""
    from app_integrated import library_files_service, watch_directory_service
    
    if not library_files_service:
        raise HTTPException(status_code=500, detail="Library service not initialized")
    if not watch_directory_service:
        raise HTTPException(status_code=500, detail="Watch directory service not initialized")
    
    try:
        # Get watch directory info
        watch_dirs = await watch_directory_service.get_watch_directories()
        watch_dir = next((wd for wd in watch_dirs if wd['id'] == watch_directory_id), None)
        
        if not watch_dir:
            raise HTTPException(status_code=404, detail="Watch directory not found")
        
        # Index files
        result = await library_files_service.index_files_in_directory(
            watch_directory_id=watch_directory_id,
            directory_path=watch_dir['path'],
            recursive=recursive if recursive is not None else watch_dir.get('recursive', True)
        )
        
        return LibraryIndexResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error indexing library directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=LibraryStatsResponse)
async def get_library_stats():
    """Get library statistics"""
    from app_integrated import library_files_service
    
    if not library_files_service:
        raise HTTPException(status_code=500, detail="Library service not initialized")
    
    try:
        stats = await library_files_service.get_library_stats()
        return LibraryStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting library stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/{library_file_id}/link")
async def link_library_file_to_document(
    library_file_id: str,
    document_id: str = Query(..., description="Document ID to link")
):
    """Link a library file to a document (after analysis)"""
    from app_integrated import library_files_service
    
    if not library_files_service:
        raise HTTPException(status_code=500, detail="Library service not initialized")
    
    try:
        result = await library_files_service.link_library_file_to_document(
            library_file_id=library_file_id,
            document_id=document_id
        )
        return {"success": result, "message": "Library file linked to document"}
    except Exception as e:
        logger.error(f"Error linking library file to document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{library_file_id}", response_model=LibraryFileResponse)
async def get_library_file(
    library_file_id: str
):
    """Get a specific library file"""
    from app_integrated import library_files_service
    
    if not library_files_service:
        raise HTTPException(status_code=500, detail="Library service not initialized")
    
    try:
        files = await library_files_service.get_library_files()
        library_file = next((f for f in files if f['id'] == library_file_id), None)
        
        if not library_file:
            raise HTTPException(status_code=404, detail="Library file not found")
        
        return LibraryFileResponse(**library_file)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting library file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions removed - services are imported directly in each endpoint

