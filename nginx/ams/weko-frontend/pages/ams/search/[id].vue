<template>
  <div>
    <!-- 検索フォーム -->
    <SearchForm :sessCondFlag="false" @click-search="reSearch" />
    <main class="max-w-[1024px] mx-auto px-2.5">
      <!-- インデックス階層 -->
      <div class="breadcrumb flex flex-wrap w-full">
        <div v-for="index in indexes" :key="index.id">
          <span v-if="index.id != route.params.id" class="font-medium cursor-pointer" @click="clickParent(index.id)">
            {{ index.name }}
          </span>
          <span v-else class="font-medium underline">
            {{ index.name }}
          </span>
          <a v-if="index.id != route.params.id" class="ml-1 mr-1">/</a>
        </div>
      </div>
      <!-- 検索結果 -->
      <div class="w-full">
        <div class="w-full">
          <div class="bg-miby-light-blue w-full flex">
            <p class="text-white leading-[43px] pl-5 icons icon-list font-bold">
              {{ $t('searchResult') }}
            </p>
            <p class="text-white leading-[43px] pr-5 ml-auto">
              {{
                (Number(total)
                  ? String((Number(conditions.currentPage) - 1) * Number(conditions.perPage) + 1)
                  : Number(total)) +
                ' - ' +
                String(
                  (Number(conditions.currentPage) - 1) * Number(conditions.perPage) + Number(conditions.perPage) >
                    Number(total)
                    ? Number(total)
                    : (Number(conditions.currentPage) - 1) * Number(conditions.perPage) + Number(conditions.perPage)
                ) +
                ' of ' +
                Number(total) +
                ' results.'
              }}
            </p>
          </div>
          <!-- 検索条件 -->
          <Conditions
            :displayType="displayType"
            :conditions="conditions"
            @click-per-page="setPerPage"
            @click-display-type="setDisplayType"
            @click-sort="setSort"
            @click-order="setOrder"
            @click-filter="openFilterModal" />
          <div class="p-5 bg-miby-bg-gray">
            <div class="flex justify-end">
              <!-- 全件マイリスト -->
              <!-- <a class="pl-1.5 md:pl-0">
                <span class="underline text-sm text-miby-link-blue pr-1 mr-3">
                  {{ $t('searchMylistAll') }}
                </span>
              </a> -->
              <!-- 全件ダウンロード -->
              <a
                v-if="total"
                class="pl-1.5 md:pl-0 icons icon-download after cursor-pointer"
                @click="downloadResultList">
                <span class="underline text-sm text-miby-link-blue pr-1">
                  {{ $t('searchDownloadAll') }}
                </span>
              </a>
            </div>
            <!-- 公開区分（凡例） -->
            <div class="flex whitespace-nowrap ml-auto mt-4 mb-8 text-center">
              <div class="w-full flex flex-wrap content-center gap-4 justify-start">
                <p class="icons-type icon-public">
                  <span>{{ $t('openPublic') }}</span>
                </p>
                <p class="icons-type icon-group">
                  <span>{{ $t('openGroup') }}</span>
                </p>
                <p class="icons-type icon-member">
                  <span>{{ $t('openPrivate') }}</span>
                </p>
                <p class="icons-type icon-private">
                  <span>{{ $t('openRestricted') }}</span>
                </p>
              </div>
            </div>
            <!-- スピナー -->
            <div v-if="!renderFlag" class="text-center">
              <span class="loading loading-bars loading-lg" />
            </div>
            <!-- 検索結果 -->
            <SearchResult v-if="renderFlag" :displayType="displayType" :searchResult="searchResult" />
            <!-- ページネーション -->
            <div class="max-w-[300px] mx-auto mt-3.5 mb-16">
              <Pagination
                v-if="total && renderFlag"
                :total="Number(total)"
                :currentPage="Number(conditions.currentPage)"
                :displayPerPage="Number(conditions.perPage)"
                @click-page="setPage" />
            </div>
          </div>
        </div>
      </div>
    </main>
    <!-- 著者情報 -->
    <CreaterInfo ref="creater" />
    <!-- アラート -->
    <Alert v-if="visibleAlert" :alert="alertData" @click-close="visibleAlert = !visibleAlert" />
  </div>
</template>

<script lang="ts" setup>
import { useRoute, useRouter } from 'vue-router';

import amsAlert from '~/assets/data/amsAlert.json';
import ResultJson from '~/assets/data/searchResult.json';
import Alert from '~/components/common/Alert.vue';
import Pagination from '~/components/common/Pagination.vue';
import SearchForm from '~/components/common/SearchForm.vue';
import CreaterInfo from '~/components/common/modal/CreaterInfo.vue';
import Conditions from '~/components/search/Conditions.vue';
import SearchResult from '~/components/search/SearchResult.vue';

const route = useRoute();

/* ///////////////////////////////////
// interface
/////////////////////////////////// */

