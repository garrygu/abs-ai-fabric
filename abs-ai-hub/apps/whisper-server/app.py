#!/usr/bin/env python3
"""
Whisper Server - Standalone speech-to-text service
"""

import os
import logging
from pathlib import Path
import whisper
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Whisper Server")

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
        # Validate file type
        if not file.filename.lower().endswith(('.wav', '.mp3', '.m4a', '.flac', '.ogg')):
            raise HTTPException(status_code=400, detail="Unsupported audio format")
        
        # Save uploaded file temporarily
        temp_path = Path(f"/tmp/{file.filename}")
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Transcribe using Whisper
        result = model.transcribe(str(temp_path))
        
        # Clean up temp file
        temp_path.unlink()
        
        return JSONResponse(content={
            "text": result["text"],
            "language": result.get("language", "unknown"),
            "segments": result.get("segments", [])
        })
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
