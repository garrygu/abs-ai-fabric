"""
FastAPI REST API endpoints for Document Management
Provides HTTP endpoints for CRUD operations on documents and analysis results
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import asyncio
from pathlib import Path
import tempfile
import os

from document_service import DocumentService


# ==================== PYDANTIC MODELS ====================

class DocumentCreate(BaseModel):
    original_filename: str
    metadata: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

class DocumentUpdate(BaseModel):
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AnalysisResultCreate(BaseModel):
    document_id: str
    analysis_type: str
    analysis_data: Dict[str, Any]
    model_used: Optional[str] = None
    processing_time_ms: Optional[int] = None
    user_id: Optional[str] = None

class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    file_type: str
    mime_type: Optional[str]
    upload_timestamp: str
    analysis_timestamp: Optional[str]
    status: str
    metadata: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str

class AnalysisResultResponse(BaseModel):
    id: str
    document_id: str
    analysis_type: str
    analysis_data: Dict[str, Any]
    analysis_timestamp: str
    model_used: Optional[str]
    processing_time_ms: Optional[int]
    status: str
    created_at: str

class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total_count: int
    limit: int
    offset: int
    has_more: bool

class StatisticsResponse(BaseModel):
    document_stats: Dict[str, Any]
    analysis_stats: List[Dict[str, Any]]


# ==================== DEPENDENCY INJECTION ====================

# Global document service instance
_document_service: Optional[DocumentService] = None

async def get_document_service() -> DocumentService:
    """Get or create document service instance"""
    global _document_service
    
    if _document_service is None:
        _document_service = DocumentService()
        await _document_service.initialize()
    
    return _document_service


# ==================== API ROUTER ====================

router = APIRouter(prefix="/api/documents", tags=["documents"])


# ==================== DOCUMENT ENDPOINTS ====================

@router.post("/", response_model=DocumentResponse)
async def create_document(
    file: UploadFile = File(...),
    metadata: Optional[str] = Query(None, description="JSON metadata as string"),
    user_id: Optional[str] = Query(None),
    doc_service: DocumentService = Depends(get_document_service)
):
    """Upload and create a new document"""
    try:
        # Parse metadata if provided
        parsed_metadata = None
        if metadata:
            import json
            parsed_metadata = json.loads(metadata)
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Create document record
            document = await doc_service.create_document(
                file_path=temp_file_path,
                original_filename=file.filename,
                metadata=parsed_metadata,
                user_id=user_id
            )
            
            return DocumentResponse(**document)
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")


@router.get("/", response_model=DocumentListResponse)
async def get_documents(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    order_by: str = Query("upload_timestamp"),
    order_direction: str = Query("DESC"),
    doc_service: DocumentService = Depends(get_document_service)
):
    """Get a list of documents with pagination"""
    try:
        documents, total_count = await doc_service.get_documents(
            limit=limit,
            offset=offset,
            status=status,
            user_id=user_id,
            order_by=order_by,
            order_direction=order_direction
        )
        
        return DocumentListResponse(
            documents=[DocumentResponse(**doc) for doc in documents],
            total_count=total_count,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total_count
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    doc_service: DocumentService = Depends(get_document_service)
):
    """Get a specific document by ID"""
    try:
        document = await doc_service.get_document_by_id(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponse(**document)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    updates: DocumentUpdate,
    user_id: Optional[str] = Query(None),
    doc_service: DocumentService = Depends(get_document_service)
):
    """Update a document"""
    try:
        # Convert Pydantic model to dict, excluding None values
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        
        if not update_dict:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        document = await doc_service.update_document(
            document_id=document_id,
            updates=update_dict,
            user_id=user_id
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponse(**document)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    user_id: Optional[str] = Query(None),
    delete_file: bool = Query(True),
    doc_service: DocumentService = Depends(get_document_service)
):
    """Delete a document"""
    try:
        success = await doc_service.delete_document(
            document_id=document_id,
            user_id=user_id,
            delete_file=delete_file
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


# ==================== ANALYSIS RESULT ENDPOINTS ====================

@router.post("/analysis", response_model=AnalysisResultResponse)
async def create_analysis_result(
    analysis_data: AnalysisResultCreate,
    doc_service: DocumentService = Depends(get_document_service)
):
    """Create a new analysis result"""
    try:
        analysis = await doc_service.create_analysis_result(
            document_id=analysis_data.document_id,
            analysis_type=analysis_data.analysis_type,
            analysis_data=analysis_data.analysis_data,
            model_used=analysis_data.model_used,
            processing_time_ms=analysis_data.processing_time_ms,
            user_id=analysis_data.user_id
        )
        
        return AnalysisResultResponse(**analysis)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create analysis result: {str(e)}")


@router.get("/analysis/{analysis_id}", response_model=AnalysisResultResponse)
async def get_analysis_result(
    analysis_id: str,
    doc_service: DocumentService = Depends(get_document_service)
):
    """Get a specific analysis result by ID"""
    try:
        analysis = await doc_service.get_analysis_result_by_id(analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis result not found")
        
        return AnalysisResultResponse(**analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analysis result: {str(e)}")


@router.get("/{document_id}/analysis", response_model=List[AnalysisResultResponse])
async def get_document_analysis_results(
    document_id: str,
    analysis_type: Optional[str] = Query(None),
    doc_service: DocumentService = Depends(get_document_service)
):
    """Get all analysis results for a document"""
    try:
        analyses = await doc_service.get_analysis_results_by_document(
            document_id=document_id,
            analysis_type=analysis_type
        )
        
        return [AnalysisResultResponse(**analysis) for analysis in analyses]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analysis results: {str(e)}")


@router.delete("/analysis/{analysis_id}")
async def delete_analysis_result(
    analysis_id: str,
    user_id: Optional[str] = Query(None),
    doc_service: DocumentService = Depends(get_document_service)
):
    """Delete an analysis result"""
    try:
        success = await doc_service.delete_analysis_result(
            analysis_id=analysis_id,
            user_id=user_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Analysis result not found")
        
        return {"message": "Analysis result deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete analysis result: {str(e)}")


# ==================== STATISTICS ENDPOINTS ====================

@router.get("/stats/overview", response_model=StatisticsResponse)
async def get_statistics(
    doc_service: DocumentService = Depends(get_document_service)
):
    """Get document and analysis statistics"""
    try:
        doc_stats = await doc_service.get_document_statistics()
        analysis_stats = await doc_service.get_analysis_statistics()
        
        return StatisticsResponse(
            document_stats=doc_stats,
            analysis_stats=analysis_stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


# ==================== HEALTH CHECK ====================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "document-management"}


# ==================== INTEGRATION WITH CONTRACT REVIEWER V2 ====================

def integrate_with_contract_reviewer(app):
    """
    Integrate document management API with Contract Reviewer v2 FastAPI app
    
    Usage in app.py:
        from document_api import router, integrate_with_contract_reviewer
        integrate_with_contract_reviewer(app)
    """
    app.include_router(router)
    
    # Add startup event to initialize document service
    @app.on_event("startup")
    async def startup_event():
        doc_service = await get_document_service()
        print("✅ Document management service initialized")
    
    # Add shutdown event to cleanup
    @app.on_event("shutdown")
    async def shutdown_event():
        global _document_service
        if _document_service:
            await _document_service.close()
            print("✅ Document management service closed")


# ==================== EXAMPLE INTEGRATION ====================

"""
To integrate with Contract Reviewer v2, add this to app.py:

from document_api import integrate_with_contract_reviewer

# After creating your FastAPI app
integrate_with_contract_reviewer(app)

This will add all the document management endpoints to your existing app.
"""
