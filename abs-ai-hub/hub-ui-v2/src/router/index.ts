import { createRouter, createWebHistory } from 'vue-router'

// Workspace-ready routes (/:workspaceId prefix for future multi-workspace support)
const routes = [
    {
        path: '/',
        redirect: '/workspace/default/apps'
    },
    {
        path: '/workspace/:workspaceId',
        redirect: to => `/workspace/${to.params.workspaceId}/apps`
    },
    {
        path: '/workspace/:workspaceId/apps',
        name: 'apps',
        component: () => import('@/views/Apps/AppsView.vue'),
        meta: { title: 'Apps' }
    },
    {
        path: '/workspace/:workspaceId/apps/:appId',
        name: 'app-detail',
        component: () => import('@/views/Apps/AppDetailView.vue'),
        meta: { title: 'App Detail' }
    },
    {
        path: '/workspace/:workspaceId/assets',
        name: 'assets',
        component: () => import('@/views/Assets/AssetsView.vue'),
        meta: { title: 'Assets' }
    },
    {
        path: '/workspace/:workspaceId/assets/:assetId',
        name: 'asset-detail',
        component: () => import('@/views/Assets/AssetDetailView.vue'),
        meta: { title: 'Asset Detail' }
    },
    {
        path: '/workspace/:workspaceId/observability',
        name: 'observability',
        component: () => import('@/views/Observability/ObservabilityView.vue'),
        meta: { title: 'Observability' }
    },
    {
        path: '/workspace/:workspaceId/admin',
        name: 'admin',
        component: () => import('@/views/Admin/AdminView.vue'),
        meta: { title: 'Admin' }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// Update document title on navigation
router.beforeEach((to) => {
    document.title = `${to.meta.title || 'Hub'} | AI Fabric`
})

export default router
