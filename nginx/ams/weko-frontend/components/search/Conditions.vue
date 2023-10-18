<template>
  <div>
    <div class="w-full bg-miby-searchtags-blue p-5">
      <div class="mb-2.5 flex flex-wrap">
        <!-- 公開区分 -->
        <p class="text-sm text-miby-dark-gray">
          {{ '[' + $t('publicRange') + ']' }}
          <span class="ml-px mr-2 text-miby-black">
            {{ detailConditions.publicRange?.length ? detailConditions.publicRange?.join(', ') : $t('unspecified') }}
          </span>
        </p>
        <!-- ダウンロード区分 -->
        <p class="text-sm text-miby-dark-gray">
          {{ '[' + $t('downloadRange') + ']' }}
          <span class="ml-px mr-2 text-miby-black">
            {{
              detailConditions.downloadRange?.length ? detailConditions.downloadRange?.join(', ') : $t('unspecified')
            }}
          </span>
        </p>
        <!-- タイトル -->
        <p class="text-sm text-miby-dark-gray">
          {{ '[' + $t('title') + ']' }}
          <span class="ml-px mr-2 text-miby-black">
            {{ conditions?.text && conditions?.text[3] != '' ? conditions?.text[3] : $t('unspecified') }}
          </span>
        </p>
        <!-- 分野 -->
        <p class="text-sm text-miby-dark-gray">
          {{ '[' + $t('field') + ']' }}
          <span class="ml-px mr-2 text-miby-black">
            {{ detailConditions.field?.length ? detailConditions.field?.join(', ') : $t('unspecified') }}
          </span>
        </p>
        <!-- 掲載日 -->
        <p class="text-sm text-miby-dark-gray">
          {{ '[' + $t('publishDate') + ']' }}
          <span class="ml-px mr-2 text-miby-black">
            {{ conditions?.date ? formatDate(conditions?.date[0]) : $t('unspecified') }} -
            {{ conditions?.date ? formatDate(conditions?.date[1]) : $t('unspecified') }}
          </span>
        </p>
        <!-- 更新日 -->
        <p class="text-sm text-miby-dark-gray">
          {{ '[' + $t('updatedDate') + ']' }}
          <span class="ml-px mr-2 text-miby-black">
            {{ conditions?.date ? formatDate(conditions?.date[0]) : $t('unspecified') }} -
            {{ conditions?.date ? formatDate(conditions?.date[1]) : $t('unspecified') }}
          </span>
        </p>
        <!-- 作成者 -->
        <p class="text-sm text-miby-dark-gray">
          {{ '[' + $t('creater') + ']' }}
          <span class="ml-px mr-2 text-miby-black">
            {{ conditions?.text && conditions?.text[7] != '' ? conditions?.text[7] : $t('unspecified') }}
          </span>
        </p>
        <!-- ヒト/動物/その他 -->
        <p class="text-sm text-miby-dark-gray">
          {{ '[' + $t('classification') + ']' }}
          <span class="ml-px mr-2 text-miby-black">
            {{ conditions?.text && conditions?.text[8] != '' ? conditions?.text[8] : $t('unspecified') }}
          </span>
        </p>
        <!-- リポジトリ -->
        <p class="text-sm text-miby-dark-gray">
          {{ '[' + $t('repository') + ']' }}
          <span class="ml-px mr-2 text-miby-black">
            {{ conditions?.text && conditions?.text[9] != '' ? conditions?.text[9] : $t('unspecified') }}
          </span>
        </p>
        <!-- 表示件数 -->
        <p class="text-sm text-miby-dark-gray">
          {{ '[' + $t('displayTotal') + ']' }}
          <span class="ml-px mr-2 text-miby-black">
            {{ perPage }}
          </span>
        </p>
      </div>
      <div class="flex flex-wrap justify-between items-center">
        <div class="flex flex-wrap gap-5 items-center">
          <!-- 表示件数（選択） -->
          <div class="text-miby-black text-sm font-medium flex items-center">
            <span>
              {{ $t('displayTotal') + '：' }}
            </span>
            <select
              v-model="perPage"
              class="cursor-pointer bg-white border text-sm border-gray-300 rounded text-miby-black block"
              @change="emits('clickPerPage', perPage)">
              <option value="20" selected>20</option>
              <option value="40">40</option>
              <option value="60">60</option>
              <option value="80">80</option>
              <option value="100">100</option>
              <option value="150">150</option>
              <option value="200">200</option>
            </select>
          </div>
          <!-- 表示形式 -->
          <div class="text-miby-black text-sm font-medium">
            <span>
              {{ $t('displayType') + '：' }}
            </span>
            <div class="inline-flex gap-x-0.5">
              <button
                :class="{ active: displayType == 'summary' }"
                class="icons icon-display display1"
                @click="emits('clickDisplayType', 'summary')" />
              <button
                :class="{ active: displayType == 'table' }"
                class="icons icon-display display2"
                @click="emits('clickDisplayType', 'table')" />
              <button
                :class="{ active: displayType == 'block' }"
                class="icons icon-display display3"
                @click="emits('clickDisplayType', 'block')" />
            </div>
          </div>
          <!-- 並び順 -->
          <div
            v-if="displayType != 'table'"
            class="text-miby-black text-sm font-medium flex justify-center items-center mr-10">
            <span>
              {{ $t('displaySort') + '：' }}
            </span>
            <select
              id="sort-dropdown"
              v-model="sort"
              class="cursor-pointer border text-sm border-gray-300 rounded"
              @change="emits('clickSort', sort)">
              <option value="wtl" selected>
                {{ $t('title') }}
              </option>
              <option value="creator">
                {{ $t('creater') }}
              </option>
              <option value="publish_date">
                {{ $t('publishDate') }}
              </option>
              <option value="createdate">
                {{ $t('createdDate') }}
              </option>
              <option value="upd">
                {{ $t('updatedDate') }}
              </option>
            </select>
            <!-- 昇順/降順 -->
            <div class="text-black ml-2">
              <div class="flex-col">
                <div class="mb-1">
                  <label class="radio cursor-pointer">
                    <input
                      id="asc"
                      v-model="order"
                      value="asc"
                      type="radio"
                      name="form-type"
                      @change="emits('clickOrder', order)" />
                    <span class="text-sm radio-label" for="type1" checked>
                      {{ $t('asc') }}
                    </span>
                  </label>
                </div>
                <div>
                  <label class="radio cursor-pointer">
                    <input
                      id="desc"
                      v-model="order"
                      value="desc"
                      type="radio"
                      name="form-type"
                      @change="emits('clickOrder', order)" />
                    <span class="text-sm radio-label" for="type2">
                      {{ $t('desc') }}
                    </span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="flex gap-2.5 py-5 md:py-0">
          <!-- フィルター -->
          <button class="btn-modal block cursor-pointer" data-target="Filter" @click="emits('clickFilter')">
            <img src="/img/btn/btn-filter.svg" alt="Filter" />
          </button>
          <!-- 項目表示 -->
          <button
            v-if="displayType == 'table'"
            class="btn-modal block cursor-pointer"
            data-target="DisplayItem"
            @click="emits('displayItem')">
            <img src="/img/btn/btn-display-item.svg" alt="Item" />
          </button>
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
  // 表示形式
  displayType: {
    type: String,
    default: ''
  },
  // 検索条件
  conditions: {
    type: Object,
    default: () => {}
  },
  // 詳細検索条件
  detailConditions: {
    type: Object,
    default: () => {}
  }
});

/* ///////////////////////////////////
// emits
/////////////////////////////////// */

const emits = defineEmits([
  'clickPerPage',
  'clickDisplayType',
  'clickSort',
  'clickOrder',
  'clickFilter',
  'displayItem'
]);

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const perPage = ref(props.conditions.perPage ?? '20');
const sort = ref(props.conditions.sort ?? 'wtl');
const order = ref(props.conditions.order ?? 'asc');

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * 日付の整形
 * @param date 日付
 */
function formatDate(date: string) {
  const objDate = new Date(date);
  const day = objDate.getDate();
  const month = objDate.getMonth() + 1;
  const year = objDate.getFullYear();

  return `${year}/${month}/${day}`;
}
</script>

<style scoped>
#sort-dropdown {
  appearance: none;
  background-image: url('/img/icon/icon_sort01.svg');
  background-size: 20%;
}
</style>
