#!/usr/bin/env python3
"""
RAG PDF Voice - Document analysis with voice interaction capabilities
Integrates with Hub Gateway for policy enforcement and service discovery
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG PDF Voice", description="Document analysis with voice interaction")

# Configuration from environment variables
HUB_GATEWAY_URL = os.getenv("HUB_GATEWAY_URL", "http://hub-gateway:8081")
WHISPER_URL = os.getenv("WHISPER_URL", "http://whisper-server:8001")
APP_PORT = int(os.getenv("APP_PORT", "8080"))

# HTTP client for gateway communication
HTTP_CLIENT = httpx.AsyncClient()

# Request/Response models
class VoiceQuery(BaseModel):
    query: str
    collection: Optional[str] = "rag-pdf-voice"

class DocumentUpload(BaseModel):
    filename: str
    content: str
    collection: Optional[str] = "rag-pdf-voice"

class TranscriptionRequest(BaseModel):
    audio_url: Optional[str] = None
    text: Optional[str] = None

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "rag-pdf-voice"}

@app.get("/catalog")
async def get_catalog_info():
    """Get catalog information for this app"""
    try:
        response = await HTTP_CLIENT.get(f"{HUB_GATEWAY_URL}/assets/rag-pdf-voice")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get catalog info: {e}")
        return {"error": "Failed to get catalog information"}

@app.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")
):
    """Transcribe audio using Whisper service"""
    logger.info(f"Transcription request from app_id: {app_id}")
    
    try:
        # Forward to Whisper service
        files = {"file": (file.filename, await file.read(), file.content_type)}
        
        response = await HTTP_CLIENT.post(
            f"{WHISPER_URL}/transcribe",
            files=files,
            timeout=httpx.Timeout(60.0)
        )
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Transcription completed for app_id: {app_id}")
        return result
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Whisper service error: status={e.response.status_code}")
        raise HTTPException(status_code=e.response.status_code, detail="Transcription failed")
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

@app.post("/query")
async def voice_query(
    request: VoiceQuery,
    app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")
):
    """Process voice query using RAG with gateway integration"""
    logger.info(f"Voice query from app_id: {app_id}: {request.query}")
    
    try:
        # Use Hub Gateway for embeddings and chat
        gateway_headers = {"X-ABS-App-Id": app_id or "rag-pdf-voice"}
        
        # Get query embedding
        embed_response = await HTTP_CLIENT.post(
            f"{HUB_GATEWAY_URL}/v1/embeddings",
            json={"input": [request.query]},
            headers=gateway_headers,
            timeout=httpx.Timeout(30.0)
        )
        embed_response.raise_for_status()
        embeddings_data = embed_response.json()
        query_vector = embeddings_data["data"][0]["embedding"]
        
        # Search documents via gateway
        search_payload = {
            "vector": query_vector,
            "limit": 5,
            "with_payload": True
        }
        
        search_response = await HTTP_CLIENT.post(
            f"{HUB_GATEWAY_URL}/v1/collections/{request.collection}/points/search",
            json=search_payload,
            headers=gateway_headers,
            timeout=httpx.Timeout(30.0)
        )
        search_response.raise_for_status()
        search_results = search_response.json()
        
        # Extract context
        context_parts = []
        if "result" in search_results:
            context_parts = [hit["payload"]["text"] for hit in search_results["result"]]
        
        context = " ".join(context_parts)
        
        # Generate response using gateway
        chat_payload = {
            "messages": [
                {"role": "system", "content": f"You are a helpful assistant for document analysis. Use the following context to answer questions about documents: {context}"},
                {"role": "user", "content": request.query}
            ],
            "temperature": 0.2,
            "max_tokens": 1024
        }
        
        chat_response = await HTTP_CLIENT.post(
            f"{HUB_GATEWAY_URL}/v1/chat/completions",
            json=chat_payload,
            headers=gateway_headers,
            timeout=httpx.Timeout(60.0)
        )
        chat_response.raise_for_status()
        chat_result = chat_response.json()
        
        return {
            "response": chat_result["choices"][0]["message"]["content"],
            "context": search_results.get("result", []),
            "model": chat_result.get("model"),
            "provider": chat_result.get("provider"),
            "query": request.query
        }
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Gateway HTTP error: status={e.response.status_code}")
        raise HTTPException(status_code=e.response.status_code, detail="Query processing failed")
    except Exception as e:
        logger.error(f"Query processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing error: {str(e)}")

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")
):
    """Upload and process document for RAG"""
    logger.info(f"Document upload from app_id: {app_id}: {file.filename}")
    
    try:
        # Read file content
        content = await file.read()
        
        # For now, assume text files - in production, you'd parse PDFs, etc.
        if file.content_type == "text/plain":
            text_content = content.decode("utf-8")
        else:
            # Placeholder for PDF parsing
            text_content = f"Document content from {file.filename} (parsing not implemented)"
        
        # Chunk the text
        chunks = chunk_text(text_content)
        
        # Use gateway for embeddings
        gateway_headers = {"X-ABS-App-Id": app_id or "rag-pdf-voice"}
        
        embed_response = await HTTP_CLIENT.post(
            f"{HUB_GATEWAY_URL}/v1/embeddings",
            json={"input": chunks},
            headers=gateway_headers,
            timeout=httpx.Timeout(60.0)
        )
        embed_response.raise_for_status()
        embeddings_data = embed_response.json()
        
        # Upload to vector store via gateway
        vectors = [item["embedding"] for item in embeddings_data["data"]]
        points = []
        
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            points.append({
                "id": f"{file.filename}_{i}",
                "vector": vector,
                "payload": {
                    "text": chunk,
                    "filename": file.filename,
                    "chunk_index": i
                }
            })
        
        upsert_payload = {"points": points}
        
        upsert_response = await HTTP_CLIENT.put(
            f"{HUB_GATEWAY_URL}/v1/collections/rag-pdf-voice/points",
            json=upsert_payload,
            headers=gateway_headers,
            timeout=httpx.Timeout(60.0)
        )
        upsert_response.raise_for_status()
        
        return {
            "status": "success",
            "filename": file.filename,
            "chunks_processed": len(chunks),
            "collection": "rag-pdf-voice"
        }
        
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Document upload error: {str(e)}")

def chunk_text(text: str, max_chars: int = 1000, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks"""
    chunks = []
    i = 0
    while i < len(text):
        chunk = text[i:i + max_chars]
        chunks.append(chunk)
        i += max_chars - overlap
    return chunks

@app.get("/collections")
async def list_collections(app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    """List available collections"""
    try:
        gateway_headers = {"X-ABS-App-Id": app_id or "rag-pdf-voice"}
        
        response = await HTTP_CLIENT.get(
            f"{HUB_GATEWAY_URL}/v1/collections",
            headers=gateway_headers,
            timeout=httpx.Timeout(30.0)
        )
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        return {"collections": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)
