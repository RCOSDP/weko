<template>
  <div v-if="Object.keys(itemInfo).length">
    <hr class="border-miby-dark-gray" />
    <div class="detail__head">
      <!-- サムネイル -->
      <div class="detail__head-image h-44 w-32 flex justify-center items-center bg-neutral-300">
        <div
          v-if="loading"
          class="font-bold text-2xl text-white h-full flex justify-center items-center content-center">
          <span class="loading loading-bars loading-l" />
        </div>
        <img v-else :src="thumbnailPath" alt="Thumbnail" class="object-contain h-44 w-32" />
      </div>
      <div class="detail__head-text">
        <div class="flex flex-wrap mb-1.5 gap-2 md:gap-5 items-center">
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
        <a class="data-dtitle text-left">
          <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.title)">
            {{ itemInfo[appConf.roCrate.root.title][0] }}
          </span>
          <span v-else>undefined</span>
        </a>
        <div class="text-left sm:flex mb-1">
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
        <div class="text-left sm:flex flex-wrap">
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
              <NuxtLink v-else class="underline text-miby-link-blue" :to="`/files?number=${itemId}`">
                {{ $t('exist') + `（${getFileLength(itemInfo.mainEntity)}）` }}
              </NuxtLink>
            </span>
          </p>
        </div>
        <!-- キーワード -->
        <div class="data-tags mt-1">
          <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.keywords)">
            <span
              v-for="keyword in String(itemInfo[appConf.roCrate.root.keywords]).split(',')"
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
const itemInfo = Object.prototype.hasOwnProperty.call(props.item, 'rocrate')
  ? getContentById(props.item.rocrate, './')
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
    const value = getContentById(props.item.rocrate, element['@id']);
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
  if (thumbnailName && thumbnailName.indexOf('/') < 0) {
    try {
      $fetch(appConf.wekoApi + '/records/' + props.itemId + '/files/' + thumbnailName, {
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
