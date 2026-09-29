import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    // maplibre-gl finds its worker file next to its own module,
    // so it must not be pre-bundled into Vite's cache
    exclude: ['maplibre-gl'],
  },
  server: {
    // in development, /api/* goes to the FastAPI server, so the browser sees one origin
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
