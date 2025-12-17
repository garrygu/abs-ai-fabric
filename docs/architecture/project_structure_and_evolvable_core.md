# ABS AI Fabric  
## Project Structure & Evolvable Core Architecture

**Version:** v1.0  
**Status:** Engineering Design – Approved  
**Audience:** Platform, Infra, Gateway, Hub-UI, Application Engineers

---

## 1. Purpose

This document defines the **project structure** and **evolvable core architecture** for **ABS AI Fabric**, an on-prem AI platform designed to support:

- Multiple AI applications
- Shared AI infrastructure
- Optional high-cost AI capabilities (e.g., 70B models, speech, OCR)
- Safe, incremental evolution of core components over time

The goal is to provide **OS-like stability** while preserving **platform-level flexibility**.

---

## 2. Core Architectural Principles

### 2.1 Everything Is an Asset

All shared AI capabilities are modeled as **Assets**, including:

- Services (LLM runtimes, vector databases, caches)
- Models (7B–70B LLMs, Whisper, OCR)
- Tools (parsers, TTS, translation)
- Data stores

Assets are:
- Centrally registered
- Lifecycle-managed
- Discoverable via UI
- Activated and suspended on demand

---

### 2.2 Core Is Evolvable, Not Fixed

The Core is **not** a static set of services.

> **Core = Stable Interfaces + Swappable Implementations**

This enables:
- Replacing Ollama with vLLM
- Replacing Qdrant with Milvus
- Running old and new runtimes in parallel
- Gradual, low-risk migration

---

### 2.3 Applications Bind to Interfaces, Not Implementations

Applications:
- Never communicate directly with Docker services
- Never assume a specific vendor or runtime
- Declare **required interfaces** and **asset dependencies**

The Gateway resolves implementations at runtime.

---

## 3. High-Level Architecture

```

Applications
↓
ABS AI Fabric Gateway (API Facade + Orchestrator)
↓
Asset Manager + Auto-Wake
↓
Asset Implementations (Core + Extended)

```

The Gateway is the **compatibility firewall** and **control plane**.

---

## 4. Repository Structure (Target State)

```

ABS/
├── abs-ai-hub/
│   ├── apps/                      # Business applications
│   ├── hub-ui/                    # UI for gateway & asset management
│   ├── docs/
│   └── installers/
│
├── core/                          # Minimal always-on runtime
│   ├── gateway/
│   │   ├── routers/
│   │   ├── services/
│   │   │   ├── asset_manager.py
│   │   │   ├── autowake.py
│   │   │   └── docker_service.py
│   │   └── adapters/              # Interface → implementation adapters
│   │
│   ├── bindings.yaml              # Interface bindings
│   ├── core.yml                   # Minimal base services
│   └── scripts/
│
├── core-interfaces/               # Contracts only (no runtime)
│   ├── llm-runtime.md
│   ├── vector-store.md
│   ├── cache-queue.md
│   ├── object-store.md
│   └── speech.md
│
├── assets/                        # Asset definitions
│   ├── registry/
│   │   ├── assets.json
│   │   ├── packs.json
│   │   └── policies.json
│   │
│   ├── core/                      # Default core implementations
│   │   ├── llm-runtime/
│   │   │   ├── ollama/
│   │   │   └── vllm/
│   │   └── vector-store/
│   │
│   └── extended/                  # Extended Asset Packs
│       ├── llm-xl/
│       ├── speech/
│       ├── document-intelligence/
│       └── vision/

````

---

## 5. Core Interfaces

### 5.1 Definition

A **Core Interface** defines:
- Required capabilities
- Required APIs
- Behavioral expectations
- Versioned compatibility contract

Examples:
- `llm-runtime`
- `vector-store`
- `cache-queue`
- `object-store`

---

### 5.2 Example: LLM Runtime Interface

```yaml
interface: llm-runtime
version: v1
capabilities:
  - chat
  - embeddings
  - streaming
