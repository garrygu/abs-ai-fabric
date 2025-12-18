/**
 * Hub UI Router
 * Handles SPA-style view switching via hash-based navigation.
 */

/**
 * Route to a specific view.
 * @param {Event|null} event - Click event (optional).
 * @param {string} viewName - Name of the view to show (e.g., 'apps', 'assets').
 */
function route(event, viewName) {
    // 1. Update Hash
    window.location.hash = viewName;

    // 2. Hide all views
    document.querySelectorAll('.view-container').forEach(el => el.style.display = 'none');

    // 3. Show target view
    const target = document.getElementById('view-' + viewName);
    if (target) {
        target.style.display = 'block';
    }

    // 4. Update Nav State
    document.querySelectorAll('.main-nav-tab').forEach(el => el.classList.remove('active'));
    document.querySelector(`a[href="#${viewName}"]`)?.classList.add('active');

    // 5. Trigger view-specific data loaders
    if (viewName === 'assets' && typeof loadAssetsTable === 'function') {
        loadAssetsTable();
    }
    if ((viewName === 'observability' || viewName === 'admin') && typeof refreshAllStatus === 'function') {
        refreshAllStatus();
    }
}

/**
 * Switch between sub-tabs within the Apps view.
 * @param {string} tabName - 'installed' or 'store'.
 */
function switchAppTab(tabName) {
    if (tabName === 'installed') {
        document.getElementById('apps-installed-content').style.display = 'block';
        document.getElementById('apps-store-content').style.display = 'none';
    } else {
        document.getElementById('apps-installed-content').style.display = 'none';
        document.getElementById('apps-store-content').style.display = 'block';
        if (typeof loadAppStore2 === 'function') {
            loadAppStore2();
        }
    }

    // Update button states
    const buttons = document.querySelectorAll('.sub-nav .tab-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    if (tabName === 'installed') buttons[0]?.classList.add('active');
    else buttons[1]?.classList.add('active');
}

/**
 * Initialize router on page load.
 */
function initRouter() {
    console.log('[Router] initRouter called');
    console.log('[Router] window.loadAssetsTable:', typeof window.loadAssetsTable);

    const hash = window.location.hash.replace('#', '') || 'apps';
    console.log('[Router] Initial hash:', hash);
    route(null, hash);

    // Listen for back/forward navigation
    window.addEventListener('hashchange', () => {
        const newHash = window.location.hash.replace('#', '') || 'apps';
        route(null, newHash);
    });
}

// Wait for API module to signal it's ready before initializing router
// This ensures window.loadAssetsTable etc. are available
document.addEventListener('api-ready', function () {
    console.log('[Router] api-ready event received, calling initRouter...');
    initRouter();
});
