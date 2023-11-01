<template>
  <div class="bg-miby-bg-gray py-10 text-center">
    <!-- 閲覧数 -->
    <p class="text-2xl font-medium mb-12">{{ total }}</p>
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
/* ///////////////////////////////////
// props
/////////////////////////////////// */

const props = defineProps({
  // アイテムID
  currentNumber: {
    type: Number,
    default: 0
  }
});

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const total = ref(0);
const span = ref('total');
const spanList = ref<string[]>([]);
const regionStats = ref({});
const openDetail = ref(false);

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * 選択された期間のアイテム閲覧数取得
 * @param span 期間
 */
async function getItemStats(span: string) {
  await $fetch(useAppConfig().wekoApi + '/records/' + props.currentNumber + '/stats', {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'GET',
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
    }
  });
}

/**
 * 閲覧数を確認できる期間を設定（1年前まで）
 */
function setSpanList() {
  spanList.value.push('total');

  const now = new Date(Date.now());
  let year = now.getFullYear();
  let month = now.getMonth() + 2;

  for (let i = 0; i < 12; i++) {
    month = month - 1;
    if (month < 1) {
      year = year - 1;
      month = 12;
    }
    spanList.value.push(year + '-' + ('00' + month).slice(-2));
  }
}

/**
 * 期間変更用イベント
 */
async function changeSpan() {
  await getItemStats(span.value === 'total' ? '' : span.value);
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
  await getItemStats('');
} catch (error) {
  // console.log(error);
}
</script>
