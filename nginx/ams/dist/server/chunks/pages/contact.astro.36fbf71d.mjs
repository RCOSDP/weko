/* empty css                           */import { c as createAstro, a as createComponent, r as renderTemplate, d as renderComponent, m as maybeRenderHead } from '../astro.4e122d94.mjs';
import 'html-escaper';
import { $ as $$Layout } from './_slug_.astro.687006e0.mjs';
/* empty css                             */import 'path-to-regexp';
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
const $$Contact = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$Contact;
  return renderTemplate`${renderComponent($$result, "Layout", $$Layout, { "title": "MIBY | CONTACT", "pageIndex": "contact", "catch": "\u672A\u75C5\u30C7\u30FC\u30BF\u30D9\u30FC\u30B9\u30BF\u30A4\u30C8\u30EB\uFF06\u30AD\u30E3\u30C3\u30C1\u30B3\u30D4\u30FC", "class": "astro-UW5KDBXL" }, { "default": ($$result2) => renderTemplate`
  ${maybeRenderHead($$result2)}<main class="single astro-UW5KDBXL">
    <div class="bg-MainBg bg-no-repeat bg-center bg-cover pt-[180px] pb-16 mt-[-180px] mb-5 text-center text-white astro-UW5KDBXL">
      <h1 class="mt-16 mb-2.5 font-black text-5xl astro-UW5KDBXL">CONTACT</h1>
      <p class="text-sm pb-14 astro-UW5KDBXL">お問い合わせ</p>
    </div>
    <div class="breadcrumb flex px-5 astro-UW5KDBXL">
      <a class="text-miby-link-blue astro-UW5KDBXL" href="/"><span class="font-medium underline astro-UW5KDBXL">TOP</span></a>
      <p class="text-miby-dark-gray astro-UW5KDBXL">CONTACT</p>
    </div>
    <div class="px-2.5 astro-UW5KDBXL">
      <div class="max-w-[748px] mx-auto mt-4 border-2 border-miby-link-blue rounded astro-UW5KDBXL">
        <div class="bg-miby-link-blue py-3 pl-5 astro-UW5KDBXL">
          <p class="text-white text-center font-bold astro-UW5KDBXL">お問い合わせ</p>
        </div>
        <div class="bg-miby-bg-gray py-10 px-5 astro-UW5KDBXL">
          <form class="max-w-[500px] mx-auto astro-UW5KDBXL">
            <div class="mb-2.5 astro-UW5KDBXL">
              <label class="text-sm text-miby-black font-medium astro-UW5KDBXL" for="form-name">お名前<span class="text-miby-form-red astro-UW5KDBXL">*</span></label>
              <input id="form-name" type="text" class="mt-2.5 mb-1 py-2.5 px-5 rounded w-full placeholder:text-miby-thin-gray h-7 border border-miby-thin-gray astro-UW5KDBXL" placeholder="山田太郎">
              <p class="text-xs text-miby-form-red astro-UW5KDBXL">※お名前をご記入ください</p>
            </div>
            <div class="mb-2.5 astro-UW5KDBXL">
              <label class="text-sm text-miby-black font-medium astro-UW5KDBXL" for="form-kana">フリガナ<span class="text-miby-form-red astro-UW5KDBXL">*</span></label>
              <input id="form-kana" type="text" class="mt-2.5 mb-1 py-2.5 px-5 rounded w-full placeholder:text-miby-thin-gray h-7 border border-miby-thin-gray astro-UW5KDBXL" placeholder="ヤマダタロウ">
              <p class="text-xs text-miby-form-red astro-UW5KDBXL">※フリガナをご記入ください</p>
            </div>
            <div class="mb-2.5 astro-UW5KDBXL">
              <label class="text-sm text-miby-black font-medium astro-UW5KDBXL" for="form-mail">メールアドレス<span class="text-miby-form-red astro-UW5KDBXL">*</span></label>
              <input id="form-mail" type="text" class="mt-2.5 mb-1 py-2.5 px-5 rounded w-full placeholder:text-miby-thin-gray h-7 border border-miby-thin-gray astro-UW5KDBXL" placeholder="sample@example.com">
              <p class="text-xs text-miby-form-red astro-UW5KDBXL">※メールアドレスをご記入ください</p>
            </div>
            <div class="mb-2.5 astro-UW5KDBXL">
              <label class="text-sm text-miby-black font-medium astro-UW5KDBXL" for="textarea">お問い合わせ内容<span class="text-miby-form-red astro-UW5KDBXL">*</span></label>
              <textarea id="textarea" class="mt-2.5 mb-1 w-full h-44 py-2.5 px-5 rounded placeholder:text-miby-thin-gray border border-miby-thin-gray focus:ring focus:ring-miby-orange focus:border-none focus:outline-none astro-UW5KDBXL" name="contact-detail" placeholder="制限公開されているデータを見るためにはどうすれば良いでしょうか。"></textarea>
              <p class="text-xs text-miby-form-red astro-UW5KDBXL">※お問い合わせ内容をご記入ください</p>
            </div>

            <button id="contactSubmit" class="text-white text-sm text-center bg-miby-orange border border-miby-orange font-medium py-1.5 px-5 mx-auto block min-w-[96px] rounded astro-UW5KDBXL">
              確認
            </button>
          </form>
        </div>
      </div>
    </div>
  </main>
` })}`;
}, "C:/11_Weko/code/IVIS/weko-front/src/pages/contact.astro");

const $$file = "C:/11_Weko/code/IVIS/weko-front/src/pages/contact.astro";
const $$url = "/contact";

export { $$Contact as default, $$file as file, $$url as url };
