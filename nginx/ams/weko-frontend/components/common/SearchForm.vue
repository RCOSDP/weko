<template>
  <div class="bg-MainBg bg-no-repeat bg-top bg-cover pt-[130px] pb-6 mt-[-180px] mb-[15px]">
    <form class="max-w-5xl mx-auto pt-16 px-5" @submit.prevent="search">
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
    <div class="text-white mb-[15px] flex gap-5 items-center justify-center" :class="{ deactive: !isOpen }">
      <div id="detail-search-content" :class="{ deactive: !isOpen }">
        <TransitionGroup name="list" tag="ul" class="h-full detail-search-list">
          <!-- タイトル検索方法 -->
          <li class="flex mb-0.5">
            <div class="detail-search-label">
              <label class="w-36">
                {{ $t('titleSearchType') }}
              </label>
            </div>
            <div class="flex-wrap ml-9 items-center list-content flex">
              <div v-for="type in titleSearchType" :key="type.name">
                <!-- TODO: 完全一致の文言・処理はそちらのチケットに合わせること -->
                <label class="mr-2 text-sm">
                  <input
                    v-model="type.select"
                    :checked="type.select"
                    type="radio"
                    class="mr-1 link-color"
                    name="title-search-type"
                    :value="true"
                    @change="changeSearchType(type.name)" />
                  {{ $t(type.name) }}
                </label>
              </div>
            </div>
          </li>
          <!-- タイトル -->
          <li class="flex mb-0.5">
            <div class="detail-search-label">
              <label class="w-36">
                {{ $t(columnList[0].i18n) }}
              </label>
            </div>
            <div class="ml-9 list-content">
              <input v-model="columnList[0].data" type="text" class="rounded h-8 w-full text-black" />
            </div>
          </li>

          <!-- タイトル（columnList[0]）以降のlistを生成 -->
          <li v-for="(column, index) in columnList" :key="column.id" class="flex mb-0.5">
            <div class="detail-search-label">
              <label v-if="index !== 0" class="w-36">
                {{ $t(column.i18n) }}
              </label>
            </div>
            <!--入力フォーム形式 -->
            <div v-if="column.type == 'text' && index !== 0" class="ml-9 list-content">
              <input v-model="column.data" type="text" class="rounded h-8 w-full text-black" />
            </div>
            <!-- チェックボックス形式 -->
            <div v-else-if="column.type === 'checkbox'" class="flex-wrap ml-9 items-center list-content flex">
              <div v-for="item in column.data" :key="item.id">
                <label
                  class="flex items-center text-sm checkbox-label mr-5"
                  :class="column.query === 'license' ? 'w-32' : 'w-auto'">
                  <input v-model="item.value" type="checkbox" class="mr-1 link-color" />
                  <span v-if="item.i18n">
                    {{ $t(item.i18n) }}
                  </span>
                  <span v-else>
                    {{ item.comment }}
                  </span>
                </label>
              </div>
            </div>
            <!-- 日付形式 -->
            <div v-else-if="column.type === 'date'" class="ml-9 items-center md:justify-start list-content flex">
              <!-- チェックボックス -->
              <div class="flex mb-2">
                <div v-for="item in column.checkbox" :key="item.id">
                  <label class="flex items-center text-sm checkbox-label date-mr">
                    <input v-model="item.value" type="checkbox" class="mr-1 link-color" />
                    <span>
                      {{ $t(item.i18n) }}
                    </span>
                  </label>
                </div>
              </div>
              <!-- カレンダー -->
              <VueDatePicker
                v-model="column.data"
                format="yyyy/MM/dd"
                model-type="yyyy-MM-dd"
                :enable-time-picker="false"
                range
                style="width: auto" />
            </div>
            <!-- リストボックス形式 -->
            <div v-else-if="column.type === 'listbox'" class="flex-wrap ml-9 items-center list-content flex">
              <select v-model="column.selected" class="rounded h-8 p-0 pl-1.5 text-black w-[auto]">
                <option v-for="list in column.data" :key="list.id" :value="list.comment">
                  {{ $t(list.i18n) }}
                </option>
              </select>
            </div>
            <!-- ラジオボタン形式 -->
            <div v-else-if="column.type === 'radio'" class="flex-wrap ml-9 items-center list-content flex">
              <div v-for="item in column.data" :key="item.id">
                <label class="flex items-center text-sm checkbox-label mr-5 w-auto">
                  <input
                    v-model="column.selected"
                    type="radio"
                    class="mr-1 link-color"
                    :name="column.i18n"
                    :value="item.comment"
                    :checked="item.comment === column.selected" />
                  <span>
                    {{ $t(item.i18n) }}
                  </span>
                </label>
              </div>
            </div>
            <!-- 項目削除ボタン -->
            <button
              v-if="index !== 0"
              class="block removeForm text-miby-black font-medium flex-col flex-wrap w-12"
              type="button"
              @click="remove(column)">
              <span class="icons icon-remove" />
            </button>
          </li>
        </TransitionGroup>
        <!-- 条件追加 -->
        <div class="max-w-5xl mx-auto">
          <div class="flex justify-end pt-2">
            <select
              id="AddCondition"
              v-model="selected"
              class="text-white text-sm block w-[150px] pl-4 rounded-md bg-link-color"
              @change="insert(selected)">
              <option disabled>{{ $t('addConditions') }}</option>
              <option v-for="column in selector" :key="column.id" :value="column.id" :disabled="isDisable(column)">
                {{ $t(column.i18n) }}
              </option>
            </select>
          </div>
        </div>
      </div>
    </div>
    <div v-if="!isOpen" class="text-white mb-[15px] flex gap-5 items-center justify-center">
      <button
        id="search_form"
        class="icons detail-search-open block cursor-pointer border py-1 text-center rounded-md text-sm w-[130px]"
        @click="isOpen = !isOpen">
        {{ $t('advanced') }}
      </button>
    </div>
    <div v-else class="text-white mb-[15px] flex gap-5 items-center justify-center">
      <button
        id="search_form"
        class="block cursor-pointer border py-1 text-center rounded-md text-sm w-[130px]"
        @click="clear">
        {{ $t('clear') }}
      </button>
      <button
        id="search_form"
        class="icons detail-search-close block cursor-pointer border py-1 text-center rounded-md text-sm w-[130px]"
        @click="isOpen = !isOpen">
        {{ $t('close') }}
      </button>

      <!-- <a class="block cursor-pointer border py-1 text-center rounded-md text-sm w-[130px]">
        <img :src="`${useAppConfig().amsImage ?? '/img'}/btn/btn-mylist.svg`" class="w-[94px] mx-auto" alt="My List" />
      </a> -->
    </div>
    <!-- データ総数 -->
    <div
      v-if="displayFlag"
      class="data-statistics p-5 sm:p-0 flex flex-wrap justify-between sm:justify-center gap-x-1 gap-y-4 sm:gap-7 w-3/4 sm:w-full mx-auto">
      <div class="sm:w-fit thesis">
        <p class="icons icon-thesis text-xs text-white md:text-center">
          {{ $t('totalDataset') }}
        </p>
        <p class="number text-white text-xs md:text-center font-bold">
          {{ dataset.toLocaleString() }}
        </p>
      </div>
      <div class="sm:w-fit thesis">
        <p class="icons icon-thesis text-xs text-white md:text-center">
          {{ $t('totalJournalArticle') }}
        </p>
        <p class="number text-white text-xs md:text-center font-bold">
          {{ journal.toLocaleString() }}
        </p>
      </div>
      <div class="sm:w-fit noro">
        <p class="icons icon-noro text-xs text-white md:text-center">
          {{ $t('totalAuthor') }}
        </p>
        <p class="number text-white text-xs md:text-center font-bold">
          {{ author.toLocaleString() }}
        </p>
      </div>
    </div>
  </div>
  <!-- 詳細検索 -->
  <DetailSearch ref="detailSearch" :sessCondFlag="isRestore" class="z-50" @detail-search="clickDetailSearch" />
