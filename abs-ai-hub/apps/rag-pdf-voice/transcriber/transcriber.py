#!/usr/bin/env python3
"""
Transcriber service for RAG PDF Voice application
Handles audio transcription using Whisper
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Optional
import whisper
from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Transcriber Service")

# Load Whisper model
MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")
model = whisper.load_model(MODEL_SIZE)

@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "model": MODEL_SIZE}

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe uploaded audio file"""
    try:
        # Save uploaded file temporarily
        temp_path = Path(f"/tmp/{file.filename}")
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Transcribe using Whisper
        result = model.transcribe(str(temp_path))
        
        # Clean up temp file
        temp_path.unlink()
        
        return {
            "text": result["text"],
            "language": result.get("language", "unknown"),
            "segments": result.get("segments", [])
        }
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
