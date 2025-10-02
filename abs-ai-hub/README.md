# ABS AI Hub - Applications

This directory contains the applications that run on top of the ABS Core Services.

## Applications

### Contract Reviewer
AI-powered contract analysis that extracts key clauses, identifies risks, and provides citation-backed reports.

**Features:**
- PDF and DOCX document support
- OCR for scanned documents
- Policy-based compliance checking
- Risk assessment and recommendations
- Citation tracking

**Access:** http://localhost:7860

### RAG PDF Voice
Document analysis with voice interaction capabilities.

**Features:**
- PDF document processing
- Voice interaction
- RAG (Retrieval-Augmented Generation)
- Audio transcription

**Access:** http://localhost:8080

### Whisper Server
Standalone speech-to-text transcription service.

**Features:**
- Multiple audio format support
- Real-time transcription
- Language detection
- Segment-based output

**Access:** http://localhost:8001

## Hub UI
Web interface for managing and accessing all applications.

**Access:** http://localhost:3000

## Quick Start

1. **Start Core Services:**
   ```powershell
   cd C:\ABS\core
   .\start-core.ps1
   ```

2. **Run an Application:**
   ```powershell
   cd C:\ABS\abs-ai-hub\apps\contract-reviewer
   docker compose up -d
   ```

3. **Access the Application:**
   Open your browser and navigate to the application URL.

## Architecture

All applications connect to the shared Core Services via the `abs-net` Docker network:

- **Ollama**: LLM inference (http://ollama:11434)
- **Qdrant**: Vector database (http://qdrant:6333)
- **Redis**: Cache and queue (redis://redis:6379)

## Development

Each application has its own `docker-compose.yml` that:
- Joins the `abs-net` network
- Connects to Core Services via Docker DNS
- Includes health checks and dependency management

## Installation

Use the provided PowerShell scripts in the `installers/` directory to install and manage applications.
