<template>
  <div>
    <!-- 検索フォーム -->
    <SearchForm :sessCondFlag="false" />
    <!-- インデックス階層 -->
    <main class="mx-auto max-w-[97vw]">
      <div class="w-full">
        <div v-for="index in indexes" :key="index.id" class="w-full">
          <span v-if="index.id != indexId" class="font-medium cursor-pointer text-14px" @click="clickParent(index.id)">
            {{ index.name }}
          </span>
          <span v-else class="font-medium cursor-pointer text-14px" @click="clickParent(index.id)">
            {{ index.name }}
          </span>
          <a v-if="index.id != indexId" class="ml-1 mr-1">/</a>
        </div>
      </div>
      <div class="flex flex-wrap w-full">
        <!-- メインコンテンツ -->
        <div class="detail__wrapper h-full">
          <div class="bg-miby-light-blue py-3 pl-5">
            <p class="icons icon-item text-white font-bold">
              {{ $t('item') }}
            </p>
          </div>
          <div class="bg-miby-bg-gray text-center">
            <!-- 前/次 -->
            <Switcher
              :sess="beforePage"
              :prev-num="prevNum"
              :next-num="nextNum"
              @click-prev="changeDetail"
              @click-next="changeDetail" />
            <!-- アイテム情報 -->
            <ItemInfo v-if="renderFlag" :item="itemDetail" :item-id="currentNumber" :oauth-error="oauthError" />
            <!-- アイテム内容 -->
            <div v-if="showPopup" class="popup">
              <p>{{ $t('message.popup.loginRequiredMessage') }}</p>
              <p>{{ $t('message.popup.transitionToLogin', { time: transitionSecond }) }}</p>
              <p>　</p>
              <p
                >{{ $t('message.popup.loginScreen') }} <a :href="loginPage" class="link">{{ loginPage }}</a></p
              >
            </div>
            <!-- アイテム内容 -->
            <ItemContent v-if="renderFlag" :item="itemDetail" />
            <!-- 前/次 -->
            <div v-if="!oauthError" class="pt-2.5 pb-28">
              <Switcher
                :sess="beforePage"
                :prev-num="prevNum"
                :next-num="nextNum"
                @click-prev="changeDetail"
                @click-next="changeDetail" />
            </div>
            <div v-else class="pt-2.5 pb-28"></div>
            <!-- 最上部に戻る -->
            <button id="page-top" class="hidden lg:block w-10 h-10 absolute right-5 bottom-[60px]" @click="scrollToTop">
              <img src="/img/btn/btn-gototop.svg" alt="Top" />
            </button>
          </div>
        </div>
        <!-- サブコンテンツ -->
        <div class="w-full md:ml-[5px] max-w-[24.5%]">
          <!-- 閲覧数 -->
          <div class="bg-miby-light-blue py-3 pl-5 flex items-center">
            <p class="icons icon-statistics text-white font-bold">
              {{ $t('detailViews') }}
            </p>
          </div>
          <ViewsNumber
            v-if="renderFlag && !oauthError"
            :current-number="currentNumber"
            :created-date="createdDate"
            @error="setError" />
          <!-- リクエストメール（未ログイン＆フィードバックアドレス有） -->
          <div v-if="!isLogin && checkMailAddress">
            <div class="bg-miby-light-blue py-3 pl-5">
              <p class="icons icon-mail text-white font-bold">
                {{ $t('requestMail') }}
              </p>
            </div>
            <div class="bg-miby-bg-gray py-7 text-center flex justify-center items-center">
              <button
                class="flex gap-1 text-white px-4 py-2 rounded"
                :class="[false ? 'bg-miby-dark-gray' : 'bg-sky-800']"
                :disabled="false"
                @click="openRequestMailModal">
                <img src="/img/icon/icon_mail-send.svg" alt="Send" />
                {{ $t('request') }}
              </button>
            </div>
          </div>
          <!-- GakuNinRDM（ログイン済み＆プロジェクトID有） -->
          <div v-else-if="isLogin && checkProjectId">
            <div class="bg-miby-light-blue py-3 pl-5">
              <p class="text-white font-bold">
                {{ $t('GakuNinRDM') }}
              </p>
            </div>
            <div class="bg-miby-bg-gray py-7 text-center flex justify-center items-center">
              <button @click="openDataSet">
                <img src="/img/logo/gakunin_logo.svg" alt="Send" />
              </button>
            </div>
          </div>
          <!-- ダウンロードランキング -->
          <div class="bg-miby-light-blue py-3 pl-5">
            <p class="icons icon-dl-rank text-white font-bold">
              {{ $t('detailDLRank') }}
            </p>
          </div>
          <DownloadRank v-if="renderFlag" :current-number="currentNumber" @error="setError" />
          <!-- エクスポート -->
          <div class="bg-miby-light-blue py-3 pl-5">
            <p class="icons icon-export text-white font-bold">
              {{ $t('detailExport') }}
            </p>
          </div>
          <Export :currentNumber="currentNumber" />
        </div>
      </div>
      <!-- 最上部に戻る -->
      <button id="page-top" class="block lg:hidden w-10 h-10 z-40 fixed right-5 bottom-2.5" @click="scrollToTop">
        <img src="/img/btn/btn-gototop_sp.svg" alt="Return To Top" />
      </button>
    </main>
    <!-- Loading -->
    <dialog id="loading_modal" class="modal bg-black bg-opacity-50">
      <form class="modal-middle h-full">
        <div class="font-bold text-2xl text-white h-full flex justify-center items-center content-center">
          <span class="loading loading-bars loading-lg mr-4" />
          <span v-if="isLoading">Loading ...</span>
          <span v-else>{{ $t('message.sending') }}</span>
        </div>
      </form>
    </dialog>
    <!-- 著者情報 -->
    <CreaterInfo ref="creater" />
    <!-- リクエストメール -->
    <RequestMail
      v-if="renderFlag"
      ref="requestMail"
      class="z-50"
      :item-id="currentNumber"
      @click-send="openLoading(false)"
      @complete-send="checkSendingResponse" />
    <!-- アラート -->
    <Alert
      v-if="visibleAlert"
      :type="alertType"
      :message="alertMessage"
      :code="alertCode"
      :position="alertPosition"
      :width="alertWidth"
      @click-close="visibleAlert = !visibleAlert" />
  </div>
