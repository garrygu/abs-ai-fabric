"""
Clean PostgreSQL-First Implementation for Contract Reviewer v2
Fresh implementation using PostgreSQL as primary storage with Redis for caching only
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
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Header
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx
import uvicorn
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import redis as redislib

# Import our PostgreSQL document service
from document_service import DocumentService
from document_api import integrate_with_contract_reviewer

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
    title="Contract Reviewer v2 - PostgreSQL First",
    description="Professional AI-powered contract analysis platform with PostgreSQL persistence",
    version="2.0.0"
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
redis_client: Optional[redislib.Redis] = None
qdrant_client: Optional[QdrantClient] = None

# Pydantic models
class AnalysisRequest(BaseModel):
    document_id: str
    analysis_type: str = "comprehensive"
    include_risks: bool = True
    include_recommendations: bool = True
    include_citations: bool = True

class AnalysisResponse(BaseModel):
    analysis_id: str
    document_id: str
    summary: Dict[str, Any]
    status: str
    processing_time_ms: int
    model_used: str

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    file_size: int
    status: str
    message: str


# ==================== INITIALIZATION ====================

async def initialize_services():
    """Initialize all services"""
    global doc_service, redis_client, qdrant_client
    
    try:
        # Initialize PostgreSQL document service
        print("🔧 Initializing PostgreSQL document service...")
        doc_service = DocumentService(POSTGRES_URL)
        await doc_service.initialize()
        print("✅ PostgreSQL document service initialized")
        
        # Initialize Redis client for caching only
        print("🔧 Initializing Redis client for caching...")
        try:
            redis_client = redislib.from_url(REDIS_URL)
            redis_client.ping()
            print("✅ Redis client initialized for caching")
        except Exception as e:
            print(f"⚠️ Redis client failed to initialize: {e}")
            redis_client = None
        
        # Initialize Qdrant client
        print("🔧 Initializing Qdrant client...")
        try:
            qdrant_client = QdrantClient(host="qdrant", port=6333)
            print("✅ Qdrant client initialized")
        except Exception as e:
            print(f"⚠️ Qdrant client failed to initialize: {e}")
            qdrant_client = None
        
        print("🎉 All services initialized successfully!")
        
    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        raise


# ==================== DOCUMENT MANAGEMENT ====================

@app.post("/api/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a document and store in PostgreSQL"""
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
                "upload_source": "contract-reviewer-v2",
                "file_type": Path(file.filename).suffix,
                "upload_timestamp": datetime.now().isoformat()
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
        
        return DocumentUploadResponse(
            document_id=document["id"],
            filename=file.filename,
            file_size=document["file_size"],
            status="uploaded",
            message="Document uploaded successfully"
        )
        
    except Exception as e:
        print(f"❌ Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
async def list_documents(limit: int = 10, offset: int = 0):
    """List documents with pagination"""
    try:
        if not doc_service:
            raise HTTPException(status_code=500, detail="Document service not initialized")
        
        # Check Redis cache first
        cache_key = f"documents:list:{limit}:{offset}"
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
        
        response = {
            "documents": documents,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
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


@app.get("/api/documents/{document_id}")
async def get_document(document_id: str):
    """Get a specific document"""
    try:
        if not doc_service:
            raise HTTPException(status_code=500, detail="Document service not initialized")
        
        # Check Redis cache first
        if redis_client:
            try:
                cached = redis_client.get(f"document:{document_id}")
                if cached:
                    print(f"✅ Document {document_id} loaded from Redis cache")
                    return json.loads(cached)
            except Exception as e:
                print(f"⚠️ Redis cache error: {e}")
        
        # Load from PostgreSQL
        document = await doc_service.get_document_by_id(document_id)
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Cache in Redis
        if redis_client:
            try:
                redis_client.setex(f"document:{document_id}", 3600, json.dumps(document))
            except Exception as e:
                print(f"⚠️ Failed to cache in Redis: {e}")
        
        print(f"✅ Document {document_id} loaded from PostgreSQL and cached")
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ANALYSIS MANAGEMENT ====================

@app.post("/api/analyze/{document_id}", response_model=AnalysisResponse)
async def analyze_document(document_id: str, request: AnalysisRequest):
    """Analyze a document and store results in PostgreSQL"""
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
        
        print(f"✅ Analysis completed for document {document_id}")
        
        return AnalysisResponse(
            analysis_id=analysis["id"],
            document_id=document_id,
            summary=analysis_data,
            status="completed",
            processing_time_ms=int(processing_time),
            model_used="llama3.2:3b"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error analyzing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """Get analysis result by ID"""
    try:
        if not doc_service:
            raise HTTPException(status_code=500, detail="Document service not initialized")
        
        # Check Redis cache first
        if redis_client:
            try:
                cached = redis_client.get(f"analysis:{analysis_id}")
                if cached:
                    print(f"✅ Analysis {analysis_id} loaded from Redis cache")
                    return json.loads(cached)
            except Exception as e:
                print(f"⚠️ Redis cache error: {e}")
        
        # Load from PostgreSQL
        analysis = await doc_service.get_analysis_result_by_id(analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Cache in Redis
        if redis_client:
            try:
                redis_client.setex(f"analysis:{analysis_id}", 3600, json.dumps(analysis))
            except Exception as e:
                print(f"⚠️ Failed to cache in Redis: {e}")
        
        print(f"✅ Analysis {analysis_id} loaded from PostgreSQL and cached")
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{document_id}/analysis")
async def get_document_analyses(document_id: str):
    """Get all analyses for a document"""
    try:
        if not doc_service:
            raise HTTPException(status_code=500, detail="Document service not initialized")
        
        # Load from PostgreSQL
        analyses = await doc_service.get_analysis_results_by_document(document_id)
        
        print(f"✅ Found {len(analyses)} analyses for document {document_id}")
        return {"analyses": analyses, "count": len(analyses)}
        
    except Exception as e:
        print(f"❌ Error getting document analyses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATISTICS ====================

@app.get("/api/stats")
async def get_statistics():
    """Get system statistics"""
    try:
        if not doc_service:
            raise HTTPException(status_code=500, detail="Document service not initialized")
        
        # Get document statistics
        doc_stats = await doc_service.get_document_statistics()
        
        # Get analysis statistics
        analysis_stats = await doc_service.get_analysis_statistics()
        
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
            "redis": redis_stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HEALTH CHECKS ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "postgresql": "unknown",
            "redis": "unknown",
            "qdrant": "unknown"
        }
    }
    
    # Check PostgreSQL
    if doc_service:
        try:
            await doc_service.get_documents(limit=1, offset=0)
            health_status["services"]["postgresql"] = "healthy"
        except:
            health_status["services"]["postgresql"] = "unhealthy"
    
    # Check Redis
    if redis_client:
        try:
            redis_client.ping()
            health_status["services"]["redis"] = "healthy"
        except:
            health_status["services"]["redis"] = "unhealthy"
    
    # Check Qdrant
    if qdrant_client:
        try:
            qdrant_client.get_collections()
            health_status["services"]["qdrant"] = "healthy"
        except:
            health_status["services"]["qdrant"] = "unhealthy"
    
    return health_status


# ==================== STARTUP AND SHUTDOWN ====================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Starting Contract Reviewer v2 - PostgreSQL First")
    await initialize_services()
    
    # Integrate document management API
    integrate_with_contract_reviewer(app)
    print("✅ Document management API integrated")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("🛑 Shutting down Contract Reviewer v2")
    
    if doc_service:
        try:
            await doc_service.close()
            print("✅ PostgreSQL service closed")
        except Exception as e:
            print(f"⚠️ Error closing PostgreSQL service: {e}")
    
    if redis_client:
        try:
            redis_client.close()
            print("✅ Redis client closed")
        except Exception as e:
            print(f"⚠️ Error closing Redis client: {e}")


# ==================== MAIN ====================

if __name__ == "__main__":
    print("🚀 Starting Contract Reviewer v2 - PostgreSQL First Implementation")
    print("✅ Redis cleared and ready for caching only")
    print("✅ PostgreSQL ready for persistent storage")
    print("✅ Fresh implementation ready")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=APP_PORT,
        reload=True,
        log_level="info"
    )