</template>

<script lang="ts" setup>
import VueDatePicker from '@vuepic/vue-datepicker';
import { useI18n } from 'vue-i18n';

import DetailColumn from '~/assets/data/detailSearch.json';
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
  },
  // 詳細検索の開閉
  isOpen: {
    type: Boolean,
    default: false
  },
  columnNameDict: {
    type: Object,
    default: () => {}
  }
});

/* ///////////////////////////////////
// emits
/////////////////////////////////// */

const emits = defineEmits(['clickSearch']);

/* ///////////////////////////////////
// interface
/////////////////////////////////// */

interface ICeckboxData {
  id: number;
  comment: string;
  name: string;
  query: string;
  value: boolean;
}
interface IIndexObj {
  list: Array<object>;
}

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const conditions = reactive({
  type: '0',
  keyword: '',
  detail: {},
  detailData: {},
  filter: {}
});
const detailSearch = ref();
const isRestore = ref(props.sessCondFlag);
const dataset = ref(0);
const journal = ref(0);
const author = ref(0);
let selector = JSON.parse(JSON.stringify(DetailColumn));
let selectorDefault = useI18n().t('addConditions');
const columnList = ref<any[]>([]);
const selected = ref(selectorDefault);
const isOpen = ref(props.isOpen);
let columnNameDict = reactive(props.columnNameDict);
const titleSearchType = reactive({
  // あいまい検索（部分一致）
  partialMatch: {
    select: true,
    name: 'partialMatch'
  },
  // 完全一致
  exactMatch: {
    select: false,
    name: 'exactMatch'
  }
});
const appConf = useAppConfig();

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * 検索ボタン押下時イベント
 */
