# ABS AI Fabric – Asset Status Lifecycle State Machine (v1.0)

**Status:** Approved
**Audience:** Gateway, Hub-UI, Infra Engineers
**Applies to:** All Assets (apps, core, models, tools, datasets)

---

## 1. Purpose

This document defines the **authoritative lifecycle state machine** for assets in ABS AI Fabric.

It standardizes:

* Allowed **asset runtime states**
* Valid **state transitions**
* Responsibilities of the **Gateway**
* How **UI and APIs** interpret state

This ensures:

* Predictable behavior
* Clear observability
* Safe auto-wake / auto-sleep
* No ambiguity between intent and reality

---

## 2. Key Design Principles

### 2.1 Desired ≠ Observed

Asset lifecycle is split into two dimensions:

| Dimension          | Source       | Meaning                      |
| ------------------ | ------------ | ---------------------------- |
| **Desired state**  | `asset.yaml` | What the system *should* do  |
| **Observed state** | Gateway      | What is *actually happening* |

The **Gateway is the source of truth** for observed state.

---

### 2.2 Lifecycle Applies to Runtime-Backed Assets

The lifecycle state machine applies to assets that have **runtime behavior**, including:

* Core services
* Tools
* Models (when loaded / served)

Pure metadata assets (e.g., static datasets) may remain in a terminal state.

---

## 3. Lifecycle States (Canonical)

### 3.1 State Definitions

| State          | Meaning                                                |
| -------------- | ------------------------------------------------------ |
| **registered** | Asset is known to the system but not installed         |
| **installed**  | Asset runtime/artifacts exist but are not running      |
| **idle**       | Asset is installed and ready, but not actively serving |
| **warming**    | Asset is starting (cold start, model load, etc.)       |
| **running**    | Asset is actively serving requests                     |
| **suspended**  | Asset was auto-stopped due to inactivity               |
| **error**      | Asset failed health check or startup                   |

---

### 3.2 State Semantics

* **registered**
  → Pure registry entry
  → No disk, GPU, or memory allocated

* **installed**
  → Docker image pulled / model downloaded
  → Not consuming runtime resources

* **idle**
  → Ready to serve
  → No active requests
  → Eligible for auto-sleep

* **warming**
  → Transitional
  → GPU / memory allocation in progress

* **running**
  → Actively serving traffic
  → Counts toward concurrency limits

* **suspended**
  → Runtime stopped
  → Can be auto-woken

* **error**
  → Requires operator or auto-recovery

---

## 4. State Machine Diagram (Logical)

```text
          ┌────────────┐
          │ registered │
          └─────┬──────┘
                │ install
                ▼
          ┌────────────┐
          │ installed  │
          └─────┬──────┘
                │ activate / auto-wake
                ▼
          ┌────────────┐
          │  warming   │
          └─────┬──────┘
                │ ready
                ▼
          ┌────────────┐
          │  running   │◄──────────────┐
          └─────┬──────┘               │
                │ idle timeout          │ request
                ▼                       │
          ┌────────────┐               │
          │    idle    │───────────────┘
          └─────┬──────┘
                │ auto-sleep
                ▼
          ┌────────────┐
          │ suspended  │
          └─────┬──────┘
                │ request
                ▼
             warming

Any state ──failure──► error
```

---

## 5. Valid State Transitions

| From       | To        | Trigger                  |
| ---------- | --------- | ------------------------ |
| registered | installed | Asset installation       |
| installed  | warming   | Manual start / auto-wake |
| warming    | running   | Startup success          |
| warming    | error     | Startup failure          |
| running    | idle      | No active requests       |
| idle       | running   | New request              |
| idle       | suspended | Auto-sleep timeout       |
| suspended  | warming   | New request              |
| running    | error     | Health check failure     |
| error      | warming   | Retry / restart          |
| error      | installed | Manual reset             |

❌ Invalid transitions MUST be rejected by the Gateway.

---

## 6. Desired State (`lifecycle.desired`)

Defined in `asset.yaml`:

```yaml
lifecycle:
  desired: running | on-demand | suspended
```

### Semantics

| Desired       | Meaning                          |
| ------------- | -------------------------------- |
| **running**   | Keep asset running               |
| **on-demand** | Auto-wake on request, auto-sleep |
| **suspended** | Never auto-start                 |

The Gateway reconciles **desired state** with **observed state**.

---

## 7. Observed Status Object (Gateway-Owned)

### 7.1 Status Schema

```yaml
status:
  state: idle | running | warming | suspended | error
  last_started_at: timestamp
  last_used_at: timestamp
  active_requests: number
  reason: string
```

### Rules

* `status` is **read-only** to users
* Only the Gateway may mutate it
* UI MUST NOT infer state independently

---

## 8. Gateway Responsibilities

The Gateway MUST:

1. Enforce valid state transitions
2. Perform auto-wake and auto-sleep
3. Update `status` atomically
4. Emit lifecycle events (future)
5. Block requests if:

   * Asset is in `error`
   * Pack limits are exceeded
   * Policy denies access

---

## 9. Hub UI Responsibilities

The UI MUST:

* Display **observed state**, not desired state
* Use consistent color semantics:

  * 🟢 running
  * 🔵 idle
  * 🟡 warming
  * ⚪ suspended
  * 🔴 error
* Show timestamps and reasons when available
* Never control runtime directly

---

## 10. Why This Model Works

This lifecycle model:

* Separates **intent vs reality**
* Supports **auto-wake / auto-sleep**
* Enables **clear observability**
* Works for **single workstation → cluster**
* Avoids Kubernetes-style complexity
* Aligns perfectly with your Assets UI

> This is an **OS-grade state machine**, not a container status mirror.

---

## 11. Summary

* Lifecycle is **Gateway-controlled**
* States are **finite and explicit**
* Transitions are **strictly enforced**
* UI is **observational, not imperative**

This document **locks Asset Status Lifecycle v1.0**.
