# Incident Report: RTX 6000 Blackwell Instability on 110V Circuit

## Problem Description
When running the "Try me" demo function using the DeepSeek 70B (Q4_K_M) model (or Dual Models mode) on an ABS Workstation Console, the system experiences critical instability requiring a manual hard reboot to recover. Two distinct failure modes have been observed:

| # | Power Limit | Symptom | Root Cause |
|---|-------------|---------|------------|
| 1 | 600W (default) | **Screen goes dark**, fans stay on | PSU OCP/OPP trip — 12V rail cut to GPU |
| 2 | 400W | **Screen stays on**, system freezes (no input response) — **stream mode only** | GPU driver/TDR hang or sustained thermal/PCIe instability |

**Hardware Profile:**
*   **GPU:** NVIDIA RTX 6000 Blackwell (96GB VRAM, 600W TDP)
*   **PSU:** 2000W Power Supply Unit
*   **Mains Power:** Standard 110V AC household/office outlet

## Root Cause Analysis
The root cause is a **hardware-level Over-Current Protection (OCP) / Over-Power Protection (OPP) trip** triggered by the Power Supply Unit (PSU) due to extreme transient power spikes during the Large Language Model (LLM) inference Prefill phase, compounded by the severe physical limitations of a 110V AC circuit.

### 1. The 110V PSU Derating Limit
While the PSU is rated for 2000W, this specification is only achievable on a 200V-240V circuit. When connected to a standard 110V (15A/20A) outlet, the PSU is physically "derated" (limited) to a maximum output of typically **1300W to 1600W** to prevent melting the wall wiring or tripping the building's circuit breaker. 

### 2. High Base System Draw + 600W GPU
The workstation's baseline power consumption (CPU, Motherboard, Fans, RAM) can be estimated between 200W–400W under load. When the RTX 6000 Blackwell operates at its maximum Continuous TDP, it draws **600W**.
*   *Total Continuous Load:* ~1000W. (This is high, but technically within the derated limit of the PSU on 110V).

### 3. The Fatal Transient Power Spike (The Prefill Phase)
The crash consistently happens on the 3rd conversation. This is because LLM inference has two distinct phases:
1.  **Prefill Phase (Context Processing):** The GPU must ingest the new prompt *and* the accumulated context from the previous two conversations. This requires calculating a massive Attention Matrix. For an architectural beast like the Blackwell GPU, tens of thousands of Tensor Cores engage simultaneously in a dense matrix multiplication (GEMM).
2.  **Decode Phase (Token Generation):** The GPU generates words one by one. This is memory-bandwidth bound and draws significantly less power. Streaming vs. Non-Streaming only affects this phase.

During that 3rd-conversation Prefill Phase, the Blackwell GPU experiences a **Transient Power Excursion**. According to ATX 3.0 / PCIe 5.0 specifications, a 600W GPU is permitted to draw up to **2x its TDP (1200W)** for a few hundred microseconds.

*   *Total Transient Load:* Base System (~300W) + GPU Transient Spike (~1200W) = **~1500W+ instantaneous demand.**

This microsecond spike exceeds the derated maximum capacity of the 2000W PSU running on 110V. The PSU detects this as a dangerous short-circuit/overload and instantly triggers OCP/OPP, severing the 12V power to the PCIe cables. The GPU drops off the bus, the screen goes black, and the OS freezes (Kernel Panic / TDR Timeout).

## Failure Mode Analysis

### Failure Mode 1: Screen Goes Dark (OCP/OPP Trip) — 600W default
The PSU detects a transient spike exceeding its derated 110V capacity and instantly severs the 12V rail. The GPU drops off the PCIe bus, screen goes black. Classic hardware overcurrent protection.

### Failure Mode 2: Screen Stays On, System Freezes — 400W cap, stream mode
At 400W, the transient spike is capped at ~800W (2x), which is within the 110V PSU's derated range — so the PSU does **not** trip. Instead, the system freezes with the screen still displaying. This is a **distinctly different failure mode** and points to:

1. **GPU TDR (Timeout Detection & Recovery) failure:** During streaming, the GPU sustains continuous Decode-phase load for an extended duration. If a driver or compute error occurs, Windows attempts a TDR reset. If TDR fails to recover the GPU, the system hangs completely.
2. **Thermal throttle cascade:** Extended streaming mode keeps the GPU at sustained load. If the GPU or VRM temperature exceeds a threshold, the GPU clocks down aggressively, which can cause the driver to lose sync with in-flight CUDA/compute kernels, leading to a hang.
3. **PCIe link instability:** Sustained power draw can cause micro-voltage droops on the PCIe 12VHPWR cable, corrupting PCIe communication without fully cutting power — leaving the display (connected via DisplayPort, not PCIe data) intact but the system unresponsive.

> **Key diagnostic clue:** The screen staying on confirms the GPU has not entirely lost power. The freeze is happening at the **driver or OS kernel level**, not the hardware power level.

## Workaround History
| Power Limit | Result |
|-------------|--------|
| 600W (default) | Crash on 3rd turn — OCP/OPP trip |
| 400W | Still freezes in stream mode — driver/thermal hang |
| 250W | Previously stable — see below |

The 250W limit was the only confirmed stable configuration:
```bash
nvidia-smi -pl 250
```
Even if a 2x transient spike occurs ($250W \times 2 = 500W$), the total system load stays well within the PSU threshold AND the sustained streaming load is low enough to avoid TDR hangs. However, this severely throttles performance.

## Permanent Solutions

To utilize the RTX 6000 Blackwell safely and at full performance, the electrical bottleneck must be resolved.

### Solution A: Upgrade to a 240V Circuit (Recommended)
This is the only way to safely run the 600W Blackwell at maximum capacity without artificial software throttling.
1.  Have a certified electrician install a dedicated 200V-240V circuit (e.g., NEMA L6-20 or L6-30 receptacle).
2.  Connect the 2000W PSU to this new 240V outlet.
3.  The PSU will now safely deliver its full 2000W capacity, easily absorbing the 1200W transient spikes.

### Solution B: Software Power Capping (Compromise)
If installing a 240V line is impossible, you must permanently cap the GPU power draw to prevent the transient spikes from tripping the PSU.
1.  **Start from the known-stable baseline (250W)** and test upward in small increments:
    ```bash
    nvidia-smi -pl 300
    ```
    Specifically test in **stream mode** with multiple conversation turns, since that is the failure trigger at 400W.
2.  Also consider disabling streaming at the application layer (already explored in previous work) to avoid the sustained Decode-phase load that triggers Failure Mode 2.
3.  **Windows Automation:** The `nvidia-smi` power limit resets on every reboot. A Windows Scheduled Task must be used to set the limit automatically (see `setup_nvidia_powerlimit.ps1`).

### Additional Safety Checks
*   **Cable Integrity:** Ensure the 600W GPU is powered by dedicated, high-quality 12V-2x6 or 12VHPWR cables connected directly to the PSU. Absolutely **do not** use "daisy-chained" (split) 8-pin PCIe cables, as combining transient spikes onto shared wires is a severe fire hazard.
