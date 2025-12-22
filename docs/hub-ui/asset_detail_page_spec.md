# Asset Detail Page – Engineering Specification (v1.0.1)

**Product:** ABS AI Hub
**Audience:** Frontend, Gateway, Platform Engineers
**Status:** Approved (revision)
**Supersedes:** v1.0
**Schema Alignment:** Standard Asset Schema v1.0

---

## 1. Revision Summary (v1.0 → v1.0.1)

This revision introduces **explainability and usability improvements** without expanding backend scope.

### Changes in v1.0.1

1. Added **Health Check Insight** to Lifecycle section (from Observability)
2. Promoted **Open App** to a primary action for app assets
3. Added **Resource Badges** (GPU / VRAM) for visual parity
4. Included **`lifecycle.auto_sleep_min`** in Lifecycle details
5. Clarified **authored vs observed relationships** in dependency views

No breaking changes.

---

## 2. Purpose & Goals

The Asset Detail Page is the **truth surface** for a single asset, and the primary source of truth for understanding an individual asset’s:

* Identity and contract
* Desired vs observed lifecycle state
* Usability constraints
* Dependencies and consumers
* Safe, contextual actions

Answering:

* What the asset *is*
* What it *wants to do* (intent)
* What it *is doing* (observed state)
* Why it is in that state
* Who depends on it
* What actions are safe

This page is not a configuration editor and not an observability dashboard.It is **read-only by default**, with **contextual actions only**.

---

## 3. Target Users

### Primary

* Platform / Infra Engineers
* AI Infrastructure Engineers

### Secondary

* App Builders
* AI Developers

### Explicitly Excluded

* End users
* Policy editors
* YAML authorship workflows

---

## 4. Data Sources

| Source                      | Responsibility             |
| --------------------------- | -------------------------- |
| `GET /v1/assets/{asset_id}` | Asset definition           |
| Gateway lifecycle engine    | `lifecycle.state`          |
| Observability service       | health + dependency checks |
| Gateway metadata            | `metadata._status`         |
| Asset registry              | authored relationships     |

---

## 5. Page Layout Overview

```
┌──────────────────────────────────────────┐
│ Header: Identity + Status + Primary Action│
├──────────────────────────────────────────┤
│ Identity & Contract                      │
├──────────────────────────────────────────┤
│ Lifecycle (Intent vs Observed + Health)  │
├──────────────────────────────────────────┤
│ Policy & Resource Constraints            │
├──────────────────────────────────────────┤
│ Relationships (Authored)                 │
├──────────────────────────────────────────┤
│ Runtime & Status (Read-only)             │
├──────────────────────────────────────────┤
│ Contextual Actions                       │
└──────────────────────────────────────────┘
```

---

## 6. Section Specifications

---

## 6.1 Header – Identity & Primary Action

**Purpose:** Immediate orientation and safe action affordance

**UI Elements**

* Asset icon (by class)
* Display name
* Badges:

  * `class`
  * `interface`
  * `lifecycle.state`

### Primary Action (v1.0.1)

* **App assets ONLY**: show **Open App** as a primary (hero) button
* Other asset types: no primary action

**Example**

```
📄 Contract Reviewer v2
[ Open App ]

[ app ] [ interface: application ] [ status: Idle ]
Used by 0 apps • Requires 1 model
```

---

## 6.2 Identity & Contract

Immutable, schema-backed fields.

| Field             | Source                 |
| ----------------- | ---------------------- |
| Asset ID          | `asset_id`             |
| Version           | `version`              |
| Class             | `class`                |
| Interface         | `interface`            |
| Interface Version | `interface_version`    |
| Provider          | `provider`             |
| Visibility        | `visibility`           |
| Pack ID           | `pack_id` (if present) |

---

## 6.3 Lifecycle – Intent, State & Health (Updated)

**Purpose:** Explain *why* the asset is in its current state.

### Intent vs Observed