interface indexInfo {
  id: string;
  name: string;
}

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const conditions = reactive({
  type: '0',
  keyword: '',
  currentPage: '1',
  perPage: '20',
  sort: 'wtl',
  order: 'asc',
  detail: {},
  detailData: {}
});
const displayType = ref('summary');
const total = ref('');
const searchResult = ref({});
const modalFilter = ref();
const renderFlag = ref(true);
const indexes = ref<indexInfo[]>([]);
const creater = ref();
const visibleAlert = ref(false);
const alertData = ref({
  msgid: '',
  msgstr: '',
  position: '',
  width: 'w-full',
  loglevel: 'info'
});
const appConf = useAppConfig();

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * アイテム検索
 */
async function search() {
  setConditions();
  let statusCode = 0;
  const isError = ref(false);
  const params = {
    q: conditions.keyword,
    search_type: conditions.type,
    page: conditions.currentPage,
    size: conditions.perPage,
    sort: conditions.order === 'asc' ? conditions.sort : '-' + conditions.sort
  };
  if (conditions.detail) {
    Object.assign(params, conditions.detail);
  }
  const urlSearchParam = new URLSearchParams(params);

  await $fetch(useAppConfig().wekoApi + '/records?' + urlSearchParam, {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'GET',
    credentials: 'omit',
    headers: {
      'Cache-Control': 'no-store',
      Pragma: 'no-cache',
      'Accept-Language': localStorage.getItem('locale') ?? 'ja',
      Authorization: localStorage.getItem('token:type') + ' ' + localStorage.getItem('token:access')
    },
    onResponse({ response }) {
      if (response.status === 200) {
        searchResult.value = response._data.search_results;
        total.value = response._data.total_results;
      }
    },
    onResponseError({ response }) {
      statusCode = response.status;
      if (!isError.value) {
        if (statusCode === 401) {
          // 認証エラー
          alertData.value = amsAlert.ID_SEARCH_MESSAGE_ERROR_AUTH;
        } else if (statusCode >= 500 && statusCode < 600) {
          // サーバーエラー
          alertData.value = amsAlert.ID_SEARCH_MESSAGE_ERROR_SERVER;
        } else {
          // リクエストエラー
          alertData.value = amsAlert.ID_SEARCH_MESSAGE_ERROR_REQUEST;
        }
        visibleAlert.value = true;
        isError.value = true;
      }
    }
  }).catch(() => {
    if (statusCode === 0 && !isError.value) {
      // fetchエラー
      alertData.value = amsAlert.ID_SEARCH_MESSAGE_ERROR_FETCH;
      visibleAlert.value = true;
      isError.value = true;
    }
  });
  return !isError.value;
}

/**
  await $fetch(useAppConfig().wekoApi + '/tree/index/' + route.params.id + '/parent', {
 */
async function getParentIndex() {
  let statusCode = 0;
  const isError = ref(false);
  await $fetch(useAppConfig().wekoApi + '/tree/index/' + route.params.id + '/parent', {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'GET',
    credentials: 'omit',
    headers: {
      'Cache-Control': 'no-store',
      Pragma: 'no-cache',
      'Accept-Language': localStorage.getItem('locale') ?? 'ja',
      Authorization: localStorage.getItem('token:type') + ' ' + localStorage.getItem('token:access')
    },
    onResponse({ response }) {
      if (response.status === 200) {
        indexes.value = [];
        let obj = response._data.index;
        while (obj) {
          const index: indexInfo = { id: obj.cid, name: obj.name };
          indexes.value.unshift(index);
          obj = obj.parent ?? false;
        }
      }
    },
    onResponseError({ response }) {
      statusCode = response.status;
      if (!isError.value) {
        if (statusCode === 401) {
          // 認証エラー
          alertData.value = amsAlert.ID_INDEX_MESSAGE_ERROR_AUTH;
        } else if (statusCode >= 500 && statusCode < 600) {
          // サーバーエラー
          alertData.value = amsAlert.ID_INDEX_MESSAGE_ERROR_SERVER;
        } else {
          // リクエストエラー
          alertData.value = amsAlert.ID_INDEX_MESSAGE_ERROR_GET_INDEX;
        }
        visibleAlert.value = true;
        isError.value = true;
      }
    }
  }).catch(() => {
    if (statusCode === 0 && !isError.value) {
      // fetchエラー
      alertData.value = amsAlert.ID_INDEX_MESSAGE_ERROR_FETCH;
      visibleAlert.value = true;
      isError.value = true;
    }
  });
  return !isError.value;
}

/**
 * 検索結果一覧ダウンロード
 */
