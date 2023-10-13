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
      <button id="page-top" class="block lg:hidden w-10 h-10 z-40 fixed right-5 bottom-2.5">
        <img src="/img/btn/btn-gototop_sp.svg" alt="Page Top" />
      </button>
    </main>
    <!-- 著者情報 -->
    <CreaterInfo ref="creater" />
    <!-- アラート -->
    <Alert v-if="visibleAlert" :type="alertType" :message="alertMessage" @click-close="visibleAlert = !visibleAlert" />
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

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * 作成者情報モーダル表示
 */
function openCreaterModal() {
  creater.value.openModal();
}

/* ///////////////////////////////////
// main
/////////////////////////////////// */

try {
  // 検索条件の初期化
  sessionStorage.removeItem('conditions');
  // 最新情報取得
  await $fetch(useAppConfig().wekoApi + '/records', {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'GET',
    headers: {
      'Accept-Language': localStorage.getItem('local') ?? 'ja',
      Authorization: localStorage.getItem('token:type') + ' ' + localStorage.getItem('token:access')
    },
    params: { size: '5', sort: '-createdate' },
    onResponse({ response }) {
      if (response.status === 200) {
        latestItem = response._data.search_results;
      }
    },
    onResponseError({ response }) {
      if (response.status === 401) {
        alertMessage.value = '(Status Code : ' + response.status + ')' + ' 認証エラーが発生しました。';
      } else if (Number(response.status) >= 500 && Number(response.status) < 600) {
        alertMessage.value =
          '(Status Code : ' + response.status + ')' + ' サーバエラーが発生しました。管理者に連絡してください。';
      } else {
        alertMessage.value = '(Status Code : ' + response.status + ')' + ' 最新情報の取得に失敗しました。';
      }
      alertType.value = 'error';
      visibleAlert.value = true;
    }
  });
} catch (error) {
  // console.log(error);
}

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

onBeforeMount(async () => {
  const query = useRoute().query;
  const state = String(query.state);

  // アクセストークン取得
  if (state) {
    if (sessionStorage.getItem('login:state') === state) {
      await useFetch('/api/token/create?code=' + String(query.code))
        .then((response) => {
          // @ts-ignore
          localStorage.setItem('token:type', response.data.value.tokenType);
          // @ts-ignore
          localStorage.setItem('token:access', response.data.value.accessToken);
          // @ts-ignore
          localStorage.setItem('token:refresh', response.data.value.refreshToken);
          // @ts-ignore
          localStorage.setItem('token:expires', response.data.value.expires);
          localStorage.setItem('token:issue', String(Date.now()));
        })
        .finally(() => {
          sessionStorage.removeItem('login:state');
          useRouter().replace({ query: {} });
        });
    }
  }
});

onMounted(() => {
  refreshToken();
});

onUpdated(() => {
  refreshToken();
});
</script>
