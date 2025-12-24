# GPU Metrics Integration Guide

This document describes how the ABS Workstation Console obtains and displays real-time GPU metrics from NVIDIA GPUs.

## Overview

The console displays live GPU information (model, utilization, VRAM, temperature) by querying `nvidia-smi` through a lightweight host-side proxy server.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Windows Host                              │
│  ┌──────────────┐       ┌─────────────────────┐                 │
│  │  nvidia-smi  │ ───── │ GPU Metrics Server  │                 │
│  └──────────────┘       │     (Port 8083)     │                 │
│                         └─────────────────────┘                 │
└─────────────────────────│───────────────────────────────────────┘
                          │ HTTP JSON
┌─────────────────────────│───────────────────────────────────────┐
│                    Browser Console                               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐         │
│  │   api.ts     │ → │ metricsStore │ → │ Vue UI       │         │
│  └──────────────┘   └──────────────┘   └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Why a Host-Side Proxy?

Docker containers on Windows cannot access `nvidia-smi` without complex GPU passthrough configuration. The proxy server:

1. Runs directly on the Windows host (outside Docker)
2. Executes `nvidia-smi` to get real GPU statistics  
3. Exposes data via a CORS-enabled HTTP endpoint
4. Allows the browser to fetch data directly

---

## Components

### 1. GPU Metrics Server

**Location**: `core/gateway/gpu_metrics_server.py`  
**Port**: `8083`

A lightweight Python HTTP server that queries `nvidia-smi`:

```python
result = subprocess.run(
    ["nvidia-smi", 
     "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu",
     "--format=csv,noheader,nounits"],
    capture_output=True, text=True, timeout=5
)
```

**API Endpoints**:

| Endpoint | Description |
|----------|-------------|
| `GET /gpu-metrics` | Returns GPU stats as JSON |
| `GET /health` | Health check endpoint |

**Response Format** (`GET /gpu-metrics`):

```json
{
  "timestamp": 1766521003.246,
  "gpus": [{
    "id": 0,
    "name": "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
    "utilization": 7.0,
    "memory_used_mb": 3346.0,
    "memory_total_mb": 97887.0,
    "temperature": 37.0
  }]
}
```

### 2. Console API Layer

**Location**: `abs-ai-hub/apps/abs_workstation_console/src/services/api.ts`

The `fetchSystemMetrics()` function orchestrates data fetching:

1. **First**: Fetches real GPU data from proxy (`http://127.0.0.1:8083/gpu-metrics`)
2. **Then**: Attempts to fetch CPU/memory from Gateway API (with 5s timeout)
3. **Fallback**: If Gateway fails, returns simulated CPU/memory but preserves **real GPU data**

```typescript
// Fetch real GPU data from host proxy
const gpuResponse = await fetch(`${GPU_METRICS_URL}/gpu-metrics`)
const gpuData = await gpuResponse.json()
realGpuData = gpuData.gpus[0]  // Real Blackwell GPU info

// Gateway fetch with timeout fallback
const controller = new AbortController()
setTimeout(() => controller.abort(), 5000)
const gatewayResponse = await fetch(GATEWAY_URL, { signal: controller.signal })
```

### 3. Metrics Store

**Location**: `abs-ai-hub/apps/abs_workstation_console/src/stores/metricsStore.ts`

Pinia store that polls `fetchSystemMetrics()` every 2 seconds and exposes computed properties:

| Property | Description |
|----------|-------------|
| `gpuModel` | GPU name (e.g., "NVIDIA RTX PRO 6000 Blackwell") |
| `gpuUtilization` | GPU usage percentage |
| `vramUsed` | VRAM used in GB |
| `vramTotal` | Total VRAM in GB |

---

## Starting the GPU Metrics Server

```powershell
cd c:\ABS\core\gateway
python gpu_metrics_server.py
```

**Expected Output**:
```
GPU Metrics Server running on http://0.0.0.0:8083
Endpoints: /gpu-metrics, /health
```

**Test the endpoint**:
```powershell
Invoke-RestMethod http://127.0.0.1:8083/gpu-metrics | ConvertTo-Json
```

---

## Data Flow

| Step | Component | Action |
|------|-----------|--------|
| 1 | GPU Server | Calls `nvidia-smi`, exposes JSON on port 8083 |
| 2 | api.ts | Fetches `/gpu-metrics`, stores real GPU data |
| 3 | api.ts | Fetches Gateway for CPU/memory (5s timeout fallback) |
| 4 | metricsStore | Polls every 2s, updates reactive state |
| 5 | Vue UI | Displays GPU model, utilization, VRAM |

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GPU_METRICS_URL` | `http://127.0.0.1:8083` | GPU proxy server URL |
| `VITE_GPU_METRICS_URL` | (env override) | Environment variable override |

---

## Troubleshooting

### GPU shows "Unknown GPU"
- Ensure GPU metrics server is running on port 8083
- Check if `nvidia-smi` works from command line
- Verify no firewall blocking localhost:8083

### Data not updating
- Check browser console for `[API] Real GPU data from proxy:` logs
- Verify metricsStore is polling (check network tab)

### Port conflict
- Port 8082 is used by Contract Reviewer
- GPU metrics server uses port 8083 to avoid conflicts