async function downloadResultList() {
  let statusCode = 0;

  const params = {
    q: conditions.keyword,
    search_type: conditions.type,
    sort: conditions.order === 'asc' ? conditions.sort : '-' + conditions.sort
  };
  if (conditions.detail) {
    Object.assign(params, conditions.detail);
  }
  const urlSearchParam = new URLSearchParams(params);

  await $fetch(useAppConfig().wekoApi + '/records/list?' + urlSearchParam, {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'POST',
    credentials: 'omit',
    headers: {
      'Cache-Control': 'no-store',
      Pragma: 'no-cache',
      'Accept-Language': localStorage.getItem('locale') ?? 'ja',
      Authorization: localStorage.getItem('token:type') + ' ' + localStorage.getItem('token:access')
    },
    body: ResultJson,
    onResponse({ response }) {
      if (response.status === 200) {
        const a = document.createElement('a');
        a.href = window.URL.createObjectURL(new Blob([response._data]));
        a.setAttribute('download', 'result_list.tsv');
        a.click();
        a.remove();
      }
    },
    onResponseError({ response }) {
      statusCode = response.status;
      if (statusCode === 401) {
        // 認証エラー
        alertData.value = amsAlert.ID_DOWNLOAD_MESSAGE_ERROR_AUTH;
      } else if (statusCode >= 500 && statusCode < 600) {
        // サーバーエラー
        alertData.value = amsAlert.ID_DOWNLOAD_MESSAGE_ERROR_SERVER;
      } else {
        // リクエストエラー
        alertData.value = amsAlert.ID_DOWNLOAD_MESSAGE_ERROR_DOWNLOAD_RESULT;
      }
      visibleAlert.value = true;
    }
  }).catch(() => {
    if (statusCode === 0) {
      // fetchエラー
      alertData.value = amsAlert.ID_DOWNLOAD_MESSAGE_ERROR_FETCH;
      visibleAlert.value = true;
    }
  });
}

/**
 * 再レンダリング
 */
async function renderResult() {
  try {
    renderFlag.value = false;
    await search();
  } finally {
    nextTick(() => {
      renderFlag.value = true;
    });
  }
}

/**
 * 検索ページ上での検索時イベント
 */
function reSearch() {
  conditions.currentPage = '1';
  navigateTo(`${appConf.amsPath ?? ''}/search`);
}

/**
 * 表示件数選択時イベント
 * @param value 表示件数
 */
function setPerPage(value: string) {
  conditions.perPage = value;
  conditions.currentPage = '1';
  sessionStorage.setItem('conditions', JSON.stringify(conditions));
  renderResult();
}

/**
 * 並び順選択時イベント
 * @param value 並び順
 */
function setSort(value: string) {
  conditions.sort = value;
  conditions.currentPage = '1';
  sessionStorage.setItem('conditions', JSON.stringify(conditions));
  renderResult();
}

/**
 * 昇順/降順選択時イベント
 * @param value 昇順/降順
 */
function setOrder(value: string) {
  conditions.order = value;
  conditions.currentPage = '1';
  sessionStorage.setItem('conditions', JSON.stringify(conditions));
  renderResult();
}

/**
 * ページネーション選択時イベント
 * @param value ページ
 */
function setPage(value: string) {
  conditions.currentPage = value;
  sessionStorage.setItem('conditions', JSON.stringify(conditions));
  renderResult();
}

/**
 * 表示形式選択時イベント
 * @param value 表示形式
 */
function setDisplayType(value: string) {
  displayType.value = value;
}

/**
 * 検索条件をセッションから復元
 */
function setConditions() {
  conditions.keyword = String(route.params.id) ?? '';
  // @ts-ignore
  const json = JSON.parse(sessionStorage.getItem('conditions'));
  conditions.type = json.type ?? '0';
  conditions.keyword = String(useRoute().params.id) ?? '';
  conditions.currentPage = json.currentPage ?? '1';
  conditions.perPage = json.perPage ?? '20';
  conditions.sort = json.sort ?? 'wtl';
  conditions.order = json.order ?? 'asc';
  conditions.detail = json.detail ?? {};
  conditions.detailData = json.detailData ?? {};
}

/**
 * インデックス名押下時イベント
 * @param indexId インデクスID
 */
function clickParent(indexId: string) {
  // @ts-ignore
  const sessConditions = JSON.parse(sessionStorage.getItem('conditions'));
  Object.assign(sessConditions, { keyword: indexId });
  sessionStorage.setItem('conditions', JSON.stringify(sessConditions));
  useRouter().replace({ params: { id: indexId } });
}

/**
 * フィルターボタン押下時イベント
 */
function openFilterModal() {
  (document.getElementById('modalFilter') as HTMLDialogElement).showModal();
  document.body.classList.add('overflow-hidden');
  modalFilter.value.showCheckBoxesWhenOpen();
}

// /**
//  * 作成者情報モーダル表示
//  */
// function openCreaterModal() {
//   creater.value.openModal();
// }

/** ファイル一覧画面からアイテム詳細画面へ戻るためのURL取得準備 */
function setURL() {
  sessionStorage.removeItem('url');
  sessionStorage.setItem('url', window.location.href);
}

/* ///////////////////////////////////
// main
/////////////////////////////////// */

async function init() {
  try {
    const successSearch = await search();
    if (!successSearch) {
      return;
    }
    await getParentIndex();
  } catch (error) {
    alertData.value = amsAlert.ID_MESSAGE_ERROR;
    visibleAlert.value = true;
  }
}
await init();

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

onMounted(() => {
  setURL();
  refreshToken();
});

onUpdated(() => {
  refreshToken();
});
</script>
