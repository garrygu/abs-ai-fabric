# Model Management Design: LLM vs Embedding Models

**Document Type:** Engineering Design Spec
**Status:** Proposed (v1.0)
**Audience:** Platform, Gateway, Hub-UI, Infra Engineers
**Applies To:** ABS AI Fabric – Admin → Model Management

---

## 1. Purpose

This document defines how **LLM models** and **Embedding models** are represented, managed, and operated in **ABS AI Fabric**.

The goal is to:

* Preserve the principle that **everything is an Asset**
* Improve operational clarity and governance
* Enable correct lifecycle, policy, and observability behavior
* Support future multi-runtime evolution (Ollama, vLLM, TEI, external APIs)

---

## 2. Background & Problem Statement

Currently, Model Management treats all models as a flat list.
This creates ambiguity because **LLMs and Embedding models differ fundamentally** in:

* Runtime behavior
* Resource usage
* Lifecycle expectations
* Observability metrics
* Governance and approval workflows

As ABS AI Fabric evolves toward an **AI OS-like platform**, this distinction must be explicit and enforced by interfaces rather than convention.

---

## 3. Design Principles

1. **Everything is an Asset**
   Models remain first-class assets with lifecycle, policy, and observability.

2. **Interfaces define semantics**
   Operational behavior is driven by `interface`, not UI heuristics.

3. **No breaking changes to apps**
   Existing `/v1/chat/completions` and `/v1/embeddings` APIs remain stable.

4. **Evolvable Core**
   Model types must support future runtimes without refactoring apps.

---

## 4. High-Level Decision

### ✅ Introduce a dedicated interface: `embedding-runtime`

| Model Type       | Interface              |
| ---------------- | ---------------------- |
| LLM Models       | `llm-runtime:v1`       |
| Embedding Models | `embedding-runtime:v1` |

Both are:

* `class: model`
* Managed by the same Asset Manager
* Resolved by the Gateway

---

## 5. Interface Definitions

### 5.1 LLM Runtime Interface (Existing)

```yaml
interface: llm-runtime
version: v1
capabilities:
  - chat
  - streaming
  - function_calling
required_endpoints:
  - POST /v1/chat/completions
metadata:
  - model_id
  - context_length
  - gpu_required
```

---

### 5.2 Embedding Runtime Interface (New)

```yaml
interface: embedding-runtime
version: v1
capabilities:
  - embeddings
required_endpoints:
  - POST /v1/embeddings
metadata:
  - model_id
  - embedding_dim
  - precision
```

> The Gateway already supports `/v1/embeddings`; this formalizes the contract.

---

## 6. Asset Schema Usage

### 6.1 LLM Model Asset (Example)

```yaml
asset_id: llama3-8b
display_name: LLaMA 3 8B
version: "1.0.0"

interface: llm-runtime
interface_version: v1
class: model

resources:
  gpu_required: true
  min_vram_gb: 16
  disk_gb: 5

lifecycle:
  desired: on-demand
  auto_sleep_min: 15

policy:
  max_concurrency: 2
```

---

### 6.2 Embedding Model Asset (Example)

```yaml
asset_id: nomic-embed-text
display_name: Nomic Embed Text
version: "1.0.0"

interface: embedding-runtime
interface_version: v1
class: model

resources:
  gpu_required: true
  min_vram_gb: 4
  disk_gb: 2

lifecycle:
  desired: running
  auto_sleep_min: 0

policy:
  max_concurrency: 10

metadata:
  embedding_dim: 768
```

---

## 7. Lifecycle Defaults (Policy Recommendation)

| Model Type | desired     | auto_sleep      |
| ---------- | ----------- | --------------- |
| LLM        | `on-demand` | 10–20 min       |
| Embedding  | `running`   | disabled / long |

Rationale:

* LLMs are interactive and expensive
* Embeddings are infrastructure primitives used frequently

---

## 8. Gateway Responsibilities

The Gateway must:

1. Resolve models by **interface**, not name
2. Route requests:

   * `/v1/chat/completions` → `llm-runtime`
   * `/v1/embeddings` → `embedding-runtime`
3. Enforce:

   * Auto-wake
   * Auto-sleep
   * Concurrency limits
4. Remain the **only component aware of concrete runtimes**

No changes are required to application code.

---

## 9. Hub-UI Changes (Admin → Models)

### 9.1 Visual Grouping

```
🧠 Language Models (LLM)
- llama3.2
- deepseek-r1-70b

📐 Embedding Models
- nomic-embed-text
- bge-large
```

### 9.2 Display Differences

**LLMs**

* Context length
* Tokens/sec
* Active sessions

**Embeddings**

* Vector dimension
* QPS
* Index throughput

---

## 10. Observability Implications

Metrics should be tagged with:

```text
asset_id
interface
model_type (derived)
```

Recommended KPIs:

| Model Type | Metrics                      |
| ---------- | ---------------------------- |
| LLM        | latency, tokens/sec, VRAM    |
| Embedding  | QPS, batch size, vector dims |

---

## 11. Backward Compatibility

* Existing assets remain valid
* Models serving both chat + embeddings may temporarily implement **both interfaces**
* Migration can be incremental

---

## 12. Future Extensions

This design enables:

* Dedicated embedding runtimes (TEI, Instructor, OpenAI)
* CPU-only embedding services
* Multi-embedding-model selection per app
* Embedding caching & batching strategies

---

## 13. Summary

By separating **LLM models** and **Embedding models** at the **interface level**, ABS AI Fabric gains:

* Clear operational semantics
* Better governance and observability
* Cleaner UI and admin workflows
* Strong alignment with the AI OS architecture

This change is **non-breaking**, **low-risk**, and **high-leverage**.

---

**End of Document**
