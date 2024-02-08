<template>
  <div class="w-full">
    <div class="bg-miby-bg-gray">
      <div class="p-5">
        <div v-if="item" class="border-b-2 border-dashed border-miby-border-black pb-5">
          <div class="flex flex-wrap mb-1.5 gap-5 items-center">
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
              <span>
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
              <span>undefined</span>
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
          <NuxtLink class="data-title" :to="`/detail?sess=top&number=${item.id}`">
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
          <div class="flex flex-wrap">
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
const itemInfo = Object.prototype.hasOwnProperty.call(props.item, 'metadata')
  ? getContentById(props.item.metadata, './')
  : {};

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
