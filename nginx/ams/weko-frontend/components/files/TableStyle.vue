<template>
  <tr>
    <!-- チェックボックス -->
    <td>
      <input v-model="isCeck" type="checkbox" @change="emits('clickCheckbox', file['@id'], isCeck)" />
    </td>
    <!-- ファイル名 -->
    <td class="text-left break-words">
      {{ file['@id'] }}
    </td>
    <!-- 詳細情報 -->
    <td class="text-left">
      <!-- 公開日 -->
      <div class="flex pt-1 pb-1 text-sm items-center h-8">
        <span class="font-medium">{{ $t('releaseDate') }} :</span>
        <span class="ml-2">
          <span v-if="file.hasOwnProperty('accessMode') && file.hasOwnProperty('dateCreated')">
            {{ file['dateCreated'][0] }}
          </span>
          <span v-else>undefined</span>
        </span>
      </div>
      <!-- サイズ -->
      <div class="flex pt-1 pb-1 text-sm items-center h-8">
        <span class="font-medium">{{ $t('size') }} :</span>
        <span class="ml-2">
          <span v-if="file.hasOwnProperty(appConfig.roCrate.root.file.size)">
            {{ file[appConfig.roCrate.root.file.size][0] }}
          </span>
          <span v-else>undefined</span>
        </span>
      </div>
      <!-- DL回数 -->
      <div class="flex pt-1 pb-1 text-sm items-center h-8">
        <span class="font-medium">{{ $t('DLNumber') }} :</span>
        <span class="ml-2">
          <span v-if="file['accessMode'] == 'open_access' || file['accessMode'] == 'open_date'">
            {{ downloadNumber.toLocaleString() }}
          </span>
          <span v-else>{{ $t('openPrivate') }}</span>
        </span>
      </div>
      <!-- ライセンス -->
      <div class="flex pt-1 pb-1 text-sm items-center h-8">
        <span class="font-medium">{{ $t('license') }} :</span>
        <span class="ml-2">
          <div v-if="isIcon">
            <img :src="licenseImg" class="cursor-pointer object-contain h-7" @click="clickLicense" />
          </div>
          <div v-else>{{ licenseImg }}</div>
        </span>
      </div>
      <!-- DL区分 -->
      <!-- <div class="flex pt-1 pb-1 text-sm items-center h-8">
        <span class="basis-1/2 font-medium">{{ $t('DLRange') }} :</span>
        <span class="basis-1/2 dl-tags unlimited w-full">無制限</span>
      </div> -->
    </td>
    <!-- アクション -->
    <td class="text-left">
      <!-- プレビュー -->
      <a class="btn-action icons-action icon-preview cursor-pointer" @click.prevent="preview">
        <div class="ml-4">
          {{ $t('preview') }}
        </div>
      </a>
      <!-- ダウンロード -->
      <a class="btn-action icons-action icon-download cursor-pointer" @click.prevent="download">
        <div class="ml-4">
          {{ $t('download') }}
        </div>
      </a>
      <!-- インフォーメーション -->
      <!-- <a class="btn-action icons-action icon-info-bk">
        <div class="ml-4">
          {{ $t('information') }}
        </div>
      </a> -->
      <!-- 利用許可申請 -->
      <!-- <a class="btn-action icons-action icon-approval">
        <div class="ml-4">
          {{ $t('requestUsePermission') }}
        </div>
      </a>
      <p class="text-miby-black text-xs font-bold text-left pl-3">※承認後30日かつ5回まで</p> -->
    </td>
    <!-- 格納場所 -->
    <td class="text-left break-words">
      <span v-if="file.hasOwnProperty(appConfig.roCrate.root.file.url)">
        <a class="inline-block break-all">
          {{ file[appConfig.roCrate.root.file.url] }}
        </a>
      </span>
      <span v-else>undefined</span>
    </td>
  </tr>
</template>

<script lang="ts" setup>
/* ///////////////////////////////////
// props
/////////////////////////////////// */

