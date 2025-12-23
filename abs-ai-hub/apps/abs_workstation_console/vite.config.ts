import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': resolve(__dirname, 'src')
        }
    },
    server: {
        port: 5200,
        proxy: {
            '/api': {
                target: 'http://localhost:8081',
                changeOrigin: true
            }
        }
    },
    define: {
        // Default to true for CES app - can be overridden with CES_MODE=false
        __CES_MODE__: JSON.stringify(process.env.CES_MODE !== 'false')
    }
})
