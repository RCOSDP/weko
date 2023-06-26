/* empty css                           */import { c as createAstro, a as createComponent, r as renderTemplate, d as renderComponent, m as maybeRenderHead } from '../astro.4e122d94.mjs';
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
const $$Detail = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$Detail;
  const res = await fetch("https://ams-dev.ir.rcos.nii.ac.jp/api/v1.0/records/2/detail");
  const item = await res.json();
  return renderTemplate`${renderComponent($$result, "Layout", $$Layout, { "title": "MIBY", "pageIndex": "detail", "catch": "\u672A\u75C5\u30C7\u30FC\u30BF\u30D9\u30FC\u30B9\u30BF\u30A4\u30C8\u30EB\uFF06\u30AD\u30E3\u30C3\u30C1\u30B3\u30D4\u30FC" }, { "default": ($$result2) => renderTemplate`
  ${renderComponent($$result2, "Form", null, { "client:only": "vue", "client:component-hydration": "only", "client:component-path": "C:/11_Weko/code/IVIS/weko-front/src/components/Form.vue", "client:component-export": "default" })}
  ${maybeRenderHead($$result2)}<main class="max-w-[1024px] mx-auto px-2.5">
    <div class="breadcrumb flex w-full">
      <a class="text-miby-link-blue" href="/"><span class="font-medium underline">TOP</span></a>
      <a class="text-miby-link-blue" href="/"><span class="font-medium underline">大カテゴリー</span></a>
      <a class="text-miby-link-blue" href="/"><span class="font-medium underline">中カテゴリー</span></a>
      <a class="text-miby-link-blue" href="/"><span class="font-medium underline">小カテゴリー</span></a>
      <a class="text-miby-link-blue" href="/"><span class="font-medium underline">AAA</span></a>
      <p class="text-miby-dark-gray">詳細AAA</p>
    </div>
    <div class="flex flex-wrap w-full">
      ${renderComponent($$result2, "DetailContent", null, { "item": item, "client:only": "vue", "client:component-hydration": "only", "client:component-path": "C:/11_Weko/code/IVIS/weko-front/src/components/Detail/DetailContent.vue", "client:component-export": "default" })}
      ${renderComponent($$result2, "DetailSideMenu", null, { "item": item, "client:only": "vue", "client:component-hydration": "only", "client:component-path": "C:/11_Weko/code/IVIS/weko-front/src/components/Detail/DetailSideMenu.vue", "client:component-export": "default" })}
    </div>
  </main>
` })}`;
}, "C:/11_Weko/code/IVIS/weko-front/src/pages/detail.astro");

const $$file = "C:/11_Weko/code/IVIS/weko-front/src/pages/detail.astro";
const $$url = "/detail";

export { $$Detail as default, $$file as file, $$url as url };
