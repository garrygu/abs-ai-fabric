/**
 * ABS Unified Framework
 * Provides app launcher, unified header, and app switching functionality
 * Can be loaded by any ABS application
 */

class ABSUnifiedFramework {
    constructor(config = {}) {
        this.config = {
            // App-specific configuration
            currentApp: {
                id: 'unknown',
                name: 'Unknown App',
                description: 'ABS Application',
                icon: 'fas fa-cube',
                colorClass: 'bg-gray-600',
                url: window.location.pathname
            },
            
            // Framework configuration
            gatewayUrl: '/',
            appRegistryUrl: '/api/apps',
            enableNotifications: true,
            enableSettings: true,
            enableExport: false,
            
            // Custom menu items
            customMenuItems: [],
            
            // Override defaults
            ...config
        };
        
        this.state = {
            showAppLauncher: false,
            appSearchQuery: '',
            availableApps: [],
            notifications: [],
            user: {
                name: 'User',
                avatar: null
            }
        };
        
        this.init();
    }
    
    async init() {
        console.log('🚀 Initializing ABS Unified Framework');
        
        // Load app registry
        await this.loadAppRegistry();
        
        // Determine current app from URL and load its config
        await this.loadCurrentAppConfig();
        
        // Inject framework HTML
        this.injectFrameworkHTML();
        
        // Initialize Alpine.js data
        this.initAlpineData();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Load models for apps that need them
        this.loadModels();
        
        console.log('✅ ABS Unified Framework initialized');
    }
    
    async loadAppRegistry() {
        try {
        // Try hub app registry first (centralized)
        console.log('🔍 Attempting to load hub app registry from http://localhost:3000/apps-registry.json');
        const response = await fetch('http://localhost:3000/apps-registry.json');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('📋 Raw registry data:', data);
            
            // Convert apps object to array
            if (data.apps && typeof data.apps === 'object') {
                this.state.availableApps = Object.entries(data.apps).map(([id, app]) => ({
                    id,
                    ...app
                }));
            } else {
                this.state.availableApps = data.apps || [];
            }
            
            console.log(`📋 Loaded ${this.state.availableApps.length} apps from hub registry:`, this.state.availableApps);
        } catch (error) {
            console.warn('⚠️ Failed to load app registry from hub, trying gateway API:', error);
            try {
                // Fallback: try gateway UI app registry API
                const response = await fetch('http://localhost:8081/api/apps');
                const data = await response.json();
                this.state.availableApps = data.apps || [];
                console.log(`📋 Loaded ${this.state.availableApps.length} apps from gateway API`);
            } catch (fallbackError) {
                console.warn('⚠️ Failed to load app registry from gateway API, using hardcoded apps:', fallbackError);
                this.state.availableApps = this.getFallbackApps();
            }
        }
    }
    
    async loadCurrentAppConfig() {
        try {
            // Determine current app from URL path
            const currentPath = window.location.pathname;
            console.log(`🔍 Determining current app from path: ${currentPath}`);
            
            // Find matching app in registry
            const currentApp = this.state.availableApps.find(app => {
                return currentPath.startsWith(app.url) || currentPath === app.url;
            });
            
            if (currentApp) {
                console.log(`✅ Found current app: ${currentApp.name}`);
                
                // Merge registry config with user config
                this.config.currentApp = currentApp;
                this.config.customMenuItems = currentApp.config.customMenuItems || [];
                this.config.enableExport = currentApp.config.enableExport || false;
                this.config.enableSettings = currentApp.config.enableSettings !== false;
                
                // Merge with any user-provided config
                if (window.ABS_FRAMEWORK_CONFIG) {
                    this.config = { ...this.config, ...window.ABS_FRAMEWORK_CONFIG };
                }
                
                console.log(`📋 Loaded config for ${currentApp.name}:`, {
                    customMenuItems: this.config.customMenuItems.length,
                    enableExport: this.config.enableExport,
                    enableSettings: this.config.enableSettings
                });
            } else {
                console.warn('⚠️ Could not determine current app from URL, using fallback');
                this.config.currentApp = {
                    id: 'unknown',
                    name: 'Unknown App',
                    description: 'ABS Application',
                    icon: 'fas fa-cube',
                    colorClass: 'bg-gray-600',
                    url: currentPath
                };
            }
        } catch (error) {
            console.error('❌ Error loading current app config:', error);
        }
    }
    
