<template>
  <tr>
    <!-- チェックボックス -->
    <td class="!p-2">
      <!-- 格納場所がweko外部のファイルは除く -->
      <input
        v-if="fileURL.startsWith(appConfig.wekoOrigin) && file['@id']"
        v-model="isCheck"
        type="checkbox"
        @change="emits('clickCheckbox', file['@id'], isCheck)" />
    </td>
    <!-- ファイル名 -->
    <td v-if="file['@id'].length <= getDisplayMaxLength(file['@id'])" class="text-left break-words !p-2">
      {{ file['@id'] }}
    </td>
    <td v-else class="text-left break-words !p-2" :class="{ 'text-clamp': showTitleOpenFlag }">
      {{ file['@id'] }}
      <p
        class="icons icon-arrow link-color cursor-pointer"
        :class="{ hidden: !showTitleOpenFlag }"
        @click="showTitleOpenFlag = !showTitleOpenFlag">
        {{ $t('showAll') }}
      </p>
      <p
        :class="{ hidden: showTitleOpenFlag }"
        class="icons icon-up-arrow link-color cursor-pointer"
        @click="showTitleOpenFlag = !showTitleOpenFlag">
        {{ $t('showSome') }}
      </p>
    </td>
    <!-- 詳細情報 -->
    <td class="text-left !p-2">
      <!-- 公開日 -->
      <div class="flex pt-1 pb-1 text-sm items-center h-8">
        <span class="font-medium">{{ $t('releaseDate') }} :</span>
        <span class="ml-2">
          <span v-if="file.hasOwnProperty('accessMode') && file.hasOwnProperty('dateCreated')">
            {{ file['dateCreated'] }}
          </span>
          <span v-else>{{ $t('notSet') }}</span>
        </span>
      </div>
      <!-- サイズ -->
      <div class="flex pt-1 pb-1 text-sm items-center h-8">
        <span class="font-medium">{{ $t('size') }} :</span>
        <span class="ml-2">
          <span v-if="fileSize">
            {{ fileSize }}
          </span>
          <span v-else>{{ $t('notSet') }}</span>
        </span>
      </div>
      <!-- DL回数 -->
      <div class="flex pt-1 pb-1 text-sm items-center h-8">
        <span class="font-medium">{{ $t('DLNumber') }} :</span>
        <span class="ml-2">
          <span v-if="file['accessMode'] == 'open_access' || file['accessMode'] == 'open_date'">
            <span v-if="downloadNumber >= 0">
              {{ downloadNumber.toLocaleString() }}
            </span>
            <span v-else>-</span>
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
    <td class="text-left !p-2">
      <!-- プレビュー -->
      <a class="btn-action icons-action icon-preview cursor-pointer !w-full" @click.prevent="preview">
        <div class="ml-4">
          {{ $t('preview') }}
        </div>
      </a>
      <!-- ダウンロード -->
      <!-- 格納場所がweko外部のファイルは除く -->
      <a
        v-if="fileURL.startsWith(appConfig.wekoOrigin)"
        class="btn-action icons-action icon-download cursor-pointer !w-full"
        @click.prevent="download">
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
    <td class="text-left break-words !p-2">
      <span v-if="fileURL">
        <span class="mr-2.5 w-11/12" :class="{ 'text-clamp inline-block': showURLOpenFlag, hidden: !showURLOpenFlag }">
          {{ fileURL }}
        </span>
        <p
          v-if="fileURL.length >= getDisplayMaxLength(fileURL)"
          class="icons icon-arrow link-color cursor-pointer"
          :class="{ hidden: !showURLOpenFlag }"
          @click="showURLOpenFlag = !showURLOpenFlag">
          {{ $t('showAll') }}
        </p>
        <NuxtLink
          v-if="!showURLOpenFlag"
          :to="fileURL"
          target="_blank"
          class="inline-block break-all text-miby-link-blue">
          <span
            v-if="!showURLOpenFlag"
            class="mr-2.5 underline w-11/12"
            :class="{ 'text-clamp inline-block': showURLOpenFlag }">
            {{ fileURL }}
          </span>
        </NuxtLink>
        <p
          v-if="fileURL.length >= getDisplayMaxLength(fileURL)"
          :class="{ hidden: showURLOpenFlag }"
          class="icons icon-up-arrow link-color cursor-pointer"
          @click="showURLOpenFlag = !showURLOpenFlag">
          {{ $t('showSome') }}
        </p>
      </span>
      <span v-else>{{ $t('notSet') }}</span>
    </td>

    <!-- コメント -->
    <td class="text-left break-words !p-2">
      <span v-if="fileComment" :class="{ 'text-clamp inline-block w-full': showCommentOpenFlag }">
        {{ fileComment }}
        <p
          v-if="fileComment.length > getDisplayMaxLength(fileComment)"
          class="icons icon-arrow link-color cursor-pointer"
          :class="{ hidden: !showCommentOpenFlag }"
          @click="showCommentOpenFlag = !showCommentOpenFlag">
          {{ $t('showAll') }}
        </p>
        <p
          :class="{ hidden: showCommentOpenFlag }"
          class="icons icon-up-arrow link-color cursor-pointer"
          @click="showCommentOpenFlag = !showCommentOpenFlag">
          {{ $t('showSome') }}
        </p>
      </span>
      <span v-else>{{ $t('notSet') }}</span>
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
  },
  // ダウンロードするファイルのチェックボックス
  checked: {
    type: Boolean,
    default: true
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
const isCheck = ref(props.checked);
const licenseImg = ref('');
const isIcon = ref(true);
const downloadNumber = ref(-1);
let licenseLink = '';
const showTitleOpenFlag = ref(true);
const showURLOpenFlag = ref(true);
const showCommentOpenFlag = ref(true);
const fileSize: any = Object.prototype.hasOwnProperty.call(props.file, appConfig.roCrate.root.file.size)
  ? props.file[appConfig.roCrate.root.file.size][0]
  : null;
const licenseType: any = setFileInfo(props.file[appConfig.roCrate.root.file.licenseType]);
const fileURL: any = setFileInfo(props.file[appConfig.roCrate.root.file.url]);
const fileComment: any = setFileInfo(props.file[appConfig.roCrate.root.file.comment]);

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
    credentials: 'omit',
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
      // emits('error', response.status, 'message.error.getFileDlNumber');
    }
  }).catch(() => {
    if (statusCode === 0) {
      // emits('error', 0, 'message.error.fetch');
    }
  });
}

