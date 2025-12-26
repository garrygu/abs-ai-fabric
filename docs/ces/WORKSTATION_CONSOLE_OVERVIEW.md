# ABS Workstation Console - Overview

**CES Flagship Showcase Application**

---

## What is ABS Workstation Console?

The ABS Workstation Console is a **visual showcase application** designed specifically for trade show demonstrations. It displays real-time AI workload monitoring with stunning GPU-accelerated visual effects that automatically activate when idle.

---

## Key Features

### 📊 **Live System Metrics**
Real-time monitoring of workstation performance:
- GPU utilization with animated ring display
- CPU usage and temperature
- RAM consumption
- Power draw monitoring

### 🤖 **AI Workload Visualization**
See AI in action:
- Active applications and their workload types
- Live inference status indicators
- Token throughput metrics
- Model loading states

### 🧠 **Installed Models**
Browse available AI models:
- Model names and sizes
- Status (Running, Idle, Loading)
- Memory usage per model
- Quick model information

### 🎬 **Attract Mode (Showcase)**
Auto-activating eye-catching demonstration:
- Activates after 60 seconds of inactivity
- WebGPU-powered particle effects
- GPU ring visualization with bloom effects
- Multiple rotating scenes
- Touch anywhere to exit

### 📋 **Guided Demo**
Pre-configured AI demonstrations:
- Challenge-based prompts
- Model recommendations per task
- One-click demo execution

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              ABS Workstation Console                │
├─────────────────────────────────────────────────────┤
│                                                     │
│   ┌─────────────────────────────────────────────┐  │
│   │              UI Layer (Vue 3)               │  │
│   │  Dashboard | Performance | Models | Explore │  │
│   └─────────────────────────────────────────────┘  │
│                                                     │
│   ┌─────────────────────────────────────────────┐  │
│   │            Attract Mode Engine              │  │
│   │    Scene Manager | WebGPU Renderer          │  │
│   │    Particle Systems | Post Effects          │  │
│   └─────────────────────────────────────────────┘  │
│                                                     │
│   ┌─────────────────────────────────────────────┐  │
│   │              Data Layer                     │  │
│   │  Pinia Stores | API Services | WebSocket    │  │
│   └─────────────────────────────────────────────┘  │
│                                                     │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
             ┌─────────────────┐
             │ Gateway API     │
             │ :8081           │
             └─────────────────┘
```

---

## Pages / Screens

| Page | Purpose | Highlights |
|------|---------|------------|
| **Dashboard** | Overview | Quick stats, recent activity |
| **Performance** | GPU metrics | Large animated GPU ring, real-time graphs |
| **Workloads** | Active AI apps | Running processes, inference status |
| **Models** | Installed LLMs | Model list, memory usage, status |
| **Explore** | Hardware info | SKU details, specifications |

---

## Attract Mode Scenes

The showcase cycles through multiple visual scenes:

| Scene | Visual | Duration |
|-------|--------|----------|
| **Scene A** | GPU ring with particle explosion | 30 sec |
| **Scene B** | Data flow visualization | 25 sec |
| **Scene C** | Neural network animation | 25 sec |
| **Scene D** | Metrics dashboard | 20 sec |
| **Scene E** | Brand showcase | 20 sec |

---

## CES Demo Mode

Enable enhanced styling for trade shows:

```powershell
CES_MODE=true npm run dev
```

**CES Mode Enhancements:**
- 🎨 Orange accent colors
- 📏 Larger fonts for visibility
- 🔒 Restricted admin operations
- 🎬 Optimized attract mode timing

---

## Technical Specs

| Component | Technology |
|-----------|------------|
| Framework | Vue 3 + TypeScript |
| State | Pinia stores |
| Graphics | WebGPU + WGSL shaders |
| Effects | Bloom, particles, gradients |
| Build | Vite |

---

## Talking Points

1. **"Real-time GPU monitoring"** - See AI workloads running live
2. **"Attract Mode"** - Auto-activating showcase grabs attention
3. **"WebGPU graphics"** - Cutting-edge GPU-accelerated visuals
4. **"Touch to engage"** - Interactive demo experience
5. **"CES-ready"** - Purpose-built for trade show environments

---

## Quick Start

```powershell
cd c:\ABS\abs-ai-hub\apps\abs_workstation_console
npm run dev
```

**Access:** http://localhost:5200
