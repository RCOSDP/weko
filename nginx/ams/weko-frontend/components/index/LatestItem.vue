<template>
  <div class="w-full">
    <div class="bg-miby-bg-gray">
      <div class="p-5">
        <div v-if="item" class="border-b-2 border-dashed border-miby-border-black pb-5">
          <div class="flex flex-wrap mb-1.5 gap-5 items-center">
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
              <span>
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
              <span>undefined</span>
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
          <NuxtLink class="data-title" :to="`/detail?sess=top&number=${item.id}`">
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
          <div class="flex flex-wrap">
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
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
/* ///////////////////////////////////
// props
/////////////////////////////////// */

defineProps({
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
</script>

<style scoped lang="scss">
.data-title {
  @apply text-miby-black;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}
.data-note {
  @apply mr-4 font-medium text-sm;
  span {
    font-weight: normal;
  }
}
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
