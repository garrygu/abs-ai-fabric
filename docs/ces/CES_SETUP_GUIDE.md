# ABS AI Fabric - CES Setup Guide

Step-by-step guide to set up and start the complete ABS AI Fabric system for CES demonstrations.

## Prerequisites

- Windows 10/11 with WSL2 or Windows Server
- Docker Desktop installed and running
- Node.js 18+ and npm
- NVIDIA GPU with CUDA drivers (for AI inference)
- Ollama installed with models downloaded

## Quick Start (TL;DR)

```powershell
# 1. Start Core Services
cd c:\ABS\core
.\start-core.ps1

# 2. Start AI Fabric (Admin UI)
cd c:\ABS\abs-ai-hub\hub-ui-v2
npm run dev

# 3. Start Workstation Console
cd c:\ABS\abs-ai-hub\apps\abs_workstation_console
npm run dev
```

---

## Detailed Setup

### Step 1: Start Core Services (Backend)

The core services provide the AI runtime infrastructure.

```powershell
cd c:\ABS\core
.\start-core.ps1
```

This starts:
| Service | Port | Description |
|---------|------|-------------|
| Ollama | 11434 | LLM inference engine |
| Qdrant | 6333 | Vector database |
| Redis | 6379 | Cache and sessions |
| PostgreSQL | 5432 | Document storage |
| GPU Metrics | - | GPU monitoring server |

**Verify services are running:**
```powershell
docker ps | Select-String "abs-"
```

Expected output shows containers: `abs-ollama`, `abs-qdrant`, `abs-redis`, `document-hub-postgres`

### Step 2: Start Hub Gateway (API)

The Gateway provides unified API access for all apps.

```powershell
cd c:\ABS\core
docker compose up -d hub-gateway
```

**Verify Gateway:**
```powershell
curl http://localhost:8081/health
```

### Step 3: Start AI Fabric (Admin UI)

The AI Fabric provides the administrative interface.

```powershell
cd c:\ABS\abs-ai-hub\hub-ui-v2
npm install  # First time only
npm run dev
```

**Access:** http://localhost:5173

**Features available:**
- ✅ Applications list and launcher
- ✅ Asset registry (models, services)
- ✅ Observability dashboard
- ✅ Admin controls

### Step 4: Start ABS Workstation Console

The flagship CES showcase application.

```powershell
cd c:\ABS\abs-ai-hub\apps\abs_workstation_console
npm install  # First time only
npm run dev
```

**Access:** http://localhost:5200

**Features available:**
- ✅ Live GPU/CPU/RAM metrics
- ✅ AI workload visualization
- ✅ Installed models panel
- ✅ Attract Mode (auto-activating showcase)
- ✅ Guided demo prompts

---

## CES Demo Mode

For trade show environments, enable CES mode for enhanced styling and restricted controls.

### Enable CES Mode for AI Fabric

```powershell
cd c:\ABS\abs-ai-hub\hub-ui-v2
echo "VITE_CES_MODE=true" > .env
npm run dev
```

### Enable CES Mode for Workstation Console

```powershell
cd c:\ABS\abs-ai-hub\apps\abs_workstation_console
CES_MODE=true npm run dev
```

**CES Mode Features:**
- 🔒 Destructive operations disabled (delete, stop, restart)
- 🎨 Orange accent colors and larger fonts
- 📢 Demo mode banner displayed
- 🎬 Attract Mode with WebGPU particle effects

---

## Verification Checklist

| Component | URL | Expected |
|-----------|-----|----------|
| Gateway API | http://localhost:8081/health | `{"status": "healthy"}` |
| AI Fabric | http://localhost:5173 | Admin dashboard |
| Workstation Console | http://localhost:5200 | System metrics |
| Ollama | http://localhost:11434 | LLM API |

---

## Stopping Services

### Stop Frontend Apps
Press `Ctrl+C` in the terminal running each app.

### Stop Core Services
```powershell
cd c:\ABS\core
.\stop-core.ps1
```

---

## Troubleshooting

### Core services won't start
```powershell
# Check Docker is running
docker info

# Check for port conflicts
netstat -an | findstr "11434 6333 6379 5432"

# View container logs
docker logs abs-ollama
```

### Gateway not responding
```powershell
# Restart gateway
cd c:\ABS\core
docker compose restart hub-gateway

# Check logs
docker logs abs-core-hub-gateway-1 --tail 50
```

### No GPU metrics
```powershell
# Ensure GPU metrics server is running
cd c:\ABS\core\gateway
python gpu_metrics_server.py
```

### Attract Mode not working
1. Ensure GPU metrics are available
2. Wait for idle timeout (default: 60 seconds)
3. Check browser console for WebGPU support

---

## Network Diagram

```
┌─────────────────────────────────────────────────────────┐
│               User Browser / Kiosk Display              │
└────────────┬──────────────────────┬─────────────────────┘
             │                      │
             ▼                      ▼
    ┌────────────────┐    ┌────────────────────┐
    │  AI Fabric     │    │ Workstation Console│
    │  :5173         │    │  :5200             │
    └───────┬────────┘    └─────────┬──────────┘
            │                       │
            └───────────┬───────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │   Hub Gateway :8081   │
            └───────────┬───────────┘
                        │
    ┌───────────────────┼───────────────────┐
    │                   │                   │
    ▼                   ▼                   ▼
┌─────────┐      ┌─────────┐        ┌─────────┐
│ Ollama  │      │ Qdrant  │        │ Redis   │
│ :11434  │      │ :6333   │        │ :6379   │
└─────────┘      └─────────┘        └─────────┘
```
