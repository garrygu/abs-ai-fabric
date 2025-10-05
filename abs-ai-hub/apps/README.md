# ABS AI Hub - Applications

This directory contains all user-facing applications that consume the core services (Ollama, Qdrant, Redis, Hub Gateway).

## Unified Access Pattern

All applications are accessible through a single entry point at `http://localhost:3000` with path-based routing:

```
http://localhost:3000/              → Hub UI (landing page)
http://localhost:3000/onyx/         → Onyx AI Assistant
http://localhost:3000/openwebui/    → Open WebUI
http://localhost:3000/contract/     → Contract Reviewer
http://localhost:3000/rag/          → RAG PDF Voice
```

## Applications

### 🤖 Onyx AI Assistant (`/onyx/`)
**Location:** `abs-ai-hub/apps/onyx/`

Custom AI assistant with:
- Chat interface
- Settings page (model selection, temperature, system prompt)
- RAG capabilities
- Agent management
- Multi-model support

**Start:** `cd onyx && docker-compose up -d`

---

### 🌐 Open WebUI (`/openwebui/`)
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

### 📄 Contract Reviewer (`/contract/`)
**Location:** `abs-ai-hub/apps/contract-reviewer/`

Legal document analysis:
- Contract analysis
- Clause extraction
- Risk flagging
- Citation-backed reports
- PDF/DOCX support with OCR

**Start:** `cd contract-reviewer && docker-compose up -d`

---

### 🎤 RAG PDF Voice (`/rag/`)
**Location:** `abs-ai-hub/apps/rag-pdf-voice/`

Document analysis with voice:
- PDF processing
- Voice interaction
- Natural language queries
- Semantic search

**Start:** `cd rag-pdf-voice && docker-compose up -d`

---

## Architecture

### Application Structure
```
abs-ai-hub/apps/
├── onyx/
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
├── open-webui/
│   └── docker-compose.yml
├── contract-reviewer/
│   └── docker-compose.yml
└── rag-pdf-voice/
    └── docker-compose.yml
```

### Network Topology
```
┌─────────────────────────────────────┐
│   Hub UI (nginx reverse proxy)     │
│   http://localhost:3000             │
└─────────────────┬───────────────────┘
                  │
         ┌────────┴────────┐
         │   abs-net       │
         │  (Docker)       │
         └────────┬────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐    ┌───▼───┐    ┌───▼───┐
│ Onyx  │    │ Open  │    │Contract│
│ :8000 │    │WebUI  │    │:7860  │
└───┬───┘    │ :8080 │    └───┬───┘
    │        └───┬───┘        │
    └────────────┼────────────┘
                 │
    ┌────────────┴────────────┐
    │   Core Services         │
    │  - Ollama (LLM)         │
    │  - Qdrant (Vector DB)   │
    │  - Redis (Cache)        │
    │  - Hub Gateway (API)    │
    └─────────────────────────┘
```

## Adding New Applications

To add a new application:

1. **Create app directory:**
   ```bash
   mkdir abs-ai-hub/apps/my-app
   ```

2. **Create docker-compose.yml:**
   ```yaml
   name: abs-my-app
   version: "3.9"
   
   networks:
     abs-net:
       external: true
   
   services:
     my-app:
       image: my-app:latest
       container_name: abs-my-app
       environment:
         OLLAMA_BASE_URL: http://ollama:11434
         QDRANT_URL: http://qdrant:6333
         REDIS_URL: redis://redis:6379/0
       ports:
         - "9000:9000"
       networks: [abs-net]
   ```

3. **Add route to nginx.conf:**
   ```nginx
   # In abs-ai-hub/hub-ui/nginx.conf
   upstream my_app {
       server my-app:9000;
   }
   
   location /myapp/ {
       rewrite ^/myapp/(.*) /$1 break;
       proxy_pass http://my_app;
       # ... standard proxy headers
   }
   ```

4. **Add to Hub UI:**
   Edit `abs-ai-hub/hub-ui/assets/index.html` to add app card.

5. **Start the app:**
   ```bash
   cd abs-ai-hub/apps/my-app
   docker-compose up -d
   ```

## Management Commands

### Start All Apps
```bash
cd abs-ai-hub/apps
for dir in */; do (cd "$dir" && docker-compose up -d); done
```

### Stop All Apps
```bash
cd abs-ai-hub/apps
for dir in */; do (cd "$dir" && docker-compose down); done
```

### View Logs
```bash
cd abs-ai-hub/apps/onyx
docker-compose logs -f
```

### Restart an App
```bash
cd abs-ai-hub/apps/onyx
docker-compose restart
```

## Environment Variables

Apps can access these core services via the `abs-net` network:

- **LLM Runtime:** `http://ollama:11434` or `http://vllm:8000/v1`
- **Vector DB:** `http://qdrant:6333`
- **Cache:** `redis://redis:6379/0`
- **Gateway:** `http://hub-gateway:8081`

## Troubleshooting

### App not accessible
1. Check if app is running: `docker ps | grep abs-`
2. Check app logs: `cd apps/[app-name] && docker-compose logs`
3. Check if connected to abs-net: `docker network inspect abs-net`

### 502 Bad Gateway
- App is starting up (wait 10-30 seconds)
- App crashed (check logs)
- Port conflict (check docker-compose.yml)

### Core services not found
- Ensure core services are running: `cd core && docker-compose ps`
- Check network connection: `docker network inspect abs-net`

## Best Practices

1. **Always use abs-net:** All apps must join the `abs-net` external network
2. **Use wait-core:** Add health checks to wait for core services
3. **Consistent naming:** Use `abs-` prefix for all containers
4. **Volume management:** Use named volumes for data persistence
5. **Graceful shutdown:** Use `restart: unless-stopped`

## Security Notes

- Apps are isolated on `abs-net` Docker network
- No direct internet access unless explicitly configured
- Hub UI acts as reverse proxy (single entry point)
- Add authentication in production deployments