</template>

<script lang="ts" setup>
import Alert from '~/components/common/Alert.vue';
import SearchForm from '~/components/common/SearchForm.vue';
import CreaterInfo from '~/components/common/modal/CreaterInfo.vue';
import DownloadRank from '~/components/detail/DownloadRank.vue';
import Export from '~/components/detail/Export.vue';
import ItemContent from '~/components/detail/ItemContent.vue';
import ItemInfo from '~/components/detail/ItemInfo.vue';
import Switcher from '~/components/detail/Switcher.vue';
import ViewsNumber from '~/components/detail/ViewsNumber.vue';
import RequestMail from '~/components/detail/modal/RequestMail.vue';

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

const appConf = useAppConfig();
const query = useRoute().query;
const switcherFlag = ref(false);
const renderFlag = ref(true);
const conditions = {
  type: '',
  keyword: '',
  currentPage: '',
  perPage: '',
  sort: '',
  order: ''
};
let beforePage = '';
let itemTotal = 0;
let itemDetail = {};
let indexId = '0';
const indexes = ref<indexInfo[]>([]);
let searchResult: number[] = [];
let prevNumList: number[] = [];
let currentNumList: number[] = [];
let nextNumList: number[] = [];
let shift = '';
let currentNumber = 0;
let createdDate = '';
const prevNum = ref(0);
const nextNum = ref(0);
const creater = ref();
const requestMail = ref();
const visibleAlert = ref(false);
const alertType = ref('info');
const alertMessage = ref('');
const alertCode = ref(0);
const alertPosition = ref('');
const alertWidth = ref('');
const isLoading = ref(true);
const isLogin = ref(false);
const checkMailAddress = ref(false);
const checkProjectId = ref(false);
const showPopup = ref(false);
const transitionSecond = appConf.transitionTime / 1000;
const loginPage = window.location.origin + '/login?source=detail';
let oauthError = ref(false);

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * アイテム詳細取得
 * @param number アイテムID
 */