function search() {
  const detail = {};
  isOpen.value = false;
  conditions.filter = {};
  // セッションに詳細検索条件を設定
  isOpen.value = false;
  for (const column of columnList.value) {
    if (column.type === 'text') {
      if (column.data) {
        Object.assign(detail, { [column.query]: column.data });
        isOpen.value = true;
      } else {
        Object.assign(detail, { [column.query]: '' });
      }
    } else if (column.type === 'checkbox') {
      const valueList: Array<string> = [];
      for (const data of column.data) {
        if (data.value) {
          valueList.push(data.comment);
          isOpen.value = true;
        }
      }
      // NOTE: 公開区分とダウンロード区分はdetailSearch.jsonのdata.queryに値があれば渡る
      if (valueList) {
        Object.assign(detail, { [column.query]: valueList.join(',') });
      } else {
        Object.assign(detail, { [column.query]: '' });
      }
    } else if (column.type === 'date') {
      if (column.checkbox) {
        const valueList: Array<string> = [];
        for (const data of column.checkbox) {
          if (data.value) {
            valueList.push(data.query);
            isOpen.value = true;
          }
        }
        Object.assign(detail, {
          [column.queryFrom]: column.data ? column.data[0].replaceAll('-', '') : ''
        });
        Object.assign(detail, {
          [column.queryTo]: column.data ? (column.data[1] ? column.data[1].replaceAll('-', '') : '') : ''
        });
        Object.assign(detail, { [column.query]: valueList.join(',') });
      } else {
        Object.assign(detail, {
          [column.queryFrom]: column.data ? column.data[0].replaceAll('-', '') : ''
        });
        Object.assign(detail, {
          [column.queryTo]: column.data ? (column.data[1] ? column.data[1].replaceAll('-', '') : '') : ''
        });
      }
    } else if (column.type === 'radio' || column.type === 'listbox') {
      for (const i in column.data) {
        if (column.data[i].comment !== column.selected || column.selected === 'notSelected') {
          Object.assign(detail, { [column.query]: '' });
        } else {
          Object.assign(detail, { [column.query]: column.selected });
          isOpen.value = true;
          break;
        }
      }
    }
  }
  if (titleSearchType.exactMatch.select) {
    Object.assign(detail, { exact_title_match: true });
  }
  conditions.detail = detail;
  conditions.detailData = columnList.value;
  if (location.pathname.includes('/search')) {
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
    navigateTo(`${appConf.amsPath ?? ''}/search`);
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
 * 詳細検索条件のインデックスに表示する項目を取得する
 * @param indexList インデックス一覧
 * @param obj インデックス名格納用オブジェクト(結果出力用)
 * @param parent 親インデックス名
 */
function createIndexList(indexList: any, obj: IIndexObj, parent = '') {
  for (const index of indexList) {
    const data: ICeckboxData = {
      id: index.position,
      comment: parent ? parent + '/' + index.value : index.value,
      name: index.name,
      query: index.id,
      value: false
    };
    obj.list.push(data);

    if (index.children.length > 0) {
      createIndexList(index.children, obj, index.name);
    }
  }
}

/**
 * 検索条件追加
 * @param item 追加する条件項目のID
 */
function insert(item: string) {
  for (const column of selector) {
    if (column.id === item) {
      columnList.value.push(JSON.parse(JSON.stringify(column)));
    }
  }
  selected.value = selectorDefault;
}

/**
 * 追加選択した検索条件が追加可能か判定
 * @param column 選択した条件項目オブジェクト
 */
function isDisable(column: any) {
  if (columnList.value.filter((e: any) => e.id === column.id).length > 0) {
    return true;
  }
  return false;
}

/**
 * 検索条件削除
 * @param column 削除する検索条件オブジェクト
 */
function remove(column: any) {
  const i = columnList.value.indexOf(column);
  if (i > -1) {
    columnList.value.splice(i, 1);
  }
}

/**
 * 詳細検索条件初期化
 */
function clear() {
  const selectColumn: any = [];
  selector = JSON.parse(JSON.stringify(DetailColumn));
  columnList.value.forEach((item: any) => {
    for (const column of selector) {
      if (item.i18n === column.i18n) {
        selectColumn.push(column);
      }
    }
  });
  columnList.value = [];

  selectColumn.forEach((item: any) => {
    columnList.value.push(JSON.parse(JSON.stringify(item)));
  });

  conditions.type = '0';
  conditions.keyword = '';
  selected.value = selectorDefault;
  isRestore.value = true;
  titleSearchType.exactMatch.select = false;
  titleSearchType.partialMatch.select = true;
  emits('clickSearch');
}

/**
 * タイトルの検索方法の切り替え
 * @param name partialMatch(あいまい検索) | exactMatch(完全一致)
 */
function changeSearchType(name: any) {
  if (name === 'exactMatch') {
    titleSearchType.partialMatch.select = false;
  } else {
    titleSearchType.exactMatch.select = false;
  }
}

/**
 * キーワードと詳細検索に検索条件コピーの内容を反映させる
 * @param key 詳細検索で使用するroCateのキー名
 * @param value 詳細検索の入力値
 */
function createColumnList(key: any, value: any) {
  if (key === 'q') {
    conditions.keyword = value;
  }

  for (const [i, column] of selector.entries()) {
    const defaultColumn = JSON.parse(JSON.stringify(DetailColumn));
    if (key === 'title') {
      if (value) {
        column.data = value;
        isOpen.value = true;
      }
      columnList.value[0] = column;
      break;
    } else if (column.query === key) {
      if (value) {
        const splitValues = value.split(',');
        if (column.type === 'checkbox') {
          for (const columnData of defaultColumn[i].data) {
            columnData.value = false;
            for (const splitValue of splitValues) {
              if (columnData.comment === splitValue) {
                columnData.value = true;
              }
            }
          }
          column.data = defaultColumn[i].data;
        } else if (column.type === 'radio' || column.type === 'listbox') {
          column.selected = '';
          for (const columnData of defaultColumn[i].data) {
            if (columnData.comment === value) {
              defaultColumn[i].selected = columnData.comment;
            }
          }
          column.selected = defaultColumn[i].selected;
        } else {
          column.data = value;
        }
        isOpen.value = true;
      }
      columnList.value.push(JSON.parse(JSON.stringify(column)));
      break;
    }
  }
  if (key === 'exact_title_match' && value === 'true') {
    titleSearchType.exactMatch.select = true;
    titleSearchType.partialMatch.select = false;
  }
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
      credentials: 'omit',
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
      credentials: 'omit',
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

    // 詳細検索の一覧更新
    await $fetch(useAppConfig().wekoApi + '/tree/index', {
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
          const dataList: IIndexObj = { list: [] };

          // 検索条件表示用インデックスデータ準備
          createIndexList(response._data.index.children, dataList);
          // 検索条件表示用インデックスデータ置き換え
          const indexJson = DetailColumn.find(({ query }) => query === 'iid');
          if (indexJson) {
            // @ts-ignore
            indexJson.data = dataList.list;
          }
          selector = JSON.parse(JSON.stringify(DetailColumn));
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

  // 検索条件コピーのURLでアクセスしてきた場合
  if (columnNameDict && Object.keys(columnNameDict).length > 0) {
    columnList.value = [];
    isOpen.value = false;
    Object.keys(columnNameDict).forEach((item, index) => {
      createColumnList(item, columnNameDict[item]);

      if (index === Object.keys(columnNameDict).length - 1) {
        columnNameDict = {};
      }
    });
  }

  if (con && props.sessCondFlag) {
    if (
      !Object.prototype.hasOwnProperty.call(JSON.parse(con), 'detail') ||
      Object.keys(JSON.parse(con).detail).length === 0
    ) {
      conditions.type = JSON.parse(con).type ?? '0';
      conditions.keyword = JSON.parse(con).keyword ?? '';
    }
  }
  selectorDefault = useI18n().t('addConditions');
  selected.value = selectorDefault;
});

onBeforeMount(() => {
  columnList.value = [];
  const con = sessionStorage.getItem('conditions');
  const json = con ? JSON.parse(con) : null;

  if (
    json &&
    props.sessCondFlag &&
    Object.prototype.hasOwnProperty.call(json, 'detailData') &&
    Object.keys(json.detailData).length !== 0
  ) {
    conditions.type = json.type ?? '0';
    conditions.keyword = json.keyword ?? '';
    columnList.value = json.detailData;
    if (json.detail.exact_title_match) {
      titleSearchType.exactMatch.select = true;
      titleSearchType.partialMatch.select = false;
    }
  } else {
    for (const column of selector) {
      if (column.default) {
        columnList.value.push(JSON.parse(JSON.stringify(column)));
      }
    }
  }
});
</script>
