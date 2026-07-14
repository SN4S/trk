// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  css: ['~/assets/reset.css','~/assets/variables.css', '~/assets/style.css'],
  runtimeConfig:{
      public: {
          apiBase: process.env.NUXT_PUBLIC_API_BASE ?? 'http://localhost:8000',
      }
  }
})
