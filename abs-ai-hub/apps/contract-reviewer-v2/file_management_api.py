"""
File Management API
Comprehensive API for file-based storage, report generation, and document management
"""

import os
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Depends, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import logging
import asyncio
import io

from file_based_storage_service import (
    FileBasedStorageService, FileType, StorageConfig, FileMetadata, StorageTier
)
from report_generation_service import (
    ReportGenerationService, ReportRequest, ReportFormat, ReportType, ReportTemplate
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class FileUploadRequest(BaseModel):
    file_type: str
    client_id: Optional[str] = None
    document_id: Optional[str] = None
    analysis_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    version: int = 1

class FileRetrieveRequest(BaseModel):
    file_id: str
    include_metadata: bool = True

class FileVersionRequest(BaseModel):
    file_id: str
    version_comment: Optional[str] = None

class ArchiveRequest(BaseModel):
    file_ids: List[str]
    archive_name: Optional[str] = None
    compression_level: int = 6

class ReportGenerationRequest(BaseModel):
    report_id: str
    report_type: str
    format: str
    document_ids: List[str]
    analysis_ids: List[str]
    client_id: Optional[str] = None
    template_id: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None
    include_charts: bool = True
    include_appendix: bool = True

class StorageConfigRequest(BaseModel):
    base_path: str
    max_file_size: int = 100 * 1024 * 1024
    max_files_per_directory: int = 10000
    enable_compression: bool = True
    enable_encryption: bool = False
    retention_days: int = 2555
    backup_enabled: bool = True
    backup_frequency_days: int = 30
    archive_enabled: bool = True
    archive_frequency_days: int = 90

# Global services
storage_service: Optional[FileBasedStorageService] = None
report_service: Optional[ReportGenerationService] = None

# Dependency injection
async def get_storage_service() -> FileBasedStorageService:
    """Get or create storage service instance"""
    global storage_service
    
    if storage_service is None:
        config = StorageConfig(
            base_path=os.getenv("FILE_STORAGE_PATH", "/data/file_storage"),
            max_file_size=int(os.getenv("MAX_FILE_SIZE", "100")) * 1024 * 1024,
            enable_compression=os.getenv("ENABLE_COMPRESSION", "true").lower() == "true"
        )
        storage_service = FileBasedStorageService(config)
    
    return storage_service

async def get_report_service() -> ReportGenerationService:
    """Get or create report service instance"""
    global report_service, storage_service
    
    if report_service is None:
        if storage_service is None:
            storage_service = await get_storage_service()
        report_service = ReportGenerationService(storage_service)
    
    return report_service

# API Router
router = APIRouter(prefix="/api/files", tags=["file-management"])

# ==================== FILE OPERATIONS ====================

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Query("document", description="File type"),
    client_id: Optional[str] = Query(None, description="Client identifier"),
    document_id: Optional[str] = Query(None, description="Document identifier"),
    analysis_id: Optional[str] = Query(None, description="Analysis identifier"),
    metadata: Optional[str] = Query(None, description="JSON metadata"),
    version: int = Query(1, description="File version"),
    storage_svc: FileBasedStorageService = Depends(get_storage_service)
):
    """
    Upload a file with metadata
    
    Args:
        file: File to upload
        file_type: Type of file (document, analysis_result, report_pdf, etc.)
        client_id: Client identifier
        document_id: Document identifier
        analysis_id: Analysis identifier
        metadata: JSON string of additional metadata
        version: File version number
        
    Returns:
        File metadata
    """
    try:
        logger.info(f"Uploading file: {file.filename} (type: {file_type})")
        
        # Parse metadata
        parsed_metadata = None
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON")
        
        # Validate file type
        try:
            file_type_enum = FileType(file_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file_type}")
        
        # Read file content
        file_content = await file.read()
        
        # Store file
        file_metadata = await storage_svc.store_file(
            file_data=file_content,
            file_type=file_type_enum,
            original_filename=file.filename,
            client_id=client_id,
            document_id=document_id,
            analysis_id=analysis_id,
            metadata=parsed_metadata,
            version=version
        )
        
        logger.info(f"✅ File uploaded: {file_metadata.file_id}")
        return {
            "file_id": file_metadata.file_id,
            "original_filename": file_metadata.original_filename,
            "file_type": file_metadata.file_type.value,
            "file_size": file_metadata.file_size,
            "file_path": file_metadata.file_path,
            "checksum": file_metadata.checksum,
            "created_at": file_metadata.created_at.isoformat(),
            "version": file_metadata.version,
            "metadata": file_metadata.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    storage_svc: FileBasedStorageService = Depends(get_storage_service)
):
    """
    Download a file by ID
    
    Args:
        file_id: File identifier
        
    Returns:
        File content
    """
    try:
        logger.info(f"Downloading file: {file_id}")
        
        # Retrieve file
        file_content, file_metadata = await storage_svc.retrieve_file(file_id)
        
        # Create response
        media_type = file_metadata.mime_type or "application/octet-stream"
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={file_metadata.original_filename}",
                "Content-Length": str(len(file_content))
            }
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"❌ Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info/{file_id}")
async def get_file_info(
    file_id: str,
    storage_svc: FileBasedStorageService = Depends(get_storage_service)
):
    """
    Get file metadata by ID
    
    Args:
        file_id: File identifier
        
    Returns:
        File metadata
    """
    try:
        logger.info(f"Getting file info: {file_id}")
        
        # Get file metadata
        file_metadata = await storage_svc._get_file_metadata(file_id)
        if not file_metadata:
            raise HTTPException(status_code=404, detail="File not found")
        
        return {
            "file_id": file_metadata.file_id,
            "original_filename": file_metadata.original_filename,
            "file_type": file_metadata.file_type.value,
            "storage_tier": file_metadata.storage_tier.value,
            "file_size": file_metadata.file_size,
            "mime_type": file_metadata.mime_type,
            "checksum": file_metadata.checksum,
            "created_at": file_metadata.created_at.isoformat(),
            "modified_at": file_metadata.modified_at.isoformat(),
            "accessed_at": file_metadata.accessed_at.isoformat(),
            "version": file_metadata.version,
            "parent_document_id": file_metadata.parent_document_id,
            "analysis_id": file_metadata.analysis_id,
            "client_id": file_metadata.client_id,
            "tags": file_metadata.tags,
            "metadata": file_metadata.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting file info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete/{file_id}")
async def delete_file(
    file_id: str,
    permanent: bool = Query(False, description="Permanently delete (vs move to trash)"),
    storage_svc: FileBasedStorageService = Depends(get_storage_service)
):
    """
    Delete a file
    
    Args:
        file_id: File identifier
        permanent: Whether to permanently delete
        
    Returns:
        Deletion confirmation
    """
    try:
        logger.info(f"Deleting file: {file_id} (permanent: {permanent})")
        
        # Delete file
        success = await storage_svc.delete_file(file_id, permanent=permanent)
        
        if success:
            return {"message": f"File {file_id} deleted successfully", "permanent": permanent}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file")
        
    except Exception as e:
        logger.error(f"❌ Error deleting file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== FILE VERSIONING ====================

@router.post("/version/{file_id}")
async def create_file_version(
    file_id: str,
    request: FileVersionRequest,
    storage_svc: FileBasedStorageService = Depends(get_storage_service)
):
    """
    Create a new version of a file
    
    Args:
        file_id: Original file identifier
        request: Version creation request
        
    Returns:
        New file version metadata
    """
    try:
        logger.info(f"Creating new version for file: {file_id}")
        
        # Get original file content
        file_content, original_metadata = await storage_svc.retrieve_file(file_id)
        
        # Create new version
        new_metadata = await storage_svc.create_file_version(
            file_id=file_id,
            new_file_data=file_content,
            version_comment=request.version_comment
        )
        
        logger.info(f"✅ File version created: {new_metadata.file_id}")
        return {
            "file_id": new_metadata.file_id,
            "version": new_metadata.version,
            "version_comment": request.version_comment,
            "created_at": new_metadata.created_at.isoformat(),
            "parent_file_id": file_id
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Original file not found")
    except Exception as e:
        logger.error(f"❌ Error creating file version: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/versions/{document_id}")
async def get_file_versions(
    document_id: str,
    storage_svc: FileBasedStorageService = Depends(get_storage_service)
):
    """
    Get all versions of a file
    
    Args:
        document_id: Document identifier
        
    Returns:
        List of file versions
    """
    try:
        logger.info(f"Getting file versions: {document_id}")
        
        # Get file versions
        versions = await storage_svc.get_file_versions(document_id)
        
        # Format response
        version_list = []
        for version in versions:
            version_list.append({
                "file_id": version.file_id,
                "version": version.version,
                "original_filename": version.original_filename,
                "file_size": version.file_size,
                "created_at": version.created_at.isoformat(),
                "modified_at": version.modified_at.isoformat(),
                "version_comment": version.metadata.get("version_comment"),
                "parent_file_id": version.metadata.get("parent_file_id")
            })
        
        return {
            "document_id": document_id,
            "versions": version_list,
            "total_versions": len(version_list)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting file versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ARCHIVING ====================

@router.post("/archive")
async def create_archive(
    request: ArchiveRequest,
    storage_svc: FileBasedStorageService = Depends(get_storage_service)
):
    """
    Create an archive of multiple files
    
    Args:
        request: Archive creation request
        
    Returns:
        Archive metadata
    """
    try:
        logger.info(f"Creating archive with {len(request.file_ids)} files")
        
        # Create archive
        archive_metadata = await storage_svc.archive_files(
            file_ids=request.file_ids,
            archive_name=request.archive_name,
            compression_level=request.compression_level
        )
        
        logger.info(f"✅ Archive created: {archive_metadata.file_id}")
        return {
            "archive_id": archive_metadata.file_id,
            "archive_name": request.archive_name or "archive",
            "archived_files": len(request.file_ids),
            "compression_level": request.compression_level,
            "file_size": archive_metadata.file_size,
            "created_at": archive_metadata.created_at.isoformat(),
            "file_ids": request.file_ids
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating archive: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract/{archive_id}")
async def extract_archive(
    archive_id: str,
    extract_to: Optional[str] = Query(None, description="Directory to extract to"),
    storage_svc: FileBasedStorageService = Depends(get_storage_service)
):
    """
    Extract files from an archive
    
    Args:
        archive_id: Archive file identifier
        extract_to: Directory to extract to
        
    Returns:
        List of extracted files
    """
    try:
        logger.info(f"Extracting archive: {archive_id}")
        
        # Extract archive
        extract_path = Path(extract_to) if extract_to else None
        extracted_files = await storage_svc.extract_archive(archive_id, extract_path)
        
        # Format response
        file_list = []
        for file_metadata in extracted_files:
            file_list.append({
                "file_id": file_metadata.file_id,
                "original_filename": file_metadata.original_filename,
                "file_type": file_metadata.file_type.value,
                "file_size": file_metadata.file_size,
                "file_path": file_metadata.file_path,
                "created_at": file_metadata.created_at.isoformat()
            })
        
        logger.info(f"✅ Archive extracted: {len(extracted_files)} files")
        return {
            "archive_id": archive_id,
            "extracted_files": file_list,
            "total_files": len(extracted_files),
            "extract_path": str(extract_path) if extract_path else "temp directory"
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archive not found")
    except Exception as e:
        logger.error(f"❌ Error extracting archive: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== REPORT GENERATION ====================

@router.post("/reports/generate")
async def generate_report(
    request: ReportGenerationRequest,
    background_tasks: BackgroundTasks,
    report_svc: ReportGenerationService = Depends(get_report_service),
    storage_svc: FileBasedStorageService = Depends(get_storage_service)
):
    """
    Generate a comprehensive report
    
    Args:
        request: Report generation request
        background_tasks: Background task handler
        
    Returns:
        Report generation status
    """
    try:
        logger.info(f"Generating report: {request.report_id}")
        
        # Validate report type and format
        try:
            report_type = ReportType(request.report_type)
            report_format = ReportFormat(request.format)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid report type or format: {e}")
        
        # Create report request
        report_request = ReportRequest(
            report_id=request.report_id,
            report_type=report_type,
            format=report_format,
            document_ids=request.document_ids,
            analysis_ids=request.analysis_ids,
            client_id=request.client_id,
            template_id=request.template_id,
            custom_data=request.custom_data,
            include_charts=request.include_charts,
            include_appendix=request.include_appendix
        )
        
        # Get analysis data (simplified - in practice, you'd fetch from database)
        analysis_data = {
            "summary": {
                "summary": "Generated analysis summary",
                "key_points": ["Key point 1", "Key point 2", "Key point 3"]
            },
            "risks": [
                {"level": "low", "description": "Low risk item"},
                {"level": "medium", "description": "Medium risk item"}
            ],
            "recommendations": [
                "Recommendation 1",
                "Recommendation 2",
                "Recommendation 3"
            ],
            "citations": [
                "Citation 1",
                "Citation 2"
            ]
        }
        
        # Get document metadata (simplified)
        document_metadata = {
            "original_filename": "sample_document.pdf",
            "file_size": 102400,
            "upload_timestamp": datetime.now().isoformat()
        }
        
        # Generate report
        report_metadata = await report_svc.generate_report(
            request=report_request,
            analysis_data=analysis_data,
            document_metadata=document_metadata
        )
        
        logger.info(f"✅ Report generated: {report_metadata.file_id}")
        return {
            "report_id": request.report_id,
            "file_id": report_metadata.file_id,
            "report_type": request.report_type,
            "format": request.format,
            "file_size": report_metadata.file_size,
            "generated_at": report_metadata.created_at.isoformat(),
            "download_url": f"/api/files/download/{report_metadata.file_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reports/templates")
async def list_report_templates(
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    report_svc: ReportGenerationService = Depends(get_report_service)
):
    """
    List available report templates
    
    Args:
        report_type: Filter by report type
        
    Returns:
        List of available templates
    """
    try:
        logger.info("Listing report templates")
        
        # Get templates
        report_type_enum = None
        if report_type:
            try:
                report_type_enum = ReportType(report_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid report type: {report_type}")
        
        templates = await report_svc.list_templates(report_type_enum)
        
        # Format response
        template_list = []
        for template in templates:
            template_list.append({
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "report_type": template.report_type.value,
                "format": template.format.value,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat(),
                "is_active": template.is_active
            })
        
        return {
            "templates": template_list,
            "total_templates": len(template_list),
            "filtered_by_type": report_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error listing templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== STORAGE MANAGEMENT ====================

@router.get("/storage/stats")
async def get_storage_stats(
    storage_svc: FileBasedStorageService = Depends(get_storage_service),
    report_svc: ReportGenerationService = Depends(get_report_service)
):
    """
    Get comprehensive storage statistics
    
    Returns:
        Storage and report statistics
    """
    try:
        logger.info("Getting storage statistics")
        
        # Get storage stats
        storage_stats = await storage_svc.get_storage_stats()
        
        # Get report stats
        report_stats = await report_svc.get_report_stats()
        
        return {
            "storage": storage_stats,
            "reports": report_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting storage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/storage/cleanup")
async def cleanup_storage(
    days_old: int = Query(30, description="Clean up files older than N days"),
    storage_svc: FileBasedStorageService = Depends(get_storage_service)
):
    """
    Clean up old temporary files
    
    Args:
        days_old: Clean up files older than N days
        
    Returns:
        Cleanup results
    """
    try:
        logger.info(f"Cleaning up files older than {days_old} days")
        
        # Clean up old files
        cleaned_count = await storage_svc.cleanup_old_files(days_old)
        
        return {
            "cleaned_files": cleaned_count,
            "days_old": days_old,
            "cleanup_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error cleaning up storage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage/health")
async def storage_health_check(
    storage_svc: FileBasedStorageService = Depends(get_storage_service)
):
    """
    Health check for storage service
    
    Returns:
        Health status
    """
    try:
        # Get storage stats to test service
        stats = await storage_svc.get_storage_stats()
        
        return {
            "status": "healthy",
            "service": "file-based-storage",
            "total_files": stats["total_files"],
            "total_size_mb": stats["total_size_mb"],
            "base_path": stats["base_path"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Storage health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "file-based-storage",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ==================== INTEGRATION WITH MAIN APP ====================

def integrate_file_management(app):
    """
    Integrate file management API with main FastAPI app
    
    Usage in app.py:
        from file_management_api import integrate_file_management
        integrate_file_management(app)
    """
    app.include_router(router)
    
    # Add startup event to initialize services
    @app.on_event("startup")
    async def startup_event():
        global storage_service, report_service
        
        try:
            # Initialize storage service
            config = StorageConfig(
                base_path=os.getenv("FILE_STORAGE_PATH", "/data/file_storage"),
                max_file_size=int(os.getenv("MAX_FILE_SIZE", "100")) * 1024 * 1024,
                enable_compression=os.getenv("ENABLE_COMPRESSION", "true").lower() == "true"
            )
            storage_service = FileBasedStorageService(config)
            
            # Initialize report service
            report_service = ReportGenerationService(storage_service)
            
            logger.info("✅ File management services initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize file management services: {e}")
    
    # Add shutdown event to cleanup
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("🛑 File management services shutdown")


# ==================== EXAMPLE INTEGRATION ====================

"""
To integrate with Contract Reviewer v2, add this to app.py:

from file_management_api import integrate_file_management

# After creating your FastAPI app
integrate_file_management(app)

This will add all the file management endpoints to your existing app.
"""
