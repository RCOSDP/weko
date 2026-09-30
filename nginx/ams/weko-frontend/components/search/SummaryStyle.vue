<template>
  <div class="search-rows">
    <!-- サムネイル -->
    <div class="rows-image h-30 w-24 flex justify-center items-center bg-neutral-300">
      <div v-if="loading" class="font-bold text-2xl text-white h-full flex justify-center items-center content-center">
        <span class="loading loading-bars loading-l" />
      </div>
      <img v-else :src="thumbnailPath" alt="Thumbnail" class="object-contain h-28 w-24" />
    </div>
    <div class="rows-detail">
      <div class="flex flex-nowrap mb-1.5 gap-5 items-center">
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
        class="data-title whitespace-normal text-18px"
        to=""
        event=""
        style="cursor: pointer"
        @click="throughDblClick(`${appConf.amsPath ?? ''}/detail?sess=search&number=${item.id}`)">
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
      <div class="flex flex-nowrap">
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
      <div class="flex flex-nowrap">
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
            <span v-if="getFileLength(itemInfo.mainEntity) < 1" class="text-14px">
              {{ $t('unexist') }}
            </span>
            <NuxtLink
              v-else
              class="underline text-miby-link-blue text-14px cursor-pointer"
              to=""
              event=""
              @click="throughDblClick(`${appConf.amsPath ?? ''}/files?number=${item.id}`)">
              {{ $t('exist') + `（${getFileLength(itemInfo.mainEntity)}）` }}
            </NuxtLink>
          </span>
        </p>
      </div>
    </div>
    <!-- <div class="grid grid-rows-4 grid-flow-col gap-0"> -->
    <!-- お気に入り -->
    <!-- <div class="row-span-1 align-top text-right pr-2">
        <label class="swap swap-rotate">
          <input type="checkbox" class="hidden" />
          <div class="swap-on w-7 rounded"><img :src="`${useAppConfig().amsImage ?? '/img'}/icon/icon_star-fill.svg`" /></div>
          <div class="swap-off w-7 rounded"><img :src="`${useAppConfig().amsImage ?? '/img'}/icon/icon_star.svg`" /></div>
        </label>
      </div> -->
    <!-- 閲覧数 -->
    <!-- <div class="row-span-3 flex justify-end items-end">
        <div class="data-note flex">
          <img :src="`${useAppConfig().amsImage ?? '/img'}/icon/icon_star-fill-black.svg`" alt="My List" class="mr-1" />
          <a>9,999</a>
        </div>
        <div class="data-note flex ml-1">
          <img :src="`${useAppConfig().amsImage ?? '/img'}/icon/icon_eye-fill.svg`" alt="Views" class="mr-1" />
          <a>9,999,999,999</a>
        </div>
      </div> -->
    <!-- </div> -->
    <!-- </div> -->
    <!-- </div> -->
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
const thumbnailPath = ref(appConf.amsImage + '/noimage_thumbnail.jpg');

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
  // 表示するサムネイルを判断する
  if (thumbnailName && !thumbnailName.includes('/')) {
    try {
      $fetch(appConf.wekoApi + '/records/' + props.item.id + '/files/' + thumbnailName, {
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
            const blob = new Blob([response._data], {
              type: response._data.type
            });
            thumbnailPath.value = window.URL.createObjectURL(blob);
          } else {
            _fieldThumbnail();
          }
          loading.value = false;
        }
      });
    } catch (error) {
      loading.value = false;
    }
  } else if (Object.prototype.hasOwnProperty.call(itemInfo, appConf.roCrate.root.field)) {
    _fieldThumbnail();
    loading.value = false;
  } else {
    loading.value = false;
  }

  // 登録されたデータセットの分野ごとにサムネイルを設定
  function _fieldThumbnail() {
    const field = itemInfo[appConf.roCrate.root.field][0];
    // 自然科学一般|Natural Science
    if (field.includes('自然科学一般') || /Natural\s?Science/.test(field)) {
      thumbnailPath.value = appConf.amsImage + '/naturalScience-sample.png';
      // ライフサイエンス|Life Science
    } else if (field.includes('ライフサイエンス') || /Life\s?Science/.test(field)) {
      thumbnailPath.value = appConf.amsImage + '/lifeScience-sample.png';
      // 情報通信|Informatics
    } else if (field.includes('情報通信') || field.includes('Informatics')) {
      thumbnailPath.value = appConf.amsImage + '/informatics-sample.png';
      // 環境|Environmental science
    } else if (field.includes('環境') || /Environmental\s?science/.test(field)) {
      thumbnailPath.value = appConf.amsImage + '/environmental-sample.png';
      // ナノテク・材料|Nanotechnology/Materials
    } else if (/ナノテク\s?・?\s?材料/.test(field) || /Nanotechnology\s?\/?\s?Materials/.test(field)) {
      thumbnailPath.value = appConf.amsImage + '/nanotech-sample.png';
      // エネルギー|Energy Engineering
    } else if (field.includes('エネルギー') || /Energy\s?Engineering/.test(field)) {
      thumbnailPath.value = appConf.amsImage + '/energy-sample.png';
      // ものづくり技術|Manufacturing Technology
    } else if (field.includes('ものづくり技術') || /Manufacturing\s?Technology/.test(field)) {
      thumbnailPath.value = appConf.amsImage + '/manufacturing-sample.png';
      // 社会基盤|Social Infrastructure
    } else if (field.includes('社会基盤') || /Social\s?Infrastructure/.test(field)) {
      thumbnailPath.value = appConf.amsImage + '/social-sample.png';
      // フロンティア|Frontier Technology
    } else if (field.includes('フロンティア') || /Frontier\s?Technology/.test(field)) {
      thumbnailPath.value = appConf.amsImage + '/frontier-sample.png';
      // 人文・社会|Humanities & Social Sciences
    } else if (/人文\s?・?\s?社会/.test(field) || /Humanities\s?&?\s?Social\s?Sciences/.test(field)) {
      thumbnailPath.value = appConf.amsImage + '/humanities-sample.png';
      // その他|Others
    } else if (field.includes('その他') || field.includes('Others')) {
      thumbnailPath.value = appConf.amsImage + '/others-sample.png';
    }
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
