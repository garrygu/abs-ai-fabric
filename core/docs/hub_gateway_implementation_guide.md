# ABS AI Hub — Hub Gateway (Implementation & Guide)

This guide ships a **comprehensive Hub Gateway** to unify access to LLM chat & embeddings across providers (Ollama or vLLM/OpenAI-compatible), plus **model registry**, **caching**, **audit logs**, **service discovery**, **auto-wake management**, **admin APIs**, and **Tri-Store Data Inspector**. Apps call the Gateway and **don't need to know** which backend is active.

---

## 1) What the Gateway Does

- **Stable API** for apps:
  - `POST /v1/chat/completions` (OpenAI-compatible response)
  - `POST /v1/embeddings`
  - `GET  /.well-known/abs-services` (service discovery)
  - `GET  /catalog` (approved models per app)
- **Provider routing**: targets **Ollama** (`/api/chat`, `/api/embeddings`) or **vLLM/OpenAI** (`/v1/*`).
- **Per-app policy**: resolves the **embedding model** (and optionally chat model) by `X-ABS-App-Id` using a **registry** JSON.
- **Caching**: Redis cache for embeddings (by `(app_id, model, text_hash)`).
- **Audit**: logs per request with `app_id`, `provider`, `model`, latency, counts.
- **Auto-wake**: Automatically starts services when needed and manages idle sleep.
- **Admin APIs**: Comprehensive management endpoints for services, models, and data inspection.
- **Tri-Store Inspector**: Cross-store data consistency analysis for PostgreSQL, Redis, and Qdrant.

---

## 2) Files & Layout

Place these under `C:\ABS\core\gateway`.

```
C:\ABS\core\gateway\
 ├─ Dockerfile
 ├─ requirements.txt
 ├─ app.py                    # Main FastAPI application
 ├─ registry.json             # model & policy registry
 ├─ catalog.json              # asset catalog and policies
 └─ postgres-init/            # PostgreSQL initialization scripts
    └─ 01-init-document-hub.sql
```

### 2.1 `Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app

# Install Docker CLI for container management
RUN apt-get update && apt-get install -y \
    docker.io \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py registry.json catalog.json ./
ENV PYTHONUNBUFFERED=1
EXPOSE 8081
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8081"]
```

### 2.2 `requirements.txt`
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
httpx==0.27.2
pydantic==2.9.2
redis==5.0.7
python-dotenv==1.0.1
sentence-transformers==2.2.2
psutil==5.9.0
docker==6.1.3
psycopg2-binary==2.9.7
```

### 2.3 `registry.json` (starter)
```json
{
  "defaults": {
    "chat_model": "contract-default",
    "embed_model": "bge-small-en-v1.5",
    "provider": "auto",            
    "dim": 384
  },
  "apps": {
    "contract-reviewer": { "embed_model": "bge-small-en-v1.5", "provider": "auto", "dim": 384 },
    "deposition-summarizer": { "embed_model": "all-minilm", "provider": "ollama", "dim": 384 }
  },
  "aliases": {
    "llama3-8b-instruct": { "openai": "llama3-8b-instruct", "ollama": "llama3:8b-instruct-q4_K_M" },
    "bge-small-en-v1.5": { "openai": "bge-small-en-v1.5", "ollama": "bge-small" },
    "all-minilm": { "openai": "all-minilm", "ollama": "all-minilm" }
  }
}
```

> **Notes**
> - `provider: "auto"` lets the Gateway probe vLLM first, then Ollama.
> - You can set per-app `chat_model` too. Embeddings are the most common per-app diff.

