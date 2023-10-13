<template>
  <div class="search-rows">
    <!-- サムネイル -->
    <div class="rows-image w-full flex justify-center items-center bg-neutral-600" style="height: 108px">
      <div v-if="loading" class="font-bold text-2xl text-white h-full flex justify-center items-center content-center">
        <span class="loading loading-bars loading-l" />
      </div>
      <div v-else>
        <img :src="thumbnailPath" alt="Thumbnail" />
      </div>
    </div>
    <div class="rows-detail">
      <div class="flex flex-nowrap mb-1.5 gap-5 items-center">
        <!-- 公開区分 -->
        <p
          v-if="item.metadata['@graph'][0].hasOwnProperty('accessMode')"
          :class="[
            item.metadata['@graph'][0].accessMode[0] === 'Public'
              ? 'icons-type icon-published'
              : item.metadata['@graph'][0].accessMode[0] === 'Shared'
              ? 'icons-type icon-group'
              : item.metadata['@graph'][0].accessMode[0] === 'Private'
              ? 'icons-type icon-private'
              : item.metadata['@graph'][0].accessMode[0] === 'Unshared'
              ? 'icons-type icon-limited'
              : ''
          ]">
          <span style="margin-left: 0px">
            {{
              item.metadata['@graph'][0].accessMode[0] === 'Public'
                ? $t('openPublic')
                : item.metadata['@graph'][0].accessMode[0] === 'Shared'
                ? $t('openGroup')
                : item.metadata['@graph'][0].accessMode[0] === 'Private'
                ? $t('openPrivate')
                : item.metadata['@graph'][0].accessMode[0] === 'Unshared'
                ? $t('openRestricted')
                : item.metadata['@graph'][0].accessMode[0]
            }}
          </span>
        </p>
        <p v-else class="icons-type icon-published">
          <span style="margin-left: 0px">undefined</span>
        </p>
        <!-- 公開日 -->
        <p class="date-upload icons icon-publish">
          <span v-if="item.metadata['@graph'][0].hasOwnProperty('dateCreated')">
            {{ item.metadata['@graph'][0].dateCreated[0] }}
          </span>
          <span v-else>undefined</span>
        </p>
        <!-- 更新日 -->
        <p class="date-update icons icon-update">
          <span v-if="item.metadata['@graph'][0].hasOwnProperty('datePublished')">
            {{
              typeof item.metadata['@graph'][0].datePublished == 'object'
                ? item.metadata['@graph'][0].datePublished[0]
                : 'undefined'
            }}
          </span>
        </p>
      </div>
      <!-- タイトル -->
      <NuxtLink class="data-title whitespace-normal" :to="`/detail?sess=search&number=${item.id}`">
        {{ item.metadata['@graph'][0].title[0] }}
      </NuxtLink>
      <div class="flex mb-1">
        <!-- 分野 -->
        <p class="data-note">
          {{ $t('field') + '：' }}
          <span v-if="item.metadata['@graph'][0].hasOwnProperty('genre')">
            {{ item.metadata['@graph'][0].genre[0] }}
          </span>
          <span v-else>undefined</span>
        </p>
        <!-- 作成者 -->
        <p class="data-note author">
          {{ $t('creater') + '：' }}
          <span v-if="item.metadata['@graph'][0].hasOwnProperty('creator')">
            <a>
              {{
                item.metadata['@graph'][0].creator[1]
                  ? `[${item.metadata['@graph'][0].creator[1] ?? 'undefined'}] `
                  : 'undefined'
              }}
            </a>
            <a class="text-miby-link-blue underline cursor-pointer" @click="emits('clickCreater')">
              {{ item.metadata['@graph'][0].creator[0] ?? '' }}
            </a>
          </span>
        </p>
      </div>
      <div class="flex flex-nowrap">
        <!-- ヒト/動物/その他 -->
        <p class="data-note">
          {{ $t('classification') + '：' }}
          <span v-if="item.metadata['@graph'][0].hasOwnProperty('target')" class="font-medium">
            {{ item.metadata['@graph'][0].target[0] }}
          </span>
          <span v-else>undefined</span>
        </p>
        <!-- アクセス権 -->
        <p class="data-note access-type">
          {{ $t('authority') + '：' }}
          <span v-if="item.metadata['@graph'][0].hasOwnProperty('accessMode')">
            {{ item.metadata['@graph'][0].accessMode[0] }}
          </span>
          <span v-else>undefined</span>
        </p>
        <!-- ファイル -->
        <p class="data-note">
          {{ $t('file') + '：' }}
          <span class="font-medium">
            <NuxtLink v-if="item.metadata['@graph'][0].mainEntity.length < 1">
              {{ $t('unexist') }}
            </NuxtLink>
            <NuxtLink v-else class="underline text-miby-link-blue" :to="`/files?number=${item.id}`">
              {{ $t('exist') + `（${item.metadata['@graph'][0].mainEntity.length}）` }}
            </NuxtLink>
          </span>
        </p>
      </div>
    </div>
    <div class="grid grid-rows-4 grid-flow-col gap-0">
      <!-- お気に入り -->
      <div class="row-span-1 align-top text-right pr-2">
        <label class="swap swap-rotate">
          <input type="checkbox" class="hidden" />
          <div class="swap-on w-7 rounded"><img src="/img/icon/icon_star-fill.svg" /></div>
          <div class="swap-off w-7 rounded"><img src="/img/icon/icon_star.svg" /></div>
        </label>
      </div>
      <!-- 閲覧数 -->
      <div class="row-span-3 flex justify-end items-end">
        <div class="data-note flex">
          <img src="/img/icon/icon_star-fill-black.svg" alt="My List" class="mr-1" />
          <a>9,999</a>
        </div>
        <div class="data-note flex ml-1">
          <img src="/img/icon/icon_eye-fill.svg" alt="Views" class="mr-1" />
          <a>9,999,999,999</a>
        </div>
      </div>
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
// const
/////////////////////////////////// */

const thumbnailName = Object.prototype.hasOwnProperty.call(props.item.metadata['@graph'][0], 'thumbnail')
  ? props.item.metadata['@graph'][0].thumbnail[0][0]
  : '';
const loading = ref(true);
const thumbnailPath = ref('/img/noimage_thumbnail.jpg');

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

onMounted(() => {
  if (thumbnailName) {
    try {
      $fetch(useAppConfig().wekoApi + '/records/' + props.item.id + '/files/' + thumbnailName, {
        timeout: useRuntimeConfig().public.apiTimeout,
        method: 'GET',
        headers: {
          'Accept-Language': localStorage.getItem('local') ?? 'ja',
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
