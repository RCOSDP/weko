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

var __freeze = Object.freeze;
var __defProp = Object.defineProperty;
var __template = (cooked, raw) => __freeze(__defProp(cooked, "raw", { value: __freeze(raw || cooked.slice()) }));
var _a;
const $$Astro = createAstro();
const $$Summary = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$Summary;
  return renderTemplate(_a || (_a = __template(["", '\n\n\n<script>\n  // const buttons = document.querySelectorAll("button.btn-modal");\n  // buttons.forEach((button) => {\n  //   button.addEventListener("click", () => {\n  //     if (button.dataset?.target) {\n  //       document.getElementById("modal" + button.dataset?.target).showModal();\n  //       return false;\n  //     }\n  //   });\n  // });\n<\/script>'])), renderComponent($$result, "Layout", $$Layout, { "title": "MIBY", "pageIndex": "search", "catch": "\u672A\u75C5\u30C7\u30FC\u30BF\u30D9\u30FC\u30B9\u30BF\u30A4\u30C8\u30EB\uFF06\u30AD\u30E3\u30C3\u30C1\u30B3\u30D4\u30FC" }, { "default": ($$result2) => renderTemplate`
  ${renderComponent($$result2, "Form", null, { "client:only": "vue", "client:component-hydration": "only", "client:component-path": "C:/11_Weko/code/IVIS/weko-front/src/components/Form.vue", "client:component-export": "default" })}
  ${renderComponent($$result2, "SearchResultPage", null, { "client:only": "vue", "page": "summary", "client:component-hydration": "only", "client:component-path": "C:/11_Weko/code/IVIS/weko-front/src/components/SearchResult/SearchResultPage.vue", "client:component-export": "default" })}
` }));
}, "C:/11_Weko/code/IVIS/weko-front/src/pages/search/summary.astro");

const $$file = "C:/11_Weko/code/IVIS/weko-front/src/pages/search/summary.astro";
const $$url = "/search/summary";

export { $$Summary as default, $$file as file, $$url as url };
