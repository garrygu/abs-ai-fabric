# ABS AI Hub - Applications

This directory contains all user-facing applications that consume the core services (Ollama, Qdrant, Redis, Hub Gateway).

## Quick Access

```
http://localhost:5173/    → AI Fabric (Admin UI)
http://localhost:5200/    → ABS Workstation Console
http://localhost:8082/    → Contract Reviewer
http://localhost:8081/    → Gateway API
```

## Applications

### 🖥️ **ABS Workstation Console** (`:5200`)
**Location:** `abs-ai-hub/apps/abs_workstation_console/`

Flagship CES showcase application featuring:
- Real-time GPU, CPU, RAM monitoring
- AI workload visualization
- Installed models display
- **Attract Mode** - Auto-activating showcase with WebGPU particle effects
- Multi-scene visual demonstrations
- Touch-to-engage interactivity

**Start:** `cd abs_workstation_console && npm run dev`

---

### ⚙️ **AI Fabric (Hub UI)** (`:5173`)
**Location:** `abs-ai-hub/hub-ui-v2/`

Modern admin interface for managing AI workloads:
- Applications management and launching
- Asset registry (models, services)
- Observability dashboard
- Admin controls (service start/stop, cache management)
- CES Demo Mode for trade shows

**Start:** `cd ../hub-ui-v2 && npm run dev`

---

### ⚖️ **Contract Reviewer** (`:8082`)
**Location:** `abs-ai-hub/apps/contract-reviewer-v2/`

Professional legal document analysis:
- PDF and DOCX upload with vector processing
- AI-powered contract analysis
- Risk identification and flagging
- Citation-backed recommendations
- Semantic document search
- Export results as JSON

**Start:** `cd contract-reviewer-v2 && docker compose up -d`

---

### 🤖 Onyx AI Assistant
**Location:** `abs-ai-hub/apps/onyx/`

Custom AI assistant with:
- Chat interface
- Settings page (model selection, temperature, system prompt)
- RAG capabilities
- Agent management
- Multi-model support

**Start:** `cd onyx && docker-compose up -d`

---

### 🌐 Open WebUI
**Location:** `abs-ai-hub/apps/open-webui/`

Advanced alternative chat interface with:
- Multi-model support
- Document attachments
- Conversation management
- User authentication
- Custom prompts and agents
- Web search integration

**Start:** `cd open-webui && docker-compose up -d`

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Applications                          │
│  AI Fabric (:5173) | Workstation Console (:5200)        │
│  Contract Reviewer (:8082) | Onyx | Open WebUI          │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Hub Gateway (:8081)                    │
│  - Unified API interface                                 │
│  - OpenAI-compatible endpoints                           │
│  - Asset registry management                             │
└────────┬──────────┬──────────┬──────────────────────────┘
         │          │          │
         ▼          ▼          ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Ollama  │ │ Qdrant  │ │ Redis   │
   │ :11434  │ │ :6333   │ │ :6379   │
   │ (LLM)   │ │(Vectors)│ │ (Cache) │
   └─────────┘ └─────────┘ └─────────┘
```

## Adding New Applications

1. **Create app directory:**
   ```bash
   mkdir abs-ai-hub/apps/my-app
   ```

2. **Create docker-compose.yml:**
   ```yaml
   name: abs-my-app
   
   networks:
     abs-net:
       external: true
   
   services:
     my-app:
       image: my-app:latest
       container_name: abs-my-app
       environment:
         OLLAMA_BASE_URL: http://abs-ollama:11434
         QDRANT_URL: http://abs-qdrant:6333
         REDIS_URL: redis://abs-redis:6379/0
         GATEWAY_URL: http://hub-gateway:8081
       ports:
         - "9000:9000"
       networks: [abs-net]
   ```

3. **Start the app:**
   ```bash
   cd abs-ai-hub/apps/my-app
   docker-compose up -d
   ```

## Environment Variables

Apps can access these core services via the `abs-net` network:

| Service | Internal URL | External Port |
|---------|--------------|---------------|
| LLM Runtime | `http://abs-ollama:11434` | 11434 |
| Vector DB | `http://abs-qdrant:6333` | 6333 |
| Cache | `redis://abs-redis:6379` | 6379 |
| Gateway | `http://hub-gateway:8081` | 8081 |

## Troubleshooting

### App not accessible
1. Check if app is running: `docker ps | grep abs-`
2. Check app logs: `cd apps/[app-name] && docker-compose logs`
3. Check network: `docker network inspect abs-net`

### Core services not found
- Ensure core services are running: `cd c:\ABS\core && .\start-core.ps1`
- Check network connection: `docker network inspect abs-net`

## Best Practices

1. **Always use abs-net:** All apps must join the `abs-net` external network
2. **Consistent naming:** Use `abs-` prefix for all containers
3. **Volume management:** Use named volumes for data persistence
4. **Graceful shutdown:** Use `restart: unless-stopped`
