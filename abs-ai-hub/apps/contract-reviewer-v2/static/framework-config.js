/**
 * ABS App Configuration Template
 * Each app uses this generic template - configuration comes from apps-registry.json
 */

// Generic configuration that works for any app
window.ABS_FRAMEWORK_CONFIG = {
    // Framework settings (same for all apps)
    gatewayUrl: '/',
    appRegistryUrl: '/static/apps-registry.json',
    enableNotifications: true,
    enableSettings: true,
    enableExport: false, // Will be overridden by registry
    
    // App-specific callbacks (implemented by each app)
    onAppSwitch: (app) => {
        console.log(`Switching to ${app.name}`);
        // App-specific logic can be implemented here
    },
    
    onSettingsOpen: () => {
        console.log('Opening app settings');
        // App-specific settings logic
        if (window.openAppSettings && typeof window.openAppSettings === 'function') {
            window.openAppSettings();
        }
    },
    
    onNotification: (notification) => {
        console.log('App notification:', notification);
        // App-specific notification handling
    }
};

console.log('🔧 ABS_FRAMEWORK_CONFIG set:', window.ABS_FRAMEWORK_CONFIG);

// App-specific functions that the framework can call
window.openAppSettings = () => {
    // Contract Reviewer v2 specific settings logic
    if (window.contractReviewer) {
        window.contractReviewer.mainTab = 'settings';
    }
};

window.exportAppResults = () => {
    // Contract Reviewer v2 specific export logic
    if (window.contractReviewer && window.contractReviewer.exportResults) {
        window.contractReviewer.exportResults();
    }
};

// Initialize the framework
document.addEventListener('DOMContentLoaded', () => {
    // Get framework path from environment or use defaults
    const frameworkPath = window.ABS_FRAMEWORK_PATH || '/static/unified-framework.js';
    const gatewayUrl = window.ABS_GATEWAY_URL || 'http://localhost:8081';
    
    console.log(`🔧 Framework path: ${frameworkPath}`);
    console.log(`🔧 Gateway URL: ${gatewayUrl}`);
    
    // Load the unified framework script
    const script = document.createElement('script');
    script.src = frameworkPath;
    script.onload = () => {
        console.log(`✅ ABS Unified Framework loaded from: ${frameworkPath}`);
        
        // Try to initialize immediately if DOM is ready
        if (document.readyState === 'loading') {
            console.log('🔧 DOM still loading, waiting for DOMContentLoaded...');
        } else {
            console.log('🔧 DOM already ready, initializing framework immediately...');
            try {
                const framework = new window.ABSUnifiedFramework(window.ABS_FRAMEWORK_CONFIG);
                console.log('✅ ABSUnifiedFramework instance created immediately:', framework);
            } catch (error) {
                console.error('❌ Error creating ABSUnifiedFramework instance immediately:', error);
            }
        }
        
        // Debug: Check if framework HTML was injected
        setTimeout(() => {
            const frameworkDiv = document.getElementById('abs-unified-framework');
            if (frameworkDiv) {
                console.log('✅ Framework HTML injected successfully');
                console.log('Framework div:', frameworkDiv);
            } else {
                console.error('❌ Framework HTML not found in DOM');
            }
        }, 1000);
    };
    script.onerror = () => {
        console.error(`❌ Failed to load unified framework from: ${frameworkPath}`);
        
        // Fallback strategies
        const fallbacks = [
            '/static/unified-framework.js',
            `${gatewayUrl}/hub-ui/assets/unified-framework.js`,
            '/hub-ui/assets/unified-framework.js'
        ];
        
        let fallbackIndex = 0;
        const tryFallback = () => {
            if (fallbackIndex < fallbacks.length) {
                const fallbackPath = fallbacks[fallbackIndex];
                console.log(`🔄 Trying fallback ${fallbackIndex + 1}: ${fallbackPath}`);
                
                const fallbackScript = document.createElement('script');
                fallbackScript.src = fallbackPath;
                fallbackScript.onload = () => {
                    console.log(`✅ ABS Unified Framework loaded from fallback: ${fallbackPath}`);
                };
                fallbackScript.onerror = () => {
                    fallbackIndex++;
                    tryFallback();
                };
                document.head.appendChild(fallbackScript);
            } else {
                console.error('❌ All fallback attempts failed');
            }
        };
        
        tryFallback();
    };
    document.head.appendChild(script);
});
