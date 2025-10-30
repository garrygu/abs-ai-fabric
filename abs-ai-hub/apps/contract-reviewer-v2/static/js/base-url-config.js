/**
 * Base URL Configuration Utility
 * Automatically detects the current host (localhost, IP address, or domain name)
 * and provides base URLs for API calls and external services
 */

(function() {
    'use strict';

    // Get the current origin (protocol + host + port)
    const getCurrentOrigin = () => {
        return window.location.origin;
    };

    // Get the current host (hostname + port)
    const getCurrentHost = () => {
        const hostname = window.location.hostname;
        const port = window.location.port;
        if (port) {
            return `${hostname}:${port}`;
        }
        return hostname;
    };

    // Get base URL for a service based on current host
    const getServiceBaseUrl = (defaultPort, path = '') => {
        const hostname = window.location.hostname;
        const port = defaultPort;
        
        // If we're on a non-standard port, use it; otherwise use default
        let servicePort = port;
        if (window.location.port && window.location.port !== '80' && window.location.port !== '443') {
            // If current page is on a specific port, try to infer service ports
            // For now, use defaults or environment variables
            servicePort = port;
        }
        
        const protocol = window.location.protocol;
        const baseUrl = `${protocol}//${hostname}:${servicePort}${path}`;
        return baseUrl;
    };

    // Configuration object
    const baseUrlConfig = {
        // Current origin (for same-origin requests)
        origin: getCurrentOrigin(),
        
        // Current host
        host: getCurrentHost(),
        
        // API base URL (same origin - uses relative URLs)
        apiBase: '', // Empty string means relative URLs will be used
        
        // Hub UI base URL (default port 3000)
        hubUI: getServiceBaseUrl(3000),
        
        // Gateway URL (default port 8081)
        gateway: getServiceBaseUrl(8081),
        
        // Helper function to build API URLs
        api: function(path) {
            // Remove leading slash if present (we'll add it)
            const cleanPath = path.startsWith('/') ? path : `/${path}`;
            // Use relative URL for same-origin API calls
            return cleanPath;
        },
        
        // Helper function to build external service URLs
        external: function(host, port, path = '') {
            const hostname = window.location.hostname;
            const protocol = window.location.protocol;
            const cleanPath = path.startsWith('/') ? path : `/${path}`;
            return `${protocol}//${hostname}:${port}${cleanPath}`;
        },
        
        // Helper function to build Hub UI URLs
        hubUIUrl: function(path = '') {
            return this.external(this.host.split(':')[0], 3000, path);
        },
        
        // Helper function to build Gateway URLs
        gatewayUrl: function(path = '') {
            return this.external(this.host.split(':')[0], 8081, path);
        }
    };

    // Allow override via window.ABS_BASE_URL_CONFIG or environment variables
    if (window.ABS_BASE_URL_CONFIG) {
        Object.assign(baseUrlConfig, window.ABS_BASE_URL_CONFIG);
    }

    // Allow override of specific service URLs via environment variables (injected by backend)
    if (window.ABS_HUB_UI_URL) {
        // Use the URL injected by backend (supports IP addresses and domain names)
        try {
            const url = new URL(window.ABS_HUB_UI_URL);
            baseUrlConfig.hubUI = window.ABS_HUB_UI_URL;
            baseUrlConfig.hubUIUrl = (path = '') => {
                const cleanPath = path.startsWith('/') ? path : `/${path}`;
                return `${window.ABS_HUB_UI_URL}${cleanPath}`;
            };
        } catch (e) {
            console.warn('Invalid ABS_HUB_UI_URL:', e);
        }
    }
    
    // Also use current host info if available (injected by backend)
    if (window.ABS_CURRENT_HOST) {
        baseUrlConfig.currentHost = window.ABS_CURRENT_HOST;
    }
    
    if (window.ABS_CURRENT_SCHEME) {
        baseUrlConfig.currentScheme = window.ABS_CURRENT_SCHEME;
    }

    if (window.ABS_GATEWAY_URL) {
        try {
            const url = new URL(window.ABS_GATEWAY_URL);
            baseUrlConfig.gateway = window.ABS_GATEWAY_URL;
            baseUrlConfig.gatewayUrl = (path = '') => {
                return `${window.ABS_GATEWAY_URL}${path.startsWith('/') ? path : `/${path}`}`;
            };
        } catch (e) {
            console.warn('Invalid ABS_GATEWAY_URL:', e);
        }
    }

    // Export to window
    window.baseUrlConfig = baseUrlConfig;
    
    console.log('🔧 Base URL Configuration initialized:', {
        origin: baseUrlConfig.origin,
        host: baseUrlConfig.host,
        hubUI: baseUrlConfig.hubUI,
        gateway: baseUrlConfig.gateway
    });
})();