async function getDetail(number: string) {
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
        itemDetail = response._data;
        indexId = response._data.index ?? '';

        // @ts-ignore
        const obj = getContentById(itemDetail.rocrate, './');
        // 閲覧数用作成日時取得
        if (Object.prototype.hasOwnProperty.call(itemDetail, 'rocrate')) {
          if (Object.prototype.hasOwnProperty.call(obj, appConf.roCrate.root.createDate)) {
            createdDate = obj[appConf.roCrate.root.createDate][0];
          }
        }

        // ログイン状況を取得する
        isLogin.value = !!sessionStorage.getItem('login:state');

        // プロジェクトIDの登録があるかどうか確認する
        // TODO: RoCrateキーは暫定のため、整理後再度指定要
        checkProjectId.value = !!obj[appConf.roCrate.root.projectId]?.[0];

        // フィードバックメールアドレスがあるかどうか確認する
        // @ts-ignore
        checkMailAddress.value = !!itemDetail.metadata.hasRequestmailAddress;
      }
    },
    onResponseError({ response }) {
      alertCode.value = 0;
      statusCode = response.status;
      if (statusCode === 401 || statusCode === 403) {
        // 認証エラー
        oauthErrorRedirect();
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
      alertPosition.value = '';
      alertWidth.value = 'w-full';
      visibleAlert.value = true;
    }
  }).catch(() => {
    if (statusCode === 0) {
      // fetchエラー
      alertMessage.value = 'message.error.fetch';
      alertType.value = 'error';
      alertPosition.value = '';
      alertWidth.value = 'w-full';
      visibleAlert.value = true;
    }
  });
}

/**
 * アイテム検索
 * @param searchPage 取得対象ページ
 */
async function search(searchPage: string) {
  if (!Number(searchPage)) {
    return;
  }

  let statusCode = 0;
  const params = {
    q: conditions.keyword,
    search_type: conditions.type,
    page: searchPage,
    size: conditions.perPage,
    sort: conditions.order === 'asc' ? conditions.sort : '-' + conditions.sort
  };
  const urlSearchParam = new URLSearchParams(params);

  await $fetch(appConf.wekoApi + '/records?' + urlSearchParam, {
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
        if (itemTotal <= 0) {
          itemTotal = response._data.total_results;
        }

        const itemList = response._data.search_results;
        searchResult = [];
        itemList.forEach((item: Object) => {
          // @ts-ignore
          searchResult.push(Number(item.id));
        });
      }
    },
    onResponseError({ response }) {
      alertCode.value = 0;
      statusCode = response.status;
      switcherFlag.value = false;
      searchResult = [];
      if (oauthError.value || statusCode === 401 || statusCode === 403) {
        // 認証エラー
        oauthErrorRedirect();
      } else if (statusCode >= 500 && statusCode < 600) {
        // サーバーエラー
        alertMessage.value = 'message.error.server';
        alertCode.value = statusCode;
      } else {
        // リクエストエラー
        alertMessage.value = 'message.error.search';
        alertCode.value = statusCode;
      }
      alertType.value = 'error';
      alertPosition.value = '';
      alertWidth.value = 'w-full';
      visibleAlert.value = true;
    }
  }).catch(() => {
    if (statusCode === 0) {
      // fetchエラー
      alertMessage.value = 'message.error.fetch';
      alertType.value = 'error';
      alertPosition.value = '';
      alertWidth.value = 'w-full';
      visibleAlert.value = true;
    }
  });
}

/**
 * インデクス階層取得
 */
async function getParentIndex() {
  let statusCode = 0;
  await $fetch(appConf.wekoApi + '/tree/index/' + indexId + '/parent', {
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
      alertCode.value = 0;
      statusCode = response.status;
      if (oauthError.value || statusCode === 401 || statusCode === 403) {
        // 認証エラー
        oauthErrorRedirect();
      } else if (statusCode >= 500 && statusCode < 600) {
        // サーバーエラー
        alertMessage.value = 'message.error.server';
        alertCode.value = statusCode;
      } else {
        // リクエストエラー
        alertMessage.value = 'message.error.getIndex';
        alertCode.value = statusCode;
      }
      alertType.value = 'error';
      alertPosition.value = '';
      alertWidth.value = 'w-full';
      visibleAlert.value = true;
    }
  }).catch(() => {
    if (statusCode === 0) {
      // fetchエラー
      alertMessage.value = 'message.error.fetch';
      alertType.value = 'error';
      alertPosition.value = '';
      alertWidth.value = 'w-full';
      visibleAlert.value = true;
    }
  });
}

/**
 * 前/次のアイテム表示用IDリスト設定
 * @param type initial:初期表示時, shift-prev:IDリストを前にシフトする, shift-prev:IDリストを次にシフトする
 */
