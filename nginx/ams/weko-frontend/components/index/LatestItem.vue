<template>
  <div class="w-full">
    <div class="bg-miby-bg-gray">
      <div class="p-5">
        <div v-if="item" class="border-b-2 border-dashed border-miby-border-black pb-5">
          <div class="flex flex-wrap mb-1.5 gap-5 items-center">
            <!-- 公開区分 -->
            <p
              v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.accessMode)"
              class="text-14px"
              :class="[
                itemInfo[appConf.roCrate.root.accessMode][0] === appConf.roCrate.selector.accessMode.public
                  ? 'icons-type icon-public'
                  : itemInfo[appConf.roCrate.root.accessMode][0] === appConf.roCrate.selector.accessMode.group
                  ? 'icons-type icon-group'
                  : itemInfo[appConf.roCrate.root.accessMode][0] === appConf.roCrate.selector.accessMode.member
                  ? 'icons-type icon-member'
                  : itemInfo[appConf.roCrate.root.accessMode][0] === appConf.roCrate.selector.accessMode.private
                  ? 'icons-type icon-private'
                  : 'icons-type icon-public'
              ]">
              <span>
                {{
                  itemInfo[appConf.roCrate.root.accessMode][0] === appConf.roCrate.selector.accessMode.public
                    ? $t('open access')
                    : itemInfo[appConf.roCrate.root.accessMode][0] === appConf.roCrate.selector.accessMode.group
                    ? $t('restricted access')
                    : itemInfo[appConf.roCrate.root.accessMode][0] === appConf.roCrate.selector.accessMode.member
                    ? $t('metadata only access')
                    : itemInfo[appConf.roCrate.root.accessMode][0] === appConf.roCrate.selector.accessMode.private
                    ? $t('embargoed access')
                    : 'undefined'
                }}
              </span>
            </p>
            <p v-else class="icons-type icon-public text-14px">
              <span class="text-14px">{{ $t('notSet') }}</span>
            </p>
            <!-- 公開日 -->
            <p class="date-upload icons icon-publish">
              <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.releaseDate)" class="text-14px">
                {{ itemInfo[appConf.roCrate.root.releaseDate][0] }}
              </span>
              <span v-else class="text-14px">{{ $t('notSet') }}</span>
            </p>
            <!-- 更新日 -->
            <p class="date-update icons icon-update">
              <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.updateDate)" class="text-14px">
                {{
                  typeof itemInfo[appConf.roCrate.root.updateDate] == 'object'
                    ? itemInfo[appConf.roCrate.root.updateDate][0]
                    : 'undefined'
                }}
              </span>
              <span v-else class="text-14px">{{ $t('notSet') }}</span>
            </p>
          </div>
          <!-- タイトル -->
          <NuxtLink
            class="data-title text-18px"
            to=""
            event=""
            style="cursor: pointer"
            @click="throughDblClick(`/detail?sess=top&number=${item.id}`)">
            <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.title)">
              {{ itemInfo[appConf.roCrate.root.title][0] }}
            </span>
            <span v-else>{{ $t('notSet') }}</span>
          </NuxtLink>
          <div class="flex mb-1">
            <!-- 作成者 -->
            <p class="data-note author text-14px">
              {{ $t('creater') + '：' }}
              <span v-if="itemInfo[appConf.roCrate.root.authorAffiliation]" class="data-author mr-1 text-14px">
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
              <span v-else class="mr-1 text-14px">[ {{ $t('notSet') }} ]</span>
              <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.authorName)" class="data-author">
                <span v-for="name in itemInfo[appConf.roCrate.root.authorName]" :key="name" class="tag-link">
                  <a @click="emits('clickCreater')">
                    {{ name }}
                  </a>
                </span>
              </span>
              <span v-else class="text-14px">{{ $t('notSet') }}</span>
            </p>
          </div>
          <div class="flex flex-wrap">
            <!-- 分野 -->
            <p class="data-note text-14px">
              {{ $t('field') + '：' }}
              <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.field)">
                {{ itemInfo[appConf.roCrate.root.field][0] }}
              </span>
              <span v-else class="text-14px">{{ $t('notSet') }}</span>
            </p>
            <!-- ヒト/動物/その他 -->
            <p class="data-note text-14px">
              {{ $t('classification') + '：' }}
              <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.target)" class="font-medium">
                {{ itemInfo[appConf.roCrate.root.target][0] }}
              </span>
              <span v-else class="text-14px">{{ $t('notSet') }}</span>
            </p>
          </div>
          <div class="flex flex-wrap">
            <!-- アクセス権 -->
            <p class="data-note access-type text-14px">
              {{ $t('authority') + '：' }}
              <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.accessMode)" class="text-14px">
                {{ itemInfo[appConf.roCrate.root.accessMode][0] }}
              </span>
              <span v-else class="text-14px">{{ $t('notSet') }}</span>
            </p>
            <!-- ファイル -->
            <p class="data-note text-14px">
              {{ $t('file') + '：' }}
              <span class="font-medium">
                <span v-if="itemInfo.mainEntity.length < 1" class="text-14px">
                  {{ $t('unexist') }}
                </span>
                <NuxtLink
                  v-else
                  class="underline text-miby-link-blue text-14px cursor-pointer"
                  to=""
                  event=""
                  @click="throughDblClick(`/files?number=${item.id}`)">
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

/** ファイル一覧画面からアイテム詳細画面へ戻るためのURL取得準備 */
function setURL() {
  sessionStorage.removeItem('url');
  sessionStorage.setItem('url', window.location.href);
}

/**
 * ダブルクリックを制御する
 */
function throughDblClick(route: any) {
  if (location.pathname + location.search !== route) {
    navigateTo(route);
  }
}

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */
onMounted(() => {
  setURL();
});
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
