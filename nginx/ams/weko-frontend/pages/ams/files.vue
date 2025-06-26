<template>
  <div>
    <!-- 検索フォーム -->
    <SearchForm :sessCondFlag="false" />
    <main class="mx-auto max-w-[97vw]">
      <div class="w-full">
        <div class="w-full">
          <div class="bg-miby-light-blue w-full flex">
            <p class="text-white leading-[43px] pl-5 icons icon-list font-bold">{{ itemTitle }}</p>
            <p class="text-white leading-[43px] pr-5 ml-auto">
              {{
                (Number(filteredList.length) ? String((Number(currentPage) - 1) * Number(perPage) + 1) : 0) +
                ' - ' +
                String(
                  (Number(currentPage) - 1) * Number(perPage) + Number(perPage) > Number(filteredList.length)
                    ? Number(filteredList.length)
                    : (Number(currentPage) - 1) * Number(perPage) + Number(perPage)
                ) +
                ' of ' +
                Number(filteredList.length) +
                ' results.'
              }}
            </p>
          </div>
          <div class="w-full bg-miby-searchtags-blue p-5">
            <div class="flex flex-wrap justify-between items-center">
              <div class="flex flex-wrap gap-5 items-center">
                <!-- 表示件数 -->
                <div class="text-miby-black text-sm font-medium flex items-center">
                  <span>
                    {{ $t('displayTotal') + '：' }}
                  </span>
                  <select
                    v-model="perPage"
                    class="cursor-pointer bg-white border text-sm border-gray-300 rounded text-miby-black block"
                    @change="selectPerPage">
                    <option value="20" selected>20</option>
                    <option value="40">40</option>
                    <option value="60">60</option>
                    <option value="80">80</option>
                    <option value="100">100</option>
                    <option value="150">150</option>
                    <option value="200">200</option>
                  </select>
                </div>
                <!-- DL回数統計対象期間 -->
                <div class="text-miby-black text-sm font-medium flex items-center">
                  <span>
                    {{ $t('displayDLTargetPeriod') + '：' }}
                  </span>
                  <select
                    v-model="span"
                    class="cursor-pointer bg-white border text-sm border-gray-300 rounded text-miby-black block">
                    <option v-for="date in spanList" :key="date" :value="date">
                      {{ date }}
                    </option>
                  </select>
                </div>
              </div>
            </div>
          </div>
          <!-- フィルター -->
          <div class="flex flex-wrap">
            <div class="bg-miby-searchtags-blue filter-area">
              <div class="bg-miby-light-blue w-full flex text-white text-center py-0.5 px-8 font-medium">
                {{ $t('filter') }}
              </div>
              <ul v-for="searchType in filterList" :key="searchType.id" class="pt-0.5 pl-2 text-sm font-medium">
                <li>
                  {{ $t(searchType.i18n) }}
                </li>
                <!-- テキストボックス -->
                <ul v-if="searchType.type == 'text'" class="text-14px font-medium pb-2">
                  <div class="text-center">
                    <input
                      v-model="searchType.data"
                      type="text"
                      class="rounded h-8 w-11/12 text-black border border-gray-50"
                      @change="filtering(filterList)" />
                  </div>
                </ul>
                <!-- チェックボックス -->
                <ul v-if="searchType.type == 'checkbox'" class="pl-4 text-14px font-medium pb-2">
                  <li v-for="item in searchType.data" :key="item.id">
                    <label>
                      <input
                        v-model="item.value"
                        type="checkbox"
                        class="link-color"
                        :checked="item.value"
                        :value="true"
                        @change="filtering(filterList)" />
                      <span class="ml-1">{{ $t(item.comment) }}</span>
                    </label>
                  </li>
                </ul>
                <!-- 日付範囲指定 -->
                <ul v-if="searchType.type == 'date'" class="text-xs font-medium pb-2 mx-auto w-11/12">
                  <li>
                    <VueDatePicker
                      v-model="searchType.data"
                      format="yyyy-MM-dd"
                      model-type="yyyy-MM-dd"
                      :enable-time-picker="false"
                      range
                      @closed="filtering(filterList)"
                      @cleared="filtering(filterList)" />
                  </li>
                </ul>
              </ul>
              <div class="flex justify-center">
                <button
                  class="min-[1022px]:block h-5 min-[1022px]:h-auto min-[1022px]:border min-[1022px]:py-1 pl-2 pr-2.5 rounded text-14px text-white font-medium bg-link-color"
                  @click="clear">
                  {{ $t('clear') }}
                </button>
              </div>
            </div>

            <!-- ファイルリスト -->
            <div class="p-5 bg-miby-bg-gray result-area">
              <div class="flex flex-wrap justify-end items-center mb-7">
                <div class="mr-auto">
                  <NuxtLink class="font-bold" to="" event="" @click="throughDblClick">
                    <a class="pl-1.5 md:pl-0">
                      <span
                        class="underline text-sm icons icon-arrow-l text-miby-link-blue font-medium pr-1 cursor-pointer">
                        {{ $t('returnToItemDetails') }}
                      </span>
                    </a>
                  </NuxtLink>
                </div>
                <!-- 全件ダウンロード -->
                <div class="ml-auto">
                  <a
                    v-if="filteredList.length"
                    class="pl-1.5 md:pl-0 icons icon-download after cursor-pointer"
                    @click="downloadFilesAll">
                    <span class="underline text-sm text-miby-link-blue font-medium pr-1">
                      {{ $t('filesDownloadAll') }}
                    </span>
                  </a>
                </div>
              </div>
              <div>
                <div class="w-full overflow-x-auto">
                  <table class="search-lists w-full border-collapse border border-slate-500 table-fixed min-w-[960px]">
                    <thead>
                      <tr>
                        <th class="w-12 !py-2">
                          {{ $t('selection') }}
                          <input
                            v-model="isAllCheck"
                            type="checkbox"
                            :checked="isAllCheck"
                            @click="clickAllCheckbox()" />
                        </th>
                        <th class="w-3/12">
                          {{ $t('fileName') }}
                        </th>
                        <th class="w-[15%]">
                          {{ $t('fileDetail') }}
                        </th>
                        <th class="w-[10%]">
                          {{ $t('action') }}
                        </th>
                        <th class="w-3/12">
                          {{ $t('storageURL') }}
                        </th>
                        <th class="w-3/12">{{ $t('comment') }}</th>
                      </tr>
                    </thead>
                    <tbody v-if="filteredList.length && renderFlag">
                      <TableStyle
                        v-for="file in divideFileList[Number(currentPage) - 1]"
                        :key="file"
                        :file="file"
                        :span="span === 'total' ? '' : span"
                        :checked="selectedFiles.includes(file['@id'])"
                        @click-checkbox="clickCheckbox"
                        @error="setError" />
                    </tbody>
                  </table>
                </div>
              </div>
              <div class="flex justify-center mt-4 mb-4 gap-8">
                <!-- 選択ダウンロード -->
                <button
                  v-if="filteredList.length"
                  class="flex gap-1 text-white px-4 py-2 rounded button-center"
                  :class="[selectedFiles.length == 0 ? 'bg-miby-dark-gray' : 'bg-miby-link-blue']"
                  :disabled="selectedFiles.length == 0"
                  @click="downloadFilesSelected(selectedFiles)">
                  <img :src="`${appConf.amsImage ?? '/img'}/icon/icon_dl-rank.svg`" alt="Download" />
                  {{ $t('download') }} ({{ selectedFiles.length }} {{ $t('items') }})
                </button>
              </div>
              <div class="max-w-[300px] mx-auto mt-3.5 mb-16">
                <Pagination
                  v-if="filteredList.length && renderFlag"
                  :total="Number(filteredList.length)"
                  :currentPage="Number(currentPage)"
                  :displayPerPage="Number(perPage)"
                  @click-page="setPage" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
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

