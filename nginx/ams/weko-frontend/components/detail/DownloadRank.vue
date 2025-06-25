<template>
  <div class="bg-miby-bg-gray py-7 px-3.5 w-full">
    <a v-if="isMessage" class="ranking-text font-medium text-sm w-full flex justify-center">
      {{ $t('message.noFileRanking') }}
    </a>
    <ul class="w-full">
      <li
        v-for="(file, index) in topThree"
        :key="index"
        class="flex items-center mb-1.5 icons icon-download after lg:justify-between cursor-pointer"
        @click="download(file.name + '.' + file.extension)">
        <p v-if="index == 0" class="ranking-number bg-miby-tag-yellow">
          {{ index + 1 }}
        </p>
        <p v-else-if="index == 1" class="ranking-number bg-miby-tag-gray">
          {{ index + 1 }}
        </p>
        <p v-else-if="index == 2" class="ranking-number bg-miby-tag-orange">
          {{ index + 1 }}
        </p>
        <div class="ranking-text font-medium tooltip" :data-tip="file.name + '.' + file.extension">
          <button class="ranking-text flex items-center w-10/12">
            <span class="inline-block text-clamp">{{ file.name }}</span>
            <span class="inline-block mr-4 lg:mr-0">{{ '.' + file.extension }}</span>
          </button>
        </div>
      </li>
      <li
        v-for="(file, index) in other"
        :key="index"
        class="flex items-center mb-1.5 icons icon-download after lg:justify-between cursor-pointer"
        @click="download(file.name + '.' + file.extension)">
        <p class="ranking-number bg-miby-border-gray">{{ index + 4 }}</p>
        <div class="ranking-text font-medium tooltip" :data-tip="file.name + '.' + file.extension">
          <button class="ranking-text flex items-center w-10/12">
            <span class="inline-block text-clamp">{{ file.name }}</span>
            <span class="inline-block mr-4 lg:mr-0">{{ '.' + file.extension }}</span>
          </button>
        </div>
      </li>
    </ul>
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
// emits
/////////////////////////////////// */

const emits = defineEmits(['error']);

/* ///////////////////////////////////
// interface
/////////////////////////////////// */

interface IFileInfo {
  name: String;
  extension: String;
}

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const appConfig = useAppConfig();
const topThree = ref<IFileInfo[]>([]);
const other = ref<IFileInfo[]>([]);
const isMessage = ref(false);

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * ファイルダウンロードランキングの取得
 */
async function getRanking() {
  let statusCode = 0;
  await $fetch(appConfig.wekoApi + '/ranking/' + props.currentNumber + '/files', {
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
      display_number: useRuntimeConfig().public.dlRanking.display ?? 5
    },
    onResponse({ response }) {
      if (response.status === 200) {
        let counter = 1;
        const files = response._data.ranking;
        for (const file of files) {
          const firstFileName: any = file.filename.split('.')[0];
          const fileExtension: any = file.filename.split('.')[1];

          if (counter <= 3) {
            topThree.value.push({ name: firstFileName, extension: fileExtension });
          } else {
            other.value.push({ name: firstFileName, extension: fileExtension });
          }
          counter = counter + 1;
        }
      }
    },
    onResponseError({ response }) {
      statusCode = response.status;
      if (statusCode !== 404) {
        // emits('error', response.status, 'message.error.getDownloadRanking');
      }
    }
  }).catch(() => {
    if (statusCode === 0) {
      // emits('error', 0, 'message.error.fetch');
    }
  });
}

/**
 * ファイルダウンロード
 * @param filename ファイル名
 */
function download(filename: string) {
  let statusCode = 0;
  $fetch(appConfig.wekoApi + '/records/' + props.currentNumber + '/files/' + filename, {
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
      mode: 'download'
    },
    onResponse({ response }) {
      if (response.status === 200) {
        const a = document.createElement('a');
        a.href = window.URL.createObjectURL(new Blob([response._data]));
        a.setAttribute('download', filename);
        a.click();
        a.remove();
      }
    },
    onResponseError({ response }) {
      statusCode = response.status;
      emits('error', response.status, 'message.error.download');
    }
  }).catch(() => {
    if (statusCode === 0) {
      emits('error', 0, 'message.error.fetch');
    }
  });
}

/* ///////////////////////////////////
// main
/////////////////////////////////// */

try {
  await getRanking();
  isMessage.value = topThree.value.length === 0;
} catch (error) {
  // console.log(error);
}
</script>
