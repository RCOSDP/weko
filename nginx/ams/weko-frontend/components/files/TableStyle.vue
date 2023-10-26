<template>
  <tr>
    <!-- チェックボックス -->
    <td>
      <input v-model="isCeck" type="checkbox" @change="emits('clickCeckbox', file['@id'], isCeck)" />
    </td>
    <!-- ファイル名 -->
    <td class="max-w-[130px] text-left">
      {{ file['@id'] }}
    </td>
    <!-- サイズ -->
    <td>{{ file[appConfig.roCrate.file.size] }}</td>
    <!-- DL区分 -->
    <td><span class="dl-tags unlimited">無制限</span></td>
    <!-- ライセンス -->
    <td>
      <div v-if="isIcon" class="w-[68px] mx-auto">
        <img :src="licenseImg" class="cursor-pointer" @click="clickLicense" />
      </div>
      <div v-else>{{ licenseImg }}</div>
    </td>
    <!-- アクション -->
    <td class="w-[190px] text-left">
      <a class="btn-action icons-action icon-preview cursor-pointer" @click.prevent="preview">
        <div class="ml-4">
          {{ $t('preview') }}
        </div>
      </a>
      <a class="btn-action icons-action icon-download cursor-pointer" @click.prevent="download">
        <div class="ml-4">
          {{ $t('download') }}
        </div>
      </a>
      <a class="btn-action icons-action icon-info-bk" href="#">
        <div class="ml-4">
          {{ $t('information') }}
        </div>
      </a>
      <a class="btn-action icons-action icon-approval" href="#">
        <div class="ml-4">
          {{ $t('requestUsePermission') }}
        </div>
      </a>
      <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
    </td>
    <!-- 格納場所 -->
    <td class="w-[190px] text-left">
      <a class="inline-block max-w-[180px] underline text-miby-link-blue break-all hover:cursor-pointer">
        {{ file[appConfig.roCrate.file.url] }}
      </a>
    </td>
    <!-- DL回数 -->
    <td>9,999,999,999</td>
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
  }
});

/* ///////////////////////////////////
// emits
/////////////////////////////////// */

const emits = defineEmits(['clickCeckbox', 'error']);

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const local = String(localStorage.getItem('locale') ?? 'ja');
const appConfig = useAppConfig();
const isCeck = ref(false);
const licenseImg = ref('');
const isIcon = ref(true);
let licenseLink = '';

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * ファイルダウンロード
 */
function download() {
  $fetch(appConfig.wekoApi + '/records/' + useRoute().query.number + '/files/' + props.file['@id'], {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'GET',
    headers: {
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
      emits('error', response.status, 'message.error.download');
    }
  });
}

/**
 * ファイルプレビュー
 */
function preview() {
  $fetch(appConfig.wekoApi + '/records/' + useRoute().query.number + '/files/' + props.file['@id'], {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'GET',
    headers: {
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
      emits('error', response.status, 'message.error.preview');
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
  if (props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.zero) {
    licenseImg.value = '/img/license/cc-zero.svg';
    licenseLink = local === 'ja' ? appConfig.cc.link.zero_ja : appConfig.cc.link.zero;
  } else if (
    props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_3 ||
    props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_4
  ) {
    licenseImg.value = '/img/license/by.svg';
    if (local === 'ja') {
      licenseLink =
        props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_3
          ? appConfig.cc.link.by_3_ja
          : appConfig.cc.link.by_4_ja;
    } else {
      licenseLink =
        props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_3
          ? appConfig.cc.link.by_3
          : appConfig.cc.link.by_4;
    }
  } else if (
    props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_sa_3 ||
    props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_sa_4
  ) {
    licenseImg.value = '/img/license/by-sa.svg';
    if (local === 'ja') {
      licenseLink =
        props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_sa_3
          ? appConfig.cc.link.by_sa_3_ja
          : appConfig.cc.link.by_sa_4_ja;
    } else {
      licenseLink =
        props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_sa_3
          ? appConfig.cc.link.by_sa_3
          : appConfig.cc.link.by_sa_4;
    }
  } else if (
    props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_nd_3 ||
    props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_nd_4
  ) {
    licenseImg.value = '/img/license/by-nd.svg';
    if (local === 'ja') {
      licenseLink =
        props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_nd_3
          ? appConfig.cc.link.by_nd_3_ja
          : appConfig.cc.link.by_nd_4_ja;
    } else {
      licenseLink =
        props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_nd_3
          ? appConfig.cc.link.by_nd_3
          : appConfig.cc.link.by_nd_4;
    }
  } else if (
    props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_nc_3 ||
    props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_nc_4
  ) {
    licenseImg.value = '/img/license/by-nc.svg';
    if (local === 'ja') {
      licenseLink =
        props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_nc_3
          ? appConfig.cc.link.by_nc_3_ja
          : appConfig.cc.link.by_nc_4_ja;
    } else {
      licenseLink =
        props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_nc_3
          ? appConfig.cc.link.by_nc_3
          : appConfig.cc.link.by_nc_4;
    }
  } else if (
    props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_nc_sa_3 ||
    props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_nc_sa_4
  ) {
    licenseImg.value = '/img/license/by-nc-sa.svg';
    if (local === 'ja') {
      licenseLink =
        props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_nc_sa_3
          ? appConfig.cc.link.by_nc_sa_3_ja
          : appConfig.cc.link.by_nc_sa_4_ja;
    } else {
      licenseLink =
        props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_nc_sa_3
          ? appConfig.cc.link.by_nc_sa_3
          : appConfig.cc.link.by_nc_sa_4;
    }
  } else if (
    props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_nc_nd_3 ||
    props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_nc_nd_4
  ) {
    licenseImg.value = '/img/license/by-nc-nd.svg';
    if (local === 'ja') {
      licenseLink =
        props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_nc_nd_3
          ? appConfig.cc.link.by_nc_nd_3_ja
          : appConfig.cc.link.by_nc_nd_4_ja;
    } else {
      licenseLink =
        props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.by_nc_nd_3
          ? appConfig.cc.link.by_nc_nd_3
          : appConfig.cc.link.by_nc_nd_4;
    }
  } else if (props.file[appConfig.roCrate.file.licenseType] === appConfig.cc.free) {
    isIcon.value = false;
    licenseImg.value = props.file[appConfig.roCrate.file.licenseWrite];
  }
} catch (error) {
  // console.log(error);
}
</script>

<style lang="scss" scoped>
th {
  @apply border border-miby-thin-gray text-center align-middle;
  @apply py-1 font-medium;
}
td {
  @apply border border-miby-thin-gray text-center align-middle;
  @apply px-2 pt-5 pb-7;
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
