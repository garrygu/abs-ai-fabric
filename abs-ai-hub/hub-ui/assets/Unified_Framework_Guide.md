# ABS Unified Framework

## Overview

The ABS Unified Framework provides a consistent, Microsoft 365-style app launcher and unified header across all ABS applications. It eliminates the need to hardcode framework components in each app and provides centralized configuration management.

## Architecture

### Components

1. **Unified Framework JavaScript** (`unified-framework.js`)
   - Core framework functionality
   - App launcher with search
   - Unified header with customizable menu items
   - App switching and navigation

2. **App Registry API** (`app-registry-api.py`)
   - Dynamic app list management
   - App configuration storage
   - Category and permission management

3. **App Configuration** (`framework-config.js`)
   - App-specific framework configuration
   - Custom menu items
   - App-specific callbacks

4. **App Registry JSON** (`apps-registry.json`)
   - Centralized app definitions
   - App metadata and configuration
   - Category and tag management

## Usage

### For New Apps

1. **Include Framework Script**
   ```html
   <script src="/static/framework-config.js"></script>
   ```

2. **Configure App**
   ```javascript
   window.ABS_FRAMEWORK_CONFIG = {
       currentApp: {
           id: 'your-app-id',
           name: 'Your App Name',
           description: 'Your app description',
           icon: 'fas fa-your-icon',
           colorClass: 'bg-your-color',
           url: '/your-app-url'
       },
       customMenuItems: [
           {
               id: 'custom-action',
               label: 'Custom Action',
               icon: 'fas fa-icon',
               action: () => { /* your action */ }
           }
       ]
   };
   ```

3. **Implement App-Specific Functions**
   ```javascript
   window.openAppSettings = () => {
       // Your settings logic
   };
   
   window.exportAppResults = () => {
       // Your export logic
   };
   ```

### For Existing Apps

1. **Remove Hardcoded Framework**
   - Remove app launcher HTML
   - Remove unified header HTML
   - Remove framework data from Alpine.js

2. **Add Framework Script**
   ```html
   <script src="/static/framework-config.js"></script>
   ```

3. **Configure App-Specific Settings**
   - Define custom menu items
   - Set up app-specific callbacks
   - Configure framework options

## Configuration Options

### App Configuration

```javascript
{
    // Required: Current app information
    currentApp: {
        id: 'app-id',
        name: 'App Name',
        description: 'App Description',
        icon: 'fas fa-icon',
        colorClass: 'bg-color',
        url: '/app-url'
    },
    
    // Optional: Framework settings
    gatewayUrl: '/',
    appRegistryUrl: '/api/apps',
    enableNotifications: true,
    enableSettings: true,
    enableExport: false,
    
    // Optional: Custom menu items
    customMenuItems: [
        {
            id: 'unique-id',
            label: 'Menu Label',
            icon: 'fas fa-icon',
            class: 'custom-css-class',
            action: () => { /* function */ },
            url: '/custom-url',
            disabled: false
        }
    ],
    
    // Optional: App-specific callbacks
    onAppSwitch: (app) => { /* callback */ },
    onSettingsOpen: () => { /* callback */ },
    onNotification: (notification) => { /* callback */ }
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

1. **Consistency**: Unified look and feel across all apps
2. **Maintainability**: Single source of truth for framework code
3. **Configurability**: App-specific customization without code duplication
4. **Scalability**: Easy to add new apps and features
5. **User Experience**: Familiar Microsoft 365-style navigation

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
   - Check script path: `/static/framework-config.js`
   - Verify `ABS_FRAMEWORK_CONFIG` is defined
   - Check browser console for errors

2. **App Not Appearing in Launcher**
   - Verify app is in `apps-registry.json`
   - Check app status is "active"
   - Verify app registry API is working

3. **Custom Menu Items Not Working**
   - Check `customMenuItems` configuration
   - Verify action functions are defined
   - Check browser console for errors

4. **App Switching Not Working**
   - Verify app URLs are correct
   - Check for JavaScript errors
   - Verify app is accessible

### Debug Mode

Enable debug mode by adding to your app configuration:

```javascript
window.ABS_FRAMEWORK_CONFIG = {
    // ... other config
    debug: true
};
```

This will enable console logging for framework operations.

## Future Enhancements

1. **User Preferences**: Save user's favorite apps and layout preferences
2. **App Categories**: Group apps by category in the launcher
3. **Recent Apps**: Show recently used apps
4. **App Search**: Enhanced search with tags and categories
5. **Notifications**: Centralized notification system
6. **Themes**: Customizable color schemes and themes
7. **Mobile Support**: Optimized mobile experience
8. **Offline Support**: Work offline with cached app list
