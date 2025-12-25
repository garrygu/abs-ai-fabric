# Attract Mode — Technical Requirements & Control Specification
## System Behavior, Backend Control, and Reliability Guarantees

**Version:** v1.0  
**Status:** Engineering & Operations Alignment Draft  
**Audience:** Engineering, Platform, Ops, QA, Product  
**Depends On:**  
- Attract Mode Showcase Narrative (Business Requirements)  
- Attract Mode — UI & Visual Experience Specification  

**Out of Scope:**  
- Rendering pipelines and shader code  
- UI layout and motion design (covered elsewhere)  
- Hardware driver optimization  

---

## 1. Purpose

This document defines **how Attract Mode behaves technically** in order to:

- Faithfully implement the approved business narrative
- Respect the locked UI & visual intent
- Ensure operational safety and reliability
- Prevent demo failures under real-world conditions
- Provide clear control boundaries for engineering and ops

This specification is the **single source of truth** for backend behavior, telemetry usage, and control logic.

---

## 2. Core Design Principles (Non-Negotiable)

1. **Attract Mode must never fail visibly**
2. **No scene may depend on backend success to render**
3. **All system activity must be truthful and defensible**
4. **Heavy operations must be policy-controlled**
5. **The system must always recover autonomously**

If any requirement conflicts with these principles, the requirement is invalid.

---

## 3. High-Level System Architecture

Attract Mode consists of four cooperating layers:

1. **UI / Visual Layer**
   - Renders scenes and effects
   - Never calls backend actions directly

2. **Scene Controller**
   - Determines active scene
   - Requests telemetry snapshots
   - Emits visual intensity hints

3. **Control Plane**
   - Evaluates policy
   - Authorizes backend actions
   - Enforces safety limits

4. **Backend Services**
   - Model runtime
   - Telemetry provider
   - Resource monitor

No direct coupling between UI and backend is allowed.

---

## 4. Scene-to-Backend Behavior Mapping

### Scene A — Hero System Status

**Backend Behavior**
- Read-only telemetry access
- No backend actions triggered

**Required Telemetry**
- GPU utilization
- VRAM usage
- System RAM usage
- System uptime

**Constraints**
- Must render even if telemetry is partially unavailable
- Cached values may be used temporarily

---

### Scene B — Installed Models Power Wall

**Backend Behavior**
- Read-only model registry access
- No model loading or unloading
- No inference triggered

**Required Backend Data**
- Installed model list
- Model class (LLM / auxiliary)
- Model state:
  - RUNNING
  - READY

**Constraints**
- Dual-model display reflects supported capacity
- No assumption that multiple models are concurrently active

---

### Scene C — Live Load Surge

Scene C is the **only scene allowed to initiate backend actions**, and only via the Control Plane.

#### Scene C Operating Modes

Scene C supports **three backend behavior modes**, selected by policy and context.

---

#### Mode 1 — AUTO (Telemetry-Driven)

**Intent**
- Demonstrate liveness without altering system state

**Allowed Backend Actions**
- Telemetry reads only

**Disallowed**
- Model loads
- Inference
- Memory allocation changes

**Guarantees**
- Scene renders successfully regardless of backend load
- Visual surge may be amplified but must remain plausible

---

#### Mode 2 — LIVE (Controlled Activity)

**Intent**
- Demonstrate real backend response with bounded risk

**Allowed Backend Actions**
- Model warm-up (already installed models)
- Short, bounded inference
- Auxiliary / small model load
- Model state transitions (READY → RUNNING → IDLE)

**Explicit Limits**
- No cold loading of 70B-class models
- No concurrent multi-model loads
- Hard time and resource caps

**Guarantees**
- GPU and VRAM movement must be real
- Scene must complete even if backend action is aborted

---

#### Mode 3 — SHOWCASE (Full Load)

**Intent**
- Provide undeniable proof of local enterprise-scale capability

**Allowed Backend Actions**
- Cold load of a single large (70B-class) model
- Optional short inference after load
- VRAM lock-in during scene

**Mandatory Safeguards**
- Manual enablement only
- Pre-flight health checks:
  - GPU temperature
  - Available VRAM
  - No conflicting workloads
