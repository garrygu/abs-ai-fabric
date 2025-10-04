#!/usr/bin/env python3
"""
Onyx AI Assistant - RAG/Agent Engine for ABS AI Hub
"""

import os
import json
import asyncio
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

import httpx
import redis
from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://vllm:8000/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "abs-local")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
ONYX_PORT = int(os.getenv("ONYX_PORT", "8000"))

# Initialize FastAPI app
app = FastAPI(title="Onyx AI Assistant", version="1.0.0")

# Initialize clients
redis_client = None
qdrant_client = None
embedding_model = None
http_client = httpx.AsyncClient(timeout=60.0)

# Pydantic models
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = "llama3.1:8b"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    app_id: Optional[str] = None

class RAGRequest(BaseModel):
    query: str
    collection: str = "documents"
    top_k: int = 5
    threshold: float = 0.7
    app_id: Optional[str] = None

class DocumentRequest(BaseModel):
    documents: List[Dict[str, Any]]
    collection: str = "documents"
    chunk_size: int = 512
    overlap: int = 50
    app_id: Optional[str] = None

class AgentRequest(BaseModel):
    input: str
    context: Optional[Dict[str, Any]] = None
    app_id: Optional[str] = None

# Initialize services
async def initialize_services():
    """Initialize Redis, Qdrant, and embedding model"""
    global redis_client, qdrant_client, embedding_model
    
    try:
        # Initialize Redis
        redis_client = redis.from_url(REDIS_URL)
        redis_client.ping()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        redis_client = None
    
    try:
        # Initialize Qdrant
        qdrant_client = QdrantClient(url=QDRANT_URL)
        qdrant_client.get_collections()
        logger.info("Qdrant connected successfully")
    except Exception as e:
        logger.error(f"Qdrant connection failed: {e}")
        qdrant_client = None
    
    try:
        # Initialize embedding model
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedding model loaded successfully")
    except Exception as e:
        logger.error(f"Embedding model loading failed: {e}")
        embedding_model = None

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await initialize_services()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    status = {
        "status": "healthy",
        "services": {
            "redis": redis_client is not None,
            "qdrant": qdrant_client is not None,
            "embedding_model": embedding_model is not None,
            "ollama": False,
            "openai": False
        }
    }
    
    # Check Ollama
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5.0)
            status["services"]["ollama"] = response.status_code == 200
    except:
        pass
    
    # Check OpenAI/vLLM
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OPENAI_BASE_URL}/models", 
                                      headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}, 
                                      timeout=5.0)
            status["services"]["openai"] = response.status_code == 200
    except:
        pass
    
    return status

