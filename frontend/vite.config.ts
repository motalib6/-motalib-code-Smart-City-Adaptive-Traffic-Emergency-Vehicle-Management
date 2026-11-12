import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'SMARTFLOW ODISHA — Intelligent Traffic & Emergency Management',
        short_name: 'SMARTFLOW',
        description:
          'AI-assisted adaptive traffic signals, YOLO vehicle detection, safe ambulance priority and connected junctions (GEC Hackathon 2026, PS-03).',
        start_url: '/',
        display: 'standalone',
        background_color: '#0B1220',
        theme_color: '#0B1220',
        icons: [
          { src: '/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icons/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // Cache the app shell; API/WebSocket traffic is never cached.
        navigateFallback: '/index.html',
        runtimeCaching: [
          {
            urlPattern: ({ url }) => url.pathname.startsWith('/api/') || url.pathname.startsWith('/ws/'),
            handler: 'NetworkOnly',
          },
        ],
      },
    }),
  ],
})
