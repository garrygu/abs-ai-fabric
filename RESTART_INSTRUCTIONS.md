# Restart & Recovery Guide

How to restart ABS AI Fabric services after code changes, configuration updates, or troubleshooting.

## Components Overview

| Component | How it runs | Default URL |
|-----------|-------------|-------------|
| **Core services** | Docker Compose (`core/docker-compose.yml`) | — |
| **Hub Gateway** | Docker container `abs-core-hub-gateway` | http://localhost:8081 |
| **GPU Metrics** | Host process (Node.js, started by `start-core.ps1`) | http://localhost:8083/gpu-metrics |
| **AI Fabric** (hub-ui-v2) | Vite dev server (`npm run dev`) | http://localhost:5173 |
| **Workstation Console** | Vite dev server (`npm run dev`) | http://localhost:5200 |
| **Containerized apps** | Per-app `docker compose up -d` | Varies (see app manifest) |

Core Docker containers: `abs-ollama`, `abs-qdrant`, `abs-redis`, `document-hub-postgres`, `abs-core-hub-gateway`.

---

## Quick Restart (Everything)

### Core + dev UIs (Windows)

From the repo root, `Start.bat` launches core services, AI Fabric, and Workstation Console in separate windows.

Or manually:

```powershell
# 1. Core services (includes gateway)
cd core
.\stop-core.ps1
.\start-core.ps1

# 2. AI Fabric — stop the running terminal (Ctrl+C), then:
cd ..\abs-ai-hub\hub-ui-v2
npm run dev

# 3. Workstation Console — stop the running terminal (Ctrl+C), then:
cd ..\apps\abs_workstation_console
npm run dev
```

---

## Restart by Component

### 1. Hub Gateway (REQUIRED after gateway code changes)

Rebuild when Python code under `core/gateway/` changes (`app.py`, routers, `store_service.py`, etc.). A plain container restart is not enough unless the image is rebuilt.

```powershell
cd core

# Option A: Rebuild and restart gateway only
docker compose build hub-gateway
docker compose up -d hub-gateway

# Option B: Full core restart with rebuild
docker compose down
docker compose up -d --build

# Option C: Use the provided scripts
.\stop-core.ps1
.\start-core.ps1
```

Verify:

```powershell
curl http://localhost:8081/health
curl http://localhost:8081/v1/store/apps
docker logs abs-core-hub-gateway --tail 50
```

### 2. All Core Services (Ollama, Qdrant, Redis, PostgreSQL, Gateway)

```powershell
cd core
.\stop-core.ps1
.\start-core.ps1
```

Or with Docker Compose directly:

```powershell
cd core
docker compose down
docker compose up -d
docker compose ps
```

`start-core.ps1` also starts the **GPU Metrics Server** on port 8083 as a background PowerShell job (requires Node.js on the host).

Stop GPU metrics separately if needed:

```powershell
Stop-Job -Name GPUMetricsServer
Remove-Job -Name GPUMetricsServer
```

### 3. AI Fabric (hub-ui-v2)

The admin UI is a Vite dev server, not a Docker container. Restart by stopping the terminal (Ctrl+C) and running:

```powershell
cd abs-ai-hub\hub-ui-v2
npm run dev
```

After changing `.env` or `VITE_CES_MODE`, restart the dev server for changes to take effect.

Production/preview build:

```powershell
npm run build
npm run preview
```

### 4. Workstation Console

Same as hub-ui-v2 — restart the dev server:

```powershell
cd abs-ai-hub\apps\abs_workstation_console
npm run dev
```

### 5. Containerized Applications

Restart a single app from its directory:

```powershell
cd abs-ai-hub\apps\contract-reviewer-v2
docker compose down
docker compose up -d --build
```

Other apps follow the same pattern: `legal-assistant`, `onyx-suite`, `whisper-server`, etc.

---

## When to Restart What

| Change | Restart |
|--------|---------|
| `core/gateway/**` Python code | Rebuild **hub-gateway** |
| `core/docker-compose.yml` or `core/.env` | Full **core** stack |
| `assets/**` registry YAML | Gateway reload or restart (`POST /admin/assets/reload` or restart gateway) |
| `abs-ai-hub/apps-registry.json` | Restart **hub-gateway** (file is volume-mounted; restart picks up changes) |
| `hub-ui-v2/src/**` | Restart **npm run dev** (HMR usually sufficient; full restart if env changed) |
| `abs_workstation_console/src/**` | Restart **npm run dev** |
| App `docker-compose.yml` or app code | Rebuild that **app container** |

---

## Verify Services

```powershell
# All ABS containers
docker ps --filter "name=abs-"
docker ps --filter "name=document-hub"

# Gateway health and store API
curl http://localhost:8081/health
curl http://localhost:8081/admin/health
curl http://localhost:8081/v1/store/apps

# GPU metrics (host process)
curl http://localhost:8083/gpu-metrics

# Ollama
curl http://localhost:11434/api/tags
```

---

## Troubleshooting

### Gateway won't start

1. Check logs: `docker logs abs-core-hub-gateway`
2. Look for import errors (e.g. missing `store_service.py`)
3. Rebuild: `cd core && docker compose build hub-gateway && docker compose up -d hub-gateway`
4. Confirm `.env` exists: `copy .env.example .env` in `core/`

### Store API returns 503

- `StoreService` failed to initialize — check gateway logs for startup errors
- Verify `abs-ai-hub/store-sources.json` and `abs-ai-hub/store/` are present (mounted into the gateway container)

### AI Fabric shows stale data or API errors

- Confirm gateway is healthy at http://localhost:8081/health
- Vite proxies `/v1` to the gateway — restart `npm run dev` if the proxy target changed
- Hard-refresh the browser (Ctrl+Shift+R)

### GPU metrics unavailable

- Ensure Node.js is installed; `start-core.ps1` skips metrics if `node` is not on PATH
- Check job status: `Get-Job -Name GPUMetricsServer`
- Restart core: `.\stop-core.ps1` then `.\start-core.ps1`

### App container can't reach core services

- Confirm the app joins the `abs-net` network in its `docker-compose.yml`
- Use Docker DNS names (`hub-gateway`, `ollama`, `qdrant`, `redis`) inside containers, not `localhost`

---

## Related Docs

- [README — Quick Start](README.md)
- [Core Services README](core/README.md)
- [CES Setup Guide](docs/ces/CES_SETUP_GUIDE.md)
