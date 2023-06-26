
<script setup>
import SearchResultTable from "./SearchResultTable.vue";
import SearchResultSummary from "./SearchResultSummary.vue";
import SearchResultBlock from "./SearchResultBlock.vue";
import ButtonFilter from "/images/btn/btn-filter.svg";
</script>

<template>
  <div class="breadcrumb flex px-5">
    <a class="text-miby-link-blue" href="/"><span class="font-medium underline">TOP</span></a>
    <p class="text-miby-dark-gray">検索結果リスト</p>
  </div>
  <div class="w-full">
    <div class="w-full">
      <div class="bg-miby-light-blue w-full">
        <p class="text-white leading-[43px] pl-5 icons icon-list font-bold">検索結果</p>
      </div>
      <div class="w-full bg-miby-searchtags-blue p-5">
        <div class="mb-2.5 flex flex-wrap">
          <p class="text-sm font-medium text-miby-dark-gray">
            [公開区分]<span class="ml-px mr-2 text-miby-black">テキストテキスト</span>
          </p>
          <p class="text-sm font-medium text-miby-dark-gray">
            [ダウンロード区分]<span class="ml-px mr-2 text-miby-black">テキストテキスト</span>
          </p>
          <p class="text-sm font-medium text-miby-dark-gray">
            [タイトル]<span class="ml-px mr-2 text-miby-black"
              >テキストテキストテキストテキストテキストテキストテキスト</span
            >
          </p>
          <p class="text-sm font-medium text-miby-dark-gray">
            [分野]<span class="ml-px mr-2 text-miby-black">医学・生物学</span>
          </p>
          <p class="text-sm font-medium text-miby-dark-gray">
            [掲載日]<span class="ml-px mr-2 text-miby-black">2023/04/18-2023/04/19</span>
          </p>
          <p class="text-sm font-medium text-miby-dark-gray">
            [更新日]<span class="ml-px mr-2 text-miby-black">2023/04/18-2023/04/19</span>
          </p>
          <p class="text-sm font-medium text-miby-dark-gray">
            [作成者]<span class="ml-px mr-2 text-miby-black">テキストテキストテキストテキスト</span>
          </p>
          <p class="text-sm font-medium text-miby-dark-gray">
            [ヒト/動物/その他]<span class="ml-px mr-2 text-miby-black">ヒト/動物/その他</span>
          </p>
          <p class="text-sm font-medium text-miby-dark-gray">
            [リポジトリ]<span class="ml-px mr-2 text-miby-black">テキストテキスト</span>
          </p>
          <p class="text-sm font-medium text-miby-dark-gray">
            [表示件数]<span class="ml-px mr-2 text-miby-black">テキストテキスト</span>
          </p>
        </div>
        <div class="flex flex-wrap justify-between items-center">
          <div class="flex flex-wrap gap-5 items-center">
            <div class="text-miby-black text-sm font-medium flex items-center">
              <span>表示件数：</span>
              <select
                class="cursor-pointer bg-white border border-gray-300 text-miby-black py-0 text-[10px] pr-1 rounded block"
              >
                <option value="5">5</option>
                <option value="10">10</option>
                <option value="20" selected>20</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
              <span class="ml-1">/986</span>
            </div>
            <div class="text-miby-black text-sm font-medium">
              <span>表示形式：</span>
              <div class="inline-flex gap-x-0.5">
                <button class="icons icon-display display1"></button>
                <button class="icons icon-display display2 active"></button>
                <button class="icons icon-display display3"></button>
              </div>
            </div>
            <div class="text-miby-black text-sm font-medium mr-10">
              <span>並び順：</span>
              <button class="icons icon-order"></button>
            </div>
          </div>

          <div class="">
            <a class="block cursor-pointer">
              <img src="{ButtonFilter}" alt="フィルター" />
            </a>
          </div>
        </div>
      </div>
      <div class="p-5 bg-miby-bg-gray">
        <div class="flex flex-wrap justify-between items-center">
          <div class="checkbox">
            <input class="absolute" type="checkbox" name="checkList" id="checkAllResult" />
            <label class="text-sm checkbox-label text-miby-black" for="checkAllResult"
              >全てをマイリストに登録</label
            >
          </div>
          <a class="pl-1.5 md:pl-0 icons icon-download after" href=""
            ><span class="underline text-sm text-miby-link-blue font-medium pr-1"
              >検索結果全てをDLする</span
            ></a
          >
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
        <div id="searchList">
        <!-- <SearchResultTable client:only="vue" /> -->
        <!-- <SearchResultSummary client:only="vue" /> -->
        <SearchResultBlock client:only="vue" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// import {computed} from 'vue'

// const props = defineProps({
//     data: {
//         type: [String],
//     }
// })

// console.log(props);
</script>