<template>
  <div v-if="Object.keys(item).length">
    <hr class="border-miby-dark-gray" />
    <div class="detail__head">
      <!-- サムネイル -->
      <div class="detail__head-image h-40 w-32 flex justify-center items-center bg-neutral-600">
        <div
          v-if="loading"
          class="font-bold text-2xl text-white h-full flex justify-center items-center content-center">
          <span class="loading loading-bars loading-l" />
        </div>
        <div v-else>
          <img :src="thumbnailPath" alt="Thumbnail" />
        </div>
      </div>
      <div class="detail__head-text">
        <div class="flex flex-wrap mb-1.5 gap-2 md:gap-5 items-center">
          <!-- 公開区分 -->
          <p
            v-if="item['@graph'][0].hasOwnProperty('accessMode')"
            :class="[
              item['@graph'][0].accessMode[0] === 'Public'
                ? 'icons-type icon-published'
                : item['@graph'][0].accessMode[0] === 'Shared'
                ? 'icons-type icon-group'
                : item['@graph'][0].accessMode[0] === 'Private'
                ? 'icons-type icon-private'
                : item['@graph'][0].accessMode[0] === 'Unshared'
                ? 'icons-type icon-limited'
                : ''
            ]">
            <span>
              {{
                item['@graph'][0].accessMode[0] === 'Public'
                  ? $t('openPublic')
                  : item['@graph'][0].accessMode[0] === 'Shared'
                  ? $t('openGroup')
                  : item['@graph'][0].accessMode[0] === 'Private'
                  ? $t('openPrivate')
                  : item['@graph'][0].accessMode[0] === 'Unshared'
                  ? $t('openRestricted')
                  : item['@graph'][0].accessMode[0]
              }}
            </span>
          </p>
          <p v-else class="icons-type icon-published">
            <span>undefined</span>
          </p>
          <!-- 公開日 -->
          <p class="date-upload icons icon-publish">
            <span v-if="item['@graph'][0].hasOwnProperty('dateCreated')">
              {{ item['@graph'][0].dateCreated[0] }}
            </span>
            <span v-else>undefined</span>
          </p>
          <!-- 更新日 -->
          <p class="date-update icons icon-update">
            <span v-if="item['@graph'][0].hasOwnProperty('datePublished')">
              {{
                typeof item['@graph'][0].datePublished == 'object' ? item['@graph'][0].datePublished[0] : 'undefined'
              }}
            </span>
          </p>
        </div>
        <!-- タイトル -->
        <a class="data-dtitle text-left">
          {{ item['@graph'][0].title[0] }}
        </a>
        <div class="text-left sm:flex mb-1">
          <!-- 分野 -->
          <p class="data-note">
            {{ $t('field') + '：' }}
            <span v-if="item['@graph'][0].hasOwnProperty('genre')">
              {{ item['@graph'][0].genre[0] }}
            </span>
            <span v-else>undefined</span>
          </p>
          <!-- 作成者 -->
          <p class="data-note author">
            {{ $t('creater') + '：' }}
            <span v-if="item['@graph'][0].hasOwnProperty('creator')">
              <a>
                {{ item['@graph'][0].creator[1] ? `[${item['@graph'][0].creator[1] ?? 'undefined'}] ` : 'undefined' }}
              </a>
              <a class="text-miby-link-blue underline cursor-pointer" @click="emits('clickCreater')">
                {{ item['@graph'][0].creator[0] ?? '' }}
              </a>
            </span>
          </p>
        </div>
        <div class="text-left sm:flex flex-wrap">
          <!-- ヒト/動物/その他 -->
          <p class="data-note">
            {{ $t('classification') + '：' }}
            <span v-if="item['@graph'][0].hasOwnProperty('target')" class="font-medium">
              {{ item['@graph'][0].target[0] }}
            </span>
            <span v-else>undefined</span>
          </p>
          <!-- アクセス権 -->
          <p class="data-note access-type">
            {{ $t('authority') + '：' }}
            <span v-if="item['@graph'][0].hasOwnProperty('accessMode')">
              {{ item['@graph'][0].accessMode[0] }}
            </span>
            <span v-else>undefined</span>
          </p>
          <!-- ファイル -->
          <p class="data-note">
            {{ $t('file') + '：' }}
            <span class="font-medium">
              <NuxtLink v-if="item['@graph'][0].mainEntity.length < 1">
                {{ $t('unexist') }}
              </NuxtLink>
              <NuxtLink v-else class="underline text-miby-link-blue" :to="`/files?number=${itemId}`">
                {{ $t('exist') + `（${item['@graph'][0].mainEntity.length}）` }}
              </NuxtLink>
            </span>
          </p>
        </div>
        <!-- キーワード -->
        <div class="data-tags mt-1">
          <span v-if="item['@graph'][0].hasOwnProperty('keywords')">
            <span v-for="keyword in String(item['@graph'][0].keywords).split(',')" :key="keyword" class="tag-link">
              <span class="hover:cursor-pointer">
                {{ keyword }}
              </span>
            </span>
          </span>
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
  // アイテム情報
  item: {
    type: Object,
    default: () => {}
  },
  // アイテムID
  itemId: {
    type: Number,
    default: 0
  }
});

/* ///////////////////////////////////
// emits
/////////////////////////////////// */

const emits = defineEmits(['clickCreater']);

/* ///////////////////////////////////
// const
/////////////////////////////////// */

const thumbnailName = Object.prototype.hasOwnProperty.call(props.item['@graph'][0], 'thumbnail')
  ? props.item['@graph'][0].thumbnail[0][0]
  : '';
const loading = ref(true);
const thumbnailPath = ref('/img/noimage_thumbnail.jpg');

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

onMounted(() => {
  if (thumbnailName) {
    try {
      $fetch(useAppConfig().wekoApi + '/records/' + props.itemId + '/files/' + thumbnailName, {
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
