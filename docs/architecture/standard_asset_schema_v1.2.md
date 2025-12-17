# Standard Asset Schema v1.1

**Status:** Engineering Specification  
**Audience:** Platform, Gateway, Hub-UI, Infra Engineers  
**Applies to:** ABS AI Fabric Asset Registry

---

## 1. Overview

The **Standard Asset Schema** defines a unified structure for representing **all managed entities** in ABS AI Fabric, including:

- Services (LLM runtimes, vector stores, caches)
- Models (7B–70B LLMs, Whisper, OCR)
- Tools (parsers, TTS, translation)
- Applications
- Datasets

This schema enables:
- Centralized asset management
- Interface-driven orchestration
- Auto-wake and auto-sleep
- Resource governance
- Safe evolution of core components

---

## 2. Design Principles

- **Everything is an Asset**
- **Apps bind to interfaces, not implementations**
- **Lifecycle intent is separate from runtime state**
- **Resource cost is explicit**
- **Schema must be YAML-friendly and human-readable**

---

## 3. Asset Schema Definition

```yaml
# =========================
# Identity
# =========================
asset_id: string                # Unique identifier (required)
display_name: string            # Human-readable name
version: string                 # Semantic version (e.g. "1.0.0")

# =========================
# Contract
# =========================
interface: string               # Interface implemented (e.g. llm-runtime)
interface_version: string       # Interface version (e.g. v1)
class: enum                     # app | service | model | tool | dataset

description: string             # Multi-line description

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
  health: string                # Health check endpoint
  api_base: string              # Base API URL

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
  allowed_models: list          # Models allowed (for apps/services)
  defaults: object              # Asset-specific defaults

# =========================
# Metadata
# =========================
metadata: object                # Free-form additional data
````

---

## 4. Property Purpose & Engineering Notes

### 4.1 Identity

| Field          | Purpose                                               |
| -------------- | ----------------------------------------------------- |
| `asset_id`     | Stable identifier used across registry, API, and UI   |
| `display_name` | Human-readable label for UI                           |
| `version`      | Enables upgrade, rollback, and compatibility tracking |

---

### 4.2 Contract

| Field               | Purpose                                            |
| ------------------- | -------------------------------------------------- |
| `interface`         | Declares which core interface the asset implements |
| `interface_version` | Enforces compatibility with apps                   |
| `class`             | Determines how the asset is managed and displayed  |

---

### 4.3 Ownership & Visibility

| Field         | Purpose                                       |
| ------------- | --------------------------------------------- |
| `provider`    | Identifies who owns and maintains the asset   |
| `visibility`  | Determines whether asset is shared or private |
| `requestable` | Enables user request flows in Hub-UI          |

---

### 4.4 Resource Requirements

| Field            | Purpose                                |
| ---------------- | -------------------------------------- |
| `gpu_required`   | Used for scheduling and admin approval |
| `min_vram_gb`    | Prevents invalid model activation      |
| `min_ram_gb`     | Guards against host memory exhaustion  |
| `disk_gb`        | Storage planning and cost visibility   |
| `cold_start_sec` | UI warnings and auto-wake tuning       |

---

### 4.5 Runtime

| Field             | Purpose                                  |
| ----------------- | ---------------------------------------- |
| `runtime.type`    | Determines how asset is executed         |
| `container`       | Docker execution details (if applicable) |
| `install.command` | Pull/install models or tools             |
| `install.once`    | Prevents repeated installs               |

---

### 4.6 Endpoints

| Field      | Purpose                                    |
| ---------- | ------------------------------------------ |
| `health`   | Health checks for auto-wake and monitoring |
| `api_base` | Gateway routing target                     |

---

### 4.7 Lifecycle

| Field            | Purpose                                         |
| ---------------- | ----------------------------------------------- |
| `desired`        | Declarative intent (admin or system controlled) |
| `auto_sleep_min` | Auto-suspend tuning                             |
| `state`          | Observed runtime state (managed by system)      |

> **Important:**
> `desired` ≠ `state`.
> The system reconciles desired intent with actual state.

---

### 4.8 Policy

| Field             | Purpose                      |
| ----------------- | ---------------------------- |
| `max_concurrency` | Prevents resource exhaustion |
| `allowed_apps`    | Enforces governance          |
| `allowed_models`  | Restricts usage scope        |
| `defaults`        | Asset-specific behavior      |

---

### 4.9 Metadata

| Field      | Purpose                             |
| ---------- | ----------------------------------- |
| `metadata` | Extension point for future features |

---

## 5. Sample Asset Definition

### Example: DeepSeek R1 70B Model

```yaml
asset_id: deepseek-r1-70b
display_name: DeepSeek R1 70B
version: "1.0.0"

interface: llm-runtime
interface_version: v1
class: model

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

## 6. Summary

The Standard Asset Schema:

* Unifies services, models, tools, and apps
* Enables safe orchestration and governance
* Supports auto-wake and evolvable core design
* Provides a future-proof foundation for ABS AI Fabric

This schema is **intentionally minimal but complete**, and can be extended without breaking compatibility.
