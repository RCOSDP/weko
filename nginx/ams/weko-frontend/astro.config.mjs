import { defineConfig } from 'astro/config';
import vue from '@astrojs/vue';
import tailwind from "@astrojs/tailwind";

import node from "@astrojs/node";

// https://astro.build/config
export default defineConfig({
  integrations: [tailwind(), vue()],
  output: "server",
  adapter: node({
    mode: "standalone"
  })
});