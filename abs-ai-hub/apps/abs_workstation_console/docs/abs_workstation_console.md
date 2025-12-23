# 📘 Engineering Specification

## App: **ABS Workstation Console**

**Type:** System App
**Owner:** ABS Platform / AI OS
**Audience:** Demo viewers, enterprise buyers, internal admins (read-only)
**Primary Goal:**
Expose **live, local workstation capability** in a way that is **visual, trustworthy, and OS-native**

---

## 1. Product Positioning (Non-Negotiable)

* This is **NOT** an admin tool
* This is **NOT** a marketing page
* This is a **system-level observability + capability console**
* Read-only, safe, always-on
* Works **offline**

> The console exists to answer one question instantly:
> **“What kind of AI machine is this, right now?”**

---

## 2. App Registration (Applications Grid)

### 2.1 App Card Metadata

```yaml
app_id: abs-workstation-console
display_name: ABS Workstation Console
class: app
pack: system
provider: abs
version: 1.0.0

badges:
  - abs_official
  - system

status: live

description: >
  Real-time system metrics, hardware overview,
  and AI workload status for this ABS workstation.

capabilities:
  - system_metrics
  - workload_observability
  - model_inventory (read_only)
  - hardware_overview
```

### 2.2 Actions

| Action  | Behavior                     |
| ------- | ---------------------------- |
| Open    | Opens main console UI        |
| Details | Shows app info + permissions |

---

## 3. High-Level Architecture

```
ABS Workstation Console (UI)
        |
        v
Hub Gateway (read-only APIs)
        |
        +-- System Metrics Collector
        +-- Core Services Registry
        +-- Model Registry
        +-- App Runtime Status
```

**Key rule:**
❌ No direct container exec
❌ No privileged system access from UI
✅ All data flows through **existing Core services**

---

## 4. UI Layout (Single-Page, Scroll Sections)

```
[ Header ]
[ Section A: Live System Metrics ]
[ Section B: Current AI Workloads ]
[ Section C: Installed Models ]
[ Section D: Explore ABS Workstations ]
```

---

## 5. Section A — Live System Metrics (WOW FACTOR)

### 5.1 Data Model

```ts
SystemMetrics {
  timestamp: ISO8601
  gpu: {
    model: string
    utilization_pct: number
    vram_used_gb: number
    vram_total_gb: number
  }
  cpu: {
    utilization_pct: number
  }
  memory: {
    used_gb: number
    total_gb: number
  }
  disk?: {
    read_mb_s: number
    write_mb_s: number
  }
  uptime_seconds: number
}
```

### 5.2 API

```
GET /system/metrics
```

* Poll every **2s**
* Cached for **1s**
* Local only

### 5.3 UI Requirements

* Large tiles
* High contrast
* Slow animated updates (no jitter)
* GPU tiles visually dominant

### 5.4 CES Script (UX Copy)

> “Everything you’re seeing is running locally on this workstation, right now.”

(This line should be **hard-coded** into CES mode.)

---

## 6. Section B — Current AI Workloads

### 6.1 Purpose

Visually connect:
**Apps → Models → Hardware**

### 6.2 Data Model

```ts
RunningWorkload {
  app_id: string
  app_name: string
  workload_type: "llm_inference" | "rag" | "embedding" | "model_management"
  status: "running" | "idle"
  associated_models?: string[]
}
```

### 6.3 API

```
GET /workloads/active
```

Source:

* App runtime registry
* Gateway routing table

### 6.4 UI Rules

* Only show **active or recently active** apps
* No start/stop controls
* Status = indicator dot + label

Example display:

```
Onyx AI Assistant
→ LLM Inference

Contract Reviewer v2
→ RAG + Embeddings
```

---

## 7. Section C — Installed Models (Read-Only)

### 7.1 Scope

This is **NOT** a model management UI.

* No delete
* No pull
* No config

Purpose: **Capability proof**

### 7.2 Data Model

```ts
InstalledModel {
  model_id: string
  display_name: string
  type: "llm" | "image" | "embedding"
  size_gb?: number
  locality: "local"
  serving_status: "ready" | "idle"
}
```

### 7.3 API

```
GET /models/installed?scope=summary
```

### 7.4 Badges (Hard-coded semantics)

* Local
* No Cloud
* Enterprise Ready

(These are **trust badges**, not status flags.)

---

## 8. Section D — Explore ABS Workstations (Soft Marketing)

### 8.1 Design Intent

* This is the **only outward-facing section**
* No iframe
* No auto-redirect
* Optional click-out

### 8.2 Data Model (Static JSON)

```ts
WorkstationSKU {
  sku_id: string
  tier: "entry" | "creator" | "enterprise"
  gpu: string
  ram: string
  target_use_case: string
  highlight?: boolean
  cta_url: string
}
```

### 8.3 Behavior

* Highlight current workstation
* CTA opens **new tab** to absworkstation.com
* Optional UTM for CES

---

## 9. Permissions & Security

### 9.1 Permissions

```yaml
permissions:
  - system.metrics.read
  - workloads.read
  - models.read_summary
```

### 9.2 Security Rules

* Read-only
* No mutation APIs
* No container access
* Safe for booth demo

---

## 10. CES Demo Mode (Optional Flag)

### 10.1 Config

```env
CES_MODE=true
```

### 10.2 Effects

* Larger metric fonts
* Orange accent for GPU tiles
* CES script visible
* Disable Details → Permissions view

---

## 11. Failure & Fallback Behavior

| Scenario             | Behavior                      |
| -------------------- | ----------------------------- |
| Metrics unavailable  | Show “Last updated Xs ago”    |
| App registry empty   | Show “No active workloads”    |
| Model registry error | Show cached snapshot          |
| Network down         | No visible error (local only) |

---

## 12. Non-Goals (Explicit)

❌ Hardware control
❌ Overclocking
❌ App lifecycle management
❌ Model ops
❌ Cloud connectivity

This is **observability, not control**.

---

## 13. Why This Fits Your Platform Perfectly

* Matches your **App mental model**
* Reuses **Core services**
* Demonstrates **local AI superiority**
* Scales beyond CES
* Becomes a permanent **system pillar**

This is a **flagship system app**, not a demo gimmick.
