<template>
  <div class="search-rows">
    <!-- サムネイル -->
    <div class="rows-image h-28 w-24 flex justify-center items-center bg-neutral-300">
      <div v-if="loading" class="font-bold text-2xl text-white h-full flex justify-center items-center content-center">
        <span class="loading loading-bars loading-l" />
      </div>
      <img v-else :src="thumbnailPath" alt="Thumbnail" class="object-contain h-28 w-24" />
    </div>
    <div class="rows-detail">
      <div class="flex flex-nowrap mb-1.5 gap-5 items-center">
        <!-- 公開区分 -->
        <p
          v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.releaseRange)"
          :class="[
            itemInfo[appConf.roCrate.root.releaseRange][0] === appConf.roCrate.selector.releaseRange.public
              ? 'icons-type icon-public'
              : itemInfo[appConf.roCrate.root.releaseRange][0] === appConf.roCrate.selector.releaseRange.group
              ? 'icons-type icon-group'
              : itemInfo[appConf.roCrate.root.releaseRange][0] === appConf.roCrate.selector.releaseRange.member
              ? 'icons-type icon-member'
              : itemInfo[appConf.roCrate.root.releaseRange][0] === appConf.roCrate.selector.releaseRange.private
              ? 'icons-type icon-private'
              : 'icons-type icon-public'
          ]">
          <span style="margin-left: 0px">
            {{
              itemInfo[appConf.roCrate.root.releaseRange][0] === appConf.roCrate.selector.releaseRange.public
                ? $t('openPublic')
                : itemInfo[appConf.roCrate.root.releaseRange][0] === appConf.roCrate.selector.releaseRange.group
                ? $t('openGroup')
                : itemInfo[appConf.roCrate.root.releaseRange][0] === appConf.roCrate.selector.releaseRange.member
                ? $t('openPrivate')
                : itemInfo[appConf.roCrate.root.releaseRange][0] === appConf.roCrate.selector.releaseRange.private
                ? $t('openRestricted')
                : 'undefined'
            }}
          </span>
        </p>
        <p v-else class="icons-type icon-public">
          <span style="margin-left: 0px">undefined</span>
        </p>
        <!-- 公開日 -->
        <p class="date-upload icons icon-publish">
          <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.releaseDate)">
            {{ itemInfo[appConf.roCrate.root.releaseDate][0] }}
          </span>
          <span v-else>undefined</span>
        </p>
        <!-- 更新日 -->
        <p class="date-update icons icon-update">
          <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.updateDate)">
            {{
              typeof itemInfo[appConf.roCrate.root.updateDate] == 'object'
                ? itemInfo[appConf.roCrate.root.updateDate][0]
                : 'undefined'
            }}
          </span>
          <span v-else>undefined</span>
        </p>
      </div>
      <!-- タイトル -->
      <NuxtLink class="data-title whitespace-normal" :to="`/detail?sess=search&number=${item.id}`">
        <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.title)">
          {{ itemInfo[appConf.roCrate.root.title][0] }}
        </span>
        <span v-else>undefined</span>
      </NuxtLink>
      <div class="flex mb-1">
        <!-- 分野 -->
        <p class="data-note">
          {{ $t('field') + '：' }}
          <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.field)">
            {{ itemInfo[appConf.roCrate.root.field][0] }}
          </span>
          <span v-else>undefined</span>
        </p>
        <!-- 作成者 -->
        <p class="data-note author">
          {{ $t('creater') + '：' }}
          <span v-if="itemInfo[appConf.roCrate.root.authorAffiliation]" class="data-author mr-1">
            [
            <span
              v-for="affiliation in itemInfo[appConf.roCrate.root.authorAffiliation]"
              :key="affiliation"
              class="affiliation">
              <a>
                {{ affiliation }}
              </a>
            </span>
            ]
          </span>
          <span v-else class="mr-1">[undefined]</span>
          <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.authorName)" class="data-author">
            <span v-for="name in itemInfo[appConf.roCrate.root.authorName]" :key="name" class="tag-link">
              <a @click="emits('clickCreater')">
                {{ name }}
              </a>
            </span>
          </span>
          <span v-else>undefined</span>
        </p>
      </div>
      <div class="flex flex-nowrap">
        <!-- ヒト/動物/その他 -->
        <p class="data-note">
          {{ $t('classification') + '：' }}
          <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.target)" class="font-medium">
            {{ itemInfo[appConf.roCrate.root.target][0] }}
          </span>
          <span v-else>undefined</span>
        </p>
        <!-- アクセス権 -->
        <p class="data-note access-type">
          {{ $t('authority') + '：' }}
          <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.accessMode)">
            {{ itemInfo[appConf.roCrate.root.accessMode][0] }}
          </span>
          <span v-else>undefined</span>
        </p>
        <!-- ファイル -->
        <p class="data-note">
          {{ $t('file') + '：' }}
          <span class="font-medium">
            <NuxtLink v-if="itemInfo.mainEntity.length < 1">
              {{ $t('unexist') }}
            </NuxtLink>
            <NuxtLink v-else class="underline text-miby-link-blue" :to="`/files?number=${item.id}`">
              {{ $t('exist') + `（${getFileLength(itemInfo.mainEntity)}）` }}
            </NuxtLink>
          </span>
        </p>
      </div>
    </div>
    <div class="grid grid-rows-4 grid-flow-col gap-0">
      <!-- お気に入り -->
      <!-- <div class="row-span-1 align-top text-right pr-2">
        <label class="swap swap-rotate">
          <input type="checkbox" class="hidden" />
          <div class="swap-on w-7 rounded"><img src="/img/icon/icon_star-fill.svg" /></div>
          <div class="swap-off w-7 rounded"><img src="/img/icon/icon_star.svg" /></div>
        </label>
      </div> -->
      <!-- 閲覧数 -->
      <!-- <div class="row-span-3 flex justify-end items-end">
        <div class="data-note flex">
          <img src="/img/icon/icon_star-fill-black.svg" alt="My List" class="mr-1" />
          <a>9,999</a>
        </div>
        <div class="data-note flex ml-1">
          <img src="/img/icon/icon_eye-fill.svg" alt="Views" class="mr-1" />
          <a>9,999,999,999</a>
        </div>
      </div> -->
    </div>
  </div>
