# GPU TDR Fix — DeepSeek R1:70B Crash Prevention

**Date:** 2026-03-16  
**GPU:** NVIDIA RTX PRO 6000 Blackwell (96 GB VRAM)  
**Runtime:** Ollama in Docker (WSL2)

---

## Problem

- **LLaMA 70B (Q4):** Streams responses near-instantly ✅
- **DeepSeek R1:70B (Q4):** Very slow, causes **whole PC reboot** after 2–3 requests ❌

## Root Cause: Windows GPU TDR (Timeout Detection & Recovery)

Windows monitors GPU kernel execution time. Default TDR timeout = **2 seconds**.

DeepSeek R1 is a **reasoning model** that generates a hidden `<think>...</think>` chain (often thousands of tokens) before producing the visible answer. This extended GPU computation exceeds the TDR timeout, causing:

1. GPU driver reset → BSOD → PC reboot

LLaMA 70B has no thinking step, so it completes GPU kernels quickly and never triggers TDR.

## Fix 1: Code Changes (Ollama Options)

Both `chat.py` (streaming) and `llm_runtime.py` (non-streaming adapter) were updated:

```python
"options": {
    "num_ctx": 8192,     # Keep model in VRAM (prevents reload with 131K default)
    "num_batch": 64,     # Smaller GPU kernel slices to stay under TDR timeout (was 128)
    "num_predict": 2048  # Cap total generation tokens including <think> chain
}
```

| Parameter     | Before | After | Why                                              |
|---------------|--------|-------|--------------------------------------------------|
| `num_batch`   | 128    | 64    | Smaller batches = shorter GPU kernels = no TDR   |
| `num_predict` | (none) | 2048  | Caps DeepSeek's thinking chain to prevent runaway |

### Files Modified
- `core/gateway/routers/chat.py` — streaming path (lines 200–204)
- `core/gateway/adapters/llm_runtime.py` — non-streaming Ollama path (lines 120–125)

## Fix 2: Windows Registry — Increase TDR Timeout

This is the **critical fix** for whole-PC reboots.

1. Open `regedit`
2. Navigate to: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\GraphicsDrivers`
3. Create two **DWORD (32-bit)** values (Base: **Decimal**):

   | Name          | Value | Description                    |
   |---------------|-------|--------------------------------|
   | `TdrDelay`    | 60    | GPU kernel timeout (seconds)   |
   | `TdrDdiDelay` | 60    | DDI callback timeout (seconds) |

4. **Reboot** Windows to apply

> **Note:** Default TDR timeout is 2 seconds. Setting to 60 seconds gives the GPU ample time for 70B model inference without triggering a driver reset.

## Tuning Notes

- If DeepSeek response is **truncated too early**, increase `num_predict` (e.g., 4096)
- If still getting TDR with `num_batch: 64`, try `32`
- With 96 GB VRAM, `num_ctx: 8192` keeps the 70B Q4 model (~40 GB) comfortably in VRAM
- Only one 70B model should be loaded at a time; switching models triggers a full unload/reload cycle (~40 GB)
