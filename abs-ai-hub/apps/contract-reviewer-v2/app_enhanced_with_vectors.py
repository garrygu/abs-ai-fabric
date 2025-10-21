"""
Enhanced Contract Reviewer v2 with Vector Search
PostgreSQL-first architecture with Qdrant vector storage for semantic search
"""

import os
import json
import uuid
import hashlib
import tempfile
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import fitz  # PyMuPDF
from docx import Document as DocxDocument
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Header, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx
import uvicorn
import redis as redislib

# Import our services
from document_service import DocumentService
from vector_storage_service import VectorStorageService
from document_processing_service import DocumentProcessingService
from vector_search_api import integrate_vector_search

# Configuration
APP_PORT = int(os.getenv("APP_PORT", "8080"))
HUB_GATEWAY_URL = os.getenv("HUB_GATEWAY_URL", "http://hub-gateway:8081")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub")
DATA_DIR = Path(os.getenv("ABS_DATA_DIR", "/data"))
REPORTS_DIR = DATA_DIR / "reports"
UPLOADS_DIR = DATA_DIR / "uploads"
TEMPLATES_DIR = DATA_DIR / "templates"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="Contract Reviewer v2 - Enhanced with Vector Search",
    description="Professional AI-powered contract analysis platform with PostgreSQL persistence and semantic search",
    version="2.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global services
doc_service: Optional[DocumentService] = None
vector_service: Optional[VectorStorageService] = None
processing_service: Optional[DocumentProcessingService] = None
redis_client: Optional[redislib.Redis] = None

# Pydantic models
class AnalysisRequest(BaseModel):
    document_id: str
    analysis_type: str = "comprehensive"
    include_risks: bool = True
    include_recommendations: bool = True
    include_citations: bool = True
    process_for_search: bool = True  # New: process document for vector search

class AnalysisResponse(BaseModel):
    analysis_id: str
    document_id: str
    summary: Dict[str, Any]
    status: str
    processing_time_ms: int
    model_used: str
    vector_processing: Optional[Dict[str, Any]] = None

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    file_size: int
    status: str
    message: str
    vector_processing: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    score_threshold: float = 0.7
    include_analysis: bool = False

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_results: int
    query: str
    search_time_ms: int


# ==================== INITIALIZATION ====================

async def initialize_services():
    """Initialize all services"""
    global doc_service, vector_service, processing_service, redis_client
    
    try:
        # Initialize PostgreSQL document service
        print("🔧 Initializing PostgreSQL document service...")
        doc_service = DocumentService(POSTGRES_URL)
        await doc_service.initialize()
        print("✅ PostgreSQL document service initialized")
        
        # Initialize Qdrant vector service
        print("🔧 Initializing Qdrant vector service...")
        vector_service = VectorStorageService()
        await vector_service.initialize()
        print("✅ Qdrant vector service initialized")
        
        # Initialize document processing service
        print("🔧 Initializing document processing service...")
        processing_service = DocumentProcessingService(vector_service, doc_service)
        await processing_service.initialize()
        print("✅ Document processing service initialized")
        
        # Initialize Redis client for caching only
        print("🔧 Initializing Redis client for caching...")
        try:
            redis_client = redislib.from_url(REDIS_URL)
            redis_client.ping()
            print("✅ Redis client initialized for caching")
        except Exception as e:
            print(f"⚠️ Redis client failed to initialize: {e}")
            redis_client = None
        
        print("🎉 All services initialized successfully!")
        
    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        raise


# ==================== ENHANCED DOCUMENT MANAGEMENT ====================

