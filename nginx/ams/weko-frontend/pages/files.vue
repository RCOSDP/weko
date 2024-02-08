<template>
  <div>
    <!-- 検索フォーム -->
    <SearchForm :sessCondFlag="false" />
    <main class="max-w-[1024px] mx-auto px-2.5">
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
              <!-- フィルター -->
              <div class="flex gap-2.5">
                <button class="btn-modal block cursor-pointer" data-target="FilterFileList" @click="openFilter">
                  <img src="/img/btn/btn-filter.svg" alt="Filter" />
                </button>
              </div>
            </div>
          </div>
          <!-- ファイルリスト -->
          <div class="p-5 bg-miby-bg-gray">
            <div class="flex flex-wrap justify-end items-center mb-10">
              <!-- 一括ダウンロード -->
              <a
                v-if="filteredList.length"
                class="pl-1.5 md:pl-0 icons icon-download after cursor-pointer"
                @click="downloadFilesAll">
                <span class="underline text-sm text-miby-link-blue font-medium pr-1">
                  {{ $t('filesDownloadAll') }}
                </span>
              </a>
            </div>
            <div>
              <div class="w-full overflow-x-auto">
                <table class="search-lists w-full border-collapse border border-slate-500 table-fixed min-w-[960px]">
                  <thead>
                    <tr>
                      <th class="w-16">
                        {{ $t('selection') }}
                      </th>
                      <th class="w-3/12">
                        {{ $t('fileName') }}
                      </th>
                      <th class="">
                        {{ $t('fileDetail') }}
                      </th>
                      <th class="">
                        {{ $t('action') }}
                      </th>
                      <th class="w-3/12">
                        {{ $t('storageURL') }}
                      </th>
                    </tr>
                  </thead>
                  <tbody v-if="filteredList.length && renderFlag">
                    <TableStyle
                      v-for="file in divideFileList[Number(currentPage) - 1]"
                      :key="file"
                      :file="file"
                      :span="span === 'total' ? '' : span"
                      @click-checkbox="clickCkeckbox"
                      @error="setError" />
                  </tbody>
                </table>
              </div>
            </div>
            <div class="flex justify-center mt-4 mb-4">
              <!-- 選択ダウンロード -->
              <button
                v-if="filteredList.length"
                class="flex gap-1 text-white px-4 py-2 rounded"
                :class="[selectedFiles.length == 0 ? 'bg-miby-dark-gray' : 'bg-miby-link-blue']"
                :disabled="selectedFiles.length == 0"
                @click="downloadFilesSelected(selectedFiles)">
                <img src="/img/icon/icon_dl-rank.svg" alt="Download" />
                {{ $t('download') }}
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
    </main>
    <!-- フィルター -->
    <Filter ref="filter" class="z-50" @filtering="filtering" />
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
import Pagination from '~/components/common/Pagination.vue';
import SearchForm from '~/components/common/SearchForm.vue';
import TableStyle from '~/components/files/TableStyle.vue';
import Filter from '~/components/files/modal/Filter.vue';

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
const filter = ref();
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
 */
function renderResult() {
  renderFlag.value = false;
  selectedFiles.value = [];
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
function clickCkeckbox(name: string, isCheck: boolean) {
  if (isCheck) {
    selectedFiles.value.push(name);
  } else {
    const files = selectedFiles.value.filter((item: string) => {
      return item !== name;
    });
    selectedFiles.value = files;
  }
}

/**
 * ページネーション選択時イベント
 * @param value 表示ページ
 */
function setPage(value: string) {
  currentPage.value = value;
  renderResult();
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
 * フィルターボタン押下時イベント
 */
function openFilter() {
  filter.value.openModal();
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
            if (item[key].includes(keyword)) {
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
            return from <= new Date(Date.parse(item.dateCreated[0])) && to >= new Date(Date.parse(item.dateCreated[0]));
          });
        } else {
          extraction = filteredList.value.filter((item: any) => {
            return from <= new Date(Date.parse(item.dateCreated[0]));
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
