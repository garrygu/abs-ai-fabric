/**
 * ABS Hub Framework Configuration
 * Hub-specific configuration for the unified framework
 */

// Add modal styles
const modalStyles = `
    <style id="hub-modal-styles">
        .hub-modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 10000;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(4px);
        }
        
        .hub-modal-content {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 600px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }
        
        .hub-modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 24px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .hub-modal-header h2 {
            margin: 0;
            font-size: 1.5rem;
            font-weight: 600;
            color: #111827;
        }
        
        .hub-modal-close {
            background: none;
            border: none;
            font-size: 1.5rem;
            color: #6b7280;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
            transition: all 0.2s;
        }
        
        .hub-modal-close:hover {
            background: #f3f4f6;
            color: #111827;
        }
        
        .hub-modal-body {
            padding: 24px;
            flex: 1;
            overflow-y: auto;
        }
        
        .hub-modal-footer {
            padding: 20px 24px;
            border-top: 1px solid #e5e7eb;
            display: flex;
            justify-content: flex-end;
            gap: 12px;
        }
        
        .settings-section {
            margin-bottom: 32px;
        }
        
        .settings-section h3 {
            margin: 0 0 16px 0;
            font-size: 1.1rem;
            font-weight: 600;
            color: #111827;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 8px;
        }
        
        .setting-item {
            margin-bottom: 16px;
        }
        
        .setting-item label {
            display: block;
            margin-bottom: 8px;
            font-size: 0.875rem;
            font-weight: 500;
            color: #374151;
        }
        
        .setting-item input[type="text"],
        .setting-item input[type="email"],
        .setting-item input[type="number"],
        .setting-item select {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 0.875rem;
            transition: border-color 0.2s;
        }
        
        .setting-item input:focus,
        .setting-item select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .setting-item input[type="checkbox"] {
            margin-right: 8px;
        }
        
        .profile-section {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 32px;
            padding-bottom: 24px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .profile-avatar {
            flex-shrink: 0;
        }
        
        .avatar-placeholder {
            width: 64px;
            height: 64px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.5rem;
        }
        
        .profile-info h3 {
            margin: 0 0 4px 0;
            font-size: 1.25rem;
            font-weight: 600;
            color: #111827;
        }
        
        .profile-info p {
            margin: 0;
            font-size: 0.875rem;
            color: #6b7280;
        }
        
        .btn-primary {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-primary:hover {
            background: #5a6fd8;
            transform: translateY(-1px);
        }
        
        .btn-secondary {
            background: #f3f4f6;
            color: #374151;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .btn-secondary:hover {
            background: #e5e7eb;
        }
    </style>
`;

// Inject modal styles immediately
(function() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectModalStyles);
    } else {
        injectModalStyles();
    }
    
    function injectModalStyles() {
        if (!document.getElementById('hub-modal-styles')) {
            document.head.insertAdjacentHTML('beforeend', modalStyles);
        }
    }
})();

window.ABS_FRAMEWORK_CONFIG = {
    // Hub-specific configuration
    currentApp: {
        id: 'hub',
        name: 'ABS AI Hub',
        description: 'Legal Workstation - AI-powered legal tools',
        icon: 'fas fa-home',
        colorClass: 'bg-purple-600',
        url: '/'
    },
    
    // Framework configuration
    gatewayUrl: '/',
    appRegistryUrl: '/api/apps',
    enableNotifications: true,
    enableSettings: true,
    enableExport: false,
    
    // Hub-specific menu items
    customMenuItems: [],
    
    // Hub-specific callbacks
    onAppSwitch: (app) => {
        console.log(`Hub: Switching to ${app.name}`);
        // Navigate to the app URL
        if (app.url && app.url !== window.location.pathname) {
            window.location.href = app.url;
        }
    },
    
    onSettingsOpen: () => {
        console.log('Hub: Opening hub settings');
        if (window.openHubSettings && typeof window.openHubSettings === 'function') {
            window.openHubSettings();
        } else {
            // Fallback: show settings modal
            showHubSettingsModal();
        }
    },
    
    onProfileOpen: () => {
        console.log('Hub: Opening user profile');
        if (window.openUserProfile && typeof window.openUserProfile === 'function') {
            window.openUserProfile();
        } else {
            // Fallback: show profile modal
            showUserProfileModal();
        }
    },
    
    onNotification: (notification) => {
        console.log('Hub notification:', notification);
        // Hub-specific notification handling
        if (window.showHubNotification && typeof window.showHubNotification === 'function') {
            window.showHubNotification(notification);
        }
    }
};

console.log('🔧 Hub Framework Config set:', window.ABS_FRAMEWORK_CONFIG);

// Hub-specific functions that the framework can call
window.openHubSettings = () => {
    console.log('🔧 openHubSettings called');
    showHubSettingsModal();
};

window.openUserProfile = () => {
    console.log('👤 openUserProfile called');
    showUserProfileModal();
};

