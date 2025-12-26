# ABS AI Fabric (Hub UI v2)

A modern admin interface for managing and monitoring AI workloads on ABS Workstations. Built with Vue 3, TypeScript, and Vite.

## Features

### 📱 **Applications**
- Browse installed AI applications with status indicators
- Launch applications directly from the hub
- View app dependencies (LLM Runtime, Embeddings, etc.)
- App Store for discovering new applications

### 📦 **Assets**
- Manage models, services, and AI resources
- View asset metadata and configurations
- Monitor asset health and availability

### 📊 **Observability**
- Real-time system metrics and monitoring
- Service health status dashboard
- Performance tracking and alerts

### ⚙️ **Admin**
- Service controls (start/stop/restart)
- Model management (load/unload/delete)
- Cache management and system diagnostics
- Policy and governance controls
- CES Demo Mode for trade show environments

## Quick Start

```bash
cd c:\ABS\abs-ai-hub\hub-ui-v2
npm install
npm run dev
```

Open http://localhost:5173

## CES Demo Mode

For trade show environments, enable CES mode to make admin operations read-only:

```bash
# Create .env file
echo "VITE_CES_MODE=true" > .env

# Restart dev server
npm run dev
```

When enabled:
- 🔒 Destructive operations are disabled (delete, stop, restart)
- ✅ Viewing and monitoring remain enabled
- 📢 Banner indicates demo mode is active

See [CES_MODE_SETUP.md](./CES_MODE_SETUP.md) for detailed configuration.

## Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── CESModeBanner.vue
│   ├── CESModeTest.vue
│   └── PoweredByBanner.vue
├── composables/          # Vue composables
│   ├── useCESMode.ts
│   └── useCESRestrictions.ts
├── layouts/              # Page layouts
│   └── MainLayout.vue
├── views/                # Page views
│   ├── Admin/
│   ├── Apps/
│   ├── Assets/
│   └── Observability/
├── stores/               # Pinia stores
├── services/             # API services
└── router/               # Vue Router config
```

## Tech Stack

- **Vue 3** with Composition API and `<script setup>`
- **TypeScript** for type safety
- **Vite** for fast development and builds
- **Pinia** for state management
- **Vue Router** for navigation

## API Integration

The UI communicates with the Gateway API at `http://localhost:8081`:
- `/v1/assets` - Asset management
- `/admin/services` - Service control
- `/admin/models` - Model management
- `/admin/health` - System health

## Build for Production

```bash
# Standard build
npm run build

# With CES mode baked in
CES_MODE=true npm run build

# Preview production build
npm run preview
```
