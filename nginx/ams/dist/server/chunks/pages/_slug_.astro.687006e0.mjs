/* empty css                           */import { c as createAstro, a as createComponent, r as renderTemplate, b as addAttribute, m as maybeRenderHead, d as renderComponent, e as renderSlot, f as renderHead } from '../astro.4e122d94.mjs';
import 'html-escaper';

const Logo1$1 = "/images/logo/logo01.png";

const Logo2 = "/images/logo/logo02.png";

const Logo1 = "/images/logo/logo_b.png";

const ButtonClose = "/images/btn/btn-close.svg";

const ButtonIndex = "/images/btn/btn-indextree.svg";

var __freeze$2 = Object.freeze;
var __defProp$2 = Object.defineProperty;
var __template$2 = (cooked, raw) => __freeze$2(__defProp$2(cooked, "raw", { value: __freeze$2(raw || cooked.slice()) }));
var _a$2;
const $$Astro$4 = createAstro();
const $$MenuMobile = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro$4, $$props, $$slots);
  Astro2.self = $$MenuMobile;
  return renderTemplate(_a$2 || (_a$2 = __template$2(["", `<dialog id="MobileMenu">
  <div class="modal-left">
    <button class="btn-close" @click="closeModal('MobileMenu')">
      <img`, ' alt="close">\n    </button>\n    <div class="wrapper">\n      <div class="flex flex-wrap items-end border-b border-miby-thin-gray p-2.5 mb-2.5">\n        <p class="mr-[5px]">\n          <a href="/"><img', ' alt="MIBY"></a>\n        </p>\n        <p class="mr-[5px]">\n          <a href="/"><img', ' alt="MIBY"></a>\n        </p>\n        <p class="text-miby-black text-xs w-full">\u672A\u75C5\u30C7\u30FC\u30BF\u30D9\u30FC\u30B9\u30BF\u30A4\u30C8\u30EB\uFF06\u30AD\u30E3\u30C3\u30C1\u30B3\u30D4\u30FC</p>\n      </div>\n      <div class="p-5">\n        <i class="icons icon-lang-b"></i>\n        <span class="ml-2.5 mr-5 text-miby-orange underline">JP</span>\n        <a class="text-miby-thin-gray" href="/en">EN</a>\n      </div>\n      <div class="w-full bg-miby-mobile-blue py-1 pl-5">\n        <img', ' alt="\u30A4\u30F3\u30C7\u30C3\u30AF\u30B9\u30C4\u30EA\u30FC">\n      </div>\n      <div class="index-tree__list p-2.5 overflow-y-auto">\n        <details class="index-tree__items">\n          <summary>\u30D3\u30B8\u30CD\u30B9\u30B5\u30A4\u30A8\u30F3\u30B9\u7CFB</summary>\n          <div class="index-tree__detail">\n            <details class="index-tree__item">\n              <summary>\u30D3\u30B8\u30CD\u30B9\u30B5\u30A4\u30A8\u30F3\u30B9\u7CFB</summary>\n              <div class="index-tree__detail"></div>\n            </details>\n          </div>\n        </details>\n        <details class="index-tree__items">\n          <summary>\u6570\u7406\u7269\u8CEA\u7CFB</summary>\n          <div class="index-tree__detail">\n            <details class="index-tree__item">\n              <summary>\u6570\u7406\u7269\u8CEA\u7CFB</summary>\n              <div class="index-tree__detail"></div>\n            </details>\n          </div>\n        </details>\n        <details class="index-tree__items" open>\n          <summary>\u30B7\u30B9\u30C6\u30E0\u60C5\u5831\u7CFB</summary>\n          <div class="index-tree__detail">\n            <details class="index-tree__item">\n              <summary>\u30B7\u30B9\u30C6\u30E0\u5206\u6790\u3068\u8A2D\u8A08\u306E\u57FA\u790E</summary>\n              <div class="index-tree__detail"></div>\n            </details>\n            <details class="index-tree__item">\n              <summary>Comparative analysis of the efficacy and safety of oral versus intravenous\n                administration of corticosteroids in the management of acute exacerbations of asthma\n                in adult patients: A randomized controlled trial</summary>\n              <div class="index-tree__detail"></div>\n            </details>\n          </div>\n        </details>\n        <details class="index-tree__items" open>\n          <summary>\u7BA1\u7406\u30B7\u30B9\u30C6\u30E0\u306E\u8A2D\u8A08</summary>\n          <div class="index-tree__detail">\n            <details class="index-tree__item">\n              <summary>\u30C7\u30FC\u30BF\u30D9\u30FC\u30B9\u7BA1\u7406\u30B7\u30B9\u30C6\u30E0\u306E\u8A2D\u8A08\u3068\u6700\u9069\u5316</summary>\n              <div class="index-tree__detail"></div>\n            </details>\n            <details class="index-tree__item">\n              <summary>\u30BD\u30D5\u30C8\u30A6\u30A7\u30A2\u958B\u767A\u30E9\u30A4\u30D5\u30B5\u30A4\u30AF\u30EB\u3068\u54C1\u8CEA\u7BA1\u7406</summary>\n              <div class="index-tree__detail"></div>\n            </details>\n            <details class="index-tree__item" open>\n              <summary>\u30CD\u30C3\u30C8\u30EF\u30FC\u30AF\u30BB\u30AD\u30E5\u30EA\u30C6\u30A3\u3068\u60C5\u5831\u4FDD\u8B77\u306E\u6226\u7565</summary>\n              <ul class="index-tree__list">\n                <li>\n                  <a class="underline" href="">Effects of a combined aerobic and resistance exercise program on insulin\n                    sensitivity and glucose metabolism in older adults with type 2 diabetes: A\n                    randomized controlled trial</a>\n                </li>\n                <li>\n                  <a class="underline" href="">Efficacy and safety of a novel topical treatment for moderate-to-severe atopic\n                    dermatitis: Results from a phase III randomized controlled trial</a>\n                </li>\n              </ul>\n            </details>\n            <details class="index-tree__item">\n              <summary>\u30D3\u30C3\u30B0\u30C7\u30FC\u30BF\u89E3\u6790\u3068\u6A5F\u68B0\u5B66\u7FD2\u306E\u5FDC\u7528</summary>\n              <div class="index-tree__detail"></div>\n            </details>\n          </div>\n        </details>\n      </div>\n    </div>\n  </div>\n</dialog>\n\n<script>\n  function closeModal(target) {\n    document.getElementById(target).close();\n  }\n<\/script>'])), maybeRenderHead($$result), addAttribute(ButtonClose, "src"), addAttribute(Logo1, "src"), addAttribute(Logo2, "src"), addAttribute(ButtonIndex, "src"));
}, "C:/11_Weko/code/IVIS/weko-front/src/components/Menu/MenuMobile.astro");

