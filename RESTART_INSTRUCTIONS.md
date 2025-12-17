# Restart Instructions for App Store Feature

## Services That Need to Be Restarted

After implementing the App Store feature, you need to restart the following services:

### 1. **Hub Gateway** (REQUIRED)
**Container:** `abs-core-hub-gateway`

**Reason:** 
- Added new Python module: `core/gateway/store_service.py`
- Modified: `core/gateway/app.py` (added new API endpoints)
- The container needs to be **rebuilt** to include the new code

**Commands:**
```powershell
# Option 1: Restart core services (rebuilds gateway)
cd C:\ABS\core
docker compose -f core.yml --env-file .env down
docker compose -f core.yml --env-file .env up -d --build

# Option 2: Just rebuild and restart the gateway
cd C:\ABS\core
docker compose -f core.yml build hub-gateway
docker compose -f core.yml restart hub-gateway

# Option 3: Quick restart (if container already has code via volume mount)
docker restart abs-core-hub-gateway
```

**Note:** Since the gateway is built from `./gateway` directory, you may need to rebuild if `store_service.py` isn't being picked up automatically.

### 2. **Hub UI** (RECOMMENDED)
**Container:** `abs-hub-ui`

**Reason:**
- Added new HTML file: `app-store.html`
- Modified: `index.html` (added navigation tabs)
- Since it uses volume mount (`./assets:/usr/share/nginx/html:ro`), changes are usually picked up automatically
- But a restart ensures everything is fresh

**Commands:**
```powershell
# Navigate to hub-ui directory
cd C:\ABS\abs-ai-hub\hub-ui

# Restart the UI container
docker compose restart hub-ui

# Or if not using compose:
docker restart abs-hub-ui
```

### 3. **Verify Services Are Running**

```powershell
# Check gateway status
docker ps | findstr "hub-gateway"

# Check UI status  
docker ps | findstr "hub-ui"

# Check gateway logs for errors
docker logs abs-core-hub-gateway --tail 50

# Check if new API endpoints are available
curl http://localhost:8081/api/store/apps
```

## Quick Restart All

If you want to restart everything at once:

```powershell
# Restart core services (including gateway)
cd C:\ABS\core
.\stop-core.ps1
.\start-core.ps1

# Restart Hub UI
cd C:\ABS\abs-ai-hub\hub-ui
docker compose restart hub-ui
```

## Troubleshooting

### If Gateway doesn't start:
1. Check logs: `docker logs abs-core-hub-gateway`
2. Look for import errors related to `store_service`
3. Verify `store_service.py` exists in `core/gateway/` directory
4. May need to rebuild: `docker compose -f core.yml build hub-gateway`

### If Store API returns 503:
- Gateway might not have loaded `store_service`
- Check logs for initialization messages
- Verify `StoreService` is being imported correctly

### If UI doesn't show new pages:
- Clear browser cache
- Check nginx logs: `docker logs abs-hub-ui`
- Verify files exist in `abs-ai-hub/hub-ui/assets/`



