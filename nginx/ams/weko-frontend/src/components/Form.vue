<script setup>
import ModalForm from "./Modal/ModalForm.vue";
import { ref, reactive } from "vue";
import BtnDetailSearch from "/images/btn/btn-detail-search.svg";
import BtnMyList from "/images/btn/btn-mylist.svg";

const props = defineProps({
  isIndex: {
    type: Boolean,
    default: false
  }
})

const isFormModalShow = ref(false); 

const onOpenFormModal = () => {
  isFormModalShow.value = true;
  document.body.classList.add("overflow-hidden");
};
const closeFormModal = () => {
  isFormModalShow.value = false
  document.body.classList.remove("overflow-hidden");
}
const searchStorage = JSON.parse(sessionStorage.getItem('search-conditions'))

const searchConditions = reactive({
  searchType:'',
  keyWord: searchStorage?.keyWord ?? '',
})
const submit = () => {
  sessionStorage.setItem('search-conditions', JSON.stringify(searchConditions))
}

</script>
<template>
  <div class="bg-MainBg bg-no-repeat bg-top bg-cover pt-[130px] pb-6 mt-[-180px] mb-[15px]">
    <form @submit="submit" class="max-w-screen-md mx-auto pt-16 px-5" action="/search/summary">
      <!-- <div class="text-white mb-2.5 flex justify-between items-center"> -->
      <div class="text-white mb-2.5 flex justify-center items-center">
        <!-- <div class="w-2/6"> -->
        <div class="">
          <div class="radio">
            <input v-model="searchConditions.searchType" value="type-full-text" class="absolute" type="radio" name="form-type" id="type1" checked />
            <label class="text-sm radio-label" for="type1">全文</label>
          </div>
          <div class="radio">
            <input v-model="searchConditions.searchType" value="type-key-word" type="radio" name="form-type" id="type2" />
            <label class="text-sm radio-label" for="type2">キーワード </label>
          </div>
        </div>
        <!-- 検索上部に設置時用に一時コメントアウト -->
        <!-- <div class="text-white">
          <button class="border py-1 pl-6 pr-6 rounded-md mr-5 icons icon-listsearch">
            詳細検索
          </button>
          <button class="border py-1 pl-6 pr-6 rounded-md icons icon-mylist">マイリスト</button>
        </div> -->
        <!-- 検索上部に設置時用に一時コメントアウト ここまで -->
      </div>
      <div class="flex w-full mb-5 h-10">
        <input
          v-model="searchConditions.keyWord"
          type="text"
          class="py-2.5 px-5 rounded-l-[30px] w-full placeholder:text-white md:placeholder:text-miby-thin-gray h-10 border border-miby-thin-gray focus:ring focus:ring-miby-orange"
          placeholder="入力後、ENTERを押して検索してください"
        />
        <button
          type="submit"
          class="ml-[-1px] h-10 text-white border border-miby-thin-gray w-[97px] bg-miby-orange rounded-r-[30px]"
        >
          <span class="icons icon-search">検索</span>
        </button>
      </div>
    </form>
    <div class="text-white mb-[15px] flex gap-5 items-center justify-center">
      <a
        id="btnSearchForm"
        class="block cursor-pointer border py-1 text-center rounded-md text-sm w-[130px]"
        @click="onOpenFormModal"
      >
        <img :src=BtnDetailSearch class="w-[81px] mx-auto" alt="詳細検索" />
      </a>
      <a
        class="block cursor-pointer border py-1 text-center rounded-md text-sm w-[130px]"
        >
        <img :src=BtnMyList class="w-[94px] mx-auto" alt="マイリスト" /></a
      >
    </div>
    <div v-if="isIndex"
      class="data-statistics p-5 sm:p-0 flex flex-wrap justify-between sm:justify-center gap-x-1 gap-y-4 sm:gap-7 w-3/4 sm:w-full mx-auto"
    >
      <div class="sm:w-fit nord">
        <p class="icons icon-nord text-xs text-white md:text-center">登録研究データ数</p>
        <p class="number text-white text-xs md:text-center font-bold">9,999,999,999</p>
      </div>
      <div class="sm:w-fit norf">
        <p class="icons icon-norf text-xs text-white md:text-center">登録ファイル数</p>
        <p class="number text-white text-xs md:text-center font-bold">9,999,999</p>
      </div>
      <div class="sm:w-fit thesis">
        <p class="icons icon-thesis text-xs text-white md:text-center">論文</p>
        <p class="number text-white text-xs md:text-center font-bold">9,999</p>
      </div>
      <div class="sm:w-fit noro">
        <p class="icons icon-noro text-xs text-white md:text-center">参加研究団体数</p>
        <p class="number text-white text-xs md:text-center font-bold">999</p>
      </div>
    </div>
  </div>
  <ModalForm client:only="vue" v-model:isFormModalShow="isFormModalShow" @close-modal="closeFormModal"/>
</template>