var __freeze$1 = Object.freeze;
var __defProp$1 = Object.defineProperty;
var __template$1 = (cooked, raw) => __freeze$1(__defProp$1(cooked, "raw", { value: __freeze$1(raw || cooked.slice()) }));
var _a$1;
const $$Astro$3 = createAstro();
const $$Header = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro$3, $$props, $$slots);
  Astro2.self = $$Header;
  return renderTemplate(_a$1 || (_a$1 = __template$1(["", '<header class="top-0 inset-x-0">\n  <div class="flex md:items-center justify-between relative p-2.5 md:p-5 bg-miby-header-blue">\n    <div class="flex items-end flex-wrap md:flex-nowrap">\n      <p class="mr-[5px]">\n        <a href="/"><img', ' alt="MIBY"></a>\n      </p>\n      <p class="mr-[5px]">\n        <a href="/"><img', ' alt="MIBY"></a>\n      </p>\n      <p class="text-white text-xs w-full md:w-auto mt-2.5 md:mt-auto">\n        \u672A\u75C5\u30C7\u30FC\u30BF\u30D9\u30FC\u30B9\u30BF\u30A4\u30C8\u30EB<br class="hidden md:block">\uFF06\u30AD\u30E3\u30C3\u30C1\u30B3\u30D4\u30FC\n      </p>\n    </div>\n    <nav class="flex justify-end items-flex-start md:items-center">\n      <div class="hidden md:block w-24 relative">\n        <button class="btn-lang icons icon-lang text-sm text-white py-1 px-3">JP</button>\n        <div class="link-lang absolute top-full mt-1 w-40 bg-white text-sm rounded hidden">\n          <p class="px-3 py-1 text-white bg-miby-orange w-full rounded-tl rounded-tr">JP</p>\n          <a class="block px-3 py-1 text-miby-black w-full" href="/en">EN</a>\n        </div>\n      </div>\n      <button class="h-5 md:h-auto md:border md:py-1 pl-2 pr-2.5 rounded icons icon-logout">\n        <span class="hidden md:inline-block text-white">\u30ED\u30B0\u30A2\u30A6\u30C8</span>\n      </button>\n      <button class="btn-sp-menu block md:hidden">\n        <span class="inline-block h-[1px] w-full bg-white"></span>\n        <span class="inline-block h-[1px] w-full bg-white"></span>\n        <span class="inline-block h-[1px] w-full bg-white"></span>\n      </button>\n    </nav>\n  </div>\n  ', "\n  ", '\n</header>\n\n<script>\n  function fixedMenu() {\n    var IndexTree = document.getElementById("IndexTree");\n    var IndexTreeHeight = IndexTree?.offsetHeight;\n    if (window.scrollY >= IndexTreeHeight) {\n      IndexTree?.classList.add("scroll");\n    } else {\n      IndexTree?.classList.remove("scroll");\n    }\n  }\n\n  window.addEventListener("load", fixedMenu);\n  window.addEventListener("resize", fixedMenu);\n  window.addEventListener("scroll", fixedMenu);\n\n  document.querySelector(".btn-lang").addEventListener("click", () => {\n    document.querySelector(".link-lang").classList.toggle("hidden");\n  });\n\n  var mobileMenuBtn = document.querySelector(".btn-sp-menu");\n  mobileMenuBtn?.addEventListener("click", () => {\n    mobileMenuBtn?.classList.toggle("active");\n    if (mobileMenuBtn?.classList.contains("active")) {\n      document.getElementById("MobileMenu").showModal();\n      document.body.classList.add("overflow-hidden");\n    } else {\n      document.body.classList.remove("overflow-hidden");\n    }\n  });\n<\/script>'])), maybeRenderHead($$result), addAttribute(Logo1$1, "src"), addAttribute(Logo2, "src"), renderComponent($$result, "IndexTree", null, { "client:only": "vue", "client:component-hydration": "only", "client:component-path": "C:/11_Weko/code/IVIS/weko-front/src/components/IndexTree.vue", "client:component-export": "default" }), renderComponent($$result, "MenuMobile", $$MenuMobile, {}));
}, "C:/11_Weko/code/IVIS/weko-front/src/components/Header.astro");

