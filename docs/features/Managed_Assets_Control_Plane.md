## ABS Hub Control Plane and Managed Assets

### Purpose
Define how the Hub acts as the control plane for apps, services, models, tools, datasets, and secrets. Establish a managed-assets model, registries, policy enforcement, health, and lifecycle so apps obtain everything from the Hub.

### Core Principles
- **Hub as Control Plane**: The Hub is the single source of truth and orchestrator for services, models, tools, apps, users, policies, and telemetry. Apps run in containers but register with the Hub and obtain everything (models, services, secrets, policies) from it.
- **Everything is a Managed Asset**: All assets share a common schema and lifecycle: metadata, version, lifecycle state, owner, policy, health, and logs.

### Asset Classes
- **Apps**: User-facing applications with a route, category, scopes, and required services/models.
- **Services**: Infrastructure capabilities like ASR, OCR, vector DB, gateways.
- **Models**: Chat/embedding/rerank models, abstracting providers (Ollama, vLLM/OpenAI, TGI, HF).
- **Tools**: Functional micro-capabilities (parsers, OCR, chunkers, rerankers) invoked via HTTP/GRPC or local libs.
- **Datasets**: Collections of documents or indices used by apps/services (e.g., RAG stores).
- **Secrets**: Indirections to credentials housed outside Git (vault/env/host store).

### Common Asset Schema (conceptual)
Each asset has:
- **id**: Stable identifier
- **class**: app | service | model | tool | dataset | secret
- **name/version**: Human-readable name and semantic version
- **owner**: Team or system owner
- **lifecycle**: desired vs actual state, timestamps
- **policy**: scopes, allowed models/tools, access rules
- **health**: status, endpoint/url, last_check, latency
- **logs**: sink (stdout/Loki), link/reference
- **metadata**: free-form details (category, container name, tags)

### Catalog and Registries
We maintain a human-readable Catalog plus specialized registries. Files first, APIs over them, DB optional later.

- **Catalog** (unified view): `/catalog`, `/assets`, `/assets/{id}`
  - Aggregates Apps, Services, Models, Tools, Datasets, Secrets
  - Serves per-app defaults and policy constraints

- **Model Registry**
  - Abstracts providers via aliases (e.g., `bge-small-en-v1.5` → { openai, ollama, hf })
  - Tracks dims, availability, and per-app allowances

- **Service Registry**
  - Defines services, container names, health URLs, and lifecycle
  - Used by auto-wake/idle-sleep and health dashboards

- **App Registry**
  - Installs, manifests, routes, scopes, health URLs
  - Links to required services and default models

### Control Plane Capabilities
- **Discovery**: `GET /.well-known/abs-services` and `GET /catalog` expose active endpoints and approved models per app.
- **Provider Routing**: Gateway normalizes chat/embeddings across Ollama and OpenAI-compatible backends.
- **Policy Enforcement**: Per-app allowed models/embeddings and scopes; reject disallowed overrides (403).
- **Lifecycle Management**: Track desired vs actual for services and apps; reconcile via Docker when permitted.
- **Health Monitoring**: Periodic probes; summarize at `GET /health` and `GET /health/{asset_id}`.
- **Telemetry**: Structured request logs (app_id, provider, model, latency); later forward to Loki/Prometheus.

### Initial API Surface (Gateway)
- `GET /.well-known/abs-services`: quick discovery of core endpoints
- `GET /catalog`: unified catalog (apps, models, aliases, policies)
- `POST /v1/chat/completions`: OpenAI-compatible chat; enforces per-app policy
- `POST /v1/embeddings`: embeddings with caching; per-app default and override gating
- (Planned) `GET /assets`, `GET /assets/{id}`: browsable asset inventory
- (Planned) `GET /services`: service registry view
- (Planned) `POST /lifecycle/{asset_id}`: set desired state (on/off/running/paused)
- (Planned) `GET /health`, `GET /health/{asset_id}`: aggregated health
- (Planned) `/metrics`: Prometheus metrics

