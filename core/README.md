# ABS Core Services

The foundational infrastructure layer providing AI runtime services, vector storage, caching, and the unified API gateway. All applications connect to these services via the `abs-net` Docker network.

## Services

| Service | Port | Description |
|---------|------|-------------|
| **Gateway** | 8081 | Unified API gateway for all AI operations |
| **Ollama** | 11434 | LLM runtime for local model inference |
| **Qdrant** | 6333 | Vector database for semantic search |
| **Redis** | 6379 | Caching and session storage |

## Quick Start

```powershell
cd c:\ABS\core

# Start all core services
.\start-core.ps1

# Or with Docker Compose
docker compose up -d
```

## Stop Services

```powershell
cd c:\ABS\core
.\stop-core.ps1

# Or with Docker Compose
docker compose down
```

## Update Core

```powershell
cd c:\ABS\core
.\update-core.ps1
```

## Gateway API

The Hub Gateway provides a unified API at `http://localhost:8081`:

### Health & Status
- `GET /health` - Health check
- `GET /admin/health` - Detailed service health
- `GET /admin/services` - Service statuses

### Models
- `GET /v1/models` - List available models
- `GET /admin/models` - Model management
- `POST /v1/models/{name}/load` - Load model to GPU
- `POST /v1/models/{name}/unload` - Unload model

### Chat & Completions
- `POST /v1/chat/completions` - OpenAI-compatible chat API
- `POST /v1/completions` - Completion API

### Assets
- `GET /v1/assets` - List registered assets
- `GET /v1/apps` - List applications
- `POST /admin/assets/reload` - Reload asset registry

### GPU Metrics
- `GET /gpu/metrics` - Real-time GPU utilization
- `GET /gpu/vram` - VRAM usage statistics

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Applications                          │
│  (Workstation Console, AI Fabric, Contract Reviewer)    │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Hub Gateway (:8081)                    │
│  - Unified API interface                                 │
│  - OpenAI-compatible endpoints                           │
│  - Asset registry management                             │
│  - Service health monitoring                             │
└────────┬──────────┬──────────┬──────────┬───────────────┘
         │          │          │          │
         ▼          ▼          ▼          ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Ollama  │ │ Qdrant  │ │ Redis   │ │ GPU     │
   │ :11434  │ │ :6333   │ │ :6379   │ │ Metrics │
   │ (LLM)   │ │(Vectors)│ │ (Cache) │ │ Server  │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

## Directory Structure

```
core/
├── docker-compose.yml    # Multi-service Docker config
├── .env                  # Environment configuration
├── start-core.ps1        # Windows start script
├── stop-core.ps1         # Windows stop script
├── update-core.ps1       # Update/rebuild script
├── bindings.yaml         # Service bindings config
└── gateway/              # Gateway service
    ├── app.py            # FastAPI application
    ├── routers/          # API route handlers
    ├── requirements.txt  # Python dependencies
    └── gpu_metrics_server.py  # GPU monitoring
```

## Configuration

Environment variables in `.env`:

```env
OLLAMA_HOST=http://abs-ollama:11434
QDRANT_URL=http://abs-qdrant:6333
REDIS_URL=redis://abs-redis:6379/0
ASSETS_PATH=/assets/registry
```

## Network

All services connect via the `abs-net` Docker network:

```bash
# Inspect network
docker network inspect abs-net

# Apps connect using service names:
# - http://abs-ollama:11434
# - http://abs-qdrant:6333
# - redis://abs-redis:6379
# - http://hub-gateway:8081
```

## Troubleshooting

### Services not starting
```powershell
# Check container status
docker ps -a | Select-String "abs-"

# View logs
docker logs abs-core-hub-gateway-1
```

### Gateway not responding
```powershell
# Check if gateway is healthy
curl http://localhost:8081/health

# Check container logs
docker logs abs-core-hub-gateway-1 --tail 50
```

### GPU metrics unavailable
```powershell
# Ensure GPU metrics server is running
python gateway/gpu_metrics_server.py
```