| Field              | Source                             |
| ------------------ | ---------------------------------- |
| Desired State      | `lifecycle.desired`                |
| Observed State     | `lifecycle.state`                  |
| Auto-sleep Timeout | `lifecycle.auto_sleep_min`         |
| Last Used At       | `metadata._status.last_used_at`    |
| Last Started At    | `metadata._status.last_started_at` |

### Health Check Insight (NEW)

Derived from Observability:

```
Health Insight
✓ Service Health: OK
✓ Dependency Health: All dependencies available
✗ Last Failure: None
Last checked: 1m ago
```

**Rules**

* Health is **observational**, not control-plane state
* Health does NOT override lifecycle state
* Visual indicators:

  * ✓ Healthy
  * ⚠️ Degraded
  * ✗ Failed

---

## 6.4 Policy & Resource Constraints (Enhanced)

**Purpose:** Answer “Can / should I use this asset?”

### Visual Resource Badges (NEW)

Displayed prominently:

* 🔥 GPU | 16GB
* 🧠 RAM | 32GB
* 💾 Disk | 50GB (optional)

### Policy Details (by asset type)

#### Model

* Served by runtime(s)
* Format
* Parameter size
* GPU required

#### App

* Required models
* Required tools
* Required datasets

#### Service

* Provided interfaces
* GPU usage
* Availability

**Source**

* `policy`
* `resources`
* `metadata`

---

## 6.5 Relationships – Authored Dependencies (Clarified)

**Purpose:** Show declared dependency intent.

### Consumers

Assets that *declare* dependency on this asset.

### Providers

Assets that *provide* required interfaces.

### Important Clarification (NEW)

> **Note:**
> In v1.0.x, relationship data reflects **authored intent**, derived from asset policy definitions
> (e.g. `policy.required_models`).
>
> True runtime consumer tracking is a planned backend enhancement and is **not yet available**.

This prevents UI/backend expectation mismatch.

---

## 6.6 Runtime & Status (Read-only)

Operational signals only.

| Field           | Source                             |
| --------------- | ---------------------------------- |
| Health          | Observability                      |
| Active Requests | `metadata._status.active_requests` |
| Cold Start Time | `resources.cold_start_sec`         |
| Reason          | `metadata._status.reason`          |

No logs, no charts.

---

## 6.7 Contextual Actions

Actions are **type + state + RBAC aware**.

| Asset Type | Actions                           |
| ---------- | --------------------------------- |
| app        | Open App (primary), View Bindings |
| service    | Start, Stop, Restart              |
| model      | View Usage, Disable (admin)       |
| dataset    | View Usage                        |
| tool       | Enable / Disable                  |

**Rules**

* Invalid actions MUST NOT render
* Destructive actions require confirmation
* RBAC enforced server-side

---

## 7. RBAC Summary

| Role      | Permissions                  |
| --------- | ---------------------------- |
| Viewer    | Read-only                    |
| Developer | Open app, view relationships |
| Operator  | Start / stop services        |
| Admin     | Disable assets               |

---

## 8. Explicit Non-Goals

The Asset Detail Page MUST NOT:

* Edit YAML
* Edit policy
* Show raw logs
* Replace Observability UI

---

## 9. Error & Edge Handling

| Condition                 | Behavior                |
| ------------------------- | ----------------------- |
| Asset missing             | 404 + back link         |
| Legacy asset              | Warning banner          |
| Partial metadata          | Graceful fallback       |
| Observability unavailable | Health marked “Unknown” |

---

## 10. Success Criteria

* Engineers can explain an asset’s state in <30 seconds
* No confusion between desired vs observed
* Users understand *why* an asset is idle or running
* Actions are safe, obvious, and contextual

---

## 11. Future (Out of Scope)

* Observed consumer tracking
* Cost attribution
* Inline dependency graphs
* Policy editing

---

**v1.0.1 principle:**
> *This page is a truth surface, not a control surface.*   
> *If the UI cannot explain why an asset is in its current state, the UI is incomplete.*
