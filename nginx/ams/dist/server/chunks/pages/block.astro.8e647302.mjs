/* empty css                           */import { c as createAstro, a as createComponent, r as renderTemplate, d as renderComponent } from '../astro.4e122d94.mjs';
import 'html-escaper';
import { $ as $$Layout } from './_slug_.astro.687006e0.mjs';
import 'path-to-regexp';
import 'cookie';
import '@astrojs/internal-helpers/path';
import 'kleur/colors';
import 'fs';
import 'http';
import 'tls';
import 'mime';
import 'string-width';
import 'slash';

const $$Astro = createAstro();
const $$Block = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$Block;
  return renderTemplate`${renderComponent($$result, "Layout", $$Layout, { "title": "MIBY", "pageIndex": "search", "catch": "\u672A\u75C5\u30C7\u30FC\u30BF\u30D9\u30FC\u30B9\u30BF\u30A4\u30C8\u30EB\uFF06\u30AD\u30E3\u30C3\u30C1\u30B3\u30D4\u30FC" }, { "default": ($$result2) => renderTemplate`
  ${renderComponent($$result2, "Form", null, { "client:only": "vue", "client:component-hydration": "only", "client:component-path": "C:/11_Weko/code/IVIS/weko-front/src/components/Form.vue", "client:component-export": "default" })}
  ${renderComponent($$result2, "SearchResultPage", null, { "client:only": "vue", "page": "block", "client:component-hydration": "only", "client:component-path": "C:/11_Weko/code/IVIS/weko-front/src/components/SearchResult/SearchResultPage.vue", "client:component-export": "default" })}
` })}`;
}, "C:/11_Weko/code/IVIS/weko-front/src/pages/search/block.astro");

const $$file = "C:/11_Weko/code/IVIS/weko-front/src/pages/search/block.astro";
const $$url = "/search/block";

export { $$Block as default, $$file as file, $$url as url };
