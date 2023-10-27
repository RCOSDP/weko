<template>
  <div>
    <!-- 検索フォーム -->
    <SearchForm :displayFlag="true" />
    <main class="max-w-[1024px] mx-auto px-2.5">
      <div class="w-full">
        <!-- お知らせ -->
        <div class="mb-[10px]">
          <News />
        </div>
        <!-- 最新情報 -->
        <div class="mb-[10px]">
          <div class="bg-miby-light-blue w-full">
            <p class="text-white leading-[43px] pl-5 icons icon-info font-bold">
              {{ $t('indexLatestItem') }}
            </p>
          </div>
          <div v-for="item in latestItem" :key="item">
            <LatestItem :item="item" @click-creater="openCreaterModal" />
          </div>
        </div>
        <!-- キーワードランキング -->
        <div class="mb-5">
          <KeywardRank />
        </div>
      </div>
      <button id="page-top" class="block lg:hidden w-10 h-10 z-40 fixed right-5 bottom-2.5" @click="scrollToTop">
        <img src="/img/btn/btn-gototop_sp.svg" alt="Page Top" />
      </button>
    </main>
    <!-- 著者情報 -->
    <CreaterInfo ref="creater" />
    <!-- アラート -->
    <Alert
      v-if="visibleAlert"
      :type="alertType"
      :message="alertMessage"
      :code="alertCode"
      @click-close="visibleAlert = !visibleAlert" />
  </div>
</template>

<script lang="ts" setup>
import Alert from '~/components/common/Alert.vue';
import SearchForm from '~/components/common/SearchForm.vue';
import CreaterInfo from '~/components/common/modal/CreaterInfo.vue';
import KeywardRank from '~/components/index/KeywardRank.vue';
import LatestItem from '~/components/index/LatestItem.vue';
import News from '~/components/index/News.vue';

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

let latestItem = {};
const creater = ref();
const visibleAlert = ref(false);
const alertType = ref('info');
const alertMessage = ref('');
const alertCode = ref(0);

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * 作成者情報モーダル表示
 */
function openCreaterModal() {
  creater.value.openModal();
}

/**
 * ページ最上部にスクロール
 */
function scrollToTop() {
  scrollTo({ top: 0, behavior: 'smooth' });
}

/* ///////////////////////////////////
// main
/////////////////////////////////// */

try {
  // 検索条件の初期化
  sessionStorage.removeItem('conditions');
  // 最新情報取得
  let statusCode = 0;
  await $fetch(useAppConfig().wekoApi + '/records', {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'GET',
    headers: {
      'Accept-Language': localStorage.getItem('locale') ?? 'ja',
      Authorization: localStorage.getItem('token:type') + ' ' + localStorage.getItem('token:access')
    },
    params: { size: '5', sort: '-createdate' },
    onResponse({ response }) {
      if (response.status === 200) {
        latestItem = response._data.search_results;
      }
    },
    onResponseError({ response }) {
      alertCode.value = 0;
      statusCode = response.status;
      if (statusCode === 401) {
        // 認証エラー
        alertMessage.value = 'message.error.auth';
      } else if (statusCode >= 500 && statusCode < 600) {
        // サーバーエラー
        alertMessage.value = 'message.error.server';
        alertCode.value = statusCode;
      } else {
        // リクエストエラー
        alertMessage.value = 'message.error.getLatestItem';
        alertCode.value = statusCode;
      }
      alertType.value = 'error';
      visibleAlert.value = true;
    }
  }).catch(() => {
    if (statusCode === 0) {
      // fetchエラー
      alertMessage.value = 'message.error.fetch';
      alertType.value = 'error';
      visibleAlert.value = true;
    }
  });
} catch (error) {
  alertCode.value = 0;
  alertMessage.value = 'message.error.error';
  alertType.value = 'error';
  visibleAlert.value = true;
}

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

onBeforeMount(() => {
  if (String(useRoute().query.state)) {
    useRouter().replace({ query: {} });
  }
});

onMounted(() => {
  refreshToken();
});

onUpdated(() => {
  refreshToken();
});
</script>
