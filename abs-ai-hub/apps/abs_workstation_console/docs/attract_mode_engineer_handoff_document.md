# Attract Mode — Engineer Handoff Document
## Motion → Implementation Contract (WebGPU + Control Plane)

**Version:** v1.0  
**Status:** Engineering Kickoff (Authoritative)  
**Audience:** UI/WebGPU engineers, Backend/Control Plane engineers, QA/Ops  
**Owner:** Product/Design (intent) + Engineering (implementation)  
**Purpose:** Preserve the approved experience while enabling fast, correct implementation.

---

## 0. One-Sentence Goal

Deliver a **cinematic, premium Attract Mode** that showcases local AI workstation capability through **motion, liveness, and restraint**, while remaining **truthful, safe, and unattended-stable**.

---

## 1. Source of Truth (Priority Order)

If anything conflicts, resolve in this order:

1) **Technical Requirements & Control Specification** *(safety, truth, control gating)*  
2) **UI & Visual Experience Specification** *(what must appear, hierarchy, non-goals)*  
3) **Motion Reference Clips** *(how it should feel)*  
4) **Scene Timing Charts** *(pacing)*  
5) **Visual Intensity Curves** *(single control input over time)*  
6) Business Narrative *(messaging intent & governance, e.g., Scene B badge wording)*

---

## 2. Non-Negotiable Invariants

### Experience / UX
- Attract Mode must **never freeze** or show raw errors.
- Scene order is **A → B → C → D → E → loop**, no deviations.
- Text is **minimal motion** (no intensity-driven text animation).
- Scene C is the **only** high-energy spike.

### Architecture
- UI **never** triggers backend actions directly.
- Scene Controller is **stateless** and drives scenes via timeline + telemetry snapshots.
- Control Plane is the **only authority** for Scene C actions (LIVE/SHOWCASE).

### Truthfulness
- Telemetry displayed/used must be **real** (or gracefully cached).
- Any Scene C backend action must be **real** when enabled, and **abortable**.

---

## 3. Deliverables Engineers Must Produce

### UI/WebGPU
- Scene renderers (A–E)
- Shared renderer primitives:
  - GPU ring
  - Particle fabric
  - Model cards
  - Post-process (bloom/blur)
- Scene Controller integration:
  - scene phase lifecycle events
  - visualIntensity input mapping
- Graceful degradation logic (telemetry drop, backend abort)

### Backend/Control Plane
- Telemetry service contract + smoothing recommendations
- Scene C control endpoints:
  - request → approve/downgrade/reject
  - action progress
  - abort/downgrade
- Safety gates (thermal, VRAM pressure, timeouts)

### Ops/QA
- Safe defaults:
  - AUTO mode by default
  - SHOWCASE requires manual enable
- Runbook + reset paths
- Stress test suite (telemetry loss, action abort, long-run stability)

---

## 4. Core Implementation Model (Engineers Must Follow)

### 4.1 Visual Control Variable (Single Control Input)

All visuals are driven by a single normalized variable:

```ts
visualIntensity: number // 0.0 ~ 1.0
````

**Definition:** A scene-specific value over time (from intensity curves) optionally modulated by telemetry hints.

**Rule:** visualIntensity may scale visuals but must not change layout or messaging.

---

### 4.2 What visualIntensity MAY drive

| Element                    | Allowed behavior       |
| -------------------------- | ---------------------- |
| Particle density           | scale up/down          |
| Particle velocity          | mild scaling           |
| GPU ring rotation          | non-linear scaling     |
| Glow/bloom                 | scaling with hard caps |
| Background fabric activity | mild scaling           |
| Scene C surge emphasis     | scaling allowed        |

### 4.3 What visualIntensity MUST NOT drive

| Element              | Forbidden behavior          |
| -------------------- | --------------------------- |
| Text motion          | no intensity-based movement |
| Scene order/duration | fixed                       |
| Layout positions     | fixed                       |
| Capacity badge       | static, calm                |
| New elements         | never introduce             |

---

## 5. Scene-by-Scene Engineering Contract

### Scene A — Hero System Status (9s)

**Intent:** Calm authority, “system is awake”.

* Intensity curve: ~0.20–0.28 steady
* GPU ring: slow rotation + micro-jitter (non-periodic)
* Particles: lowest density, calm drift
* Telemetry: read-only (util, VRAM, RAM, uptime)
* Failure behavior: freeze last good telemetry; gently reduce intensity (do not show errors)

**Must not:** show model names, use cases, or interactivity cues.

---

### Scene B — Installed Models Power Wall (11s)

**Intent:** Capacity and headroom without stress.

* Intensity curve: ~0.30–0.45 mid
* Cards: heavy float (no synchronized bobbing)
* RUNNING vs READY:

  * RUNNING: slight energy bump (local only), cap at +0.10 intensity equivalent — visually this means brighter border glow and ~20% faster nearby particle emission
  * READY: calm
* **Capacity Indicator Badge:** must appear, calm and static

**Governance Note:** Badge wording options and interpretation are defined in the Business Narrative; do not alter copy without product approval.

**Must not:** imply “always running dual 70B”, show numeric spec tables, or overcrowd grid.

---

### Scene C — Live Load Surge (9s)

**Intent:** Controlled power, real responsiveness.

* Intensity curve: `0.25 → 0.60 → 1.00 → 0.35`
* The only scene allowed to peak near 1.0
* Visual phases:

  * 0–2s calm baseline
  * 2–6s ramp (accel + progress)
  * 6–7.5s peak + lock-in (brief, <2s)
  * 7.5–9s release to calm

**Visual variability:** intensity may modulate based on telemetry/state, but structure must not change.

**Backend coupling rules:**

* Scene C may request actions, but rendering must never depend on action success.
* Modes (AUTO/LIVE/SHOWCASE) are controlled by Control Plane:

  * AUTO: telemetry only
  * LIVE: bounded warm-up/inference (no 70B cold load)
  * SHOWCASE: manual enable + safety gates + abortable

**Abort behavior:** always complete scene visually (calm finish), no error text.

---

### Scene D — Platform Message (7s)

**Intent:** Clarity, minimal spectacle.

* Intensity curve: mostly low; small spike during cloud dissolve (~0.55 max)
* Typography dominates; motion is subtle
* Cloud dissolve is brief and abstract

**Must not:** add diagrams, icons, or explanatory paragraphs.

---

### Scene E — Gentle Invitation (7s)

**Intent:** Invite engagement, not hype.

* Intensity curve: low (0.18–0.28)
* Magnetic button motion: subtle only
* Cursor ripple: localized and soft

**Must not:** aggressive CTA, countdown timers, salesy language.

---

## 6. Timing Authority (Engineers Must Respect)

Scene durations are fixed:

| Scene | Duration |
|-------|----------|
| A | 9s |
| B | 11s |
| C | 9s |
| D | 7s |
| E | 7s |
| **Total Loop** | **~43s** |

Scene Timing Charts define phases; do not compress/extend without Product approval.

---

## 7. Degradation & Performance Strategy

### Performance targets

* Maintain stable frame pacing (goal: 60 FPS or locked target)
* If performance drops, degrade in this order:

1. Reduce post-process cost (bloom blur iterations)
2. Reduce particle density
3. Reduce particle velocity variance
4. Reduce secondary glow layers
5. Preserve hero elements (ring + cards) as long as possible

**Never degrade:**

* Text readability
* Scene timing/structure
* Scene transitions

---

## 8. Telemetry & Smoothing Requirements (UI Side)

UI should not render raw telemetry directly.

* Apply smoothing / interpolation to counters and utilization
* Clamp unrealistic jumps
* If telemetry missing:

  * hold last good values
  * gradually reduce intensity
  * never show “N/A” or errors publicly

Telemetry update expectation: ≥ 5 Hz, but UI must tolerate slower.

---

## 9. Control Plane Integration Contract (Engineering Checklist)

UI/Scene Controller integration points:

| Function | Endpoint | Method |
|----------|----------|--------|
| `getTelemetrySnapshot()` | `/v1/attract/telemetry` | GET |
| `requestSceneCAction(intent)` | `/v1/attract/sceneC/request` | POST |
| `getSceneCStatus()` | `/v1/attract/sceneC/status` | GET |
| `enableShowcaseMode()` | `/v1/attract/sceneC/showcase/enable` | POST |
| `resetSceneC()` | `/v1/attract/sceneC/reset` | POST |

> See [attract.py](file:///c:/ABS/core/gateway/routers/attract.py) for implementation.

**UI never calls runtime directly.**

---

## 10. Acceptance Criteria (Definition of Done)

### Visual

* Feels consistent with motion reference clips (by feel, not frame-match)
* Timing matches timing charts
* Intensity follows curves; only Scene C peaks

### Reliability

* Runs unattended for 8+ hours
* Survives telemetry dropout without visible errors
* Scene C aborts gracefully without UI failure
* Always returns to Scene A loop

### Governance

* Scene B capacity badge implemented as specified and calm
* No unapproved messaging or new UI elements introduced

---

## 11. Open Decisions (Engineers May Decide)

Engineers are free to choose:

* WebGPU implementation details
* Internal file/module organization
* Exact easing curves (must match feel)
* Exact particle counts (subject to performance)
* Post-process technique (must stay within bloom bounds)

Engineers must not decide:

* Scene order
* Messaging
* Whether backend actions are allowed (Control Plane owns this)
* Text motion style

---

## 12. Handoff Package Checklist (Links to Attach)

Attach these items when publishing this doc:

* [ ] Motion reference clips (MP4/GIF)
* [ ] Scene timing charts (A–E)
* [ ] Visual intensity curves (A–E)
* [ ] [UI & Visual Experience Spec](file:///c:/ABS/abs-ai-hub/apps/abs_workstation_console/docs/attract_mode_ui_visual_experience_spec.md)
* [ ] [Technical Requirements & Control Spec](file:///c:/ABS/abs-ai-hub/apps/abs_workstation_console/docs/attract_mode_technical_requirements_control_specification.md)
* [ ] [Architecture diagram + JSON contracts](file:///c:/ABS/abs-ai-hub/apps/abs_workstation_console/docs/attract_mode_tech_architecture_interface_list.md)

---

## 13. Final Reminder

> **Attract Mode is a live system performance.**
> Build for truth, stability, and cinematic confidence—then tune for dazzle on real hardware.