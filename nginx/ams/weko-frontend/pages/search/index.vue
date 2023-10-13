<template>
  <div>
    <!-- 検索フォーム -->
    <SearchForm :sessCondFlag="true" @click-search="reSearch" />
    <main class="max-w-[1024px] mx-auto px-2.5">
      <!-- 検索結果 -->
      <div class="w-full">
        <div class="w-full">
          <div class="bg-miby-light-blue w-full">
            <p class="text-white leading-[43px] pl-5 icons icon-list font-bold">
              {{ $t('searchResult') }}
            </p>
          </div>
          <!-- 検索条件 -->
          <Conditions
            :displayType="displayType"
            :conditions="conditions"
            :detailConditions="detailConditions"
            :total="Number(total)"
            @click-per-page="setPerPage"
            @click-display-type="setDisplayType"
            @click-sort="setSort"
            @click-order="setOrder"
            @click-filter="openFilterModal" />
          <div class="p-5 bg-miby-bg-gray">
            <div class="flex justify-end">
              <!-- 全件マイリスト -->
              <a class="pl-1.5 md:pl-0" href="#">
                <span class="underline text-sm text-miby-link-blue pr-1 mr-3">
                  {{ $t('searchMylistAll') }}
                </span>
              </a>
              <!-- 全件ダウンロード -->
              <a class="pl-1.5 md:pl-0 icons icon-download after" href="#">
                <span class="underline text-sm text-miby-link-blue pr-1">
                  {{ $t('searchDownloadAll') }}
                </span>
              </a>
            </div>
            <!-- 公開区分（凡例） -->
            <div class="flex whitespace-nowrap ml-auto mt-4 mb-8 text-center">
              <div class="w-full flex flex-wrap content-center gap-4 justify-start">
                <p class="icons-type icon-published">
                  <span>{{ $t('openPublic') }}</span>
                </p>
                <p class="icons-type icon-group">
                  <span>{{ $t('openGroup') }}</span>
                </p>
                <p class="icons-type icon-private">
                  <span>{{ $t('openPrivate') }}</span>
                </p>
                <p class="icons-type icon-limited">
                  <span>{{ $t('openRestricted') }}</span>
                </p>
              </div>
            </div>
            <!-- スピナー -->
            <div v-if="!renderFlag" class="text-center">
              <span class="loading loading-bars loading-lg" />
            </div>
            <!-- 検索結果 -->
            <SearchResult
              v-if="renderFlag"
              :displayType="displayType"
              :searchResult="searchResult"
              @click-creater="openCreaterModal" />
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
    <Alert v-if="visibleAlert" :type="alertType" :message="alertMessage" @click-close="visibleAlert = !visibleAlert" />
  </div>
</template>

<script lang="ts" setup>
import Alert from '~/components/common/Alert.vue';
import Pagination from '~/components/common/Pagination.vue';
import SearchForm from '~/components/common/SearchForm.vue';
import CreaterInfo from '~/components/common/modal/CreaterInfo.vue';
import Conditions from '~/components/search/Conditions.vue';
import SearchResult from '~/components/search/SearchResult.vue';

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const conditions = reactive({
  type: '0',
  keyword: '',
  currentPage: '1',
  perPage: '20',
  sort: 'wtl',
  order: 'asc'
});
const detailConditions = reactive({
  typePublic: [],
  typeDownload: [],
  field: []
});
const displayType = ref('summary');
const total = ref('');
const searchResult = ref({});
const modalFilter = ref();
const renderFlag = ref(true);
const creater = ref();
const visibleAlert = ref(false);
const alertType = ref('info');
const alertMessage = ref('');

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * アイテム検索
 */
async function search() {
  setConditions();
  await $fetch(useAppConfig().wekoApi + '/records', {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'GET',
    headers: {
      'Accept-Language': localStorage.getItem('local') ?? 'ja',
      Authorization: localStorage.getItem('token:type') + ' ' + localStorage.getItem('token:access')
    },
    params: {
      q: conditions.keyword,
      search_type: conditions.type,
      page: conditions.currentPage,
      size: conditions.perPage,
      sort: conditions.order === 'asc' ? conditions.sort : '-' + conditions.sort
    },
    onResponse({ response }) {
      if (response.status === 200) {
        searchResult.value = response._data.search_results;
        total.value = response._data.total_results;
      }
    },
    onResponseError({ response }) {
      if (response.status === 401) {
        alertMessage.value = '(Status Code : ' + response.status + ')' + ' 認証エラーが発生しました。';
      } else if (Number(response.status) >= 500 && Number(response.status) < 600) {
        alertMessage.value =
          '(Status Code : ' + response.status + ')' + ' サーバエラーが発生しました。管理者に連絡してください。';
      } else {
        alertMessage.value = '(Status Code : ' + response.status + ')' + ' アイテムの検索に失敗しました。';
      }
      alertType.value = 'error';
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
  setConditions();
  conditions.currentPage = '1';
  sessionStorage.setItem('conditions', JSON.stringify(conditions));
  renderResult();
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
  if (sessionStorage.getItem('conditions')) {
    // @ts-ignore
    const json = JSON.parse(sessionStorage.getItem('conditions'));
    conditions.type = json.type ?? '0';
    conditions.keyword = json.keyword ?? '';
    conditions.currentPage = json.currentPage ?? '1';
    conditions.perPage = json.perPage ?? '20';
    conditions.sort = json.sort ?? 'wtl';
    conditions.order = json.order ?? 'asc';
  }
}

/**
 * フィルターボタン押下時イベント
 */
function openFilterModal() {
  (document.getElementById('modalFilter') as HTMLDialogElement).showModal();
  document.body.classList.add('overflow-hidden');
  modalFilter.value.showCheckBoxesWhenOpen();
}

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
  await search();
} catch (error) {
  // console.log(error);
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
