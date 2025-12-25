## Attract Mode — 1-Page Technical Architecture

![Image](https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API/basic-webgpu-stack.png)

![Image](https://estuary.dev/static/cf42ddce7617b379fb88ae111b08e69b/2e227/02_Event_Driven_Architecture_Examples_Unilever_0133bb992b.png)

![Image](https://www.tigera.io/app/uploads/2024/07/Service-Mesh-Architecture.png)

### High-Level Flow (Authoritative)

```
┌────────────────────────────────────────────┐
│              Attract UI (WebGPU)            │
│  - Scene renderers (A–E)                    │
│  - Particle / ring / post-process shaders   │
│  - Visual state + intensity only            │
│                                            │
│  ❌ NO backend actions                      │
│  ❌ NO business logic                       │
└───────────────┬────────────────────────────┘
                │  (read-only, event-driven)
                ▼
┌────────────────────────────────────────────┐
│              Scene Controller               │
│  - Scene timeline & transitions             │
│  - Scene lifecycle (enter / idle / exit)   │
│  - Requests telemetry snapshots             │
│  - Emits visual-intensity hints             │
│                                            │
│  ❌ NO safety decisions                     │
│  ❌ NO heavy ops                            │
└───────────────┬────────────────────────────┘
                │  (policy-gated requests)
                ▼
┌────────────────────────────────────────────┐
│               Control Plane                 │
│  - Scene C mode enforcement                 │
│  - Safety & thermal gates                   │
│  - Authorization for backend actions        │
│  - Abort / downgrade logic                  │
│                                            │
│  ✅ Single authority for risk               │
└───────────────┬────────────────────────────┘
                │  (internal RPC / HTTP)
                ▼
┌────────────────────────────────────────────┐
│              Backend Services               │
│  - Telemetry Service                        │
│  - Model Runtime Adapter                    │
│  - Resource / Health Monitor                │
│                                            │
│  ❌ No UI awareness                         │
└────────────────────────────────────────────┘
```

### Architectural Invariants (Non-Negotiable)

* UI **never** calls backend services directly
* Scene Controller is **stateless**
* Control Plane is the **only** component allowed to trigger load / inference
* Backend failures **never** surface to UI
* All interfaces are **read-only by default**

---

## Interface List & JSON Contracts

Below are the **minimum required contracts**.
They are intentionally small, stable, and demo-safe.

> [!NOTE]
> These contracts are implemented at `http://localhost:8081` via the ABS Hub Gateway.
> See [attract.py](file:///c:/ABS/core/gateway/routers/attract.py) for implementation.

---

## 1️⃣ Telemetry Service API

*(Backend → Control Plane → Scene Controller)*

### `GET /v1/attract/telemetry`

```json
{
  "timestamp": 1735852800,
  "gpu": {
    "utilization_pct": 42,
    "temperature_c": 68,
    "vram": {
      "used_mb": 41236,
      "total_mb": 98304
    }
  },
  "system": {
    "ram_used_mb": 118432,
    "ram_total_mb": 262144,
    "uptime_seconds": 93724
  },
  "models": [
    {
      "model_id": "llama3-70b",
      "class": "llm",
      "state": "RUNNING"
    },
    {
      "model_id": "deepseek-r1-70b",
      "class": "llm",
      "state": "READY"
    }
  ]
}
```

**Rules**

* Update rate ≥ 5 Hz
* Missing fields allowed (UI must degrade gracefully)
* Never blocks scene rendering

---

## 2️⃣ Scene Controller → Control Plane

*(Policy-gated requests only)*

### `POST /v1/attract/sceneC/request`

```json
{
  "scene_id": "sceneC",
  "requested_intent": "LOAD_ACTIVITY",
  "visual_context": {
    "current_scene": "sceneC",
    "desired_intensity": "HIGH"
  }
}
```

**Notes**

* This is a *request*, not a command
* Control Plane may downgrade or reject silently

---

## 3️⃣ Control Plane Decision Response

*(Control Plane → Scene Controller)*

```json
{
  "approved": true,
  "mode": "LIVE",
  "constraints": {
    "max_duration_seconds": 12,
    "max_vram_mb": 65536
  },
  "reason": "Thermal and memory conditions nominal"
}
```

If rejected:

```json
{
  "approved": false,
  "mode": "AUTO",
  "reason": "GPU temperature above threshold"
}
```

---

## 4️⃣ Control Plane → Model Runtime Adapter

*(Internal, never exposed to UI)*

### `POST /runtime/action`

```json
{
  "action_id": "sceneC-warmup-001",
  "action_type": "MODEL_WARMUP",
  "model_id": "llama3-70b",
  "limits": {
    "timeout_seconds": 10,
    "max_vram_mb": 65536
  }
}
```

---

## 5️⃣ Backend Action Progress

*(Backend → Control Plane → Scene Controller)*

```json
{
  "action_id": "sceneC-warmup-001",
  "status": "IN_PROGRESS",
  "progress_pct": 73,
  "telemetry_hint": {
    "gpu_utilization_pct": 78,
    "vram_used_mb": 62112
  }
}
```

**Important**

* Progress is advisory
* UI may smooth or exaggerate visually (within spec)
* Abort signals may arrive at any time

---

## 6️⃣ Abort / Downgrade Signal

*(Control Plane → Scene Controller)*

```json
{
  "action_id": "sceneC-warmup-001",
  "status": "ABORTED",
  "fallback": "AUTO",
  "reason": "Thermal threshold reached"
}
```

UI behavior:

* Transition Scene C to calm completion
* No error text
* Continue loop

---

## 7️⃣ Scene Controller → UI (Internal Event)

```json
{
  "event": "SCENE_STATE_UPDATE",
  "scene": "sceneC",
  "phase": "LOCK_IN",
  "visual_intensity": 0.92
}
```

**Key Rule**

* UI reacts only to **visual intent**
* UI never inspects backend causes

---

## Ownership Summary

| Component        | Owns                   |
| ---------------- | ---------------------- |
| UI (WebGPU)      | Visual execution only  |
| Scene Controller | Timeline & transitions |
| Control Plane    | Safety, truth, policy  |
| Backend Services | Real system state      |
| Ops              | Thresholds & configs   |

---

## Why This Works

* **Truthful** (real telemetry, real actions)
* **Safe** (policy-gated, abortable)
* **Dazzling** (UI free to exaggerate visually)
* **Reliable** (no single point of demo failure)
* **Scalable** (future SKUs, future scenes)
