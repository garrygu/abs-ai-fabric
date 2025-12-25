# CES Showcase — Scene A (System Pulse) — WebGPU Spec (v1.0)

## Purpose

Scene A (“System Pulse”) is the hero Attract Mode scene for CES showcasing:

- **Local-first AI** credibility (No Cloud)
- **Real capability** (70B+ model readiness + live inference)
- **High-end workstation identity** (e.g., RTX Pro 6000 96GB)
- A **visually compelling** loop that attracts attention from a distance while remaining readable and trustworthy

This scene is implemented using **WebGPU Attract Mode** for the cinematic background and a **HUD overlay** (DOM or Canvas2D) for crisp text.

---

## Goals

1. **Attract:** Strong motion language visible from 10–20 feet.
2. **Explain:** In 10 seconds, a passerby understands “Local AI / No Cloud / Big model.”
3. **Prove:** Live inference state displays real performance metrics (no fake numbers).
4. **Stay readable:** Bloom/effects never reduce HUD legibility.

---

## Non-Goals

- Full interactive app experience (handled elsewhere)
- Accurate benchmarking UI (this is a showcase scene, not a profiling tool)

---

## Architecture

### Two-layer composition (recommended)

**Layer A — WebGPU Visual Field (full screen)**
- Particles / flow field / bloom / vignette
- Halo ring visual behind HUD
- Visual energy changes per state (IDLE → LOADING → LIVE)

**Layer B — HUD Overlay (DOM or Canvas2D)**
- All text, numbers, and UI cards
- Right-side carousel cards, performance card, and optional QR

Rationale: HUD typography must stay crisp and layout-friendly. WebGPU focuses on “wow” visuals.

---

## State Machine

Scene A is a **3-state narrative**:

1. `IDLE_READY` — attract + credible standby
2. `LOADING_70B` — “process theatre” (loading/progress)
3. `LIVE_INFERENCE` — capability payoff (util + TTFT + tok/s)

### Transitions (inputs)

- `onUserInteract` → begin LOADING or LIVE (depending on demo flow)
- `onModelLoadStart(model)` → `LOADING_70B`
- `onModelLoadComplete(model)` → `LIVE_INFERENCE` (or `IDLE_READY` if not running)
- `onInferenceStart` → `LIVE_INFERENCE`
- `onInferenceStop` → inactivity timeout → `IDLE_READY`
- telemetry stale (`> 3s` no updates) → gracefully drift to `IDLE_READY` cadence and show small “DEMO/STALE” indicator

---

## Telemetry Contract (Normalized)

Telemetry is normalized to a single struct (values may be missing). **Never fabricate metrics.**