- Automatic abort on:
  - Timeouts
  - Thermal thresholds
  - Memory pressure

**Guarantees**
- Visuals must track real backend progress
- Any abort must degrade gracefully (no error UI)

---

### Scene D — Platform Message

**Backend Behavior**
- No backend interaction
- No telemetry required

---

### Scene E — Gentle Invitation

**Backend Behavior**
- No backend interaction
- Optional readiness checks for interactive handoff

---

## 5. Telemetry Contract

Attract Mode relies on a **stable, minimal telemetry contract**.

### Required Fields
- `gpu_utilization_pct`
- `vram_used_mb`
- `vram_total_mb`
- `system_ram_used_mb`
- `uptime_seconds`
- `model_state[]`

### Telemetry Guarantees
- Update rate: ≥5 Hz
- Latency tolerance: ≤500 ms
- Missing values must degrade gracefully

### Smoothing Rules
- UI must apply smoothing to prevent jitter
- Raw telemetry must never be shown directly

---

## 6. Control Plane Responsibilities

The Control Plane is responsible for:

- Evaluating Scene C mode eligibility
- Enforcing safety thresholds
- Preventing unauthorized heavy operations
- Coordinating aborts and recovery

The UI layer must **never** bypass the Control Plane.

---

## 7. Failure & Fallback Behavior

### Telemetry Failure
- Freeze last known good values
- Gradually decay visual intensity
- Never show error messages

### Backend Action Failure
- Abort operation
- Transition Scene C visuals to calm state
- Continue Attract Mode loop normally

### Resource Exhaustion
- Automatically downgrade Scene C mode
- Log internally
- No visible indication to user

---

## 8. Demo Reliability Requirements

Attract Mode must:

- Never freeze or hang
- Never display raw errors
- Never require manual reset
- Always return to Scene A within one loop
- Recover automatically after interruptions

---

## 9. Security & Governance

- No external network dependency required
- No cloud calls permitted in Attract Mode
- All model operations must be local
- No customer data processed

---

## 10. Configuration & Operations

### Configurable Parameters (Admin Only)
- Scene C mode enablement
- Thermal thresholds
- Timeout limits
- Telemetry polling rates

### Non-Configurable
- Scene order
- Scene messaging
- Visual narrative intent

---

## 11. Validation & Acceptance Criteria

Attract Mode is acceptable if:

- It runs unattended for extended periods
- Scene transitions are smooth and deterministic
- Scene C behaves correctly under all modes
- Backend failures do not surface visually
- Engineering, Ops, and Sales agree behavior is truthful

---

## 12. Summary Statement

> This Technical Requirements & Control Specification ensures that Attract Mode delivers a truthful, resilient, and enterprise-grade live showcase — balancing visual impact with operational safety and reliability.

---

## Appendix A: Gateway Implementation Notes

> [!NOTE]
> The following endpoints are implemented in the ABS Hub Gateway (`c:\ABS\core\gateway\routers\attract.py`).

### Base URL
```
http://localhost:8081
```

### Implemented Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/attract/telemetry` | GET | Unified telemetry snapshot (GPU, system, models) |
| `/v1/attract/sceneC/request` | POST | Request Scene C backend activity |
| `/v1/attract/sceneC/status` | GET | Current mode and action status |
| `/v1/attract/sceneC/showcase/enable` | POST | Enable SHOWCASE mode (staff only) |
| `/v1/attract/sceneC/reset` | POST | Reset to AUTO mode |

### Telemetry Response Shape
```json
{
  "timestamp": 1735852800,
  "gpu": {"utilization_pct": 42, "temperature_c": 68, "vram": {"used_mb": 41236, "total_mb": 98304}},
  "system": {"ram_used_mb": 118432, "ram_total_mb": 262144, "uptime_seconds": 93724},
  "models": [{"model_id": "deepseek-r1:70b", "class": "llm", "state": "RUNNING"}]
}
```

### Safety Thresholds (Configurable)
- **Thermal Threshold:** 80°C
- **VRAM Threshold:** 90%