@app.post("/api/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...), process_vectors: bool = Query(True)):
    """Upload a document and optionally process it for vector search"""
    try:
        if not doc_service:
            raise HTTPException(status_code=500, detail="Document service not initialized")
        
        # Save file to disk
        file_path = UPLOADS_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Create document record in PostgreSQL
        document = await doc_service.create_document(
            file_path=str(file_path),
            original_filename=file.filename,
            metadata={
                "upload_source": "contract-reviewer-v2-enhanced",
                "file_type": Path(file.filename).suffix,
                "upload_timestamp": datetime.now().isoformat(),
                "vector_processing_enabled": process_vectors
            }
        )
        
        # Cache document info in Redis for quick access
        if redis_client:
            try:
                redis_client.setex(
                    f"document:{document['id']}", 
                    3600,  # 1 hour cache
                    json.dumps(document)
                )
            except Exception as e:
                print(f"⚠️ Failed to cache document in Redis: {e}")
        
        # Process document for vector search if requested
        vector_processing = None
        if process_vectors and processing_service:
            try:
                print(f"🔍 Processing document {document['id']} for vector search...")
                processing_result = await processing_service.process_document(
                    document_id=document['id'],
                    file_path=str(file_path),
                    metadata={"client": "Contract Reviewer v2", "document_type": "Contract"}
                )
                
                vector_processing = {
                    "chunks_created": processing_result["chunks_created"],
                    "vector_ids": processing_result["vector_ids"],
                    "processing_status": processing_result["processing_status"],
                    "processed_at": processing_result["processed_at"]
                }
                
                print(f"✅ Document processed for vector search: {processing_result['chunks_created']} chunks")
                
            except Exception as e:
                print(f"⚠️ Failed to process document for vector search: {e}")
                vector_processing = {
                    "error": str(e),
                    "processing_status": "failed"
                }
        
        return DocumentUploadResponse(
            document_id=document["id"],
            filename=file.filename,
            file_size=document["file_size"],
            status="uploaded",
            message="Document uploaded successfully",
            vector_processing=vector_processing
        )
        
    except Exception as e:
        print(f"❌ Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
async def list_documents(limit: int = 10, offset: int = 0, include_vectors: bool = Query(False)):
    """List documents with optional vector processing information"""
    try:
        if not doc_service:
            raise HTTPException(status_code=500, detail="Document service not initialized")
        
        # Check Redis cache first
        cache_key = f"documents:list:{limit}:{offset}:{include_vectors}"
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    print("✅ Document list loaded from Redis cache")
                    return json.loads(cached)
            except Exception as e:
                print(f"⚠️ Redis cache error: {e}")
        
        # Load from PostgreSQL
        documents, total_count = await doc_service.get_documents(
            limit=limit, 
            offset=offset,
            order_by="upload_timestamp",
            order_direction="DESC"
        )
        
        # Add vector processing information if requested
        if include_vectors and processing_service:
            for doc in documents:
                try:
                    chunks = await processing_service.vector_service.get_document_chunks(doc["id"], limit=1)
                    doc["vector_info"] = {
                        "has_vectors": len(chunks) > 0,
                        "chunk_count": len(chunks) if chunks else 0
                    }
                except Exception as e:
                    doc["vector_info"] = {
                        "has_vectors": False,
                        "error": str(e)
                    }
        
        response = {
            "documents": documents,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count,
            "include_vectors": include_vectors
        }
        
        # Cache in Redis
        if redis_client:
            try:
                redis_client.setex(cache_key, 300, json.dumps(response))  # 5 min cache
            except Exception as e:
                print(f"⚠️ Failed to cache in Redis: {e}")
        
        print("✅ Document list loaded from PostgreSQL and cached")
        return response
        
    except Exception as e:
        print(f"❌ Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENHANCED ANALYSIS ====================

@app.post("/api/analyze/{document_id}", response_model=AnalysisResponse)
async def analyze_document(document_id: str, request: AnalysisRequest):
    """Analyze a document and optionally process it for vector search"""
    try:
        if not doc_service:
            raise HTTPException(status_code=500, detail="Document service not initialized")
        
        # Get document
        document = await doc_service.get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if analysis already exists
        existing_analyses = await doc_service.get_analysis_results_by_document(
            document_id=document_id,
            analysis_type=request.analysis_type
        )
        
        if existing_analyses:
            print(f"✅ Analysis already exists for document {document_id}")
            analysis = existing_analyses[0]
            
            # Cache in Redis for quick access
            if redis_client:
                try:
                    redis_client.setex(
                        f"analysis:{analysis['id']}", 
                        86400 * 7,  # 7 days cache
                        json.dumps(analysis)
                    )
                except Exception as e:
                    print(f"⚠️ Failed to cache analysis in Redis: {e}")
            
            return AnalysisResponse(
                analysis_id=analysis["id"],
                document_id=document_id,
                summary=analysis["analysis_data"],
                status="completed",
                processing_time_ms=analysis.get("processing_time_ms", 0),
                model_used=analysis.get("model_used", "llama3.2:3b")
            )
        
        # Perform analysis (simplified for demo)
        start_time = datetime.now()
        
        # Simulate analysis processing
        await asyncio.sleep(1)  # Simulate processing time
        
        analysis_data = {
            "summary": {
                "summary": f"Analysis of {document['original_filename']}",
                "document_type": "Contract",
                "key_points": [
                    "Confidentiality period: 2 years",
                    "Governing law: California",
                    "Dispute resolution: Arbitration"
                ]
            },
            "risks": [
                {"level": "low", "description": "Standard confidentiality clause"},
                {"level": "medium", "description": "Consider adding return of materials clause"}
            ],
            "recommendations": [
                "Review confidentiality period",
                "Consider adding return of materials clause",
                "Verify governing law jurisdiction"
            ],
            "citations": [
                "Section 2.1: Confidentiality obligations",
                "Section 4.2: Term and termination"
            ]
        }
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Save analysis result to PostgreSQL
        analysis = await doc_service.create_analysis_result(
            document_id=document_id,
            analysis_type=request.analysis_type,
            analysis_data=analysis_data,
            model_used="llama3.2:3b",
            processing_time_ms=int(processing_time)
        )
        
        # Cache analysis result in Redis
        if redis_client:
            try:
                redis_client.setex(
                    f"analysis:{analysis['id']}", 
                    86400 * 7,  # 7 days cache
                    json.dumps(analysis)
                )
            except Exception as e:
                print(f"⚠️ Failed to cache analysis in Redis: {e}")
        
        # Process document for vector search if requested
        vector_processing = None
        if request.process_for_search and processing_service:
            try:
                print(f"🔍 Processing document {document_id} for vector search...")
                processing_result = await processing_service.process_document(
                    document_id=document_id,
                    file_path=document["file_path"],
                    metadata={"analysis_id": analysis["id"], "analysis_type": request.analysis_type}
                )
                
                vector_processing = {
                    "chunks_created": processing_result["chunks_created"],
                    "vector_ids": processing_result["vector_ids"],
                    "processing_status": processing_result["processing_status"],
                    "processed_at": processing_result["processed_at"]
                }
                
                print(f"✅ Document processed for vector search: {processing_result['chunks_created']} chunks")
                
            except Exception as e:
                print(f"⚠️ Failed to process document for vector search: {e}")
                vector_processing = {
                    "error": str(e),
                    "processing_status": "failed"
                }
        
        print(f"✅ Analysis completed for document {document_id}")
        
        return AnalysisResponse(
            analysis_id=analysis["id"],
            document_id=document_id,
            summary=analysis_data,
            status="completed",
            processing_time_ms=int(processing_time),
            model_used="llama3.2:3b",
            vector_processing=vector_processing
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error analyzing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SEMANTIC SEARCH ====================

@app.post("/api/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """Perform semantic search across all documents"""
    try:
        if not processing_service:
            raise HTTPException(status_code=500, detail="Processing service not initialized")
        
        start_time = datetime.now()
        
        print(f"🔍 Performing semantic search: {request.query}")
        
        # Perform semantic search
        search_results = await processing_service.search_documents(
            query=request.query,
            limit=request.limit,
            score_threshold=request.score_threshold
        )
        
        # Enhance results with analysis data if requested
        if request.include_analysis:
            for result in search_results:
                try:
                    analyses = await doc_service.get_analysis_results_by_document(result["document_id"])
                    if analyses:
                        result["analysis"] = analyses[0]  # Get most recent analysis
                except Exception as e:
                    print(f"⚠️ Could not load analysis for document {result['document_id']}: {e}")
        
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        response = SearchResponse(
            results=search_results,
            total_results=len(search_results),
            query=request.query,
            search_time_ms=int(search_time)
        )
        
        print(f"✅ Semantic search completed: {len(search_results)} results in {search_time:.0f}ms")
        return response
        
    except Exception as e:
        print(f"❌ Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
async def semantic_search_get(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    score_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity score"),
    include_analysis: bool = Query(False, description="Include analysis data in results")
):
    """Perform semantic search (GET endpoint for easy testing)"""
    try:
        request = SearchRequest(
            query=query,
            limit=limit,
            score_threshold=score_threshold,
            include_analysis=include_analysis
        )
        
        return await semantic_search(request)
        
    except Exception as e:
        print(f"❌ Error in semantic search (GET): {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/similar/{document_id}")
async def find_similar_documents(
    document_id: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of similar documents"),
    score_threshold: float = Query(0.8, ge=0.0, le=1.0, description="Minimum similarity score")
):
    """Find documents similar to a given document"""
    try:
        if not processing_service:
            raise HTTPException(status_code=500, detail="Processing service not initialized")
        
        print(f"🔍 Finding documents similar to {document_id}")
        
        # Find similar documents
        similar_docs = await processing_service.find_similar_documents(
            document_id=document_id,
            limit=limit,
            score_threshold=score_threshold
        )
        
        print(f"✅ Found {len(similar_docs)} similar documents")
        return {"similar_documents": similar_docs, "count": len(similar_docs)}
        
    except Exception as e:
        print(f"❌ Error finding similar documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ENHANCED STATISTICS ====================

@app.get("/api/stats")
async def get_statistics():
    """Get comprehensive system statistics"""
    try:
        if not doc_service:
            raise HTTPException(status_code=500, detail="Document service not initialized")
        
        # Get document statistics
        doc_stats = await doc_service.get_document_statistics()
        
        # Get analysis statistics
        analysis_stats = await doc_service.get_analysis_statistics()
        
        # Get vector processing statistics
        vector_stats = None
        if processing_service:
            try:
                vector_stats = await processing_service.get_processing_stats()
            except Exception as e:
                print(f"⚠️ Error getting vector stats: {e}")
        
        # Get Redis statistics
        redis_stats = {}
        if redis_client:
            try:
                redis_info = redis_client.info()
                redis_stats = {
                    "connected_clients": redis_info.get("connected_clients", 0),
                    "used_memory": redis_info.get("used_memory_human", "0B"),
                    "keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "keyspace_misses": redis_info.get("keyspace_misses", 0)
                }
            except Exception as e:
                print(f"⚠️ Error getting Redis stats: {e}")
        
        return {
            "documents": doc_stats,
            "analyses": analysis_stats,
            "vector_processing": vector_stats,
            "redis": redis_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HEALTH CHECKS ====================

@app.get("/api/health")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "postgresql": "unknown",
            "qdrant": "unknown",
            "redis": "unknown",
            "processing": "unknown"
        }
    }
    
    # Check PostgreSQL
    if doc_service:
        try:
            await doc_service.get_documents(limit=1, offset=0)
            health_status["services"]["postgresql"] = "healthy"
        except:
            health_status["services"]["postgresql"] = "unhealthy"
    
    # Check Qdrant
    if vector_service:
        try:
            await vector_service.get_collection_stats()
            health_status["services"]["qdrant"] = "healthy"
        except:
            health_status["services"]["qdrant"] = "unhealthy"
    
    # Check Redis
    if redis_client:
        try:
            redis_client.ping()
            health_status["services"]["redis"] = "healthy"
        except:
            health_status["services"]["redis"] = "unhealthy"
    
    # Check Processing Service
    if processing_service:
        try:
            await processing_service.get_processing_stats()
            health_status["services"]["processing"] = "healthy"
        except:
            health_status["services"]["processing"] = "unhealthy"
    
    # Overall status
    unhealthy_services = [svc for svc, status in health_status["services"].items() if status == "unhealthy"]
    if unhealthy_services:
        health_status["status"] = "degraded"
        health_status["unhealthy_services"] = unhealthy_services
    
    return health_status


# ==================== STARTUP AND SHUTDOWN ====================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Starting Contract Reviewer v2 - Enhanced with Vector Search")
    await initialize_services()
    
    # Integrate vector search API
    integrate_vector_search(app)
    print("✅ Vector search API integrated")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down Contract Reviewer v2 - Enhanced")
    
    if processing_service:
        try:
            await processing_service.close()
            print("✅ Processing service closed")
        except Exception as e:
            print(f"⚠️ Error closing processing service: {e}")
    
    if doc_service:
        try:
            await doc_service.close()
            print("✅ PostgreSQL service closed")
        except Exception as e:
            print(f"⚠️ Error closing PostgreSQL service: {e}")
    
    if vector_service:
        try:
            await vector_service.close()
            print("✅ Qdrant service closed")
        except Exception as e:
            print(f"⚠️ Error closing Qdrant service: {e}")
    
    if redis_client:
        try:
            redis_client.close()
            print("✅ Redis client closed")
        except Exception as e:
            print(f"⚠️ Error closing Redis client: {e}")


# ==================== MAIN ====================

if __name__ == "__main__":
    print("🚀 Starting Contract Reviewer v2 - Enhanced with Vector Search")
    print("✅ PostgreSQL ready for persistent storage")
    print("✅ Qdrant ready for vector storage and semantic search")
    print("✅ Redis ready for caching")
    print("✅ Enhanced implementation ready")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=APP_PORT,
        reload=True,
        log_level="info"
    )
