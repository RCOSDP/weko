<template>
  <dialog :class="[modalShowFlag ? 'visible' : 'invisible']" class="bg-black" @click="closeModal">
    <div class="modal-center z-50" @click.stop>
      <div class="bg-miby-light-blue flex flex-row">
        <div class="basis-1/6" />
        <!-- タイトル -->
        <div class="basis-4/6">
          <p class="text-white leading-[43px] text-center font-medium">{{ $t('advanced') }}</p>
        </div>
        <!-- 閉じるボタン -->
        <div class="basis-1/6 flex text-end justify-end pr-3">
          <button type="button" class="btn-close">
            <img :src="`${appConf.amsImage ?? '/img'}/btn/btn-close.svg`" alt="×" @click="closeModal" />
          </button>
        </div>
      </div>
      <form
        v-if="modalShowFlag"
        class="mt-[-3px] pt-8 pb-8 md:mt-0 md:border-0 rounded-b-md px-2.5"
        @submit.prevent="search">
        <div class="modalForm overflow-y-auto scroll-smooth h-full">
          <div class="mb-2.5 flex justify-between items-center">
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
            <!-- マイリスト -->
            <!-- <button id="addMyList" class="text-miby-blue text-sm" disabled>
              <span class="icons icon-mylist-b align-middle text-miby-link-blue">{{ $t('myList') }}</span>
            </button> -->
          </div>
          <div class="mb-8">
            <!-- 検索ワード入力フォーム -->
            <input v-model="conditions.keyword" type="text" class="rounded h-10 w-full" />
          </div>
          <!-- 詳細検索条件 -->
          <TransitionGroup name="list" tag="ul" class="h-full">
            <li v-for="column in columnList" :key="column.id" class="mb-5">
              <!-- 項目削除ボタン -->
              <button class="block mb-2 removeForm text-miby-black font-medium" type="button" @click="remove(column)">
                <span class="icons icon-remove align-middle">
                  {{ $t(column.i18n) }}
                </span>
              </button>
              <!--入力フォーム形式 -->
              <div v-if="column.type == 'text'" class="ml-9">
                <input v-model="column.data" type="text" class="rounded h-8 w-full" />
              </div>
              <!-- チェックボックス形式 -->
              <div
                v-else-if="column.type == 'checkbox'"
                class="flex-wrap ml-7 items-center"
                :class="column.query === 'iid' ? 'flex-col' : 'flex'">
                <div v-for="item in column.data" :key="item.id">
                  <label
                    class="flex items-center text-sm checkbox-label mr-5"
                    :class="column.query === 'iid' ? 'w-auto' : 'w-32'">
                    <input v-model="item.value" type="checkbox" class="mr-1" />
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
              <div
                v-else-if="column.type == 'date'"
                class="ml-9 flex-col flex-wrap md:flex-nowrap items-center md:justify-start max-w-[345px]">
                <!-- チェックボックス -->
                <div class="flex mb-2">
                  <div v-for="item in column.checkbox" :key="item.id">
                    <label class="flex items-center text-sm checkbox-label mr-5">
                      <input v-model="item.value" type="checkbox" class="mr-1" />
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
                  range />
              </div>
            </li>
          </TransitionGroup>
        </div>
        <!-- 条件追加 -->
        <div class="max-w-[500px] mx-auto">
          <div class="flex justify-end pt-2">
            <select
              id="AddCondition"
              v-model="selected"
              class="bg-miby-link-blue border border-miby-link-blue text-white text-sm block w-[150px] pl-4"
              @change="insert(selected)">
              <option disabled>{{ $t('addConditions') }}</option>
              <option v-for="column in selector" :key="column.id" :value="column.id" :disabled="isDisable(column)">
                {{ $t(column.i18n) }}
              </option>
            </select>
          </div>
        </div>
        <!-- 検索/クリア -->
        <div class="flex items-center justify-center pt-5 gap-4">
          <button
            type="button"
            class="text-miby-black text-sm text-center font-medium border hover:bg-gray-200 border-miby-black py-1.5 px-5 block min-w-[96px] rounded"
            @click="clear">
            {{ $t('clear') }}
          </button>
          <button
            type="submit"
            class="text-white text-sm text-center bg-orange-400 hover:bg-miby-orange font-medium py-1.5 px-5 block min-w-[96px] rounded">
            {{ $t('search') }}
          </button>
        </div>
      </form>
    </div>
    <div class="backdrop" />
  </dialog>
</template>

<script lang="ts" setup>
import VueDatePicker from '@vuepic/vue-datepicker';
import { useI18n } from 'vue-i18n';

