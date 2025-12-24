/**
 * ABS Unified Header Web Component
 * 
 * A Web Component with Shadow DOM that provides a consistent header
 * across all ABS applications with app switching capability.
 * 
 * Usage in any app:
 * <script type="module" src="http://localhost:5173/abs-header.js"></script>
 * <abs-unified-header 
 *   app-id="contract-reviewer-v2"
 *   app-name="Contract Reviewer"
 *   app-icon="⚖️"
 *   hub-url="http://localhost:5173"
 *   gateway-url="http://localhost:8081">
 * </abs-unified-header>
 */

class ABSUnifiedHeader extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });

    // Configuration with defaults
    this.config = {
      appId: 'unknown',
      appName: 'ABS Application',
      appIcon: '📱',
      hubUrl: 'http://localhost:5173',
      gatewayUrl: 'http://localhost:8081',
      showAppLauncher: true,
      customMenuItems: []
    };

    this.state = {
      apps: [],
      showLauncher: false,
      searchQuery: '',
      loading: true
    };
  }

  static get observedAttributes() {
    return ['app-id', 'app-name', 'app-icon', 'hub-url', 'gateway-url', 'settings-url'];
  }

  attributeChangedCallback(name, oldValue, newValue) {
    const configMap = {
      'app-id': 'appId',
      'app-name': 'appName',
      'app-icon': 'appIcon',
      'hub-url': 'hubUrl',
      'gateway-url': 'gatewayUrl',
      'settings-url': 'settingsUrl'
    };

    if (configMap[name]) {
      this.config[configMap[name]] = newValue;
      this.render();
    }
  }

  async connectedCallback() {
    // Apply initial config from attributes
    this.config.appId = this.getAttribute('app-id') || this.config.appId;
    this.config.appName = this.getAttribute('app-name') || this.config.appName;
    this.config.appIcon = this.getAttribute('app-icon') || this.config.appIcon;
    this.config.hubUrl = this.getAttribute('hub-url') || this.config.hubUrl;
    this.config.gatewayUrl = this.getAttribute('gateway-url') || this.config.gatewayUrl;
    this.config.settingsUrl = this.getAttribute('settings-url') || null;

    // Check for global config override
    if (window.ABS_HEADER_CONFIG) {
      Object.assign(this.config, window.ABS_HEADER_CONFIG);
    }

    // Initial render
    this.render();

    // Fetch apps from gateway
    await this.loadApps();

    // Setup event listeners
    this.setupEventListeners();
  }

  async loadApps() {
    try {
      const response = await fetch(`${this.config.gatewayUrl}/v1/assets?class=app`);
      if (!response.ok) throw new Error('Failed to fetch apps');

      const data = await response.json();
      this.state.apps = Array.isArray(data) ? data : (data.assets || []);
      this.state.loading = false;
      this.render();
    } catch (error) {
      console.warn('[ABS Header] Failed to load apps:', error);
      this.state.apps = this.getFallbackApps();
      this.state.loading = false;
      this.render();
    }
  }

  getFallbackApps() {
    return [
      { id: 'contract-reviewer-v2', display_name: 'Contract Reviewer', metadata: { url: 'http://localhost:8082', category: 'Legal Apps' } },
      { id: 'legal-assistant', display_name: 'Legal Assistant', metadata: { url: 'http://localhost:7862', category: 'Legal Apps' } },
      { id: 'onyx-assistant', display_name: 'Onyx AI Assistant', metadata: { url: 'http://localhost:8000', category: 'AI Assistants' } },
      { id: 'open-webui', display_name: 'Open WebUI', metadata: { url: 'http://localhost:3200', category: 'AI Platforms' } }
    ];
  }

  getAppIcon(category) {
    const icons = {
      'Legal Apps': '⚖️',
      'AI Assistants': '🤖',
      'AI Platforms': '🔮',
      'Application': '📱'
    };
    return icons[category] || '📱';
  }

  get filteredApps() {
    if (!this.state.searchQuery) return this.state.apps;
    const query = this.state.searchQuery.toLowerCase();
    return this.state.apps.filter(app =>
      (app.display_name || app.id).toLowerCase().includes(query) ||
      (app.description || '').toLowerCase().includes(query)
    );
  }

  setupEventListeners() {
    const shadow = this.shadowRoot;

    // App launcher toggle
    shadow.querySelector('.launcher-btn')?.addEventListener('click', (e) => {
      e.stopPropagation();
      this.state.showLauncher = !this.state.showLauncher;
      this.render();
    });

    // Close launcher on outside click
    document.addEventListener('click', () => {
      if (this.state.showLauncher) {
        this.state.showLauncher = false;
        this.render();
      }
    });
  }

  handleAppClick(app) {
    const url = app.metadata?.url || `${this.config.hubUrl}/workspace/default/apps`;
    window.location.href = url;
  }

  goToHub() {
    window.location.href = `${this.config.hubUrl}/workspace/default/apps`;
  }

  goToSettings() {
    if (this.config.settingsUrl) {
      window.location.href = this.config.settingsUrl;
    } else {
      // Default: go to /settings on current origin
      window.location.href = '/settings';
    }
  }

  render() {
    const styles = `
      <style>
        :host {
          display: block;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        * {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
        }
        
        .header {
          background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
          color: white;
          padding: 0.75rem 1.5rem;
          display: flex;
          align-items: center;
          justify-content: space-between;
          position: sticky;
          top: 0;
          z-index: 1000;
          box-shadow: 0 2px 10px rgba(0,0,0,0.15);
        }
        
        .left-section {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
        
        .launcher-btn {
          background: rgba(255,255,255,0.1);
          border: none;
          color: white;
          padding: 0.5rem;
          border-radius: 6px;
          cursor: pointer;
          font-size: 1.25rem;
          transition: background 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 36px;
          height: 36px;
        }
        
        .launcher-btn:hover {
          background: rgba(255,255,255,0.2);
        }
        
        .app-info {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        
        .app-icon {
          font-size: 1.5rem;
        }
        
        .app-details h1 {
          font-size: 1rem;
          font-weight: 600;
          margin: 0;
        }
        
        .app-details p {
          font-size: 0.7rem;
          opacity: 0.8;
          margin: 0;
        }
        
        .right-section {
          display: flex;
          align-items: center;
          gap: 1rem;
        }
        
        .ces-badge {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          padding: 0.4rem 0.75rem;
          background: rgba(255, 107, 0, 0.15);
          border: 1px solid rgba(255, 107, 0, 0.3);
          border-radius: 6px;
          cursor: default;
          transition: all 0.2s;
          position: relative;
        }
        
        .ces-badge:hover {
          background: rgba(255, 107, 0, 0.25);
        }
        
        .ces-badge span {
          font-size: 0.7rem;
          font-weight: 600;
          color: #FF6B00;
        }
        
        /* CES Popover */
        .ces-popover {
          position: absolute;
          top: 100%;
          right: 0;
          margin-top: 0.5rem;
          width: 220px;
          background: white;
          border-radius: 10px;
          box-shadow: 0 8px 30px rgba(0,0,0,0.15);
          padding: 1rem;
          z-index: 1001;
          opacity: 0;
          visibility: hidden;
          transform: translateY(-5px);
          transition: all 0.2s ease;
        }
        
        .ces-badge:hover .ces-popover,
        .ces-badge.popover-open .ces-popover {
          opacity: 1;
          visibility: visible;
          transform: translateY(0);
        }
        
        .ces-popover::before {
          content: '';
          position: absolute;
          top: -6px;
          right: 20px;
          width: 12px;
          height: 12px;
          background: white;
          transform: rotate(45deg);
          box-shadow: -2px -2px 4px rgba(0,0,0,0.05);
        }
        
        .ces-popover-item {
          display: flex;
          align-items: center;
          gap: 0.6rem;
          padding: 0.4rem 0;
          font-size: 0.8rem;
          color: #374151;
        }
        
        .ces-popover-item span:first-child {
          font-size: 1rem;
        }
        
        .ces-popover-link {
          display: block;
          margin-top: 0.75rem;
          padding-top: 0.75rem;
          border-top: 1px solid #e5e7eb;
          text-align: center;
          color: #FF6B00;
          font-size: 0.8rem;
          font-weight: 600;
          text-decoration: none;
          cursor: pointer;
          transition: color 0.2s;
        }
        
        .ces-popover-link:hover {
          color: #cc5500;
        }
        
        .hub-btn, .icon-btn {
          background: rgba(255,255,255,0.15);
          border: 1px solid rgba(255,255,255,0.3);
          color: white;
          padding: 0.5rem 1rem;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.8rem;
          font-weight: 500;
          transition: all 0.2s;
        }
        
        .hub-btn:hover, .icon-btn:hover {
          background: rgba(255,255,255,0.25);
        }
        
        .icon-btn {
          padding: 0.5rem 0.6rem;
          font-size: 1rem;
        }
        
        .icon-btn.settings {
          background: rgba(255,255,255,0.1);
          border: none;
        }
        
        /* App Launcher Dropdown */
        .launcher-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0,0,0,0.3);
          z-index: 999;
        }
        
        .launcher-dropdown {
          position: fixed;
          top: 60px;
          left: 1rem;
          width: 320px;
          background: white;
          border-radius: 12px;
          box-shadow: 0 10px 40px rgba(0,0,0,0.2);
          z-index: 1000;
          overflow: hidden;
        }
        
        .launcher-header {
          padding: 1rem;
          border-bottom: 1px solid #e5e7eb;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .launcher-header h3 {
          font-size: 1rem;
          font-weight: 600;
          color: #1f2937;
        }
        
        .close-btn {
          background: none;
          border: none;
          font-size: 1.25rem;
          cursor: pointer;
          color: #6b7280;
        }
        
        .search-box {
          padding: 0.75rem 1rem;
          border-bottom: 1px solid #e5e7eb;
        }
        
        .search-box input {
          width: 100%;
          padding: 0.5rem 0.75rem;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          font-size: 0.875rem;
        }
        
        .search-box input:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }
        
        .apps-grid {
          padding: 1rem;
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 0.75rem;
          max-height: 300px;
          overflow-y: auto;
        }
        
        .app-tile {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 0.75rem;
          border-radius: 8px;
          cursor: pointer;
          transition: background 0.2s;
          border: 1px solid transparent;
        }
        
        .app-tile:hover {
          background: #f3f4f6;
          border-color: #e5e7eb;
        }
        
        .app-tile.current {
          background: #eff6ff;
          border-color: #3b82f6;
        }
        
        .app-tile-icon {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.25rem;
          margin-bottom: 0.5rem;
        }
        
        .app-tile-icon.legal { background: #dbeafe; }
        .app-tile-icon.ai { background: #fae8ff; }
        .app-tile-icon.platform { background: #dcfce7; }
        
        .app-tile-name {
          font-size: 0.7rem;
          font-weight: 500;
          color: #374151;
          text-align: center;
          line-height: 1.2;
        }
        
        .launcher-footer {
          padding: 1rem;
          border-top: 1px solid #e5e7eb;
        }
        
        .return-hub-btn {
          width: 100%;
          padding: 0.75rem;
          background: #f3f4f6;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.875rem;
          color: #374151;
          transition: background 0.2s;
        }
        
        .return-hub-btn:hover {
          background: #e5e7eb;
        }
        
        .hidden {
          display: none !important;
        }
      </style>
    `;

    const appsHtml = this.filteredApps.map(app => {
      const name = app.display_name || app.id;
      const category = app.metadata?.category || 'Application';
      const icon = this.getAppIcon(category);
      const isCurrent = app.id === this.config.appId;
      const iconClass = category.includes('Legal') ? 'legal' :
        category.includes('AI') ? 'ai' : 'platform';

      return `
        <div class="app-tile ${isCurrent ? 'current' : ''}" data-app-id="${app.id}">
          <div class="app-tile-icon ${iconClass}">${icon}</div>
          <div class="app-tile-name">${name}</div>
        </div>
      `;
    }).join('');

    this.shadowRoot.innerHTML = `
      ${styles}
      
      <header class="header">
        <div class="left-section">
          <button class="launcher-btn" title="App Launcher">⋮⋮⋮</button>
          <div class="app-info">
            <span class="app-icon">${this.config.appIcon}</span>
            <div class="app-details">
              <h1>${this.config.appName}</h1>
              <p>ABS AI Fabric</p>
            </div>
          </div>
        </div>
        
        <div class="right-section">
          <div class="ces-badge" id="ces-badge">
            <span>⚡</span>
            <span>Powered by ABS Workstation</span>
            <div class="ces-popover">
              <div class="ces-popover-item"><span>🎮</span><span>RTX Pro 6000</span></div>
              <div class="ces-popover-item"><span>💾</span><span>128GB RAM</span></div>
              <div class="ces-popover-item"><span>🧠</span><span>Local AI Processing</span></div>
              <a class="ces-popover-link" href="https://absworkstation.com?utm_source=ai_fabric&utm_campaign=ces_demo" target="_blank" rel="noopener">View Hardware →</a>
            </div>
          </div>
          <button class="icon-btn settings" onclick="this.getRootNode().host.goToSettings()" title="Settings">⚙️</button>
          <button class="hub-btn" onclick="this.getRootNode().host.goToHub()">🏠 Return to Hub</button>
        </div>
      </header>
      
      <!-- App Launcher Dropdown -->
      <div class="launcher-overlay ${this.state.showLauncher ? '' : 'hidden'}" id="overlay"></div>
      <div class="launcher-dropdown ${this.state.showLauncher ? '' : 'hidden'}">
        <div class="launcher-header">
          <h3>ABS Applications</h3>
          <button class="close-btn" id="close-launcher">✕</button>
        </div>
        <div class="search-box">
          <input type="text" placeholder="Find applications..." id="app-search" value="${this.state.searchQuery}">
        </div>
        <div class="apps-grid">
          ${this.state.loading ? '<div style="grid-column: span 3; text-align: center; padding: 2rem; color: #6b7280;">Loading apps...</div>' : appsHtml}
        </div>
        <div class="launcher-footer">
          <button class="return-hub-btn" onclick="this.getRootNode().host.goToHub()">
            🏠 Return to AI Fabric Hub
          </button>
        </div>
      </div>
    `;

    // Re-attach event listeners after render
    this.attachEventListeners();
  }

  attachEventListeners() {
    const shadow = this.shadowRoot;

    // Launcher button
    shadow.querySelector('.launcher-btn')?.addEventListener('click', (e) => {
      e.stopPropagation();
      this.state.showLauncher = !this.state.showLauncher;
      this.render();
    });

    // Close button
    shadow.querySelector('#close-launcher')?.addEventListener('click', () => {
      this.state.showLauncher = false;
      this.render();
    });

    // Overlay click
    shadow.querySelector('#overlay')?.addEventListener('click', () => {
      this.state.showLauncher = false;
      this.render();
    });

    // Search input
    shadow.querySelector('#app-search')?.addEventListener('input', (e) => {
      this.state.searchQuery = e.target.value;
      this.render();
    });

    // App tiles
    shadow.querySelectorAll('.app-tile').forEach(tile => {
      tile.addEventListener('click', () => {
        const appId = tile.dataset.appId;
        const app = this.state.apps.find(a => a.id === appId);
        if (app) this.handleAppClick(app);
      });
    });
  }
}

// Register the custom element
customElements.define('abs-unified-header', ABSUnifiedHeader);

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ABSUnifiedHeader;
}

console.log('✅ ABS Unified Header Web Component loaded');
