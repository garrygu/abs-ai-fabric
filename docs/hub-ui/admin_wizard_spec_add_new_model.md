# Admin Wizard Spec: Add New Model

**Document Type:** Engineering + Product Specification
**Status:** Proposed (v1.0)
**Audience:** Hub-UI, Gateway, Platform, Infra Engineers
**Applies To:** ABS AI Fabric – Admin → Models
**Feature Name:** Add New Model Wizard

---

## 1. Purpose

The **Add New Model Wizard** provides a **safe, guided, and auditable** process for introducing new models into ABS AI Fabric and exposing them to end users **without breaking applications**.

This wizard enforces:

* Interface correctness
* Resource awareness
* Validation before exposure
* Governance & approval
* Full observability

---

## 2. Design Principles

1. **Declarative, not procedural**
   The wizard produces an **asset definition**, not imperative logic.

2. **No app impact by default**
   Models are invisible until explicitly approved.

3. **Fail closed**
   Validation failures prevent exposure.

4. **One-way progression**
   Each step must pass before advancing.

5. **Reversible at every stage**
   Rollback requires no app redeploys.

---

## 3. Wizard Entry Points

### Primary

* Admin → Models → **➕ Add Model**

### Secondary (future)

* Admin → Assets → Add Asset → Model

---

## 4. Wizard Flow Overview

```
Step 1: Model Basics
   ↓
Step 2: Interface & Runtime
   ↓
Step 3: Resource Requirements
   ↓
Step 4: Install / Pull
   ↓
Step 5: Validation
   ↓
Step 6: Exposure & Policy
   ↓
Step 7: Review & Confirm
```

Each step saves **draft state**.

---

## 5. Step-by-Step Specification

---

## STEP 1 — Model Basics

**Goal:** Identify the model and create asset identity.

### Fields

| Field        | Required | Notes                    |
| ------------ | -------- | ------------------------ |
| Display Name | ✅        | Human-readable           |
| Asset ID     | ✅        | Auto-suggested, editable |
| Description  | ⬜        | Markdown supported       |
| Version      | ⬜        | Defaults to `1.0.0`      |
| Provider     | ⬜        | Meta only                |

### System Actions

* Validate `asset_id` uniqueness
* Create **draft asset**

---

## STEP 2 — Interface & Runtime

**Goal:** Define semantic behavior and routing.

### Required Selection

**Model Interface**

* 🧠 `llm-runtime:v1`
* 📐 `embedding-runtime:v1`
* (future) vision, speech, reranker

### Runtime Type

* `container` (default)
* `external` (future)

### Runtime Fields (container)

| Field            | Required      |
| ---------------- | ------------- |
| Install Command  | ✅             |
| Runtime Endpoint | Auto-derived  |
| Protocol         | default: REST |

### System Actions

* Lock interface (cannot change later)
* Pre-configure Gateway routing

⚠️ Interface choice determines:

* Observability metrics
* Lifecycle defaults
* UI grouping

---

## STEP 3 — Resource Requirements

**Goal:** Prevent system overload.

### Fields

| Field                     | Required |
| ------------------------- | -------- |
| GPU Required              | ✅        |
| Min VRAM (GB)             | ⬜        |
| Min RAM (GB)              | ⬜        |
| Disk Footprint (GB)       | ⬜        |
| Expected Cold Start (sec) | ⬜        |

### System Actions

* Validate against host capacity
* Warn (not block) if insufficient

---

## STEP 4 — Install / Pull

**Goal:** Make model available locally without exposure.

### UI Actions

* **Install Model** button
* Live progress output
* Retry / Cancel

### States

| State         | Meaning              |
| ------------- | -------------------- |
| Not Installed | No artifacts         |
| Installing    | Pull in progress     |
| Installed     | Ready for validation |
| Failed        | Retry allowed        |

### System Actions

* Execute install command once
* Record install logs
* Update asset lifecycle → `installed`

---

## STEP 5 — Validation (Mandatory Gate)

**Goal:** Ensure runtime correctness before exposure.

### Validation Checks (per interface)

#### LLM Runtime

* `/v1/chat/completions` responds
* Model metadata retrievable
* Cold start < expected threshold

#### Embedding Runtime

* `/v1/embeddings` responds
* Vector dimension matches metadata
* Batch request succeeds

### Outcomes

| Result | Action            |
| ------ | ----------------- |
| Pass   | Continue          |
| Warn   | Admin can proceed |
| Fail   | Block exposure    |

### System Actions

* Store validation report
* Expose results in Observability

---

## STEP 6 — Exposure & Policy

**Goal:** Control who can use the model.

### Policy Controls

| Setting           | Options             |
| ----------------- | ------------------- |
| Visibility        | shared / private    |
| Requestable       | yes / no            |
| Allowed Apps      | multi-select        |
| Max Concurrency   | numeric             |
| Default Lifecycle | on-demand / running |

### Defaults

| Interface | Default   |
| --------- | --------- |
| LLM       | on-demand |
| Embedding | running   |

⚠️ Model is still **not active** until confirmed.

---

## STEP 7 — Review & Confirm

**Goal:** Final approval checkpoint.

### Summary View

* Asset YAML preview (read-only)
* Interface & lifecycle
* Resource usage
* Exposure policy
* Validation results

### Actions

* ✅ Confirm & Activate
* ⬅ Back to Edit
* ❌ Cancel (discard draft)

### System Actions

* Commit asset to registry
* Activate lifecycle
* Emit audit log event

---

## 6. Post-Wizard Behavior

After confirmation:

### System Effects

* Model appears in:

  * Admin → Models
  * Observability → Models
* Gateway routes traffic
* Auto-wake enabled
* Health contributes to System Health

### End User Impact

* New capability becomes available
* No restart
* No app changes

---

## 7. Failure & Rollback Handling

### Rollback Options

| Action          | Effect           |
| --------------- | ---------------- |
| Suspend Model   | Immediate stop   |
| Remove Exposure | Hidden from apps |
| Delete Asset    | Full removal     |

Rollback **never** requires app redeploy.

---

## 8. Audit & Logging

Every wizard action emits:

* `model.added`
* `model.installed`
* `model.validated`
* `model.exposed`

Stored in:

* Admin Logs
* Change Log
* Observability Timeline

---

## 9. Security & Guardrails

* Admin-only access
* No raw command execution outside install sandbox
* Interface immutable post-creation
* Validation required before exposure

---

## 10. Non-Goals (Explicit)

* ❌ Model fine-tuning
* ❌ Prompt management
* ❌ User-level model switching
* ❌ Billing / metering (future)

---

## 11. Success Criteria

The wizard is successful if:

* New models can be added **without code changes**
* Exposure is intentional and auditable
* Observability works on day one
* Rollback is trivial

---

## 12. Summary

The **Add New Model Wizard** formalizes model onboarding as a **platform capability**, not an engineering task.

It turns “adding a model” into:

> A safe, repeatable, governed operation
> consistent with an AI OS.

