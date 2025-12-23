# ABS Workstation Console

A flagship system app for CES showcase that demonstrates live local AI capability through real-time metrics, workload visualization, and an auto-activating Attract Mode.

## Quick Start

```bash
cd c:\ABS\abs-ai-hub\apps\abs_workstation_console
npm install
npm run dev
```

Then open http://localhost:5200

## Features

- **Live System Metrics**: Real-time GPU, CPU, RAM monitoring with animated visualizations
- **AI Workloads**: Display of active apps and their AI workload types
- **Installed Models**: Read-only view of local models with status
- **Explore Workstations**: SKU information with CTAs
- **Attract Mode**: Auto-activating idle visualization with GPU-aware resource budgeting

## CES Mode

To enable CES-specific styling (larger fonts, orange accents):

```bash
CES_MODE=true npm run build
```

## Architecture

```
src/
├── components/
│   ├── attract/           # Attract Mode components
│   │   ├── AttractModeOverlay.vue
│   │   ├── MetricsLayer.vue
│   │   ├── BrandingLayer.vue
│   │   ├── VisualDemoLayer.vue
│   │   └── visuals/
│   │       └── SystemVisualization.vue
│   ├── ConsoleHeader.vue
│   ├── LiveMetricsPanel.vue
│   ├── WorkloadsPanel.vue
│   ├── ModelsPanel.vue
│   └── ExploreSKUsPanel.vue
├── stores/
│   ├── metricsStore.ts
│   ├── workloadsStore.ts
│   ├── modelsStore.ts
│   └── attractModeStore.ts
├── services/
│   └── api.ts
├── composables/
│   └── useCESMode.ts
└── views/
    └── ConsoleView.vue
```
