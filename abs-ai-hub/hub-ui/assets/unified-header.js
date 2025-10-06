/**
 * Unified Header Component for ABS AI Hub
 * Can be included in any application to provide consistent navigation
 */

class ABSUnifiedHeader {
    constructor(options = {}) {
        this.options = {
            showBreadcrumb: true,
            showQuickActions: true,
            customNavLinks: [],
            ...options
        };
        this.init();
    }

    init() {
        this.createHeaderHTML();
        this.injectHeader();
        this.setupEventListeners();
        this.updateActiveState();
    }

    createHeaderHTML() {
        const currentApp = this.getCurrentApp();
        const breadcrumb = this.createBreadcrumb(currentApp);
        const navLinks = this.createNavLinks();
        const quickActions = this.createQuickActions();

        this.headerHTML = `
            <div class="abs-unified-header">
                <div class="abs-header-container">
                    <!-- Logo and Brand -->
                    <div class="abs-logo-section">
                        <div class="abs-logo">🤖</div>
                        <div class="abs-brand">
                            <h1 class="abs-brand-title">ABS AI Hub</h1>
                            <p class="abs-brand-subtitle">Legal Workstation</p>
                        </div>
                    </div>

                    <!-- Navigation -->
                    <div class="abs-nav-section">
                        <nav class="abs-nav-links">
                            ${navLinks}
                        </nav>
                        ${breadcrumb}
                        ${quickActions}
                    </div>
                </div>
            </div>
        `;
    }

    getCurrentApp() {
        const hostname = window.location.hostname;
        const port = window.location.port;
        const pathname = window.location.pathname;

        // Detect current application
        if (hostname.includes('onyx') || pathname.includes('onyx')) {
            return { name: 'Onyx Assistant', type: 'app', url: 'http://localhost:8000' };
        }
        if (hostname.includes('rag') || pathname.includes('rag')) {
            return { name: 'RAG PDF Voice', type: 'app', url: 'http://localhost:8080' };
        }
        if (hostname.includes('contract') || pathname.includes('contract')) {
            return { name: 'Contract Reviewer', type: 'app', url: 'http://localhost:7860' };
        }
        if (pathname.includes('/manage')) {
            return { name: 'Asset Management', type: 'admin', url: 'http://localhost:3000/manage' };
        }
        if (pathname.includes('/admin')) {
            return { name: 'Admin Dashboard', type: 'admin', url: 'http://localhost:3000/admin' };
        }
        if (port === '3000' || pathname === '/') {
            return { name: 'Hub Home', type: 'hub', url: 'http://localhost:3000' };
        }
        
        return { name: 'Unknown App', type: 'app', url: '#' };
    }

    createNavLinks() {
        const links = [
            { id: 'home', label: '🏠 Home', url: 'http://localhost:3000', icon: '🏠' },
            { id: 'admin', label: '⚙️ Admin', url: 'http://localhost:3000/admin', icon: '⚙️' },
            { id: 'manage', label: '📊 Assets', url: 'http://localhost:3000/manage', icon: '📊' },
            { id: 'apps', label: '📱 Apps', url: 'http://localhost:3000/apps', icon: '📱' }
        ];

        // Add custom nav links if provided
        if (this.options.customNavLinks.length > 0) {
            links.push(...this.options.customNavLinks);
        }

        return links.map(link => `
            <a href="${link.url}" class="abs-nav-link" data-page="${link.id}">
                ${link.label}
            </a>
        `).join('');
    }

    createBreadcrumb(currentApp) {
        if (!this.options.showBreadcrumb) return '';

        return `
            <div class="abs-breadcrumb">
                <span>ABS AI Hub</span>
                <span class="abs-breadcrumb-separator">›</span>
                <span class="abs-current-app">${currentApp.name}</span>
            </div>
        `;
    }

    createQuickActions() {
        if (!this.options.showQuickActions) return '';

        return `
            <div class="abs-quick-actions">
                <button class="abs-quick-action" onclick="ABSHeader.refreshStatus()">🔄 Refresh</button>
                <button class="abs-quick-action" onclick="ABSHeader.showHelp()">❓ Help</button>
            </div>
        `;
    }

    injectHeader() {
        // Add CSS styles
        this.injectStyles();
        
        // Inject header HTML at the top of the body
        const body = document.body;
        if (body) {
            body.insertAdjacentHTML('afterbegin', this.headerHTML);
        }
    }