const $$Astro$2 = createAstro();
const $$Footer = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro$2, $$props, $$slots);
  Astro2.self = $$Footer;
  return renderTemplate`${maybeRenderHead($$result)}<footer class="sticky top-[100vh] bg-gradient-to-r from-miby-blue to-miby-dark-blue mt-24 pt-16 px-5 pb-10">
  <div class="flex flex-wrap gap-10 lg:gap-20 items-end justify-between">
    <div class="flex">
      <ul class="text-white text-sm mr-20">
        <li class="mb-1.5">
          <a class="underline" href="/"><span>TOP</span></a>
        </li>
        <li class="mb-1.5">
          <a class="underline" href="/about"><span>ABOUT</span></a>
        </li>
        <li class="mb-1.5">
          <a class="underline" href="/help"><span>HELP</span></a>
        </li>
        <li class="mb-1.5">
          <a class="underline" href="/faq"><span>FAQ</span></a>
        </li>
        <li>
          <a class="underline" href="/contact"><span>CONTACT</span></a>
        </li>
      </ul>
      <ul class="text-white text-sm">
        <li class="mb-1.5">
          <a class="underline" href="/application"><span>利用許可申請</span></a>
        </li>
        <li class="mb-1.5">
          <a class="underline" href="/about"><span>運営機関</span></a>
        </li>
        <li>
          <a class="underline" href="#"><span>プライバシーポリシー</span></a>
        </li>
      </ul>
    </div>
    <div class="flex flex-wrap lg:flex-nowrap items-center max-w-[245px] lg:max-w-full mx-auto md:mr-0">
      <p class="mr-[5px]">
        <a href="/"><img${addAttribute(Logo1$1, "src")} alt="MIBY"></a>
      </p>
      <p class="mr-[5px]">
        <a href="/"><img${addAttribute(Logo2, "src")} alt="MIBY"></a>
      </p>
      <p class="text-white text-xs leading-6">
        未病データベースタイトル＆キャッチコピー<br><span class="block text-[10px]">Copyright 2023 IVIS inc.</span>
      </p>
    </div>
  </div>
</footer>`;
}, "C:/11_Weko/code/IVIS/weko-front/src/components/Footer.astro");

