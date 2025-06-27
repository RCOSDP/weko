<template>
  <div>
    <!-- 検索フォーム -->
    <SearchForm :sessCondFlag="true" :isOpen="isOpen" :columnNameDict="columnNameDict" @click-search="reSearch" />
    <main class="mx-auto max-w-[97vw]">
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
            @click-order="setOrder" />
          <div class="flex flex-wrap">
            <!-- フィルター -->
            <div class="bg-miby-searchtags-blue filter-area">
              <div class="bg-miby-light-blue w-full flex text-white text-center py-0.5 px-8 font-medium">
                {{ $t('filter') }}
              </div>
              <ul v-for="searchType in filterList" :key="searchType.id" class="pt-0.5 pl-2 text-sm font-medium">
                <li>
                  {{ $t(searchType.i18n) }}
                </li>
                <!-- チェックボックス -->
                <ul v-if="searchType.type == 'checkbox'" class="pl-4 text-14px font-medium pb-2">
                  <li v-for="(item, index) in searchType.data" :key="item.id">
                    <div
                      v-if="index <= searchType.displayNumber - 1"
                      class="filterSearchCheck w-full"
                      @click="checkTooltip($t(item.comment))">
                      <label class="flex" :class="{ 'tooltip-label': checkTooltip($t(item.comment)) }">
                        <span v-if="checkTooltip($t(item.comment))" class="tooltiptext">
                          {{ $t(item.comment) }}
                        </span>
                        <input
                          v-model="item.value"
                          type="checkbox"
                          class="link-color"
                          :checked="item.value"
                          :value="true"
                          @change="filterSearch" />
                        <span ref="target" class="ml-1 text-clamp w-4/5">
                          {{ $t(item.comment) }}
                        </span>
                        <span class="float-right mr-4">({{ $t(item.length) }})</span>
                      </label>
                    </div>
                    <div
                      v-else
                      class="w-full"
                      :class="{
                        'last-item': index === item.length - 1,
                        filterSearchCheck: showFlagDict[searchType.i18n]
                      }">
                      <div v-if="index == searchType.displayNumber" :class="{ hidden: showFlagDict[searchType.i18n] }">
                        <label
                          class="icons icon-arrow link-color cursor-pointer"
                          @click="showFlagDict[searchType.i18n] = !showFlagDict[searchType.i18n]">
                          {{ $t('showAll') }}
                        </label>
                      </div>
                      <div class="w-full" :class="{ filterSearchCheck: showFlagDict[searchType.i18n] }">
                        <label
                          class="flex"
                          :class="{
                            hidden: !showFlagDict[searchType.i18n],
                            'tooltip-label': checkTooltip($t(item.comment))
                          }">
                          <span v-if="checkTooltip($t(item.comment))" class="tooltiptext">
                            {{ $t(item.comment) }}
                          </span>
                          <input
                            v-model="item.value"
                            type="checkbox"
                            class="link-color"
                            :checked="item.value"
                            :value="true"
                            @change="filterSearch" />
                          <span class="ml-1 text-clamp w-4/5">{{ $t(item.comment) }}</span>
                          <span class="float-right mr-4">({{ $t(item.length) }})</span>
                        </label>
                      </div>

                      <div v-if="index == searchType.data.length - 1">
                        <label
                          class="icons icon-up-arrow link-color cursor-pointer"
                          :class="{ hidden: !showFlagDict[searchType.i18n] }"
                          @click="showFlagDict[searchType.i18n] = !showFlagDict[searchType.i18n]">
                          {{ $t('showSome') }}
                        </label>
                      </div>
                    </div>
                  </li>
                </ul>
                <!-- 日付範囲指定 -->
                <ul v-if="searchType.type == 'date'" class="text-xs font-medium pb-2 max-w-[90%] mx-auto">
                  <li>
                    <VueDatePicker
                      v-model="searchType.data"
                      format="yyyy-MM-dd"
                      model-type="yyyy-MM-dd"
                      :enable-time-picker="false"
                      range
                      @closed="filterSearch"
                      @cleared="filterSearch" />
                  </li>
                </ul>
                <!-- ラジオボタン -->
                <ul v-if="searchType.type == 'radio'" class="pl-4 text-14px font-medium pb-4">
                  <li v-for="item in searchType.data" :key="item.id">
                    <div class="filterSearchCheck w-full" @click="checkTooltip($t(item.comment))">
                      <label class="flex" :class="{ 'tooltip-label': checkTooltip($t(item.comment)) }">
                        <span v-if="checkTooltip($t(item.comment))" class="tooltiptext">
                          {{ $t(item.comment) }}
                        </span>
                        <input
                          :id="item.comment"
                          v-model="searchType.selected"
                          type="radio"
                          :name="searchType.name"
                          class="link-color mt-1"
                          :checked="item.value === 'on'"
                          :value="item.comment"
                          @change="filterSearch" />
                        <label ref="target" class="ml-1 text-clamp w-[78%]" :for="item.comment">
                          {{ $t(item.comment) }}
                        </label>
                        <span class="float-right mr-4">({{ $t(item.length) }})</span>
                      </label>
                    </div>
                  </li>
                </ul>
              </ul>
              <div class="flex justify-center">
                <button
                  class="min-[1022px]:block h-5 min-[1022px]:h-auto min-[1022px]:border min-[1022px]:py-1 pl-2 pr-2.5 rounded text-white font-medium bg-link-color text-14px"
                  @click="clear">
                  {{ $t('clear') }}
                </button>
              </div>
            </div>
            <div class="bg-miby-bg-gray result-area">
              <div class="flex whitespace-nowrap ml-auto my-2 text-center">
                <div class="w-full flex flex-wrap content-center gap-4 justify-start">
                  <p class="icons-type icon-public text-14px">
                    <span>{{ $t('open access') }}</span>
                  </p>
                  <p class="icons-type icon-group text-14px">
                    <span>{{ $t('restricted access') }}</span>
                  </p>
                  <p class="icons-type icon-member text-14px">
                    <span>{{ $t('metadata only access') }}</span>
                  </p>
                  <p class="icons-type icon-private text-14px">
                    <span>{{ $t('embargoed access') }}</span>
                  </p>
                </div>
                <div class="flex justify-end">
                  <a
                    v-if="total"
                    class="pl-1.5 md:pl-0 icons icon-download after cursor-pointer"
                    @click="downloadResultList">
                    <span class="underline text-sm text-miby-link-blue pr-1 text-14px">
                      {{ $t('searchDownloadAll') }}
                    </span>
                  </a>
                </div>
              </div>
              <!-- <div class="flex justify-end"> -->
              <!-- 全件マイリスト -->
              <!-- <a class="pl-1.5 md:pl-0">
                <span class="underline text-sm text-miby-link-blue pr-1 mr-3">
                  {{ $t('searchMylistAll') }}
                </span>
              </a> -->
              <!-- 全件ダウンロード -->
              <!-- <a
                  v-if="total"
                  class="pl-1.5 md:pl-0 icons icon-download after cursor-pointer"
                  @click="downloadResultList"
                >
                  <span class="underline text-sm text-miby-link-blue pr-1">
                    {{ $t("searchDownloadAll") }}
                  </span>
                </a> -->
              <!-- </div> -->
              <!-- スピナー -->
              <div v-if="!renderFlag" class="text-center">
                <span class="loading loading-bars loading-lg" />
              </div>
              <!-- 検索結果 -->
              <SearchResult
                v-if="renderFlag"
                :displayType="displayType"
                :searchResult="searchResult"
                :showFlagDict="showFlagDict" />
              <!-- ページネーション -->
              <div class="max-w-[300px] mx-auto mb-4">
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
      </div>
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
import VueDatePicker from '@vuepic/vue-datepicker';

