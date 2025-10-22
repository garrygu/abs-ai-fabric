# ABS Unified Framework

## Overview

The ABS Unified Framework provides a consistent, Microsoft 365-style app launcher and unified header across all ABS applications. It uses a **centralized architecture** where framework files are served from the Hub UI (port 3000) and dynamically loaded by individual applications, eliminating code duplication and providing centralized configuration management.

## Architecture

### Centralized Components

1. **Hub UI (Port 3000)** - Centralized Framework Server
   - Serves `unified-framework.js` from `/usr/share/nginx/html/`
   - Serves `apps-registry.json` for dynamic app discovery
   - Provides CORS headers for cross-origin requests
   - Single source of truth for all framework assets

2. **Individual Applications** - Framework Consumers
   - Load framework dynamically from Hub UI
   - Use `framework-config.js` for app-specific configuration
   - No local framework files (eliminates duplication)
   - Environment variable configuration for flexible deployment

### Framework Files

1. **Unified Framework JavaScript** (`hub-ui/assets/unified-framework.js`)
   - Core framework functionality
   - App launcher with search
   - Unified header with customizable menu items
   - App switching and navigation
   - Alpine.js integration and HTML injection

2. **App Registry JSON** (`hub-ui/assets/apps-registry.json`)
   - Centralized app definitions
   - App metadata and configuration
   - Category and tag management
   - Single source of truth for all apps

3. **App Configuration Template** (`apps/*/static/framework-config.js`)
   - Generic configuration template
   - Dynamic framework loading from Hub UI
   - Fallback mechanisms for reliability
   - Environment variable integration

## Usage

### For New Apps

1. **Include Framework Configuration Script**
   ```html
   <script src="/static/framework-config.js"></script>
   ```

2. **Configure Environment Variables** (in `docker-compose.yml`)
   ```yaml
   environment:
     - ABS_FRAMEWORK_PATH=http://localhost:3000/unified-framework.js
     - ABS_GATEWAY_URL=http://localhost:8081
     - ABS_APP_REGISTRY_URL=http://localhost:3000/apps-registry.json
   ```

3. **Add App to Registry** (in `hub-ui/assets/apps-registry.json`)
   ```json
   {
     "apps": {
       "your-app-id": {
         "name": "Your App Name",
         "description": "Your app description",
         "icon": "fas fa-your-icon",
         "colorClass": "bg-your-color",
         "url": "/your-app-url",
         "status": "active",
         "version": "1.0.0",
         "category": "your-category",
         "tags": ["tag1", "tag2"],
         "permissions": ["read", "write"],
         "config": {
           "enableExport": true,
           "enableSettings": true,
           "customMenuItems": []
         }
       }
     }
   }
   ```