var __freeze = Object.freeze;
var __defProp = Object.defineProperty;
var __template = (cooked, raw) => __freeze(__defProp(cooked, "raw", { value: __freeze(raw || cooked.slice()) }));
var _a;
const $$Astro$1 = createAstro();
const $$Layout = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro$1, $$props, $$slots);
  Astro2.self = $$Layout;
  const { title, catch: catch2, pageIndex } = Astro2.props;
  return renderTemplate(_a || (_a = __template(['<html lang="ja-jp" class="scroll-smooth h-full">\n  <head>\n    <meta charset="UTF-8">\n    <meta name="keywords" content="">\n    <meta name="description" content="">\n    <meta name="viewport" content="width=device-width">\n    <link rel="icon" type="image/svg+xml" href="/favicon.svg">\n    <link rel="preconnect" href="https://fonts.googleapis.com">\n    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP&family=Noto+Serif+JP:wght@400&display=swap" rel="stylesheet">\n    <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Outlined" rel="stylesheet">\n    <meta name="generator"', ">\n    <title>", '</title>\n    <!-- <script src="../js/script.js"><\/script> -->\n  ', "</head>\n  <body", ' class="font-notoSans bg-miby-border-gray h-full">\n    <div class="bg-miby-gray">\n      ', "\n      ", "\n	    ", "\n    </div>\n  </body></html>"])), addAttribute(Astro2.generator, "content"), title, renderHead($$result), addAttribute(pageIndex, "id"), renderComponent($$result, "Header", $$Header, {}), renderSlot($$result, $$slots["default"]), renderComponent($$result, "Footer", $$Footer, {}));
}, "C:/11_Weko/code/IVIS/weko-front/src/layouts/Layout.astro");

const $$Astro = createAstro();
const $$slug = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$slug;
  const id = Astro2.params.slug;
  const res = await fetch(`https://ams-dev.ir.rcos.nii.ac.jp/api/v1.0/records/${id}/detail`);
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
}, "C:/11_Weko/code/IVIS/weko-front/src/pages/detail/[slug].astro");

const $$file = "C:/11_Weko/code/IVIS/weko-front/src/pages/detail/[slug].astro";
const $$url = "/detail/[slug]";

const _slug_ = /*#__PURE__*/Object.freeze(/*#__PURE__*/Object.defineProperty({
  __proto__: null,
  default: $$slug,
  file: $$file,
  url: $$url
}, Symbol.toStringTag, { value: 'Module' }));

export { $$Layout as $, ButtonClose as B, _slug_ as _ };
