<template>
  <div v-if="Object.keys(itemInfo).length">
    <hr class="border-miby-dark-gray" />

    <div class="detail__head flex">
      <!-- サムネイル -->
      <div class="detail__head-image h-44 w-32 flex justify-center items-center bg-neutral-300" style="width: 20%">
        <div
          v-if="loading"
          class="font-bold text-2xl text-white h-full flex justify-center items-center content-center">
          <span class="loading loading-bars loading-l" />
        </div>
        <img v-else :src="thumbnailPath" alt="Thumbnail" class="object-contain h-44 w-32" />
      </div>

      <div class="detail__head-text w-[80%]">
        <div class="flex flex-wrap mb-1.5 gap-2 md:gap-5 items-center">
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
        <a class="data-dtitle text-left text-18px">
          <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.title)">
            {{ itemInfo[appConf.roCrate.root.title][0] }}
          </span>
          <span v-else>{{ $t('notSet') }}</span>
        </a>

        <div class="text-left sm:flex mb-1">
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
            <span v-else class="mr-1 text-14px">[{{ $t('notSet') }}]</span>
            <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.authorName)" class="data-author">
              <span v-for="name in itemInfo[appConf.roCrate.root.authorName]" :key="name" class="tag-link">
                <a @click="emits('clickCreater')">
                  {{ name }}
                </a>
              </span>
            </span>
            <span v-else text-14px>{{ $t('notSet') }}</span>
          </p>
        </div>

        <div class="text-left sm:flex flex-wrap">
          <!-- 分野 -->
          <p class="data-note text-14px">
            {{ $t('field') + '：' }}
            <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.field)">
              {{ $t(itemInfo[appConf.roCrate.root.field][0]) }}
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
        <div class="text-left sm:flex flex-wrap">
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
              <span v-else class="text-14px">
                {{ $t('exist') + `（${getFileLength(itemInfo.mainEntity)}）` }}
              </span>
            </span>
          </p>
        </div>

        <!-- キーワード -->
        <div class="data-tags mt-1">
          <span v-if="itemInfo.hasOwnProperty(appConf.roCrate.root.keywords)">
            <span
              v-for="keyword in String(itemInfo[appConf.roCrate.root.keywords]).split(',')"
              :key="keyword"
              class="tag-link text-14px">
              <span class="hover:cursor-pointer">
                {{ keyword }}
              </span>
            </span>
          </span>
        </div>
      </div>
    </div>
    <div v-if="itemInfo.mainEntity.length < 1" class="detail__head-text open-file-button-area" />
    <div v-else class="detail__head-text open-file-button-area">
      <NuxtLink class="font-bold" to="" event="" @click="throughDblClick(`/files?number=${itemId}`)">
        <button
          v-if="local == 'ja'"
          class="min-[1022px]:block h-5 min-[1022px]:h-auto min-[1022px]:border min-[1022px]:py-1 pl-2 pr-2.5 rounded text-white open-file-list-button">
          {{ $t('fileList') }}
          <br />
          {{ $t('open') }}
        </button>
        <button
          v-else
          class="min-[1022px]:block h-5 min-[1022px]:h-auto min-[1022px]:border min-[1022px]:py-1 pl-2 pr-2.5 rounded text-white open-file-list-button">
          {{ $t('openFileList') }}
        </button>
      </NuxtLink>
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
const local = String(localStorage.getItem('locale') ?? 'ja');

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
  if (thumbnailName && !thumbnailName.includes('/')) {
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
      thumbnailPath.value = '/img/naturalScience-sample.png';
      // ライフサイエンス|Life Science
    } else if (field.includes('ライフサイエンス') || /Life\s?Science/.test(field)) {
      thumbnailPath.value = '/img/lifeScience-sample.png';
      // 情報通信|Informatics
    } else if (field.includes('情報通信') || field.includes('Informatics')) {
      thumbnailPath.value = '/img/informatics-sample.png';
      // 環境|Environmental science
    } else if (field.includes('環境') || /Environmental\s?science/.test(field)) {
      thumbnailPath.value = '/img/environmental-sample.png';
      // ナノテク・材料|Nanotechnology/Materials
    } else if (/ナノテク\s?・?\s?材料/.test(field) || /Nanotechnology\s?\/?\s?Materials/.test(field)) {
      thumbnailPath.value = '/img/nanotech-sample.png';
      // エネルギー|Energy Engineering
    } else if (field.includes('エネルギー') || /Energy\s?Engineering/.test(field)) {
      thumbnailPath.value = '/img/energy-sample.png';
      // ものづくり技術|Manufacturing Technology
    } else if (field.includes('ものづくり技術') || /Manufacturing\s?Technology/.test(field)) {
      thumbnailPath.value = '/img/manufacturing-sample.png';
      // 社会基盤|Social Infrastructure
    } else if (field.includes('社会基盤') || /Social\s?Infrastructure/.test(field)) {
      thumbnailPath.value = '/img/social-sample.png';
      // フロンティア|Frontier Technology
    } else if (field.includes('フロンティア') || /Frontier\s?Technology/.test(field)) {
      thumbnailPath.value = '/img/frontier-sample.png';
      // 人文・社会|Humanities & Social Sciences
    } else if (/人文\s?・?\s?社会/.test(field) || /Humanities\s?&?\s?Social\s?Sciences/.test(field)) {
      thumbnailPath.value = '/img/humanities-sample.png';
      // その他|Others
    } else if (field.includes('その他') || field.includes('Others')) {
      thumbnailPath.value = '/img/others-sample.png';
    }
  }
});
</script>
