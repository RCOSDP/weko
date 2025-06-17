<template>
  <div v-if="isRender">
    <!-- 検索フォーム -->
    <SearchForm :displayFlag="true" />
    <main class="max-w-[1024px] mx-auto px-2.5">
      <div class="w-full">
        <!-- お知らせ -->
        <!-- <div class="mb-[10px]">
          <div class="bg-miby-light-blue w-full">
            <p class="text-white leading-[43px] pl-5 icons icon-news font-bold">
              {{ $t('indexLatestInfo') }}
            </p>
          </div>
          <News />
        </div> -->
        <!-- 最新情報 -->
        <div class="mb-[10px]">
          <div class="bg-miby-light-blue w-full">
            <p class="text-white leading-[43px] pl-5 icons icon-info font-bold">
              {{ $t('indexLatestItem') }}
            </p>
          </div>
          <div v-for="item in latestItem" :key="item">
            <LatestItem :item="item" />
          </div>
        </div>
        <!-- キーワードランキング -->
        <!-- <div class="mb-5">
          <div class="bg-miby-light-blue w-full">
            <p class="text-white leading-[43px] pl-5 icons icon-rank font-bold">{{ $t('indexRank') }}</p>
          </div>
          <KeywardRank />
        </div> -->
      </div>
      <!-- スクロールボタン -->
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
// import KeywardRank from '~/components/index/KeywardRank.vue';
import LatestItem from '~/components/index/LatestItem.vue';
// import News from '~/components/index/News.vue';

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

let latestItem = {};
const creater = ref();
const visibleAlert = ref(false);
const alertType = ref('info');
const alertMessage = ref('');
const alertCode = ref(0);
const isRender = ref(false);

/* ///////////////////////////////////
// function
/////////////////////////////////// */

// /**
//  * 作成者情報モーダル表示
//  */
// function openCreaterModal() {
//   creater.value.openModal();
// }

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
  const query = useRoute().query;
  const state = String(query.state);

  // Shibbolethログインの場合、TOP画面でOAuth認証を実行
  const next = query.next === 'ams' ? 'ams' : '';
  if (next == 'ams') {
    const url = new URL(useAppConfig().wekoOrigin + '/oauth/authorize');
    const random = Math.random().toString(36);
    url.searchParams.append('response_type', 'code');
    url.searchParams.append('client_id', useRuntimeConfig().public.clientId);
    url.searchParams.append('scope', 'item:read index:read ranking:read file:read user:email');
    url.searchParams.append('state', random);
    sessionStorage.setItem('login:state', random);
    window.open(url.href, '_self');
  }

  const baseURI = useRuntimeConfig().public.redirectURI;
  const itemURL = sessionStorage.getItem('item-url');
  const redirectURL = itemURL ? itemURL : baseURI;

  // アクセストークン取得
  if (state) {
    if (sessionStorage.getItem('login:state') === state) {
      await useFetch('/api/token/create', {
        method: 'GET',
        params: { code: String(query.code) }
      })
        .then((response) => {
          if (response.status.value === 'success') {
            const data: any = response.data.value;
            localStorage.setItem('token:type', data.tokenType);
            localStorage.setItem('token:access', data.accessToken);
            localStorage.setItem('token:refresh', data.refreshToken);
            localStorage.setItem('token:expires', data.expires);
            localStorage.setItem('token:issue', String(Date.now()));
          }
        })
        .finally(() => {
          const params = new URLSearchParams(redirectURL.replace(baseURI, ''));
          const number = params.get('number');
          if (!number) {
            useRouter().replace({ query: {} });
          } else {
            sessionStorage.removeItem('item-url');
            useRouter().replace({
              path: redirectURL,
              query: {
                sess: 'top',
                number: number,
              }
            });
          }
          setTimeout(() => {
            location.reload();
          }, 100);
        });
    }
  }
  isRender.value = true;

  // 検索条件の初期化
  sessionStorage.removeItem('conditions');
  // 最新情報取得
  let statusCode = 0;
  await $fetch(useAppConfig().wekoApi + '/records', {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'GET',
    headers: {
      'Cache-Control': 'no-store',
      Pragma: 'no-cache',
      'Accept-Language': localStorage.getItem('locale') ?? 'ja',
      Authorization: localStorage.getItem('token:type') + ' ' + localStorage.getItem('token:access')
    },
    params: { size: '5', sort: '-publish_date' },
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

onMounted(() => {
  refreshToken();
});

onUpdated(() => {
  refreshToken();
});
</script>
