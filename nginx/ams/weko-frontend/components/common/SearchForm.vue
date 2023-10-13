<template>
  <div class="bg-MainBg bg-no-repeat bg-top bg-cover pt-[130px] pb-6 mt-[-180px] mb-[15px]">
    <form class="max-w-screen-md mx-auto pt-16 px-5" @submit.prevent="search">
      <!-- 検索条件 -->
      <div class="text-white mb-2.5 flex justify-center items-center">
        <div>
          <!-- 検索条件（全文） -->
          <label class="radio cursor-pointer">
            <input id="all" v-model="conditions.type" value="0" type="radio" name="form-type" />
            <span class="text-sm radio-label" for="type1">
              {{ $t('searchRadioAll') }}
            </span>
          </label>
          <!-- 検索条件（キーワード） -->
          <label class="radio cursor-pointer">
            <input id="keyword" v-model="conditions.type" value="1" type="radio" name="form-type" />
            <span class="text-sm radio-label" for="type2">
              {{ $t('searchRadioKeyword') }}
            </span>
          </label>
        </div>
      </div>
      <!-- 検索フォーム -->
      <div class="flex w-full mb-5 h-10">
        <input
          v-model="conditions.keyword"
          type="text"
          class="py-2.5 px-5 rounded-l-[30px] w-full placeholder:text-white md:placeholder:text-miby-thin-gray h-10 border border-miby-thin-gray focus:ring focus:ring-miby-orange"
          :placeholder="$t('searchFromText')" />
        <button
          type="submit"
          class="ml-[-1px] h-10 text-white border border-miby-thin-gray w-[97px] bg-miby-orange rounded-r-[30px]">
          <span class="icons icon-search">
            {{ $t('searchBtn') }}
          </span>
        </button>
      </div>
    </form>
    <!-- 詳細検索/マイリスト -->
    <div class="text-white mb-[15px] flex gap-5 items-center justify-center">
      <a
        id="search_form"
        class="block cursor-pointer border py-1 text-center rounded-md text-sm w-[130px]"
        @click="openDetailModal">
        <img src="/img/btn/btn-detail-search.svg" class="w-[81px] mx-auto" alt="Detail Search" />
      </a>
      <a class="block cursor-pointer border py-1 text-center rounded-md text-sm w-[130px]">
        <img src="/img/btn/btn-mylist.svg" class="w-[94px] mx-auto" alt="My List" />
      </a>
    </div>
    <!-- データ総数 -->
    <div
      v-if="displayFlag"
      class="data-statistics p-5 sm:p-0 flex flex-wrap justify-between sm:justify-center gap-x-1 gap-y-4 sm:gap-7 w-3/4 sm:w-full mx-auto">
      <div class="sm:w-fit nord">
        <p class="icons icon-nord text-xs text-white md:text-center">{{ $t('totalData') }}</p>
        <p class="number text-white text-xs md:text-center font-bold">9,999,999,999</p>
      </div>
      <div class="sm:w-fit norf">
        <p class="icons icon-norf text-xs text-white md:text-center">{{ $t('totalFile') }}</p>
        <p class="number text-white text-xs md:text-center font-bold">9,999,999</p>
      </div>
      <div class="sm:w-fit thesis">
        <p class="icons icon-thesis text-xs text-white md:text-center">{{ $t('totalPaper') }}</p>
        <p class="number text-white text-xs md:text-center font-bold">9,999</p>
      </div>
      <div class="sm:w-fit noro">
        <p class="icons icon-noro text-xs text-white md:text-center">{{ $t('totalGroup') }}</p>
        <p class="number text-white text-xs md:text-center font-bold">999</p>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
/* ///////////////////////////////////
// props
/////////////////////////////////// */

const props = defineProps({
  // 検索条件の復元可否
  sessCondFlag: {
    type: Boolean,
    default: false
  },
  // データ総数表示可否
  displayFlag: {
    type: Boolean,
    default: false
  }
});

/* ///////////////////////////////////
// emits
/////////////////////////////////// */

const emits = defineEmits(['clickSearch']);

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const conditions = reactive({ type: '0', keyword: '' });
const modalForm = ref();
const isFormModalShow = ref(false);

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * 検索ボタン押下時イベント
 */
function search() {
  if (useRoute().path.includes('/search')) {
    if (sessionStorage.getItem('conditions')) {
      // @ts-ignore
      const sessConditions = JSON.parse(sessionStorage.getItem('conditions'));
      Object.assign(sessConditions, conditions);
      sessionStorage.setItem('conditions', JSON.stringify(sessConditions));
    } else {
      sessionStorage.setItem('conditions', JSON.stringify(conditions));
    }
    emits('clickSearch');
  } else {
    sessionStorage.setItem('conditions', JSON.stringify(conditions));
    navigateTo('/search');
  }
}

/**
 * 詳細ボタン押下時イベント
 */
function openDetailModal() {
  modalForm.value.showCheckBoxesWhenOpen();
  isFormModalShow.value = true;
  document.body.classList.add('overflow-hidden');
}

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

onBeforeMount(() => {
  if (sessionStorage.getItem('conditions') && props.sessCondFlag) {
    // @ts-ignore
    conditions.type = JSON.parse(sessionStorage.getItem('conditions')).type ?? '0';
    // @ts-ignore
    conditions.keyword = JSON.parse(sessionStorage.getItem('conditions')).keyword ?? '';
  }
});
</script>
