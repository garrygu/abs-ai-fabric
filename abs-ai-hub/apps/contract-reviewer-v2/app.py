import os, json, uuid, hashlib, tempfile, asyncio
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

# Configuration
APP_PORT = int(os.getenv("APP_PORT", "8080"))
HUB_GATEWAY_URL = os.getenv("HUB_GATEWAY_URL", "http://hub-gateway:8081")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
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
    title="Contract Reviewer v2",
    description="Professional AI-powered contract analysis platform",
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

# HTTP client for gateway communication
http_client = httpx.AsyncClient(timeout=60)

# Redis client for caching
redis_client = None
try:
    redis_client = redislib.from_url(REDIS_URL)
    redis_client.ping()
except Exception:
    redis_client = None

# Global state
review_sessions = {}
document_cache = {}
analysis_results_cache = {}  # Cache for saved analysis results

# Pydantic models
class DocumentUpload(BaseModel):
    filename: str
    content_type: str
    size: int

class ReviewRequest(BaseModel):
    document_id: str
    model: Optional[str] = None
    analysis_type: str = "comprehensive"  # comprehensive, quick, risk-focused
    include_recommendations: bool = True

class ReviewResult(BaseModel):
    document_id: str
    session_id: str
    summary: Dict[str, Any]
    risks: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    clauses: List[Dict[str, Any]]
    confidence_score: float
    created_at: datetime

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: str
    message: str
    model: Optional[str] = None

# Utility functions
def get_file_hash(file_content: bytes) -> str:
    """Generate hash for file content"""
    return hashlib.sha256(file_content).hexdigest()