/**
 * ライセンスアイコン設定
 */
function setLicenseIcon() {
  if (licenseType === appConfig.cc.zero) {
    licenseImg.value = '/img/license/cc-zero.svg';
    licenseLink = local === 'ja' ? appConfig.cc.link.zero_ja : appConfig.cc.link.zero;
  } else if (licenseType === appConfig.cc.by_3 || licenseType === appConfig.cc.by_4) {
    licenseImg.value = '/img/license/by.svg';
    if (local === 'ja') {
      licenseLink = licenseType === appConfig.cc.by_3 ? appConfig.cc.link.by_3_ja : appConfig.cc.link.by_4_ja;
    } else {
      licenseLink = licenseType === appConfig.cc.by_3 ? appConfig.cc.link.by_3 : appConfig.cc.link.by_4;
    }
  } else if (licenseType === appConfig.cc.by_sa_3 || licenseType === appConfig.cc.by_sa_4) {
    licenseImg.value = '/img/license/by-sa.svg';
    if (local === 'ja') {
      licenseLink = licenseType === appConfig.cc.by_sa_3 ? appConfig.cc.link.by_sa_3_ja : appConfig.cc.link.by_sa_4_ja;
    } else {
      licenseLink = licenseType === appConfig.cc.by_sa_3 ? appConfig.cc.link.by_sa_3 : appConfig.cc.link.by_sa_4;
    }
  } else if (licenseType === appConfig.cc.by_nd_3 || licenseType === appConfig.cc.by_nd_4) {
    licenseImg.value = '/img/license/by-nd.svg';
    if (local === 'ja') {
      licenseLink = licenseType === appConfig.cc.by_nd_3 ? appConfig.cc.link.by_nd_3_ja : appConfig.cc.link.by_nd_4_ja;
    } else {
      licenseLink = licenseType === appConfig.cc.by_nd_3 ? appConfig.cc.link.by_nd_3 : appConfig.cc.link.by_nd_4;
    }
  } else if (licenseType === appConfig.cc.by_nc_3 || licenseType === appConfig.cc.by_nc_4) {
    licenseImg.value = '/img/license/by-nc.svg';
    if (local === 'ja') {
      licenseLink = licenseType === appConfig.cc.by_nc_3 ? appConfig.cc.link.by_nc_3_ja : appConfig.cc.link.by_nc_4_ja;
    } else {
      licenseLink = licenseType === appConfig.cc.by_nc_3 ? appConfig.cc.link.by_nc_3 : appConfig.cc.link.by_nc_4;
    }
  } else if (licenseType === appConfig.cc.by_nc_sa_3 || licenseType === appConfig.cc.by_nc_sa_4) {
    licenseImg.value = '/img/license/by-nc-sa.svg';
    if (local === 'ja') {
      licenseLink =
        licenseType === appConfig.cc.by_nc_sa_3 ? appConfig.cc.link.by_nc_sa_3_ja : appConfig.cc.link.by_nc_sa_4_ja;
    } else {
      licenseLink =
        licenseType === appConfig.cc.by_nc_sa_3 ? appConfig.cc.link.by_nc_sa_3 : appConfig.cc.link.by_nc_sa_4;
    }
  } else if (licenseType === appConfig.cc.by_nc_nd_3 || licenseType === appConfig.cc.by_nc_nd_4) {
    licenseImg.value = '/img/license/by-nc-nd.svg';
    if (local === 'ja') {
      licenseLink =
        licenseType === appConfig.cc.by_nc_nd_3 ? appConfig.cc.link.by_nc_nd_3_ja : appConfig.cc.link.by_nc_nd_4_ja;
    } else {
      licenseLink =
        licenseType === appConfig.cc.by_nc_nd_3 ? appConfig.cc.link.by_nc_nd_3 : appConfig.cc.link.by_nc_nd_4;
    }
  } else if (licenseType === appConfig.cc.free) {
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
    credentials: 'omit',
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
        // プレーンテキストの場合(= response._data.type がない場合)に専用のURLを作成する必要あり
        const preview = !response._data.type ? '/file_preview/' : '/preview/';
        const url = appConfig.wekoOrigin + '/record/' + useRoute().query.number + preview + props.file['@id'];
        window.open(url, '', 'toolbar=no');
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

/**
 * 省略表示を行うための文字数判定
 */
function getDisplayMaxLength(item: String) {
  let itemLength: Number = 22;
  if (checkEn(item)) {
    itemLength = 40;
  }
  return itemLength;
}

/**
 * 英文(記号含む)かどうかチェックする
 * @param name
 */
function checkEn(name: any) {
  name = name.replace(/\s+/g, '');
  if (/[\p{Script_Extensions=Greek}]/v.test(name)) {
    name = name.replace(/[α-ω]/g, '');
  }
  return /^[ -~]+$/.test(name);
}

/**
 * マッピング済みのファイル情報を取得する
 * マッピングされていない場合は空文字を返す
 * @param info ファイル情報（ライセンス、格納場所、コメント）
 * @returns ファイル情報
 */
function setFileInfo(info: any) {
  const returnInfo = Array.isArray(info) ? info[0] : info;
  return returnInfo ? returnInfo : '';
}

/* ///////////////////////////////////
// main
/////////////////////////////////// */

try {
  setLicenseIcon();
  if (props.file.accessMode === 'open_access' || props.file.accessMode === 'open_date') {
    if (new Date(Date.parse(props.file.dateCreated)) <= new Date(Date.now())) {
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
      if (new Date(Date.parse(props.file.dateCreated)) <= new Date(Date.now())) {
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
  @apply w-[120px] relative mx-auto text-xs p-1 mb-1.5 block border-2 border-miby-black rounded bg-miby-tag-white;
  &::before {
    @apply absolute left-1.5 top-1.5;
  }
}
</style>