    async loadModels() {
        try {
            const response = await fetch('/api/models');
            const data = await response.json();
            this.state.availableModels = data.models || [];
            console.log(`📋 Loaded ${this.state.availableModels.length} models`);
        } catch (error) {
            console.warn('⚠️ Failed to load models:', error);
            this.state.availableModels = [];
        }
    }
    
    getFallbackApps() {
        return [
            {
                id: 'contract-reviewer',
                name: 'Contract Reviewer',
                description: 'AI Contract Analysis',
                icon: 'fas fa-file-contract',
                colorClass: 'bg-blue-600',
                url: '/contract-reviewer'
            },
            {
                id: 'contract-reviewer-v2',
                name: 'Contract Reviewer v2',
                description: 'Professional AI Contract Analysis',
                icon: 'fas fa-file-contract',
                colorClass: 'bg-blue-600',
                url: '/contract-reviewer-v2'
            },
            {
                id: 'legal-assistant',
                name: 'Legal Assistant',
                description: 'AI Legal Research Assistant',
                icon: 'fas fa-gavel',
                colorClass: 'bg-green-600',
                url: '/legal-assistant'
            },
            {
                id: 'onyx',
                name: 'Onyx',
                description: 'AI Document Processing',
                icon: 'fas fa-brain',
                colorClass: 'bg-purple-600',
                url: '/onyx'
            },
            {
                id: 'rag-pdf-voice',
                name: 'RAG PDF Voice',
                description: 'Voice-Enabled Document Search',
                icon: 'fas fa-microphone',
                colorClass: 'bg-red-600',
                url: '/rag-pdf-voice'
            },
            {
                id: 'whisper-server',
                name: 'Whisper Server',
                description: 'Speech-to-Text Service',
                icon: 'fas fa-volume-up',
                colorClass: 'bg-orange-600',
                url: '/whisper-server'
            }
        ];
    }
    
