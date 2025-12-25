# Attract Mode — UI & Visual Experience Specification
## Scene-by-Scene Visual Design & Motion Intent

**Version:** v1.1  
**Status:** Design & Product Alignment Draft  
**Audience:** Product, Design, Creative, Engineering Leads  
**Related Docs:**  
- Attract Mode Showcase Narrative (Business Requirements)  
- Attract Mode Technical Requirements & Control Specification (future)

**Out of Scope:**  
- Rendering pipelines  
- Shader / WebGPU implementation  
- Backend APIs and orchestration logic  

---

## 1. Purpose

This document defines **what the user sees and feels** during Attract Mode.

It translates the approved **Business Narrative** into:
- Visual hierarchy
- Motion language
- Emphasis and restraint
- Interaction affordances

This document is **authoritative for look & feel**, but intentionally **non-technical**.

---

## 2. Global Visual Language

### 2.1 Overall Tone

The Attract Mode experience must feel:

- Cinematic
- Heavy
- Confident
- Premium
- Computed (not decorative)

Avoid:
- Playful or cartoon-like visuals
- Flashy colors or gimmicks
- “Web app” or dashboard aesthetics

---

### 2.2 Color & Contrast

- Background: near-black / deep charcoal
- Accents: restrained whites and cool blues
- High contrast for distance readability
- No rainbow gradients
- No brand-color flooding

Color must imply **energy under control**, not chaos.

---

### 2.3 Motion Principles

All motion must follow these rules:

1. **Slow by default**  
   Motion should feel deliberate and weighted.

2. **Acceleration has meaning**  
   Increased speed implies increased system activity.

3. **No obvious loops**  
   Motion must feel computed and non-repeating.

4. **Subtle imperfection**  
   Micro-drift and variation reinforce realism.

---

### 2.4 Background Visual Fabric

- Persistent across all scenes
- Abstract particle / energy field
- Responds subtly to system state
- Never competes with foreground content

This layer represents **the internal energy of the system**.

---

## 3. Scene-by-Scene Specification

---

## Scene A — Hero System Status

**Duration:** ~9 seconds  

### Visual Goal
Establish **credibility, seriousness, and real-time operation** immediately.

---

### Layout & Composition

- Full-screen centered GPU ring (primary anchor)
- Left-side vertical metrics rail
- Top-right fixed badge:
  **“LIVE AI · NO CLOUD · RTX PRO 6000”**
- No buttons, no calls to action

---

### Visual Elements

**GPU Ring**
- Three-dimensional
- Slow parallax rotation
- Inner and outer structure visually distinct
- Subtle micro-jitter (non-looping)

**System Metrics**
- GPU VRAM, RAM, uptime
- Typography must feel stable and “live”
- No flashing or pulsing

**Background**
- Particle field with depth and calm motion

---

### Must NOT Appear
- Model names
- Use cases
- Explanatory text
- Interactivity hints

---

## Scene B — Installed Models Power Wall (Updated)

**Duration:** ~11 seconds  

### Visual Goal
Communicate **enterprise-scale AI capacity, flexibility, and headroom**, while clearly signaling that the configuration shown represents **supported capability**, not typical usage.

---

### Layout & Composition

- Primary focus: grid of large model cards (hero row)
- Secondary focus: auto-expanding right-side information panel
- Clear negative space to avoid “maxed-out” appearance
- Composition must suggest **room to grow**

---

### Visual Elements

#### 1. Model Cards (Primary)

- Large floating tiles with subtle 3D depth
- Soft volumetric lighting
- Gravity-like presence (slight vertical drift)
- Clear model identity (e.g., 70B-class)
- No configuration or tuning details

**State Representation**
- **RUNNING**
  - Visually energized
  - Slightly brighter glow
  - Subtle motion emphasis
- **READY**
  - Calm, stable appearance
  - Clearly present but restrained

This distinction reinforces that **not all models are active simultaneously**.

---

#### 2. Capacity Indicator Badge (Mandatory)

**Purpose**  
Explicitly communicate that the dual 70B display represents **system capacity and headroom**, not typical or required usage.

**Placement**
- Near the scene header or right-side panel title
- Never overlaid on model cards
- Subordinate to primary visual elements

