<template>
  <div class="w-full">
    <div class="bg-miby-bg-gray">
      <div class="p-5">
        <div v-if="item" class="border-b-2 border-dashed border-miby-border-black pb-5">
          <div class="flex flex-wrap mb-1.5 gap-5 items-center">
            <!-- 公開区分 -->
            <p
              v-if="itemInfo.hasOwnProperty(appConf.roCrate.info.releaseRange)"
              :class="[
                itemInfo[appConf.roCrate.info.releaseRange][0] === appConf.roCrate.selector.releaseRange.public
                  ? 'icons-type icon-published'
                  : itemInfo[appConf.roCrate.info.releaseRange][0] === appConf.roCrate.selector.releaseRange.shared
                  ? 'icons-type icon-group'
                  : itemInfo[appConf.roCrate.info.releaseRange][0] === appConf.roCrate.selector.releaseRange.private
                  ? 'icons-type icon-private'
                  : itemInfo[appConf.roCrate.info.releaseRange][0] === appConf.roCrate.selector.releaseRange.unshared
                  ? 'icons-type icon-limited'
                  : 'icons-type icon-published'
              ]">
              <span>
                {{
                  itemInfo[appConf.roCrate.info.releaseRange][0] === appConf.roCrate.selector.releaseRange.public
                    ? $t('openPublic')
                    : itemInfo[appConf.roCrate.info.releaseRange][0] === appConf.roCrate.selector.releaseRange.shared
                    ? $t('openGroup')
                    : itemInfo[appConf.roCrate.info.releaseRange][0] === appConf.roCrate.selector.releaseRange.private
                    ? $t('openPrivate')
                    : itemInfo[appConf.roCrate.info.releaseRange][0] === appConf.roCrate.selector.releaseRange.unshared
                    ? $t('openRestricted')
                    : 'undefined'
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
          <NuxtLink class="data-title" :to="`/detail?sess=top&number=${item.id}`">
            {{ itemInfo[appConf.roCrate.info.title][0] }}
          </NuxtLink>
          <div class="flex mb-1">
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
          <div class="flex flex-wrap">
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
                <NuxtLink v-else class="underline text-miby-link-blue" :to="`/files?number=${item.id}`">
                  {{ $t('exist') + `（${itemInfo.mainEntity.length}）` }}
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
const itemInfo = getContentById(props.item.metadata, './');
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
