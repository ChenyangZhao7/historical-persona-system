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

// Most of these paths are *both* API endpoints and client-side routes. A
// browser navigation to /reverse sends `Accept: text/html`; an API call from
// axios sends `Accept: application/json, text/plain, */*`. Without this check
// the proxy forwarded page loads too, and the backend's SPA fallback returned
// the production index.html — whose hashed /assets/*.js does not exist on the
// dev server, so the browser refused to execute it and the page went blank on
// refresh. Returning the URL lets Vite serve its own index.html and React
// Router resolve the route client-side.
function apiProxy(target) {
  return {
    target,
    changeOrigin: true,
    bypass(req) {
      if (req.method === 'GET' && (req.headers.accept || '').includes('text/html')) {
        return req.url
      }
    },
  }
}

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: Object.fromEntries(
      backendRoutes.map(route => [route, apiProxy(API_TARGET)])
    ),
  },
})