def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from PDF file"""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading PDF: {str(e)}")

def extract_text_from_docx(file_path: Path) -> str:
    """Extract text from DOCX file"""
    try:
        doc = DocxDocument(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading DOCX: {str(e)}")

def extract_text_from_file(file_path: Path) -> str:
    """Extract text from supported file types"""
    suffix = file_path.suffix.lower()
    if suffix == '.pdf':
        return extract_text_from_pdf(file_path)
    elif suffix == '.docx':
        return extract_text_from_docx(file_path)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

async def get_embedding(text: str, model: str = None) -> List[float]:
    """Get embedding for text using gateway"""
    try:
        payload = {
            "input": [text],
            "override_model": model
        }
        response = await http_client.post(
            f"{HUB_GATEWAY_URL}/v1/embeddings",
            json=payload,
            headers={"X-ABS-App-Id": "contract-reviewer-v2"}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()
        return data["data"][0]["embedding"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting embedding: {str(e)}")

async def chat_with_model(messages: List[Dict[str, str]], model: str = None) -> str:
    """Chat with LLM using gateway"""
    try:
        payload = {
            "messages": messages,
            "model": model,
            "temperature": 0.2,
            "max_tokens": 4000
        }
        response = await http_client.post(
            f"{HUB_GATEWAY_URL}/v1/chat/completions",
            json=payload,
            headers={"X-ABS-App-Id": "contract-reviewer-v2"}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with chat: {str(e)}")

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    
    return chunks

def save_analysis_result(document_id: str, analysis_data: Dict[str, Any]) -> str:
    """Save analysis result to Redis and local cache"""
    analysis_id = str(uuid.uuid4())
    analysis_data["analysis_id"] = analysis_id
    analysis_data["document_id"] = document_id
    analysis_data["saved_at"] = datetime.now().isoformat()
    
    # Save to Redis if available
    if redis_client:
        try:
            redis_client.setex(
                f"analysis:{analysis_id}", 
                86400 * 30,  # 30 days expiry
                json.dumps(analysis_data)
            )
            redis_client.setex(
                f"document_analysis:{document_id}", 
                86400 * 30,  # 30 days expiry
                analysis_id
            )
        except Exception as e:
            print(f"Error saving to Redis: {e}")
    
    # Save to local cache
    analysis_results_cache[analysis_id] = analysis_data
    
    return analysis_id

def load_analysis_result(document_id: str) -> Optional[Dict[str, Any]]:
    """Load analysis result for a document"""
    # Try Redis first
    if redis_client:
        try:
            analysis_id = redis_client.get(f"document_analysis:{document_id}")
            if analysis_id:
                analysis_data = redis_client.get(f"analysis:{analysis_id.decode()}")
                if analysis_data:
                    return json.loads(analysis_data)
        except Exception as e:
            print(f"Error loading from Redis: {e}")
    
    # Try local cache
    for analysis_id, analysis_data in analysis_results_cache.items():
        if analysis_data.get("document_id") == document_id:
            return analysis_data
    
    return None

def get_analysis_result(analysis_id: str) -> Optional[Dict[str, Any]]:
    """Get analysis result by ID"""
    # Try Redis first
    if redis_client:
        try:
            analysis_data = redis_client.get(f"analysis:{analysis_id}")
            if analysis_data:
                return json.loads(analysis_data)
        except Exception as e:
            print(f"Error loading from Redis: {e}")
    
    # Try local cache
    return analysis_results_cache.get(analysis_id)

async def analyze_document_comprehensive(document_text: str, model: str = None) -> Dict[str, Any]:
    """Comprehensive document analysis"""
    
    # Split document into chunks for analysis
    chunks = chunk_text(document_text)
    
    # Analyze each chunk
    analysis_prompts = {
        "summary": "Provide a concise executive summary of this contract section, highlighting key terms, parties, and obligations.",
        "risks": "Identify potential legal risks, ambiguities, or problematic clauses in this contract section. Rate each risk as Low, Medium, or High.",
        "clauses": "Extract and categorize key clauses from this contract section (e.g., liability, termination, payment, confidentiality).",
        "recommendations": "Provide specific recommendations for improving this contract section, including suggested language changes."
    }
    
    results = {
        "summary": "",
        "risks": [],
        "clauses": [],
        "recommendations": []
    }
    
    for chunk in chunks[:5]:  # Limit to first 5 chunks for performance
        for analysis_type, prompt in analysis_prompts.items():
            messages = [
                {"role": "system", "content": "You are a legal expert analyzing contracts. Provide detailed, professional analysis."},
                {"role": "user", "content": f"{prompt}\n\nContract section:\n{chunk}"}
            ]
            
            try:
                response = await chat_with_model(messages, model)
                results[analysis_type] += f"\n\n{response}"
            except Exception as e:
                print(f"Error analyzing chunk: {e}")
                continue
    
    return results

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint - serve the frontend"""
    return FileResponse("static/index.html")

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/models")
async def get_available_models():
    """Get available models from gateway"""
    try:
        response = await http_client.get(
            f"{HUB_GATEWAY_URL}/admin/models",
            params={"app_id": "contract-reviewer-v2"}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting models: {str(e)}")

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    try:
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.pdf', '.docx']:
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        
        # Read file content
        content = await file.read()
        file_hash = get_file_hash(content)
        
        # Check if file already exists
        if file_hash in document_cache:
            return {
                "document_id": file_hash,
                "filename": file.filename,
                "status": "cached",
                "message": "Document already processed"
            }
        
        # Save file temporarily
        temp_path = UPLOADS_DIR / f"{file_hash}{file_ext}"
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Extract text
        try:
            text = extract_text_from_file(temp_path)
        except Exception as e:
            temp_path.unlink()  # Clean up
            raise HTTPException(status_code=400, detail=str(e))
        
        # Store in cache
        document_cache[file_hash] = {
            "filename": file.filename,
            "text": text,
            "uploaded_at": datetime.now().isoformat(),
            "file_path": str(temp_path)
        }
        
        return {
            "document_id": file_hash,
            "filename": file.filename,
            "text_length": len(text),
            "status": "processed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/api/review")
async def review_document(request: ReviewRequest):
    """Perform comprehensive document review"""
    try:
        # Get document from cache
        if request.document_id not in document_cache:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = document_cache[request.document_id]
        document_text = document["text"]
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Perform analysis
        analysis_results = await analyze_document_comprehensive(
            document_text, 
            request.model
        )
        
        # Create review result
        review_result = ReviewResult(
            document_id=request.document_id,
            session_id=session_id,
            summary=analysis_results,
            risks=[],  # Will be populated from analysis
            recommendations=[],  # Will be populated from analysis
            clauses=[],  # Will be populated from analysis
            confidence_score=0.85,  # Placeholder
            created_at=datetime.now()
        )
        
        # Store in session
        review_sessions[session_id] = {
            "document_id": request.document_id,
            "document_text": document_text,
            "review_result": review_result.dict(),
            "created_at": datetime.now().isoformat()
        }
        
        # Save analysis result persistently
        analysis_id = save_analysis_result(request.document_id, review_result.dict())
        
        # Add analysis_id to the response
        result_dict = review_result.dict()
        result_dict["analysis_id"] = analysis_id
        
        return result_dict
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reviewing document: {str(e)}")

@app.post("/api/chat")
async def chat_with_document(request: ChatRequest):
    """Chat with the document using AI"""
    try:
        # Get session
        if request.session_id not in review_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = review_sessions[request.session_id]
        document_text = session["document_text"]
        
        # Prepare context
        context = f"Document context:\n{document_text[:2000]}..."  # Limit context
        
        messages = [
            {"role": "system", "content": "You are a legal assistant helping to analyze contracts. Answer questions based on the provided document context."},
            {"role": "user", "content": f"{context}\n\nQuestion: {request.message}"}
        ]
        
        # Get response from model
        response = await chat_with_model(messages, request.model)
        
        return {
            "response": response,
            "session_id": request.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get review session details"""
    if session_id not in review_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return review_sessions[session_id]

@app.get("/api/sessions")
async def list_sessions():
    """List all review sessions"""
    return {
        "sessions": [
            {
                "session_id": sid,
                "document_id": session["document_id"],
                "created_at": session["created_at"]
            }
            for sid, session in review_sessions.items()
        ]
    }

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a review session"""
    if session_id not in review_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del review_sessions[session_id]
    return {"status": "deleted", "session_id": session_id}

@app.get("/api/documents")
async def list_documents(limit: int = 10, offset: int = 0):
    """List uploaded documents with pagination"""
    # Convert document cache to list and sort by upload date (newest first)
    all_documents = []
    for doc_id, doc in document_cache.items():
        # Check if analysis exists for this document
        analysis_result = load_analysis_result(doc_id)
        
        document_info = {
            "document_id": doc_id,
            "filename": doc["filename"],
            "uploaded_at": doc["uploaded_at"],
            "text_length": len(doc["text"])
        }
        
        if analysis_result:
            document_info["has_analysis"] = True
            document_info["analysis_id"] = analysis_result["analysis_id"]
            document_info["analysis_saved_at"] = analysis_result["saved_at"]
        else:
            document_info["has_analysis"] = False
        
        all_documents.append(document_info)
    
    # Sort by upload date (newest first)
    all_documents.sort(key=lambda x: x["uploaded_at"], reverse=True)
    
    # Apply pagination
    total_count = len(all_documents)
    paginated_documents = all_documents[offset:offset + limit]
    
    return {
        "documents": paginated_documents,
        "total_count": total_count,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total_count
    }

@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    if document_id not in document_cache:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Clean up file
    doc = document_cache[document_id]
    if "file_path" in doc:
        try:
            Path(doc["file_path"]).unlink()
        except:
            pass
    
    del document_cache[document_id]
    
    # Clean up related sessions
    sessions_to_delete = [
        sid for sid, session in review_sessions.items()
        if session["document_id"] == document_id
    ]
    for sid in sessions_to_delete:
        del review_sessions[sid]
    
    return {"status": "deleted", "document_id": document_id}

@app.get("/api/analysis/{document_id}")
async def get_saved_analysis(document_id: str):
    """Get saved analysis result for a document"""
    analysis_result = load_analysis_result(document_id)
    if not analysis_result:
        raise HTTPException(status_code=404, detail="No saved analysis found for this document")
    
    return analysis_result

@app.get("/api/export/{session_id}")
async def export_review(session_id: str, format: str = "json"):
    """Export review results"""
    if session_id not in review_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = review_sessions[session_id]
    
    if format == "json":
        return JSONResponse(content=session["review_result"])
    elif format == "pdf":
        # TODO: Implement PDF export
        raise HTTPException(status_code=501, detail="PDF export not yet implemented")
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)

