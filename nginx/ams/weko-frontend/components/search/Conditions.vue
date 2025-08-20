<template>
  <div>
    <div class="w-full bg-miby-searchtags-blue p-2">
      <div class="flex flex-wrap" />
      <div class="flex flex-wrap justify-between items-center">
        <div class="flex flex-wrap gap-5 items-center mr-auto">
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
              <!-- <button
                :class="{ active: displayType == 'table' }"
                class="icons icon-display display2"
                @click="emits('clickDisplayType', 'table')" />
              <button
                :class="{ active: displayType == 'block' }"
                class="icons icon-display display3"
                @click="emits('clickDisplayType', 'block')" /> -->
            </div>
          </div>
          <!-- 並び順 -->
          <div
            v-if="displayType != 'table'"
            class="text-miby-black text-sm font-medium flex justify-center items-center">
            <span>
              {{ $t('displaySort') + '：' }}
            </span>
            <select
              id="sort-dropdown"
              v-model="sort"
              class="cursor-pointer border text-sm border-gray-300 rounded"
              @change="emits('clickSort', sort)">
              <option value="wtl" selected>
                {{ $t('titleOfDataset') }}
              </option>
              <option value="createdate">
                {{ $t('createdDate') }}
              </option>
              <option value="upd">
                {{ $t('updatedDate') }}
              </option>
              <option value="creator">
                {{ $t('nameOfDataCreator') }}
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
        <div class="flex ml-auto">
          <button
            class="min-[1022px]:block h-5 min-[1022px]:h-auto min-[1022px]:border min-[1022px]:py-1 pl-2 pr-2.5 rounded text-xs text-white bg-link-color whitespace-normal"
            style="max-width: 100%"
            @click="copySearchCondition">
            <p class="text-14px">
              {{ $t('search/Filter') }}
              <br />
              {{ $t('conditionCopy') }}
            </p>
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
let copyURL = '';

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/** 検索条件コピー機能 */
function copySearchCondition() {
  copyURL = '';
  const params = {
    q: props.conditions.keyword,
    search_type: props.conditions.type,
    page: props.conditions.currentPage,
    size: props.conditions.perPage,
    sort: props.conditions.order === 'asc' ? props.conditions.sort : '-' + props.conditions.sort
  };
  if (props.conditions.detail) {
    Object.assign(params, props.conditions.detail);
  }
  if (props.conditions.filter) {
    Object.assign(params, props.conditions.filter);
  }

  // paramsをクエリ文字列に変換
  const urlSearchParam = new URLSearchParams(params).toString();
  const hereURL = window.location.href.split('?')[0];
  copyURL = hereURL + '?' + urlSearchParam;

  // クリップボードに貼り付け
  navigator.clipboard.writeText(copyURL).then(
    () => {
      alert('Copy successful');
    },
    () => {
      alert('Copy failed');
    }
  );
}
</script>

<style scoped>
#sort-dropdown {
  appearance: none;
  background-image: url('/img/icon/icon_sort01.svg');
  background-size: 25px;
}
</style>