</template>

<script lang="ts" setup>
/* ///////////////////////////////////
// props
/////////////////////////////////// */

const props = defineProps({
  // API Response(JSON)
  item: {
    type: Object,
    default: () => {}
  }
});

/* ///////////////////////////////////
// emits
/////////////////////////////////// */

const emits = defineEmits(['clickCreater']);

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const appConf = useAppConfig();
const itemInfo = Object.prototype.hasOwnProperty.call(props.item, 'metadata')
  ? getContentById(props.item.metadata, './')
  : {};
const thumbnailName = Object.prototype.hasOwnProperty.call(itemInfo, appConf.roCrate.root.thumbnail)
  ? itemInfo[appConf.roCrate.root.thumbnail][0]
  : '';
const loading = ref(true);
const thumbnailPath = ref('/img/noimage_thumbnail.jpg');

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * RO-Crateレスポンスからファイル数を取得
 * @param fileList アイテムに紐づくファイル
 */
function getFileLength(fileList: any[]) {
  const tmpList = [];

  for (const element of fileList) {
    const value = getContentById(props.item.metadata, element['@id']);
    // NOTE: ロール制御が出来ないので下記のアクセス種別のファイルのみ表示している
    if (value.accessMode !== 'open_no') {
      // @ts-ignore
      tmpList.push(value);
    }
  }

  return tmpList.length;
}

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

onMounted(() => {
  if (thumbnailName) {
    try {
      $fetch(appConf.wekoApi + '/records/' + props.item.id + '/files/' + thumbnailName, {
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
            const blob = new Blob([response._data], { type: response._data.type });
            thumbnailPath.value = window.URL.createObjectURL(blob);
          }
          loading.value = false;
        }
      });
    } catch (error) {
      loading.value = false;
    }
  } else {
    loading.value = false;
  }
});
</script>

<style scoped>
.author span,
.author span::before,
.author span:first-child::before,
.access-type span {
  display: inline-block;
}
.access-type span::before {
  content: ', ';
}
.access-type span:first-child::before {
  content: '';
}
</style>
