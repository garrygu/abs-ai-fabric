# Migration to Unified Access Pattern

## Overview

We've restructured the ABS AI Hub to use a unified access pattern where all applications are accessible through a single entry point (`http://localhost:3000`) with path-based routing.

## What Changed

### Before (Port-based Access)
```
http://localhost:3000      → Hub UI
http://localhost:8000      → Onyx (in core/)
http://localhost:8080      → Open WebUI
http://localhost:7860      → Contract Reviewer
http://localhost:8080      → RAG PDF Voice
```

### After (Path-based Access)
```
http://localhost:3000/              → Hub UI
http://localhost:3000/onyx/         → Onyx (moved to apps/)
http://localhost:3000/openwebui/    → Open WebUI
http://localhost:3000/contract/     → Contract Reviewer
http://localhost:3000/rag/          → RAG PDF Voice
```

## Architecture Changes

### 1. Onyx Moved from Core to Apps
**Before:**
- Location: `core/onyx/`
- Defined in: `core/core.yml`
- Purpose: Treated as core service

**After:**
- Location: `abs-ai-hub/apps/onyx/`
- Defined in: `abs-ai-hub/apps/onyx/docker-compose.yml`
- Purpose: User-facing application (correct!)

**Rationale:** Onyx is an application that *consumes* core services, not a core service itself.

### 2. Hub UI as Reverse Proxy
The Hub UI now uses Nginx to route traffic to backend applications:

```
Hub UI (nginx) → Route by path → Backend Apps
    ↓
abs-net (Docker network)
    ↓
Core Services (Ollama, Qdrant, Redis, Gateway)
```

### 3. Added Open WebUI
New application for power users with advanced features:
- Multi-model chat interface
- Document attachments
- Conversation management
- Custom agents and prompts

## Migration Steps

### Step 1: Stop Old Services
```bash
# Stop Onyx from core
cd core
docker-compose down onyx

# Or stop all core services
docker-compose down
```

### Step 2: Clean Up Old Onyx
```bash
# Remove old Onyx image (optional)
docker rmi abs-onyx-v2

# Keep the volume if you want to preserve data
# docker volume rm abs-onyx-data
```

### Step 3: Start Core Services (without Onyx)
```bash
cd core
docker-compose up -d
```

### Step 4: Start Hub UI with New Configuration
```bash
cd abs-ai-hub/hub-ui
docker-compose up -d
```

### Step 5: Start Applications
```bash
# Start Onyx
cd abs-ai-hub/apps/onyx
docker-compose up -d

# Start Open WebUI
cd ../open-webui
docker-compose up -d

# Start other apps as needed
cd ../contract-reviewer
docker-compose up -d

cd ../rag-pdf-voice
docker-compose up -d
```

### Step 6: Verify Access
```bash
# Check all containers are running
docker ps

# Test endpoints
curl http://localhost:3000/              # Hub UI
curl http://localhost:3000/onyx/health   # Onyx
curl http://localhost:3000/api/health    # Gateway via proxy
```

## Configuration Files Changed

### 1. `core/core.yml`
**Removed:**
- `onyx` service definition
- `onyx_data` volume
- Onyx dependencies from hub-gateway

### 2. `abs-ai-hub/hub-ui/docker-compose.yml`
**Updated:**
- Added nginx configuration mount
- Added error pages mount

### 3. `abs-ai-hub/hub-ui/nginx.conf` (NEW)
**Created:**
- Reverse proxy configuration
- Upstream definitions for all apps
- Path-based routing rules
- WebSocket support
- Error handling

### 4. `abs-ai-hub/hub-ui/assets/index.html`
**Updated:**
- Changed all app links from `http://localhost:[port]` to `/[app]/`
- Added Open WebUI card
- Removed `target="_blank"` (no longer opening new tabs)

### 5. `abs-ai-hub/apps/onyx/docker-compose.yml` (NEW)
**Created:**
- Standalone Onyx application
- Connects to abs-net
- Wait for core services
- Independent lifecycle

### 6. `abs-ai-hub/apps/open-webui/docker-compose.yml` (NEW)
**Created:**
- Open WebUI application
- Connects to Ollama via abs-net
- Data persistence

## Benefits of This Architecture

### 1. **Logical Separation**
- **Core** = Infrastructure (Ollama, Qdrant, Redis, Gateway)
- **Apps** = User-facing applications (Onyx, Open WebUI, etc.)

### 2. **Unified Access**
- Single entry point (port 3000)
- Path-based routing (easier to remember)
- Consistent URL structure

### 3. **Better Scalability**
- Easy to add new applications
- Applications are independent
- Can start/stop apps without affecting others

### 4. **Production Ready**
- Single SSL certificate needed
- Easier reverse proxy setup
- Better for domain mapping

### 5. **Security**
- Single point of authentication (future)
- Centralized access control
- Network isolation maintained

## Troubleshooting

### Issue: "502 Bad Gateway" when accessing `/onyx/`
**Cause:** Onyx container not running or still starting up

**Solution:**
```bash
# Check if Onyx is running
docker ps | grep abs-onyx

# Check Onyx logs
cd abs-ai-hub/apps/onyx
docker-compose logs -f

# Restart Onyx
docker-compose restart
```

### Issue: Old Onyx still responding on port 8000
**Cause:** Old Onyx container from core/ still running

**Solution:**
```bash
# Stop old Onyx
docker stop abs-onyx
docker rm abs-onyx

# Verify it's gone
docker ps -a | grep onyx
```

### Issue: Nginx routing not working
**Cause:** Hub UI using old configuration

**Solution:**
```bash
# Restart Hub UI
cd abs-ai-hub/hub-ui
docker-compose restart

# Check nginx logs
docker-compose logs -f
```

### Issue: "404 Not Found" for all apps
**Cause:** Apps not connected to abs-net

**Solution:**
```bash
# Check network
docker network inspect abs-net

# Verify apps are on the network
docker inspect abs-onyx | grep -i network
```

## Rollback Procedure

If you need to rollback to the old architecture:

1. **Stop new setup:**
   ```bash
   cd abs-ai-hub/apps/onyx
   docker-compose down
   
   cd abs-ai-hub/hub-ui
   docker-compose down
   ```

2. **Restore Onyx to core:**
   ```bash
   # Copy onyx back (if you deleted it)
   cp -r abs-ai-hub/apps/onyx core/onyx
   ```

3. **Restore core.yml:**
   Use git to restore the old version:
   ```bash
   git checkout HEAD~1 core/core.yml
   ```

4. **Start old setup:**
   ```bash
   cd core
   docker-compose up -d
   ```

## Next Steps

1. **Test all applications** through the new routing
2. **Update bookmarks** to use new URLs
3. **Consider adding authentication** to Hub UI
4. **Add more applications** (Jupyter, Dify, etc.)
5. **Configure SSL** for production use

## Support

If you encounter issues:
1. Check `docker ps` - ensure all containers are running
2. Check logs - `docker-compose logs -f` in each app directory
3. Check network - `docker network inspect abs-net`
4. Verify nginx config - `docker exec abs-hub-ui nginx -t`

---

**Migration Date:** October 2025  
**Version:** 2.0 (Unified Access Pattern)