### 2.4 `app.py` (FastAPI Gateway)
```python
import os, json, hashlib, time
from typing import Optional, List

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
import redis as redislib

# ---- Config ----
PORT = int(os.getenv("GATEWAY_PORT", "8081"))
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "http://vllm:8000/v1")
OPENAI_KEY  = os.getenv("OPENAI_API_KEY", "abs-local")
REGISTRY_PATH = os.getenv("REGISTRY_PATH", "registry.json")

# Redis cache (optional but recommended)
rds = None
try:
    rds = redislib.from_url(REDIS_URL)
    rds.ping()
except Exception:
    rds = None

with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
    REG = json.load(f)

app = FastAPI(title="ABS Hub Gateway")
HTTP = httpx.AsyncClient(timeout=60)

# ---- Schemas ----
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatReq(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = None

class EmbedReq(BaseModel):
    input: List[str]
    override_model: Optional[str] = None

# ---- Helpers ----
async def detect_provider() -> str:
    # Prefer OpenAI/vLLM if reachable
    try:
        r = await HTTP.get(f"{OPENAI_BASE.rstrip('/')}/models")
        if r.is_success:
            return "openai"
    except Exception:
        pass
    try:
        r = await HTTP.get(f"{OLLAMA_BASE.rstrip('/')}/api/tags")
        if r.is_success:
            return "ollama"
    except Exception:
        pass
    raise HTTPException(503, "No LLM provider reachable")

def logical_to_provider_id(logical: str, provider: str) -> str:
    return REG.get("aliases", {}).get(logical, {}).get(provider, logical)

def pick_app_cfg(app_id: Optional[str]):
    dfl = REG.get("defaults", {})
    app_cfg = REG.get("apps", {}).get(app_id or "", {})
    return {**dfl, **app_cfg}

# ---- Discovery & Catalog ----
@app.get("/.well-known/abs-services")
async def services():
    return {
        "llm_openai": OPENAI_BASE,
        "llm_ollama": OLLAMA_BASE,
        "redis": REDIS_URL,
        "catalog": "/catalog"
    }

@app.get("/catalog")
async def catalog():
    return REG

# ---- Chat ----
@app.post("/v1/chat/completions")
async def chat(req: ChatReq, request: Request, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    t0 = time.time()
    cfg = pick_app_cfg(app_id)
    provider = cfg.get("provider", "auto")
    if provider == "auto":
        provider = await detect_provider()

    model_logical = req.model or cfg.get("chat_model", "contract-default")
    model = logical_to_provider_id(model_logical, provider)

    if provider == "openai":
        payload = {
            "model": model,
            "messages": [m.model_dump() for m in req.messages],
            "temperature": req.temperature,
            "max_tokens": req.max_tokens,
        }
        r = await HTTP.post(f"{OPENAI_BASE.rstrip('/')}/chat/completions",
                            headers={"Authorization": f"Bearer {OPENAI_KEY}"},
                            json=payload)
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        out = r.json()
    else:
        # Ollama chat → normalize to OpenAI-like response
        payload = {
            "model": model,
            "messages": [m.model_dump() for m in req.messages],
            "stream": False,
            "options": {"temperature": req.temperature}
        }
        r = await HTTP.post(f"{OLLAMA_BASE.rstrip('/')}/api/chat", json=payload)
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        data = r.json()
        text = data.get("message", {}).get("content", data.get("response", ""))
        out = {
            "id": "chatcmpl_abs",
            "object": "chat.completion",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}}],
            "usage": {
                "prompt_tokens": data.get("prompt_eval_count"),
                "completion_tokens": data.get("eval_count"),
                "total_tokens": None
            },
            "model": model,
            "provider": "ollama"
        }
    dt = time.time() - t0
    print(json.dumps({"event":"chat","app_id":app_id,"provider":provider,"model":model,"ms":int(dt*1000)}))
    return out

# ---- Embeddings ----
@app.post("/v1/embeddings")
async def embeddings(req: EmbedReq, request: Request, app_id: Optional[str] = Header(None, alias="X-ABS-App-Id")):
    t0 = time.time()
    cfg = pick_app_cfg(app_id)
    provider = cfg.get("provider", "auto")
    if provider == "auto":
        provider = await detect_provider()

    logical = req.override_model or cfg.get("embed_model") or REG.get("defaults", {}).get("embed_model")
    model = logical_to_provider_id(logical, provider)

    # Cache key
    hasher = hashlib.sha256()
    for t in req.input:
        hasher.update(t.encode("utf-8"))
    key = f"emb:{app_id or 'unknown'}:{provider}:{model}:{hasher.hexdigest()}"

    if rds is not None:
        cached = rds.get(key)
        if cached:
            return json.loads(cached)

    if provider == "openai":
        r = await HTTP.post(f"{OPENAI_BASE.rstrip('/')}/embeddings",
                            headers={"Authorization": f"Bearer {OPENAI_KEY}"},
                            json={"model": model, "input": req.input})
        if not r.is_success:
            raise HTTPException(r.status_code, r.text)
        out = r.json()
    else:
        # Ollama: call per text
        data = []
        for i, t in enumerate(req.input):
            r = await HTTP.post(f"{OLLAMA_BASE.rstrip('/')}/api/embeddings", json={"model": model, "prompt": t})
            if not r.is_success:
                raise HTTPException(r.status_code, r.text)
            emb = r.json()["embedding"]
            data.append({"index": i, "embedding": emb})
        out = {"data": data, "model": model, "object": "list"}

    if rds is not None:
        rds.setex(key, 86400, json.dumps(out))  # 1 day

    dt = time.time() - t0
    print(json.dumps({"event":"embed","app_id":app_id,"provider":provider,"model":model,"n":len(req.input),"ms":int(dt*1000)}))
    return out
```

