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
from document_history_service import DocumentHistoryService
from file_management_api import integrate_file_management
from watch_directory_service import WatchDirectoryService
from library_files_service import LibraryFilesService
from library_api import router as library_router
from db_migration_handler import run_migrations_on_startup

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

# Lifespan context manager for startup/shutdown
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Contract Reviewer v2 - Integrated")
    await initialize_services()
    logger.info("✅ All services initialized and ready")
    yield
    # Shutdown
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
    if watch_directory_service:
        try:
            await watch_directory_service.close()
            logger.info("✅ Watch directory service closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing watch directory service: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="Contract Reviewer v2 - Integrated",
    description="Complete AI-powered contract analysis platform with PostgreSQL persistence, vector search, and file management",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
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

# Serve test-tabs page
@app.get("/test-tabs.html")
async def test_tabs():
    return FileResponse("static/test-tabs.html")

# Serve index2 page
@app.get("/index2.html")
async def index2():
    return FileResponse("static/index2.html")

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
history_service: Optional[DocumentHistoryService] = None
redis_client: Optional[redislib.Redis] = None
watch_directory_service: Optional[WatchDirectoryService] = None
library_files_service: Optional[LibraryFilesService] = None

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
    force_reanalysis: bool = False  # New parameter to force re-analysis
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
    score_threshold: float = 0.5
    include_analysis: bool = False
    include_reports: bool = False

class ChatRequest(BaseModel):
    session_id: str
    message: str
    model: Optional[str] = None

class GlobalChatRequest(BaseModel):
    message: str
    model: Optional[str] = None
    search_limit: Optional[int] = 5  # Number of documents to search
    include_analysis: Optional[bool] = True  # Whether to include analysis data

class ChatResponse(BaseModel):
    response: str
    model_used: str
    processing_time_ms: int
    citations: Optional[List[Dict[str, Any]]] = None

class GlobalChatResponse(BaseModel):
    response: str
    model_used: str
    processing_time_ms: int
    documents_used: List[Dict[str, Any]]  # Information about documents that were searched
    total_documents_searched: int

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_results: int
    query: str
    search_time_ms: int











# ==================== INITIALIZATION ====================

async def initialize_services():
    """Initialize all services"""
    global doc_service, vector_service, processing_service, storage_service, report_service, history_service, redis_client, watch_directory_service, library_files_service
    
    try:
        logger.info("🚀 Initializing Contract Reviewer v2 - Integrated Services")
        
        # Run database migrations first (idempotent)
        await run_migrations_on_startup()
        
        # Initialize PostgreSQL document service
        logger.info("🔧 Initializing PostgreSQL document service...")
        doc_service = DocumentService(POSTGRES_URL)
        await doc_service.initialize()
        logger.info("✅ PostgreSQL document service initialized")
        
        # Initialize document history service
        logger.info("🔧 Initializing document history service...")
        history_service = DocumentHistoryService(doc_service.pool)
        logger.info("✅ Document history service initialized")
        
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
        
        # Initialize watch directory service (non-blocking)
        logger.info("🔧 Initializing watch directory service...")
        try:
            watch_directory_service = WatchDirectoryService(
                db_pool=doc_service.pool,
                processing_service=processing_service,
                doc_service=doc_service,
                storage_service=storage_service
            )
            await watch_directory_service.initialize()
            logger.info("✅ Watch directory service initialized")
        except Exception as e:
            logger.warning(f"⚠️ Watch directory service failed to initialize: {e}")
            logger.warning("⚠️ App will continue without watch directory functionality")
            watch_directory_service = None
        
        # Initialize library files service
        logger.info("🔧 Initializing library files service...")
        try:
            library_files_service = LibraryFilesService(db_pool=doc_service.pool)
            await library_files_service.initialize()
            logger.info("✅ Library files service initialized")
        except Exception as e:
            logger.warning(f"⚠️ Library files service failed to initialize: {e}")
            logger.warning("⚠️ App will continue without library files functionality")
            library_files_service = None
        
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
            
            # Log upload event to history
            if history_service:
                try:
                    await history_service.log_upload(
                        document_id=document['id'],
                        filename=file.filename,
                        file_size=file_size,
                        processing_time_ms=None  # Will be calculated later
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to log upload event: {e}")
            
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
                
                # Update document record with permanent file path
                try:
                    await doc_service.update_document(
                        document_id=document["id"],
                        updates={"file_path": file_metadata.file_path}
                    )
                    logger.info(f"✅ Updated document file path: {file_metadata.file_path}")
                except Exception as update_error:
                    logger.warning(f"⚠️ Failed to update document file path: {update_error}")
                
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
                    
                    # Log vector processing event
                    if history_service:
                        try:
                            await history_service.log_vector_processing(
                                document_id=document['id'],
                                chunk_count=processing_result["chunks_created"],
                                vector_count=len(processing_result["vector_ids"]),
                                processing_time_ms=None  # Could be calculated from processing_result
                            )
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to log vector processing event: {e}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to process document for vector search: {e}")
                    vector_processing = {
                        "error": str(e),
                        "processing_status": "failed"
                    }
                    
                    # Log vector processing error
                    if history_service:
                        try:
                            await history_service.log_event(
                                document_id=document['id'],
                                event_type="vector_processing_error",
                                event_status="error",
                                event_description="Vector processing failed",
                                error_message=str(e)
                            )
                        except Exception as log_error:
                            logger.warning(f"⚠️ Failed to log vector processing error: {log_error}")
            
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
            "confidence_score": analysis.get("confidence_score", 0.0),
            "status": analysis.get("status", "completed")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting analysis for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{document_id}/content")
async def get_document_content(document_id: str):
    """Get the text content of a document for display in the document viewer"""
    try:
        logger.info(f"📄 Getting document content for: {document_id}")
        
        # Get document from database
        document = await doc_service.get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Extract text from the document file
        try:
            file_path = document['file_path']
            logger.info(f"📄 File path: {file_path}")
            logger.info(f"📄 File exists: {os.path.exists(file_path)}")
            
            text_extraction_result = processing_service.extract_text_from_file(file_path)
            document_text = text_extraction_result.get('text', '')
            
            logger.info(f"📄 Extracted text length: {len(document_text)}")
            
            if not document_text:
                return {
                    "document_id": document_id,
                    "content": "No text content available",
                    "filename": document.get("original_filename", "Unknown"),
                    "status": "empty",
                    "file_path": file_path,
                    "file_exists": os.path.exists(file_path)
                }
            
            return {
                "document_id": document_id,
                "content": document_text,
                "filename": document.get("original_filename", "Unknown"),
                "status": "success",
                "file_path": file_path,
                "text_length": len(document_text)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to extract text from document {document_id}: {e}")
            return {
                "document_id": document_id,
                "content": f"Error extracting text: {str(e)}",
                "filename": document.get("original_filename", "Unknown"),
                "status": "error",
                "file_path": document.get('file_path', 'Unknown'),
                "file_exists": os.path.exists(document.get('file_path', '')) if document.get('file_path') else False
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting document content for {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{document_id}/download")
async def download_document(document_id: str):
    """Download the original document file"""
    try:
        logger.info(f"📥 Downloading document: {document_id}")
        
        # Get document from database
        document = await doc_service.get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = document.get('file_path')
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # Return the file
        return FileResponse(
            path=file_path,
            filename=document.get('original_filename', 'document'),
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error downloading document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{document_id}/logs")
async def get_document_logs(
    document_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    log_level: Optional[str] = Query(None, description="Filter by log level"),
    search_term: Optional[str] = Query(None, description="Search in log messages")
):
    """Get operation history for a document from the database"""
    try:
        if not history_service:
            raise HTTPException(status_code=500, detail="History service not initialized")
        
        logger.info(f"📋 Fetching document history for: {document_id}")
        
        # Get history from database
        history = await history_service.get_document_history(
            document_id=document_id,
            event_type=None,  # Get all event types
            limit=limit,
            offset=offset
        )
        
        # Convert history events to log format
        logs = []
        for event in history:
            # Format log entry similar to Docker logs
            log_entry = {
                "timestamp": event.get("created_at"),
                "level": event.get("event_status", "INFO").upper(),
                "message": event.get("event_description", ""),
                "event_type": event.get("event_type"),
                "event_data": event.get("event_data"),
                "processing_time_ms": event.get("processing_time_ms"),
                "error_message": event.get("error_message")
            }
            
            # Apply filters
            if log_level and log_level.upper() != log_entry["level"]:
                continue
            
            if search_term and search_term.lower() not in log_entry["message"].lower():
                continue
            
            logs.append(log_entry)
        
        # Get total count
        total_count = len(history)
        
        return {
            "logs": logs,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": total_count > offset + limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting document history: {e}")
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
        
        # Log document deletion event
        if history_service:
            try:
                await history_service.log_document_delete(
                    document_id=document_id,
                    filename=document.get('original_filename', 'Unknown'),
                    user_id=None
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to log document deletion event: {e}")
        
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
        
        # Log analysis start event
        if history_service:
            try:
                await history_service.log_analysis_start(
                    document_id=document_id,
                    analysis_type="comprehensive",
                    user_id=None  # Could be extracted from request context
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to log analysis start event: {e}")
        
        # Get document
        document = await doc_service.get_document_by_id(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Initialize analysis variable
        analysis = None
        
        # Check if analysis already exists (unless force re-analysis is requested)
        if not request.force_reanalysis:
            existing_analyses = await doc_service.get_analysis_results_by_document(
                document_id=document_id,
                analysis_type=request.analysis_type
            )
            
            if existing_analyses:
                logger.info(f"✅ Analysis already exists for document {document_id}")
                analysis = existing_analyses[0]
            
            # Cache in Redis for quick access
            if redis_client and analysis:
                try:
                    redis_client.setex(
                        f"analysis:{analysis['id']}", 
                        86400 * 7,  # 7 days cache
                        json.dumps(analysis)
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to cache analysis in Redis: {e}")
            
            # Parse the analysis_data if it's a string and return if analysis exists
            if analysis:
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
                    "confidence_score": analysis.get("confidence_score", 0.0),
                    "status": "completed"
                }
        else:
            logger.info(f"🔄 Force re-analysis requested for document {document_id}")
        
        # Perform analysis (simplified for demo - in production, integrate with AI models)
        start_time = datetime.now()
        
        # Perform real AI analysis using Hub Gateway
        start_time = datetime.now()
        
        try:
            # Extract text from the document for analysis
            text_extraction_result = processing_service.extract_text_from_file(document['file_path'])
            document_text = text_extraction_result.get('text', '')
            
            # Prepare analysis prompt
            analysis_prompt = f"""
            Analyze the following legal document and provide a comprehensive review with specific citations:
            
            Document: {document['original_filename']}
            
            Document Content:
            {document_text[:4000]}  # Limit to first 4000 chars for API limits
            
            Please provide detailed analysis with specific citations for each finding. For every key point, risk, and recommendation, include:
            - Exact section/clause references
            - Page numbers or paragraph numbers where available
            - Specific text excerpts
            - Line references when possible
            
            Format your response as JSON with the following structure:
            {{
                "summary": {{
                    "summary": "Executive summary text",
                    "document_type": "Document type",
                    "key_points": [
                        {{
                            "point": "Key point description",
                            "citation": "Specific section, clause, or page reference",
                            "importance": "high|medium|low",
                            "text_excerpt": "Relevant text from document"
                        }}
                    ]
                }},
                "risks": [
                    {{
                        "level": "high|medium|low",
                        "description": "Risk description",
                        "section": "Relevant section or clause",
                        "citation": "Specific text excerpt or reference",
                        "impact": "Potential impact description",
                        "text_excerpt": "Exact text from document"
                    }}
                ],
                "recommendations": [
                    {{
                        "recommendation": "Specific recommendation",
                        "rationale": "Why this recommendation is important",
                        "citation": "Relevant section that supports this recommendation",
                        "priority": "high|medium|low",
                        "text_excerpt": "Supporting text from document"
                    }}
                ],
                "key_clauses": [
                    {{
                        "clause": "Clause description",
                        "type": "Type of clause (liability, termination, payment, etc.)",
                        "citation": "Exact text or section reference",
                        "significance": "Why this clause is important",
                        "text_excerpt": "Full clause text"
                    }}
                ],
                "compliance": {{
                    "gdpr_compliant": true/false,
                    "ccpa_compliant": true/false,
                    "industry_standards": ["Standard 1", "Standard 2"],
                    "compliance_issues": [
                        {{
                            "issue": "Compliance issue description",
                            "standard": "Which standard/regulation",
                            "citation": "Specific section or clause",
                            "severity": "high|medium|low",
                            "text_excerpt": "Relevant text from document"
                        }}
                    ]
                }},
                "confidence_score": 0.85
            }}
            
            IMPORTANT: Provide specific citations for every finding including:
            - Section numbers (e.g., "Section 3.2", "Clause 5.1")
            - Page numbers if available
            - Exact text excerpts in quotes
            - Paragraph or line references
            - Specific clause identifiers
            """
            
            # Call Hub Gateway for AI analysis
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://hub-gateway:8081/v1/chat/completions",
                    json={
                        "model": "llama3.2:3b",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a legal document analysis expert. Provide accurate, professional analysis of legal documents."
                            },
                            {
                                "role": "user", 
                                "content": analysis_prompt
                            }
                        ],
                        "temperature": 0.3,
                        "max_tokens": 2000
                    },
                    timeout=60.0
                )
                
            if response.status_code == 200:
                ai_response = response.json()
                ai_content = ai_response['choices'][0]['message']['content']
                
                # Debug: Log the raw AI response
                logger.info(f"🔍 Raw AI response: {ai_content[:200]}...")
                
                # Parse AI response - handle markdown-wrapped JSON
                try:
                    # Remove markdown code blocks if present
                    cleaned_content = ai_content.strip()
                    if cleaned_content.startswith('```json'):
                        cleaned_content = cleaned_content[7:]  # Remove ```json
                    if cleaned_content.startswith('```'):
                        cleaned_content = cleaned_content[3:]   # Remove ```
                    if cleaned_content.endswith('```'):
                        cleaned_content = cleaned_content[:-3]  # Remove trailing ```
                    
                    cleaned_content = cleaned_content.strip()
                    
                    # Find the first complete JSON object by looking for the closing brace
                    # This handles cases where there's extra content after the JSON
                    json_start = cleaned_content.find('{')
                    if json_start != -1:
                        # Find the matching closing brace
                        brace_count = 0
                        json_end = json_start
                        for i, char in enumerate(cleaned_content[json_start:], json_start):
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    json_end = i + 1
                                    break
                        
                        if brace_count == 0:  # Found complete JSON object
                            cleaned_content = cleaned_content[json_start:json_end]
                    
                    logger.info(f"🔍 Cleaned content: {cleaned_content[:200]}...")
                    analysis_data = json.loads(cleaned_content)
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ Failed to parse AI JSON response: {e}")
                    # Fallback if AI doesn't return valid JSON
                    analysis_data = {
                        "summary": {
                            "summary": ai_content[:200] + "...",
                            "document_type": "Contract",
                            "key_points": [
                                {
                                    "point": "AI analysis completed - manual review recommended",
                                    "citation": "AI-generated analysis",
                                    "importance": "medium",
                                    "text_excerpt": "Analysis generated by AI system"
                                }
                ]
            },
            "risks": [
                            {
                                "level": "medium", 
                                "description": "Manual review recommended", 
                                "section": "N/A",
                                "citation": "AI-generated analysis",
                                "impact": "Analysis may require human verification",
                                "text_excerpt": "AI-generated risk assessment"
                            }
            ],
            "recommendations": [
                            {
                                "recommendation": "Review AI analysis manually",
                                "rationale": "Ensure accuracy of AI-generated analysis",
                                "citation": "AI-generated recommendation",
                                "priority": "high",
                                "text_excerpt": "Manual review recommended"
                            }
                        ],
                        "key_clauses": [],
            "compliance": {
                "gdpr_compliant": True,
                "ccpa_compliant": True,
                            "industry_standards": [],
                            "compliance_issues": []
                        },
                        "confidence_score": 0.1
                    }
            else:
                raise Exception(f"AI analysis failed: {response.status_code}")
                    
        except Exception as e:
            logger.warning(f"⚠️ AI analysis failed, using fallback: {e}")
            # Fallback to enhanced mock data
            analysis_data = {
                "summary": {
                    "summary": f"Analysis of {document['original_filename']} - AI service unavailable, using template analysis",
                    "document_type": document.get("metadata", {}).get("document_type", "Contract"),
                    "key_points": [
                        {
                            "point": "Document uploaded and processed successfully",
                            "citation": "System status",
                            "importance": "high",
                            "text_excerpt": "Document processing completed"
                        },
                        {
                            "point": "AI analysis service temporarily unavailable",
                            "citation": "System status",
                            "importance": "high",
                            "text_excerpt": "AI service unavailable"
                        },
                        {
                            "point": "Template analysis provided for demonstration",
                            "citation": "System fallback",
                            "importance": "medium",
                            "text_excerpt": "Fallback analysis mode"
                        }
                    ]
                },
                "risks": [
                    {
                        "level": "medium", 
                        "description": "AI analysis unavailable - manual review recommended", 
                        "section": "System",
                        "citation": "System status",
                        "impact": "Manual review required",
                        "text_excerpt": "AI service unavailable"
                    },
                    {
                        "level": "low", 
                        "description": "Template analysis may not reflect actual document content", 
                        "section": "Analysis",
                        "citation": "System limitation",
                        "impact": "Analysis accuracy reduced",
                        "text_excerpt": "Template-based analysis"
                    }
                ],
                "recommendations": [
                    {
                        "recommendation": "Retry analysis when AI service is available",
                        "rationale": "AI service may be temporarily down",
                        "citation": "System recommendation",
                        "priority": "high",
                        "text_excerpt": "Retry analysis"
                    },
                    {
                        "recommendation": "Perform manual document review",
                        "rationale": "Ensure document is properly analyzed",
                        "citation": "System recommendation",
                        "priority": "high",
                        "text_excerpt": "Manual review required"
                    }
                ],
                "key_clauses": [],
                "compliance": {
                    "gdpr_compliant": True,
                    "ccpa_compliant": True, 
                    "industry_standards": ["Manual review recommended"],
                    "compliance_issues": []
                },
                "confidence_score": 0.1  # Low confidence due to fallback
        }
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Save analysis result to PostgreSQL
        analysis = await doc_service.create_analysis_result(
            document_id=document_id,
            analysis_type=request.analysis_type,
            analysis_data=analysis_data,
            model_used="llama3.2:3b",
            processing_time_ms=int(processing_time),
            confidence_score=analysis_data.get("confidence_score", 0.5)
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
        
        # Generate report if requested - Moved after analysis is created
        report_generation = None
        if request.generate_report and report_service and 'analysis' in locals():
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
        
        # Log analysis completion event
        if history_service:
            try:
                await history_service.log_analysis_complete(
                    document_id=document_id,
                    analysis_id=analysis.get("analysis_id", "unknown"),
                    analysis_type="comprehensive",
                    confidence_score=analysis_data.get("confidence_score", 0.5),
                    processing_time_ms=int(processing_time),
                    user_id=None
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to log analysis completion event: {e}")
        
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
        
        # Log analysis error event
        if history_service:
            try:
                await history_service.log_analysis_error(
                    document_id=document_id,
                    analysis_type="comprehensive",
                    error_message=str(e),
                    user_id=None
                )
            except Exception as log_error:
                logger.warning(f"⚠️ Failed to log analysis error event: {log_error}")
        
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
        
        # Format results to match SearchResult model
        formatted_results = []
        for result in search_results:
            # Check if document has analysis
            has_analysis = False
            if doc_service:
                try:
                    analyses = await doc_service.get_analysis_results_by_document(result["document_id"])
                    has_analysis = len(analyses) > 0
                except Exception:
                    has_analysis = False
            
            formatted_result = {
                "document_id": result.get("document_id"),
                "filename": result.get("filename", "Unknown"),
                "score": result.get("score", 0.0),
                "excerpt": result.get("chunk_text", ""),
                "upload_timestamp": result.get("upload_timestamp"),
                "has_analysis": has_analysis
            }
            
            formatted_results.append(formatted_result)
        
        response = SearchResponse(
            results=formatted_results,
            total_results=len(formatted_results),
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

# Add library API router
app.include_router(library_router)

# Add watch directory API router
@app.get("/api/watch-directories")
async def list_watch_directories_endpoint(enabled_only: bool = Query(False)):
    """List all watch directories"""
    if not watch_directory_service:
        raise HTTPException(status_code=500, detail="Watch directory service not initialized")
    
    watch_dirs = await watch_directory_service.get_watch_directories(enabled_only=enabled_only)
    return watch_dirs

@app.post("/api/watch-directories")
async def create_watch_directory_endpoint(
    path: str,
    path_type: str = "local",
    enabled: bool = True,
    recursive: bool = True,
    file_patterns: Optional[str] = None
):
    """Add a new watch directory"""
    if not watch_directory_service:
        raise HTTPException(status_code=500, detail="Watch directory service not initialized")
    
    patterns = file_patterns.split(',') if file_patterns else None
    
    try:
        watch_id = await watch_directory_service.add_watch_directory(
            path=path,
            path_type=path_type,
            enabled=enabled,
            recursive=recursive,
            file_patterns=patterns
        )
        return {"success": True, "watch_id": watch_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating watch directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/watch-directories/{watch_id}")
async def delete_watch_directory_endpoint(watch_id: str):
    """Remove a watch directory"""
    if not watch_directory_service:
        raise HTTPException(status_code=500, detail="Watch directory service not initialized")
    
    try:
        result = await watch_directory_service.remove_watch_directory(watch_id)
        return {"success": result, "message": "Watch directory removed"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting watch directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/watch-directories/{watch_id}/toggle")
async def toggle_watch_directory_endpoint(watch_id: str, enabled: bool = Query(...)):
    """Enable or disable a watch directory"""
    if not watch_directory_service:
        raise HTTPException(status_code=500, detail="Watch directory service not initialized")
    
    try:
        result = await watch_directory_service.toggle_watch_directory(watch_id, enabled)
        return {"success": result, "message": f"Watch directory {'enabled' if enabled else 'disabled'}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error toggling watch directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/watch-directories/{watch_id}/scan")
async def scan_watch_directory_endpoint(watch_id: str):
    """Manually scan a watch directory"""
    if not watch_directory_service:
        raise HTTPException(status_code=500, detail="Watch directory service not initialized")
    
    try:
        result = await watch_directory_service.manual_scan(watch_id)
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


# ==================== STARTUP AND SHUTDOWN ====================
# Now handled by lifespan context manager above


# ==================== SESSION MANAGEMENT ====================

@app.post("/api/sessions")
async def create_session(document_id: str = Query(..., description="Document ID to create session for")):
    """Create a new session for a document"""
    try:
        session_id = f"session_{document_id}_{int(datetime.now().timestamp())}"
        
        # Store session in Redis
        session_data = {
            "session_id": session_id,
            "document_id": document_id,
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat()
        }
        
        redis_client.setex(
            f"session:{session_id}",
            3600,  # 1 hour TTL
            json.dumps(session_data)
        )
        
        logger.info(f"✅ Created session {session_id} for document {document_id}")
        
        return {
            "session_id": session_id,
            "document_id": document_id,
            "created_at": session_data["created_at"]
        }
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


# ==================== CHAT API ====================

@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_contract(request: ChatRequest):
    """
    Chat with the AI about the analyzed contract.
    Uses the document context and analysis results to provide intelligent responses.
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Chat request received: session_id={request.session_id}, message='{request.message[:50]}...'")
        
        # Get the session data to understand which document we're chatting about
        session_data = redis_client.get(f"session:{request.session_id}")
        if not session_data:
            logger.error(f"Session not found: {request.session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = json.loads(session_data)
        document_id = session.get("document_id")
        
        if not document_id:
            logger.error(f"No document_id in session: {session}")
            raise HTTPException(status_code=400, detail="No document associated with this session")
        
        logger.info(f"Found document_id: {document_id}")
        
        # Get the document and its analysis data
        document_query = """
        SELECT d.*, ar.analysis_data, ar.confidence_score, ar.model_used
        FROM document_hub.documents d
        LEFT JOIN document_hub.analysis_results ar ON d.id = ar.document_id
        WHERE d.id = $1
        ORDER BY ar.created_at DESC
        LIMIT 1
        """
        
        async with doc_service.pool.acquire() as conn:
            result = await conn.fetchrow(document_query, document_id)
            
            if not result:
                logger.error(f"Document not found in database: {document_id}")
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Extract document and analysis data
            analysis_data = result['analysis_data']
            if isinstance(analysis_data, str):
                try:
                    analysis_data = json.loads(analysis_data)
                except json.JSONDecodeError:
                    analysis_data = {}
            
            doc_data = {
                'id': result['id'],
                'filename': result['filename'],
                'original_filename': result['original_filename'],
                'file_path': result['file_path'],
                'file_size': result['file_size'],
                'file_type': result['file_type'],
                'upload_timestamp': result['upload_timestamp'],
                'analysis_timestamp': result['analysis_timestamp'],
                'status': result['status'],
                'analysis_data': analysis_data,
                'confidence_score': result['confidence_score'] if result['confidence_score'] else 0.0,
                'model_used': result['model_used'] if result['model_used'] else 'unknown'
            }
        
        logger.info(f"Document data retrieved: {doc_data['original_filename']}")
        
        # Get document text content for context
        document_text = ""
        try:
            if doc_data['file_path'] and os.path.exists(doc_data['file_path']):
                # Extract text from the document using the global processing service
                extraction_result = processing_service.extract_text_from_file(doc_data['file_path'])
                document_text = extraction_result.get('text', '')
                logger.info(f"Document text extracted: {len(document_text)} characters")
        except Exception as e:
            logger.warning(f"Could not extract document text: {e}")
        
        # Prepare context for the AI
        analysis_data = doc_data.get('analysis_data', {})
        
        # Build context string
        context_parts = []
        
        if document_text:
            context_parts.append(f"DOCUMENT CONTENT:\n{document_text[:5000]}...")  # Increased to 5000 chars for better context
        
        # Add analysis data only if document is analyzed
        if analysis_data and doc_data['status'] == 'analyzed':
            context_parts.append(f"ANALYSIS SUMMARY:\n{json.dumps(analysis_data.get('summary', {}), indent=2)}")
            
            if analysis_data.get('risks'):
                context_parts.append(f"IDENTIFIED RISKS:\n{json.dumps(analysis_data['risks'], indent=2)}")
            
            if analysis_data.get('recommendations'):
                context_parts.append(f"RECOMMENDATIONS:\n{json.dumps(analysis_data['recommendations'], indent=2)}")
            
            if analysis_data.get('key_clauses'):
                context_parts.append(f"KEY CLAUSES:\n{json.dumps(analysis_data['key_clauses'], indent=2)}")
            
            if analysis_data.get('compliance'):
                context_parts.append(f"COMPLIANCE ISSUES:\n{json.dumps(analysis_data['compliance'], indent=2)}")
        
        context = "\n\n".join(context_parts)
        
        # Prepare the chat prompt based on document status
        if doc_data['status'] == 'analyzed':
            chat_prompt = f"""
You are a legal contract analysis assistant. You have access to the following contract document and its analysis:

{context}

USER QUESTION: {request.message}

Please provide a helpful, accurate response about this contract based on BOTH the original document content and the analysis above. 
- If the question is about specific clauses, risks, or recommendations, reference both the original text and the analysis data.
- If you need to cite specific sections, use the format "Section X" or "Clause Y" as appropriate.
- If the question requires information not covered in the analysis, refer to the original document content.
- Keep your response concise but informative and accurate.

RESPONSE:
"""
        else:
            chat_prompt = f"""
You are a legal contract analysis assistant. You have access to the following contract document (raw content, not yet analyzed):

{context}

USER QUESTION: {request.message}

Please provide a helpful, accurate response about this contract based on the original document content. 
- Analyze the document content directly to answer the user's question.
- If you need to cite specific sections, use the format "Section X" or "Clause Y" as appropriate.
- Provide insights about key clauses, potential risks, or important terms you identify in the document.
- Keep your response concise but informative and accurate.

RESPONSE:
"""
        
        # Determine which model to use
        model_to_use = request.model or "llama3.2:3b"
        logger.info(f"Using model: {model_to_use}")
        
        # Call Hub Gateway for AI response
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HUB_GATEWAY_URL}/v1/chat/completions",
                json={
                    "model": model_to_use,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful legal contract analysis assistant. Provide accurate, professional responses based on the contract document and analysis provided."
                        },
                        {
                            "role": "user", 
                            "content": chat_prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000
                },
                timeout=30.0
            )
        
        if response.status_code == 200:
            ai_response = response.json()
            ai_content = ai_response.get("choices", [{}])[0].get("message", {}).get("content", "I'm sorry, I couldn't process your question.")
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.info(f"Chat response generated successfully in {processing_time}ms")
            
            return ChatResponse(
                response=ai_content,
                model_used=model_to_use,
                processing_time_ms=processing_time,
                citations=None  # Could be enhanced to extract citations from the response
            )
        else:
            logger.error(f"AI service error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="AI service unavailable")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")


@app.post("/api/chat/global", response_model=GlobalChatResponse)
async def global_chat_with_documents(request: GlobalChatRequest):
    """
    Chat with AI about all documents in the system.
    Searches across multiple documents to provide comprehensive responses.
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"Global chat request received: message='{request.message[:50]}...', search_limit={request.search_limit}")
        
        # Get all documents from the database (including unanalyzed ones)
        documents_query = """
        SELECT d.*, ar.analysis_data, ar.confidence_score, ar.model_used
        FROM document_hub.documents d
        LEFT JOIN document_hub.analysis_results ar ON d.id = ar.document_id
        WHERE d.status IN ('uploaded', 'analyzed')
        ORDER BY 
            CASE WHEN d.status = 'analyzed' THEN 0 ELSE 1 END,
            COALESCE(d.analysis_timestamp, d.upload_timestamp) DESC
        LIMIT $1
        """
        
        async with doc_service.pool.acquire() as conn:
            results = await conn.fetch(documents_query, request.search_limit)
        
        if not results:
            raise HTTPException(status_code=404, detail="No documents found")
        
        logger.info(f"Found {len(results)} documents to search")
        
        # Process each document and extract relevant content
        document_contexts = []
        documents_used = []
        
        for result in results:
            try:
                # Extract document metadata
                doc_data = {
                    'id': result['id'],
                    'filename': result['filename'],
                    'original_filename': result['original_filename'],
                    'file_path': result['file_path'],
                    'file_size': result['file_size'],
                    'file_type': result['file_type'],
                    'upload_timestamp': result['upload_timestamp'],
                    'analysis_timestamp': result['analysis_timestamp'],
                    'status': result['status'],
                    'analysis_data': result['analysis_data'] if result['analysis_data'] else {},
                    'confidence_score': result['confidence_score'] if result['confidence_score'] else 0.0,
                    'model_used': result['model_used'] if result['model_used'] else 'unknown'
                }
                
                # Extract text from document if file exists
                document_text = ""
                if doc_data['file_path'] and os.path.exists(doc_data['file_path']):
                    try:
                        extraction_result = processing_service.extract_text_from_file(doc_data['file_path'])
                        document_text = extraction_result.get('text', '')
                    except Exception as e:
                        logger.warning(f"Could not extract text from {doc_data['original_filename']}: {e}")
                
                # Parse analysis data if it's a string
                analysis_data = doc_data.get('analysis_data', {})
                if isinstance(analysis_data, str):
                    try:
                        analysis_data = json.loads(analysis_data)
                    except json.JSONDecodeError:
                        analysis_data = {}
                
                # Build context for this document
                status_indicator = "✓ Analyzed" if doc_data['status'] == 'analyzed' else "○ Raw Content"
                doc_context_parts = [f"DOCUMENT: {doc_data['original_filename']} ({status_indicator})"]
                
                if document_text:
                    # Use first 2000 characters for global search to avoid token limits
                    doc_context_parts.append(f"CONTENT:\n{document_text[:2000]}...")
                
                if request.include_analysis and analysis_data and doc_data['status'] == 'analyzed':
                    if analysis_data.get('summary'):
                        doc_context_parts.append(f"SUMMARY: {json.dumps(analysis_data['summary'], indent=2)}")
                    if analysis_data.get('risks'):
                        doc_context_parts.append(f"RISKS: {json.dumps(analysis_data['risks'][:3], indent=2)}")  # Limit to top 3 risks
                    if analysis_data.get('recommendations'):
                        doc_context_parts.append(f"RECOMMENDATIONS: {json.dumps(analysis_data['recommendations'][:3], indent=2)}")  # Limit to top 3
                
                doc_context = "\n".join(doc_context_parts)
                document_contexts.append(doc_context)
                
                documents_used.append({
                    'id': doc_data['id'],
                    'filename': doc_data['original_filename'],
                    'status': doc_data['status'],
                    'has_content': bool(document_text),
                    'has_analysis': bool(analysis_data) and doc_data['status'] == 'analyzed',
                    'confidence_score': doc_data['confidence_score'] if doc_data['status'] == 'analyzed' else None
                })
                
            except Exception as e:
                logger.warning(f"Error processing document {result['id']}: {e}")
                continue
        
        if not document_contexts:
            raise HTTPException(status_code=404, detail="No documents could be processed")
        
        # Combine all document contexts
        combined_context = "\n\n---\n\n".join(document_contexts)
        
        # Prepare the global chat prompt
        chat_prompt = f"""
You are a legal contract analysis assistant with access to multiple contract documents. You have been provided with information from {len(documents_used)} documents:

{combined_context}

USER QUESTION: {request.message}

Please provide a comprehensive response about the contracts based on the information above. 
- If the question is about specific documents, mention which document(s) contain the relevant information.
- If comparing across documents, highlight similarities and differences.
- If asking about general patterns, analyze across all provided documents.
- Cite specific document names when referencing information.
- Keep your response informative and well-structured.

RESPONSE:
"""
        
        # Determine which model to use
        model_to_use = request.model or "llama3.2:3b"
        logger.info(f"Using model: {model_to_use}")
        
        # Call Hub Gateway for AI response
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{HUB_GATEWAY_URL}/v1/chat/completions",
                json={
                    "model": model_to_use,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful legal contract analysis assistant. Provide accurate, comprehensive responses based on the contract documents provided. Always cite specific document names when referencing information."
                        },
                        {
                            "role": "user", 
                            "content": chat_prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1500  # Increased for global responses
                },
                timeout=60.0  # Increased timeout for global search
            )
        
        if response.status_code == 200:
            ai_response = response.json()
            ai_content = ai_response.get("choices", [{}])[0].get("message", {}).get("content", "I'm sorry, I couldn't process your question.")
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            logger.info(f"Global chat response generated successfully in {processing_time}ms")
            
            return GlobalChatResponse(
                response=ai_content,
                model_used=model_to_use,
                processing_time_ms=processing_time,
                documents_used=documents_used,
                total_documents_searched=len(documents_used)
            )
        else:
            logger.error(f"AI service error: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="AI service unavailable")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Global chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Global chat processing error: {str(e)}")


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

# ==================== SEMANTIC SEARCH API ====================

class SearchRequest(BaseModel):
    query: str
    limit: int = 10

# Simplified SearchResult to accept dicts
class SearchResult(BaseModel):
    document_id: str
    filename: str
    score: float
    excerpt: str
    upload_timestamp: Optional[str] = None
    has_analysis: bool
    
    # Allow creation from dict
    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)

class SearchResponse(BaseModel):
    results: List[dict]  # Change to dict instead of SearchResult
    total_results: int
    query: str
    search_time_ms: int

# DUPLICATE ENDPOINT - REMOVED (original at line 1767)
# The entire function from lines 2502-2605 was a duplicate
# and is removed to avoid route conflicts

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
