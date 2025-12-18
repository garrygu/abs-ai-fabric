console.log('[API] api.js script starting...');
/**
 * Hub UI API Functions
 * Handles data fetching and rendering for various views.
 */

const GATEWAY_URL = 'http://localhost:8081';
console.log('[API] GATEWAY_URL set, defining functions...');

// ============== HELPERS ==============

/**
 * Returns an icon for the given asset class.
 */
function getAssetIcon(assetClass) {
    const icons = {
        'model': '🧠',
        'service': '⚙️',
        'tool': '🛠️',
        'dataset': '📚',
        'application': '📱'
    };
    return icons[assetClass?.toLowerCase()] || '📦';
}

/**
 * Capitalizes the first letter of a string.
 */
function capitalizeFirst(string) {
    if (!string) return '';
    return string.charAt(0).toUpperCase() + string.slice(1);
}

/**
 * Placeholder for asset detail view.
 */
function showAssetDetail(assetId) {
    alert('Asset Detail View for ' + assetId + ' coming soon!');
}

// ============== ASSETS VIEW ==============

/**
 * Loads and renders the Assets Table.
 */
async function loadAssetsTable() {
    console.log('[API] loadAssetsTable called');
    const container = document.getElementById('assets-table-container');
    if (!container) {
        console.error('[API] assets-table-container not found!');
        return;
    }

    container.innerHTML = '<div class="loading-spinner">Loading assets...</div>';
    console.log('[API] Set loading state, starting fetch...');

    try {
        const response = await fetch(`${GATEWAY_URL}/v1/assets`);
        if (!response.ok) throw new Error('Failed to fetch assets');

        let assets = [];
        const data = await response.json();

        // Parse response format
        if (Array.isArray(data)) assets = data;
        else if (data.assets) assets = data.assets;
        else if (data.value) assets = data.value;

        if (assets.length === 0) {
            container.innerHTML = '<div class="empty-state">No assets found.</div>';
            return;
        }

        // Render Table
        let html = `
        <table class="assets-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Interface</th>
                    <th>Status</th>
                    <th>Consumers</th>
                    <th>GPU</th>
                </tr>
            </thead>
            <tbody>
        `;

        assets.forEach(asset => {
            const statusClass = (asset.status || 'unknown').toLowerCase();
            const gpuIcon = asset.usage?.gpu ? '✅' : 'No';
            const consumers = asset.consumers?.length || 0;

            html += `
                <tr onclick="showAssetDetail('${asset.id}')" class="asset-row">
                    <td class="asset-name">
                        <span class="asset-icon">${getAssetIcon(asset.class)}</span>
                        ${asset.display_name || asset.id}
                    </td>
                    <td>${asset.class || '-'}</td>
                    <td><span class="badgish">${asset.interface || '-'}</span></td>
                    <td><span class="status-dot ${statusClass}">●</span> ${capitalizeFirst(asset.status || 'Unknown')}</td>
                    <td>${consumers}</td>
                    <td>${gpuIcon}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        container.innerHTML = html;

    } catch (error) {
        console.error('Error loading assets table:', error);
        container.innerHTML = `<div class="error-state" style="color: red; padding: 20px;">
            <h3>Failed to load assets</h3>
            <p>${error.message}</p>
        </div>`;
    }
}

// ============== APP STORE VIEW ==============

/**
 * Loads and renders the App Store (mock data for v1.0).
 */
async function loadAppStore2() {
    try {
        console.log('Loading App Store...');
        const container = document.getElementById('apps-store-content');
        if (!container) {
            console.error('App Store Container not found');
            return;
        }

        // Mock Store Data
        const storeApps = [
            { id: 'legal-researcher-pro', name: 'Legal Researcher Pro', description: 'Advanced caselaw search.', icon: '⚖️' },
            { id: 'contract-review-bot', name: 'Contract Review Bot', description: 'Auto-review NDAs.', icon: '📝' },
            { id: 'client-intake-flow', name: 'Client Intake Flow', description: 'Automated client onboarding.', icon: '👥' }
        ];

        let html = `
            <div class="section-header">
                <h2>🛒 App Store</h2>
                <p class="section-desc">Browse and install new AI applications.</p>
            </div>
            <div class="apps-grid">
        `;

        storeApps.forEach(app => {
            const props = JSON.stringify({
                name: app.name,
                description: app.description,
                icon: app.icon,
                status: 'Available',
                url: '#'
            });
            const propsStr = props.replace(/'/g, "&apos;").replace(/"/g, "&quot;");

            html += `
                <div class="component-wrapper" data-component="app-card"
                    data-props='${propsStr}'>
                    <!-- Fallback -->
                    <div class="app-card">
                        <h3>${app.name}</h3>
                        <button class="btn btn-secondary">Install</button>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;

        // Re-render components if available
        if (window.Components && typeof window.Components.renderAll === 'function') {
            window.Components.renderAll(container);
        }
    } catch (e) {
        console.error('Error in loadAppStore2:', e);
    }
}

// ============== OBSERVABILITY / ADMIN ==============

/**
 * Refreshes all service and model statuses.
 * (Placeholder - calls existing functions if they exist)
 */
async function refreshAllStatus() {
    console.log('Refreshing all status...');
    // Call existing functions if available
    if (typeof updateServiceSummary === 'function') {
        updateServiceSummary();
    }
    if (typeof updateAssetStats === 'function') {
        updateAssetStats();
    }
    if (typeof loadAdminModels === 'function') {
        loadAdminModels();
    }
}

// Expose functions globally for router and other modules
window.loadAssetsTable = loadAssetsTable;
window.loadAppStore2 = loadAppStore2;
window.refreshAllStatus = refreshAllStatus;
window.getAssetIcon = getAssetIcon;
window.capitalizeFirst = capitalizeFirst;
window.showAssetDetail = showAssetDetail;

console.log('[API] All functions exported to window, dispatching ready event...');
// Signal that API module is ready
document.dispatchEvent(new CustomEvent('api-ready'));
