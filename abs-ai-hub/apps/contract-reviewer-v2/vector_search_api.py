"""
Semantic Search API
FastAPI endpoints for semantic search and document similarity
"""

import asyncio
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
import logging

from vector_storage_service import VectorStorageService
from document_processing_service import DocumentProcessingService
from document_service import DocumentService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    score_threshold: float = 0.7
    filters: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    vector_id: str
    score: float
    document_id: str
    chunk_text: str
    chunk_index: int
    chunk_type: str
    start_position: int
    end_position: int
    word_count: int
    filename: str
    upload_timestamp: str
    file_size: int
    file_type: str
    metadata: Dict[str, Any]

class SimilarDocumentRequest(BaseModel):
    document_id: str
    limit: int = 5
    score_threshold: float = 0.8

class SimilarDocument(BaseModel):
    document_id: str
    max_score: float
    filename: str
    upload_timestamp: str
    file_size: int
    file_type: str
    chunks: List[Dict[str, Any]]

class ProcessDocumentRequest(BaseModel):
    document_id: str
    file_path: str
    metadata: Optional[Dict[str, Any]] = None

class ProcessDocumentResponse(BaseModel):
    document_id: str
    file_path: str
    chunks_created: int
    vector_ids: List[str]
    processing_status: str
    processed_at: str

# Global services
vector_service: Optional[VectorStorageService] = None
processing_service: Optional[DocumentProcessingService] = None
doc_service: Optional[DocumentService] = None

# Dependency injection
async def get_vector_service() -> VectorStorageService:
    """Get or create vector service instance"""
    global vector_service
    
    if vector_service is None:
        vector_service = VectorStorageService()
        await vector_service.initialize()
    
    return vector_service

async def get_processing_service() -> DocumentProcessingService:
    """Get or create processing service instance"""
    global processing_service, doc_service
    
    if processing_service is None:
        if doc_service is None:
            doc_service = DocumentService()
            await doc_service.initialize()
        
        vector_svc = await get_vector_service()
        processing_service = DocumentProcessingService(vector_svc, doc_service)
        await processing_service.initialize()
    
    return processing_service

# API Router
router = APIRouter(prefix="/api/vector", tags=["vector-search"])

# ==================== SEMANTIC SEARCH ENDPOINTS ====================