import FilterColumn from '~/assets/data/filterSearchInfo.json';
import ResultJson from '~/assets/data/searchResult.json';
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
  order: 'asc',
  detail: {},
  detailData: {},
  filter: {}
});
const local = String(localStorage.getItem('locale') ?? 'ja');
const displayType = ref('summary');
const total = ref('');
const searchResult: any = ref({});
const aggregations: any = ref({});
const renderFlag = ref(true);
const creater = ref();
const visibleAlert = ref(false);
const alertType = ref('info');
const alertMessage = ref('');
const alertCode = ref('');
let filterColumnList = JSON.parse(JSON.stringify(FilterColumn));
const filterList = ref<any[]>([]);
let filterNameDict = reactive({});
const columnNameDict = reactive({});
const isOpen = ref(false);
let showFlagDict: any = reactive({}); // 一部を表示|全てを表示
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
  const params = {
    q: conditions.keyword,
    search_type: conditions.type,
    page: conditions.currentPage,
    size: conditions.perPage,
    sort: conditions.order === 'asc' ? conditions.sort : '-' + conditions.sort
  };
  if (conditions.detail) {
    Object.assign(params, conditions.detail);
    for (const key of Object.values(conditions.detail)) {
      if (key) {
        isOpen.value = true;
        break;
      }
    }
  }
  if (conditions.filter) {
    Object.assign(params, conditions.filter);
  }
  const queryStr = createQueryStr(params);

  sessionStorage.setItem('conditions', JSON.stringify(conditions));
  const urlSearchParam = new URLSearchParams(queryStr);

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
        aggregations.value = response._data.aggregations;
        if (filterList.value.length <= 0) {
          createFilter();
        }
        if (filterNameDict && Object.keys(filterNameDict).length > 0) {
          let recheckFlg = false;
          Object.keys(filterNameDict).forEach((item, index) => {
            // @ts-ignore
            reflectCopyFilter(item, filterNameDict[item]);
            if (item.includes('date_range')) {
              recheckFlg = true;
            }
            if (index === Object.keys(filterNameDict).length - 1) {
              filterNameDict = {};
            }
          });
          if (recheckFlg) {
            // NOTE:日付検索のみファセット検索を使用出来ないため、フィルター作成後に絞り込みする
            filterSearch();
          }
        }
      }
    },
    onResponseError({ response }) {
      alertCode.value = '';
      statusCode = response.status;
      if (statusCode === 401) {
        // 認証エラー
        alertMessage.value = 'message.error.auth';
        alertCode.value = 'E_SEARCH_INDEX_0001';
      } else if (statusCode >= 500 && statusCode < 600) {
        // サーバーエラー
        alertMessage.value = 'message.error.server';
        alertCode.value = 'E_SEARCH_INDEX_0002';
      } else {
        // リクエストエラー
        alertMessage.value = 'message.error.search';
        alertCode.value = 'E_SEARCH_INDEX_0003';
      }
      alertType.value = 'error';
      visibleAlert.value = true;
    },
  }).catch(() => {
    if (statusCode === 0) {
      // fetchエラー
      alertMessage.value = 'message.error.fetch';
      alertType.value = 'error';
      alertCode.value = 'E_SEARCH_INDEX_0004';
      visibleAlert.value = true;
    }
  });
}