### Data Ownership and Storage
- Store registries as JSON/YAML in Git for auditability.
- Store secrets as references (vault path, env var key), never values.
- Optionally cache runtime state (health, usage) in Redis; persist long-term telemetry to a log sink.

### Security and Policy
- Identity: apps identify via `X-ABS-App-Id`; introduce signed tokens for stronger auth.
- Authorization: Registry-driven allowlists for models, embeddings, and tools per app.
- Rate Limiting: Token bucket per app in Redis (requests/minute, tokens per time unit).
- Network: Keep the gateway bound inside Docker network; restrict external exposure.

### Phased Rollout
1) **Phase 1: Catalog & Read-only**
   - Create unified `catalog.json` from current `apps-registry.json` and `registry.json`.
   - Expose `GET /assets`, `GET /assets/{id}`; keep `/catalog` stable.
   - Validate embedding dimensions based on chosen provider alias.

2) **Phase 2: Policy Enforcement**
   - Add `allowed_models` and `allowed_embeddings` per app.
   - Enforce in chat/embeddings endpoints using `X-ABS-App-Id`.

3) **Phase 3: Lifecycle & Health**
   - Expand Service Registry with health URLs and container names; track desired vs actual.
   - Add background reconcilers and `/services`, `/health`, `/lifecycle/{id}` endpoints.

4) **Phase 4: Secrets & Datasets**
   - Introduce secrets as references; mount/inject at runtime.
   - Add datasets and tools to the Catalog with minimal metadata and health.

5) **Phase 5: Observability**
   - Add `/metrics`, correlation IDs, rate limits; forward logs to Loki/Prometheus.

### Alignment with Current Codebase
- `core/gateway/app.py` already implements provider routing, per-app config, Redis caching, and structured logs.
- `core/gateway/registry.json` already models defaults, app-specific models, and provider aliases.
- `abs-ai-hub/apps-registry.json` provides app inventory and health endpoints.
- This plan formalizes a Catalog around existing files and adds a few endpoints plus background checks.

### Immediate Next Steps
- Draft `catalog.json` by merging current app and model registries.
- Add per-app `allowed_models` and `allowed_embeddings` gates.
- Extend gateway endpoints to serve unified Catalog and enforce policy.

### Appendix: Minimal Schema Examples

```json
{
  "version": "1.0",
  "assets": [
    {
      "id": "contract-reviewer",
      "class": "app",
      "name": "Contract Reviewer",
      "owner": "legal-platform",
      "version": "2.1.0",
      "lifecycle": { "desired": "running", "actual": "running" },
      "policy": { "scopes": ["contracts.read"], "allowed_models": ["llama3.2:latest"], "allowed_embeddings": ["legal-bert", "bge-small-en-v1.5"] },
      "health": { "status": "healthy", "url": "http://localhost:7860" },
      "metadata": { "category": "Legal Apps" }
    },
    {
      "id": "whisper-server",
      "class": "service",
      "type": "asr",
      "name": "Whisper Server",
      "owner": "platform",
      "version": "1.0.0",
      "lifecycle": { "desired": "on", "actual": "on" },
      "policy": { "scopes": ["audio.transcribe"] },
      "health": { "status": "healthy", "url": "http://localhost:8001/healthz" },
      "metadata": { "container": "abs-whisper" }
    },
    {
      "id": "bge-small-en-v1.5",
      "class": "model",
      "provider_alias": { "openai": "bge-small-en-v1.5", "ollama": "bge-small", "huggingface": "BAAI/bge-small-en-v1.5" },
      "version": "1.5",
      "owner": "ml-platform",
      "policy": { "apps_allowed": ["contract-reviewer", "deposition-summarizer"] },
      "health": { "status": "ready" },
      "metadata": { "dim": 384 }
    }
  ]
}
```