import FilterColumn from '~/assets/data/filesFilter.json';
import Alert from '~/components/common/Alert.vue';
import Pagination from '~/components/common/Pagination.vue';
import SearchForm from '~/components/common/SearchForm.vue';
import TableStyle from '~/components/files/TableStyle.vue';

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const appConf = useAppConfig();
const query = useRoute().query;
const renderFlag = ref(true);
const currentPage = ref('1');
const perPage = ref('20');
const itemTitle = ref('undefined');
const fileList = ref([]);
const filteredList = ref([]);
const span = ref('total');
const spanList = ref<string[]>([]);
const selectedFiles = ref<string[]>([]);
const visibleAlert = ref(false);
const alertType = ref('info');
const alertMessage = ref('');
const alertCode = ref(0);
let divideFileList: any[] = [];
let createdDate = '';
let isAllCheck = false;
let filterColumnList = JSON.parse(JSON.stringify(FilterColumn));
const filterList = ref<any[]>([]);
let url = '';

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * アイテム詳細取得API
 * @param number アイテムID
 */
async function getFiles(number: string) {
  let statusCode = 0;
  await $fetch(appConf.wekoApi + '/records/' + number, {
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
        const itemInfo = Object.prototype.hasOwnProperty.call(response._data, 'rocrate')
          ? getContentById(response._data.rocrate, './')
          : {};
        // タイトル取得
        if (Object.prototype.hasOwnProperty.call(itemInfo, appConf.roCrate.root.title)) {
          itemTitle.value = itemInfo[appConf.roCrate.root.title][0];
        }
        // DL数用作成日時取得
        if (Object.prototype.hasOwnProperty.call(itemInfo, appConf.roCrate.root.createDate)) {
          createdDate = itemInfo[appConf.roCrate.root.createDate][0];
        }
        // ファイルリスト作成
        for (const element of itemInfo.mainEntity) {
          const value = getContentById(response._data.rocrate, element['@id']);
          // NOTE: ロール制御が出来ないので下記のアクセス種別のファイルのみ表示している
          if (value.accessMode !== 'open_no') {
            // @ts-ignore
            fileList.value.push(value);
          }
        }
        filteredList.value = fileList.value;

        for (const column of filterColumnList) {
          filterList.value.push(JSON.parse(JSON.stringify(column)));
        }
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
        alertMessage.value = 'message.error.getItemDetail';
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
}

/**
 * 一括ファイルダウンロード
 */
function downloadFilesAll() {
  let statusCode = 0;

  if (filteredList.value.length === fileList.value.length) {
    $fetch(appConf.wekoApi + '/records/' + String(query.number) + '/files/all', {
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
          const a = document.createElement('a');
          a.href = window.URL.createObjectURL(new Blob([response._data]));
          a.setAttribute('download', itemTitle.value + '_files.zip');
          a.click();
          a.remove();
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
          alertMessage.value = 'message.error.downloadAll';
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
  } else {
    const filesList: any[] = [];
    filteredList.value.forEach((obj) => {
      filesList.push(obj['@id']);
    });
    downloadFilesSelected(filesList);
  }
}

/**
 * 選択ファイルダウンロード
 * @param filesList ダウンロードするファイル名リスト
 */
function downloadFilesSelected(filesList: string[]) {
  let statusCode = 0;
  $fetch(appConf.wekoApi + '/records/' + String(query.number) + '/files/selected', {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'POST',
    credentials: 'omit',
    headers: {
      'Cache-Control': 'no-store',
      Pragma: 'no-cache',
      'Accept-Language': localStorage.getItem('locale') ?? 'ja',
      Authorization: localStorage.getItem('token:type') + ' ' + localStorage.getItem('token:access')
    },
    body: {
      filenames: filesList
    },
    onResponse({ response }) {
      if (response.status === 200) {
        const a = document.createElement('a');
        a.href = window.URL.createObjectURL(new Blob([response._data]));
        a.setAttribute('download', itemTitle.value + '_files.zip');
        a.click();
        a.remove();
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
        alertMessage.value = 'message.error.downloadSelected';
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
}

/**
 * ファイルリストを表示用に整形
 * @param fileList 表示対象ファイルリスト
 */
function divideList(fileList: any[]) {
  if (fileList.length <= 0) {
    return;
  }

  divideFileList = [];
  let loopCount = Math.floor(fileList.length / Number(perPage.value));
  if (fileList.length % Number(perPage.value)) {
    loopCount++;
  }

  for (let i = 0; i < loopCount; i++) {
    divideFileList.push(fileList.slice(i * Number(perPage.value), (i + 1) * Number(perPage.value)));
  }
}

/**
 * DL数を確認できる期間を設定
 */
function setSpanList() {
  spanList.value.push('total');

  const now = new Date(Date.now());
  let year = now.getFullYear();
  let month = now.getMonth() + 2; // 計算上1月多く足している

  if (createdDate) {
    // 作成日が設定されてる場合、作成日からの期間を設定
    const cDate = new Date(Date.parse(createdDate));
    const createdYear = cDate.getFullYear();
    const createdMonth = cDate.getMonth() + 1;

    if (year - createdYear > 0 || (year - createdYear === 0 && month - createdMonth >= 0)) {
      for (let i = 0; year !== createdYear || month !== createdMonth; i++) {
        month = month - 1;
        if (month < 1) {
          year = year - 1;
          month = 12;
        }
        spanList.value.push(year + '-' + ('00' + month).slice(-2));
      }
    }
  } else {
    // 作成日が設定されていない場合、現在から1年前までの期間を設定
    for (let i = 0; i < 12; i++) {
      month = month - 1;
      if (month < 1) {
        year = year - 1;
        month = 12;
      }
      spanList.value.push(year + '-' + ('00' + month).slice(-2));
    }
  }
}

/**
 * 再レンダリング用イベント
 * @param clearSelectedFiles ダウンロードするファイルリストをリセットするか
 */
function renderResult(clearSelectedFiles = true) {
  renderFlag.value = false;
  if (clearSelectedFiles) {
    isAllCheck = false;
    selectedFiles.value = [];
  }
  nextTick(() => {
    renderFlag.value = true;
  });
}

/**
 * 表示件数選択時イベント
 */
function selectPerPage() {
  currentPage.value = '1';
  divideList(filteredList.value);
  renderResult();
}

/**
 * 選択ファイルダウンロードリスト作成
 * @param name ファイル名
 * @param isCheck チェック状態
 */
function clickCheckbox(name: string, isCheck: boolean) {
  if (isCheck) {
    selectedFiles.value.push(name);
  } else {
    const files = selectedFiles.value.filter((item: string) => {
      return item !== name;
    });
    selectedFiles.value = files;
  }
  changeAllCheckBox();
}

/**
 * 現在のページに表示されているファイルのチェックを全選択／全解除する
 */
function clickAllCheckbox() {
  if (isAllCheck) {
    isAllCheck = false;
    selectedFiles.value = selectedFiles.value.filter((file) => {
      return !divideFileList[Number(currentPage.value) - 1].some((divide: any) => divide['@id'] === file);
    });
  } else {
    isAllCheck = true;
    for (const file of divideFileList[Number(currentPage.value) - 1]) {
      const fileUrl = setFileInfo(file[appConf.roCrate.root.file.url]);
      // 格納場所がweko外部のファイルは除く
      if (fileUrl.startsWith(useAppConfig().wekoOrigin)) {
        if (!selectedFiles.value.includes(file['@id'])) {
          selectedFiles.value.push(file['@id']);
        }
      }
    }
  }
  setPage(currentPage.value);
}

/**
 * 手動で現在のページに表示されているファイルのチェックをすべて入れたら全選択のチェックをつける
 * そうでなかったらチェックを外す
 */
function changeAllCheckBox() {
  const currentDivideFiles = divideFileList[Number(currentPage.value) - 1];
  const divideLength = currentDivideFiles.length;
  isAllCheck = false;
  if (selectedFiles.value.length >= divideLength) {
    let count = 0;
    for (const file of currentDivideFiles) {
      const fileUrl = setFileInfo(file[appConf.roCrate.root.file.url])
      // 格納場所がweko外部のファイルは除く
      if (fileUrl.startsWith(useAppConfig().wekoOrigin)) {
        if (selectedFiles.value.includes(file['@id'])) {
          count++;
          if (count === divideLength) {
            isAllCheck = true;
            break;
          }
        }
      }
    }
  }
}

/**
 * ページネーション選択時イベント
 * @param value 表示ページ
 */
function setPage(value: string) {
  currentPage.value = value;
  renderResult(false);
  changeAllCheckBox();
}

/**
 * エラー発生時イベント
 * @param status ステータスコード
 * @param message エラーメッセージ
 */
function setError(status = 0, message: string) {
  alertMessage.value = message;
  alertCode.value = status;
  alertType.value = 'error';
  visibleAlert.value = true;
}

/**
 * フィルタリング実行
 * @param value フィルタリング条件
 */
function filtering(value: any) {
  let isAll = true;
  const filterCondition: any = {};

  // フィルタリング条件の整理
  for (const column of value) {
    if (column.type === 'text') {
      if (column.data) {
        Object.assign(filterCondition, { [column.roCrateKey]: { type: 'text', data: column.data } });
        isAll = false;
      }
    } else if (column.type === 'date') {
      if (column.data) {
        Object.assign(filterCondition, { [column.roCrateKey]: { type: 'date', data: column.data } });
        isAll = false;
      }
    } else if (column.type === 'checkbox') {
      const valueList = [];
      for (const item of column.data) {
        if (item.value) {
          valueList.push(item.roCrateValue);
          isAll = false;
        }
      }

      if (!isAll) {
        Object.assign(filterCondition, { [column.roCrateKey]: { type: 'checkbox', data: valueList } });
      }
    }
  }

  if (isAll) {
    filteredList.value = fileList.value;
  } else {
    filteredList.value = fileList.value;

    for (const key of Object.keys(filterCondition)) {
      if (filteredList.value.length < 1) {
        break;
      }

      if (filterCondition[key].type === 'text') {
        // 検索キーワードを空白区切りにすることによりOR検索
        const separatorString = /\s+/;
        const arrayStrig = filterCondition[key].data.split(separatorString);
        // 部分一致検索
        const extraction = filteredList.value.filter((item: any) => {
          for (const keyword of arrayStrig) {
            if (keyword && item[key].includes(keyword)) {
              return item[key].includes(keyword);
            }
          }
          return false;
        });
        filteredList.value = extraction;
      } else if (filterCondition[key].type === 'date') {
        const from = new Date(Date.parse(filterCondition[key].data[0]));
        const to = new Date(Date.parse(filterCondition[key].data[1]));
        let extraction;
        if (filterCondition[key].data[1]) {
          extraction = filteredList.value.filter((item: any) => {
            return from <= new Date(Date.parse(item.dateCreated)) && to >= new Date(Date.parse(item.dateCreated));
          });
        } else {
          extraction = filteredList.value.filter((item: any) => {
            return from <= new Date(Date.parse(item.dateCreated));
          });
        }
        filteredList.value = extraction;
      } else if (filterCondition[key].type === 'checkbox' && filterCondition[key].data.length > 0) {
        const extraction = filteredList.value.filter((item: any) => {
          return filterCondition[key].data.includes(item[key]);
        });
        filteredList.value = extraction;
      }
    }
  }
  divideList(filteredList.value);
  currentPage.value = '1';
  renderResult();
}

/**
 * フィルタリング条件の初期化
 */
function clear() {
  filterColumnList = JSON.parse(JSON.stringify(FilterColumn));
  filterList.value = [];

  for (const column of filterColumnList) {
    filterList.value.push(JSON.parse(JSON.stringify(column)));
  }

  filtering(filterList.value);
}

/** ファイル一覧画面からアイテム詳細画面へ戻るためのURLを生成 */
function getURL() {
  const itemInfoUrl = sessionStorage.getItem('url')?.split('/');
  if (itemInfoUrl && itemInfoUrl[3] === 'search') {
    url = `${appConf.amsPath ?? ''}/detail?sess=search&number=${query.number}`;
  } else {
    url = `${appConf.amsPath ?? ''}/detail?sess=top&number=${query.number}`;
  }
}

/**
 * ダブルクリックを制御する
 */
function throughDblClick() {
  if (location.pathname + location.search !== url) {
    navigateTo(url);
  }
}

/**
 * マッピング済みのファイル情報を取得する
 * マッピングされていない場合は空文字を返す
 * @param info ファイル情報（格納場所）
 * @returns ファイル情報
 */
 function setFileInfo(info: any) {
  const returnInfo = Array.isArray(info) ? info[0] : info;
  return returnInfo || '';
}

/* ///////////////////////////////////
// main
/////////////////////////////////// */

try {
  await getFiles(String(query.number));
  divideList(filteredList.value);
  setSpanList();
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
  getURL();
  refreshToken();
});

onUpdated(() => {
  refreshToken();
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
