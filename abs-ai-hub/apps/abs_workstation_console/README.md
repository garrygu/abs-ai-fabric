# ABS Workstation Console

A flagship system showcase application for CES demonstrations. Features real-time AI workload monitoring, live system metrics, and an auto-activating Attract Mode with GPU-accelerated visualizations.

## Features

### 📊 **Live System Metrics**
- Real-time GPU, CPU, and RAM monitoring
- Animated progress rings and performance cards
- Temperature and power consumption tracking

### 🤖 **AI Workloads**
- Active applications with workload type indicators
- Live inference status and model information
- Token throughput and latency metrics

### 🧠 **Installed Models**
- Read-only view of local AI models
- Status indicators (Running, Idle, Loading)
- Model metadata and specifications

### 🖥️ **Explore Workstations**
- SKU information and specifications
- Call-to-action buttons for engagement
- Product comparison features

### 🎬 **Attract Mode (Showcase Mode)**
- Auto-activates after idle timeout
- Multi-scene visual demonstrations:
  - **Scene A**: GPU ring with particle effects
  - **Scene B-E**: Additional visualization scenes
- WebGPU-accelerated particle systems
- Touch/mouse interaction to exit
- GPU-aware resource budgeting

### 📋 **Guided Demo**
- CES-optimized guided prompts kiosk
- Pre-configured AI demonstrations
- Challenge-based interactions

## Quick Start

```bash
cd c:\ABS\abs-ai-hub\apps\abs_workstation_console
npm install
npm run dev
```

Open http://localhost:5200

## CES Mode

Enable CES-specific styling (larger fonts, orange accents, demo features):

```bash
# Development
CES_MODE=true npm run dev

# Production build
CES_MODE=true npm run build
```

## Project Structure

```
src/
├── pages/                    # Main application pages
│   ├── Page1Dashboard.vue
│   ├── Page2Performance.vue
│   ├── Page3Workloads.vue
│   ├── Page4Models.vue
│   └── Page5Explore.vue
├── attract/                  # Attract Mode system
│   ├── config/              # Scene manifests and config
│   ├── engine/              # Rendering engines
│   ├── services/            # Backend integration
│   └── ui/
│       └── scenes/          # Scene components
│           ├── SceneA.vue   # GPU ring visualization
│           ├── SceneB.vue
│           ├── SceneC.vue
│           ├── SceneD.vue
│           └── SceneE.vue
├── webgpu/                   # WebGPU rendering
│   ├── shaders/             # WGSL shaders
│   │   ├── particles/
│   │   └── post/
│   └── pipelines/           # GPU compute pipelines
├── components/               # Reusable UI components
│   ├── demo/                # Demo control components
│   │   ├── DemoControlPanel.vue
│   │   └── GuidedPromptKiosk.vue
│   └── ...
├── stores/                   # Pinia state stores
│   ├── metricsStore.ts
│   ├── workloadsStore.ts
│   ├── modelsStore.ts
│   ├── attractModeStore.ts
│   └── demoControlStore.ts
├── composables/              # Vue composables
│   ├── useCESMode.ts
│   ├── useBloomEffect.ts
│   └── useWebGPUAttractMode.ts
└── services/
    └── api.ts               # Gateway API client
```

## Tech Stack

- **Vue 3** with Composition API and `<script setup>`
- **TypeScript** for type safety
- **Vite** for fast development and builds
- **Pinia** for state management
- **WebGPU** for GPU-accelerated particle systems
- **WGSL** shaders for custom effects

## API Integration

Connects to the Gateway API at `http://localhost:8081`:
- `/gpu/metrics` - Real-time GPU metrics
- `/v1/models` - Model information
- `/v1/apps` - Application status
- `/admin/health` - System health

## Attract Mode Configuration

Edit `src/attract/config/sceneManifest.ts`:

```typescript
export const DEV_MODE = false;  // Set true for testing
export const SCENE_MANIFEST = [
  { id: 'scene-a', duration: 30000 },
  { id: 'scene-b', duration: 25000 },
  // ...
];
```

## Build for Production

```bash
# Standard build
npm run build

# With CES styling
CES_MODE=true npm run build

# Preview production build
npm run preview
```

## Documentation

Detailed specifications available in `docs/`:
- [Attract Mode Execution Plan](docs/attract_mode_end-to-end_execution_plan.md)
- [Scene A Engineering Spec](docs/scene_a_engineering_spec.md)
- [WebGPU Implementation](docs/scene_a_system_pulse_webgpu_spec_v1.0.md)