4. **Implement App-Specific Functions** (in your app's HTML)
   ```javascript
   window.openAppSettings = () => {
       // Your settings logic
   };
   
   window.exportAppResults = () => {
       // Your export logic
   };
   ```

### For Existing Apps

1. **Remove Local Framework Files**
   - Delete `static/unified-framework.js` (if exists)
   - Delete `static/apps-registry.json` (if exists)
   - Remove hardcoded framework HTML from your app

2. **Add Framework Configuration Script**
   ```html
   <script src="/static/framework-config.js"></script>
   ```

3. **Configure Environment Variables** (in `docker-compose.yml`)
   ```yaml
   environment:
     - ABS_FRAMEWORK_PATH=http://localhost:3000/unified-framework.js
     - ABS_GATEWAY_URL=http://localhost:8081
     - ABS_APP_REGISTRY_URL=http://localhost:3000/apps-registry.json
   ```

4. **Update Backend** (in your FastAPI app)
   ```python
   # Inject environment variables into HTML
   ABS_FRAMEWORK_PATH = os.getenv("ABS_FRAMEWORK_PATH", "http://localhost:3000/unified-framework.js")
   ABS_GATEWAY_URL = os.getenv("ABS_GATEWAY_URL", "http://localhost:8081")
   ABS_APP_REGISTRY_URL = os.getenv("ABS_APP_REGISTRY_URL", "http://localhost:3000/apps-registry.json")
   
   @app.get("/")
   async def serve_frontend():
       with open("static/index.html", "r", encoding="utf-8") as f:
           html_content = f.read()
       
       env_script = f"""
       <script>
           window.ABS_FRAMEWORK_PATH = "{ABS_FRAMEWORK_PATH}";
           window.ABS_GATEWAY_URL = "{ABS_GATEWAY_URL}";
           window.ABS_APP_REGISTRY_URL = "{ABS_APP_REGISTRY_URL}";
       </script>
       """
       html_content = html_content.replace("</head>", f"{env_script}</head>")
       
       return HTMLResponse(content=html_content)
   ```

5. **Add App to Registry** (in `hub-ui/assets/apps-registry.json`)
   - Add your app definition to the centralized registry

## Configuration Options

### Environment Variables

The framework uses environment variables for configuration:

```yaml
# docker-compose.yml
environment:
  - ABS_FRAMEWORK_PATH=http://localhost:3000/unified-framework.js
  - ABS_GATEWAY_URL=http://localhost:8081
  - ABS_APP_REGISTRY_URL=http://localhost:3000/apps-registry.json
```

### Hub UI Configuration

The Hub UI nginx configuration includes CORS headers:

```nginx
# hub-ui/nginx.conf
location / {
    root /usr/share/nginx/html;
    index index.html index.htm;
    try_files $uri $uri/ /index.html;
    
    # Add CORS headers for cross-origin requests from apps
    add_header 'Access-Control-Allow-Origin' '*' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range' always;
    add_header 'Access-Control-Expose-Headers' 'Content-Length,Content-Range' always;
}
```

### App Registry JSON

```json
{
    "apps": {
        "app-id": {
            "name": "App Name",
            "description": "App Description",
            "icon": "fas fa-icon",
            "colorClass": "bg-color",
            "url": "/app-url",
            "status": "active",
            "version": "1.0.0",
            "category": "category",
            "tags": ["tag1", "tag2"],
            "permissions": ["read", "write"],
            "config": {
                "enableExport": true,
                "enableSettings": true,
                "customMenuItems": []
            }
        }
    }
}
```

## API Endpoints

### App Registry API

- `GET /api/apps` - Get all apps
- `GET /api/apps/{app_id}` - Get specific app
- `POST /api/apps/{app_id}/config` - Update app config
- `GET /api/apps/categories` - Get app categories

## Customization

### Custom Menu Items

Each app can define custom menu items that appear in the unified header:

```javascript
customMenuItems: [
    {
        id: 'export',
        label: 'Export',
        icon: 'fas fa-download',
        class: 'px-4 py-2 bg-blue-600 text-white rounded-md',
        action: () => {
            // App-specific export logic
            if (window.contractReviewer?.exportResults) {
                window.contractReviewer.exportResults();
            }
        }
    }
]
```

### App-Specific Callbacks

The framework provides hooks for app-specific functionality:

```javascript
onAppSwitch: (app) => {
    // Called when user switches to another app
    console.log(`Switching from ${currentApp.name} to ${app.name}`);
    // Save state, show confirmation, etc.
},

onSettingsOpen: () => {
    // Called when settings button is clicked
    if (window.contractReviewer) {
        window.contractReviewer.mainTab = 'settings';
    }
}
```

## Benefits

1. **Centralized Architecture**: Single source of truth for framework files
2. **Zero Duplication**: No local framework files in individual apps
3. **Consistency**: Unified look and feel across all apps
4. **Maintainability**: Update framework once, affects all apps
5. **Scalability**: Easy to add new apps and features
6. **CORS-Safe**: Proper cross-origin resource sharing
7. **Environment-Driven**: Flexible configuration via environment variables
8. **User Experience**: Familiar Microsoft 365-style navigation

## Migration Guide

### From Hardcoded Framework

1. **Remove Hardcoded HTML**
   ```html
   <!-- Remove these sections -->
   <!-- App Launcher Overlay -->
   <!-- App Launcher Menu -->
   <!-- Unified Header -->
   ```

2. **Remove Hardcoded Data**
   ```javascript
   // Remove from Alpine.js data
   showAppLauncher: false,
   appSearchQuery: '',
   currentApp: { ... },
   availableApps: [ ... ],
   ```

3. **Remove Hardcoded Methods**
   ```javascript
   // Remove from Alpine.js methods
   get filteredApps() { ... },
   switchToApp(app) { ... },
   goToGateway() { ... }
   ```

4. **Add Framework Script**
   ```html
   <script src="/static/framework-config.js"></script>
   ```

5. **Configure App**
   ```javascript
   window.ABS_FRAMEWORK_CONFIG = {
       // Your app configuration
   };
   ```

## Troubleshooting

### Common Issues

1. **Framework Not Loading**
   - Check environment variables in `docker-compose.yml`
   - Verify Hub UI is running on port 3000
   - Check browser console for CORS errors
   - Verify `framework-config.js` is included

2. **CORS Errors**
   - Ensure Hub UI nginx has CORS headers configured
   - Check that `Access-Control-Allow-Origin` header is present
   - Verify Hub UI container is restarted after nginx changes

3. **App Not Appearing in Launcher**
   - Verify app is in `hub-ui/assets/apps-registry.json`
   - Check app status is "active"
   - Verify app registry is accessible at `http://localhost:3000/apps-registry.json`

4. **Environment Variables Not Working**
   - Check backend HTML injection is working
   - Verify environment variables are set in `docker-compose.yml`
   - Check browser console for `window.ABS_FRAMEWORK_PATH` values

5. **App Switching Not Working**
   - Verify app URLs are correct in registry
   - Check for JavaScript errors
   - Verify target app is accessible

### Debug Mode

The framework includes comprehensive console logging. Check browser console for:
- `🔧 Framework path: ...`
- `🔧 Gateway URL: ...`
- `🔍 Attempting to load hub app registry...`
- `✅ ABS Unified Framework initialized`

## Future Enhancements

1. **User Preferences**: Save user's favorite apps and layout preferences
2. **App Categories**: Group apps by category in the launcher
3. **Recent Apps**: Show recently used apps
4. **App Search**: Enhanced search with tags and categories
5. **Notifications**: Centralized notification system
6. **Themes**: Customizable color schemes and themes
7. **Mobile Support**: Optimized mobile experience
8. **Offline Support**: Work offline with cached app list
