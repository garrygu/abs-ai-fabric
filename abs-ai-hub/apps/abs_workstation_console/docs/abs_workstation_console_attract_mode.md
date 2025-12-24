Below is a **full, implementation-ready engineering specification** for **Showcase Mode**, written to fit **ABS AI OS**, **ABS Workstation Console**, your **Core Services architecture**, and **CES constraints**.

This is not a concept doc — this is something you can hand directly to engineering.

---

# 📘 Engineering Specification

## Feature: **Showcase Mode**

**App:** ABS Workstation Console
**Version:** v1.0
**Status:** Proposed → Ready for implementation
**Primary Use Case:** CES demo, showroom, idle workstation visualization

---

## 1. Purpose & Goals

### 1.1 Purpose

Showcase Mode is an **automatic, GPU-powered, OS-native visualization mode** that activates when the system is idle and demonstrates the **live AI and compute capabilities** of an ABS Workstation.

### 1.2 Goals

* Visually demonstrate **local AI + GPU power**
* Require **zero user interaction**
* Be **safe, non-destructive, read-only**
* Never interfere with real workloads
* Work **offline**
* Reinforce ABS brand: *powerful, reliable, high-tech*

### 1.3 Non-Goals

❌ Screensaver
❌ Marketing video player
❌ Cloud demo
❌ Stress test
❌ Hardware control or tuning

---

## 2. Activation & Exit Conditions

### 2.1 Idle Detection

Showcase Mode activates when **all** of the following are true:

```yaml
attract_mode:
  enabled: true
  idle_after_seconds: 120
```

#### Idle Definition

* No mouse movement
* No keyboard input
* No touch interaction
* No navigation events in Hub UI
* No app focus changes

Idle detection lives in the **Hub UI layer**, not Windows OS.

---

### 2.2 Exit Conditions (Immediate)

Showcase Mode **must exit instantly** on:

```yaml
exit_on:
  - mouse_move
  - keyboard_input
  - click
  - app_open
  - window_focus
```

Exit behavior:

* Fade out visuals
* Restore previous UI state
* No reloads
* No loss of context

---

## 3. GPU Safety & Resource Budgeting (CRITICAL)

### 3.1 GPU Utilization Cap

```yaml
gpu_policy:
  utilization_soft_cap_pct: 60
  utilization_hard_cap_pct: 70
```

Rules:

* Showcase Mode must **throttle or pause** if GPU usage exceeds soft cap
* Showcase Mode **must stop immediately** if hard cap is reached
* Showcase Mode **always yields** to real workloads

---

### 3.2 App Priority Rules

| Scenario                  | Behavior            |
| ------------------------- | ------------------- |
| Any app starts inference  | Pause Showcase Mode  |
| App GPU usage > threshold | Suspend visuals     |
| All apps idle again       | Resume Showcase Mode |

No contention. Ever.

---

## 4. High-Level Architecture

```
ABS Workstation Console
 └── Showcase Mode Controller
      ├── Idle Detector
      ├── Visual Scheduler
      ├── GPU Budget Monitor
      ├── Metrics Stream
      └── Exit Listener
```

All components run **locally** and reuse **existing Core services**.

---

## 5. Visual Stack (Layered)

Showcase Mode is composed of **three layers**, rendered full-screen.

---

## 6. Layer A — Live System Metrics (Always On)

### 6.1 Purpose

Continuously reinforce that:

> “This system is alive and running locally.”

### 6.2 Data Source

```http
GET /system/metrics
```

### 6.3 Displayed Metrics

* GPU Utilization (%)
* GPU VRAM Used / Total
* GPU Model (e.g., RTX Pro 6000)
* CPU Load (%)
* RAM Used / Total
* Uptime

### 6.4 UI Rules

* Large typography
* Slow animated value transitions
* No flashing
* No jitter

### 6.5 CES Overlay Text (CES_MODE only)

> **LIVE LOCAL AI**
> **RTX Pro 6000 Active**

---

## 7. Layer B — AI Visual Demonstrations (Rotating)

### 7.1 Scheduler