@router.post("/search", response_model=List[SearchResult])
async def semantic_search(
    request: SearchRequest,
    processing_svc: DocumentProcessingService = Depends(get_processing_service)
):
    """
    Perform semantic search across all documents
    
    Args:
        request: Search request with query and parameters
        
    Returns:
        List of search results with document metadata
    """
    try:
        logger.info(f"Semantic search request: {request.query}")
        
        # Perform search
        search_results = await processing_svc.search_documents(
            query=request.query,
            limit=request.limit,
            score_threshold=request.score_threshold,
            filters=request.filters
        )
        
        # Convert to response format
        results = []
        for result in search_results:
            results.append(SearchResult(
                vector_id=result["vector_id"],
                score=result["score"],
                document_id=result["document_id"],
                chunk_text=result["chunk_text"],
                chunk_index=result["chunk_index"],
                chunk_type=result["chunk_type"],
                start_position=result["start_position"],
                end_position=result["end_position"],
                word_count=result["word_count"],
                filename=result.get("filename", "Unknown"),
                upload_timestamp=result.get("upload_timestamp", ""),
                file_size=result.get("file_size", 0),
                file_type=result.get("file_type", ""),
                metadata=result.get("metadata", {})
            ))
        
        logger.info(f"✅ Semantic search completed: {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def semantic_search_get(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    score_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity score"),
    filters: Optional[str] = Query(None, description="JSON filters"),
    processing_svc: DocumentProcessingService = Depends(get_processing_service)
):
    """
    Perform semantic search (GET endpoint for easy testing)
    
    Args:
        query: Search query text
        limit: Maximum number of results
        score_threshold: Minimum similarity score
        filters: JSON string of filters
        
    Returns:
        List of search results
    """
    try:
        # Parse filters if provided
        parsed_filters = None
        if filters:
            try:
                parsed_filters = json.loads(filters)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid filters JSON")
        
        # Create search request
        request = SearchRequest(
            query=query,
            limit=limit,
            score_threshold=score_threshold,
            filters=parsed_filters
        )
        
        # Perform search
        return await semantic_search(request, processing_svc)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in semantic search (GET): {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== SIMILARITY ENDPOINTS ====================

@router.post("/similar", response_model=List[SimilarDocument])
async def find_similar_documents(
    request: SimilarDocumentRequest,
    processing_svc: DocumentProcessingService = Depends(get_processing_service)
):
    """
    Find documents similar to a given document
    
    Args:
        request: Similar document request with document ID and parameters
        
    Returns:
        List of similar documents
    """
    try:
        logger.info(f"Finding documents similar to {request.document_id}")
        
        # Find similar documents
        similar_docs = await processing_svc.find_similar_documents(
            document_id=request.document_id,
            limit=request.limit,
            score_threshold=request.score_threshold
        )
        
        # Convert to response format
        results = []
        for doc in similar_docs:
            results.append(SimilarDocument(
                document_id=doc["document_id"],
                max_score=doc["max_score"],
                filename=doc.get("filename", "Unknown"),
                upload_timestamp=doc.get("upload_timestamp", ""),
                file_size=doc.get("file_size", 0),
                file_type=doc.get("file_type", ""),
                chunks=doc.get("chunks", [])
            ))
        
        logger.info(f"✅ Found {len(results)} similar documents")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error finding similar documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar/{document_id}")
async def find_similar_documents_get(
    document_id: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of similar documents"),
    score_threshold: float = Query(0.8, ge=0.0, le=1.0, description="Minimum similarity score"),
    processing_svc: DocumentProcessingService = Depends(get_processing_service)
):
    """
    Find documents similar to a given document (GET endpoint)
    
    Args:
        document_id: ID of the reference document
        limit: Maximum number of similar documents
        score_threshold: Minimum similarity score
        
    Returns:
        List of similar documents
    """
    try:
        # Create similar document request
        request = SimilarDocumentRequest(
            document_id=document_id,
            limit=limit,
            score_threshold=score_threshold
        )
        
        # Find similar documents
        return await find_similar_documents(request, processing_svc)
        
    except Exception as e:
        logger.error(f"❌ Error finding similar documents (GET): {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== DOCUMENT PROCESSING ENDPOINTS ====================

@router.post("/process", response_model=ProcessDocumentResponse)
async def process_document(
    request: ProcessDocumentRequest,
    processing_svc: DocumentProcessingService = Depends(get_processing_service)
):
    """
    Process a document for vector storage
    
    Args:
        request: Process document request with document ID and file path
        
    Returns:
        Processing results
    """
    try:
        logger.info(f"Processing document {request.document_id}: {request.file_path}")
        
        # Process document
        result = await processing_svc.process_document(
            document_id=request.document_id,
            file_path=request.file_path,
            metadata=request.metadata
        )
        
        # Convert to response format
        response = ProcessDocumentResponse(
            document_id=result["document_id"],
            file_path=result["file_path"],
            chunks_created=result["chunks_created"],
            vector_ids=result["vector_ids"],
            processing_status=result["processing_status"],
            processed_at=result["processed_at"]
        )
        
        logger.info(f"✅ Document processed: {result['chunks_created']} chunks created")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error processing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reprocess/{document_id}")
async def reprocess_document(
    document_id: str,
    file_path: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    processing_svc: DocumentProcessingService = Depends(get_processing_service)
):
    """
    Reprocess a document (update existing vectors)
    
    Args:
        document_id: ID of the document to reprocess
        file_path: Path to the document file (optional)
        metadata: Additional metadata (optional)
        
    Returns:
        Reprocessing results
    """
    try:
        logger.info(f"Reprocessing document {document_id}")
        
        # Reprocess document
        result = await processing_svc.reprocess_document(
            document_id=document_id,
            file_path=file_path,
            metadata=metadata
        )
        
        logger.info(f"✅ Document reprocessed: {result['chunks_updated']} chunks updated")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error reprocessing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/process/{document_id}")
async def delete_document_vectors(
    document_id: str,
    processing_svc: DocumentProcessingService = Depends(get_processing_service)
):
    """
    Delete all vectors for a document
    
    Args:
        document_id: ID of the document
        
    Returns:
        Deletion confirmation
    """
    try:
        logger.info(f"Deleting vectors for document {document_id}")
        
        # Delete document vectors
        success = await processing_svc.delete_document_vectors(document_id)
        
        if success:
            logger.info(f"✅ Vectors deleted for document {document_id}")
            return {"message": f"Vectors deleted for document {document_id}", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete vectors")
        
    except Exception as e:
        logger.error(f"❌ Error deleting document vectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== DOCUMENT CHUNKS ENDPOINTS ====================

@router.get("/chunks/{document_id}")
async def get_document_chunks(
    document_id: str,
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Maximum number of chunks"),
    vector_svc: VectorStorageService = Depends(get_vector_service)
):
    """
    Get all chunks for a document
    
    Args:
        document_id: ID of the document
        limit: Maximum number of chunks to return
        
    Returns:
        List of document chunks
    """
    try:
        logger.info(f"Getting chunks for document {document_id}")
        
        # Get document chunks
        chunks = await vector_svc.get_document_chunks(document_id, limit)
        
        logger.info(f"✅ Retrieved {len(chunks)} chunks for document {document_id}")
        return {"chunks": chunks, "count": len(chunks)}
        
    except Exception as e:
        logger.error(f"❌ Error getting document chunks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== STATISTICS ENDPOINTS ====================

@router.get("/stats")
async def get_vector_stats(
    processing_svc: DocumentProcessingService = Depends(get_processing_service)
):
    """
    Get vector storage and processing statistics
    
    Returns:
        Statistics about vector storage and processing
    """
    try:
        logger.info("Getting vector storage statistics")
        
        # Get processing stats
        stats = await processing_svc.get_processing_stats()
        
        logger.info("✅ Retrieved vector storage statistics")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error getting vector stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def vector_health_check(
    vector_svc: VectorStorageService = Depends(get_vector_service)
):
    """
    Health check for vector storage service
    
    Returns:
        Health status
    """
    try:
        # Get collection stats to test connection
        stats = await vector_svc.get_collection_stats()
        
        return {
            "status": "healthy",
            "service": "vector-storage",
            "collection_name": stats["collection_name"],
            "vectors_count": stats["vectors_count"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Vector storage health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "vector-storage",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ==================== INTEGRATION WITH MAIN APP ====================

def integrate_vector_search(app):
    """
    Integrate vector search API with main FastAPI app
    
    Usage in app.py:
        from vector_search_api import integrate_vector_search
        integrate_vector_search(app)
    """
    app.include_router(router)
    
    # Add startup event to initialize services
    @app.on_event("startup")
    async def startup_event():
        global vector_service, processing_service, doc_service
        
        try:
            # Initialize vector service
            vector_service = VectorStorageService()
            await vector_service.initialize()
            
            # Initialize document service
            doc_service = DocumentService()
            await doc_service.initialize()
            
            # Initialize processing service
            processing_service = DocumentProcessingService(vector_service, doc_service)
            await processing_service.initialize()
            
            logger.info("✅ Vector search services initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector search services: {e}")
    
    # Add shutdown event to cleanup
    @app.on_event("shutdown")
    async def shutdown_event():
        global vector_service, processing_service, doc_service
        
        try:
            if processing_service:
                await processing_service.close()
            if doc_service:
                await doc_service.close()
            if vector_service:
                await vector_service.close()
            
            logger.info("✅ Vector search services closed")
            
        except Exception as e:
            logger.error(f"⚠️ Error closing vector search services: {e}")


# ==================== EXAMPLE INTEGRATION ====================

"""
To integrate with Contract Reviewer v2, add this to app.py:

from vector_search_api import integrate_vector_search

# After creating your FastAPI app
integrate_vector_search(app)

This will add all the vector search endpoints to your existing app.
"""
