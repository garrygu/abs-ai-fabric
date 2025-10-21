# Contract Reviewer v2 - Deployment Options

## 🎯 **Deployment Architecture Overview**

The Contract Reviewer v2 application supports multiple deployment patterns depending on your needs:

### **📁 File Structure**
```
abs-ai-hub/apps/
├── contract-reviewer-v2/
│   ├── docker-compose.yml                    # Single app deployment
│   ├── docker-compose-host-mount.yml         # Single app with host mounting
│   └── ...
├── docker-compose-shared-volumes.yml         # Multi-app deployment
└── ...
```

## 🚀 **Deployment Options**

### **Option 1: Single App Deployment** (Recommended for Development)
**File**: `contract-reviewer-v2/docker-compose.yml`
**Purpose**: Deploy ONLY Contract Reviewer v2
**Use Case**: Development, testing, single-app production

```bash
cd abs-ai-hub/apps/contract-reviewer-v2
docker-compose up -d
```

**Features**:
- ✅ Contract Reviewer v2 only
- ✅ App-specific file storage volumes
- ✅ Connects to CORE services (Redis, PostgreSQL, Qdrant)
- ✅ Port: 8082

### **Option 2: Single App with Host Mounting**
**File**: `contract-reviewer-v2/docker-compose-host-mount.yml`
**Purpose**: Deploy Contract Reviewer v2 with direct host directory access
**Use Case**: Development with easy file access

```bash
cd abs-ai-hub/apps/contract-reviewer-v2
docker-compose -f docker-compose-host-mount.yml up -d
```

**Features**:
- ✅ Contract Reviewer v2 only
- ✅ Direct host directory mounting (`./data/`)
- ✅ Easy file access from host system
- ✅ Port: 8082

### **Option 3: Multi-App Deployment** (Recommended for Production)
**File**: `apps/docker-compose-shared-volumes.yml`
**Purpose**: Deploy multiple apps with shared document storage
**Use Case**: Production with centralized document hub

```bash
cd abs-ai-hub/apps
docker-compose -f docker-compose-shared-volumes.yml up -d
```

**Features**:
- ✅ Contract Reviewer v2 (port 8082)
- ✅ Legal Assistant (port 8083)
- ✅ RAG PDF Voice (port 8084)
- ✅ Onyx Suite (port 8085)
- ✅ Shared document storage across all apps
- ✅ Centralized document hub

## 🏗️ **Core Services Dependency**

All deployment options rely on **CORE services** managed by the gateway:

### **Required Core Services**:
- **Redis**: `abs-redis:6379`
- **PostgreSQL**: `document-hub-postgres:5432`
- **Qdrant**: `abs-qdrant:6333`
- **Hub Gateway**: `abs-hub-gateway:8081`

### **Start Core Services First**:
```bash
cd core
docker-compose -f core.yml up -d
```

## 🔧 **Configuration Differences**

| Option | Apps | Storage | Ports | Use Case |
|--------|------|---------|-------|----------|
| Single App | Contract Reviewer v2 only | App-specific volumes | 8082 | Development |
| Host Mount | Contract Reviewer v2 only | Host directories | 8082 | Development |
| Multi-App | All apps | Shared volumes | 8082-8085 | Production |

## 📋 **Quick Start Guide**

### **For Development**:
```bash
# 1. Start core services
cd core
docker-compose -f core.yml up -d

# 2. Start Contract Reviewer v2 only
cd ../abs-ai-hub/apps/contract-reviewer-v2
docker-compose up -d

# 3. Access app
open http://localhost:8082
```

### **For Production**:
```bash
# 1. Start core services
cd core
docker-compose -f core.yml up -d

# 2. Start all apps with shared storage
cd ../abs-ai-hub/apps
docker-compose -f docker-compose-shared-volumes.yml up -d

# 3. Access apps
open http://localhost:8082  # Contract Reviewer v2
open http://localhost:8083  # Legal Assistant
open http://localhost:8084  # RAG PDF Voice
open http://localhost:8085  # Onyx Suite
```

## 🔍 **Monitoring**

All services are managed by the Hub Gateway:
- **Gateway UI**: http://localhost:8081
- **Service Status**: http://localhost:8081/api/services/status
- **Health Checks**: http://localhost:8081/api/health

## 📝 **Notes**

- **No Duplicate Services**: Apps connect to CORE services, don't start their own
- **External Network**: All apps use `abs-net` external network
- **Gateway Management**: Core services managed by `abs-hub-gateway`
- **Data Persistence**: All data persists across container restarts
- **Scalability**: Easy to add new apps to multi-app deployment
