import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  // Set the third parameter to '' to load all env regardless of the `VITE_` prefix.
  const env = loadEnv(mode, process.cwd(), '')
  
  // Determine CES mode from environment variables
  const isCESMode = 
    env.CES_MODE === 'true' || 
    env.CES_MODE === '1' ||
    env.VITE_CES_MODE === 'true' || 
    env.VITE_CES_MODE === '1'
  
  return {
    plugins: [vue()],
    define: {
      // Inject CES mode flag at build time
      // Supports both CES_MODE (build) and VITE_CES_MODE (dev) environment variables
      __CES_MODE__: JSON.stringify(isCESMode)
    },
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
      port: 5173,
      proxy: {
        // Proxy API requests to Gateway during development
        '/v1': {
          target: 'http://localhost:8081',
          changeOrigin: true
        }
      }
    }
  }
})