/**
 * 検索用にクエリ文字列を作成する
 * @param params
 */
function createQueryStr(params: any) {
  const queryStringParts = [];

  for (const key in params) {
    if (Array.isArray(params[key])) {
      params[key].forEach((value) => {
        queryStringParts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
      });
    } else {
      queryStringParts.push(`${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`);
    }
  }

  return queryStringParts.join('&');
}

/**
 * ファセット検索の結果からフィルターを作成する
 */
function createFilter() {
  for (const column of filterColumnList) {
    if (column.displayed) {
      if (column.type === 'checkbox') {
        Object.keys(aggregations.value).forEach((ag: any) => {
          if (ag === column.facetKey) {
            let count = 1;
            const name = column.facetKey;
            if (aggregations.value[name].buckets.length) {
              for (const i in aggregations.value[name].buckets) {
                const item = aggregations.value[name].buckets[i];
                if (column.langCheckNeed) {
                  if ((local === 'ja' && !checkEn(item.key)) || (local === 'en' && checkEn(item.key))) {
                    // do nothting
                  } else {
                    continue;
                  }
                }
                column.data.push({
                  id: count++,
                  comment: item.key,
                  length: item.doc_count,
                  value: false
                });
              }
            }
            if (column.data.length > 0) {
              filterList.value.push(JSON.parse(JSON.stringify(column)));
              // 「すべてを表示／一部を表示」のflagを生成する
              showFlagDict[column.i18n] = false;
            }
          }
        });
      } else if (column.type === 'date') {
        filterList.value.push(JSON.parse(JSON.stringify(column)));
      } else if (column.type === 'radio') {
        const name = column.facetKey;
        if (aggregations.value[name] && aggregations.value[name].buckets.length) {
          let count = 2;
          for (const i in aggregations.value[name].buckets) {
            const item = aggregations.value[name].buckets[i];
            column.data.push({
              id: count++,
              comment: item.key,
              length: item.doc_count,
              value: false
            });
          }
          filterList.value.push(JSON.parse(JSON.stringify(column)));
        }
      }
    }
  }
}

