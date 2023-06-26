/* empty css                          */import { c as createAstro, a as createComponent, r as renderTemplate, d as renderComponent, m as maybeRenderHead, b as addAttribute } from './astro.4e122d94.mjs';
import 'html-escaper';
import { $ as $$Layout } from './pages/_slug_.astro.687006e0.mjs';
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

const BtnGotoTop = "/images/btn/btn-gototop.svg";

var __freeze = Object.freeze;
var __defProp = Object.defineProperty;
var __template = (cooked, raw) => __freeze(__defProp(cooked, "raw", { value: __freeze(raw || cooked.slice()) }));
var _a;
const $$Astro = createAstro();
const prerender = true;
const $$Faq = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$Faq;
  return renderTemplate(_a || (_a = __template(["", `

<script>
document.addEventListener('DOMContentLoaded', () => {
  // anker
  let elms = document.querySelectorAll('.anker');
  if (elms) {
    elms.forEach((elm) => { 
      elm.addEventListener('click', (e) => {
        e.preventDefault();
        const target = document.querySelector(e.currentTarget.getAttribute('href'));
        if (target) {
          target.scrollIntoView({
            behavior: "smooth",
          });
        }
      })
    })
  }

  // pageTop
  let pagetopBtn = document.getElementById("page-top");
  pagetopBtn?.addEventListener("click", (e) => {
    window.scrollTo({top: 0, behavior: 'smooth'})
    return false;
  });
})
<\/script>`])), renderComponent($$result, "Layout", $$Layout, { "title": "MIBY | FAQ", "pageIndex": "faq", "catch": "\u672A\u75C5\u30C7\u30FC\u30BF\u30D9\u30FC\u30B9\u30BF\u30A4\u30C8\u30EB\uFF06\u30AD\u30E3\u30C3\u30C1\u30B3\u30D4\u30FC" }, { "default": ($$result2) => renderTemplate`
  ${maybeRenderHead($$result2)}<main class="single">
    <div class="bg-MainBg bg-no-repeat bg-center bg-cover pt-[180px] pb-16 mt-[-180px] mb-5 text-center text-white">
      <h1 class="mt-16 mb-2.5 font-black text-5xl">FAQ</h1>
      <p class="text-sm pb-14">よくあるご質問</p>
    </div>
    <div class="breadcrumb flex px-5">
      <a class="text-miby-link-blue" href="/"><span class="font-medium underline">TOP</span></a>
      <p class="text-miby-dark-gray">FAQ</p>
    </div>
    <div class="max-w-[748px] mx-auto mt-4">
      <div class="bg-miby-light-blue py-3 pl-5">
        <p class="text-white font-bold">FAQ</p>
      </div>
      <div class="bg-miby-bg-gray py-10 px-5">
        <div class="faq-index">
          <p class="faq-index__title">FAQカテゴリー</p>
          <div class="faq-index__item">
            <a class="anker" href="#faq1">未病データベースについてカテゴリー01<i class="icons icon-arrow"></i></a>
          </div>
          <div class="faq-index__item">
            <a class="anker" href="#faq2">本サイトの使い方についてカテゴリー02<i class="icons icon-arrow"></i></a>
          </div>
          <div class="faq-index__item">
            <a class="anker" href="#faq3">データの登録方法についてカテゴリー03<i class="icons icon-arrow"></i></a>
          </div>
          <div class="faq-index__item">
            <a class="anker" href="#faq4">登録料や使用料についてカテゴリー04<i class="icons icon-arrow"></i></a>
          </div>
          <div class="faq-index__item">
            <a class="anker" href="#faq5">その他カテゴリー05<i class="icons icon-arrow"></i></a>
          </div>
        </div>
        <div id="faq1" class="faq-content">
          <h2 class="faq-content__title">未病データベースについてカテゴリー01</h2>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？〇〇は△△でしょうか？〇〇は△△でしょうか？〇〇は△△でしょうか？〇〇は△△でしょうか？〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
        </div>
        <div id="faq2" class="faq-content">
          <h2 class="faq-content__title">本サイトの使い方についてカテゴリー02</h2>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
        </div>
        <div id="faq3" class="faq-content">
          <h2 class="faq-content__title">データの登録方法についてカテゴリー03</h2>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
        </div>
        <div id="faq4" class="faq-content">
          <h2 class="faq-content__title">データの登録方法についてカテゴリー04</h2>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
        </div>
        <div id="faq5" class="faq-content">
          <h2 class="faq-content__title">データの登録方法についてカテゴリー05</h2>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
          <details class="faq-content__list">
            <summary><span class="">〇〇は△△でしょうか？</span></summary>
            <p class="text-miby-black font-sm"><span>〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。〇〇は□□です。</span></p>
          </details>
        </div>
        <div class="relative mt-16 pb-10">
          <a class="block text-center underline text-sm text-miby-link-blue" href="/contact">お問い合わせはこちら</a>
          <button id="page-top" class="lg:block w-10 h-10 absolute right-5 top-0"><img${addAttribute(BtnGotoTop, "src")} alt=""></button>
        </div>
      </div>
    </div>
  </main>
` }));
}, "C:/11_Weko/code/IVIS/weko-front/src/pages/faq.astro");

const $$file = "C:/11_Weko/code/IVIS/weko-front/src/pages/faq.astro";
const $$url = "/faq";

export { $$Faq as default, $$file as file, prerender, $$url as url };
