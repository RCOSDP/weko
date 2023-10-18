<template>
  <div v-if="Object.keys(itemInfo).length">
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
            v-if="itemInfo.hasOwnProperty(appConf.roCrate.info.releaseRange)"
            :class="[
              itemInfo[appConf.roCrate.info.releaseRange][0] === 'Public'
                ? 'icons-type icon-published'
                : itemInfo[appConf.roCrate.info.releaseRange][0] === 'Shared'
                ? 'icons-type icon-group'
                : itemInfo[appConf.roCrate.info.releaseRange][0] === 'Private'
                ? 'icons-type icon-private'
                : itemInfo[appConf.roCrate.info.releaseRange][0] === 'Unshared'
                ? 'icons-type icon-limited'
                : ''
            ]">
            <span>
              {{
                itemInfo[appConf.roCrate.info.releaseRange][0] === 'Public'
                  ? $t('openPublic')
                  : itemInfo[appConf.roCrate.info.releaseRange][0] === 'Shared'
                  ? $t('openGroup')
                  : itemInfo[appConf.roCrate.info.releaseRange][0] === 'Private'
                  ? $t('openPrivate')
                  : itemInfo[appConf.roCrate.info.releaseRange][0] === 'Unshared'
                  ? $t('openRestricted')
                  : itemInfo[appConf.roCrate.info.releaseRange][0]
              }}
            </span>
          </p>
          <p v-else class="icons-type icon-published">
            <span>undefined</span>
          </p>
          <!-- 公開日 -->
          <p class="date-upload icons icon-publish">
            <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.info.reelaseDate)">
              {{ itemInfo[appConf.roCrate.info.reelaseDate][0] }}
            </span>
            <span v-else>undefined</span>
          </p>
          <!-- 更新日 -->
          <p class="date-update icons icon-update">
            <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.info.updateDate)">
              {{
                typeof itemInfo[appConf.roCrate.info.updateDate] == 'object'
                  ? itemInfo[appConf.roCrate.info.updateDate][0]
                  : 'undefined'
              }}
            </span>
            <span v-else>undefined</span>
          </p>
        </div>
        <!-- タイトル -->
        <a class="data-dtitle text-left">
          {{ itemInfo[appConf.roCrate.info.title][0] }}
        </a>
        <div class="text-left sm:flex mb-1">
          <!-- 分野 -->
          <p class="data-note">
            {{ $t('field') + '：' }}
            <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.info.field)">
              {{ itemInfo[appConf.roCrate.info.field][0] }}
            </span>
            <span v-else>undefined</span>
          </p>
          <!-- 作成者 -->
          <p class="data-note author">
            {{ $t('creater') + '：' }}
            <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.info.author)">
              <a>
                {{
                  itemInfo[appConf.roCrate.info.author][1]
                    ? `[${itemInfo[appConf.roCrate.info.author][1] ?? 'undefined'}] `
                    : 'undefined'
                }}
              </a>
              <a class="text-miby-link-blue underline cursor-pointer" @click="emits('clickCreater')">
                {{ itemInfo[appConf.roCrate.info.author][0] ?? '' }}
              </a>
            </span>
          </p>
        </div>
        <div class="text-left sm:flex flex-wrap">
          <!-- ヒト/動物/その他 -->
          <p class="data-note">
            {{ $t('classification') + '：' }}
            <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.info.target)" class="font-medium">
              {{ itemInfo[appConf.roCrate.info.target][0] }}
            </span>
            <span v-else>undefined</span>
          </p>
          <!-- アクセス権 -->
          <p class="data-note access-type">
            {{ $t('authority') + '：' }}
            <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.info.accessMode)">
              {{ itemInfo[appConf.roCrate.info.accessMode][0] }}
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
              <NuxtLink v-else class="underline text-miby-link-blue" :to="`/files?number=${itemId}`">
                {{ $t('exist') + `（${itemInfo.mainEntity.length}）` }}
              </NuxtLink>
            </span>
          </p>
        </div>
        <!-- キーワード -->
        <div class="data-tags mt-1">
          <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.info.keywords)">
            <span
              v-for="keyword in String(itemInfo[appConf.roCrate.info.keywords]).split(',')"
              :key="keyword"
              class="tag-link">
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

const appConf = useAppConfig();
const itemInfo = getContentById(props.item.rocrate, './');
const thumbnailName = Object.prototype.hasOwnProperty.call(itemInfo, appConf.roCrate.info.thumbnail)
  ? itemInfo[appConf.roCrate.info.thumbnail][0][0]
  : '';
const loading = ref(true);
const thumbnailPath = ref('/img/noimage_thumbnail.jpg');

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

onMounted(() => {
  if (thumbnailName) {
    try {
      $fetch(appConf.wekoApi + '/records/' + props.itemId + '/files/' + thumbnailName, {
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