// Hub Settings Modal
function showHubSettingsModal() {
    // Create or show settings modal
    let modal = document.getElementById('hub-settings-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'hub-settings-modal';
        modal.className = 'hub-modal-overlay';
        modal.innerHTML = `
            <div class="hub-modal-content">
                <div class="hub-modal-header">
                    <h2>Hub Settings</h2>
                    <button class="hub-modal-close" onclick="closeHubSettingsModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="hub-modal-body">
                    <div class="settings-section">
                        <h3>Appearance</h3>
                        <div class="setting-item">
                            <label>Theme</label>
                            <select id="theme-select">
                                <option value="light">Light</option>
                                <option value="dark">Dark</option>
                                <option value="auto">Auto</option>
                            </select>
                        </div>
                        <div class="setting-item">
                            <label>Language</label>
                            <select id="language-select">
                                <option value="en">English</option>
                                <option value="es">Español</option>
                                <option value="fr">Français</option>
                            </select>
                        </div>
                    </div>
                    <div class="settings-section">
                        <h3>Notifications</h3>
                        <div class="setting-item">
                            <label>
                                <input type="checkbox" id="notifications-enabled" checked>
                                Enable notifications
                            </label>
                        </div>
                        <div class="setting-item">
                            <label>
                                <input type="checkbox" id="email-notifications">
                                Email notifications
                            </label>
                        </div>
                    </div>
                    <div class="settings-section">
                        <h3>General</h3>
                        <div class="setting-item">
                            <label>
                                <input type="checkbox" id="auto-refresh" checked>
                                Auto-refresh status
                            </label>
                        </div>
                        <div class="setting-item">
                            <label>Refresh Interval (seconds)</label>
                            <input type="number" id="refresh-interval" value="30" min="10" max="300">
                        </div>
                    </div>
                </div>
                <div class="hub-modal-footer">
                    <button onclick="saveHubSettings()" class="btn-primary">Save Settings</button>
                    <button onclick="closeHubSettingsModal()" class="btn-secondary">Cancel</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Load saved settings
        loadHubSettings();
    }
    modal.style.display = 'flex';
}

function closeHubSettingsModal() {
    const modal = document.getElementById('hub-settings-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function loadHubSettings() {
    const settings = JSON.parse(localStorage.getItem('hubSettings') || '{}');
    if (settings.theme) document.getElementById('theme-select').value = settings.theme;
    if (settings.language) document.getElementById('language-select').value = settings.language;
    if (settings.notificationsEnabled !== undefined) {
        document.getElementById('notifications-enabled').checked = settings.notificationsEnabled;
    }
    if (settings.emailNotifications !== undefined) {
        document.getElementById('email-notifications').checked = settings.emailNotifications;
    }
    if (settings.autoRefresh !== undefined) {
        document.getElementById('auto-refresh').checked = settings.autoRefresh;
    }
    if (settings.refreshInterval) {
        document.getElementById('refresh-interval').value = settings.refreshInterval;
    }
}

function saveHubSettings() {
    const settings = {
        theme: document.getElementById('theme-select').value,
        language: document.getElementById('language-select').value,
        notificationsEnabled: document.getElementById('notifications-enabled').checked,
        emailNotifications: document.getElementById('email-notifications').checked,
        autoRefresh: document.getElementById('auto-refresh').checked,
        refreshInterval: parseInt(document.getElementById('refresh-interval').value)
    };
    
    localStorage.setItem('hubSettings', JSON.stringify(settings));
    closeHubSettingsModal();
    
    // Apply settings
    applyHubSettings(settings);
    
    // Show notification
    if (window.absFrameworkInstance) {
        window.absFrameworkInstance.showNotification('Settings saved successfully', 'success');
    }
}

function applyHubSettings(settings) {
    // Apply theme
    if (settings.theme === 'dark') {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }
    
    // Store for framework to use
    window.hubSettings = settings;
}

// User Profile Modal
function showUserProfileModal() {
    let modal = document.getElementById('user-profile-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'user-profile-modal';
        modal.className = 'hub-modal-overlay';
        modal.innerHTML = `
            <div class="hub-modal-content">
                <div class="hub-modal-header">
                    <h2>User Profile</h2>
                    <button class="hub-modal-close" onclick="closeUserProfileModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="hub-modal-body">
                    <div class="profile-section">
                        <div class="profile-avatar">
                            <div class="avatar-placeholder">
                                <i class="fas fa-user"></i>
                            </div>
                        </div>
                        <div class="profile-info">
                            <h3 id="profile-name">User</h3>
                            <p id="profile-email">user@example.com</p>
                        </div>
                    </div>
                    <div class="settings-section">
                        <h3>Account Information</h3>
                        <div class="setting-item">
                            <label>Full Name</label>
                            <input type="text" id="profile-full-name" value="User">
                        </div>
                        <div class="setting-item">
                            <label>Email</label>
                            <input type="email" id="profile-email-input" value="user@example.com">
                        </div>
                    </div>
                    <div class="settings-section">
                        <h3>Preferences</h3>
                        <div class="setting-item">
                            <label>
                                <input type="checkbox" id="profile-email-updates" checked>
                                Receive email updates
                            </label>
                        </div>
                    </div>
                </div>
                <div class="hub-modal-footer">
                    <button onclick="saveUserProfile()" class="btn-primary">Save Profile</button>
                    <button onclick="closeUserProfileModal()" class="btn-secondary">Cancel</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Load user profile data
        loadUserProfile();
    }
    modal.style.display = 'flex';
}

