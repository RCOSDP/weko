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
                String((Number(currentPage) - 1) * Number(perPage) + 1) +
                ' - ' +
                String(
                  (Number(currentPage) - 1) * Number(perPage) + Number(perPage) > Number(fileList.length)
                    ? Number(fileList.length)
                    : (Number(currentPage) - 1) * Number(perPage) + Number(perPage)
                ) +
                ' of ' +
                fileList.length +
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
                  <select class="cursor-pointer bg-white border text-sm border-gray-300 rounded text-miby-black block">
                    <option value="all" selected>全期間</option>
                  </select>
                </div>
              </div>
              <div class="flex gap-2.5">
                <button class="btn-modal block cursor-pointer" data-target="FilterFileList">
                  <img src="/img/btn/btn-filter.svg" alt="Filter" />
                </button>
              </div>
            </div>
          </div>
          <!-- ファイルリスト -->
          <div class="p-5 bg-miby-bg-gray">
            <div class="flex flex-wrap justify-end items-center mb-10">
              <!-- 一括ダウンロード -->
              <a v-if="fileList.length" class="pl-1.5 md:pl-0 icons icon-download after" href="#">
                <span class="underline text-sm text-miby-link-blue font-medium pr-1">
                  {{ $t('filesDownloadAll') }}
                </span>
              </a>
            </div>
            <div v-if="fileList.length">
              <div class="w-full overflow-x-auto">
                <table class="search-lists w-[1274px] border-collapse border border-slate-500 table-auto">
                  <thead>
                    <tr>
                      <th class="max-w-[44px]">
                        {{ $t('selection') }}
                      </th>
                      <th class="max-w-[130px]">
                        {{ $t('fileName') }}
                      </th>
                      <th class="max-w-[86px]">
                        {{ $t('size') }}
                      </th>
                      <th class="max-w-[137px]">
                        {{ $t('DLRange') }}
                      </th>
                      <th class="max-w-[110px]">
                        {{ $t('license') }}
                      </th>
                      <th class="max-w-[134px]">
                        {{ $t('action') }}
                      </th>
                      <th class="max-w-[210px]">
                        {{ $t('storageURL') }}
                      </th>
                      <th class="max-w-[130px]">
                        {{ $t('DLNumber') }}
                      </th>
                    </tr>
                  </thead>
                  <tbody v-for="file in divideFileList[Number(currentPage) - 1]" :key="file">
                    <TableStyle :file="file" @error="setError" />
                  </tbody>
                </table>
              </div>
            </div>
            <div class="flex justify-center mt-2 mb-4">
              <!-- 選択ダウンロード -->
              <button v-if="fileList.length" class="flex gap-1 bg-miby-link-blue text-white px-4 py-2 rounded">
                <img src="/img/icon/icon_dl-rank.svg" alt="Download" />
                {{ $t('download') }}
              </button>
            </div>
            <div class="max-w-[300px] mx-auto mt-3.5 mb-16">
              <Pagination
                v-if="fileList.length && renderFlag"
                :total="Number(fileList.length)"
                :currentPage="Number(currentPage)"
                :displayPerPage="Number(perPage)"
                @click-page="setPage" />
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
const itemTitle = ref('');
const fileList = ref([]);
const visibleAlert = ref(false);
const alertType = ref('info');
const alertMessage = ref('');
const alertCode = ref(0);
let divideFileList: any[] = [];

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * アイテム詳細取得API
 * @param number アイテムID
 */
async function getFiles(number: string) {
  let statusCode = 0;
  alertCode.value = 0;
  await $fetch(appConf.wekoApi + '/records/' + number, {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'GET',
    onResponse({ response }) {
      if (response.status === 200) {
        const itemInfo = getContentById(response._data.rocrate, './');
        itemTitle.value = itemInfo[appConf.roCrate.info.title][0];
        for (const element of itemInfo.mainEntity) {
          // @ts-ignore
          fileList.value.push(getContentById(response._data.rocrate, element['@id']));
        }
      }
    },
    onResponseError({ response }) {
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
      alertMessage.value = 'message.error.fetchError';
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
 * 再レンダリング用イベント
 */
function renderResult() {
  renderFlag.value = false;
  nextTick(() => {
    renderFlag.value = true;
  });
}

/**
 * 表示件数選択時イベント
 */
function selectPerPage() {
  currentPage.value = '1';
  divideList(fileList.value);
  renderResult();
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

/* ///////////////////////////////////
// main
/////////////////////////////////// */

try {
  await getFiles(String(query.number));
  divideList(fileList.value);
} catch (error) {
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
