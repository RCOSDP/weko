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
    buildAssetsDir: '/ams/_nuxt/',
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
      clientId: 'qIx5G7vr9ZF8Fy4171xUSaG5ZVd51FdHCDrl8oM7',
      redirectURI: 'http://localhost:3000',
      apiTimeout: 10000, // api response timeout (ms)
      tokenRefreshLimit: 600, // refresh access token before time (s)
      contact: {
        use: 'smtp' // email type used for contact (smtp or gmail)
      },
      dlRanking: {
        display: 5 // number of items displayed in DL ranking
      }
    },
    clientSecret: 'LLwKok4nIrOs1Kn44IrDWJFIOdiAGGgDHVlbC1QCu4Vc8jQRjuPSXSxJjQw0',
    // email setting for contact
    contact: {
      to: 'sample@sample.co.jp',
      subject: 'Contact subject',
      smtp: {
        host: 'localhost',
        port: '1025',
        user: 'user',
        pass: 'pass'
      },
      gmail: {
        address: 'sample@gmail.com', // Gmail address
        pass: 'rcir twcq kjwh cnfu' // application password
      }
    }
  }
});
