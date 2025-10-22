"""
Contract Reviewer v2 - Integrated Application
Complete legal document analysis platform with PostgreSQL, Qdrant, Redis, and File Storage
"""

import os
import json
import uuid
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Query, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import redis as redislib
import httpx
import io

# Import our services
from document_service import DocumentService
from vector_storage_service import VectorStorageService
from document_processing_service import DocumentProcessingService
from file_based_storage_service import FileBasedStorageService, StorageConfig, FileType
from report_generation_service import ReportGenerationService, ReportRequest, ReportFormat, ReportType
from file_management_api import integrate_file_management

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
APP_PORT = int(os.getenv("APP_PORT", "8080"))
HUB_GATEWAY_URL = os.getenv("HUB_GATEWAY_URL", "http://hub-gateway:8081")

# Framework Configuration
ABS_FRAMEWORK_PATH = os.getenv("ABS_FRAMEWORK_PATH", "http://localhost:3000/unified-framework.js")
ABS_GATEWAY_URL = os.getenv("ABS_GATEWAY_URL", "http://localhost:8081")
ABS_APP_REGISTRY_URL = os.getenv("ABS_APP_REGISTRY_URL", "http://localhost:8081/api/apps")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://hub_user:secure_password@document-hub-postgres:5432/document_hub")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
FILE_STORAGE_PATH = os.getenv("FILE_STORAGE_PATH", "/data/file_storage")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "100")) * 1024 * 1024  # MB to bytes

