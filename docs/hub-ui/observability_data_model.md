# ABS AI Fabric — Observability Data Model (v1.0)

**Audience:** Gateway, Hub-UI, Platform, Infra
**Purpose:** Power the Observability page, admin actions, and future alerts
**Scope:** Asset-level, interface-aware, lifecycle-aware observability

---

## 1. Design Principles

### 1️⃣ Asset-First

Everything observed is tied to an **asset_id**
(No container-centric leakage)

### 2️⃣ Semantic States > Raw Metrics

“Idle”, “Warming”, “Suspended” are **first-class states**

### 3️⃣ Desired vs Actual

Observability must distinguish:

* *Desired lifecycle intent*
* *Observed runtime state*

### 4️⃣ Lightweight by Default

No heavy TSDB required for v1
Supports **in-memory + rolling snapshots**

---

## 2. Core Entities (ER Overview)

```
Asset
 ├── Asset_Runtime_State
 ├── Asset_Health_Snapshot
 ├── Asset_Usage_Snapshot
 ├── Asset_Resource_Snapshot
 ├── Asset_Lifecycle_Event
 └── Asset_Dependency_View (derived)
```

---

## 3. Asset (Reference)

Already exists from Asset Registry.
Observability **references** this entity.

```yaml
asset_id: string
class: enum        # model | service | app | tool | dataset
interface: string
interface_version: string
```

---

## 4. Asset_Runtime_State (Authoritative State)

> **One row per asset (current state)**

```yaml
asset_id: string (PK)

# Desired vs Actual
desired_state: enum
  - running
  - on-demand
  - suspended

actual_state: enum
  - registered
  - installed
  - idle
  - warming
  - running
  - suspended
  - error

state_reason: string           # human-readable explanation
state_since: timestamp

# Auto-wake context
last_used_at: timestamp|null
auto_sleep_at: timestamp|null
cold_start_expected_sec: number|null
```

### Why this matters

This is what drives:

* UI badges
* Action availability
* “Is this healthy?”

---

## 5. Asset_Health_Snapshot

> Health is **not binary**

```yaml
asset_id: string
snapshot_at: timestamp

health_status: enum
  - healthy
  - degraded
  - unhealthy

health_reason_codes: list
  - DEPENDENCY_DOWN
  - FAILED_HEALTHCHECK
  - RESOURCE_STARVATION
  - STARTUP_TIMEOUT
  - POLICY_BLOCKED

health_message: string
```

📌 Used to compute:

* “4 / 20 assets healthy”
* System DEGRADED banner

---

## 6. Asset_Usage_Snapshot

> Logical usage, not system metrics

```yaml
asset_id: string
snapshot_window_sec: number    # e.g. last 60s

request_count: number
active_consumers: number       # apps currently using it
last_consumer_asset_id: string|null

avg_latency_ms: number|null
p95_latency_ms: number|null
error_rate: number|null
```

📌 Applies to:

* Models
* Services
* Apps (request ingress)

---

## 7. Asset_Resource_Snapshot

> Physical cost footprint (optional per asset)

```yaml
asset_id: string
snapshot_at: timestamp

cpu_percent: number|null
memory_mb: number|null

gpu_used: boolean
gpu_vram_used_mb: number|null
gpu_vram_total_mb: number|null

disk_used_mb: number|null
```

📌 UI rule:

* Only show GPU metrics if `gpu_required = true`

---

## 8. Asset_Lifecycle_Event (Event Log)

> The **story of what happened**

```yaml
event_id: string (PK)
asset_id: string
event_type: enum
  - REGISTERED
  - INSTALLED
  - WARMING_STARTED
  - RUNNING
  - AUTO_SLEEP
  - SUSPENDED
  - ERROR
  - RESTARTED
  - MANUAL_OVERRIDE

event_at: timestamp
triggered_by: enum
  - system
  - auto_wake
  - admin
  - policy

event_message: string
```

📌 Used for:

* Debugging
* Audit
* “Why did this stop?”

---

## 9. Asset_Dependency_View (Derived, Read-Only)

> No physical table required (computed via registry + usage)

```yaml
asset_id: string

depends_on: list[string]       # assets this one uses
used_by: list[string]          # assets depending on this

dependency_health: enum
  - ok
  - degraded
  - blocked
```

📌 Critical for:

* Root cause analysis
* Safe stop / suspend warnings

---

## 10. System_Health_Snapshot (Top Banner)

> Aggregated view (computed)

```yaml
snapshot_at: timestamp

total_assets: number
healthy_assets: number
degraded_assets: number
unhealthy_assets: number

running_assets: number
idle_assets: number
suspended_assets: number
error_assets: number

system_status: enum
  - healthy
  - degraded
  - critical
```

---

## 11. How This Maps to Your UI (Directly)

| UI Element           | Data Source             |
| -------------------- | ----------------------- |
| System Health banner | System_Health_Snapshot  |
| Asset card status    | Asset_Runtime_State     |
| DEGRADED badge       | Asset_Health_Snapshot   |
| “Idle / Warming”     | actual_state            |
| GPU column           | Asset_Resource_Snapshot |
| Consumers count      | Asset_Usage_Snapshot    |
| Inspect → Timeline   | Asset_Lifecycle_Event   |
| Used By / Depends On | Asset_Dependency_View   |

---

## 12. Storage Strategy (v1 Recommendation)

| Data              | Storage               |
| ----------------- | --------------------- |
| Runtime state     | In-memory + persisted |
| Health snapshot   | Rolling (last N)      |
| Usage snapshot    | Rolling window        |
| Resource snapshot | Optional polling      |
| Lifecycle events  | Append-only (DB)      |

👉 **No Prometheus required** for v1
👉 Easy to integrate later

---

## 13. Why This Model Fits ABS AI Fabric

✅ Asset-native
✅ Interface-aware
✅ Auto-wake friendly
✅ UI-driven
✅ Evolvable to SaaS / cluster later

> This model makes observability a **first-class platform capability**, not an afterthought.

