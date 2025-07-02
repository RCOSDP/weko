<template>
  <div class="bg-miby-bg-gray py-7 text-center">
    <!-- 閲覧数 -->
    <p class="text-2xl font-medium mb-7">{{ total }}</p>
    <!-- 期間 -->
    <select
      v-model="span"
      class="max-w-[130px] mb-3.5 mx-auto border rounded border-miby-black text-left"
      @change="changeSpan">
      <option v-for="date in spanList" :key="date" :value="date">
        {{ date }}
      </option>
    </select>
    <!-- 閲覧数詳細 -->
    <span
      class="hover:cursor-pointer block text-miby-link-blue underline text-sm font-medium"
      @click="changeToggleState">
      See details
    </span>
    <div v-if="openDetail" class="divide-y-2 mt-2">
      <div v-for="(value, key) in regionStats" :key="key" class="mx-2">
        <div class="text-[#8A939F] flex justify-between">
          <span>{{ key }}</span>
          <span>{{ value }}</span>
        </div>
      </div>
      <div v-if="Object.keys(regionStats).length == 0" class="text-[#8A939F] flex justify-center">No viewing</div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import amsAlert from '~/assets/data/amsAlert.json';
/* ///////////////////////////////////
// props
/////////////////////////////////// */

const props = defineProps({
  // アイテムID
  currentNumber: {
    type: Number,
    default: 0
  },
  // アイテム作成日時
  createdDate: {
    type: String,
    default: ''
  }
});

/* ///////////////////////////////////
// emits
/////////////////////////////////// */

const emits = defineEmits(['error']);

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const total = ref(0);
const span = ref('total');
const spanList = ref<string[]>([]);
const regionStats = ref({});
const openDetail = ref(false);
const alertData = ref({
  msgid: '',
  msgstr: '',
  position: '',
  width: 'w-full',
  loglevel: 'info'
});

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * 選択された期間のアイテム閲覧数取得
 * @param span 期間
 */
function getItemStats(span: string) {
  let statusCode = 0;
  $fetch(useAppConfig().wekoApi + '/records/' + props.currentNumber + '/stats', {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'GET',
    credentials: 'omit',
    headers: {
      'Cache-Control': 'no-store',
      Pragma: 'no-cache',
      'Accept-Language': localStorage.getItem('locale') ?? 'ja',
      Authorization: localStorage.getItem('token:type') + ' ' + localStorage.getItem('token:access')
    },
    params: {
      date: span
    },
    onResponse({ response }) {
      if (response.status === 200) {
        total.value = response._data.total;
        regionStats.value = response._data.country;
      }
    },
    onResponseError({ response }) {
      statusCode = response.status;
      if (statusCode === 500) {
        alertData.value = amsAlert['VIEWS_NUMBER_MESSAGE_ERROR'];
      } else {
        alertData.value = amsAlert['VIEWS_NUMBER_MESSAGE_ERROR_GET_ITEM'];
      }
      emits('error', alertData.value.msgid, alertData.value.msgstr);
    }
  }).catch(() => {
    if (statusCode === 0) {
      alertData.value = amsAlert['VIEWS_NUMBER_MESSAGE_ERROR_FETCH'];
      emits('error', alertData.value.msgid, alertData.value.msgstr);
    }
  });
}

/**
 * 閲覧数を確認できる期間を設定
 */
function setSpanList() {
  spanList.value.push('total');

  const now = new Date(Date.now());
  let year = now.getFullYear();
  let month = now.getMonth() + 2; // 計算上1月多く足している

  if (props.createdDate) {
    // 作成日が設定されてる場合、作成日からの期間を設定
    const createdDate = new Date(Date.parse(props.createdDate));
    const createdYear = createdDate.getFullYear();
    const createdMonth = createdDate.getMonth() + 1;

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
 * 期間変更用イベント
 */
function changeSpan() {
  getItemStats(span.value === 'total' ? '' : span.value);
}

/**
 * 詳細表示用イベント
 */
function changeToggleState() {
  openDetail.value = !openDetail.value;
}

/* ///////////////////////////////////
// main
/////////////////////////////////// */

try {
  setSpanList();
  getItemStats('');
} catch (error) {
  // console.log(error);
}
</script>
