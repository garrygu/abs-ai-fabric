# AI Workstation - Legal

A comprehensive AI-powered workstation for legal professionals, featuring contract review, document analysis, and legal research capabilities.

## Architecture

This workstation follows a **Core Services** strategy with shared infrastructure:

### Core Services (Always-On)
- **LLM Runtime**: Ollama or vLLM for language model inference
- **Qdrant**: Vector database for semantic search and document embeddings
- **Redis**: Cache and message queue for performance optimization
- **Onyx**: AI assistant with chat interface, RAG capabilities, and agent management

### Optional Services (On-Demand)
- **Parser/OCR**: Document parsing and optical character recognition
- **MinIO**: Object storage for document management
- **Whisper**: Speech-to-text transcription
- **TTS/Translation**: Text-to-speech and translation services
- **Redaction/PII**: Privacy and sensitive data detection

## Project Structure

```
C:\ABS\
├── core\                    # Core Services (shared infrastructure)
│   ├── core.yml            # Core services definition
│   ├── start-core.ps1      # Start core services
│   ├── stop-core.ps1       # Stop core services
│   └── update-core.ps1     # Update core services
│
└── abs-ai-hub\             # Applications
    ├── apps\               # Individual applications
    │   ├── contract-reviewer\
    │   ├── rag-pdf-voice\
    │   └── whisper-server\
    ├── hub-ui\             # Web interface
    └── installers\         # Installation scripts
```

## Quick Start

### 1. Start Core Services
```powershell
cd C:\ABS\core
.\start-core.ps1
```

### 2. Run Applications
```powershell
cd C:\ABS\abs-ai-hub\apps\contract-reviewer
docker compose up -d
```

### 3. Access Applications
- **ABS AI Hub**: http://localhost:3000 (Main interface)
- **Onyx Chat**: http://localhost:8000 (AI assistant with chat interface)
- **Contract Reviewer**: http://localhost:7860
- **RAG PDF Voice**: http://localhost:8080

## Requirements

- Windows 10 Pro or later
- Docker Desktop with WSL2 integration
- NVIDIA GPU driver with CUDA support (recommended)
- PowerShell (Admin) for script execution

## Applications

### Contract Reviewer
AI-powered contract analysis that extracts key clauses, identifies risks, and provides citation-backed reports.

**Features:**
- PDF and DOCX document support
- OCR for scanned documents
- Policy-based compliance checking
- Risk assessment and recommendations
- Citation tracking

### RAG PDF Voice
Document analysis with voice interaction capabilities.

### Whisper Server
Speech-to-text transcription service for audio processing.

### Onyx AI Assistant
AI assistant with built-in chat interface, RAG capabilities, and agent management.

**Features:**
- Natural language chat interface
- Document upload and analysis
- RAG queries against knowledge base
- Custom agent creation and management
- Multi-model support (Ollama, vLLM)
- Web search integration
- Code execution capabilities

## Documentation

### Onyx Integration
- **[Onyx Integration Guide](core/docs/Onyx_Integration_Guide.md)**: Complete technical integration guide
- **[Onyx Chat User Manual](core/docs/Onyx_Chat_User_Manual.md)**: User interface guide
- **[Onyx Quick Reference](core/docs/Onyx_Quick_Reference.md)**: Quick reference card

### Core Services
- **[Core Services Guide](core/docs/core_services_guide.md)**: Core service management
- **[Hub Gateway Implementation](core/docs/hub_gateway_implementation_guide.md)**: Gateway configuration
- **[Auto-Wake Architecture](core/docs/Flexible%20Core%20Services%20and%20Auto-Wake%20Architecture.md)**: Service orchestration

## Development

### Adding New Applications
1. Create app directory in `abs-ai-hub/apps/`
2. Add `docker-compose.yml` that joins `abs-net` network
3. Configure environment variables to connect to Core services
4. Add app manifest to `apps-registry.json`

### Core Service Management
- **Start**: `.\start-core.ps1`
- **Stop**: `.\stop-core.ps1`
- **Update**: `.\update-core.ps1`
- **Status**: `docker compose -f core.yml ps`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with Core services
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions, please create an issue in the repository.
