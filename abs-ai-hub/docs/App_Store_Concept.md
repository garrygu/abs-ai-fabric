# ABS AI Hub App Store Concept

## Overview

The ABS AI Hub implements a clear separation between **Asset Management** (what's installed on your machine) and **App Store** (where you discover apps to install). The Assets repository centrally controls all installed resources (apps, models, services, data, tools, secrets) on the local machine, while the App Store provides a discovery mechanism where users can browse and install apps from multiple sources.

---

## Core Architecture

### Three-Layer System

```
┌─────────────────────────────────────────────────────────────┐
│                    APP STORE (Discovery)                     │
│  Browse and find apps from multiple sources                 │
│  - ABS Pre-configured Store (curated, maintained)          │
│  - Third-Party Sources (GitHub, GitLab, etc.)              │
│  - Self-Developed Apps (local repositories)                │
│                                                              │
│  [User browses → selects app → clicks "Install"]            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ User installs app
                     │
┌────────────────────▼────────────────────────────────────────┐
│              ASSETS REPOSITORY (Catalog)                     │
│  Central control of all installed resources                 │
│  catalog.json contains:                                     │
│  - Apps (installed and configured)                          │
│  - Models (available for use)                              │
│  - Services (qdrant, postgresql, etc.)                      │
│  - Tools (OCR, parsers, etc.)                               │
│  - Datasets (vector stores, file collections)               │
│  - Secrets (credentials, API keys)                          │
│                                                              │
│  Managed through Asset Management UI/API                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Physical deployment
                     │
┌────────────────────▼────────────────────────────────────────┐
│           INSTALLED RESOURCES (Local Machine)               │
│  Physical files and containers                              │
│  - abs-ai-hub/apps/{app-id}/ (app code & config)           │
│  - Docker containers (running apps/services)                │
│  - Volume mounts (data persistence)                         │
│  - Network configuration (abs-net)                          │
└─────────────────────────────────────────────────────────────┘
```

### Key Distinctions

| Component | Purpose | Location | Managed By |
|-----------|---------|----------|------------|
| **App Store** | Discovery & browsing apps | Remote/External sources | ABS team, community, user |
| **Assets Repository** | Central control of installed resources | `catalog.json` | Asset Management System |
| **Installed Resources** | Physical deployment | Filesystem, Docker | Docker Compose, Hub Gateway |

---

## Assets Repository (Central Control)

### Purpose

The **Assets Repository** is the single source of truth for everything installed and configured on the user's local machine. It is structured as a two-tier system:

1. **`assets/registry/assets.json`** — The **primary asset index** (bind-mounted into the gateway as `/app/assets/registry/assets.json`). This is the canonical file the gateway reads to enumerate which apps, models, services, tools, and datasets are registered. Each entry points to a `.yaml` file with full asset metadata.

2. **`core/gateway/catalog.json`** — A **supplementary catalog** (also bind-mounted into the gateway). It provides additional configuration for assets such as model policies, allowed embeddings, and defaults. It is loaded by the gateway alongside the registry index.

> [!IMPORTANT]
> To **add, remove, or hide an app from the Hub UI**, you must edit **`assets/registry/assets.json`** and then call the gateway reload API:
> ```
> POST http://localhost:8081/v1/admin/assets/reload
> ```
> Changes to `catalog.json`, `apps-registry.json`, or `store/official-apps.json` alone will NOT remove an app from the Installed Apps dashboard, as those files serve different purposes.

The Assets Repository centrally controls:

- **Apps**: Installed applications with their configurations
- **Models**: LLM models, embedding models available for use
- **Services**: Infrastructure services (qdrant, postgresql, redis, etc.)
- **Tools**: Functional capabilities (OCR, parsers, chunkers, rerankers)
- **Datasets**: Data collections (vector stores, file collections)
- **Secrets**: Credentials and API keys (references only)

### Gateway Mount Map

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `assets/` | `/app/assets` | Full assets directory (YAML files + registry index) |
| `core/gateway/catalog.json` | `/app/catalog.json` | Policy and supplementary config |
| `abs-ai-hub/apps-registry.json` | `/app/apps-registry.json` | App registry (for the App Store installation tracking) |
| `abs-ai-hub/store` | `/app/store` | App Store official catalog |

### Asset Schema (App Example)

```json
{
  "id": "contract-reviewer-v2",
  "class": "app",
  "name": "Contract Reviewer v2",
  "version": "2.1.0",
  "description": "Professional AI-powered contract analysis",
  "owner": "user",
  "lifecycle": {
    "desired": "running",
    "actual": "running"
  },
  "policy": {
    "allowed_models": ["llama3.2:3b", "llama3.2:latest"],
    "allowed_embeddings": ["legal-bert", "bge-small-en-v1.5"],
    "defaults": {
      "chat_model": "llama3.2:3b",
      "embed_model": "legal-bert"
    }
  },
  "health": {
    "status": "healthy",
    "url": "http://localhost:8082/healthz",
    "last_check": "2024-01-15T10:30:00Z"
  },
  "metadata": {
    "category": "Legal Apps",
    "icon": "contract-reviewer.png",
    "url": "http://localhost:8082",
    "port": 8082,
    "path": "apps/contract-reviewer-v2",
    "database_schema": "document_hub"
  },
  "updates": {
    "latest_version": "2.2.0",
    "current_version": "2.1.0",
    "update_available": true,
    "update_source": "git://github.com/abs-ai/contract-reviewer-v2.git",
    "changelog": "https://github.com/abs-ai/contract-reviewer-v2/releases/tag/v2.2.0"
  },
  "dependencies": {
    "services": ["qdrant", "postgresql"],
    "models": [],
    "status": "satisfied",
    "missing": []
  },
  "security": {
    "trust_level": "verified",
    "source_type": "abs-official",
    "scan_status": "passed",
    "badge": "verified"
  }
}
```

### Asset Management Operations

All assets are managed through the Asset Management system:

- **View Assets**: Browse all installed apps, models, services, etc.
- **Edit Assets**: Modify configuration, policy, metadata
- **Enable/Disable**: Start/stop lifecycle of assets
- **Delete Assets**: Remove from catalog (and uninstall if applicable)

**Important**: When an app is installed from the App Store, it automatically becomes an asset in the catalog and is centrally controlled through the Asset system.

---

## App Store (Discovery & Browsing)

### Purpose

The **App Store** is where users discover and find apps to install. It is NOT stored in the assets repository until an app is installed. Instead, it's a discovery/browsing interface that aggregates apps from multiple sources.

### App Store Sources

#### 1. **ABS Pre-configured Store**

- Curated apps maintained and updated by ABS team
- Quality-controlled, tested, and documented
- Automatically updated with new releases
- Can be hosted:
  - Locally bundled with ABS installation
  - Remote URL (ABS-maintained repository)
  - Hybrid (local cache + remote updates)

**Example Sources:**
```
https://store.abs-ai.com/official/v1/apps.json
file:///abs-ai-hub/store/official-apps.json (local cache)
```

#### 2. **Third-Party Sources**

- Community-contributed apps
- External repositories (GitHub, GitLab, etc.)
- Custom app registries
- User can add/manage sources:
  - Add GitHub repository
  - Add GitLab group
  - Add custom app registry URL
  - Browse community marketplace (future)

**Example Sources:**
```
https://github.com/community/abs-apps
https://gitlab.com/groups/abs-community/apps
https://custom-store.example.com/abs-apps.json
```

#### 3. **Self-Developed Apps**

- Apps created by the user
- Local development repositories
- User's own Git repositories
- Can be:
  - Added manually from local path
  - Linked from user's Git repository
  - Imported from development workspace

**Example Sources:**
```
file:///home/user/my-abs-apps/app1/
git://github.com/user/my-custom-app.git
file:///workspace/abs-projects/new-app/
```

### App Store Entry Structure

Apps in the store are defined with metadata needed for discovery and installation:

```json
{
  "id": "example-app",
  "name": "Example Application",
  "version": "1.2.0",
  "description": "An example application for the App Store",
  "author": "Developer Name",
  "license": "MIT",
  "category": "Legal Apps",
  "tags": ["document-analysis", "rag", "pdf"],
  "icon": "https://store.abs-ai.com/icons/example-app.png",
  "screenshots": [
    "https://store.abs-ai.com/screenshots/example-app-1.png"
  ],
  "source": {
    "type": "abs-official" | "third-party" | "self-developed",
    "location": "git://github.com/user/repo.git",
    "repository": "https://github.com/user/repo",
    "branch": "main",
    "manifest_path": "app.manifest.json"
  },
  "requirements": {
    "abs_version": ">= 1.0.0",
    "services": ["qdrant", "postgresql"],
    "models": [],
    "resources": {
      "cpu": "2 cores",
      "memory": "4GB",
      "disk": "1GB"
    }
  },
  "installation": {
    "method": "docker-compose",
    "steps": [
      "Clone repository",
      "Copy to apps/{app-id}/",
      "Run docker compose up -d"
    ]
  },
  "metadata": {
    "rating": 4.5,
    "download_count": 1234,
    "last_updated": "2024-01-15",
    "verified": true
  }
}
```

### Store Aggregation

The App Store UI aggregates apps from all configured sources:

```
App Store View
├── ABS Official Store (pre-configured)
│   ├── Contract Reviewer v2
│   ├── Legal Assistant
│   ├── RAG PDF Voice
│   └── ...
├── Third-Party Sources
│   ├── Community App 1
│   ├── Community App 2
│   └── ...
└── Self-Developed
    ├── My Custom App
    └── ...
```

---

## User Workflow

### 1. **Browse App Store**

- User opens App Store from Hub dashboard
- Browse apps from all sources (ABS, third-party, self-developed)
- Filter by category, tags, source type
- Search by name, description, tags
- View app details: description, screenshots, requirements, ratings

### 2. **Install App**

- User clicks "Install" on desired app
- **Dependency Resolution**:
  - System automatically detects missing services/dependencies
  - Displays dependency graph visualization
  - User can click "Install Dependencies" to auto-install missing services
  - Shows warnings for optional dependencies
- **Security Check** (for third-party apps):
  - Scans Dockerfile/manifest for risky instructions
  - Displays trust badge (verified, community, unknown)
  - User confirms before proceeding
- System validates requirements (dependencies, resources, ABS version)
- Retrieves app from source:
  - **ABS Official**: Already available or downloaded from ABS store
  - **Third-Party**: Clone from Git repository or download from URL
  - **Self-Developed**: Copy from local path or clone from user's repo
- Creates app directory: `abs-ai-hub/apps/{app-id}/`
- Copies necessary files (docker-compose.yml, Dockerfile, source code, etc.)
- **Adds app to Assets Repository** (`catalog.json`) with initial configuration
- Registers app in `apps-registry.json` for Hub UI
- App appears in "My Apps" and Asset Management

### 3. **Manage Installed App (Via Assets)**

Once installed, the app is managed through the Asset Management system:

- **View**: See app in Asset Management UI
- **Configure**: Edit policy, models, metadata
- **Start/Stop**: Control lifecycle (`lifecycle.desired: "running" | "stopped"`)
- **Monitor**: View health status, logs, metrics
- **Update Management**:
  - System tracks available updates via version comparison
  - "Update Available" badge shown in UI
  - One-click update to latest version
  - Rollback to previous version if needed
  - Changelog preview before updating
- **Dependency Management**:
  - View dependency graph
  - Check dependency status
  - Auto-install missing dependencies
- **Uninstall**: Remove from assets and delete local files

### 4. **Physical Deployment**

- Asset Management controls Docker containers
- Gateway orchestrates container lifecycle
- Apps run in `abs-net` Docker network
- Data persisted in Docker volumes

---

## Data Flow

### Installation Flow

```
User browses App Store
    ↓
Selects app from ABS/Third-party/Self-developed source
    ↓
Clicks "Install"
    ↓
System retrieves app from source
    ↓
Validates requirements
    ↓
Creates app directory (abs-ai-hub/apps/{app-id}/)
    ↓
Copies files and configuration
    ↓
Adds entry to assets/registry/assets.json (Primary Asset Index)
    ↓
Adds policy config to catalog.json (Supplementary)
    ↓
Registers in apps-registry.json (App Store tracking)
    ↓
Calls POST /v1/admin/assets/reload (triggers live gateway refresh)
    ↓
App appears in Asset Management and "My Apps"
    ↓
User can start app via Asset Management
    ↓
Docker container starts
    ↓
App becomes available in Hub
```

### Management Flow

```
App installed → Asset in catalog.json
    ↓
Managed through Asset Management UI
    ↓
Changes to policy/configuration
    ↓
Applied to running container
    ↓
Health monitored by Gateway
    ↓
Status reflected in Asset Management
```

---

## Technical Implementation

### Assets Repository Structure

The gateway uses a two-tier system:

#### Primary Index: `assets/registry/assets.json`

This is the **canonical source of truth** the gateway reads at startup and on reload. It is an index of all registered assets. Each entry points to a YAML file with full metadata.

```json
{
  "version": "1.0",
  "description": "ABS AI Fabric Asset Registry Index",
  "core_assets": [
    { "id": "ollama",      "interface": "llm-runtime",    "path": "core/llm-runtime/ollama/asset.yaml" },
    { "id": "postgresql",  "interface": "metadata-store", "path": "core/metadata-store/postgresql/asset.yaml" }
  ],
  "apps": [
    { "id": "contract-reviewer-v2", "interface": "application", "path": "apps/contract-reviewer-v2/asset.yaml" },
    { "id": "onyx-assistant",       "interface": "application", "path": "apps/onyx-assistant/asset.yaml" }
  ],
  "models": [ ... ],
  "tools": [ ... ],
  "datasets": [ ... ]
}
```

**To add or remove an app from the Hub UI**, edit this file and call:
```
POST http://localhost:8081/v1/admin/assets/reload
```

#### Supplementary Config: `core/gateway/catalog.json`

Provides model policies, allowed embeddings, and defaults for assets that need fine-grained configuration. Loaded alongside the registry index.

```json
{
  "version": "1.0",
  "assets": [
    {
      "id": "contract-reviewer-v2",
      "class": "app",
      "name": "Contract Reviewer v2",
      "lifecycle": { "desired": "running", "actual": "running" },
      "policy": { "allowed_models": ["llama3.2:3b"], "allowed_embeddings": ["legal-bert"] },
      "metadata": { "url": "http://localhost:8082" }
    }
  ]
}
```

### App Store Sources Configuration

**File**: `abs-ai-hub/store-sources.json` (new file)

```json
{
  "sources": [
    {
      "id": "abs-official",
      "name": "ABS Official Store",
      "type": "official",
      "url": "https://store.abs-ai.com/official/v1/apps.json",
      "local_cache": "abs-ai-hub/store/official-apps.json",
      "enabled": true,
      "auto_update": true
    },
    {
      "id": "github-community",
      "name": "Community Apps (GitHub)",
      "type": "third-party",
      "url": "https://github.com/community/abs-apps",
      "enabled": true
    },
    {
      "id": "my-repos",
      "name": "My Self-Developed Apps",
      "type": "self-developed",
      "path": "file:///home/user/my-abs-apps/",
      "enabled": true
    }
  ]
}
```

### Store Aggregation API

**Future Endpoint**: `GET /api/store/apps`

- Aggregates apps from all enabled sources
- Caches results locally
- Returns unified list of available apps
- Indicates which apps are already installed

---

## UI/UX Design

### Hub Dashboard - Two Main Tabs

The Hub Dashboard uses a simple, discoverable two-tab navigation pattern:

```
┌─────────────────────────────────────────────────────┐
│  ABS AI Hub                                         │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────┐  ┌──────────────────┐        │
│  │   🧩 My Assets   │  │  🛍️ App Store    │        │
│  └──────────────────┘  └──────────────────┘        │
│         ▲                    ▲                        │
│         │ Selected           │                        │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Design Philosophy:**
- **My Assets**: Everything installed and running (apps, models, tools, services, datasets, secrets)
- **App Store**: Where to find and install new apps
- Mimics familiar App Store + Installed Apps experience

---

### App Store Page Layout

**Modern Marketplace-Style Interface:**

```
┌─────────────────────────────────────────────────────────────┐
│  App Store                                    🔍 [Search]   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [🔍 Search: "contract" or "LLM"                   ]        │
│                                                              │
│  ┌───────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ Official Store│ │  Community   │ │   My Apps    │        │
│  │   ● Selected  │ │              │ │              │        │
│  └───────────────┘ └──────────────┘ └──────────────┘        │
│                                                              │
│  ⚖️ Legal & Compliance                                      │
│  ┌────────────────────────────┐ ┌──────────────────────────┐
│  │ Contract Reviewer v2        │ │ Legal Assistant          │
│  │ 📄 [Icon]                   │ │ ⚖️ [Icon]                │
│  │                             │ │                          │
│  │ ⭐ 4.8 | Docker | 1.2GB    │ │ ⭐ 4.6 | Python | 800MB  │
│  │ Professional AI-powered     │ │ AI tool for legal        │
│  │ contract analysis           │ │ document review...       │
│  │                             │ │                          │
│  │ ✅ Verified  [Details] [Install]│ ✅ Verified [Details] [Install]│
│  └────────────────────────────┘ └──────────────────────────┘
│                                                              │
│  🤖 AI Tools                                                 │
│  ┌────────────────────────────┐ ┌──────────────────────────┐
│  │ RAG PDF Voice               │ │ OCR Parser               │
│  │ 📋 [Icon]                   │ │ 📸 [Icon]                │
│  │ RAG application for         │ │ Text extraction from      │
│  │ conversational voice PDF... │ │ images and scanned...    │
│  │ ✅ Verified [Details] [Install]│ 👥 Community [Details] [Install]│
│  └────────────────────────────┘ └──────────────────────────┘
│                                                              │
│  💡 Recommended for You                                      │
│  "Since you installed Contract Reviewer, you may also like:" │
│  [Legal Clause Extractor] [Deposition Summarizer]           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**App Card Components:**

Each app card includes:
- **Icon**: Visual representation of the app
- **Name**: App title
- **Category**: App category (Legal, AI Tools, etc.)
- **Short Description**: Brief overview
- **Badges**:
  - ✅ **Verified**: ABS official apps (trusted)
  - 👥 **Community**: Third-party, security-scanned
  - ⚠️ **Unknown**: Unverified third-party
  - 🟢 **Installed**: Already installed
  - ⬆️ **Update**: Update available (shows version)
  - 🧱 **Dependency Missing**: Required dependencies not installed
- **Metadata**: Rating (⭐), Technology (Docker/Python), Size (GB)
- **Actions**:
  - `[Details]`: Opens app detail modal/page
  - `[Install]`: Installs the app (changes to `[Open]` if installed)
  - `[Update]`: Updates to latest version (if update available)

**Sub-Navigation Tabs:**
- **Official Store**: ABS pre-configured, curated apps
- **Community**: Third-party and community-contributed apps
- **My Apps**: User's self-developed apps

---

### App Detail Modal / Page

When user clicks `[Details]`, opens a modal or dedicated page:

```
┌─────────────────────────────────────────────────────────────┐
│  Contract Reviewer v2                          [Close] ✕  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐  ┌────────────────────────────────────────┐   │
│  │         │  │  Contract Reviewer v2                  │   │
│  │   📄    │  │  ⭐ 4.8 | ✅ Verified | Latest: 2.2.0  │   │
│  │  Icon   │  │  By: ABS Team | Legal & Compliance    │   │
│  │         │  │                                        │   │
│  │         │  │  📸 Screenshots:                      │   │
│  │         │  │  [Screenshot 1] [Screenshot 2] [...]  │   │
│  │         │  │                                        │   │
│  │         │  │  📝 Description:                      │   │
│  │         │  │  Professional AI-powered contract      │   │
│  │         │  │  analysis platform with modern         │   │
│  │         │  │  three-panel interface...               │   │
│  │         │  │                                        │   │
│  │         │  │  📚 Version History:                  │   │
│  │         │  │  v2.2.0 (Latest) - New features...      │   │
│  │         │  │  v2.1.0 - Bug fixes...                 │   │
│  │         │  │  v2.0.0 - Initial release              │   │
│  └─────────┘  └────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  📋 Requirements                                    │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  CPU: 2 cores                                        │  │
│  │  Memory: 4GB                                        │  │
│  │  Disk: 1GB                                           │  │
│  │                                                      │  │
│  │  Dependencies:                                       │  │
│  │  ✅ PostgreSQL (Installed)                          │  │
│  │  ✅ Qdrant (Installed)                               │  │
│  │  ❌ Redis (Missing) [Install Dependency]              │  │
│  │                                                      │  │
│  │  ⚠️ This app depends on Qdrant and PostgreSQL.     │  │
│  │  Install missing dependencies first.                 │  │
│  │                                                      │  │
│  │  [Status: 🟢 Running] (if installed)                 │  │
│  │  [Health Check: ✅ Healthy]                          │  │
│  │                                                      │  │
│  │  [Install] or [Update] or [Open]                     │  │
│  │  [Rollback to v2.1.0] (if update available)         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Detail Page Structure:**
- **Left Panel**: App logo, name, author, rating, badges
- **Main Area**: 
  - Screenshots carousel
  - Full description
  - Version history with changelog
  - Reviews/ratings (future)
- **Right Sidebar**:
  - Requirements (CPU, memory, disk)
  - Dependency list with status
  - Dependency installation prompt if missing
  - Install/Update/Open button
  - Health check status (if installed)
  - Rollback option (if update available)

---

### My Assets Page

Unified asset management view with grid or list layout:

```
┌─────────────────────────────────────────────────────────────┐
│  My Assets                                    🔍 [Search]   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐        │
│  │All │ │Apps│ │Models│ │Services│ │Tools│ │Data│ │Secrets│ │
│  │●   │ │    │ │     │ │        │ │    │ │   │ │       │ │
│  └────┘ └────┘ └─────┘ └────────┘ └────┘ └────┘ └───────┘ │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Asset Type │ Name           │ Status  │ Version │ Actions│ │
│  ├──────────────────────────────────────────────────────┤  │
│  │ 📱 App     │ Contract       │ 🟢Running│ 2.1.0  │ ⚙️ ⬆️ 📄│ │
│  │            │ Reviewer       │          │        │ Stop │ │
│  │            │                │          │        │Update│ │
│  │            │                │          │        │ Logs │ │
│  ├──────────────────────────────────────────────────────┤  │
│  │ 🤖 Model   │ Llama3.2:3b    │ 🟢Ready  │ latest │ 🔄   │ │
│  │            │                │          │        │Reload│ │
│  ├──────────────────────────────────────────────────────┤  │
│  │ 🔧 Service │ Qdrant         │ 🟢Healthy│ 1.8.1  │ 📄   │ │
│  │            │                │          │        │ Logs │ │
│  ├──────────────────────────────────────────────────────┤  │
│  │ 🛠️ Tool    │ OCR Parser     │ 🟠Stopped│ 0.9.0  │ ▶️   │ │
│  │            │                │          │        │ Start│ │
│  ├──────────────────────────────────────────────────────┤  │
│  │ 📊 Dataset │ Contracts      │ 🟢Active │ 1.0.0  │ 📄🔍│ │
│  │            │ Corpus         │          │        │ View │ │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Quick Stats:                                                 │
│  • 5 Apps Running | 1 Stopped | 2 Updates Available         │
│  • 3 Models Ready | 4 Services Healthy                       │
│  • 1 Dependency Issue                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**My Assets Features:**

1. **Filter Tabs**: All | Apps | Models | Services | Tools | Datasets | Secrets
2. **Table/Grid View**: 
   - Asset type icon
   - Asset name
   - Status badge (🟢 Running, ⚙️ Stopped, 🟠 Error, ⬆️ Update)
   - Current version
   - Quick actions (Start, Stop, Update, Logs, Edit, Delete)
3. **Status Indicators**:
   - 🟢 **Running/Ready/Healthy**: Asset is active
   - ⚙️ **Stopped**: Asset installed but not running
   - ⬆️ **Update**: New version available
   - 🟠 **Error**: Asset has errors
   - 🧱 **Dependency Missing**: Required dependencies not installed
4. **Quick Stats**: Overview of asset health and status
5. **Bulk Actions**: Select multiple assets for batch operations

**Asset Detail Panel:**
- Click asset row to expand details
- View full configuration, policy, health metrics
- Edit asset properties
- View logs and metrics
- Manage lifecycle

---

### Smart Recommendation Section

**Location**: Below the App Store grid

```
┌─────────────────────────────────────────────────────────────┐
│  💡 Recommended for You                                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  "Since you installed Contract Reviewer, you may also like:" │
│                                                              │
│  ┌─────────────────────┐ ┌─────────────────────┐         │
│  │ Legal Clause         │ │ Deposition          │         │
│  │ Extractor            │ │ Summarizer          │         │
│  │ ⭐ 4.5 | Verified    │ │ ⭐ 4.7 | Verified   │         │
│  │                      │ │                     │         │
│  │ Extract legal clauses│ │ Summarize deposition│         │
│  │ from contracts...    │ │ transcripts...      │         │
│  │                      │ │                     │         │
│  │ [Details] [Install]  │ │ [Details] [Install] │         │
│  └─────────────────────┘ └─────────────────────┘         │
│                                                              │
│  "Apps that integrate with Qdrant:"                          │
│  [Vector Search App] [Document Analyzer]                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Recommendation Types:**
- **Similar Apps**: Based on category and tags
- **Integration Suggestions**: "Apps that work with [Service]"
- **Usage Patterns**: "Users who installed X also installed Y"
- **Complementary Tools**: Related apps that enhance workflow

---

### Future UI Enhancements

#### 1. Dependency Visualizer

Interactive graph showing relationships:

```
┌─────────────────────────────────────────────────────────────┐
│  Dependency Graph                           [Zoom] [Export] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│           Contract Reviewer v2                              │
│                    │                                        │
│          ┌─────────┼─────────┐                             │
│          │         │         │                             │
│      PostgreSQL  Qdrant   Redis                           │
│          │         │         │                             │
│      [Running] [Running] [Missing]                         │
│                                                              │
│  Click to view details or install missing dependencies     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### 2. App Update Center

Dedicated update management interface:

```
┌─────────────────────────────────────────────────────────────┐
│  Update Center                                [Update All]   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  2 Updates Available                                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Contract Reviewer v2                                   │  │
│  │ Current: 2.1.0 → Latest: 2.2.0                        │  │
│  │                                                       │  │
│  │ 📝 Changelog:                                         │  │
│  │ • New: Enhanced document analysis                     │  │
│  │ • Fixed: Memory leak in vector search                │  │
│  │ • Improved: UI responsiveness                         │  │
│  │                                                       │  │
│  │ [View Full Changelog] [Update] [Rollback to 2.1.0]   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Deposition Summarizer                                  │  │
│  │ Current: 1.0.0 → Latest: 1.1.5                        │  │
│  │ [View Changelog] [Update] [Skip]                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### 3. One-Click Reinstall/Rollback

Versioned backups enable quick rollback:

- Rollback to previous version via UI
- Version history stored in `catalog.json`
- Backup snapshots before updates
- One-click restore from backup

#### 4. CLI Integration

Command-line interface for power users:

```bash
# Install app
abs install contract-reviewer-v2

# Update app
abs update contract-reviewer-v2

# List installed apps
abs list

# Start/stop app
abs start contract-reviewer-v2
abs stop contract-reviewer-v2

# View app status
abs status contract-reviewer-v2

# Install with dependencies
abs install contract-reviewer-v2 --with-dependencies
```

---

## UI Design Principles

1. **Simplicity**: Two main tabs (My Assets, App Store) for clarity
2. **Discoverability**: Search, categories, filters make finding apps easy
3. **Visual Feedback**: Status badges, icons, colors convey information quickly
4. **Familiarity**: Mimics known app store patterns users already understand
5. **Consistency**: Unified design language across all views
6. **Accessibility**: Keyboard navigation, screen reader support, clear labels

---

## Enhanced Features

### 1. Dependency Resolution Layer

**Automated Dependency Management:**
- Pre-installation dependency detection
- Missing service identification (PostgreSQL, Qdrant, etc.)
- One-click "Install Dependencies" button
- Dependency graph visualization in UI
- Automatic dependency installation option

**Implementation:**
- Dependency resolver scans `requirements.services` from app manifest
- Checks against `catalog.json` for installed services
- Displays visual dependency graph
- Offers to install missing dependencies before app installation
- Tracks dependency relationships for uninstall safety

**Example Dependency Graph:**
```
Contract Reviewer v2
├── PostgreSQL (✅ Installed)
├── Qdrant (✅ Installed)
└── Redis (❌ Missing - Click to Install)
```

### 2. Versioning and Update Management

**Version Tracking:**
- Store latest version information in `catalog.json`
- Compare installed version with store version
- Track update availability per app
- Changelog integration

**Update Capabilities:**
- "Update Available" badges in UI
- One-click update to latest version
- Rollback to previous version
- Update history tracking
- Changelog preview before updating

**Asset Schema Enhancement:**
```json
{
  "updates": {
    "latest_version": "2.2.0",
    "current_version": "2.1.0",
    "update_available": true,
    "update_source": "git://github.com/abs-ai/app.git",
    "changelog": "https://github.com/abs-ai/app/releases/tag/v2.2.0",
    "update_history": [
      { "version": "2.1.0", "installed": "2024-01-10", "rolled_back": false }
    ]
  }
}
```

**API Endpoints:**
- `POST /api/apps/{id}/update` - Update to latest version
- `POST /api/apps/{id}/rollback` - Rollback to previous version
- `GET /api/apps/updates` - List all available updates

### 3. Sandboxing and Security Policy

**Security Scanning:**
- Pre-installation Dockerfile/manifest scanning
- Detect risky instructions (privileged mode, host networking, etc.)
- Container security policy enforcement
- Trust badge system

**Trust Levels:**
- ✅ **Verified**: ABS official apps (trusted)
- 👥 **Community**: Third-party apps that passed security scan
- ⚠️ **Unknown**: Unverified third-party apps (warning required)

**Implementation:**
```json
{
  "security": {
    "trust_level": "verified" | "community" | "unknown",
    "source_type": "abs-official" | "third-party" | "self-developed",
    "scan_status": "passed" | "failed" | "pending",
    "badge": "verified" | "community" | "unknown",
    "scan_results": {
      "risky_instructions": [],
      "network_isolation": true,
      "resource_limits": true
    }
  }
}
```

**Sandboxing Options:**
- Limited container network (optional isolated network)
- Resource limits enforcement
- Security policy per app (via Asset Management)
- Warning dialogs for untrusted apps

### 4. AI-Powered Recommendations

**Personalized App Suggestions:**
- Analyze user's installed apps and usage patterns
- Collaborative filtering based on app categories and tags
- Tag-based recommendations
- Integration suggestions (e.g., "Apps that work with Qdrant")

**Recommendation Engine:**
```javascript
// Pseudocode
function getRecommendations(userInstalledApps, storeApps) {
  // Extract categories and tags from installed apps
  const userCategories = extractCategories(userInstalledApps);
  const userTags = extractTags(userInstalledApps);
  
  // Find similar apps
  const recommendations = storeApps
    .filter(app => !userInstalledApps.includes(app.id))
    .map(app => ({
      app,
      score: calculateSimilarity(app, userCategories, userTags)
    }))
    .sort((a, b) => b.score - a.score)
    .slice(0, 5);
  
  return recommendations;
}
```

**UI Integration:**
- "Recommended for You" section on App Store
- Personalized suggestions in Hub Dashboard
- Context-aware recommendations based on current app usage
- "Users who installed X also installed Y" feature

### 5. App Store Submission Portal

**Developer Submission Workflow:**
- "Submit Your App" form in App Store UI
- Manifest validation before submission
- Automated pipeline checks:
  - Validate `app.manifest.json` structure
  - Verify Dockerfile builds successfully
  - Check for security issues
  - Validate required fields
- Pull request flow for community submissions
- Approval process for ABS official store

**Submission Requirements:**
```json
{
  "submission": {
    "manifest_validation": {
      "status": "passed",
      "errors": [],
      "warnings": []
    },
    "docker_build": {
      "status": "success",
      "logs": "..."
    },
    "security_scan": {
      "status": "passed",
      "issues": []
    },
    "status": "pending_review" | "approved" | "rejected"
  }
}
```

**Submission API:**
- `POST /api/store/submit` - Submit new app
- `GET /api/store/submissions` - View submission status
- `POST /api/store/submissions/{id}/approve` - Approve submission (admin)

### 6. Visual Dashboard Integration

**Dashboard Cards:**
- **Installed Apps Card**: Grid view of installed apps with status badges
- **Available Updates Card**: List of apps with updates available
- **Dependency Issues Card**: Apps with missing dependencies
- **Recently Installed**: Recently added apps

**Status Badges:**
- 🟢 **Running**: App is currently running
- ⚙️ **Stopped**: App is installed but stopped
- ⬆️ **Update**: Update available (shows version)
- 🧱 **Dependency Missing**: Required dependencies not installed
- ⚠️ **Error**: App has errors (click to view logs)

**Category Navigation:**
- Visual category tabs: Legal | NLP | Vision | DevTools | All
- Filter apps by category
- Category-based recommendations
- Quick category stats (e.g., "5 Legal Apps installed")

**Enhanced App Cards:**
```
┌─────────────────────────┐
│  Contract Reviewer v2    │
│  🟢 Running  ⬆️ 2.2.0    │
│  Legal Apps              │
│  [View] [Update] [Stop]  │
└─────────────────────────┘
```

**Real-time Updates:**
- WebSocket connection for live status updates
- Push notifications for app status changes
- Update notifications
- Dependency resolution status

---

## Summary

**Assets Repository** = Central control of everything installed on the local machine (apps, models, services, tools, datasets, secrets). Managed through Asset Management system.

**App Store** = Discovery mechanism where users browse and find apps from:
- ABS pre-configured store (maintained by ABS)
- Third-party sources (community, external repos)
- Self-developed apps (user's own apps)

**Workflow**: User browses Store → Installs app → App becomes Asset → Managed centrally through Asset system → Physically deployed on machine

**Enhanced Capabilities:**
- 🔗 **Dependency Resolution**: Automated dependency detection and installation
- 📦 **Version Management**: Update tracking, rollback, changelog
- 🔒 **Security**: Trust badges, security scanning, sandboxing
- 🤖 **AI Recommendations**: Personalized app suggestions
- 📝 **Submission Portal**: Developer app submission workflow
- 📊 **Visual Dashboard**: Enhanced UI with status badges and categories

This architecture provides clear separation: Assets = what you have installed (controlled), Store = where you find new apps (discovery), enhanced with modern features for dependency management, security, and user experience.
