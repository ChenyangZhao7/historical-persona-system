import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In dev the frontend runs on :5173 and the API on :8000, so every backend
// route is proxied. Without this, requests hit the Vite server and get
// index.html back with a 200, which reads as "empty database" in the UI.
const API_TARGET = process.env.VITE_API_TARGET || 'http://127.0.0.1:8000'

const backendRoutes = [
  '/figures',
  '/analyze',
  '/match',
  '/predict',
  '/reconstruct',
  '/reverse',
  '/chat',
  '/graph',
  '/locations',
  '/relics',
]

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: Object.fromEntries(
      backendRoutes.map(route => [route, { target: API_TARGET, changeOrigin: true }])
    ),
  },
})