import DetailColumn from '~/assets/data/detailSearch.json';
import '@vuepic/vue-datepicker/dist/main.css';

/* ///////////////////////////////////
// expose
/////////////////////////////////// */

defineExpose({
  openModal
});

/* ///////////////////////////////////
// props
/////////////////////////////////// */

const props = defineProps({
  // 検索条件の復元可否
  sessCondFlag: {
    type: Boolean,
    default: false
  }
});

/* ///////////////////////////////////
// emits
/////////////////////////////////// */

const emits = defineEmits(['detailSearch']);

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

let selectorDefault = useI18n().t('addConditions');
const modalShowFlag = ref(false);
const conditions = reactive({ type: '0', keyword: '', detail: {}, detailData: {} });
const columnList = ref<any[]>([]);
const selected = ref(selectorDefault);
let selector = JSON.parse(JSON.stringify(DetailColumn));
const appConf = useAppConfig();

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * 検索条件追加
 * @param item 追加する条件項目名
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
 * 詳細検索
 */
function search() {
  const detail = {};
  // セッションに詳細検索条件を設定
  for (const column of columnList.value) {
    if (column.type === 'text') {
      Object.assign(detail, { [column.query]: column.data ?? '' });
    } else if (column.type === 'checkbox') {
      const valueList: Array<string> = [];
      for (const data of column.data) {
        if (data.value) {
          valueList.push(data.query);
        }
      }
      Object.assign(detail, { [column.query]: valueList.join(',') });
    } else if (column.type === 'date') {
      if (column.checkbox.length > 0) {
        const valueList: Array<string> = [];
        for (const data of column.checkbox) {
          if (data.value) {
            valueList.push(data.query);
          }
        }
        Object.assign(detail, { [column.queryFrom]: column.data ? column.data[0].replaceAll('-', '') : '' });
        Object.assign(detail, {
          [column.queryTo]: column.data ? (column.data[1] ? column.data[1].replaceAll('-', '') : '') : ''
        });
        Object.assign(detail, { [column.query]: valueList.join(',') });
      } else {
        Object.assign(detail, { [column.queryFrom]: column.data ? column.data[0].replaceAll('-', '') : '' });
        Object.assign(detail, {
          [column.queryTo]: column.data ? (column.data[1] ? column.data[1].replaceAll('-', '') : '') : ''
        });
      }
    }
  }
  conditions.detail = detail;
  conditions.detailData = columnList.value;

  // ページ遷移
  if (useRoute().path.includes('/search')) {
    if (sessionStorage.getItem('conditions')) {
      // @ts-ignore
      const sessConditions = JSON.parse(sessionStorage.getItem('conditions'));
      Object.assign(sessConditions, conditions);
      sessionStorage.setItem('conditions', JSON.stringify(sessConditions));
    } else {
      sessionStorage.setItem('conditions', JSON.stringify(conditions));
    }
    emits('detailSearch');
    closeModal();
  } else {
    sessionStorage.setItem('conditions', JSON.stringify(conditions));
    navigateTo(`${appConf.amsPath ?? ''}/search`);
    closeModal();
  }
}

/**
 * 詳細検索条件初期化
 */
function clear() {
  columnList.value = [];
  for (const column of selector) {
    if (column.default) {
      columnList.value.push(JSON.parse(JSON.stringify(column)));
    }
  }
  conditions.type = '0';
  conditions.keyword = '';
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
 * 詳細検索条件のインデクスに表示する項目を取得する
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
 * モーダル表示
 */
function openModal() {
  modalShowFlag.value = true;
  document.body.classList.add('overflow-hidden');
}

/**
 * モーダル非表示
 */
function closeModal() {
  modalShowFlag.value = false;
  document.body.classList.remove('overflow-hidden');
}

/* ///////////////////////////////////
// main
/////////////////////////////////// */

try {
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
} catch (error) {
  // console.log(error);
}

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

watch(
  () => props.sessCondFlag,
  () => {
    if (!props.sessCondFlag) {
      clear();
    }
  }
);

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
  } else {
    for (const column of selector) {
      if (column.default) {
        columnList.value.push(JSON.parse(JSON.stringify(column)));
      }
    }
  }
});

onMounted(() => {
  selectorDefault = useI18n().t('addConditions');
  selected.value = selectorDefault;
});
</script>

<style scoped lang="scss">
.border-collapse {
  th {
    @apply border border-miby-thin-gray text-center align-middle;
    @apply py-1 font-medium;
  }
  td {
    @apply border border-miby-thin-gray text-center align-middle;
    @apply px-2 pt-5 pb-7;
  }
}
</style>