    injectStyles() {
        const styleId = 'abs-unified-header-styles';
        if (document.getElementById(styleId)) return;

        const styles = `
            <style id="${styleId}">
                .abs-unified-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 12px 0;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    position: sticky;
                    top: 0;
                    z-index: 1000;
                    margin-bottom: 20px;
                }

                .abs-header-container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 0 20px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .abs-logo-section {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }

                .abs-logo {
                    width: 36px;
                    height: 36px;
                    background: white;
                    border-radius: 6px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 18px;
                }

                .abs-brand-title {
                    font-size: 20px;
                    font-weight: bold;
                    margin: 0;
                    line-height: 1;
                }

                .abs-brand-subtitle {
                    font-size: 11px;
                    opacity: 0.8;
                    margin: 0;
                    line-height: 1;
                }

                .abs-nav-section {
                    display: flex;
                    align-items: center;
                    gap: 20px;
                }

                .abs-nav-links {
                    display: flex;
                    gap: 12px;
                }

                .abs-nav-link {
                    color: white;
                    text-decoration: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    transition: background-color 0.2s;
                    font-size: 13px;
                    font-weight: 500;
                }

                .abs-nav-link:hover {
                    background: rgba(255,255,255,0.1);
                }

                .abs-nav-link.active {
                    background: rgba(255,255,255,0.2);
                }

                .abs-breadcrumb {
                    display: flex;
                    align-items: center;
                    gap: 6px;
                    font-size: 13px;
                    opacity: 0.9;
                }

                .abs-breadcrumb-separator {
                    opacity: 0.6;
                }

                .abs-quick-actions {
                    display: flex;
                    gap: 8px;
                }

                .abs-quick-action {
                    background: rgba(255,255,255,0.1);
                    color: white;
                    border: none;
                    padding: 6px 10px;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 11px;
                    transition: background-color 0.2s;
                }

                .abs-quick-action:hover {
                    background: rgba(255,255,255,0.2);
                }

                @media (max-width: 768px) {
                    .abs-header-container {
                        flex-direction: column;
                        gap: 12px;
                    }
                    
                    .abs-nav-links {
                        flex-wrap: wrap;
                        justify-content: center;
                    }
                    
                    .abs-breadcrumb {
                        order: -1;
                    }
                }
            </style>
        `;

        document.head.insertAdjacentHTML('beforeend', styles);
    }

    setupEventListeners() {
        // Add click handlers for navigation links
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('abs-nav-link')) {
                e.preventDefault();
                const url = e.target.getAttribute('href');
                if (url && url !== '#') {
                    window.location.href = url;
                }
            }
        });
    }

    updateActiveState() {
        const currentApp = this.getCurrentApp();
        document.querySelectorAll('.abs-nav-link').forEach(link => {
            link.classList.remove('active');
            
            // Determine active state based on current app
            const linkPage = link.getAttribute('data-page');
            if (currentApp.type === 'hub' && linkPage === 'home') {
                link.classList.add('active');
            } else if (currentApp.type === 'admin' && linkPage === 'admin') {
                link.classList.add('active');
            } else if (currentApp.name === 'Asset Management' && linkPage === 'manage') {
                link.classList.add('active');
            }
        });
    }

    // Static methods for quick actions
    static refreshStatus() {
        // Try to call refresh functions if they exist
        if (typeof loadAssets === 'function') loadAssets();
        if (typeof loadAdminData === 'function') loadAdminData();
        if (typeof refreshModels === 'function') refreshModels();
        
        // Show feedback
        const btn = event.target;
        const originalText = btn.textContent;
        btn.textContent = '✅ Refreshed';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }

    static showHelp() {
        const currentApp = ABSHeader.getCurrentApp();
        alert(`ABS AI Hub Help

Current App: ${currentApp.name}

🏠 Home: Browse available applications and services
⚙️ Admin: Monitor system status and manage services  
📊 Assets: Configure apps, services, and models
📱 Apps: Direct access to application interfaces

Use the navigation links to switch between different sections.
Click "Refresh" to update status information.`);
    }

    static getCurrentApp() {
        const pathname = window.location.pathname;
        const hostname = window.location.hostname;

        if (hostname.includes('onyx') || pathname.includes('onyx')) {
            return { name: 'Onyx Assistant', type: 'app' };
        }
        if (hostname.includes('rag') || pathname.includes('rag')) {
            return { name: 'RAG PDF Voice', type: 'app' };
        }
        if (hostname.includes('contract') || pathname.includes('contract')) {
            return { name: 'Contract Reviewer', type: 'app' };
        }
        if (pathname.includes('/manage')) {
            return { name: 'Asset Management', type: 'admin' };
        }
        if (pathname.includes('/admin')) {
            return { name: 'Admin Dashboard', type: 'admin' };
        }
        return { name: 'Hub Home', type: 'hub' };
    }
}

// Global instance
let ABSHeader;

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    ABSHeader = new ABSUnifiedHeader();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ABSUnifiedHeader;
}
