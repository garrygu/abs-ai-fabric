# ABS AI Fabric – Hub UI Specification (v1.0)

**Version:** v1.0
**Status:** Engineering-ready
**Audience:** Frontend, Gateway, Platform Engineers
**Applies to:** ABS AI Hub / ABS AI Fabric UI

---

## 1. Purpose & Scope

The Hub UI is the **primary control plane UI** for ABS AI Fabric.

It enables:

* Discovery and execution of AI applications
* Asset lifecycle visibility and management
* Resource observability
* Safe self-service configuration
* Admin governance (approval, control, policy)

The UI **does not**:

* Directly control Docker
* Bypass the Gateway
* Embed infrastructure logic

All state is sourced from **Gateway APIs**.

---

## 2. User Roles (v1.0)

### 2.1 Roles Supported

| Role      | Description                                            |
| --------- | ------------------------------------------------------ |
| **Admin** | Full control of assets, policies, approvals, lifecycle |
| **User**  | Can run apps, view assets, configure allowed bindings  |

> **Note:** No fine-grained RBAC in v1.0. UI must be role-aware but simple.

---

## 3. Global Layout & Navigation

### 3.1 Top Navigation (Persistent)

```
[ Workspace ] [ Apps ] [ Assets ] [ Observability ] [ Admin ]
                                                [ User ▼ ]
```

Visibility rules:

* `Admin` tab visible to admins only
* Other tabs visible to all users

---

### 3.2 Workspace Context

* Single workspace in v1.0
* UI must assume future multi-workspace support
* All API calls are workspace-scoped (implicit for now)

---

## 4. Apps UI

### 4.1 Apps Landing Page

**Route:** `/apps`

**Tabs:**

* **Installed Apps**
* **App Store**

---

### 4.2 Installed Apps View

Each app is rendered as a **card**.

**Required fields:**

* App name
* Description
* Status: `online | offline | error`
* Dependency summary (chips)
* Primary action: **Open App**

**Optional metadata (footer row):**

* Last used timestamp
* Bound assets count
* Resource hint (GPU / CPU)

---

### 4.3 App Store View

Shows apps **not yet installed**.

Each card includes:

* App name + description
* Required interfaces
* Optional assets
* Install / Request button

---

### 4.4 App Detail Page

**Route:** `/apps/{app_id}`

**Sections:**

1. Overview
2. Assets & Bindings
3. Activity
4. Configuration (if supported)
5. Data (read-only inspection)

---

#### 4.4.1 Assets & Bindings Section (Critical)

For each asset dependency:

| Field           | Behavior                   |
| --------------- | -------------------------- |
| Asset Name      | Clickable → Asset Detail   |
| Interface       | Read-only                  |
| Current Binding | Dropdown if configurable   |
| Lock State      | 🔒 if admin-locked         |
| Status          | Running / Idle / Suspended |

Rules:

* Only assets declared as configurable by app metadata can be changed
* Changes invoke Gateway validation
* UI must show impact warning (restart / warm-up)

---

## 5. Assets UI

### 5.1 Assets Landing Page

**Route:** `/assets`

**Tabs by class:**

* Models
* Services
* Tools
* Datasets
* All

---

### 5.2 Asset Table Columns (Minimum)

| Column    | Source                |
| --------- | --------------------- |
| Name      | asset.display_name    |
| Type      | asset.class           |
| Interface | asset.interface       |
| Status    | asset.lifecycle.state |
| Consumers | Derived               |
| Resource  | Derived               |
| Scope     | ownership.visibility  |

---

### 5.3 Asset Detail Page

**Route:** `/assets/{asset_id}`

#### Tabs

```
Overview | Usage | Consumers | Logs | Config | History
```

---

#### 5.3.1 Overview Tab

Displays:

* Identity (name, version, pack_id)
* Interface + version
* Description
* Lifecycle state
* Desired state
* Auto-sleep configuration
* Resource requirements (GPU, RAM, disk)

---

#### 5.3.2 Usage Tab

* Current utilization (if available)
* Requests / minute
* Warm vs cold starts
* Idle duration

---

#### 5.3.3 Consumers Tab

List of apps using this asset:

* App name
* Binding type (required / optional)
* Active usage indicator

---

#### 5.3.4 Config Tab

Editable **only if allowed**:

* Desired lifecycle state
* Auto-sleep minutes
* Max concurrency
* Allowed apps (admin only)

---

## 6. Observability UI

### 6.1 Observability Landing Page

**Route:** `/observability`

**Purpose:** System-level situational awareness

---

### 6.2 Required Widgets (v1.0)

1. **Asset Health Summary**

   * Running / Idle / Suspended / Error counts

2. **Resource Utilization**

   * GPU usage (aggregate)
   * RAM usage
   * Disk usage

3. **Top Consumers**

   * Apps by request volume
   * Assets by utilization

4. **Warnings**

   * Assets near capacity
   * Failed starts
   * Policy violations

---

## 7. Admin UI

### 7.1 Admin Landing Page

**Route:** `/admin`

Answers:

1. Is the system healthy?
2. What needs attention?
3. What is consuming resources?

---

### 7.2 Asset Requests

**Route:** `/admin/requests`

Supports:

* New asset requests
* Asset pack requests
* App install requests

Each request shows:

* Requestor
* Asset / App
* Resource impact
* Status
* Admin decision + comment

---

### 7.3 Manual Controls (Admin Only)

Per asset:

* Force start
* Force stop
* Restart
* Mark error resolved

UI must show **danger confirmation**.

---

## 8. Requests & Self-Service (User)

### 8.1 Request New Asset / App

Accessible from:

* Assets page
* Apps page

Request form includes:

* Asset / App selection
* Reason
* Intended usage

Submission creates a **pending request**.

---

## 9. App Switching UX

### 9.1 App Switcher (v1.0 Optional, v1.1 Recommended)

* Keyboard shortcut (`Ctrl+K` / `Cmd+K`)
* Recent apps
* Search by name

---

## 10. Data Inspection (Read-Only)

### 10.1 App Data Inspection

If supported by app:

* View vector count
* View document metadata
* View cache keys (summary only)

No destructive actions in v1.0.

---

## 11. UI → API Contract Rules

The UI:

* Calls **Gateway APIs only**
* Never calls Docker or services directly
* Treats Gateway as source of truth

All state must be:

* Observable
* Explainable
* Eventually consistent

---

## 12. Non-Goals (Explicit)

The UI will **not**:

* Implement scheduling logic
* Implement auto-wake logic
* Contain hard-coded asset rules
* Assume cloud or SaaS deployment

---

## 13. Versioning & Future Readiness

v1.0 is designed to support:

* Multi-workspace
* RBAC
* Asset packs marketplace
* SaaS control plane

No breaking UI assumptions are allowed.

---

## 14. Summary

This UI spec ensures that ABS AI Fabric:

* Feels like an **AI operating fabric**, not an app launcher
* Keeps **assets first-class**
* Enables **safe self-service**
* Preserves **enterprise trust and inspectability**

> The UI is a **control plane**, not a shortcut.

## 15. v1.1 Roadmap / Future Considerations

### 15.1 Real-time Updates
* **Current State (v1.0):** State is refreshed via periodic polling (every 30s).
* **Target State (v1.1):** Evaluate WebSocket or Server-Sent Events (SSE) for real-time asset status and observability.

### 15.2 Mobile Responsiveness
* **Current State (v1.0):** Desktop-first design.
* **Target State (v1.1):** Full mobile responsiveness and touch-friendly controls for on-the-go monitoring.

