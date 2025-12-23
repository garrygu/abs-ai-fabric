# ABS AI Hub – Core Services Guide

This document explains the **Core Services strategy** for ABS AI Hub, how to deploy and use them, and how to extend the Core with optional services in the future.

---

## 1. Strategy Overview

- **Core Services = shared infrastructure** used by all ABS AI Hub apps.
- **Apps = business logic** (Contract Reviewer, Deposition Summarizer, etc.) that connect to Core services.
- **Separation of concerns:**
  - Core runs independently in its own folder: `C:\ABS\core`
  - Apps live in the ABS-AI-HUB repo: `C:\ABS\ABS-AI-HUB\apps`
- **Always-on Core Services** (minimal set):
  - LLM Runtime (Ollama or vLLM)
  - Qdrant (vector database)
  - Redis (cache + queue)
  - PostgreSQL (document hub database)
  - Hub Gateway (unified API + admin management)
- **Optional Services** (started only if needed by an app):
  - Parser + OCR (Unstructured API)
  - MinIO (object storage)
  - Whisper (speech-to-text)
  - TTS, Translation, Redaction, etc.
- **Auto-Wake Management**: Services automatically start when needed and sleep when idle
- **Admin APIs**: Comprehensive management endpoints for services, models, and data inspection
- **Tri-Store Data Inspector**: Cross-store consistency analysis across PostgreSQL, Redis, and Qdrant

---

## 2. Deployment Layout

```
C:\
 ├─ ABS\
 │   ├─ core\                 # Minimal Core lives here
 │   │   ├─ .env
 │   │   ├─ core.yml
 │   │   ├─ start-core.ps1
 │   │   ├─ stop-core.ps1
 │   │   └─ update-core.ps1
 │   │
 │   └─ ABS-AI-HUB\           # All apps live here
 │       ├─ apps\
 │       │   ├─ contract-reviewer\
 │       │   ├─ rag-pdf-voice\
 │       │   └─ whisper-server\
 │       ├─ hub-ui\
 │       ├─ installers\
 │       └─ docker-compose.yml
```

---

## 3. Requirements

- **Windows 10 Pro**
- **Docker Desktop** with WSL2 integration
- **NVIDIA GPU driver** with CUDA support (for Ollama/vLLM/Whisper)
- **PowerShell (Admin)** to run scripts

> **📘 Setup Instructions**: For detailed Windows setup, including Docker Desktop WSL2 configuration and GPU passthrough, see the **[Windows Setup Guide](Windows_Setup_Guide.md)**.

---

## 4. Deploying the Core

1. Go to the core folder:
   ```powershell
   cd C:\ABS\core
   ```

2. Start Core services:
   ```powershell
   .\start-core.ps1
   ```

3. Verify services:
    ```powershell
    curl http://localhost:8081/health            # Gateway Health
    curl http://localhost:8081/v1/models         # Gateway Models (Unified)
    # Direct container checks (optional):
    curl http://localhost:11434/api/tags         # Ollama
    redis-cli -h 127.0.0.1 ping                  # Redis -> PONG
    ```

4. (Optional) Pull models into Ollama:
   ```powershell
   curl http://localhost:11434/api/pull -d '{"name":"llama3:8b-instruct-q4_K_M"}'
   ```

---

## 5. Running Apps on Top of Core

Each app has its own `compose.yml` and joins the **shared network** `abs-net`.

Example (Contract Reviewer):
```yaml
networks:
  abs-net:
    external: true

services:
  reviewer:
    build: .
    environment:
      QDRANT_URL: http://qdrant:6333
      # Point to Gateway for Unified API (OpenAI-compatible)
      # The Gateway handles adaptation to Ollama or vLLM automatically
      LLM_API_BASE: http://hub-gateway:8081/v1
      REDIS_URL: redis://redis:6379/0
    networks: [abs-net]
```

To run:
```powershell
cd C:\ABS\ABS-AI-HUB\apps\contract-reviewer
docker compose up -d
```

The app will discover and use the running Core services automatically.

---

## 6. Managing the Core

- **Start Core:**
  ```powershell
  C:\ABS\core\start-core.ps1
  ```
- **Stop Core:**
  ```powershell
  C:\ABS\core\stop-core.ps1
  ```
- **Update Core:**
  ```powershell
  C:\ABS\core\update-core.ps1
  ```
- **View status:**
  ```powershell
  docker compose -f C:\ABS\core\core.yml ps
  ```

---

## 7. Extending Core with Optional Services

When new apps require additional infrastructure, extend the Core gradually:

### Example: Add Parser + MinIO

1. Define optional services in a new file `optional-services.yml`:
```yaml
services:
  parser:
    image: downloads.unstructured.io/unstructured-io/unstructured-api:latest
    networks: [abs-net]

  minio:
    image: minio/minio:RELEASE.2024-07-26T00-00-00Z
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: absadmin
      MINIO_ROOT_PASSWORD: change-me
    ports: ["9000:9000","9001:9001"]
    networks: [abs-net]
```

2. Start them only when needed:
```powershell
cd C:\ABS\core
docker compose -f core.yml -f optional-services.yml up -d parser minio
```

3. Apps can now call:
- `PARSER_URL=http://parser:8000`
- `S3_ENDPOINT=http://minio:9000`

---

## 8. Best Practices

- **Pin versions** of Docker images (no `:latest` in production).
- **Keep Core always-on** for Ollama/vLLM, Qdrant, Redis.
- **Optional services** are started only by apps that need them.
- **Shared network** (`abs-net`) ensures DNS-based discovery by service name.
- **Logs & health checks** help confirm readiness (`docker compose ps`).
- **Back up volumes:**
  - `ollama_models` (models)
  - `qdrant_storage` (vector DB)
  - `redis_data` (cache/queue)
- **Security:**
  - BitLocker enabled
  - Strong passwords for MinIO and any externalized services

---

## 9. Roadmap

Future shared services that can be integrated:
- Whisper server (speech-to-text)
- TTS (text-to-speech)
- Translation service
- Redaction/PII detection
- Audit/Observability stack (Prometheus, Grafana, Loki)

---

✅ With this approach, the ABS AI Hub has a **minimal, always-on Core** that apps can build upon, while keeping the flexibility to add optional services when needed.

