# Onyx Quick Reference Card

## 🚀 Getting Started

### Start Onyx
```bash
cd C:\ABS\core
.\start-core.ps1
```

### Access Points
- **Chat UI**: http://localhost:8000
- **Hub Gateway**: http://localhost:8081/v1/onyx/*
- **ABS Hub**: http://localhost:3000 → "Onyx AI Assistant"

---

## 💬 Basic Chat Usage

### Direct Chat (Web UI)
1. Open http://localhost:8000
2. Type your message
3. Press Enter or click Send
4. Upload files for analysis

### API Chat
```bash
curl -H "X-ABS-App-Id: my-app" \
     -H "Content-Type: application/json" \
     -d '{"messages":[{"role":"user","content":"Hello!"}],"model":"llama3.1:8b"}' \
     http://localhost:8081/v1/onyx/chat
```

---

## 🔍 RAG Queries

### Search Documents
```bash
curl -H "X-ABS-App-Id: my-app" \
     -H "Content-Type: application/json" \
     -d '{"query":"liability clauses","collection":"contracts","top_k":5}' \
     http://localhost:8081/v1/onyx/rag
```

### Upload Documents
```bash
curl -H "X-ABS-App-Id: my-app" \
     -H "Content-Type: application/json" \
     -d '{"documents":[{"text":"Contract content...","metadata":{"source":"contract.pdf"}}],"collection":"contracts"}' \
     http://localhost:8081/v1/onyx/ingest
```

---

## 🤖 Agent Management

### List Agents
```bash
curl -H "X-ABS-App-Id: my-app" \
     http://localhost:8081/v1/onyx/agents
```

### Execute Agent
```bash
curl -H "X-ABS-App-Id: my-app" \
     -H "Content-Type: application/json" \
     -d '{"input":"Review this contract","context":{"document_id":"123"}}' \
     http://localhost:8081/v1/onyx/agents/contract-reviewer/execute
```

---

## 🐍 Python Examples

### Basic Chat
```python
import httpx

async def chat(message):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8081/v1/onyx/chat",
            headers={"X-ABS-App-Id": "my-app"},
            json={"messages": [{"role": "user", "content": message}]}
        )
        return response.json()
```

### RAG Query
```python
async def search_docs(query, collection="contracts"):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8081/v1/onyx/rag",
            headers={"X-ABS-App-Id": "my-app"},
            json={"query": query, "collection": collection, "top_k": 5}
        )
        return response.json()
```

---

## 🔧 Troubleshooting

### Check Status
```bash
# Container status
docker ps | grep onyx

# Health check
curl http://localhost:8000/health

# Service status
curl http://localhost:8081/admin/services/status
```

### View Logs
```bash
# Onyx logs
docker logs -f abs-onyx

# Gateway logs
docker logs -f abs-hub-gateway
```

### Common Issues
- **Service not starting**: Check dependencies (Redis, Qdrant, Ollama)
- **Connection errors**: Verify network connectivity
- **Empty RAG results**: Check document ingestion and collection names
- **Slow responses**: Monitor resource usage, consider caching

---

## 📊 Monitoring

### Resource Usage
```bash
docker stats abs-onyx
```

### Service Dependencies
```bash
# Check all services
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### API Health
```bash
# Gateway health
curl http://localhost:8081/.well-known/abs-services

# Onyx health
curl http://localhost:8000/health
```

---

## 🎯 Best Practices

### Performance
- Use appropriate model sizes (3B-7B for chat, 8B+ for analysis)
- Implement response caching
- Batch document ingestion
- Monitor resource usage

### Security
- Always include `X-ABS-App-Id` header
- Validate input parameters
- Use environment variables for configuration
- Implement proper error handling

### Integration
- Use async/await for API calls
- Implement retry logic for robustness
- Monitor API call metrics
- Handle service unavailability gracefully

---

## 📚 Resources

- **Full Guide**: `core/docs/Onyx_Integration_Guide.md`
- **Onyx Docs**: https://docs.onyx.app
- **ABS Hub Docs**: `core/docs/`
- **API Reference**: Hub Gateway endpoints

---

*Keep this card handy for quick Onyx operations!*