---

## 3) Add Gateway to Core Compose

In `C:\ABS\core\core.yml`, add the service:

```yaml
services:
  hub-gateway:
    build: ./gateway
    container_name: abs-hub-gateway
    environment:
      REDIS_URL: redis://redis:6379/0
      OLLAMA_BASE_URL: http://ollama:11434
      OPENAI_BASE_URL: http://vllm:8000/v1
      OPENAI_API_KEY: abs-local
      REGISTRY_PATH: /app/registry.json
    ports: ["8081:8081"]
    depends_on: [redis]
    networks: [abs-net]
```

> If you’re using **Compose profiles** to switch between Ollama and vLLM, this gateway will probe which is live (`/models` vs `/api/tags`).

**Build & run**
```powershell
cd C:\ABS\core
docker compose build hub-gateway
docker compose up -d hub-gateway
```

**Smoke tests**
```powershell
curl http://localhost:8081/.well-known/abs-services
curl http://localhost:8081/catalog
```

---

## 4) App Integration (simple)

**Always call the Gateway** and identify the app:

```python
import requests
HUB = "http://hub-gateway:8081"   # inside Docker network; outside: http://localhost:8081

# Chat
r = requests.post(
    f"{HUB}/v1/chat/completions",
    headers={"X-ABS-App-Id": "contract-reviewer"},
    json={
      "model": "contract-default",   # optional; registry can supply default
      "messages": [
        {"role":"user","content":"List 3 risks in this NDA."}
      ]
    }, timeout=30)
print(r.json()["choices"][0]["message"]["content"])

# Embeddings (uses app’s default embedding model from registry)
resp = requests.post(
    f"{HUB}/v1/embeddings",
    headers={"X-ABS-App-Id": "contract-reviewer"},
    json={"input": ["Confidentiality survives 5 years."]}, timeout=60).json()
vector = resp["data"][0]["embedding"]
```

**Optional per-request override**
```python
requests.post(
  f"{HUB}/v1/embeddings",
  headers={"X-ABS-App-Id":"contract-reviewer"},
  json={"input":["text"], "override_model":"bge-small-en-v1.5"}
)
```

---

## 5) Admin APIs & Management

The Hub Gateway provides comprehensive admin APIs for managing services, models, and data inspection.

### 5.1 Service Management
- `GET /admin/services/discovery` - Discover all available services
- `GET /admin/services/status` - Get status of all services
- `POST /admin/services/{service_name}/control` - Start/stop/restart services
- `POST /admin/services/ensure-ready` - Ensure multiple services are running
- `GET /admin/services/dependencies` - Get service dependency information

### 5.2 Model Management
- `GET /admin/models` - List all available models with status
- `POST /admin/models/{model_name}/pull` - Pull model from Ollama registry
- `POST /admin/models/{model_name}/load` - Load model into VRAM
- `POST /admin/models/{model_name}/unload` - Force unload model
- `DELETE /admin/models/{model_name}` - Delete model from storage

