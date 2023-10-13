import { defineNuxtConfig } from 'nuxt/config';

export default defineNuxtConfig({
  typescript: {
    strict: true
  },
  vite: {
    css: {
      preprocessorOptions: {
        scss: {
          additionalData: '@import "@/assets/sass/variables.scss";'
        }
      }
    }
  },
  modules: ['@nuxtjs/tailwindcss', 'nuxt-lodash'],
  css: ['@/assets/sass/styles.scss'],
  ssr: false,
  app: {
    head: {
      htmlAttrs: { lang: 'ja' },
      title: 'AMS-alpha',
      meta: [
        { charset: 'utf-8' },
        { name: 'keywords', content: '' },
        { name: 'description', content: '' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1.0' }
      ],
      link: [
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Noto+Sans+JP&family=Noto+Serif+JP:wght@400&display=swap'
        },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/icon?family=Material+Icons+Outlined'
        }
      ]
    }
  },
  runtimeConfig: {
    public: {
      clientId: 'i2Xqlq1zaGvvhkTu9N7uyAZHTnMKAePHrFBrpghV',
      apiTimeout: 10000, // api response timeout (ms)
      tokenRefreshLimit: 600 // refresh access token before time (s)
    },
    clientSecret: 'w60r5CrI9qXN3vJKKcj4dWxHDV5owbCYqzaxtDUENYmdFKeMd08qJtMbBE0U'
  }
});
