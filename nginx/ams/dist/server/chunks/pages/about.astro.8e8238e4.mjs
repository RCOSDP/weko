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
const $$About = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$About;
  return renderTemplate`${renderComponent($$result, "Layout", $$Layout, { "title": "MIBY | ABOUT", "pageIndex": "about", "catch": "\u672A\u75C5\u30C7\u30FC\u30BF\u30D9\u30FC\u30B9\u30BF\u30A4\u30C8\u30EB\uFF06\u30AD\u30E3\u30C3\u30C1\u30B3\u30D4\u30FC" }, { "default": ($$result2) => renderTemplate`
  ${maybeRenderHead($$result2)}<main class="single">
    <div class="bg-MainBg bg-no-repeat bg-center bg-cover pt-[180px] pb-16 mt-[-180px] mb-5 text-center text-white">
      <h1 class="mt-16 mb-2.5 font-black text-5xl">ABOUT</h1>
      <p class="text-sm pb-14">MIBYO - 未病データベースについて -</p>
    </div>
    <div class="breadcrumb flex px-5">
      <a class="text-miby-link-blue" href="/"><span class="font-medium underline">TOP</span></a>
      <p class="text-miby-dark-gray">ABOUT</p>
    </div>
    <div class="max-w-[598px] mx-auto mt-4">
      <h2 class="text-center font-bold text-xl text-miby-black mb-8">
        未病に関するデータを取り扱います
      </h2>
      <p class="text-justify text-miby-black leading-7 px-2.5 md:px-0 pb-10">
        未病データベースに関する説明が入ります。未病データベースに関する説明が入ります。未病データベースに関する説明が入ります。未病データベースに関する説明が入ります。未病データベースに関する説明が入ります。未病データベースに関する説明が入ります。未病データベースに関する説明が入ります。未病データベースに関する説明が入ります。未病データベースに関する説明が入ります。未病データベースに関する説明が入ります。未病データベースに関する説明が入ります。未病データベースに関する説明が入ります。未病データベースに関する説明が入ります。未病データベースに関する説明が入ります。
      </p>
    </div>
  </main>
` })}`;
}, "C:/11_Weko/code/IVIS/weko-front/src/pages/about.astro");

const $$file = "C:/11_Weko/code/IVIS/weko-front/src/pages/about.astro";
const $$url = "/about";

export { $$About as default, $$file as file, $$url as url };