```ts
export type Telemetry = {
  ts: number;                 // epoch ms
  gpuUtilPct: number;         // 0..100
  vramUsedGB: number;
  vramTotalGB: number;
  ramUsedGB: number;
  ramTotalGB: number;
  uptimeSec: number;

  // Optional fields (if available)
  activeModel?: string;       // e.g., "Llama 70B"
  loadPhase?: "pull" | "quant" | "warm" | "ready";
  loadProgress?: number;      // 0..1
  tokPerSec?: number;         // tokens per second
  ttftMs?: number;            // time-to-first-token
  contextTokens?: number;     // current context window usage
};
````

### Trust rule (critical)

If `vramUsedGB` is high but `gpuUtilPct` is low, the HUD must explain it as **READY / PRELOADED / STANDBY**.
Avoid showing a bare `7%` in the center without a label.

---

## WebGPU Visual Design (Per State)

### Common visual primitives

* **Flow field** (noise-driven vector field)
* **Particles** (100k+ where feasible)
* **Halo ring** (center glow ring behind HUD)
* **Bloom** + **vignette** (clamped to maintain legibility)

### Uniforms (proposed)

```ts
type SceneAUniforms = {
  u_state: 0 | 1 | 2;         // 0=IDLE, 1=LOADING, 2=LIVE
  u_energy: number;           // 0..1 overall intensity
  u_flowSpeed: number;        // 0..1
  u_particleSpeed: number;    // 0..1 (or wider range)
  u_ringProgress: number;     // 0..1 (LOADING only)
  u_pulseFreq: number;        // 0..3-ish (LIVE pulse)
  u_bloom: number;            // 0..1 clamped
};
```

### IDLE_READY (u_state = 0)

**Audience feeling:** calm “system heartbeat”, premium tech ambience.

* Flow: slow drift
* Particles: slow, clean, fewer intense streaks
* Halo ring: breathing pulse (2.8–3.6s cycle)
* Bloom: medium-low

**Suggested parameters**

* `u_energy = 0.25`
* `u_flowSpeed = 0.12`
* `u_particleSpeed = 0.18`
* `u_bloom = 0.35`
* ring pulse driven by time (`sin()`)

### LOADING_70B (u_state = 1)

**Audience feeling:** “it’s working / assembling / charging up”

* Flow: inward swirl / center attraction increased
* Halo ring: progress arc (arc length = `loadProgress`)
* Subtle scanline/shimmer (light, not glitchy)
* Phase transitions: micro flash (100–150ms), very subtle

**Suggested parameters**

* `u_energy = 0.55`
* `u_flowSpeed = 0.30`
* `u_particleSpeed = 0.35`
* `u_ringProgress = loadProgress`
* `u_bloom = 0.55`
* `scanlineStrength ≈ 0.15` (if implemented)

### LIVE_INFERENCE (u_state = 2)

**Audience feeling:** “computation / electric inference”

* Particles: speed scales with `gpuUtilPct` (or tok/s)
* Halo ring: electric arc pulse frequency scales with tok/s (fallback util)
* Spark bursts: on request start (or periodic if signal unavailable)
* Bloom: highest but hard-clamped to protect HUD

**Suggested parameters**

* `u_energy = 0.80`
* `u_flowSpeed = 0.45`
* `u_particleSpeed = 0.55 + 0.60*(utilNormalized)`
* `u_pulseFreq = map(tokps, 0..80 -> 0.8..2.2)` (fallback util)
* `u_bloom = 0.65` (with clamp)

---

## HUD Layout & Content

HUD is responsible for all readable metrics and messaging.

### Top Hero Status Bar (CES memory hook)

* `LOCAL AI` | `NO CLOUD` | `RTX PRO 6000 · 96GB`
* Add small state dot:

  * `● READY` / `● LOADING` / `● LIVE`
* If telemetry stale: show `● DEMO` or `● STALE`

### Left Metrics Block (always visible)

* GPU VRAM: `82 / 96 GB`
* RAM: `17 / 128 GB`
* Uptime: `00:54:27`

### Center Ring Label (must be self-explanatory)

* IDLE: show `READY` or `LOCAL AI`
* LOADING: show `LOADING 70B`
* LIVE: show `GPU 72%` (label required)

### Right Panel

#### IDLE: Carousel Cards (8s rotation)

Rotate 3–5 cards:

1. `No Cloud · 0 data leaves device`
2. `70B Ready · 96GB VRAM`
3. `Apps: Chat · RAG · Vision`
4. `One-click Live Demo`

Animation: fade in 250ms → hold 7s → fade out 250ms

#### LOADING: Phase Card (fixed)

* `Pulling weights…` / `Quantizing…` / `Warming up…`
* Optional subtext: `Preparing 70B for instant inference`

#### LIVE: Performance Card (fixed)

Show only metrics that are real/available:

* `Model: Llama 70B`
* `TTFT: 0.8s` (if available)
* `Throughput: 38 tok/s` (if available)
* `Context: 128k` (if available)

If unavailable, hide those lines rather than showing placeholders.

### Optional CTA/QR (bottom-right)

* QR + label: `Scan to run 70B demo`
* Must not overpower the hero bar.

---

## “CES Wow” Enhancements (Explicit)

These are the 6 enhancements, mapped to implementation layers:

1. **“Running:” headline** (HUD)

   * `Running: <model> · <tok/s> · TTFT <ms>`

2. **Right-side carousel** (HUD)

   * Rotating story cards in IDLE; fixed cards in LOADING/LIVE

3. **Ring as narrative** (WebGPU)

   * Pulse → progress arc → electric arc

4. **Hero status bar** (HUD)

   * `LOCAL AI · NO CLOUD · RTX PRO 6000`

5. **Experience metrics** (HUD)

   * TTFT / tok/s / context (only if real)

6. **Actionable CTA/QR** (HUD)

   * Scan to run demo

---

## Smoothing, Clamping, and Telemetry Freshness

### EMA smoothing

Apply EMA to reduce jitter:

* gpu util
* tok/s
* load progress

```ts
function ema(prev: number, next: number, alpha = 0.15) {
  return prev + alpha * (next - prev);
}
```

### Clamping

* util: 0..100
* progress: 0..1
* bloom: hard clamp to preserve readability

### Stale telemetry behavior

If `now - telemetry.ts > 3000ms`:

* HUD shows `● STALE` or `● DEMO`
* WebGPU cadence eases back toward IDLE visuals
* Do not freeze everything completely (screen should remain “alive”)

---

## Implementation Tasks (Jira-ready)

1. **SceneAController**

* State machine + telemetry normalization
* Outputs `SceneAUniforms`

2. **HaloRing shader module**

* 3 modes: pulse / progress arc / electric arc
* Optional spark burst emitter

3. **HUD overlay component**

* Hero bar, left metrics, right carousel/perf cards, optional QR

4. **Telemetry freshness layer**

* stale detection + graceful fallback

---

## Acceptance Criteria

* From 15 feet away, a viewer can read:

  * `LOCAL AI` and `NO CLOUD`
  * GPU VRAM and center state text
* In IDLE, no ambiguous center value (no bare “7%” without “GPU” label)
* LOADING clearly shows progress + phase
* LIVE clearly shows `GPU xx%` plus at least one performance metric when available
* HUD remains readable under all bloom/particle configurations

---

## Open Questions (track as TODO)

* Primary telemetry endpoint and update cadence (target: 5–10Hz if possible)
* Availability of TTFT/tok/s/context metrics in current runtime
* HUD implementation choice: DOM (Vue overlay) vs Canvas2D text rendering
