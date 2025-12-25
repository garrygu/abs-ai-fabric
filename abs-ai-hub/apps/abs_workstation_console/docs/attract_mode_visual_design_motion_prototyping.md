# Visual Design & Motion Prototyping

## Attract Mode — Motion-First Design Package

**Version:** v1.1  
**Status:** Execution-Ready  
**Audience:** Motion Design, UI Engineering, Product  
**Objective:** Lock motion language and visual energy *before* implementation

---

## 1. Purpose

This phase defines **how the system feels in motion**.

It exists to:

- Eliminate ambiguity around "cool / dazzling"
- Prevent engineering guesswork
- Ensure premium, cinematic presence
- Enable efficient WebGPU implementation

This phase **does not** aim to finalize UI pixels or shaders.

---

## 2. Scope of Prototyping

### In Scope

- Motion behavior
- Timing and pacing
- Weight and scale
- Energy progression
- Scene-to-scene rhythm

### Out of Scope

- Final typography
- Brand color tuning
- Exact particle counts
- Performance optimization
- Backend interaction

---

## 3. Core Motion Language

These rules apply to **all scenes**.

### Motion Personality

- **Heavy, deliberate**
- **Non-repetitive**
- **Computed, not animated**
- **Calm by default, powerful under load**

### Forbidden Motion Styles

- Elastic / bouncy easing
- Fast looping cycles
- Synchronized movement
- Game-like feedback
- Overly reactive UI motion

---

## 4. Deliverables

### Output Formats

- **Clips:** MP4 (preferred) + optional GIF previews
- **Charts/curves:** PNG/PDF or slide deck (one page per scene)

---

### 4.1 Motion Reference Clips

#### Global Visual Primitives (reused across scenes)

| # | Element | Duration | Description | Purpose |
|---|---------|----------|-------------|---------|
| 1 | **GPU Ring — Calm** | 8–10s loop | Slow rotation + micro-jitter (non-periodic), minimal glow | "expensive, stable, alive" |
| 2 | **GPU Ring — Surge** | 8–10s sequence | Rotation ramps + glow increases, ends with lock-in flash then calm | "controlled power surge" |
| 3 | **Particle Field — Fabric** | 8–10s loop | Multi-depth layers (near/mid/far), asynchronous drift | "internal energy, not distraction" |
| 4 | **Particle Field — Collapse** | 6–9s sequence | Gradual inward drift → convergence near peak → release | "system focus + load convergence" |
| 5 | **Model Cards — Heavy Float** | 8–10s loop | Slight vertical drift + subtle tilt/parallax, RUNNING vs READY states | "infrastructure objects, not UI widgets" |
| 6 | **Post FX Bounds** | 5–8s A/B | Show "acceptable bloom" vs "too much bloom" | prevent readability loss |

#### Scene Hero Moments (one per scene, match scene duration)

| Scene | Duration | Focus |
|-------|----------|-------|
| **Scene A** | 9s | Ring + metrics rail, stable + live |
| **Scene B** | 11s | Cards + status badges, Capacity Badge placement (static, calm) |
| **Scene C** | 9s | Progress + ring accel + particle collapse + lock-in + calm |
| **Scene D** | 7s | Typography dominance + brief cloud dissolve |
| **Scene E** | 7s | Gentle magnetic button + cursor ripple (subtle) |

> **Acceptance bar:** Someone watching muted for 5 seconds should think: "This is real, premium, and powerful."

---

### 4.2 Scene Timing Charts

One chart per scene showing phases over time (3–5 labeled phases).

#### Scene A (9s) — "Calm Authority"

- 0–1s: Fade-in / settle
- 1–8s: Stable drift
- 8–9s: Fade-out / transition

#### Scene B (11s) — "Capacity Without Stress"

- 0–2s: Grid reveals / settle
- 2–8s: Slow independent drift + RUNNING subtle energy
- 8–11s: Right panel expansion + settle

#### Scene C (9s) — "Controlled Surge"

- 0–2s: Calm baseline
- 2–6s: Ramp (acceleration + progress)
- 6–7.5s: Peak + lock-in moment
- 7.5–9s: Release + calm completion

#### Scene D (7s) — "Clarity"

- 0–1s: Statement 1 enters
- 1–4s: Statement rotation
- 4–6s: "ZERO CLOUD" + cloud dissolve
- 6–7s: Fade out

#### Scene E (7s) — "Invitation"

- 0–2s: Text line 1–2 reveal
- 2–5s: Gentle button magnetism
- 5–7s: Cursor ripple hint + fade out