### 5.3 Auto-Wake & Idle Sleep
- `GET /admin/settings` - Get auto-wake settings
- `POST /admin/settings` - Update auto-wake settings
- `POST /admin/services/{service_name}/idle-sleep` - Toggle idle sleep for service
- `GET /admin/idle-status` - Get current idle status of services and models

### 5.4 System Monitoring
- `GET /admin/system/metrics` - Get real-time system metrics (CPU, memory, GPU)
- `GET /admin/logs/{service_name}` - Get logs for a specific service
- `GET /api/health/postgresql` - PostgreSQL health check
- `GET /api/metrics/postgresql` - PostgreSQL performance metrics

---

## 6) Tri-Store Data Inspector

The Tri-Store Data Inspector provides cross-store data consistency analysis across PostgreSQL, Redis, and Qdrant.

### 6.1 Document Inspection
- `GET /admin/inspector/{doc_id}` - Inspect document across all stores
- `GET /admin/inspector/diff/{doc_id}` - Get only consistency analysis
- `POST /admin/inspector/batch` - Inspect multiple documents
- `GET /admin/inspector/health` - Health check for all data stores

### 6.2 Vector Analysis
- `GET /admin/inspector/vectors/{doc_id}` - Analyze vector neighborhood
- Export capabilities for inspection results (JSON/CSV)

### 6.3 Data Export
- `GET /admin/inspector/export/{doc_id}` - Export single document inspection
- `POST /admin/inspector/export/batch` - Export batch inspection results

---

## 7) Security & Policy

- **Identity**: apps must send `X-ABS-App-Id`. Add tokens later (e.g., `Authorization: Bearer <token>`).
- **Allowed models**: Restrict models per app in `registry.json`. Reject unapproved overrides.
- **Rate limits**: Add a simple token bucket in Redis keyed by `app_id` if needed.
- **Audit**: Gateway prints structured logs to stdout; route to Loki or file.
- **Network**: Keep Gateway bound to `localhost` externally; expose inside Docker network (`abs-net`).

---

## 8) Operations

- **Update registry**: edit `registry.json` and `docker compose up -d hub-gateway` (no rebuild needed).
- **Switch Ollama/vLLM**: change Core profile; Gateway auto-detects on next request.
- **Cache control**: flush Redis cache for embeddings if you change models.
- **Backups**: registry file (Git), Redis persistence if used (AOF), standard Core volume backups.
- **Auto-wake**: Services automatically start when needed and sleep when idle (configurable).

---

## 9) Troubleshooting

- `503 No LLM provider reachable` → ensure either vLLM (`/v1/models`) or Ollama (`/api/tags`) is healthy.
- Wrong embeddings dim → check `registry.json` dims, and confirm selected provider model.
- Timeouts → raise Gateway timeout (HTTPX `timeout`), reduce batch size, or increase provider capacity.
- Service not starting → check Docker client availability and container mappings.
- Data inconsistency → use Tri-Store Inspector to identify cross-store issues.

---

## 10) Roadmap (optional enhancements)

- **Tokens & RBAC**: per-app JWTs and role-based routes.
- **Rate limiting**: Redis token bucket per app.
- **Rerank API**: `/v1/rerank` (add bge-reranker or Cohere rerank local).
- **Streaming chat**: support `stream=true` for OpenAI-compatible SSE.
- **Observability**: `/metrics` (Prometheus), request tracing headers.
- **Policy dates**: registry with `effective_date` to schedule migrations.
- **Advanced analytics**: usage patterns, model performance metrics.

---

## 11) Quick Start (cheatsheet)

```powershell
# From C:\ABS\core
# 1) Build & run gateway
cd C:\ABS\core\gateway
docker build -t abs/hub-gateway:local .
cd ..
docker compose up -d hub-gateway

# 2) Test
curl http://localhost:8081/.well-known/abs-services
curl -X POST http://localhost:8081/v1/embeddings -H "X-ABS-App-Id: contract-reviewer" -H "Content-Type: application/json" -d "{\"input\":[\"hello\"]}"
```

With this Gateway in place, apps can **auto-adapt** to Ollama or vLLM, choose **app-specific embeddings** centrally, and benefit from shared caching and audit without duplicating logic in each app.