async function setNumList(type: string) {
  try {
    const prevPage = Number(conditions.currentPage) - 1;
    const nextPage = Number(conditions.currentPage) + 1;
    if (type === 'initial') {
      await search(conditions.currentPage);
      currentNumList = searchResult ?? [];
      if (prevPage >= 1) {
        await search(String(prevPage));
        prevNumList = searchResult ?? [];
      } else {
        prevNumList = [];
      }
      if (nextPage <= Math.ceil(itemTotal / Number(conditions.perPage))) {
        await search(String(nextPage));
        nextNumList = searchResult ?? [];
      } else {
        nextNumList = [];
      }
    } else if (type === 'shift-prev') {
      nextNumList = currentNumList;
      currentNumList = prevNumList;
      conditions.currentPage = String(prevPage);
      if (prevPage - 1 >= 1) {
        await search(String(prevPage - 1));
        prevNumList = searchResult ?? [];
      } else {
        prevNumList = [];
      }
    } else if (type === 'shift-next') {
      prevNumList = currentNumList;
      currentNumList = nextNumList;
      conditions.currentPage = String(nextPage);
      if (nextPage + 1 <= parseInt(String(itemTotal / Number(conditions.perPage)))) {
        await search(String(nextPage + 1));
        nextNumList = searchResult ?? [];
      } else {
        nextNumList = [];
      }
    }
  } catch (error) {
    currentNumList = [];
    prevNumList = [];
    nextNumList = [];
  }
}

/**
 * 前/次のアイテム表示用ID設定
 */
function setSwitchNum(): string {
  const i = currentNumList.indexOf(currentNumber);
  let result = '';

  if (i >= 0) {
    currentNumber = currentNumList[i];

    if (i - 1 < 0) {
      if (prevNumList.length <= 0) {
        prevNum.value = 0;
      } else {
        prevNum.value = prevNumList[prevNumList.length - 1];
        result = 'shift-prev';
      }
    } else {
      prevNum.value = currentNumList[i - 1];
    }

    if (i + 1 >= currentNumList.length) {
      if (nextNumList.length <= 0) {
        nextNum.value = 0;
      } else {
        nextNum.value = nextNumList[0];
        result = 'shift-next';
      }
    } else {
      nextNum.value = currentNumList[i + 1];
    }
  } else {
    prevNum.value = 0;
    nextNum.value = 0;
  }

  return result;
}

/**
 * 次アイテム/前アイテムを表示用イベント
 * @param value prev or next
 */
async function changeDetail(value: string) {
  if (!switcherFlag.value) {
    return;
  }

  if (value === 'prev') {
    if (prevNum.value === 0) {
      return;
    }

    try {
      openLoading(true);
      await getDetail(String(prevNum.value));
      // REVIEW: pushでクエリを置き換える場合、ブラウザーバック対応をする
      useRouter().replace({
        query: { sess: beforePage, number: prevNum.value }
      });
      if (shift === 'shift-prev') {
        await setNumList(shift);
      }
      currentNumber = prevNum.value;
      shift = setSwitchNum();
      await getParentIndex();
      // 再レンダリング
      renderFlag.value = false;
      nextTick(() => {
        renderFlag.value = true;
      });
    } finally {
      // setTimeout(() => {
      //   (document.getElementById('loading_modal') as HTMLDialogElement).close();
      //   scrollToTop();
      // }, 500);
      nextTick(() => {
        (document.getElementById('loading_modal') as HTMLDialogElement).close();
        scrollToTop();
      });
    }
  } else if (value === 'next') {
    if (nextNum.value === 0) {
      return;
    }

    try {
      openLoading(true);
      await getDetail(String(nextNum.value));
      // REVIEW: pushでクエリを置き換える場合、ブラウザーバック対応をする
      useRouter().replace({
        query: { sess: beforePage, number: nextNum.value }
      });
      if (shift === 'shift-next') {
        await setNumList(shift);
      }
      currentNumber = nextNum.value;
      shift = setSwitchNum();
      await getParentIndex();
      // 再レンダリング
      renderFlag.value = false;
      nextTick(() => {
        renderFlag.value = true;
      });
    } finally {
      // setTimeout(() => {
      //   (document.getElementById('loading_modal') as HTMLDialogElement).close();
      //   scrollToTop();
      // }, 500);
      nextTick(() => {
        (document.getElementById('loading_modal') as HTMLDialogElement).close();
        scrollToTop();
      });
    }
  }
}

/**
 * 検索条件をセッションから復元
 * @param sess top or search
 */