# Chat endpoint
@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat with AI models"""
    try:
        # Prepare messages
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Try Ollama first
        try:
            payload = {
                "model": request.model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": request.temperature}
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("message", {}).get("content", data.get("response", ""))
                    
                    return {
                        "id": "chatcmpl_onyx_ollama",
                        "object": "chat.completion",
                        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}}],
                        "usage": {
                            "prompt_tokens": data.get("prompt_eval_count"),
                            "completion_tokens": data.get("eval_count"),
                            "total_tokens": None
                        },
                        "model": request.model,
                        "provider": "ollama"
                    }
        except Exception as e:
            logger.warning(f"Ollama chat failed: {e}")
        
        # Fallback to OpenAI/vLLM
        try:
            payload = {
                "model": request.model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{OPENAI_BASE_URL}/chat/completions",
                                           headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                                           json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        **data,
                        "provider": "openai"
                    }
        except Exception as e:
            logger.warning(f"OpenAI chat failed: {e}")
        
        raise HTTPException(status_code=503, detail="All chat providers unavailable")
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# RAG endpoint
@app.post("/rag")
async def rag_query(request: RAGRequest):
    """RAG query against vector database"""
    try:
        if not qdrant_client or not embedding_model:
            raise HTTPException(status_code=503, detail="Vector database or embedding model unavailable")
        
        # Generate query embedding
        query_embedding = embedding_model.encode(request.query).tolist()
        
        # Search in Qdrant
        search_results = qdrant_client.search(
            collection_name=request.collection,
            query_vector=query_embedding,
            limit=request.top_k,
            score_threshold=request.threshold
        )
        
        # Format results
        results = []
        for result in search_results:
            results.append({
                "content": result.payload.get("content", ""),
                "score": result.score,
                "metadata": result.payload.get("metadata", {})
            })
        
        return {
            "query": request.query,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Document ingestion endpoint
@app.post("/ingest")
async def ingest_documents(request: DocumentRequest):
    """Ingest documents into vector database"""
    try:
        if not qdrant_client or not embedding_model:
            raise HTTPException(status_code=503, detail="Vector database or embedding model unavailable")
        
        # Ensure collection exists
        try:
            qdrant_client.get_collection(request.collection)
        except:
            qdrant_client.create_collection(
                collection_name=request.collection,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
        
        # Process documents
        points = []
        for doc in request.documents:
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            
            # Chunk the text
            chunks = chunk_text(text, request.chunk_size, request.overlap)
            
            for i, chunk in enumerate(chunks):
                # Generate embedding
                embedding = embedding_model.encode(chunk).tolist()
                
                # Create point
                point = PointStruct(
                    id=f"{hash(text)}_{i}",
                    vector=embedding,
                    payload={
                        "content": chunk,
                        "metadata": {**metadata, "chunk_index": i}
                    }
                )
                points.append(point)
        
        # Upsert points
        qdrant_client.upsert(
            collection_name=request.collection,
            points=points
        )
        
        return {
            "status": "success",
            "documents_processed": len(request.documents),
            "chunks_created": len(points),
            "collection": request.collection
        }
        
    except Exception as e:
        logger.error(f"Document ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Agents endpoint
@app.get("/agents")
async def list_agents(app_id: Optional[str] = None):
    """List available agents"""
    agents = [
        {
            "id": "contract-reviewer",
            "name": "Contract Review Agent",
            "description": "Specialized contract analysis agent",
            "status": "active",
            "capabilities": ["analysis", "risk_assessment", "extraction"]
        },
        {
            "id": "document-qa",
            "name": "Document Q&A Agent",
            "description": "Answer questions about uploaded documents",
            "status": "active",
            "capabilities": ["qa", "search", "citation"]
        },
        {
            "id": "legal-research",
            "name": "Legal Research Agent",
            "description": "Research legal topics and precedents",
            "status": "active",
            "capabilities": ["research", "analysis", "synthesis"]
        }
    ]
    
    return {"agents": agents}

# Agent execution endpoint
@app.post("/agents/{agent_id}/execute")
async def execute_agent(agent_id: str, request: AgentRequest):
    """Execute a specific agent"""
    try:
        # Get agent configuration
        agents = await list_agents()
        agent = next((a for a in agents["agents"] if a["id"] == agent_id), None)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Prepare context-aware prompt
        context = request.context or {}
        prompt = f"""
        You are the {agent['name']}: {agent['description']}
        
        User Input: {request.input}
        Context: {json.dumps(context, indent=2)}
        
        Please provide a helpful response based on your capabilities: {', '.join(agent['capabilities'])}
        """
        
        # Create chat request
        chat_request = ChatRequest(
            messages=[ChatMessage(role="user", content=prompt)],
            model="llama3.1:8b",
            temperature=0.7
        )
        
        # Execute chat
        response = await chat(chat_request)
        
        return {
            "agent_id": agent_id,
            "agent_name": agent["name"],
            "input": request.input,
            "response": response["choices"][0]["message"]["content"],
            "context": context
        }
        
    except Exception as e:
        logger.error(f"Agent execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Utility functions
def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Chunk text into overlapping segments"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    
    return chunks

# Static files and templates for web UI
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Web UI endpoint
@app.get("/", response_class=HTMLResponse)
async def web_ui(request: Request):
    """Serve the web UI"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Onyx AI Assistant</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .endpoint { background: #f8f9fa; padding: 10px; margin: 10px 0; border-left: 4px solid #007bff; }
            .method { font-weight: bold; color: #007bff; }
            code { background: #f1f1f1; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Onyx AI Assistant</h1>
            <div class="status">
                <h3>Service Status</h3>
                <p>Onyx AI Assistant is running and ready to serve your AI needs!</p>
                <p><strong>Health Check:</strong> <a href="/health">/health</a></p>
            </div>
            
            <h3>Available Endpoints</h3>
            
            <div class="endpoint">
                <div class="method">POST</div> <code>/chat</code> - Chat with AI models
                <p>Send messages to AI models (Ollama, vLLM) for conversational AI.</p>
            </div>
            
            <div class="endpoint">
                <div class="method">POST</div> <code>/rag</code> - RAG queries
                <p>Search your document knowledge base using retrieval-augmented generation.</p>
            </div>
            
            <div class="endpoint">
                <div class="method">POST</div> <code>/ingest</code> - Document ingestion
                <p>Upload and process documents for your knowledge base.</p>
            </div>
            
            <div class="endpoint">
                <div class="method">GET</div> <code>/agents</code> - List agents
                <p>Get available AI agents for specialized tasks.</p>
            </div>
            
            <div class="endpoint">
                <div class="method">POST</div> <code>/agents/{agent_id}/execute</code> - Execute agent
                <p>Run specific AI agents for specialized workflows.</p>
            </div>
            
            <h3>Integration</h3>
            <p>Onyx is integrated with the ABS AI Hub Gateway at <code>/v1/onyx/*</code> endpoints.</p>
            <p>Access through Hub Gateway: <code>http://localhost:8081/v1/onyx/chat</code></p>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=ONYX_PORT)