**Approved Badge Text (select one)**
- **Capacity Demonstration** *(preferred)*
- Enterprise Capacity
- Headroom Shown
- Max Configuration Illustrated

**Visual Treatment**
- Small, authoritative badge
- Low-contrast but legible
- Neutral tone
- Gentle fade-in only

**Explicit Prohibitions**
- No asterisks
- No footnotes
- No tooltips
- No “typical usage” or defensive language

---

#### 3. Supporting Capability Callouts

Short, declarative phrases may appear in the side panel:

- **“70B-Class Models Supported”**
- **“Enterprise-Scale Model Capacity”**
- **“Multi-Model Ready”**

These reinforce capability without prescribing usage.

---

#### 4. Flexibility & Expandability Cues

Without listing specs, the UI should subtly imply:

- Support for additional model types (embedding, vision, speech, OCR)
- Support for customer-owned / in-house models
- Hardware scalability (multi-GPU, expandable memory and storage)

Allowed cues:
- Faded secondary tiles or silhouettes
- Phrases such as:
  - **“Additional models supported as needed”**
  - **“Scales with your workload”**

---

### Motion Behavior

- Model cards drift subtly and asynchronously
- RUNNING models emit slightly more energy
- Capacity badge remains calm and static
- No pulsing or attention-grabbing animation on the badge

---

### Must NOT Appear
- Spec tables or numeric limits
- “Always-on” language
- Crowded grids
- Legal or disclaimer-style copy

---

## Scene C — Live Load Surge

**Duration:** ~9 seconds  

### Visual Goal
Demonstrate **real-time responsiveness** and system reaction.

---

### Layout & Composition

- Central progress indicator
- GPU ring returns as activity anchor
- Telemetry layered, not stacked

---

### Visual Elements

- Smooth progress bar (no jump cuts)
- Accelerating GPU ring rotation
- Natural upward-counting telemetry
- Particle field collapses inward with purpose

---

### Emphasis Moments

- Subtle tension build near completion
- Brief lock-in moment at finish
- Immediate visual calm afterward

---

### Must NOT Appear
- Error states
- Logs
- Benchmark data

---

## Scene D — Platform Message

**Duration:** ~7 seconds  

### Visual Goal
Deliver **clear differentiation** with confidence and restraint.

---

### Layout & Composition

- Centered typography
- One statement visible at a time

---

### Visual Elements

- Rotating statements:
  - **ONE WORKSTATION**
  - **MULTIPLE AI MINDS**
  - **ZERO CLOUD DEPENDENCY**
- Abstract cloud dissolution effect on “ZERO CLOUD”
- Supporting keywords appear sequentially:
  - **ASSET-BASED**
  - **AUTO-WAKE**
  - **GOVERNED**

---

### Must NOT Appear
- Diagrams
- Icons
- Explanatory text

---

## Scene E — Gentle Invitation to Engage

**Duration:** ~7 seconds  

### Visual Goal
Invite interaction **without pressure**.

---

### Layout & Composition

- Centered text
- Generous spacing
- Minimal visual noise

---

### Visual Elements

- Progressive text reveal:
  - **“Touch any key to explore”**
  - **“Run a 70B model live”**
  - **“Guided Tour Available”**
- Subtle magnetic button motion
- Soft cursor ripple in background fabric

---

### Must NOT Appear
- Aggressive CTAs
- Countdown timers
- Sales language

---

## 4. Scene Transitions

- Smooth crossfades or spatial continuity
- No hard cuts
- Background fabric persists across scenes

Transitions must feel like **one continuous system**, not separate screens.

---

## 5. Accessibility & Readability

- Legible from distance
- Avoid small text
- Avoid low-contrast overlays
- Designed for bright exhibition environments

---

## 6. Explicit Visual Non-Goals

The experience must never resemble:

- A website
- A game
- A benchmark tool
- A training interface

It must feel like:

> **A live, professional system visualization**

---

## 7. Approval Gate

This document must be approved by:
- Product
- Design / Creative
- Sales Enablement

Before finalizing technical implementation.

---

## 8. Summary Statement

> This UI & Visual Experience Specification defines a cinematic, restrained, and credible visual language that proves enterprise AI capability through presence and motion — not explanation.