> **Acceptance bar:** Scenes feel cinematic, not rushed; Scene C is the only "high energy" spike.

---

### 4.3 Visual Intensity Curves

Define a normalized **visualIntensity(t)** curve for each scene: **0.0–1.0**.  
This becomes the engineering control input for glow, particles, ring speed, etc.

| Scene | Intensity Curve | Notes |
|-------|-----------------|-------|
| **A** | `0.20 → 0.28 → 0.22` | Low and steady (baseline) |
| **B** | `0.30 → 0.45 → 0.35` | Medium, gentle variance; RUNNING cards +0.10 local bump |
| **C** | `0.25 → 0.60 → 1.00 → 0.35` | **Only scene reaching 1.0** — short peak |
| **D** | `0.20 → 0.30 → 0.55 → 0.20` | Low; small spike during cloud dissolve |
| **E** | `0.18 → 0.28 → 0.22` | Low, gentle, inviting |

#### What Intensity May Drive

- Particle density
- Ring rotation speed (nonlinear scale)
- Glow/bloom (capped)
- Background fabric movement

#### What Intensity Must NOT Drive

- Text motion (must remain minimal)
- Layout changes
- Capacity badge behavior (static)

> **Acceptance bar:** Only Scene C reaches ~1.0; all others stay below ~0.6.

---

## 5. Scene-Specific Motion Intent

| Scene | Intent | Viewer Should Think |
|-------|--------|---------------------|
| **A — Hero Status** | Calm authority | "This system is awake and stable." |
| **B — Power Wall** | Capacity without stress | "This system has room to spare." |
| **C — Live Surge** | Controlled power | "That was real — and it's under control." |
| **D — Platform Message** | Clarity, not spectacle | "I understand the difference." |
| **E — Invitation** | Invitation, not hype | "I'm welcome to try this." |

---

## 6. Dazzle Boundaries

### Allowed to Scale

- Particle density
- Glow intensity
- Motion speed ranges
- Depth layering

### Must Remain Subtle

- Text motion
- UI layout changes
- Badge behavior
- Scene order

> If something competes with **content clarity**, it's too much.

---

## 7. Package Organization

```
motion_prototyping/
  clips/
    global/
      ring_calm.mp4
      ring_surge.mp4
      particles_fabric.mp4
      particles_collapse.mp4
      cards_heavyfloat.mp4
      postfx_bloom_bounds.mp4
    scenes/
      sceneA_hero.mp4
      sceneB_powerwall.mp4
      sceneC_surge.mp4
      sceneD_message.mp4
      sceneE_invite.mp4
  charts/
    sceneA_timing.png
    sceneB_timing.png
    sceneC_timing.png
    sceneD_timing.png
    sceneE_timing.png
  curves/
    sceneA_intensity.png
    sceneB_intensity.png
    sceneC_intensity.png
    sceneD_intensity.png
    sceneE_intensity.png
  README.md
```

---

## 8. Timeline

| Phase | Duration |
|-------|----------|
| Motion exploration | 1–2 days |
| Scene boards | 1–2 days |
| Refinement | 1 day |
| Final sign-off | 0.5 day |

**Total:** ~5 days

---

## 9. Tooling (Flexible)

Designers may use:

- After Effects
- Blender
- TouchDesigner
- Unreal / Unity (offline)
- Three.js sandbox

**Output requirement** matters more than tool choice.

---

## 10. Review & Sign-Off

Motion prototypes are approved if:

- [ ] Product says: "Yes, this feels right"
- [ ] Engineering says: "We know how to build this"
- [ ] Sales says: "This would stop me walking past"
- [ ] Clips feel premium and "expensive"
- [ ] Timing charts match desired pacing
- [ ] Intensity curves are consistent across scenes
- [ ] Scene C is the only true peak
- [ ] Badge in Scene B stays calm and subordinate
- [ ] No one asks: "What does dazzling mean?"

---

## 11. Output Checklist

- [ ] GPU ring motion clips (calm + surge)
- [ ] Particle field motion clips (fabric + collapse)
- [ ] Model card motion clip
- [ ] Post FX bloom bounds clip
- [ ] 5 scene hero moment clips
- [ ] 5 scene timing charts
- [ ] 5 scene intensity curves
- [ ] Written motion intent summary (README.md)

---

## Final Principle

> **If the motion feels expensive, the workstation feels powerful.**  
> Specs only confirm what motion already proved.