const props = defineProps({
  // API Response(JSON)
  file: {
    type: Object,
    default: () => {}
  },
  // DL回数統計期間
  span: {
    type: String,
    default: ''
  }
});

/* ///////////////////////////////////
// emits
/////////////////////////////////// */

const emits = defineEmits(['clickCheckbox', 'error']);

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const local = String(localStorage.getItem('locale') ?? 'ja');
const appConfig = useAppConfig();
const isCeck = ref(false);
const licenseImg = ref('');
const isIcon = ref(true);
const downloadNumber = ref(0);
let licenseLink = '';

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * ファイルのダウンロード回数取得
 */
function getDownloadNumber() {
  let statusCode = 0;
  $fetch(appConfig.wekoApi + '/records/' + useRoute().query.number + '/files/' + props.file['@id'] + '/stats', {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'GET',
    headers: {
      'Cache-Control': 'no-store',
      Pragma: 'no-cache',
      'Accept-Language': localStorage.getItem('locale') ?? 'ja',
      Authorization: localStorage.getItem('token:type') + ' ' + localStorage.getItem('token:access')
    },
    params: {
      date: props.span
    },
    onResponse({ response }) {
      if (response.status === 200) {
        downloadNumber.value = response._data.download_total;
      }
    },
    onResponseError({ response }) {
      statusCode = response.status;
      emits('error', response.status, 'message.error.getFileDlNumber');
    }
  }).catch(() => {
    if (statusCode === 0) {
      emits('error', 0, 'message.error.fetch');
    }
  });
}

/**
 * ライセンスアイコン設定
 */
function setLicenseIcon() {
  if (props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.zero) {
    licenseImg.value = '/img/license/cc-zero.svg';
    licenseLink = local === 'ja' ? appConfig.cc.link.zero_ja : appConfig.cc.link.zero;
  } else if (
    props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_3 ||
    props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_4
  ) {
    licenseImg.value = '/img/license/by.svg';
    if (local === 'ja') {
      licenseLink =
        props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_3
          ? appConfig.cc.link.by_3_ja
          : appConfig.cc.link.by_4_ja;
    } else {
      licenseLink =
        props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_3
          ? appConfig.cc.link.by_3
          : appConfig.cc.link.by_4;
    }
  } else if (
    props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_sa_3 ||
    props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_sa_4
  ) {
    licenseImg.value = '/img/license/by-sa.svg';
    if (local === 'ja') {
      licenseLink =
        props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_sa_3
          ? appConfig.cc.link.by_sa_3_ja
          : appConfig.cc.link.by_sa_4_ja;
    } else {
      licenseLink =
        props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_sa_3
          ? appConfig.cc.link.by_sa_3
          : appConfig.cc.link.by_sa_4;
    }
  } else if (
    props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_nd_3 ||
    props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_nd_4
  ) {
    licenseImg.value = '/img/license/by-nd.svg';
    if (local === 'ja') {
      licenseLink =
        props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_nd_3
          ? appConfig.cc.link.by_nd_3_ja
          : appConfig.cc.link.by_nd_4_ja;
    } else {
      licenseLink =
        props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_nd_3
          ? appConfig.cc.link.by_nd_3
          : appConfig.cc.link.by_nd_4;
    }
  } else if (
    props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_nc_3 ||
    props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_nc_4
  ) {
    licenseImg.value = '/img/license/by-nc.svg';
    if (local === 'ja') {
      licenseLink =
        props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_nc_3
          ? appConfig.cc.link.by_nc_3_ja
          : appConfig.cc.link.by_nc_4_ja;
    } else {
      licenseLink =
        props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_nc_3
          ? appConfig.cc.link.by_nc_3
          : appConfig.cc.link.by_nc_4;
    }
  } else if (
    props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_nc_sa_3 ||
    props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_nc_sa_4
  ) {
    licenseImg.value = '/img/license/by-nc-sa.svg';
    if (local === 'ja') {
      licenseLink =
        props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_nc_sa_3
          ? appConfig.cc.link.by_nc_sa_3_ja
          : appConfig.cc.link.by_nc_sa_4_ja;
    } else {
      licenseLink =
        props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_nc_sa_3
          ? appConfig.cc.link.by_nc_sa_3
          : appConfig.cc.link.by_nc_sa_4;
    }
  } else if (
    props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_nc_nd_3 ||
    props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_nc_nd_4
  ) {
    licenseImg.value = '/img/license/by-nc-nd.svg';
    if (local === 'ja') {
      licenseLink =
        props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_nc_nd_3
          ? appConfig.cc.link.by_nc_nd_3_ja
          : appConfig.cc.link.by_nc_nd_4_ja;
    } else {
      licenseLink =
        props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.by_nc_nd_3
          ? appConfig.cc.link.by_nc_nd_3
          : appConfig.cc.link.by_nc_nd_4;
    }
  } else if (props.file[appConfig.roCrate.root.file.licenseType] === appConfig.cc.free) {
    isIcon.value = false;
    licenseImg.value = props.file[appConfig.roCrate.root.file.licenseWrite];
  } else {
    isIcon.value = false;
  }
}