/**
 * 英文(記号含む)かどうかチェックする
 * @param name
 */
function checkEn(name: any) {
  name = name.replace(/\s+/g, '');
  if (/[\p{Script_Extensions=Greek}]/v.test(name)) {
    name = name.replace(/[α-ω]/g, '');
  }
  return /^[ -~]+$/.test(name);
}

/**
 * 全角を1文字、半角を0.5文字として文字数をカウントし、14ないし15文字を超えるかどうかを判定する
 * 超えたらTooltipを表示する
 * @param name
 * @returns {boolean}
 */
function checkTooltip(name: any) {
  // FIXME: 日本語と英語が入り混じった文章が来る想定のため、文字数での判定には限界がある
  // 文字列のwidthを計算して判定する方法を検討する必要あり
  let totalLength = 0;
  let halfwidthChar = 0;

  for (let i = 0; i < name.length; i++) {
    const char = name[i];
    if (char === '｜') {
      // 「｜」を1.25文字としてカウント
      totalLength += 1.25;
    } else if (char.match(/[\uFF01-\uFF60\uFFE0-\uFFE6\u4E00-\u9FFF]/) || char.match(/[^\x20-\x7E]/)) {
      // 全角文字
      totalLength += 1;
    } else {
      // 半角文字
      totalLength += 0.5;
      halfwidthChar++;
    }
  }

  if (totalLength !== 15 && halfwidthChar > 14) {
    return totalLength > 14;
  }
  return totalLength > 15;
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
  if (conditions.filter) {
    Object.assign(params, conditions.filter);
  }
  const queryStr = createQueryStr(params);

  const urlSearchParam = new URLSearchParams(queryStr);

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
      alertCode.value = '';
      statusCode = response.status;
      if (statusCode === 401) {
        // 認証エラー
        alertMessage.value = 'message.error.auth';
        alertCode.value = 'E_SEARCH_INDEX_0005';
      } else if (statusCode >= 500 && statusCode < 600) {
        // サーバーエラー
        alertMessage.value = 'message.error.server';
        alertCode.value = 'E_SEARCH_INDEX_0006';
      } else {
        // リクエストエラー
        alertMessage.value = 'message.error.downloadResult';
        alertCode.value = 'E_SEARCH_INDEX_0007';
      }
      alertType.value = 'error';
      visibleAlert.value = true;
    },
  }).catch(() => {
    if (statusCode === 0) {
      // fetchエラー
      alertMessage.value = 'message.error.fetch';
      alertType.value = 'error';
      alertCode.value = 'E_SEARCH_INDEX_0008';
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
    showFlagDict = reactive({});
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
  filterList.value = [];
  filterColumnList = JSON.parse(JSON.stringify(FilterColumn));
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
    conditions.detail = json.detail ?? {};
    conditions.detailData = json.detailData ?? {};
    conditions.filter = json.filter ?? {};
  }
}

// /**
//  * 作成者情報モーダル表示
//  * 10/25 現在使用出来ていない
//  */
// function openCreaterModal() {
//   creater.value.openModal();
// }

/**
 * フィルターによる絞り込み
 */
function filterSearch() {
  const filter: any = {};
  for (const column of filterList.value) {
    if (column.type === 'checkbox') {
      const valueList: Array<string> = [];
      column.data.forEach((data: any) => {
        if (data.value) {
          valueList.push(data.comment);
        }
      });
      if (valueList.length > 0) {
        Object.assign(filter, { [column.facetKey]: valueList });
      }
    } else if (column.type === 'date') {
      if (!column.data || !column.data[0]) {
        continue;
      }
      Object.assign(filter, {
        [column.queryFrom]: column.data ? column.data[0].replaceAll('-', '') : ''
      });
      Object.assign(filter, {
        [column.queryTo]: column.data ? (column.data[1] ? column.data[1].replaceAll('-', '') : '') : ''
      });
    } else if (column.type === 'radio') {
      if (column.selected !== 'notSelected') {
        Object.assign(filter, { [column.facetKey]: column.selected });
      }
    }
  }
  conditions.filter = filter;
  sessionStorage.setItem('conditions', JSON.stringify(conditions));
  renderResult();
}

/**
 * フィルターのクリアボタン押下時イベント
 */
function clear() {
  filterColumnList = JSON.parse(JSON.stringify(FilterColumn));
  filterList.value = [];
  conditions.filter = {};
  sessionStorage.setItem('conditions', JSON.stringify(conditions));
  renderResult();
}

/** ファイル一覧画面からアイテム詳細画面へ戻るためのURL取得準備 */
function setURL() {
  sessionStorage.removeItem('url');
  sessionStorage.setItem('url', window.location.href);
}

/**
 * アクセスされたURLがエクスポートされたものかどうか判断する
 */
function checkExportURL() {
  const hereURL = window.location.href.split('?');
  conditions.filter = {};
  conditions.detail = {};
  if (hereURL[1]) {
    sessionStorage.removeItem('conditions');
    history.pushState('', '', `${appConf.amsPath ?? ''}/search`);
    const searchParams = new URLSearchParams(hereURL[1]);
    const params = Object.fromEntries(searchParams.entries());
    for (const key in params) {
      if (key === 'q') {
        Object.assign(columnNameDict, { [key]: params[key] });
        conditions.keyword = params[key];
      } else if (key === 'search_type') {
        conditions.type = params[key];
      } else if (key === 'page') {
        conditions.currentPage = params[key];
      } else if (key === 'size') {
        conditions.perPage = params[key];
      } else if (key === 'sort') {
        conditions.sort = params[key];
        if (params[key][0] === '-') {
          conditions.sort = params[key].slice(1);
          conditions.order = 'desc';
        } else {
          conditions.sort = params[key];
          conditions.order = 'asc';
        }
      } else if (key.endsWith('_filter')) {
        Object.assign(filterNameDict, { [key]: params[key] });
        if (typeof params[key] === 'string' && params[key].includes(',')) {
          Object.assign(conditions.filter, { [key]: params[key].split(',') });
        } else {
          Object.assign(conditions.filter, { [key]: params[key] });
        }
      } else if (key.startsWith('date_range')) {
        Object.assign(filterNameDict, { [key]: params[key] });
      } else {
        Object.assign(columnNameDict, { [key]: params[key] });
        Object.assign(conditions.detail, { [key]: params[key] });
        isOpen.value = true;
      }
    }
  }
}

/**
 * フィルターに検索条件コピーの内容を反映させる
 */
function reflectCopyFilter(key: any, value: any) {
  const values = typeof value === 'string' ? value.split(',') : [value];
  for (const filter of filterList.value) {
    if (filter.facetKey === key) {
      for (const item of filter.data) {
        if (filter.type === 'checkbox') {
          for (const value of values) {
            if (item.comment === value) {
              item.value = true;
            }
          }
        } else if (filter.type === 'radio') {
          if (item.comment === value) {
            item.value = 'on';
          } else {
            item.value = false;
          }
        }
      }
    } else if (filter.type === 'date') {
      if (filter.queryFrom === key || filter.queryTo === key) {
        Object.assign(conditions.filter, { [key]: value });
        const dateArray = [];
        // NOTE:dateのvalueはYYYYMMDDの形式で来る
        if (value.length === 8) {
          dateArray.push(value.slice(0, 4)); // YYYY
          dateArray.push(value.slice(4, 6)); // MM
          dateArray.push(value.slice(6, 8)); // DD
        } else {
          return;
        }

        value = dateArray.join('-');
        filter.data.push(value);
        if (filter.data.length === 2) {
          filter.data.sort();
        }
      }
    }
  }
}

/* ///////////////////////////////////
// main
/////////////////////////////////// */

try {
  checkExportURL();
  await search();
} catch (error) {
  alertCode.value = 'E_SEARCH_INDEX_0009';
  alertMessage.value = 'message.error.error';
  alertType.value = 'error';
  visibleAlert.value = true;
}

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
