# ABS AI Fabric – Asset Management Standard (v1.0)

**Status:** Approved
**Audience:** Gateway, Hub-UI, Infra, Application Engineers
**Scope:** ABS AI Hub / ABS AI Fabric
**Version:** 1.0

---

## 1. Purpose

This document defines **how assets are managed, governed, and operated** in ABS AI Fabric.

It does **not** redefine asset fields or schemas.
Instead, it specifies:

* Asset categories and organization
* Lifecycle and status behavior
* Pack governance and enforcement
* Gateway and Hub UI responsibilities
* Normative usage rules for the asset schema

> The **Standard Asset Schema v1.0** is the *only canonical schema definition*
> and MUST be used for all asset authoring and validation.

---

## 2. Canonical Schema Reference

All assets in ABS AI Fabric MUST conform to:

> **Standard Asset Schema v1.0**
> (`docs/architecturestandard_asset_schema_v1.0.md`)

This document defines:

* Required and optional fields
* Field-level semantics
* Validation rules
* Backward compatibility notes
* Sample assets

📌 **This Asset Management document references the schema but does not duplicate it.**

---

## 3. Core Principles

### 3.1 Everything Is an Asset

All managed capabilities are modeled as **Assets**, including:

* Applications
* Core infrastructure services
* Models
* Tools
* Datasets

Assets are:

* Declarative
* Versioned
* Centrally indexed
* Lifecycle-managed by the Gateway

---

### 3.2 Interface-First Architecture

Assets bind to **interfaces**, not implementations.

* Interfaces define contracts
* Implementations are resolved dynamically
* Applications never bind directly to runtimes or containers

This enables:

* Runtime replacement
* Parallel implementations
* Safe upgrades

---

### 3.3 Packs Are Distribution, Not Types

**Asset Packs**:

* Do not introduce new asset types
* Do not replace asset identity
* Provide grouping, governance, and limits

---

## 4. Asset Categories (v1.0 – Locked)

All assets MUST belong to exactly one category:

```text
assets/
├── apps/
├── core/
├── models/
├── tools/
├── datasets/
```

### Category Semantics

| Category | Purpose                        |
| -------- | ------------------------------ |
| apps     | User-facing applications       |
| core     | Shared infrastructure services |
| models   | Inference artifacts            |
| tools    | Atomic capabilities            |
| datasets | Persistent knowledge           |

Categories are **organizational and semantic**, not behavioral.

---

## 5. Asset Registry

### 5.1 Registry Role

The registry provides a **single index** of all assets.

* It lists asset IDs and file paths
* It contains no business logic
* It does not duplicate asset metadata

---

### 5.2 Registry Structure

```json
{
  "version": "1.0",
  "assets": [
    {
      "asset_id": "ollama",
      "path": "core/llm-runtime/ollama/asset.yaml"
    }
  ]
}
```

The Gateway uses the registry to discover assets and load their definitions.

---

## 6. Asset Lifecycle & Status

### 6.1 Declarative Intent vs Observed State

The asset schema separates:

| Concept                | Field               | Authority    |
| ---------------------- | ------------------- | ------------ |
| Desired behavior       | `lifecycle.desired` | Asset author |
| Observed runtime state | `lifecycle.state`   | Gateway      |

**Asset authors MUST NOT set or modify `lifecycle.state`.**

---

### 6.2 Lifecycle States

Observed states are:

* `registered`
* `installed`
* `idle`
* `warming`
* `running`
* `suspended`
* `error`

State transitions are enforced by the Gateway according to the **Asset Status Lifecycle State Machine v1.0**.

---

### 6.3 Auto-Wake / Auto-Sleep

* Assets with `desired: on-demand` are auto-woken on request
* Idle assets may transition to `suspended`
* Pack limits may override asset-level auto-sleep

---

## 7. Asset Packs

### 7.1 Definition

An **Asset Pack** is a **policy and governance layer** applied to a group of assets.

Packs:

* Are optional
* Do not alter asset schemas
* Apply additional constraints and approvals

---

### 7.2 Pack Specification

Packs are defined via:

```text
assets/packs/<pack_id>/pack.yaml
```

The `pack.yaml` spec defines:

* Tier (core / extended / experimental)
* Requestability and approval rules
* Resource budgets
* Concurrency and auto-sleep limits
* UI hints

---

### 7.3 Asset–Pack Relationship

Assets opt into packs using:

```yaml
pack_id: <pack_id>
```

Assets remain first-class and independently lifecycle-managed.

---

## 8. Schema Usage Rules (Normative)

This section defines **how the Standard Asset Schema v1.0 MUST be used**.

---

### 8.1 Lifecycle Rules

* `lifecycle.desired` is author-defined
* `lifecycle.state` is Gateway-owned and read-only
* UI MUST display observed state, not desired state

---

### 8.2 Interface Rules

* Applications MUST declare required interfaces
* Implementations are resolved by the Gateway
* UI MUST surface interface names, not runtime details

---

### 8.3 Policy Rules

* `required_models` applies ONLY to `class: app`
* `served_models` applies ONLY to runtimes/services
* `max_concurrency` is enforced by the Gateway

---

### 8.4 Ownership & Visibility Rules

* `ownership.requestable` controls whether users can request an asset
* `visibility` controls discoverability in the UI
* Packs may impose stricter rules than assets

---

## 9. Gateway Responsibilities

The Gateway is the **sole control plane**.

It MUST:

1. Load the registry and asset definitions
2. Validate assets against Standard Asset Schema v1.0
3. Resolve interfaces to implementations
4. Enforce lifecycle and pack rules
5. Populate observed state
6. Expose Assets and Packs APIs

---

## 10. Hub UI Responsibilities

The Hub UI:

* Displays assets by category
* Shows interface, pack, and status
* Allows requests based on ownership and pack rules
* Does NOT manage runtime directly

The UI is **observational, not imperative**.

---

## 11. Explicit Non-Goals (v1.0)

This document does NOT define:

* Billing or pricing
* Workflow orchestration
* Dependency graphs
* Kubernetes CRDs
* Agent-specific abstractions

These may be layered later without changing the asset model.

---

## 12. Summary

ABS AI Fabric Asset Management v1.0:

* Uses **Standard Asset Schema v1.0** as the sole contract
* Cleanly separates schema from behavior
* Provides predictable lifecycle management
* Supports safe extensibility via packs
* Aligns Gateway, UI, and filesystem models

> This document defines **how assets behave**,
> not **what an asset is**.
