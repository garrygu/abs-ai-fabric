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
            activeHubTab: 'apps', // Track active hub tab
            user: {
                name: 'User',
                avatar: null
            }
        };
        
        this.init();
    }
    
    async init() {
        console.log('🚀 Initializing ABS Unified Framework');
        
        // Check if we're on hub early (before loading app config)
        const pathname = window.location.pathname;
        const isHubEarly = pathname === '/' || pathname === '/index.html' || pathname.includes('hub') ||
                          (window.ABS_FRAMEWORK_CONFIG && window.ABS_FRAMEWORK_CONFIG.currentApp && 
                           window.ABS_FRAMEWORK_CONFIG.currentApp.id === 'hub');
        
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
        
        // Load models for apps that need them (only if not hub)
        if (!isHubEarly && !(this.config.currentApp && this.config.currentApp.id === 'hub')) {
            this.loadModels();
        }
        
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
        // Skip models loading for hub (hub doesn't have models endpoint)
        // Check if we're on the hub based on pathname or if currentApp is hub
        const pathname = window.location.pathname;
        const isHub = pathname === '/' || 
                     pathname === '/index.html' || 
                     pathname.includes('hub') ||
                     (this.config.currentApp && this.config.currentApp.id === 'hub');
        
        if (isHub) {
            this.state.availableModels = [];
            return;
        }
        
        try {
            const response = await fetch('/api/models');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            this.state.availableModels = data.models || [];
            console.log(`📋 Loaded ${this.state.availableModels.length} models`);
        } catch (error) {
            // Silently fail - models endpoint may not exist for all apps
            // Don't log error to avoid console noise
            this.state.availableModels = [];
        }
    }
    
    createHubNavigationTabs() {
        // Create nav tabs container that integrates with the unified framework
        const container = document.querySelector('.container');
        if (!container) return;
        
        // Check if nav tabs already exist
        if (container.querySelector('.hub-nav-tabs')) return;
        
        // Hide original nav tabs if they exist
        const originalNavTabs = container.querySelector('.nav-tabs');
        if (originalNavTabs) {
            originalNavTabs.style.display = 'none';
        }
        
        // Create nav tabs with proper styling
        const navTabsHTML = `
            <div class="hub-nav-tabs" style="display: flex; gap: 10px; margin-bottom: 30px; justify-content: center; margin-top: 20px; padding-top: 20px;">
                <button class="hub-nav-tab active" onclick="showTab('apps')" style="padding: 12px 24px; border: none; background: #667eea; color: white; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 500; transition: all 0.3s;">📱 Apps</button>
                <button class="hub-nav-tab" onclick="showTab('admin')" style="padding: 12px 24px; border: none; background: rgba(255, 255, 255, 0.7); color: #666; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 500; transition: all 0.3s;">⚙️ Admin</button>
                <button class="hub-nav-tab" onclick="showTab('assets')" style="padding: 12px 24px; border: none; background: rgba(255, 255, 255, 0.7); color: #666; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 500; transition: all 0.3s;">📊 Assets</button>
            </div>
        `;
        
        // Insert nav tabs at the beginning of container
        container.insertAdjacentHTML('afterbegin', navTabsHTML);
        
        // Add tab switching behavior
        document.querySelectorAll('.hub-nav-tab').forEach(tab => {
            tab.addEventListener('click', function() {
                // Update active state
                document.querySelectorAll('.hub-nav-tab').forEach(t => {
                    t.classList.remove('active');
                    t.style.background = 'rgba(255, 255, 255, 0.7)';
                    t.style.color = '#666';
                });
                this.classList.add('active');
                this.style.background = '#667eea';
                this.style.color = 'white';
            });
        });
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
        // Determine data component name based on context
        const pathname = window.location.pathname;
        const isHub = pathname === '/' || pathname === '/index.html' || pathname.includes('hub') ||
                     (this.config.currentApp && this.config.currentApp.id === 'hub');
        const dataComponentName = isHub ? 'hubFramework' : 'contractReviewer';
        
        // For hub, hide the original header and nav tabs BEFORE injecting framework
        if (isHub) {
            // Hide original header and nav tabs
            const hideElement = (selector) => {
                const element = document.querySelector(selector);
                if (element) {
                    element.style.display = 'none';
                    element.style.visibility = 'hidden';
                    element.style.opacity = '0';
                    element.style.height = '0';
                    element.style.margin = '0';
                    element.style.padding = '0';
                    element.style.overflow = 'hidden';
                    try {
                        element.remove();
                    } catch(e) {}
                }
            };
            
            // Hide original header and nav tabs
            hideElement('#original-header');
            hideElement('#original-nav-tabs');
            hideElement('.header#original-header');
            hideElement('.nav-tabs#original-nav-tabs');
            
            // Also hide hub-nav-tabs if they exist (old duplicate buttons)
            hideElement('.hub-nav-tabs');
            
            // Also try generic selectors
            const originalHeader = document.getElementById('original-header');
            const originalNavTabs = document.getElementById('original-nav-tabs');
            const hubNavTabs = document.querySelector('.hub-nav-tabs');
            
            if (originalHeader) {
                originalHeader.style.cssText = 'display:none!important;visibility:hidden!important;';
                try {
                    originalHeader.remove();
                } catch(e) {}
            }
            if (originalNavTabs) {
                originalNavTabs.style.cssText = 'display:none!important;visibility:hidden!important;';
                try {
                    originalNavTabs.remove();
                } catch(e) {}
            }
            if (hubNavTabs) {
                hubNavTabs.style.cssText = 'display:none!important;visibility:hidden!important;';
                try {
                    hubNavTabs.remove();
                } catch(e) {}
            }
        }
        
        const frameworkHTML = `
            <!-- ABS Unified Framework -->
            <div id="abs-unified-framework" x-data="${dataComponentName}">
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
                <header class="bg-gradient-to-r from-blue-600 to-blue-700 shadow-lg border-b border-blue-800 fixed top-0 left-0 right-0 z-40" style="min-height: 70px; width: 100%;">
                    <div class="px-6 py-2 w-full">
                        <div class="flex items-center justify-between w-full">
                            <!-- Left Side: App Launcher + App Info -->
                            <div class="flex items-center">
                                <!-- App Launcher Button -->
                                <button @click="absFramework.showAppLauncher = !absFramework.showAppLauncher" 
                                        class="mr-3 p-1.5 rounded-lg hover:bg-blue-500 transition-colors text-white">
                                    <i class="fas fa-th text-sm"></i>
                                </button>
                                
                                <!-- Current App Info -->
                                <div class="flex items-center cursor-pointer hover:opacity-80 transition-opacity flex-shrink-0" 
                                     @click="absFramework.goToAppHome()"
                                     title="Click to go to app homepage">
                                    <div class="w-7 h-7 rounded-lg flex items-center justify-center mr-2.5 bg-white bg-opacity-20 flex-shrink-0"
                                         :class="absFramework.currentApp && absFramework.currentApp.colorClass ? absFramework.currentApp.colorClass : 'bg-blue-500'">
                                        <i :class="absFramework.currentApp && absFramework.currentApp.icon ? absFramework.currentApp.icon : 'fas fa-home'" class="text-white text-xs"></i>
                                    </div>
                                    <div class="flex-shrink-0">
                                        <h1 class="text-lg font-bold text-white leading-tight whitespace-nowrap" x-text="absFramework.currentApp && absFramework.currentApp.name ? absFramework.currentApp.name : 'ABS AI Hub'"></h1>
                                        <p class="text-xs text-blue-100 leading-tight -mt-0.5 whitespace-nowrap" x-text="absFramework.currentApp && absFramework.currentApp.description ? absFramework.currentApp.description : 'Legal Workstation'"></p>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Center: Navigation Tabs (for Hub only) -->
                            <div x-show="absFramework.currentApp && absFramework.currentApp.id === 'hub'" 
                                 class="flex items-center space-x-2 mx-auto flex-shrink-0">
                                <button @click="absFramework.switchHubTab('apps')" 
                                        :class="absFramework.activeHubTab === 'apps' ? 'bg-white bg-opacity-30 text-white font-semibold' : 'text-blue-100 hover:bg-blue-500 hover:text-white'"
                                        class="px-4 py-1.5 rounded-lg transition-colors text-sm flex items-center space-x-1.5">
                                    <i class="fas fa-th text-xs"></i>
                                    <span>Apps</span>
                                </button>
                                <button @click="absFramework.switchHubTab('admin')" 
                                        :class="absFramework.activeHubTab === 'admin' ? 'bg-white bg-opacity-30 text-white font-semibold' : 'text-blue-100 hover:bg-blue-500 hover:text-white'"
                                        class="px-4 py-1.5 rounded-lg transition-colors text-sm flex items-center space-x-1.5">
                                    <i class="fas fa-cog text-xs"></i>
                                    <span>Admin</span>
                                </button>
                                <button @click="absFramework.switchHubTab('assets')" 
                                        :class="absFramework.activeHubTab === 'assets' ? 'bg-white bg-opacity-30 text-white font-semibold' : 'text-blue-100 hover:bg-blue-500 hover:text-white'"
                                        class="px-4 py-1.5 rounded-lg transition-colors text-sm flex items-center space-x-1.5">
                                    <i class="fas fa-chart-bar text-xs"></i>
                                    <span>Assets</span>
                                </button>
                            </div>
                            
                            <!-- Right Side: Custom Menu Items + User Info -->
                            <div class="flex items-center space-x-2 ml-auto flex-shrink-0">
                                <!-- Custom Menu Items -->
                                <template x-for="item in absFramework.customMenuItems" :key="item.id">
                                    <div>
                                        <!-- Select Dropdown -->
                                        <select x-show="item.type === 'select'" 
                                                x-model="absFramework.selectedModel"
                                                @change="absFramework.handleModelChange($event)"
                                                class="px-3 py-2 border border-blue-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white">
                                            <option value="">Auto Select</option>
                                            <template x-for="model in absFramework.availableModels" :key="model.name">
                                                <option :value="model.name" x-text="model.name"></option>
                                            </template>
                                        </select>
                                        
                                        <!-- Regular Button -->
                                        <button x-show="item.type !== 'select'" 
                                                @click="absFramework.handleCustomAction(item)" 
                                                :class="item.class || 'px-3 py-2 text-blue-100 hover:text-white hover:bg-blue-500 rounded-lg transition-colors'"
                                                :disabled="item.disabled">
                                            <i :class="item.icon" class="mr-2"></i>
                                            <span x-text="item.label"></span>
                                        </button>
                                    </div>
                                </template>
                                
                                <!-- Notifications -->
                                <button x-show="absFramework.config.enableNotifications" 
                                        class="relative p-2 rounded-lg hover:bg-blue-500 transition-colors text-white flex-shrink-0"
                                        title="Notifications">
                                    <i class="fas fa-bell text-sm"></i>
                                    <span x-show="absFramework.notifications.length > 0" 
                                          class="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-red-500 rounded-full"></span>
                                </button>
                                
                                <!-- Settings -->
                                <button x-show="absFramework.config.enableSettings" 
                                        @click="absFramework.openSettings(); console.log('Settings button clicked')" 
                                        class="p-2 rounded-lg hover:bg-blue-500 transition-colors text-white flex-shrink-0"
                                        title="Settings">
                                    <i class="fas fa-cog text-sm"></i>
                                </button>
                                
                                <!-- User Profile Dropdown -->
                                <div class="relative flex-shrink-0" x-data="{ showProfileMenu: false }">
                                    <button @click="showProfileMenu = !showProfileMenu" 
                                            class="flex items-center space-x-1.5 p-1.5 rounded-lg hover:bg-blue-500 transition-colors text-white"
                                            @click.away="showProfileMenu = false"
                                            title="User Menu">
                                        <div class="w-7 h-7 bg-white bg-opacity-20 rounded-full flex items-center justify-center flex-shrink-0">
                                            <i class="fas fa-user text-white text-xs"></i>
                                        </div>
                                        <span class="text-xs font-medium text-white whitespace-nowrap" x-text="absFramework.user.name"></span>
                                        <i class="fas fa-chevron-down text-xs ml-0.5 flex-shrink-0"></i>
                                    </button>
                                    
                                    <!-- Profile Dropdown Menu -->
                                    <div x-show="showProfileMenu" 
                                         x-transition:enter="transition ease-out duration-100"
                                         x-transition:enter-start="opacity-0 scale-95"
                                         x-transition:enter-end="opacity-100 scale-100"
                                         x-transition:leave="transition ease-in duration-75"
                                         x-transition:leave-start="opacity-100 scale-100"
                                         x-transition:leave-end="opacity-0 scale-95"
                                         class="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl border border-gray-200 z-50"
                                         @click.stop>
                                        <div class="py-2">
                                            <!-- Profile Info -->
                                            <div class="px-4 py-3 border-b border-gray-200">
                                                <div class="text-sm font-medium text-gray-900" x-text="absFramework.user.name"></div>
                                                <div class="text-xs text-gray-500 mt-1" x-text="absFramework.user.email || 'user@example.com'"></div>
                                            </div>
                                            
                                            <!-- Menu Items -->
                                            <button @click="absFramework.openProfile(); showProfileMenu = false" 
                                                    class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center">
                                                <i class="fas fa-user-circle mr-3 text-gray-400"></i>
                                                View Profile
                                            </button>
                                            <button @click="absFramework.openSettings(); showProfileMenu = false" 
                                                    class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center">
                                                <i class="fas fa-cog mr-3 text-gray-400"></i>
                                                Settings
                                            </button>
                                            <button @click="absFramework.openNotifications(); showProfileMenu = false" 
                                                    x-show="absFramework.config.enableNotifications"
                                                    class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center">
                                                <i class="fas fa-bell mr-3 text-gray-400"></i>
                                                Notifications
                                                <span x-show="absFramework.notifications.length > 0" 
                                                      class="ml-auto bg-red-500 text-white text-xs rounded-full px-2 py-1" 
                                                      x-text="absFramework.notifications.length"></span>
                                            </button>
                                            <div class="border-t border-gray-200 my-1"></div>
                                            <button @click="absFramework.showHelp()" 
                                                    class="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center">
                                                <i class="fas fa-question-circle mr-3 text-gray-400"></i>
                                                Help & Support
                                            </button>
                                            <button @click="absFramework.signOut(); showProfileMenu = false" 
                                                    class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center">
                                                <i class="fas fa-sign-out-alt mr-3"></i>
                                                Sign Out
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </header>
            </div>
        `;
        
        // Wait for Alpine.js and styles to be fully ready before injecting
        const waitForReady = () => {
            const isReady = window.Alpine && 
                           typeof window.Alpine.data === 'function' &&
                           (window.Tailwind !== undefined || document.styleSheets.length > 0);
            
            if (isReady) {
                // Inject framework HTML into the page
                document.body.insertAdjacentHTML('afterbegin', frameworkHTML);
                
                // Mark body as having unified framework active
                document.body.classList.add('unified-framework-active');
                
                // Force a reflow to ensure styles are applied
                void document.body.offsetHeight;
                
                // Initialize Alpine.js data immediately after injection
                this.initAlpineData();
                
                // Add padding to body to account for fixed header
                // Calculate actual header height after it's rendered
                setTimeout(() => {
                    const header = document.querySelector('#abs-unified-framework header');
                    if (header) {
                        const headerHeight = header.offsetHeight;
                        document.body.style.paddingTop = `${headerHeight + 10}px`; // Add 10px extra spacing
                        console.log(`📏 Header height: ${headerHeight}px, Body padding: ${headerHeight + 10}px`);
                    } else {
                        // Fallback if header not found
                        document.body.style.paddingTop = '80px';
                    }
                }, 50);
            } else {
                // Retry after a short delay
                setTimeout(waitForReady, 50);
            }
        };
        
        waitForReady();
        
        // Navigation tabs are now in the header - no need to create them below
        // Removed createHubNavigationTabs() call
    }
    
    initAlpineData() {
        console.log('🔧 Initializing Alpine.js data...');
        
        // Wait for Alpine.js to be available
        if (!window.Alpine || !window.Alpine.data) {
            console.warn('⚠️ Alpine.js not available yet, retrying in 100ms...');
            setTimeout(() => this.initAlpineData(), 100);
            return;
        }
        
        // Determine data component name based on context
        const pathname = window.location.pathname;
        const isHub = pathname === '/' || pathname === '/index.html' || pathname.includes('hub') ||
                     (this.config.currentApp && this.config.currentApp.id === 'hub');
        const dataComponentName = isHub ? 'hubFramework' : 'contractReviewer';
        const existingDataName = dataComponentName === 'hubFramework' ? '__originalHubFramework' : '__originalContractReviewer';
        const existingData = window[existingDataName] || (() => ({}));
        
        // Capture framework instance context
        const frameworkInstance = this;
        
        // Create or extend the appropriate Alpine.js data component
        const dataComponent = () => {
            const originalData = existingData();
            console.log('🔧 Extending Alpine.js data with absFramework:', {
                currentApp: frameworkInstance.config.currentApp,
                availableApps: frameworkInstance.state.availableApps.length,
                customMenuItems: frameworkInstance.config.customMenuItems.length
            });
            
            return {
                ...originalData,
                absFramework: {
                    showAppLauncher: false,
                    appSearchQuery: '',
                    currentApp: frameworkInstance.config.currentApp,
                    availableApps: frameworkInstance.state.availableApps,
                    customMenuItems: frameworkInstance.config.customMenuItems,
                    notifications: frameworkInstance.state.notifications,
                    user: frameworkInstance.state.user,
                    config: frameworkInstance.config,
                    selectedModel: '',
                    availableModels: frameworkInstance.state.availableModels,
                    activeHubTab: frameworkInstance.state.activeHubTab || 'apps',
                    
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
                            
                            switchHubTab(tabName) {
                                // Update active tab state
                                this.activeHubTab = tabName;
                                
                                // Call the existing showTab function if it exists
                                if (typeof window.showTab === 'function') {
                                    window.showTab(tabName);
                                } else {
                                    // Fallback: manually show/hide tabs
                                    const tabs = ['apps', 'admin', 'assets'];
                                    tabs.forEach(tab => {
                                        const tabElement = document.getElementById(`${tab}-tab`);
                                        if (tabElement) {
                                            if (tab === tabName) {
                                                tabElement.classList.add('active');
                                                tabElement.style.display = 'block';
                                            } else {
                                                tabElement.classList.remove('active');
                                                tabElement.style.display = 'none';
                                            }
                                        }
                                    });
                                }
                            },
                    
                    goToGateway() {
                        console.log('🏠 Navigating to Gateway');
                        this.showAppLauncher = false;
                        window.location.href = this.config.gatewayUrl;
                    },
                    
                    goToAppHome() {
                        console.log('🏠 Navigating to App Home');
                        this.showAppLauncher = false;
                        // Navigate to the current app's home URL
                        if (this.currentApp && this.currentApp.url) {
                            window.location.href = this.currentApp.url;
                        } else {
                            // Fallback to root if no URL is set
                            window.location.href = '/';
                        }
                    },
                    
                    handleCustomAction(item) {
                        if (item.action && typeof item.action === 'function') {
                            item.action();
                        } else if (item.url) {
                            window.location.href = item.url;
                        }
                    },
                    
                    openSettings() {
                        console.log('🔧 absFramework.openSettings() called');
                        // Trigger app-specific settings
                        if (window.openAppSettings && typeof window.openAppSettings === 'function') {
                            console.log('🔧 Calling window.openAppSettings()');
                            window.openAppSettings();
                        } else if (window.openHubSettings && typeof window.openHubSettings === 'function') {
                            console.log('🔧 Calling window.openHubSettings()');
                            window.openHubSettings();
                        } else {
                            console.log('⚙️ Settings clicked - implement openAppSettings() or openHubSettings() function');
                        }
                    },
                    
                    openProfile() {
                        console.log('👤 absFramework.openProfile() called');
                        // Trigger profile opening
                        if (window.openUserProfile && typeof window.openUserProfile === 'function') {
                            console.log('👤 Calling window.openUserProfile()');
                            window.openUserProfile();
                        } else if (absFramework.config.onProfileOpen && typeof absFramework.config.onProfileOpen === 'function') {
                            console.log('👤 Calling config.onProfileOpen()');
                            absFramework.config.onProfileOpen();
                        } else {
                            console.log('👤 Profile clicked - implement openUserProfile() function');
                        }
                    },
                    
                    openNotifications() {
                        console.log('🔔 absFramework.openNotifications() called');
                        // Show notifications panel
                        // This can be implemented as a dropdown or modal
                        if (window.openNotificationsPanel && typeof window.openNotificationsPanel === 'function') {
                            window.openNotificationsPanel();
                        } else {
                            alert(`You have ${this.notifications.length} notification(s)`);
                        }
                    },
                    
                    showHelp() {
                        console.log('❓ absFramework.showHelp() called');
                        // Show help content
                        if (window.showHelpContent && typeof window.showHelpContent === 'function') {
                            window.showHelpContent();
                        } else {
                            // Default help
                            alert('ABS AI Hub Help\n\nNavigate between apps using the app launcher.\nAccess your profile and settings from the user menu.\nUse the admin panel to manage services and models.');
                        }
                    },
                    
                    signOut() {
                        console.log('🚪 absFramework.signOut() called');
                        // Handle sign out
                        if (window.handleSignOut && typeof window.handleSignOut === 'function') {
                            window.handleSignOut();
                        } else {
                            // Default: confirm and reload
                            if (confirm('Are you sure you want to sign out?')) {
                                // Clear user data if needed
                                localStorage.removeItem('userSession');
                                // Reload page
                                window.location.reload();
                            }
                        }
                    },
                    
                    async loadModels() {
                        // Skip models loading for hub
                        const pathname = window.location.pathname;
                        const isHub = pathname === '/' || 
                                     pathname === '/index.html' || 
                                     pathname.includes('hub') ||
                                     (absFramework.config.currentApp && absFramework.config.currentApp.id === 'hub');
                        
                        if (isHub) {
                            this.availableModels = [];
                            return;
                        }
                        
                        try {
                            const response = await fetch('/api/models');
                            if (!response.ok) {
                                throw new Error(`HTTP ${response.status}`);
                            }
                            const data = await response.json();
                            this.availableModels = data.models || [];
                            console.log(`📋 Loaded ${this.availableModels.length} models`);
                        } catch (error) {
                            // Silently fail - models endpoint may not exist
                            // Don't log error to avoid console noise
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
        };
        
        // Register the data component with the appropriate name
        window.Alpine.data(dataComponentName, dataComponent);
        
        console.log(`✅ Alpine.js data component '${dataComponentName}' initialized`);
        
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