```yaml
visual_loop:
  rotation_interval_seconds: 45
  max_concurrent_visuals: 1
```

Only **one** visual demo runs at a time.

---

### 7.2 Visual Type 1 — Live Image Generation (Primary)

**Engine:** SDXL (local)

#### Behavior

* Predefined prompt set
* Generates images in real time
* Shows generation progress subtly
* Displays finished image, then fades

#### Prompt Rules

* Non-sensitive
* Non-violent
* Brand-safe
* Deterministic variants

Example prompts:

* “Futuristic AI workstation in a dark premium environment”
* “Abstract visualization of local AI compute”

---

### 7.3 Visual Type 2 — AI System Visualization (Secondary)

**Engine:** WebGL / Canvas

#### Visualization Concepts

* Token flows
* Model activation nodes
* App → Model → Hardware graph
* GPU memory waves

This is **conceptual**, not literal data.

Purpose:

* Feel advanced
* Feel unique to ABS
* Avoid privacy or complexity risks

---

### 7.4 Visual Type 3 — LLM Thought Stream (Optional)

**Engine:** Local LLM (low token rate)

#### Behavior

* Short, pre-approved prompts
* Token-by-token rendering
* Text fades out slowly

Example prompt:

> “Explain why local AI improves enterprise security.”

Limit:

* ≤ 1 request per cycle
* Low token count

---

## 8. Layer C — Branding & Messaging

### 8.1 Static Elements

* ABS logo (subtle)
* “Powered by ABS Workstation”
* “Local • Secure • Enterprise”

### 8.2 Rules

* No call-to-action
* No pricing
* No URLs
* No QR codes

This is **presence**, not sales.

---

## 9. Configuration & Feature Flags

### 9.1 Config Example

```yaml
attract_mode:
  enabled: true
  idle_after_seconds: 120
  gpu_utilization_cap_pct: 60
  visuals:
    image_generation: true
    system_visualization: true
    llm_stream: false
```

### 9.2 CES Mode

```env
CES_MODE=true
```

Effects:

* Larger visuals
* Orange ABS accents
* Slower transitions
* CES overlay text enabled

---

## 10. Failure Handling & Resilience

| Failure                | Behavior                   |
| ---------------------- | -------------------------- |
| Metrics unavailable    | Show “Last updated Xs ago” |
| Image generation fails | Skip visual, continue      |
| GPU overload           | Suspend visuals            |
| LLM unavailable        | Disable LLM stream         |
| Network unavailable    | No visible impact          |

Showcase Mode must **never crash the Console**.

---

## 11. Security & Privacy

* No user data
* No document access
* No prompts from user content
* No logging of generated content
* No cloud calls

Safe for public display.

---

## 12. Performance Constraints

| Resource | Limit                  |
| -------- | ---------------------- |
| GPU      | ≤ 60% sustained        |
| VRAM     | ≤ 70%                  |
| CPU      | Best-effort            |
| Disk     | No writes beyond cache |

---

## 13. Testing Checklist (Pre-CES)

* [ ] Idle detection reliable
* [ ] Immediate exit on input
* [ ] GPU throttle works
* [ ] No memory leaks (1hr run)
* [ ] Offline mode verified
* [ ] App launch interrupts Showcase Mode
* [ ] CES overlay visible

---

## 14. UX Copy (Locked)

Use only the following phrases:

* “Live Local AI”
* “RTX Pro 6000 Active”
* “No Cloud Required”
* “Enterprise-Grade Compute”

No buzzwords.

---

## 15. Why This Is Strategic

* Differentiates ABS instantly
* Turns idle time into value
* Reinforces hardware authority
* Feels engineered, not gimmicky
* Reusable beyond CES

---

## 16. Implementation Order (Suggested)

1. Idle detection
2. Metrics full-screen view
3. GPU budget enforcement
4. Visual scheduler
5. Image generation demo
6. CES mode polish

---

## Final Statement

> **Showcase Mode is a living proof of power — not a screensaver.**
> If implemented as specified, it becomes a signature ABS capability.