/**
 * ファイルダウンロード
 */
function download() {
  let statusCode = 0;
  $fetch(appConfig.wekoApi + '/records/' + useRoute().query.number + '/files/' + props.file['@id'], {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'GET',
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
        a.setAttribute('download', props.file['@id']);
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

/**
 * ファイルプレビュー
 */
function preview() {
  let statusCode = 0;
  $fetch(appConfig.wekoApi + '/records/' + useRoute().query.number + '/files/' + props.file['@id'], {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'GET',
    headers: {
      'Cache-Control': 'no-store',
      Pragma: 'no-cache',
      'Accept-Language': localStorage.getItem('locale') ?? 'ja',
      Authorization: localStorage.getItem('token:type') + ' ' + localStorage.getItem('token:access')
    },
    params: {
      mode: 'preview'
    },
    onResponse({ response }) {
      if (response.status === 200) {
        const mimeType = response._data.type;
        const blob = new Blob([response._data], { type: mimeType });
        const url = '/preview' + '?type=' + mimeType + '&blob=' + window.URL.createObjectURL(blob);
        window.open(url, '_blank');
      }
    },
    onResponseError({ response }) {
      statusCode = response.status;
      emits('error', response.status, 'message.error.preview');
    }
  }).catch(() => {
    if (statusCode === 0) {
      emits('error', 0, 'message.error.fetch');
    }
  });
}

/**
 * ライセンス押下時イベント
 */
function clickLicense() {
  window.open(licenseLink, '_blank');
}

/* ///////////////////////////////////
// main
/////////////////////////////////// */

try {
  setLicenseIcon();
  if (props.file.accessMode === 'open_access' || props.file.accessMode === 'open_date') {
    if (new Date(Date.parse(props.file.dateCreated[0])) <= new Date(Date.now())) {
      getDownloadNumber();
    }
  }
} catch (error) {
  // console.log(error);
}

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

watch(
  () => props.span,
  () => {
    if (props.file.accessMode === 'open_access' || props.file.accessMode === 'open_date') {
      if (new Date(Date.parse(props.file.dateCreated[0])) <= new Date(Date.now())) {
        getDownloadNumber();
      }
    }
  }
);
</script>

<style lang="scss" scoped>
th {
  @apply border border-miby-thin-gray text-center align-middle;
  @apply py-1 font-medium;
}
td {
  @apply border border-miby-thin-gray text-center align-middle;
  @apply px-2 pt-5 pb-5;
  &.text-left {
    text-align: left;
  }
}
.btn-action {
  @apply w-[160px] relative mx-auto text-xs p-1 mb-1.5 block border-2 border-miby-black rounded bg-miby-tag-white;
  &::before {
    @apply absolute left-1.5 top-1.5;
  }
}
</style>
