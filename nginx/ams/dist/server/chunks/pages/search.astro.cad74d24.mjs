/* empty css                           */import { c as createAstro, a as createComponent, r as renderTemplate, d as renderComponent, m as maybeRenderHead } from '../astro.4e122d94.mjs';
import 'html-escaper';
import { B as ButtonClose, $ as $$Layout } from './_slug_.astro.687006e0.mjs';
import { useSSRContext, mergeProps } from 'vue';
import { ssrRenderAttrs, ssrRenderAttr, ssrRenderList, ssrInterpolate } from 'vue/server-renderer';
/* empty css                            */import { _ as _export_sfc } from './filelist.astro.885646cd.mjs';
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
/* empty css                              */
const _sfc_main$1 = {
  __name: 'ModalFilter',
  setup(__props, { expose: __expose }) {
  __expose();

function closeFilterModal() {
  document.getElementById("modalFilter").close();
}

const __returned__ = { closeFilterModal, get ButtonClose() { return ButtonClose } };
Object.defineProperty(__returned__, '__isScriptSetup', { enumerable: false, value: true });
return __returned__
}

};

function _sfc_ssrRender$1(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<dialog${
    ssrRenderAttrs(mergeProps({
      id: "modalFilter",
      class: "w-11/12 md:w-full max-w-[728px] mx-auto z-10"
    }, _attrs))
  } data-v-0ce09a55><div class="bg-miby-light-blue w-full rounded-t relative" data-v-0ce09a55><p class="text-white leading-[43px] pl-5 text-center font-medium relative" data-v-0ce09a55>フィルター</p><button id="" type="button" class="btn-close" data-v-0ce09a55><img${
    ssrRenderAttr("src", $setup.ButtonClose)
  } alt="×" data-v-0ce09a55></button></div><form method="dialog" class="border-4 border-miby-light-blue mt-[-3px] md:mt-0 md:border-0 rounded-b-md px-2.5" data-v-0ce09a55><div class="modalForm pt-2.5 overflow-y-auto scroll-smooth h-full" data-v-0ce09a55><div class="max-w-full mx-auto p-5" data-v-0ce09a55><div id="" class="mb-5" data-v-0ce09a55><button class="block mb-2 removeForm text-miby-black text-sm font-medium" data-v-0ce09a55><span class="icons icon-minus align-middle" data-v-0ce09a55>配布者</span></button><div class="pl-5" data-v-0ce09a55><div class="block checkbox" data-v-0ce09a55><input class="absolute" type="checkbox" name="publish-type" id="type-group" checked data-v-0ce09a55><label class="text-sm checkbox-label" for="type-group" data-v-0ce09a55>〇〇大学経済研究所（34293）</label></div><div class="block checkbox" data-v-0ce09a55><input class="absolute" type="checkbox" name="publish-type" id="type-publish" data-v-0ce09a55><label class="text-sm checkbox-label" for="type-publish" data-v-0ce09a55>〇〇大学史料編纂所（1799）</label></div><div class="block checkbox" data-v-0ce09a55><input class="absolute" type="checkbox" name="publish-type" id="type-private" data-v-0ce09a55><label class="text-sm checkbox-label" for="type-private" data-v-0ce09a55>JGSS研究センター（75）</label></div><div class="block checkbox" data-v-0ce09a55><input class="absolute" type="checkbox" name="publish-type" id="type-limited" data-v-0ce09a55><label class="text-sm checkbox-label" for="type-limited" data-v-0ce09a55>〇〇大学パネルデータ設計・解析センター（47）</label></div></div></div><div id="" class="mb-5" data-v-0ce09a55><button class="block mb-2 removeForm text-miby-black text-sm font-medium" data-v-0ce09a55><span class="icons icon-minus align-middle" data-v-0ce09a55>データの言語</span></button><div class="pl-5" data-v-0ce09a55><div class="block checkbox" data-v-0ce09a55><input class="absolute" type="checkbox" name="publish-type" id="type-group" checked data-v-0ce09a55><label class="text-sm checkbox-label" for="type-group" data-v-0ce09a55>jp（34293）</label></div><div class="block checkbox" data-v-0ce09a55><input class="absolute" type="checkbox" name="publish-type" id="type-publish" data-v-0ce09a55><label class="text-sm checkbox-label" for="type-publish" data-v-0ce09a55>en（1799）</label></div></div></div><div id="" class="mb-5" data-v-0ce09a55><button class="block mb-2 removeForm text-miby-black text-sm font-medium" data-v-0ce09a55><span class="icons icon-minus align-middle" data-v-0ce09a55>アクセス権</span></button><div class="pl-5" data-v-0ce09a55><div class="block checkbox" data-v-0ce09a55><input class="absolute" type="checkbox" name="publish-type" id="type-group" checked data-v-0ce09a55><label class="text-sm checkbox-label" for="type-group" data-v-0ce09a55>metadata only（34293）</label></div><div class="block checkbox" data-v-0ce09a55><input class="absolute" type="checkbox" name="publish-type" id="type-publish" data-v-0ce09a55><label class="text-sm checkbox-label" for="type-publish" data-v-0ce09a55>open（1799）</label></div><div class="block checkbox" data-v-0ce09a55><input class="absolute" type="checkbox" name="publish-type" id="type-publish" data-v-0ce09a55><label class="text-sm checkbox-label" for="type-publish" data-v-0ce09a55>restricted（75）</label></div></div></div><div id="" class="mb-5" data-v-0ce09a55><button class="block mb-2 removeForm text-miby-black text-sm font-medium" data-v-0ce09a55><span class="icons icon-minus align-middle" data-v-0ce09a55>対象地域</span></button><div class="pl-5 mt-5" data-v-0ce09a55><select id="" class="border border-miby-dark-gray rounded text-sm block w-[160px]" data-v-0ce09a55><option selected data-v-0ce09a55>選択してください</option><option value="" data-v-0ce09a55>北海道</option><option value="" data-v-0ce09a55>岩手県</option><option value="" data-v-0ce09a55>青森県</option></select></div></div><div id="" class="mb-5" data-v-0ce09a55><button class="block mb-2 removeForm text-miby-black text-sm font-medium" data-v-0ce09a55><span class="icons icon-minus align-middle" data-v-0ce09a55>対象時期</span></button><div class="pl-5 mt-5 flex flex-wrap items-center" data-v-0ce09a55><div class="relative" data-v-0ce09a55><input name="start" type="text" value="1875" class="border border-miby-thin-gray text-miby-black text-sm py-2.5 px-5 h-7 w-[160px] rounded focus:ring-miby-orange focus:border-miby-orange" data-v-0ce09a55></div><span class="px-2.5 align-top w-full md:w-[24px]" data-v-0ce09a55>—</span><div class="relative" data-v-0ce09a55><input name="end" type="text" value="2023" class="border border-miby-thin-gray text-miby-black text-sm py-2.5 px-5 h-7 w-[160px] rounded focus:ring-miby-orange focus:border-miby-orange" data-v-0ce09a55></div></div></div></div></div><div class="flex items-center justify-center pb-15 gap-4" data-v-0ce09a55><a id="seachClear" class="text-miby-black text-sm text-center font-medium border border-miby-black py-1.5 px-5 block min-w-[96px] rounded" data-v-0ce09a55> クリア </a><button id="filtersubmit" class="text-white text-sm text-center bg-miby-orange border border-miby-orange font-medium py-1.5 px-5 block min-w-[96px] rounded" data-v-0ce09a55> 適用 </button></div></form></dialog>`);
}
const _sfc_setup$1 = _sfc_main$1.setup;
_sfc_main$1.setup = (props, ctx) => {
  const ssrContext = useSSRContext()
  ;(ssrContext.modules || (ssrContext.modules = new Set())).add("src/components/Modal/ModalFilter.vue");
  return _sfc_setup$1 ? _sfc_setup$1(props, ctx) : undefined
};
const ModalFilter = /*#__PURE__*/_export_sfc(_sfc_main$1, [['ssrRender',_sfc_ssrRender$1],['__scopeId',"data-v-0ce09a55"]]);

const columns = [
	{
		name: "no",
		value: "No"
	},
	{
		name: "type_public",
		value: "公開区分"
	},
	{
		name: "title",
		value: "タイトル"
	},
	{
		name: "category",
		value: "分野"
	},
	{
		name: "creator",
		value: "作成者"
	},
	{
		name: "creator_group",
		value: "作成者所属"
	},
	{
		name: "admin",
		value: "管理者"
	},
	{
		name: "admin_group",
		value: "管理者所属"
	},
	{
		name: "publication_date",
		value: "掲載日"
	},
	{
		name: "update_date",
		value: "更新日"
	},
	{
		name: "type",
		value: "ヒト/動物/その他"
	},
	{
		name: "file",
		value: "ファイル"
	}
];

const _sfc_main = {
  __name: 'ModalDisplayItem',
  setup(__props, { expose: __expose }) {
  __expose();


const __returned__ = { get ButtonClose() { return ButtonClose }, get columns() { return columns } };
Object.defineProperty(__returned__, '__isScriptSetup', { enumerable: false, value: true });
return __returned__
}

};

function _sfc_ssrRender(_ctx, _push, _parent, _attrs, $props, $setup, $data, $options) {
  _push(`<dialog${
    ssrRenderAttrs(mergeProps({
      id: "modalDisplayItem",
      class: "w-11/12 md:w-full max-w-[728px] mx-auto z-10"
    }, _attrs))
  } data-v-14e36c27><div class="bg-miby-light-blue w-full rounded-t relative" data-v-14e36c27><p class="text-white leading-[43px] pl-5 text-center font-medium relative" data-v-14e36c27>項目表示</p><button id="" type="button" class="btn-close" data-v-14e36c27><img${
    ssrRenderAttr("src", $setup.ButtonClose)
  } alt="×" data-v-14e36c27></button></div><form method="dialog" class="border-4 border-miby-light-blue mt-[-3px] md:mt-0 md:border-0 rounded-b-md px-2.5" data-v-14e36c27><div class="modalForm pt-5 pb-10 overflow-y-auto scroll-smooth h-full" data-v-14e36c27><div class="max-w-[566px] mx-auto flex flex-wrap" data-v-14e36c27><!--[-->`);
  ssrRenderList($setup.columns, (column) => {
    _push(`<div class="checkbox" data-v-14e36c27><input class="absolute" type="checkbox" name="field"${
      ssrRenderAttr("value", column)
    }${
      ssrRenderAttr("id", 'category-' + column.name)
    } data-v-14e36c27><label class="text-sm checkbox-label"${
      ssrRenderAttr("for", 'category-' + column.name)
    } data-v-14e36c27>${
      ssrInterpolate(column.value)
    }</label></div>`);
  });
  _push(`<!--]--></div></div><div class="flex items-center justify-center py-5 gap-4" data-v-14e36c27><a id="seachClear" class="text-miby-black text-sm text-center font-medium border border-miby-black py-1.5 px-5 block min-w-[96px] rounded" data-v-14e36c27> クリア </a><button id="filtersubmit" class="text-white text-sm text-center bg-miby-orange border border-miby-orange font-medium py-1.5 px-5 block min-w-[96px] rounded" data-v-14e36c27> 適用 </button></div></form></dialog>`);
}
const _sfc_setup = _sfc_main.setup;
_sfc_main.setup = (props, ctx) => {
  const ssrContext = useSSRContext()
  ;(ssrContext.modules || (ssrContext.modules = new Set())).add("src/components/Modal/ModalDisplayItem.vue");
  return _sfc_setup ? _sfc_setup(props, ctx) : undefined
};
const ModalDisplayItem = /*#__PURE__*/_export_sfc(_sfc_main, [['ssrRender',_sfc_ssrRender],['__scopeId',"data-v-14e36c27"]]);

var __freeze = Object.freeze;
var __defProp = Object.defineProperty;
var __template = (cooked, raw) => __freeze(__defProp(cooked, "raw", { value: __freeze(raw || cooked.slice()) }));
var _a;
const $$Astro = createAstro();
const $$Search = createComponent(async ($$result, $$props, $$slots) => {
  const Astro2 = $$result.createAstro($$Astro, $$props, $$slots);
  Astro2.self = $$Search;
  return renderTemplate(_a || (_a = __template(["", '\n<script>\n  const buttons = document.querySelectorAll("button.btn-modal");\n  buttons.forEach((button) => {\n    button.addEventListener("click", () => {\n      if (button.dataset?.target) {\n        document.getElementById("modal" + button.dataset?.target).showModal();\n        // document.body.classList.add("overflow-hidden");\n        return false;\n      }\n    });\n  });\n<\/script>'])), renderComponent($$result, "Layout", $$Layout, { "title": "MIBY", "pageIndex": "search", "catch": "\u672A\u75C5\u30C7\u30FC\u30BF\u30D9\u30FC\u30B9\u30BF\u30A4\u30C8\u30EB\uFF06\u30AD\u30E3\u30C3\u30C1\u30B3\u30D4\u30FC" }, { "default": ($$result2) => renderTemplate`
  ${renderComponent($$result2, "Form", null, { "client:only": "vue", "client:component-hydration": "only", "client:component-path": "C:/11_Weko/code/IVIS/weko-front/src/components/Form.vue", "client:component-export": "default" })}
  ${maybeRenderHead($$result2)}<main class="max-w-[1024px] mx-auto px-2.5">
    <div class="breadcrumb flex w-full">
      <a class="text-miby-link-blue" href="/"><span class="font-medium underline">TOP</span></a>
      <p class="text-miby-dark-gray">検索結果リスト</p>
    </div>
    
    <div class="w-full">
      <div class="w-full">
        <div class="bg-miby-light-blue w-full">
          <p class="text-white leading-[43px] pl-5 icons icon-list font-bold">検索結果</p>
        </div>
        ${renderComponent($$result2, "SearchConditions", null, { "client:only": "vue", "isBlock": true, "client:component-hydration": "only", "client:component-path": "C:/11_Weko/code/IVIS/weko-front/src/components/SearchResult/SearchConditions.vue", "client:component-export": "default" })}
        <div class="p-5 bg-miby-bg-gray">
          <div class="flex flex-wrap justify-between items-center">
            <div class="checkbox">
              <input class="absolute" type="checkbox" name="checkList" id="checkAllResult">
              <label class="text-sm checkbox-label text-miby-black" for="checkAllResult">全てをマイリストに登録</label>
            </div>
            <a class="pl-1.5 md:pl-0 icons icon-download after" href=""><span class="underline text-sm text-miby-link-blue font-medium pr-1">検索結果全てをDLする</span></a>
          </div>
          <div class="max-w-[500px] ml-auto mt-4 mb-8 text-center">
            <div class="w-full flex gap-5 justify-end">
              <p class="icons-type icon-published">
                <span>一般公開</span>
              </p>
              <p class="icons-type icon-group">
                <span>グループ内公開</span>
              </p>
              <p class="icons-type icon-private">
                <span>非公開</span>
              </p>
              <p class="icons-type icon-limited">
                <span>制限公開</span>
              </p>
            </div>
          </div>
          <!-- <SearchResultTable client:only="vue" /> -->
          <!-- <SearchResultSummary client:only="vue" /> -->
          <!-- data="block"ってなに？ SearchResultBlockのpropだった -->
          ${renderComponent($$result2, "SearchResultBlock", null, { "client:only": "vue", "client:component-hydration": "only", "client:component-path": "C:/11_Weko/code/IVIS/weko-front/src/components/SearchResult/SearchResultBlock.vue", "client:component-export": "default" })}
        </div>
      </div>
    </div>
    ${renderComponent($$result2, "ModalFilter", ModalFilter, {})}
    ${renderComponent($$result2, "ModalDisplayItem", ModalDisplayItem, {})}
  </main>
` }));
}, "C:/11_Weko/code/IVIS/weko-front/src/pages/search.astro");

const $$file = "C:/11_Weko/code/IVIS/weko-front/src/pages/search.astro";
const $$url = "/search";

export { $$Search as default, $$file as file, $$url as url };