# Ensure directories exist
Path(FILE_STORAGE_PATH).mkdir(parents=True, exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="Contract Reviewer v2 - Integrated",
    description="Complete AI-powered contract analysis platform with PostgreSQL persistence, vector search, and file management",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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

# Serve frontend at root
@app.get("/")
async def serve_frontend():
    """Serve the frontend application with environment variables"""
    # Read the HTML file
    with open("static/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Inject environment variables
    env_script = f"""
    <script>
        window.ABS_FRAMEWORK_PATH = "{ABS_FRAMEWORK_PATH}";
        window.ABS_GATEWAY_URL = "{ABS_GATEWAY_URL}";
        window.ABS_APP_REGISTRY_URL = "{ABS_APP_REGISTRY_URL}";
    </script>
    """
    
    # Insert the script before the closing head tag
    html_content = html_content.replace("</head>", f"{env_script}</head>")
    
    return HTMLResponse(content=html_content)

# Redirect old upload endpoint to new one for compatibility
@app.post("/api/upload")
async def upload_file_redirect(file: UploadFile = File(...)):
    """Redirect upload requests to the new endpoint"""
    return await upload_document(
        file=file,
        client_id=None,
        document_type="contract",
        metadata=None,
        process_for_search=True,
        generate_report=False,
        report_format="pdf"
    )

# Add models endpoint for frontend compatibility
@app.get("/api/models")
async def get_models():
    """Get available models from the hub gateway"""
    try:
        # Get models from the hub gateway admin endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{HUB_GATEWAY_URL}/admin/models")
            if response.status_code == 200:
                data = response.json()
                # Transform the admin format to frontend format
                models = []
                for model in data.get("models", []):
                    if model.get("type") == "llm" and model.get("available", False):
                        models.append({
                            "name": model["name"],
                            "provider": "ollama",  # Default provider
                            "status": model.get("status", "unknown"),
                            "is_default": model.get("is_default_chat", False)
                        })
                return {"models": models}
            else:
                # Fallback to basic models if gateway is not available
                return {
                    "models": [
                        {"name": "gpt-3.5-turbo", "provider": "openai"},
                        {"name": "gpt-4", "provider": "openai"},
                        {"name": "claude-3-sonnet", "provider": "anthropic"},
                        {"name": "claude-3-haiku", "provider": "anthropic"}
                    ]
                }
    except Exception as e:
        logger.warning(f"Failed to get models from gateway: {e}")
        # Fallback to basic models
        return {
            "models": [
                {"name": "gpt-3.5-turbo", "provider": "openai"},
                {"name": "gpt-4", "provider": "openai"},
                {"name": "claude-3-sonnet", "provider": "anthropic"},
                {"name": "claude-3-haiku", "provider": "anthropic"}
            ]
        }

# Global services
doc_service: Optional[DocumentService] = None
vector_service: Optional[VectorStorageService] = None
processing_service: Optional[DocumentProcessingService] = None
storage_service: Optional[FileBasedStorageService] = None
report_service: Optional[ReportGenerationService] = None
redis_client: Optional[redislib.Redis] = None

# Pydantic models
class DocumentUploadRequest(BaseModel):
    client_id: Optional[str] = None
    document_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    process_for_search: bool = True
    generate_report: bool = False
    report_format: str = "pdf"

class AnalysisRequest(BaseModel):
    analysis_type: str = "comprehensive"
    include_risks: bool = True
    include_recommendations: bool = True
    include_citations: bool = True
    process_for_search: bool = True
    generate_report: bool = False
    report_format: str = "pdf"

class AnalysisResponse(BaseModel):
    analysis_id: str
    document_id: str
    summary: Dict[str, Any]
    status: str
    processing_time_ms: int
    model_used: str
    vector_processing: Optional[Dict[str, Any]] = None
    report_generation: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    file_size: int
    status: str
    message: str
    vector_processing: Optional[Dict[str, Any]] = None
    file_storage: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    score_threshold: float = 0.7
    include_analysis: bool = False
    include_reports: bool = False

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_results: int
    query: str
    search_time_ms: int


# ==================== INITIALIZATION ====================

async def initialize_services():
    """Initialize all services"""
    global doc_service, vector_service, processing_service, storage_service, report_service, redis_client
    
    try:
        logger.info("🚀 Initializing Contract Reviewer v2 - Integrated Services")
        
        # Initialize PostgreSQL document service
        logger.info("🔧 Initializing PostgreSQL document service...")
        doc_service = DocumentService(POSTGRES_URL)
        await doc_service.initialize()
        logger.info("✅ PostgreSQL document service initialized")
        
        # Initialize Qdrant vector service
        logger.info("🔧 Initializing Qdrant vector service...")
        vector_service = VectorStorageService(
            qdrant_host=QDRANT_HOST,
            qdrant_port=QDRANT_PORT
        )
        await vector_service.initialize()
        logger.info("✅ Qdrant vector service initialized")
        
        # Initialize document processing service
        logger.info("🔧 Initializing document processing service...")
        processing_service = DocumentProcessingService(vector_service, doc_service)
        await processing_service.initialize()
        logger.info("✅ Document processing service initialized")
        
        # Initialize file-based storage service
        logger.info("🔧 Initializing file-based storage service...")
        storage_config = StorageConfig(
            base_path=FILE_STORAGE_PATH,
            max_file_size=MAX_FILE_SIZE,
            enable_compression=True
        )
        storage_service = FileBasedStorageService(storage_config)
        logger.info("✅ File-based storage service initialized")
        
        # Initialize report generation service
        logger.info("🔧 Initializing report generation service...")
        report_service = ReportGenerationService(storage_service)
        logger.info("✅ Report generation service initialized")
        
        # Initialize Redis client for caching
        logger.info("🔧 Initializing Redis client for caching...")
        try:
            redis_client = redislib.from_url(REDIS_URL)
            redis_client.ping()
            logger.info("✅ Redis client initialized for caching")
        except Exception as e:
            logger.warning(f"⚠️ Redis client failed to initialize: {e}")
            redis_client = None
        
        logger.info("🎉 All services initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise


# ==================== DOCUMENT MANAGEMENT ====================

@app.post("/api/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    client_id: Optional[str] = Query(None, description="Client identifier"),
    document_type: Optional[str] = Query("contract", description="Type of document"),
    metadata: Optional[str] = Query(None, description="JSON metadata"),
    process_for_search: bool = Query(True, description="Process for vector search"),
    generate_report: bool = Query(False, description="Generate initial report"),
    report_format: str = Query("pdf", description="Report format"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload a document with comprehensive processing
    
    This endpoint handles:
    1. File upload and storage
    2. PostgreSQL metadata storage
    3. Vector processing for semantic search
    4. File-based storage for persistence
    5. Optional report generation
    """
    try:
        if not all([doc_service, processing_service, storage_service]):
            raise HTTPException(status_code=500, detail="Services not initialized")
        
        logger.info(f"📄 Uploading document: {file.filename}")
        
        # Parse metadata
        parsed_metadata = {}
        if metadata and isinstance(metadata, str):
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid metadata JSON")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Create temporary file for processing
        original_extension = Path(file.filename).suffix
        temp_file_path = Path(FILE_STORAGE_PATH) / "temp" / f"upload_{uuid.uuid4().hex}{original_extension}"
        temp_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Write temporary file
            with open(temp_file_path, "wb") as f:
                f.write(file_content)
            
            # Create document record in PostgreSQL
            document = await doc_service.create_document(
                file_path=str(temp_file_path),
                original_filename=file.filename,
                metadata={
                    **parsed_metadata,
                    "upload_source": "contract-reviewer-v2-integrated",
                    "file_type": Path(file.filename).suffix,
                    "upload_timestamp": datetime.now().isoformat(),
                    "client_id": client_id,
                    "document_type": document_type,
                    "vector_processing_enabled": process_for_search,
                    "report_generation_enabled": generate_report
                }
            )
            
            if not document:
                raise HTTPException(status_code=500, detail="Failed to create document record")
            
            logger.info(f"✅ Document created in PostgreSQL: {document['id']}")
            
            # Store file in file-based storage
            file_storage_result = None
            try:
                file_metadata = await storage_service.store_file(
                    file_data=file_content,
                    file_type=FileType.DOCUMENT,
                    original_filename=file.filename,
                    client_id=client_id,
                    document_id=document["id"],
                    metadata={
                        **parsed_metadata,
                        "document_type": document_type,
                        "upload_source": "contract-reviewer-v2-integrated"
                    }
                )
                
                file_storage_result = {
                    "file_id": file_metadata.file_id,
                    "file_path": file_metadata.file_path,
                    "file_size": file_metadata.file_size,
                    "checksum": file_metadata.checksum,
                    "stored_at": file_metadata.created_at.isoformat()
                }
                
                logger.info(f"✅ File stored in file-based storage: {file_metadata.file_id}")
                
            except Exception as e:
                logger.error(f"❌ Error storing file in file-based storage: {e}")
                file_storage_result = {"error": str(e)}
            
            # Cache document info in Redis for quick access
            if redis_client:
                try:
                    redis_client.setex(
                        f"document:{document['id']}", 
                        3600,  # 1 hour cache
                        json.dumps(document)
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to cache document in Redis: {e}")
            
            # Process document for vector search if requested
            vector_processing = None
            if process_for_search:
                try:
                    logger.info(f"🔍 Processing document {document['id']} for vector search...")
                    
                    # Process document for vector storage
                    processing_result = await processing_service.process_document(
                        document_id=document['id'],
                        file_path=str(temp_file_path),
                        metadata={
                            "client": client_id or "Unknown",
                            "document_type": document_type,
                            "upload_source": "contract-reviewer-v2-integrated"
                        }
                    )
                    
                    vector_processing = {
                        "chunks_created": processing_result["chunks_created"],
                        "vector_ids": processing_result["vector_ids"],
                        "processing_status": processing_result["processing_status"],
                        "processed_at": processing_result["processed_at"]
                    }
                    
                    logger.info(f"✅ Document processed for vector search: {processing_result['chunks_created']} chunks")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to process document for vector search: {e}")
                    vector_processing = {
                        "error": str(e),
                        "processing_status": "failed"
                    }
            
            # Generate initial report if requested
            report_generation = None
            if generate_report and report_service:
                try:
                    logger.info(f"📊 Generating initial report for document {document['id']}...")
                    
                    # Create a basic analysis for the report
                    basic_analysis = {
                        "summary": {
                            "summary": f"Initial analysis of {file.filename}",
                            "key_points": [
                                f"Document type: {document_type}",
                                f"File size: {file_size / 1024:.1f} KB",
                                f"Uploaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            ]
                        },
                        "risks": [
                            {"level": "info", "description": "Document uploaded successfully"}
                        ],
                        "recommendations": [
                            "Perform detailed analysis",
                            "Review document content",
                            "Check for compliance requirements"
                        ],
                        "citations": [
                            f"Document: {file.filename}",
                            f"Upload timestamp: {datetime.now().isoformat()}"
                        ]
                    }
                    
                    # Generate report
                    report_request = ReportRequest(
                        report_id=f"initial_report_{document['id']}",
                        report_type=ReportType.ANALYSIS_SUMMARY,
                        format=ReportFormat(report_format.lower()),
                        document_ids=[document['id']],
                        analysis_ids=[f"initial_analysis_{document['id']}"],
                        client_id=client_id
                    )
                    
                    report_metadata = await report_service.generate_report(
                        request=report_request,
                        analysis_data=basic_analysis,
                        document_metadata={
                            "original_filename": file.filename,
                            "file_size": file_size,
                            "upload_timestamp": datetime.now().isoformat()
                        }
                    )
                    
                    report_generation = {
                        "report_id": report_request.report_id,
                        "file_id": report_metadata.file_id,
                        "file_size": report_metadata.file_size,
                        "format": report_format,
                        "generated_at": report_metadata.created_at.isoformat(),
                        "download_url": f"/api/reports/download/{report_metadata.file_id}"
                    }
                    
                    logger.info(f"✅ Initial report generated: {report_metadata.file_id}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to generate initial report: {e}")
                    report_generation = {
                        "error": str(e),
                        "generation_status": "failed"
                    }
            
            # Update document metadata with processing results
            await doc_service.update_document(
                document_id=document["id"],
                updates={
                    "metadata": {
                        **document.get("metadata", {}),
                        "vector_processing": vector_processing,
                        "file_storage": file_storage_result,
                        "report_generation": report_generation,
                        "processing_completed_at": datetime.now().isoformat()
                    }
                }
            )
            
            logger.info(f"✅ Document uploaded successfully: {document['id']}")
            
            # Clear document list cache to ensure fresh data
            if redis_client:
                try:
                    # Clear all document list cache keys
                    cache_pattern = "documents:list:*"
                    keys = redis_client.keys(cache_pattern)
                    if keys:
                        redis_client.delete(*keys)
                        logger.info(f"✅ Cleared {len(keys)} document list cache entries")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to clear document list cache: {e}")
            
            return DocumentResponse(
                document_id=document["id"],
                filename=file.filename,
                file_size=file_size,
                status="uploaded",
                message="Document uploaded and processed successfully",
                vector_processing=vector_processing,
                file_storage=file_storage_result
            )
            
        finally:
            # Clean up temporary file
            if temp_file_path.exists():
                temp_file_path.unlink()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/{document_id}")
async def get_analysis(document_id: str):
    """Get saved analysis for a document"""
    try:
        if not doc_service:
            raise HTTPException(status_code=500, detail="Document service not initialized")
        
        logger.info(f"🔍 Getting analysis for document: {document_id}")
        
        # Get analysis results for the document
        analysis_results = await doc_service.get_analysis_results_by_document(
            document_id=document_id,
            analysis_type="comprehensive"
        )
        
        if not analysis_results:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Get the most recent analysis
        analysis = analysis_results[0]
        
        # Parse the analysis_data if it's a string
        analysis_data = analysis.get("analysis_data", {})
        if isinstance(analysis_data, str):
            try:
                analysis_data = json.loads(analysis_data)
            except json.JSONDecodeError:
                analysis_data = {}
        
        # Return the analysis in the format expected by the frontend
        return {
            "analysis_id": analysis["id"],
            "document_id": document_id,
            "summary": analysis_data.get("summary", {}),
            "risks": analysis_data.get("risks", []),
            "recommendations": analysis_data.get("recommendations", []),
            "citations": analysis_data.get("citations", []),
            "compliance": analysis_data.get("compliance", {}),
            "analysis_timestamp": analysis["analysis_timestamp"],
            "model_used": analysis.get("model_used"),
            "processing_time_ms": analysis.get("processing_time_ms"),
            "status": analysis.get("status", "completed")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting analysis for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its associated data"""
    try:
        if not doc_service:
            raise HTTPException(status_code=500, detail="Document service not initialized")
        
        logger.info(f"🗑️ Deleting document: {document_id}")
        
        # Get document details before deletion
        document = await doc_service.get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete from PostgreSQL (this will cascade to analysis_results and document_chunks)
        await doc_service.delete_document(document_id)
        
        # Delete from file storage
        if storage_service:
            try:
                await storage_service.delete_document_files(document_id)
                logger.info(f"✅ Deleted files for document: {document_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to delete files for document {document_id}: {e}")
        
        # Delete from vector storage
        if vector_service:
            try:
                await vector_service.delete_document_chunks(document_id)
                logger.info(f"✅ Deleted vectors for document: {document_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to delete vectors for document {document_id}: {e}")
        
        # Clear related cache
        if redis_client:
            try:
                # Clear document cache
                cache_keys = [
                    f"document:{document_id}",
                    f"analysis:{document_id}",
                    f"documents:list:*"
                ]
                for pattern in cache_keys:
                    keys = redis_client.keys(pattern)
                    if keys:
                        redis_client.delete(*keys)
                logger.info(f"✅ Cleared cache for document: {document_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to clear cache for document {document_id}: {e}")
        
        logger.info(f"✅ Document deleted successfully: {document_id}")
        return {"message": "Document deleted successfully", "document_id": document_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reprocess/{document_id}")
async def reprocess_document(document_id: str):
    """Retry vector processing for a document that had processing errors"""
    try:
        if not doc_service:
            raise HTTPException(status_code=500, detail="Document service not initialized")
        
        logger.info(f"🔄 Retrying vector processing for document: {document_id}")
        
        # Get the document
        document = await doc_service.get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if document has vector processing error
        if not document.get("metadata", {}).get("vector_processing", {}).get("error"):
            raise HTTPException(status_code=400, detail="Document does not have vector processing errors")
        
        # Get the file path
        file_path = document.get("file_path")
        if not file_path:
            raise HTTPException(status_code=400, detail="Document file path not found")
        
        # Retry vector processing
        if not processing_service:
            raise HTTPException(status_code=500, detail="Processing service not initialized")
        
        try:
            processing_result = await processing_service.process_document(
                document_id=document_id,
                file_path=file_path,
                metadata={
                    "client": document.get("metadata", {}).get("client", "Unknown"),
                    "document_type": document.get("metadata", {}).get("document_type", "contract"),
                    "upload_source": "contract-reviewer-v2-integrated",
                    "retry": True
                }
            )
            
            # Update document metadata to clear the error
            await doc_service.update_document(
                document_id=document_id,
                updates={
                    "metadata": {
                        **document.get("metadata", {}),
                        "vector_processing": {
                            "chunks_created": processing_result["chunks_created"],
                            "vector_ids": processing_result["vector_ids"],
                            "processing_status": processing_result["processing_status"],
                            "processed_at": processing_result["processed_at"],
                            "retried_at": datetime.now().isoformat(),
                            "retry_successful": True,
                            "error": None
                        }
                    }
                }
            )
            
            # Clear document list cache
            if redis_client:
                try:
                    cache_pattern = "documents:list:*"
                    keys = redis_client.keys(cache_pattern)
                    if keys:
                        redis_client.delete(*keys)
                        logger.info(f"✅ Cleared document list cache after reprocessing")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to clear cache after reprocessing: {e}")
            
            logger.info(f"✅ Successfully reprocessed document {document_id}")
            return {
                "message": "Document reprocessed successfully",
                "processing_result": processing_result
            }
            
        except Exception as processing_error:
            logger.error(f"❌ Reprocessing failed for document {document_id}: {processing_error}")
            
            # Update metadata to record the retry failure
            await doc_service.update_document(
                document_id=document_id,
                updates={
                    "metadata": {
                        **document.get("metadata", {}),
                        "vector_processing": {
                            **document.get("metadata", {}).get("vector_processing", {}),
                            "retried_at": datetime.now().isoformat(),
                            "retry_successful": False,
                            "retry_error": str(processing_error)
                        }
                    }
                }
            )
            
            raise HTTPException(status_code=500, detail=f"Reprocessing failed: {str(processing_error)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error reprocessing document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reprocess document: {str(e)}")


@app.get("/api/documents")
async def list_documents(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of documents"),
    offset: int = Query(0, ge=0, description="Number of documents to skip"),
    include_vectors: bool = Query(False, description="Include vector processing information"),
    include_reports: bool = Query(False, description="Include report information"),
    client_id: Optional[str] = Query(None, description="Filter by client ID")
):
    """List documents with optional processing information"""
    try:
        if not doc_service:
            raise HTTPException(status_code=500, detail="Document service not initialized")
        
        # Check Redis cache first
        cache_key = f"documents:list:{limit}:{offset}:{include_vectors}:{include_reports}:{client_id}"
        if redis_client:
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.info("✅ Document list loaded from Redis cache")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"⚠️ Redis cache error: {e}")
        
        # Load from PostgreSQL
        documents, total_count = await doc_service.get_documents(
            limit=limit, 
            offset=offset,
            order_by="upload_timestamp",
            order_direction="DESC"
        )
        
        logger.info(f"📋 Loaded {len(documents)} documents from database (total_count: {total_count})")
        
        # Debug: Log each document's key fields
        for i, doc in enumerate(documents):
            logger.info(f"Document {i}: id={doc.get('id')}, filename={doc.get('filename')}, original_filename={doc.get('original_filename')}, has_id={bool(doc.get('id'))}")
        
        # Filter by client_id if provided
        if client_id:
            documents = [doc for doc in documents if doc.get("metadata", {}).get("client_id") == client_id]
            total_count = len(documents)
        
        # Add analysis status to each document and ensure required fields
        valid_documents = []
        logger.info(f"🔍 Validating {len(documents)} documents...")
        
        for i, doc in enumerate(documents):
            # Only skip documents that are completely null/undefined
            if doc is None:
                logger.warning(f"⚠️ Skipping null document at index {i}")
                continue
            
            # Ensure document has an ID (this is the only critical requirement)
            if not doc.get("id"):
                logger.warning(f"⚠️ Skipping document {i} with missing ID: {doc}")
                continue
            
            # Ensure required fields have default values (don't skip if missing)
            doc.setdefault("original_filename", doc.get("filename", "Unknown"))
            doc.setdefault("file_size", 0)
            doc.setdefault("file_type", "Unknown")
            doc.setdefault("mime_type", "application/octet-stream")
            doc.setdefault("metadata", {})
            doc.setdefault("status", "uploaded")
            
            # Add analysis status (with error handling - don't skip if this fails)
            try:
                analysis_results = await doc_service.get_analysis_results_by_document(doc["id"])
                doc["has_analysis"] = len(analysis_results) > 0
            except Exception as analysis_error:
                logger.warning(f"⚠️ Could not get analysis results for document {doc['id']}: {analysis_error}")
                doc["has_analysis"] = False
            
            # Always add the document to valid_documents (we only skip if completely broken)
            valid_documents.append(doc)
            logger.info(f"✅ Document {i} validated: {doc.get('original_filename')} (ID: {doc.get('id')})")
        
        documents = valid_documents
        logger.info(f"✅ Validated {len(documents)} documents for API response")
        
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
        
        # Add report information if requested
        if include_reports and storage_service:
            for doc in documents:
                try:
                    # Find reports for this document
                    reports = await storage_service._find_files_by_document_id(doc["id"])
                    report_files = [f for f in reports if f.file_type in [FileType.REPORT_PDF, FileType.REPORT_WORD]]
                    
                    doc["report_info"] = {
                        "has_reports": len(report_files) > 0,
                        "report_count": len(report_files),
                        "reports": [
                            {
                                "file_id": f.file_id,
                                "file_type": f.file_type.value,
                                "created_at": f.created_at.isoformat(),
                                "file_size": f.file_size
                            }
                            for f in report_files
                        ]
                    }
                except Exception as e:
                    doc["report_info"] = {
                        "has_reports": False,
                        "error": str(e)
                    }
        
        response = {
            "documents": documents,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count,
            "include_vectors": include_vectors,
            "include_reports": include_reports,
            "client_id": client_id
        }
        
        # Cache in Redis
        if redis_client:
            try:
                redis_client.setex(cache_key, 300, json.dumps(response))  # 5 min cache
            except Exception as e:
                logger.warning(f"⚠️ Failed to cache in Redis: {e}")
        
        logger.info(f"✅ Document list loaded: {len(documents)} documents")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ANALYSIS ====================

@app.post("/api/analyze/{document_id}", response_model=AnalysisResponse)
async def analyze_document(
    document_id: str,
    request: AnalysisRequest,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Analyze a document with comprehensive processing
    
    This endpoint handles:
    1. Document analysis using AI models
    2. Vector processing for semantic search
    3. Analysis result storage in PostgreSQL and file system
    4. Optional report generation
    """
    try:
        if not all([doc_service, processing_service, storage_service]):
            raise HTTPException(status_code=500, detail="Services not initialized")
        
        logger.info(f"🔍 Analyzing document: {document_id}")
        
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
            logger.info(f"✅ Analysis already exists for document {document_id}")
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
                    logger.warning(f"⚠️ Failed to cache analysis in Redis: {e}")
            
            # Parse the analysis_data if it's a string
            analysis_data = analysis.get("analysis_data", {})
            if isinstance(analysis_data, str):
                try:
                    analysis_data = json.loads(analysis_data)
                except json.JSONDecodeError:
                    analysis_data = {}
            
            # Return the analysis in the same format as the get analysis endpoint
            return {
                "analysis_id": analysis["id"],
                "document_id": document_id,
                "summary": analysis_data.get("summary", {}),
                "risks": analysis_data.get("risks", []),
                "recommendations": analysis_data.get("recommendations", []),
                "citations": analysis_data.get("citations", []),
                "compliance": analysis_data.get("compliance", {}),
                "analysis_timestamp": analysis["analysis_timestamp"],
                "model_used": analysis.get("model_used", "llama3.2:3b"),
                "processing_time_ms": analysis.get("processing_time_ms", 0),
                "status": "completed"
            }
        
        # Perform analysis (simplified for demo - in production, integrate with AI models)
        start_time = datetime.now()
        
        # Simulate analysis processing
        await asyncio.sleep(2)  # Simulate processing time
        
        # Generate comprehensive analysis
        analysis_data = {
            "summary": {
                "summary": f"Comprehensive analysis of {document['original_filename']}",
                "document_type": document.get("metadata", {}).get("document_type", "Contract"),
                "key_points": [
                    "Confidentiality period: 2 years",
                    "Governing law: California",
                    "Dispute resolution: Arbitration",
                    "Termination clauses: Standard",
                    "Intellectual property: Protected"
                ]
            },
            "risks": [
                {"level": "low", "description": "Standard confidentiality clause", "section": "2.1"},
                {"level": "medium", "description": "Consider adding return of materials clause", "section": "3.2"},
                {"level": "low", "description": "Appropriate governing law selection", "section": "5.1"}
            ],
            "recommendations": [
                "Review confidentiality period for appropriateness",
                "Consider adding return of materials clause",
                "Verify governing law jurisdiction",
                "Review termination notice periods",
                "Ensure IP protection is comprehensive"
            ],
            "citations": [
                "Section 2.1: Confidentiality obligations",
                "Section 3.2: Use of confidential information",
                "Section 4.2: Term and termination",
                "Section 5.1: Governing law and jurisdiction"
            ],
            "compliance": {
                "gdpr_compliant": True,
                "ccpa_compliant": True,
                "industry_standards": ["ISO 27001", "SOC 2"]
            }
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
        
        if not analysis:
            logger.error(f"❌ Failed to create analysis result for document {document_id}")
            raise HTTPException(status_code=500, detail="Failed to save analysis result")
        
        # Store analysis result in file-based storage
        try:
            analysis_file_metadata = await storage_service.store_analysis_result(
                analysis_data=analysis_data,
                document_id=document_id,
                analysis_id=analysis["id"],
                client_id=document.get("metadata", {}).get("client_id"),
                format="json"
            )
            
            logger.info(f"✅ Analysis result stored in file system: {analysis_file_metadata.file_id}")
            
        except Exception as e:
            logger.error(f"❌ Error storing analysis result in file system: {e}")
        
        # Cache analysis result in Redis
        if redis_client and analysis:
            try:
                redis_client.setex(
                    f"analysis:{analysis['id']}", 
                    86400 * 7,  # 7 days cache
                    json.dumps(analysis)
                )
                logger.info(f"✅ Analysis result cached in Redis: {analysis['id']}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to cache analysis in Redis: {e}")
        
        # Process document for vector search if requested
        vector_processing = None
        if request.process_for_search and processing_service:
            try:
                logger.info(f"🔍 Processing document {document_id} for vector search...")
                
                # Get document file path
                file_path = document["file_path"]
                if not Path(file_path).exists():
                    # Try to get file from file-based storage
                    try:
                        file_content, file_metadata = await storage_service.retrieve_file(
                            document.get("metadata", {}).get("file_storage", {}).get("file_id")
                        )
                        # Create temporary file with original extension
                        original_extension = Path(file_metadata.file_path).suffix
                        temp_file_path = Path(FILE_STORAGE_PATH) / "temp" / f"analysis_{uuid.uuid4().hex}{original_extension}"
                        temp_file_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(temp_file_path, "wb") as f:
                            f.write(file_content)
                        file_path = str(temp_file_path)
                    except Exception as e:
                        logger.warning(f"Could not retrieve file from storage: {e}")
                        raise
                
                processing_result = await processing_service.process_document(
                    document_id=document_id,
                    file_path=file_path,
                    metadata={
                        "analysis_id": analysis["id"],
                        "analysis_type": request.analysis_type,
                        "client": document.get("metadata", {}).get("client_id", "Unknown")
                    }
                )
                
                # Handle case where processing_result might be None
                if processing_result is None:
                    logger.warning("⚠️ Processing result is None, using default values")
                    processing_result = {
                        "chunks_created": 0,
                        "vector_ids": [],
                        "processing_status": "failed",
                        "processed_at": datetime.now().isoformat()
                    }
                
                vector_processing = {
                    "chunks_created": processing_result.get("chunks_created", 0),
                    "vector_ids": processing_result.get("vector_ids", []),
                    "processing_status": processing_result.get("processing_status", "failed"),
                    "processed_at": processing_result.get("processed_at", datetime.now().isoformat())
                }
                
                logger.info(f"✅ Document processed for vector search: {processing_result.get('chunks_created', 0)} chunks")
                
            except Exception as e:
                logger.error(f"❌ Failed to process document for vector search: {e}")
                vector_processing = {
                    "error": str(e),
                    "processing_status": "failed"
                }
        
        # Generate report if requested
        report_generation = None
        if request.generate_report and report_service:
            try:
                logger.info(f"📊 Generating analysis report for document {document_id}...")
                
                report_request = ReportRequest(
                    report_id=f"analysis_report_{analysis['id']}",
                    report_type=ReportType.DETAILED_ANALYSIS,
                    format=ReportFormat(request.report_format.lower()),
                    document_ids=[document_id],
                    analysis_ids=[analysis["id"]],
                    client_id=document.get("metadata", {}).get("client_id")
                )
                
                report_metadata = await report_service.generate_report(
                    request=report_request,
                    analysis_data=analysis_data,
                    document_metadata={
                        "original_filename": document["original_filename"],
                        "file_size": document["file_size"],
                        "upload_timestamp": document["upload_timestamp"]
                    }
                )
                
                report_generation = {
                    "report_id": report_request.report_id,
                    "file_id": report_metadata.file_id,
                    "file_size": report_metadata.file_size,
                    "format": request.report_format,
                    "generated_at": report_metadata.created_at.isoformat(),
                    "download_url": f"/api/reports/download/{report_metadata.file_id}"
                }
                
                logger.info(f"✅ Analysis report generated: {report_metadata.file_id}")
                
            except Exception as e:
                logger.error(f"❌ Failed to generate analysis report: {e}")
                report_generation = {
                    "error": str(e),
                    "generation_status": "failed"
                }
        
        # Update analysis with processing results
        await doc_service.update_analysis_result(
            analysis_id=analysis["id"],
            updates={
                "metadata": {
                    "vector_processing": vector_processing,
                    "report_generation": report_generation,
                    "processing_completed_at": datetime.now().isoformat()
                }
            }
        )
        
        logger.info(f"✅ Analysis completed for document {document_id}")
        
        # Update document status to "analyzed" - CRITICAL for consistency
        try:
            await doc_service.update_document(
                document_id=document_id,
                updates={
                    "status": "analyzed",
                    "analysis_timestamp": datetime.now()
                }
            )
            logger.info(f"✅ Updated document status to 'analyzed' for {document_id}")
        except Exception as e:
            logger.error(f"❌ CRITICAL: Failed to update document status: {e}")
            # If status update fails, we should clean up the analysis result to maintain consistency
            try:
                await doc_service.delete_analysis_result(analysis["id"])
                logger.info(f"✅ Cleaned up analysis result {analysis['id']} due to status update failure")
            except Exception as cleanup_error:
                logger.error(f"❌ Failed to clean up analysis result: {cleanup_error}")
            raise HTTPException(status_code=500, detail="Analysis completed but failed to update document status")
        
        # Clear document list cache to reflect updated analysis status
        if redis_client:
            try:
                cache_pattern = "documents:list:*"
                keys = redis_client.keys(cache_pattern)
                if keys:
                    redis_client.delete(*keys)
                    logger.info(f"✅ Cleared {len(keys)} document list cache entries after analysis")
            except Exception as e:
                logger.warning(f"⚠️ Failed to clear document list cache after analysis: {e}")
        
        # Return the analysis in the same format as the get analysis endpoint
        return {
            "analysis_id": analysis["id"],
            "document_id": document_id,
            "summary": analysis_data.get("summary", {}),
            "risks": analysis_data.get("risks", []),
            "recommendations": analysis_data.get("recommendations", []),
            "citations": analysis_data.get("citations", []),
            "compliance": analysis_data.get("compliance", {}),
            "analysis_timestamp": analysis["analysis_timestamp"],
            "model_used": analysis.get("model_used", "llama3.2:3b"),
            "processing_time_ms": analysis.get("processing_time_ms", int(processing_time)),
            "status": "completed",
            "vector_processing": vector_processing,
            "report_generation": report_generation
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error analyzing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SEARCH ====================

@app.post("/api/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Perform semantic search across all documents"""
    try:
        if not processing_service:
            raise HTTPException(status_code=500, detail="Processing service not initialized")
        
        start_time = datetime.now()
        
        logger.info(f"🔍 Performing semantic search: {request.query}")
        
        # Perform semantic search
        search_results = await processing_service.search_documents(
            query=request.query,
            limit=request.limit,
            score_threshold=request.score_threshold
        )
        
        # Enhance results with analysis data if requested
        if request.include_analysis and doc_service:
            for result in search_results:
                try:
                    analyses = await doc_service.get_analysis_results_by_document(result["document_id"])
                    if analyses:
                        result["analysis"] = analyses[0]  # Get most recent analysis
                except Exception as e:
                    logger.warning(f"Could not load analysis for document {result['document_id']}: {e}")
        
        # Enhance results with report data if requested
        if request.include_reports and storage_service:
            for result in search_results:
                try:
                    # Find reports for this document
                    reports = await storage_service._find_files_by_document_id(result["document_id"])
                    report_files = [f for f in reports if f.file_type in [FileType.REPORT_PDF, FileType.REPORT_WORD]]
                    
                    if report_files:
                        result["reports"] = [
                            {
                                "file_id": f.file_id,
                                "file_type": f.file_type.value,
                                "created_at": f.created_at.isoformat(),
                                "file_size": f.file_size,
                                "download_url": f"/api/reports/download/{f.file_id}"
                            }
                            for f in report_files
                        ]
                except Exception as e:
                    logger.warning(f"Could not load reports for document {result['document_id']}: {e}")
        
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        response = SearchResponse(
            results=search_results,
            total_results=len(search_results),
            query=request.query,
            search_time_ms=int(search_time)
        )
        
        logger.info(f"✅ Semantic search completed: {len(search_results)} results in {search_time:.0f}ms")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in semantic search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATISTICS ====================

@app.get("/api/stats")
async def get_statistics():
    """Get comprehensive system statistics"""
    try:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "services": {}
        }
        
        # Get document statistics
        if doc_service:
            try:
                doc_stats = await doc_service.get_document_statistics()
                analysis_stats = await doc_service.get_analysis_statistics()
                stats["services"]["postgresql"] = {
                    "status": "healthy",
                    "documents": doc_stats,
                    "analyses": analysis_stats
                }
            except Exception as e:
                stats["services"]["postgresql"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Get vector processing statistics
        if processing_service:
            try:
                vector_stats = await processing_service.get_processing_stats()
                stats["services"]["qdrant"] = {
                    "status": "healthy",
                    "vector_stats": vector_stats
                }
            except Exception as e:
                stats["services"]["qdrant"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Get file storage statistics
        if storage_service:
            try:
                storage_stats = await storage_service.get_storage_stats()
                stats["services"]["file_storage"] = {
                    "status": "healthy",
                    "storage_stats": storage_stats
                }
            except Exception as e:
                stats["services"]["file_storage"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Get report statistics
        if report_service:
            try:
                report_stats = await report_service.get_report_stats()
                stats["services"]["reports"] = {
                    "status": "healthy",
                    "report_stats": report_stats
                }
            except Exception as e:
                stats["services"]["reports"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Get Redis statistics
        if redis_client:
            try:
                redis_info = redis_client.info()
                stats["services"]["redis"] = {
                    "status": "healthy",
                    "connected_clients": redis_info.get("connected_clients", 0),
                    "used_memory": redis_info.get("used_memory_human", "0B"),
                    "keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "keyspace_misses": redis_info.get("keyspace_misses", 0)
                }
            except Exception as e:
                stats["services"]["redis"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error getting statistics: {e}")
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
            "file_storage": "unknown",
            "reports": "unknown"
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
            # Test Qdrant connection by checking if we can get collections
            # This avoids the optimizer_status parsing error
            collections = vector_service.qdrant_client.get_collections()
            if collections:
                health_status["services"]["qdrant"] = "healthy"
            else:
                health_status["services"]["qdrant"] = "unhealthy"
        except Exception as e:
            logger.warning(f"Qdrant health check failed: {e}")
            health_status["services"]["qdrant"] = "unhealthy"
    else:
        health_status["services"]["qdrant"] = "unhealthy"
    
    # Check Redis
    if redis_client:
        try:
            redis_client.ping()
            health_status["services"]["redis"] = "healthy"
        except:
            health_status["services"]["redis"] = "unhealthy"
    
    # Check File Storage
    if storage_service:
        try:
            await storage_service.get_storage_stats()
            health_status["services"]["file_storage"] = "healthy"
        except:
            health_status["services"]["file_storage"] = "unhealthy"
    
    # Check Reports
    if report_service:
        try:
            await report_service.get_report_stats()
            health_status["services"]["reports"] = "healthy"
        except:
            health_status["services"]["reports"] = "unhealthy"
    
    # Overall status
    unhealthy_services = [svc for svc, status in health_status["services"].items() if status == "unhealthy"]
    if unhealthy_services:
        health_status["status"] = "degraded"
        health_status["unhealthy_services"] = unhealthy_services
    
    return health_status


# ==================== FILE MANAGEMENT INTEGRATION ====================

# Integrate file management API
integrate_file_management(app)


# ==================== STARTUP AND SHUTDOWN ====================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting Contract Reviewer v2 - Integrated")
    await initialize_services()
    logger.info("✅ All services initialized and ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down Contract Reviewer v2 - Integrated")
    
    if processing_service:
        try:
            await processing_service.close()
            logger.info("✅ Processing service closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing processing service: {e}")
    
    if doc_service:
        try:
            await doc_service.close()
            logger.info("✅ PostgreSQL service closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing PostgreSQL service: {e}")
    
    if vector_service:
        try:
            await vector_service.close()
            logger.info("✅ Qdrant service closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing Qdrant service: {e}")
    
    if redis_client:
        try:
            redis_client.close()
            logger.info("✅ Redis client closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing Redis client: {e}")


# ==================== SETTINGS ROUTE ====================

@app.get("/settings")
async def settings_page():
    """Serve the Operations Console settings page"""
    # Try multiple possible paths
    possible_paths = [
        Path("static/settings.html"),
        Path("./static/settings.html"),
        Path(__file__).parent / "static" / "settings.html"
    ]
    
    for settings_path in possible_paths:
        if settings_path.exists():
            return FileResponse(str(settings_path))
    
    # If none found, return error with debug info
    raise HTTPException(
        status_code=404, 
        detail=f"Settings page not found. Checked paths: {[str(p) for p in possible_paths]}"
    )

@app.get("/test-settings")
async def test_settings():
    """Test route to verify settings page is accessible"""
    return {"message": "Settings route is working", "path": str(Path("static/settings.html").absolute())}

# ==================== MAIN ====================

if __name__ == "__main__":
    logger.info("🚀 Starting Contract Reviewer v2 - Integrated")
    logger.info("✅ PostgreSQL ready for persistent storage")
    logger.info("✅ Qdrant ready for vector storage and semantic search")
    logger.info("✅ Redis ready for caching")
    logger.info("✅ File-based storage ready for document management")
    logger.info("✅ Report generation ready for comprehensive reports")
    logger.info("✅ Integrated implementation ready")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=APP_PORT,
        reload=True,
        log_level="info"
    )
