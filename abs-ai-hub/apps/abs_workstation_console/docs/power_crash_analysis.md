# Incident Report: RTX 6000 Blackwell Power Crash on 110V Circuit

## Problem Description
When running the "Try me" demo function using the DeepSeek 70B (Q4_K_M) model (or Dual Models mode) on an ABS Workstation Console, the system experiences a critical hardware crash (screen goes dark, system becomes unresponsive but fans remain on) during the 3rd conversation turn. The issue occurs consistently on Windows 11 Pro and requires a manual hard reboot to recover.

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

## Verified Workaround
The issue was temporarily mitigated by limiting the GPU's power via the NVIDIA System Management Interface:
```bash
nvidia-smi -pl 250
```
This forces the GPU to operate at a maximum of 250W. Even if a 2x transient spike occurs ($250W \times 2 = 500W$), the total system load stays well below the 110V PSU threshold. However, this severely throttles the performance of the Blackwell architecture.

## Permanent Solutions

To utilize the RTX 6000 Blackwell safely and at full performance, the electrical bottleneck must be resolved.

### Solution A: Upgrade to a 240V Circuit (Recommended)
This is the only way to safely run the 600W Blackwell at maximum capacity without artificial software throttling.
1.  Have a certified electrician install a dedicated 200V-240V circuit (e.g., NEMA L6-20 or L6-30 receptacle).
2.  Connect the 2000W PSU to this new 240V outlet.
3.  The PSU will now safely deliver its full 2000W capacity, easily absorbing the 1200W transient spikes.

### Solution B: Software Power Capping (Compromise)
If installing a 240V line is impossible, you must permanently cap the GPU power draw to prevent the transient spikes from tripping the PSU.
1.  Determine the highest stable power limit. 250W is overly restrictive; test limits in 25W increments (e.g., 350W, 400W).
    ```bash
    nvidia-smi -pl 400
    ```
2.  **Windows Automation:** The `nvidia-smi` power limit resets on every reboot. You must create a Windows Scheduled Task to run this command automatically on startup with highest (Administrator) privileges.

### Additional Safety Checks
*   **Cable Integrity:** Ensure the 600W GPU is powered by dedicated, high-quality 12V-2x6 or 12VHPWR cables connected directly to the PSU. Absolutely **do not** use "daisy-chained" (split) 8-pin PCIe cables, as combining transient spikes onto shared wires is a severe fire hazard.