    injectFrameworkHTML() {
        const frameworkHTML = `
            <!-- ABS Unified Framework -->
            <div id="abs-unified-framework" x-data="contractReviewer">
                <!-- App Launcher Overlay -->
                <div x-show="absFramework.showAppLauncher" 
                     x-transition:enter="transition ease-out duration-200"
                     x-transition:enter-start="opacity-0"
                     x-transition:enter-end="opacity-100"
                     x-transition:leave="transition ease-in duration-150"
                     x-transition:leave-start="opacity-100"
                     x-transition:leave-end="opacity-0"
                     class="fixed inset-0 bg-black bg-opacity-25 z-50" 
                     @click="absFramework.showAppLauncher = false">
                </div>
                
                <!-- App Launcher Menu -->
                <div x-show="absFramework.showAppLauncher" 
                     x-transition:enter="transition ease-out duration-200"
                     x-transition:enter-start="opacity-0 transform scale-95"
                     x-transition:enter-end="opacity-100 transform scale-100"
                     x-transition:leave="transition ease-in duration-150"
                     x-transition:leave-start="opacity-100 transform scale-100"
                     x-transition:leave-end="opacity-0 transform scale-95"
                     class="fixed top-16 left-4 w-80 bg-white rounded-lg shadow-xl z-50 border border-gray-200"
                     @click.stop>
                    <div class="p-4">
                        <div class="flex items-center justify-between mb-4">
                            <h3 class="text-lg font-semibold text-gray-900">ABS Applications</h3>
                            <button @click="absFramework.showAppLauncher = false" class="text-gray-400 hover:text-gray-600">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                        
                        <!-- Search Apps -->
                        <div class="mb-4">
                            <div class="relative">
                                <input type="text" 
                                       x-model="absFramework.appSearchQuery"
                                       placeholder="Find applications..."
                                       class="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500">
                                <i class="fas fa-search absolute left-3 top-3 text-gray-400"></i>
                            </div>
                        </div>
                        
                        <!-- Apps Grid -->
                        <div class="grid grid-cols-3 gap-3">
                            <template x-for="app in absFramework.filteredApps" :key="app.id">
                                <div @click="absFramework.switchToApp(app)" 
                                     class="p-3 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors">
                                    <div class="text-center">
                                        <div class="w-12 h-12 mx-auto mb-2 rounded-lg flex items-center justify-center"
                                             :class="app.colorClass">
                                            <i :class="app.icon" class="text-white text-xl"></i>
                                        </div>
                                        <div class="text-xs font-medium text-gray-700" x-text="app.name"></div>
                                    </div>
                                </div>
                            </template>
                        </div>
                        
                        <!-- Gateway Access -->
                        <div class="mt-4 pt-4 border-t border-gray-200">
                            <button @click="absFramework.goToGateway()" 
                                    class="w-full p-3 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors">
                                <div class="flex items-center">
                                    <i class="fas fa-home text-gray-600 mr-2"></i>
                                    <span class="text-sm font-medium text-gray-700">Return to Gateway</span>
                                </div>
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Unified Header -->
                <header class="bg-white shadow-sm border-b border-gray-200 fixed top-0 left-0 right-0 z-40">
                    <div class="px-6 py-4">
                        <div class="flex items-center justify-between">
                            <!-- Left Side: App Launcher + App Info -->
                            <div class="flex items-center">
                                <!-- App Launcher Button -->
                                <button @click="absFramework.showAppLauncher = !absFramework.showAppLauncher" 
                                        class="mr-4 p-2 rounded-lg hover:bg-gray-100 transition-colors">
                                    <i class="fas fa-th text-gray-600"></i>
                                </button>
                                
                                <!-- Current App Info -->
                                <div class="flex items-center">
                                    <div class="w-8 h-8 rounded-lg flex items-center justify-center mr-3"
                                         :class="absFramework.currentApp.colorClass">
                                        <i :class="absFramework.currentApp.icon" class="text-white text-sm"></i>
                                    </div>
                                    <div>
                                        <h1 class="text-xl font-bold text-gray-900" x-text="absFramework.currentApp.name"></h1>
                                        <p class="text-sm text-gray-500" x-text="absFramework.currentApp.description"></p>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Right Side: Custom Menu Items + User Info -->
                            <div class="flex items-center space-x-4">
                                <!-- Custom Menu Items -->
                                <template x-for="item in absFramework.customMenuItems" :key="item.id">
                                    <div>
                                        <!-- Select Dropdown -->
                                        <select x-show="item.type === 'select'" 
                                                x-model="absFramework.selectedModel"
                                                @change="absFramework.handleModelChange($event)"
                                                class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                                            <option value="">Auto Select</option>
                                            <template x-for="model in absFramework.availableModels" :key="model.name">
                                                <option :value="model.name" x-text="model.name"></option>
                                            </template>
                                        </select>
                                        
                                        <!-- Regular Button -->
                                        <button x-show="item.type !== 'select'" 
                                                @click="absFramework.handleCustomAction(item)" 
                                                :class="item.class || 'px-3 py-2 text-gray-600 hover:text-gray-900'"
                                                :disabled="item.disabled">
                                            <i :class="item.icon" class="mr-2"></i>
                                            <span x-text="item.label"></span>
                                        </button>
                                    </div>
                                </template>
                                
                                <!-- Notifications -->
                                <button x-show="absFramework.config.enableNotifications" 
                                        class="relative p-2 rounded-lg hover:bg-gray-100 transition-colors">
                                    <i class="fas fa-bell text-gray-600"></i>
                                    <span x-show="absFramework.notifications.length > 0" 
                                          class="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
                                </button>
                                
                                <!-- Settings -->
                                <button x-show="absFramework.config.enableSettings" 
                                        @click="absFramework.openSettings()" 
                                        class="p-2 rounded-lg hover:bg-gray-100 transition-colors">
                                    <i class="fas fa-cog text-gray-600"></i>
                                </button>
                                
                                <!-- User Profile -->
                                <div class="flex items-center space-x-2">
                                    <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                                        <i class="fas fa-user text-white text-sm"></i>
                                    </div>
                                    <span class="text-sm font-medium text-gray-700" x-text="absFramework.user.name"></span>
                                </div>
                            </div>
                        </div>
                    </div>
                </header>
            </div>
        `;
        
        // Inject at the beginning of body
        document.body.insertAdjacentHTML('afterbegin', frameworkHTML);
        
        // Add padding to body to account for fixed header
        document.body.style.paddingTop = '80px';
    }
    
