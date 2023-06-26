<script setup>
import ButtonFilter from "/images/btn/btn-filter.svg";
import ButtonDisplayItem from "/images/btn/btn-display-item.svg";
import { ref, computed } from "vue";

const props = defineProps({
  page: String,
  searchConditions: Object,
  typePublic: Array,
  typeDownload: Array,
  category: Array,
})

const displayAmount = JSON.parse(sessionStorage.getItem('display-value'))
const sortConditions = JSON.parse(sessionStorage.getItem('sort'))
const displayValue = ref(displayAmount ?? 20)
const sort = ref(sortConditions ?? [])

const emit = defineEmits(['display-value', 'sort', 'open-filter', 'open-display'])
</script>

<template>
    <div>
        <div class="w-full bg-miby-searchtags-blue p-5">
          <div class="mb-2.5 flex flex-wrap">
            <p class="text-sm font-medium text-miby-dark-gray">
              [公開区分]<span class="ml-px mr-2 text-miby-black">{{ typePublic?.join(', ') ?? null }}</span>
            </p>
            <p class="text-sm font-medium text-miby-dark-gray">
              [ダウンロード区分]<span class="ml-px mr-2 text-miby-black">{{ typeDownload?.join(', ') ?? null }}</span>
            </p>
            <p class="text-sm font-medium text-miby-dark-gray">
              [タイトル]<span class="ml-px mr-2 text-miby-black"
                >{{searchConditions?.text ? searchConditions?.text[3] : null}}</span
              >
            </p>
            <p class="text-sm font-medium text-miby-dark-gray">
              [分野]<span class="ml-px mr-2 text-miby-black">{{ category?.join(', ') ?? null }}</span>
            </p>
            <p class="text-sm font-medium text-miby-dark-gray">
              [掲載日]<span class="ml-px mr-2 text-miby-black">{{ searchConditions?.publishedStart }}-{{ searchConditions?.publishedEnd }}</span>
            </p>
            <p class="text-sm font-medium text-miby-dark-gray">
              [更新日]<span class="ml-px mr-2 text-miby-black">{{ searchConditions?.updatedStart }}-{{ searchConditions?.updatedEnd }}</span>
            </p>
            <p class="text-sm font-medium text-miby-dark-gray">
              [作成者]<span class="ml-px mr-2 text-miby-black"
                >{{ searchConditions?.text ? searchConditions?.text[7] : null }}</span
              >
            </p>
            <p class="text-sm font-medium text-miby-dark-gray">
              [ヒト/動物/その他]<span class="ml-px mr-2 text-miby-black">{{ searchConditions?.text ? searchConditions?.text[8] : null }}</span>
            </p>
            <p class="text-sm font-medium text-miby-dark-gray">
              [リポジトリ]<span class="ml-px mr-2 text-miby-black">{{ searchConditions?.text ? searchConditions?.text[9] : null }}</span>
            </p>
            <p class="text-sm font-medium text-miby-dark-gray">
              [表示件数]<span class="ml-px mr-2 text-miby-black">{{ displayValue }}</span>
            </p>
          </div>
          <div class="flex flex-wrap justify-between items-center">
            <div class="flex flex-wrap gap-5 items-center">
              <div class="text-miby-black text-sm font-medium flex items-center">
                <span>表示件数：</span>
                <select
                  @change="emit('display-value', displayValue)"
                  v-model="displayValue"
                  class="cursor-pointer bg-white border border-gray-300 text-miby-black py-0 text-[10px] pr-1 rounded block"
                >
                  <option value="20" selected>20</option>
                  <option value="40">40</option>
                  <option value="60">60</option>
                  <option value="80">80</option>
                  <option value="100">100</option>
                  <option value="150">150</option>
                  <option value="200">200</option>
                </select>
                <span class="ml-1">/986</span>
              </div>
              <div class="text-miby-black text-sm font-medium">
                <span>表示形式：</span>
                <div class="inline-flex gap-x-0.5">
                  <a href="/search/summary"><button :class="{'active': page == 'summary'}" class="icons icon-display display1"></button></a>
                  <a href="/search/table"><button :class="{'active': page == 'table'}" class="icons icon-display display2"></button></a>
                  <a href="/search/block"><button :class="{'active': page == 'block'}" class="icons icon-display display3"></button></a>
                </div>
              </div>
              <div v-if="page != 'table'" class="text-miby-black text-sm font-medium mr-10">
                <span>並び順：</span>
                <!-- <label class="icons icon-order" for="sort-dropdown"></label> -->
                <select id="sort-dropdown" v-model="sort" @change="emit('sort', sort)">
                  <option selected value=""></option>
                  <option value="-createdate">最新順</option>
                  <option value="wtl">タイトル</option>
                </select>
              </div>
            </div>

            <div class="flex gap-2.5 py-5 md:py-0">
              <button @click="emit('open-filter')" class="btn-modal block cursor-pointer" data-target="Filter">
                <img :src="ButtonFilter" alt="フィルター" />
              </button>
              <button @click="emit('open-display')" v-if="page == 'table' || page == 'block'" class="btn-modal block cursor-pointer" data-target="DisplayItem">
                <img :src="ButtonDisplayItem" alt="項目表示" />
              </button>
            </div>
          </div>
        </div>
    </div>
</template>

<style scoped>
#sort-dropdown{
    appearance: none;
    background-image: url("../images/icon/icon_sort01.svg");
}
</style>