required_endpoints:
  - POST /v1/chat/completions
  - POST /v1/embeddings
metadata:
  - model_id
  - context_length
  - gpu_required
````

Interfaces are versioned and backward compatible whenever possible.

---

## 6. Core Implementations

Core implementations live under `assets/core/`.

```
assets/core/llm-runtime/
├── ollama/
│   ├── asset.yaml
│   └── runtime.yaml
└── vllm/
    ├── asset.yaml
    └── runtime.yaml
```

Each implementation:

* Implements a Core Interface
* Declares resource requirements
* Can be activated or replaced independently

---

## 7. Core Bindings

Active implementations are selected via configuration, not code.

```yaml
# core/bindings.yaml
core_bindings:
  llm-runtime: ollama
  vector-store: qdrant
  cache-queue: redis
```

Changing bindings:

* Requires no application changes
* Is reversible
* Is centrally controlled

---

## 8. Extended Asset Packs

### 8.1 Definition

Extended Asset Packs provide **optional, high-cost, or specialized capabilities**, such as:

* 70B reasoning models
* Speech-to-text (Whisper)
* OCR and document parsing
* Vision models

They are:

* User-requestable
* Admin-approved
* Auto-activated and auto-suspended

---

### 8.2 Pack Structure

```
assets/extended/llm-xl/
├── pack.yaml
├── deepseek-r1-70b/
│   ├── asset.yaml
│   ├── runtime.yaml
│   └── install.ps1
└── llama3-70b/
```

---

### 8.3 Pack Definition Example

```yaml
pack_id: llm-xl
display_name: Large Reasoning Models
assets:
  - deepseek-r1-70b
  - llama3-70b
policies:
  admin_approval_required: true
  auto_sleep_minutes: 20
```

---

## 9. Asset Lifecycle Model

Assets follow a controlled lifecycle:

```
registered → installed → idle → warming → running
                 ↓
              suspended → error
```

Lifecycle transitions are managed by:

* `asset_manager`
* `autowake`
* `docker_service`

---

## 10. Gateway Responsibilities

The **ABS AI Fabric Gateway** is the system control plane.

Responsibilities:

* Interface enforcement
* Asset resolution
* Auto-wake / auto-sleep
* Dependency validation
* Backward compatibility shielding

The Gateway is the **only layer aware of concrete implementations**.

---

## 11. Application Rules

Applications must:

* Declare interface requirements
* Declare asset dependencies
* Never manage infrastructure directly

Example `app.yaml`:

```yaml
required_interfaces:
  - llm-runtime:v1
required_assets:
  - qdrant
optional_assets:
  - deepseek-r1-70b
```

---

## 12. Hub-UI Responsibilities

The UI provides:

* Asset catalog browsing
* Core vs Extended visibility
* Asset request & approval flows
* Resource usage visibility
* Data inspection tools

The UI never communicates with Docker directly.

---

## 13. Upgrade & Evolution Strategy

Supported:

* Core runtime replacement
* Parallel implementations
* Gradual app migration
* Safe asset deprecation

Avoided:

* Hard-coded vendors
* Breaking changes without migration paths
* Direct app-to-service coupling

---

## 14. Why This Architecture Matters

This architecture enables:

* Long-lived on-prem platforms
* Hardware investment protection
* Enterprise trust
* Predictable operational costs
* Future SaaS or hybrid deployment models

---

## 15. Recommended Implementation Phases

1. Introduce `core-interfaces`
2. Add asset registry and definitions
3. Implement `asset_manager`
4. Bind core implementations via configuration
5. Expose Assets UI
6. Migrate optional services into assets

---

## 16. Summary

**ABS AI Fabric** is designed as an **AI operating fabric**, not a fixed toolchain.

Stable interfaces combined with asset-based flexibility ensure:

* Today’s needs are met
* Tomorrow’s changes are safe
* Teams can build with confidence
