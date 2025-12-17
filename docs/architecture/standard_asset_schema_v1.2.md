# Standard Asset Schema v1.2

**Status:** Engineering Specification  
**Audience:** Platform, Gateway, Hub-UI, Infra Engineers  
**Applies to:** ABS AI Fabric Asset Registry  
**Supersedes:** v1.1

---

## 1. Overview

The **Standard Asset Schema v1.2** defines a unified, extensible structure for representing **all managed entities** in ABS AI Fabric, including:

- Services (LLM runtimes, vector stores, caches)
- Models (7B–70B LLMs, Whisper, OCR)
- Tools (parsers, TTS, translation)
- Applications
- Datasets

This schema enables:

- Interface-driven orchestration
- Auto-wake / auto-sleep lifecycle management
- Explicit resource governance
- Safe evolution of core components
- Clear separation between **assets** and **asset packs**

---

## 2. Design Principles

1. **Everything is an Asset**  
   All shared capabilities are modeled uniformly.

2. **Apps bind to interfaces, not implementations**  
   Concrete runtimes are resolved by the Gateway.

3. **Lifecycle intent ≠ runtime state**  
   Declarative intent and observed state are distinct.

4. **Resource cost must be explicit**  
   GPU, memory, disk, and startup cost are first-class data.

5. **Packs are groupings, not assets**  
   Asset Packs organize assets but do not replace asset identity.

---

## 3. Asset Schema Definition (v1.2)

```yaml
# =========================
# Identity
# =========================
asset_id: string                # Unique identifier (required)
display_name: string            # Human-readable name
version: string                 # Semantic version (e.g. "1.2.0")

# =========================
# Contract
# =========================
interface: string               # Interface implemented (e.g. llm-runtime)
interface_version: string       # Interface version (e.g. v1)
class: enum                     # app | service | model | tool | dataset

description: string             # Multi-line description

# =========================
# Pack Association (Optional)
# =========================
pack_id: string                 # Asset Pack identifier (e.g. llm-xl)

# =========================
# Ownership & Visibility
# =========================
ownership:
  provider: enum                # system | admin | user
  visibility: enum              # shared | private
  requestable: boolean          # Can users request this asset?

# =========================
# Resource Requirements
# =========================
resources:
  gpu_required: boolean         # Whether GPU is required
  min_vram_gb: number           # Minimum GPU VRAM
  min_ram_gb: number            # Minimum system RAM
  disk_gb: number               # Disk footprint
  cold_start_sec: number        # Expected cold-start time

# =========================
# Runtime Definition
# =========================
runtime:
  type: enum                    # container | native | external
  container:
    image: string               # Docker image
    name: string                # Container name
    ports: list                 # Exposed ports
    volumes: list               # Volume mounts
  install:
    command: string             # One-time install or pull command
    once: boolean               # Run only once

# =========================
# Endpoints (Optional)
# =========================
endpoints:
  protocol: enum                # rest | grpc | websocket (default: rest)
  api_base: string              # Base API URL
  health: string                # Health check endpoint

# =========================
# Lifecycle
# =========================
lifecycle:
  desired: enum                 # running | on-demand | suspended
  auto_sleep_min: number        # Idle time before suspension
  state: enum                   # registered | installed | idle | warming | running | error

# =========================
# Policy
# =========================
policy:
  max_concurrency: number       # Max parallel usage
  allowed_apps: list            # Apps allowed to use this asset

  # Model semantics clarified
  required_models: list         # Models required by apps
  served_models: list           # Models served by runtimes/services

  defaults: object              # Asset-specific defaults

# =========================
# Metadata
# =========================
metadata: object                # Free-form additional data
````

---

## 4. Field-Level Clarifications (v1.2 Changes)

### 4.1 `pack_id` (New)

* Associates an asset with an **Extended Asset Pack**
* Packs are defined separately (e.g. `packs.yaml`)
* Assets remain first-class and independently lifecycle-managed

> `pack_id` is optional and MUST NOT affect asset identity.

---

### 4.2 Policy: `required_models` vs `served_models`

| Field             | Applies To          | Meaning                          |
| ----------------- | ------------------- | -------------------------------- |
| `required_models` | Apps                | Models the app needs to function |
| `served_models`   | Services / runtimes | Models this runtime can serve    |

This removes ambiguity present in v1.1.

---

### 4.3 `endpoints.protocol` (New)

Explicitly declares the protocol used by the asset endpoint.

Supported values (v1.2):

* `rest` (default)
* `grpc`
* `websocket`

Used by:

* Gateway routing
* UI capability display
* Future protocol-specific adapters

---

## 5. Validation & Type Enforcement

### 5.1 Source of Truth

* YAML is used for **authoring**
* **Runtime validation is mandatory**

### 5.2 Required Validation Layers

#### Gateway (Required)

* Pydantic models enforce:

  * Field presence
  * Enum values
  * Type correctness

#### Optional (Future)

* JSON Schema generated from Pydantic
* Used for:

  * Hub-UI form validation
  * CLI tooling
  * IDE autocomplete

---

## 6. Sample Asset (v1.2)

### DeepSeek R1 70B – Large Reasoning Model

```yaml
asset_id: deepseek-r1-70b
display_name: DeepSeek R1 70B
version: "1.2.0"

interface: llm-runtime
interface_version: v1
class: model
pack_id: llm-xl

description: |
  Large-scale reasoning model optimized for complex multi-step tasks
  and advanced analytical workloads.

ownership:
  provider: system
  visibility: shared
  requestable: true

resources:
  gpu_required: true
  min_vram_gb: 48
  min_ram_gb: 64
  disk_gb: 80
  cold_start_sec: 120

runtime:
  type: container
  install:
    command: ollama pull deepseek-r1:70b
    once: true

endpoints:
  protocol: rest
  api_base: http://ollama:11434

lifecycle:
  desired: on-demand
  auto_sleep_min: 20
  state: installed

policy:
  max_concurrency: 1
  allowed_apps:
    - contract-reviewer
    - deposition-summarizer

metadata:
  vendor: DeepSeek
  precision: fp16
  notes: Requires high-VRAM GPU
```

---

## 7. Backward Compatibility Notes

* v1.1 assets remain valid with:

  * `allowed_models` mapped to `required_models` or `served_models`
* `pack_id` is optional and non-breaking
* `endpoints.protocol` defaults to `rest` if omitted

---

## 8. Summary

Standard Asset Schema v1.2:

* Resolves semantic ambiguity
* Aligns with Extended Asset Pack architecture
* Improves Gateway and UI clarity
* Preserves backward compatibility
* Remains minimal and implementation-ready

This schema is the **contractual foundation** of ABS AI Fabric’s asset-based platform design.
