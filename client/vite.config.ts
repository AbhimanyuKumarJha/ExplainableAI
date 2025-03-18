import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiBasePath = (env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '')
  const apiTarget = (env.VITE_DEV_API_TARGET ?? 'http://127.0.0.1:8000').replace(
    /\/$/,
    '',
  )
  const escapedApiBasePath = apiBasePath.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

  return {
    plugins: [react()],
    server: {
      proxy: apiBasePath.startsWith('/')
        ? {
            [apiBasePath]: {
              target: apiTarget,
              changeOrigin: true,
              rewrite: (path) =>
                path.replace(new RegExp(`^${escapedApiBasePath}`), ''),
            },
          }
        : undefined,
    },
  }
})