function setConditions(sess: string): boolean {
  if (sess === 'top') {
    conditions.type = '0';
    conditions.keyword = '';
    conditions.currentPage = '1';
    conditions.perPage = '20';
    conditions.sort = 'publish_date';
    conditions.order = 'desc';
  } else if (sess === 'search') {
    if (!sessionStorage.getItem('conditions')) {
      return false;
    }

    // @ts-ignore
    const json = JSON.parse(sessionStorage.getItem('conditions'));
    conditions.type = json.type ?? '0';
    conditions.keyword = json.keyword ?? '';
    conditions.currentPage = json.currentPage ?? '1';
    conditions.perPage = json.perPage ?? '20';
    conditions.sort = json.sort ?? 'wtl';
    conditions.order = json.order ?? 'asc';
  } else {
    return false;
  }

  return true;
}

/**
 * インデックス名押下時イベント
 * @param indexId インデクスID
 */
function clickParent(indexId: string) {
  if (sessionStorage.getItem('conditions')) {
    // @ts-ignore
    const sessConditions = JSON.parse(sessionStorage.getItem('conditions'));
    // 詳細検索条件が設定されている場合は削除
    if (Object.prototype.hasOwnProperty.call(sessConditions, 'detail')) {
      delete sessConditions.detail;
      delete sessConditions.detailData;
    }
    // 検索条件設定
    Object.assign(sessConditions, { keyword: indexId });
    sessionStorage.setItem('conditions', JSON.stringify(sessConditions));
  } else {
    sessionStorage.setItem('conditions', JSON.stringify({ type: '0', keyword: indexId }));
  }

  navigateTo('/search/' + indexId);
}

/**
 * 作成者情報モーダル表示(10/25現在未使用)
 */
// function openCreaterModal() {
//   creater.value.openModal();
// }

/**
 * リクエストモーダル表示
 */
function openRequestMailModal() {
  requestMail.value.getCaptcha();
  requestMail.value.openModal();
}

/**
 * 別ウィンドウでデータセットを開く
 */
function openDataSet() {
  // TODO: 下記urlにデータセットを開くアドレスを入れる
  // const url = '';
  // window.open(url, '_blank');
}

/**
 * loadingモーダル表示
 * @param type true:Loading / false:Sending
 */
function openLoading(type: boolean) {
  isLoading.value = type;
  (document.getElementById('loading_modal') as HTMLDialogElement).showModal();
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
  alertPosition.value = '';
  alertWidth.value = 'w-full';
  visibleAlert.value = true;
}

/**
 * 問い合わせ送信完了時イベント
 * @param val true:送信成功 / false:送信失敗
 */
function checkSendingResponse(val: boolean) {
  if (val) {
    alertType.value = 'success';
    alertMessage.value = 'message.sendingSuccess';
    alertPosition.value = 'toast-top pt-20';
    alertWidth.value = 'w-auto';
    // 入力内容初期化
    requestMail.value.initInput();
  } else {
    alertType.value = 'error';
    alertMessage.value = 'message.sendingFailed';
    alertCode.value = 0;
    alertPosition.value = 'toast-top pt-20';
    alertWidth.value = 'w-auto';
  }
  (document.getElementById('loading_modal') as HTMLDialogElement).close();
  visibleAlert.value = true;
}

/**
 * ページ最上部にスクロール
 */
function scrollToTop() {
  scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * 認証エラー時のリダイレクト処理
 */
function oauthErrorRedirect() {
  showPopup.value = true;
  alertMessage.value = 'message.popup.oauthError';
  oauthError.value = true;
  alertType.value = 'error';
  sessionStorage.removeItem('item-url');
  sessionStorage.setItem('item-url', window.location.pathname + window.location.search);
  setTimeout(() => {
    // 認証エラーの場合はログイン画面に遷移
     navigateTo({
       path: '/login',
       query: { source: 'detail' }
     });
  }, appConf.transitionTime);
}

/* ///////////////////////////////////
// main
/////////////////////////////////// */

try {
  beforePage = String(query.sess);
  currentNumber = Number(query.number);
  await getDetail(String(currentNumber) ?? '0');
  switcherFlag.value = setConditions(beforePage);
  if (switcherFlag.value) {
    await setNumList('initial');
    shift = setSwitchNum();
  }
  await getParentIndex();
} catch (error) {
  alertCode.value = 0;
  alertMessage.value = 'message.error.error';
  alertType.value = 'error';
  alertPosition.value = '';
  alertWidth.value = 'w-full';
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