function closeUserProfileModal() {
    const modal = document.getElementById('user-profile-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function loadUserProfile() {
    const profile = JSON.parse(localStorage.getItem('userProfile') || '{}');
    if (profile.name) {
        document.getElementById('profile-name').textContent = profile.name;
        document.getElementById('profile-full-name').value = profile.name;
    }
    if (profile.email) {
        document.getElementById('profile-email').textContent = profile.email;
        document.getElementById('profile-email-input').value = profile.email;
    }
    if (profile.emailUpdates !== undefined) {
        document.getElementById('profile-email-updates').checked = profile.emailUpdates;
    }
}

function saveUserProfile() {
    const profile = {
        name: document.getElementById('profile-full-name').value,
        email: document.getElementById('profile-email-input').value,
        emailUpdates: document.getElementById('profile-email-updates').checked
    };
    
    localStorage.setItem('userProfile', JSON.stringify(profile));
    
    // Update framework user state
    if (window.absFrameworkInstance && window.absFrameworkInstance.state) {
        window.absFrameworkInstance.state.user = {
            name: profile.name,
            email: profile.email,
            avatar: window.absFrameworkInstance.state.user.avatar
        };
    }
    
    closeUserProfileModal();
    
    // Show notification
    if (window.absFrameworkInstance) {
        window.absFrameworkInstance.showNotification('Profile updated successfully', 'success');
    }
}

// Wait for all dependencies to be ready before initializing framework
function waitForDependencies(callback, maxAttempts = 50, attempt = 0) {
    // Check if Tailwind CSS is loaded (via CDN script)
    const tailwindReady = window.Tailwind !== undefined || 
                         window.tailwindcss !== undefined ||
                         document.querySelector('script[src*="tailwindcss"]') !== null;
    
    // Check if Font Awesome is loaded
    const fontAwesomeReady = document.querySelector('link[href*="font-awesome"]') !== null;
    
    // Check if Alpine.js is loaded and initialized
    const alpineReady = window.Alpine !== undefined && typeof window.Alpine.data === 'function';
    
    const allReady = tailwindReady && fontAwesomeReady && alpineReady;
    
    if (allReady) {
        console.log('✅ All dependencies ready (Tailwind, Alpine, Font Awesome)');
        callback();
    } else if (attempt >= maxAttempts) {
        console.warn('⚠️ Some dependencies may not be fully loaded, proceeding anyway...', {
            tailwind: tailwindReady,
            fontAwesome: fontAwesomeReady,
            alpine: alpineReady
        });
        callback();
    } else {
        setTimeout(() => waitForDependencies(callback, maxAttempts, attempt + 1), 50);
    }
}

// Initialize framework when DOM is ready AND dependencies are loaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait for all dependencies before loading framework
    waitForDependencies(() => {
        const frameworkPath = '/unified-framework.js';
        
        console.log(`🔧 Loading unified framework from: ${frameworkPath}`);
        
        const script = document.createElement('script');
        script.src = frameworkPath;
        script.onload = () => {
            console.log(`✅ ABS Unified Framework loaded for Hub`);
            
            // Wait a bit more for Alpine to be fully ready
            setTimeout(() => {
                if (window.ABSUnifiedFramework && window.Alpine && typeof window.Alpine.data === 'function') {
                    window.absFrameworkInstance = new window.ABSUnifiedFramework(window.ABS_FRAMEWORK_CONFIG);
                    console.log('✅ ABSUnifiedFramework instance created for Hub:', window.absFrameworkInstance);
                    
                    // Load saved settings
                    const savedSettings = JSON.parse(localStorage.getItem('hubSettings') || '{}');
                    if (Object.keys(savedSettings).length > 0) {
                        applyHubSettings(savedSettings);
                    }
                    
                    // Load user profile
                    const savedProfile = JSON.parse(localStorage.getItem('userProfile') || '{}');
                    if (savedProfile.name && window.absFrameworkInstance && window.absFrameworkInstance.state) {
                        window.absFrameworkInstance.state.user = {
                            name: savedProfile.name,
                            email: savedProfile.email,
                            avatar: null
                        };
                    }
                    
                    // Update Alpine.js data if needed
                    if (window.Alpine && window.Alpine.data('hubFramework')) {
                        console.log('✅ Hub framework Alpine.js component registered');
                    }
                } else {
                    // Retry if Alpine not ready
                    setTimeout(() => {
                        if (window.ABSUnifiedFramework) {
                            window.absFrameworkInstance = new window.ABSUnifiedFramework(window.ABS_FRAMEWORK_CONFIG);
                            console.log('✅ ABSUnifiedFramework instance created for Hub (retry):', window.absFrameworkInstance);
                        }
                    }, 200);
                }
            }, 100);
        };
        script.onerror = () => {
            console.error(`❌ Failed to load unified framework from: ${frameworkPath}`);
        };
        document.head.appendChild(script);
    });
});

