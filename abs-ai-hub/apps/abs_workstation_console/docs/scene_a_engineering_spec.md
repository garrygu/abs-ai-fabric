## 1) Composition: 2-layer approach (recommended)

### Layer A — WebGPU “Visual Field” (full screen)

* 100k+ particles / flow field / bloom / subtle vignette
* A **halo ring** effect behind the HUD (shader-driven)
* Color temperature shifts by state (IDLE → LOADING → LIVE)

### Layer B — HUD Overlay (DOM or Canvas2D)

* All text + numbers + small charts
* Reason: crisp typography, easy layout, zero GPU text complexity
* WebGPU stays purely “visual energy”, HUD stays purely “information”

This also makes your CES demo *reliable* (no font atlas bugs on show day).

---

## 2) State machine (3 states) + transitions

### States

1. **IDLE_READY**

* Goal: attract + “LOCAL AI / NO CLOUD” trust
* Show: VRAM/RAM/Uptime + “READY” (not raw %)

2. **LOADING_70B**

* Goal: “process theatre”
* Show: progress ring + step labels (Pulling / Quantizing / Warming)

3. **LIVE_INFERENCE**

* Goal: prove performance
* Show: GPU Util clearly labeled + TTFT / tok/s (or your real metrics)

### Transition events

* `onUserInteract` → enter LOADING or LIVE (depending on demo flow)
* `onModelLoadStart(model)` → LOADING_70B
* `onModelLoadComplete(model)` → LIVE_INFERENCE (or IDLE_READY if not running)
* `onInferenceStart` → LIVE_INFERENCE
* `onInferenceStop` → if no activity for N seconds → IDLE_READY
* `telemetryMissing > 3s` → “DEMO_TELEMETRY” fallback (still looks alive)

---

## 3) Telemetry contract (minimal but solid)

You likely already have `/admin/system/metrics`. Map it to a normalized struct:

```ts
type Telemetry = {
  ts: number;                 // epoch ms
  gpuUtilPct: number;         // 0-100
  vramUsedGB: number;
  vramTotalGB: number;
  ramUsedGB: number;
  ramTotalGB: number;
  uptimeSec: number;

  // optional "wow" fields (if available)
  activeModel?: string;       // "Llama 70B"
  loadPhase?: "pull"|"quant"|"warm"|"ready";
  loadProgress?: number;      // 0..1
  tokPerSec?: number;
  ttftMs?: number;
  contextTokens?: number;
};
```

**Important CES trust rule:** if `vramUsedGB` is high but `gpuUtilPct` is low, the HUD must show **READY / PRELOADED** so it reads as intentional.

---

## 4) WebGPU visual mapping (what changes per state)

Think “same scene, different energy”:

### IDLE_READY

* Flow field: slow drift
* Particle speed: low
* Halo ring: breathing pulse
* Bloom: medium-low
* Accent color: cooler orange/amber (stable)

### LOADING_70B

* Flow field: tighter, more “inward” swirl
* Halo ring: becomes progress arc (GPU shader arc, or just glow that tracks `loadProgress`)
* Add subtle “scanline” pass to signal “system working”
* Bloom: higher
* Micro-glitch (very subtle) on phase change

### LIVE_INFERENCE

* Particle speed: tied to `gpuUtilPct`
* Halo ring: pulsing frequency tied to `tokPerSec` (or fallback to gpuUtil)
* Bloom: highest but clamp hard to avoid washed-out text
* Optional: light “spark burst” on each request start

---

## 5) Smoothing + clamping (prevents ugly jumps)

Use EMA smoothing for util + rates:

```ts
function ema(prev: number, next: number, alpha = 0.15) {
  return prev + alpha * (next - prev);
}
```

Clamp everything:

* util: 0–100
* tok/s: 0–(reasonable max)
* progress: 0–1

If telemetry stales:

* freeze HUD values
* slowly decay animations to IDLE cadence
* show tiny “LIVE” indicator only if updates are fresh

---

## 6) Implementation skeleton (TypeScript-ish)

```ts
type SceneState = "IDLE_READY" | "LOADING_70B" | "LIVE_INFERENCE";

class AttractModeSceneA {
  state: SceneState = "IDLE_READY";
  lastTelemetryTs = 0;

  // smoothed values
  gpuUtil = 0;
  tokPerSec = 0;
  loadProgress = 0;

  enter(next: SceneState) {
    this.state = next;
    // optional: reset timers, burst effects
  }

  onTelemetry(t: Telemetry) {
    this.lastTelemetryTs = t.ts;

    this.gpuUtil = ema(this.gpuUtil, t.gpuUtilPct);
    if (t.tokPerSec != null) this.tokPerSec = ema(this.tokPerSec, t.tokPerSec);
    if (t.loadProgress != null) this.loadProgress = ema(this.loadProgress, t.loadProgress);

    // state decisions
    if (t.loadProgress != null && t.loadProgress < 1) this.enter("LOADING_70B");
    else if (t.tokPerSec != null || t.gpuUtilPct > 20) this.enter("LIVE_INFERENCE");
    else this.enter("IDLE_READY");
  }

  tick(now: number) {
    const stale = (now - this.lastTelemetryTs) > 3000;
    if (stale) {
      // fallback: demo motion, soften toward idle
      this.enter("IDLE_READY");
    }

    // feed uniforms for WebGPU shaders
    const uniforms = {
      state: this.state,
      gpuUtil: this.gpuUtil / 100,
      tokPulse: Math.min(1, this.tokPerSec / 80),
      progress: this.loadProgress,
    };

    // render WebGPU visual field using uniforms
    // render HUD overlay with the latest telemetry + labels
  }
}
```

