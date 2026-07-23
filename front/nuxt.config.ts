// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  css: ['~/assets/reset.css','~/assets/variables.css', '~/assets/style.css'],

  runtimeConfig:{
      apiTarget: process.env.NUXT_API_TARGET ?? 'http://api:8000',
      public: {
          apiBase: process.env.NUXT_PUBLIC_API_BASE ?? '',
      }
  },


  modules: ['@vite-pwa/nuxt'],
  pwa: {
    strategies: 'injectManifest',
    srcDir: '.',
    filename: 'sw.js',
    registerType: 'autoUpdate',
    manifest: {
      name: 'XPro Support',
      short_name: 'XPro',
      theme_color: '#ffffff',
      icons: [
        {
          src: 'pwa-192x192.svg',
          sizes: '192x192',
          type: 'image/svg+xml',
        },
        {
          src: 'pwa-512x512.svg',
          sizes: '512x512',
          type: 'image/svg+xml',
        },
        {
          src: 'pwa-512x512.svg',
          sizes: '512x512',
          type: 'image/svg+xml',
          purpose: 'any maskable',
        },
      ],
    },
    workbox: {
      navigateFallback: '/',
      globPatterns: ['**/*.{js,css,html,png,svg,ico}'],
    },
    devOptions: {
      enabled: true,
      suppressWarnings: true,
      navigateFallbackAllowlist: [/^\/$/],
      type: 'module',
    },
  }
})