    initAlpineData() {
        console.log('🔧 Initializing Alpine.js data...');
        
        // Wait for Alpine.js to be available
        if (!window.Alpine || !window.Alpine.data) {
            console.warn('⚠️ Alpine.js not available yet, retrying in 100ms...');
            setTimeout(() => this.initAlpineData(), 100);
            return;
        }
        
        // Extend existing Alpine.js data or create new
        const existingData = window.__originalContractReviewer || (() => ({}));
        
        window.Alpine.data('contractReviewer', () => {
            const originalData = existingData();
            console.log('🔧 Extending Alpine.js data with absFramework:', {
                currentApp: this.config.currentApp,
                availableApps: this.state.availableApps.length,
                customMenuItems: this.config.customMenuItems.length
            });
            
            return {
                ...originalData,
                absFramework: {
                    showAppLauncher: false,
                    appSearchQuery: '',
                    currentApp: this.config.currentApp,
                    availableApps: this.state.availableApps,
                    customMenuItems: this.config.customMenuItems,
                    notifications: this.state.notifications,
                    user: this.state.user,
                    config: this.config,
                    selectedModel: '',
                    availableModels: this.state.availableModels,
                    
                    get filteredApps() {
                        if (!this.appSearchQuery) {
                            return this.availableApps;
                        }
                        return this.availableApps.filter(app => 
                            app.name.toLowerCase().includes(this.appSearchQuery.toLowerCase()) ||
                            app.description.toLowerCase().includes(this.appSearchQuery.toLowerCase())
                        );
                    },
                    
                    switchToApp(app) {
                        console.log(`🔄 Switching to app: ${app.name}`);
                        this.showAppLauncher = false;
                        
                        // Update current app info
                        this.currentApp = app;
                        
                        // Navigate to the app URL
                        if (app.url && app.url !== window.location.pathname) {
                            window.location.href = app.url;
                        }
                    },
                    
                    goToGateway() {
                        console.log('🏠 Navigating to Gateway');
                        this.showAppLauncher = false;
                        window.location.href = this.config.gatewayUrl;
                    },
                    
                    handleCustomAction(item) {
                        if (item.action && typeof item.action === 'function') {
                            item.action();
                        } else if (item.url) {
                            window.location.href = item.url;
                        }
                    },
                    
                    openSettings() {
                        // Trigger app-specific settings
                        if (window.openAppSettings && typeof window.openAppSettings === 'function') {
                            window.openAppSettings();
                        } else {
                            console.log('⚙️ Settings clicked - implement openAppSettings() function');
                        }
                    },
                    
                    async loadModels() {
                        try {
                            const response = await fetch('/api/models');
                            const data = await response.json();
                            this.availableModels = data.models || [];
                            console.log(`📋 Loaded ${this.availableModels.length} models`);
                        } catch (error) {
                            console.warn('⚠️ Failed to load models:', error);
                            this.availableModels = [];
                        }
                    },
                    
                    handleModelChange(event) {
                        const selectedModel = event.target.value;
                        console.log(`🔄 Model changed to: ${selectedModel}`);
                        
                        // Call app-specific model update function
                        if (window.contractReviewer && window.contractReviewer.updateModel) {
                            window.contractReviewer.updateModel(selectedModel);
                        }
                    }
                }
            };
        });
        
        console.log('✅ Alpine.js data initialized');
        
        // Mount the just-injected framework subtree
        const el = document.getElementById('abs-unified-framework');
        if (window.Alpine && el) {
            window.Alpine.initTree(el);
            console.log('✅ Alpine.js framework subtree initialized');
        }
    }
    
    setupEventListeners() {
        // Listen for app registry updates
        window.addEventListener('abs-app-registry-updated', (event) => {
            this.state.availableApps = event.detail.apps;
            console.log('📋 App registry updated');
        });
        
        // Listen for notifications
        window.addEventListener('abs-notification', (event) => {
            this.state.notifications.push(event.detail);
            console.log('🔔 New notification:', event.detail);
        });
    }
    
    // Public API methods
    addCustomMenuItem(item) {
        this.config.customMenuItems.push(item);
    }
    
    removeCustomMenuItem(itemId) {
        this.config.customMenuItems = this.config.customMenuItems.filter(item => item.id !== itemId);
    }
    
    updateCurrentApp(appInfo) {
        this.config.currentApp = { ...this.config.currentApp, ...appInfo };
    }
    
    showNotification(message, type = 'info') {
        const notification = {
            id: Date.now(),
            message,
            type,
            timestamp: new Date()
        };
        
        this.state.notifications.push(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            this.state.notifications = this.state.notifications.filter(n => n.id !== notification.id);
        }, 5000);
    }
}

// Auto-initialize if config is provided
window.ABSUnifiedFramework = ABSUnifiedFramework;

// Auto-initialize with default config if ABS_FRAMEWORK_CONFIG is available
if (window.ABS_FRAMEWORK_CONFIG) {
    document.addEventListener('DOMContentLoaded', () => {
        new ABSUnifiedFramework(window.ABS_FRAMEWORK_CONFIG);
    });
}
