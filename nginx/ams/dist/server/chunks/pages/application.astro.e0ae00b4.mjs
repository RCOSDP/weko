/* empty css                           */import { c as createAstro, a as createComponent, r as renderTemplate, d as renderComponent, m as maybeRenderHead } from '../astro.4e122d94.mjs';
import 'html-escaper';
import { $ as $$Layout } from './_slug_.astro.687006e0.mjs';
/* empty css                                 */import 'path-to-regexp';
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
const $$Application = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$Application;
  return renderTemplate`${renderComponent($$result, "Layout", $$Layout, { "title": "MIBY | APPLICATION", "pageIndex": "application", "catch": "\u672A\u75C5\u30C7\u30FC\u30BF\u30D9\u30FC\u30B9\u30BF\u30A4\u30C8\u30EB\uFF06\u30AD\u30E3\u30C3\u30C1\u30B3\u30D4\u30FC", "class": "astro-MIBYINBQ" }, { "default": ($$result2) => renderTemplate`
  ${maybeRenderHead($$result2)}<main class="single astro-MIBYINBQ">
    <div class="bg-MainBg bg-no-repeat bg-center bg-cover pt-[180px] pb-16 mt-[-180px] mb-5 text-center text-white astro-MIBYINBQ">
      <h1 class="mt-16 mb-2.5 font-black text-5xl astro-MIBYINBQ">APPLICATION</h1>
      <p class="text-sm pb-14 astro-MIBYINBQ">利用許可申請</p>
    </div>
    <div class="breadcrumb flex px-5 astro-MIBYINBQ">
      <a class="text-miby-link-blue astro-MIBYINBQ" href="/"><span class="font-medium underline astro-MIBYINBQ">TOP</span></a>
      <p class="text-miby-dark-gray astro-MIBYINBQ">APPLICATION</p>
    </div>
    <div class="px-2.5 astro-MIBYINBQ">
      <div class="max-w-[748px] mx-auto mt-4 border-2 border-miby-link-blue rounded astro-MIBYINBQ">
        <div class="bg-miby-link-blue py-3 pl-5 astro-MIBYINBQ">
          <p class="text-white text-center font-bold astro-MIBYINBQ">利用許可申請</p>
        </div>
        <div class="bg-miby-bg-gray py-10 px-5 astro-MIBYINBQ">
          <form class="max-w-[500px] mx-auto astro-MIBYINBQ">
            <div class="mb-2.5 astro-MIBYINBQ">
              <label class="text-sm text-miby-black font-medium astro-MIBYINBQ" for="form-name">お名前<span class="text-miby-form-red astro-MIBYINBQ">*</span></label>
              <input id="form-name" type="text" class="mt-2.5 mb-1 py-2.5 px-5 rounded w-full placeholder:text-miby-thin-gray h-7 border border-miby-thin-gray astro-MIBYINBQ" placeholder="山田太郎">
              <p class="text-xs text-miby-form-red astro-MIBYINBQ">※お名前をご記入ください</p>
            </div>
            <div class="mb-2.5 astro-MIBYINBQ">
              <label class="text-sm text-miby-black font-medium astro-MIBYINBQ" for="form-kana">フリガナ<span class="text-miby-form-red astro-MIBYINBQ">*</span></label>
              <input id="form-kana" type="text" class="h-7 mt-2.5 mb-1 py-2.5 px-5 rounded w-full placeholder:text-miby-thin-gray border border-miby-thin-gray astro-MIBYINBQ" placeholder="ヤマダタロウ">
              <p class="text-xs text-miby-form-red astro-MIBYINBQ">※フリガナをご記入ください</p>
            </div>
            <div class="mb-2.5 astro-MIBYINBQ">
              <label class="text-sm text-miby-black font-medium astro-MIBYINBQ" for="form-mail">所属<span class="text-miby-form-red astro-MIBYINBQ">*</span></label>
              <input id="form-mail" type="text" class="mt-2.5 mb-1 py-2.5 px-5 rounded w-full placeholder:text-miby-thin-gray h-7 border border-miby-thin-gray astro-MIBYINBQ" placeholder="〇〇研究室">
              <p class="text-xs text-miby-form-red astro-MIBYINBQ">※所属をご記入ください</p>
            </div>
            <div class="mb-2.5 astro-MIBYINBQ">
              <label class="text-sm text-miby-black font-medium astro-MIBYINBQ" for="form-mail">メールアドレス<span class="text-miby-form-red astro-MIBYINBQ">*</span></label>
              <input id="form-mail" type="email" class="mt-2.5 mb-1 py-2.5 px-5 rounded w-full placeholder:text-miby-thin-gray h-7 border border-miby-thin-gray astro-MIBYINBQ" placeholder="sample@example.com">
              <p class="text-xs text-miby-form-red astro-MIBYINBQ">※メールアドレスをご記入ください</p>
            </div>
            <div class="mb-2.5 astro-MIBYINBQ">
              <label class="text-sm text-miby-black font-medium astro-MIBYINBQ" for="form-mail">電話番号</label>
              <input id="form-mail" type="email" class="mt-2.5 mb-1 py-2.5 px-5 rounded w-full placeholder:text-miby-thin-gray h-7 border border-miby-thin-gray astro-MIBYINBQ" placeholder="0000000000">
            </div>
            <div class="mb-2.5 astro-MIBYINBQ">
              <label class="text-sm text-miby-black font-medium astro-MIBYINBQ" for="form-mail">内容<span class="text-miby-form-red astro-MIBYINBQ">*</span></label>
              <select class="mt-2.5 mb-1 w-full text-miby-thin-gray border-miby-thin-gray rounded h-7 text-sm py-0 astro-MIBYINBQ"><option selected class="astro-MIBYINBQ">選択してください</option></select>
              <p class="text-xs text-miby-form-red astro-MIBYINBQ">※内容を選択ください</p>
            </div>
            <div class="mb-2.5 astro-MIBYINBQ">
              <label class="text-sm text-miby-black font-medium block w-full mb-2.5 astro-MIBYINBQ" for="form-file">ファイル</label>
              <input type="file" id="form-file" class="astro-MIBYINBQ">
              <!-- <input id="form-file" type="file" class="" /> -->
            </div>
            <div class="mb-2.5 astro-MIBYINBQ">
              <label class="text-sm text-miby-black font-medium astro-MIBYINBQ" for="textarea">備考</label>
              <textarea id="textarea" class="mt-2.5 mb-1 py-2.5 px-5 text-sm rounded w-full placeholder:text-miby-thin-gray h-44 border border-miby-thin-gray focus:ring focus:ring-miby-orange focus:border-none focus:outline-none astro-MIBYINBQ" name="contact-detail" placeholder="コメントがあればこちらに記載できます。"></textarea>
            </div>

            <button id="contactSubmit" class="text-white text-sm text-center bg-miby-orange border border-miby-orange font-medium py-1.5 px-5 mx-auto block min-w-[96px] rounded astro-MIBYINBQ">
              送信
            </button>
          </form>
        </div>
      </div>
    </div>
  </main>
` })}`;
}, "C:/11_Weko/code/IVIS/weko-front/src/pages/application.astro");

const $$file = "C:/11_Weko/code/IVIS/weko-front/src/pages/application.astro";
const $$url = "/application";

export { $$Application as default, $$file as file, $$url as url };
