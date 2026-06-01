# ABS AI Fabric

A local AI platform for running AI workloads on ABS workstations — no cloud required. ABS AI Fabric provides shared core services, a unified API gateway, asset management, and a growing catalog of applications including legal document review, chat assistants, and system observability.

All processing stays on-device. Data never leaves the workstation.

## Architecture

ABS AI Fabric follows an **asset-based, interface-driven** design: applications bind to stable interfaces (LLM runtime, vector store, cache) rather than specific implementations. The Hub Gateway resolves bindings at runtime and orchestrates auto-wake for on-demand services.

```
Applications (Hub UI, Workstation Console, Contract Reviewer, …)
        ↓
Hub Gateway (:8081) — OpenAI-compatible API, asset registry, service orchestration
        ↓
Core Services (Ollama, Qdrant, Redis, PostgreSQL)
        ↓
NVIDIA GPU + local storage
```

### Core Services (Always-On)

| Service | Port | Description |
|---------|------|-------------|
| **Hub Gateway** | 8081 | Unified API, asset registry, model management, GPU metrics |
| **Ollama** | 11434 | LLM runtime for local inference |
| **Qdrant** | 6333 | Vector database for semantic search |
| **Redis** | 6379 | Cache and session storage |
| **PostgreSQL** | 5432 | Document metadata and application data |

Optional extended assets (Whisper, OCR, vLLM, etc.) are registered under `assets/` and activated on demand via the gateway.

See [Core README](core/README.md) for gateway API endpoints and service management.

## Project Structure

```
abs-ai-fabric/
├── core/                       # Core services (Docker Compose, Hub Gateway)
├── abs-ai-hub/                 # Applications and admin UI
│   ├── hub-ui-v2/              # AI Fabric admin UI (Vue 3)
│   ├── apps/                   # Individual applications
│   │   ├── abs_workstation_console/
│   │   ├── contract-reviewer-v2/
│   │   ├── legal-assistant/
│   │   ├── onyx-suite/
│   │   └── whisper-server/
│   └── apps-registry.json      # Application catalog for the Hub
├── assets/                     # Asset definitions (models, services, tools)
├── core-interfaces/            # Versioned interface contracts
└── docs/                       # Architecture, API, and operational guides
```

## Quick Start

### Prerequisites

- Windows 10/11 with Docker Desktop (WSL2 recommended)
- NVIDIA GPU with CUDA drivers (for LLM inference)
- Node.js 18+ and npm (for Hub UI and Workstation Console)
- PowerShell (for core service scripts on Windows)

> For detailed Windows setup — Docker Desktop, WSL2, GPU passthrough — see the [Windows Setup Guide](docs/guides/Windows_Setup_Guide.md).

### 1. Start Core Services

```powershell
cd core
copy .env.example .env   # first time only
.\start-core.ps1
```

Or with Docker Compose directly:

```powershell
cd core
docker compose up -d
```

Verify the gateway:

```powershell
curl http://localhost:8081/health
```

### 2. Start AI Fabric (Admin UI)

```powershell
cd abs-ai-hub/hub-ui-v2
npm install   # first time only
npm run dev
```

**Access:** http://localhost:5173

### 3. Start Workstation Console (optional)

Real-time system metrics, GPU observability, and CES showcase mode.

```powershell
cd abs-ai-hub/apps/abs_workstation_console
npm install   # first time only
npm run dev
```

**Access:** http://localhost:5200

### Windows one-click start

Run `Start.bat` from the repo root to launch core services, AI Fabric, and Workstation Console in separate windows.

For a full CES demo setup, see the [CES Setup Guide](docs/ces/CES_SETUP_GUIDE.md).

## Applications

| Application | Port | Description |
|-------------|------|-------------|
| **AI Fabric** (hub-ui-v2) | 5173 | Admin UI — apps, assets, observability, service controls |
| **Workstation Console** | 5200 | System metrics, GPU workloads, attract-mode showcase |
| **Contract Reviewer v2** | 8082 | AI contract analysis with document library and risk assessment |
| **Legal Assistant** | 8050 | Chat, RAG, and legal document research |
| **Onyx Suite** | 8150 | Full Onyx deployment for chat and knowledge management |
| **Whisper Server** | 8001 | Speech-to-text transcription |

Start a containerized app from its directory:

```powershell
cd abs-ai-hub/apps/contract-reviewer-v2
docker compose up -d
```

All containerized apps join the `abs-net` Docker network and connect to core services via the gateway.

## Documentation

Full documentation index: [docs/README.md](docs/README.md)

**Team handoff:** [项目移交说明](docs/项目移交说明.md) — project purpose, architecture, key docs, and operational notes for new teams.

### Getting started

- [Core Services Guide](docs/guides/core_services_guide.md)
- [CES Setup Guide](docs/ces/CES_SETUP_GUIDE.md)
- [Platform Overview](docs/ces/ABS_AI_FABRIC_OVERVIEW.md)

### Architecture

- [Project Structure & Evolvable Core](docs/architecture/project_structure_and_evolvable_core.md)
- [Architecture and Component View](docs/architecture/Architecture_and_Component_View.md)
- [Auto-Wake Architecture](docs/architecture/Flexible%20Core%20Services%20and%20Auto-Wake%20Architecture.md)

### API & integration

- [API Reference](docs/api/API_Reference_and_Usage_Scenarios.md)
- [Hub Gateway Implementation](docs/guides/hub_gateway_implementation_guide.md)
- [App Manifest Specification](docs/architecture/app_manifest_specification.md)

### Onyx

- [Onyx Integration Guide](docs/guides/Onyx_Integration_Guide.md)
- [Onyx Chat User Manual](docs/guides/Onyx_Chat_User_Manual.md)
- [Onyx Quick Reference](docs/guides/Onyx_Quick_Reference.md)

## Development

### Adding a new application

1. Create an app directory under `abs-ai-hub/apps/`
2. Add `docker-compose.yml` that joins the `abs-net` network
3. Add an `app.manifest.json` following the [app manifest spec](docs/architecture/app_manifest_specification.md)
4. Register the app in `abs-ai-hub/apps-registry.json`

Applications should call the Hub Gateway (`http://hub-gateway:8081`) rather than connecting directly to core service containers.

### Core service management

```powershell
cd core
.\start-core.ps1          # Start all core services
.\stop-core.ps1            # Stop all core services
.\update-core.ps1          # Rebuild and update
docker compose ps          # Check status
```

## Contributing

1. Fork the repository
2. Create a feature branch (`feat/scope-brief`)
3. Make your changes and test against core services
4. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions, open an issue in the repository.
