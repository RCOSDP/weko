/* empty css                           */import { c as createAstro, a as createComponent, r as renderTemplate, d as renderComponent, m as maybeRenderHead, b as addAttribute } from '../astro.4e122d94.mjs';
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

const BtnGotoTopSp = "/images/btn/btn-gototop_sp.svg";

const $$Astro = createAstro();
const $$Index = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$Index;
  const res = await fetch(`https://ams-dev.ir.rcos.nii.ac.jp/api/v1.0/search?` + new URLSearchParams({
    size: "5"
  }));
  const latestItems = await res.json();
  const allItems = latestItems.hits.hits;
  return renderTemplate`${renderComponent($$result, "Layout", $$Layout, { "title": "MIBY", "pageIndex": "top", "catch": "\u672A\u75C5\u30C7\u30FC\u30BF\u30D9\u30FC\u30B9\u30BF\u30A4\u30C8\u30EB\uFF06\u30AD\u30E3\u30C3\u30C1\u30B3\u30D4\u30FC" }, { "default": ($$result2) => renderTemplate`
  ${renderComponent($$result2, "Form", null, { "client:only": "vue", "client:component-hydration": "only", "client:component-path": "C:/11_Weko/code/IVIS/weko-front/src/components/Form.vue", "client:component-export": "default" })}
  ${maybeRenderHead($$result2)}<main class="max-w-[1024px] mx-auto px-2.5">
    <div class="w-full">
      <div class="mb-5">
        ${renderComponent($$result2, "News", null, { "client:only": "vue", "client:component-hydration": "only", "client:component-path": "C:/11_Weko/code/IVIS/weko-front/src/components/News.vue", "client:component-export": "default" })}
      </div>
      <div class="mb-5">
        <div class="bg-miby-light-blue w-full">
          <p class="text-white leading-[43px] pl-5 icons icon-info font-bold">最新情報</p>
        </div>
        ${allItems.map((item) => renderTemplate`${renderComponent($$result2, "LatestInfo", null, { "item": item, "client:only": "vue", "client:component-hydration": "only", "client:component-path": "C:/11_Weko/code/IVIS/weko-front/src/components/LatestInfo.vue", "client:component-export": "default" })}`)}
      </div>
      <div class="mb-5">
        ${renderComponent($$result2, "KeywordRank", null, { "client:only": "vue", "client:component-hydration": "only", "client:component-path": "C:/11_Weko/code/IVIS/weko-front/src/components/KeywordRank.vue", "client:component-export": "default" })}
      </div>
    </div>
    <button id="page-top" class="block lg:hidden w-10 h-10 z-40 fixed right-5 bottom-2.5"><img${addAttribute(BtnGotoTopSp, "src")} alt=""></button>
  </main>
` })}`;
}, "C:/11_Weko/code/IVIS/weko-front/src/pages/index.astro");

const $$file = "C:/11_Weko/code/IVIS/weko-front/src/pages/index.astro";
const $$url = "";

export { $$Index as default, $$file as file, $$url as url };
