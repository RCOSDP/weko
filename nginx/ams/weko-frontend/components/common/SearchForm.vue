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
            {{ $t('search') }}
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
      <!-- <a class="block cursor-pointer border py-1 text-center rounded-md text-sm w-[130px]">
        <img src="/img/btn/btn-mylist.svg" class="w-[94px] mx-auto" alt="My List" />
      </a> -->
    </div>
    <!-- データ総数 -->
    <div
      v-if="displayFlag"
      class="data-statistics p-5 sm:p-0 flex flex-wrap justify-between sm:justify-center gap-x-1 gap-y-4 sm:gap-7 w-3/4 sm:w-full mx-auto">
      <div class="sm:w-fit thesis">
        <p class="icons icon-thesis text-xs text-white md:text-center">{{ $t('totalDataset') }}</p>
        <p class="number text-white text-xs md:text-center font-bold">{{ dataset.toLocaleString() }}</p>
      </div>
      <div class="sm:w-fit thesis">
        <p class="icons icon-thesis text-xs text-white md:text-center">{{ $t('totalJournalArticle') }}</p>
        <p class="number text-white text-xs md:text-center font-bold">{{ journal.toLocaleString() }}</p>
      </div>
      <div class="sm:w-fit noro">
        <p class="icons icon-noro text-xs text-white md:text-center">{{ $t('totalAuthor') }}</p>
        <p class="number text-white text-xs md:text-center font-bold">{{ author.toLocaleString() }}</p>
      </div>
    </div>
  </div>
  <!-- 詳細検索 -->
  <DetailSearch ref="detailSearch" :sessCondFlag="isRestore" class="z-50" @detail-search="clickDetailSearch" />
</template>

<script lang="ts" setup>
import DetailSearch from '~/components/common/modal/DetailSearch.vue';

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
const detailSearch = ref();
const isRestore = ref(props.sessCondFlag);
const dataset = ref(0);
const journal = ref(0);
const author = ref(0);

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
      // 詳細検索条件が設定されている場合は削除
      if (Object.prototype.hasOwnProperty.call(sessConditions, 'detail')) {
        delete sessConditions.detail;
        delete sessConditions.detailData;
        isRestore.value = false;
      }
      // 検索条件設定
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
 * 詳細検索実行時イベント
 */
function clickDetailSearch() {
  // 通常検索フォームの値を初期化する
  conditions.type = '0';
  conditions.keyword = '';
  isRestore.value = true;
  emits('clickSearch');
}

/**
 * 詳細ボタン押下時イベント
 */
function openDetailModal() {
  detailSearch.value.openModal();
}

/* ///////////////////////////////////
// main
/////////////////////////////////// */

try {
  if (props.displayFlag) {
    // Dataset数の取得
    $fetch(useAppConfig().wekoApi + '/records', {
      timeout: useRuntimeConfig().public.apiTimeout,
      method: 'GET',
      headers: {
        'Cache-Control': 'no-store',
        Pragma: 'no-cache',
        'Accept-Language': localStorage.getItem('locale') ?? 'ja',
        Authorization: localStorage.getItem('token:type') + ' ' + localStorage.getItem('token:access')
      },
      params: { size: '0', type: '17' },
      onResponse({ response }) {
        if (response.status === 200) {
          dataset.value = response._data.total_results;
        }
      }
    });

    // JournalArticle数の取得
    $fetch(useAppConfig().wekoApi + '/records', {
      timeout: useRuntimeConfig().public.apiTimeout,
      method: 'GET',
      headers: {
        'Cache-Control': 'no-store',
        Pragma: 'no-cache',
        'Accept-Language': localStorage.getItem('locale') ?? 'ja',
        Authorization: localStorage.getItem('token:type') + ' ' + localStorage.getItem('token:access')
      },
      params: { size: '0', type: '4' },
      onResponse({ response }) {
        if (response.status === 200) {
          journal.value = response._data.total_results;
        }
      }
    });

    // 著者数の取得
    $fetch(useAppConfig().wekoApi + '/authors/count', {
      timeout: useRuntimeConfig().public.apiTimeout,
      method: 'GET',
      headers: {
        'Cache-Control': 'no-store',
        Pragma: 'no-cache'
      },
      onResponse({ response }) {
        if (response.status === 200) {
          author.value = response._data.count;
        }
      }
    });
  }
} catch (error) {
  // console.log(error;)
}

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

onMounted(() => {
  const con = sessionStorage.getItem('conditions');

  if (con && props.sessCondFlag) {
    if (
      !Object.prototype.hasOwnProperty.call(JSON.parse(con), 'detail') ||
      Object.keys(JSON.parse(con).detail).length === 0
    ) {
      conditions.type = JSON.parse(con).type ?? '0';
      conditions.keyword = JSON.parse(con).keyword ?? '';
    }
  }
});
</script>
