<template>
  <div>
    <div class="w-full bg-miby-searchtags-blue p-5">
      <div class="mb-2.5 flex flex-wrap">
        <!-- 検索条件 -->
        <div v-for="column in DetailColumn" :key="column.id">
          <p class="text-sm text-miby-dark-gray">
            {{ '[' + $t(column.i18n) + ']' }}
            <span class="ml-px mr-2 text-miby-black">
              {{ formatConditionsValue(column) ?? $t('unspecified') }}
            </span>
          </p>
        </div>
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
          <!-- <button class="btn-modal block cursor-pointer" data-target="Filter" @click="emits('clickFilter')">
            <img src="/img/btn/btn-filter.svg" alt="Filter" />
          </button> -->
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
import { useI18n } from 'vue-i18n';

import DetailColumn from '~/assets/data/detailSearch.json';

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

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * 検索条件に表示する値を整形
 * @param column 検索条件オブジェクト
 */
function formatConditionsValue(column: any) {
  if (column.type === 'text') {
    return props.conditions.detail[column.query] === '' ? null : props.conditions.detail[column.query];
  } else if (column.type === 'checkbox') {
    const valueList: Array<string> = [];
    // 設定された検索条件値があるか判定
    if (props.conditions.detail[column.query]) {
      // カンマ区切りの文字列を配列にする
      for (const val of String(props.conditions.detail[column.query]).split(',')) {
        // クエリ用値から表示用値に読み替え
        for (const data of Array.from(column.data ?? [])) {
          // @ts-ignore
          if (data.query === val) {
            // @ts-ignore
            valueList.push(data.comment);
          }
        }
      }
      return valueList.join(', ');
    } else {
      return null;
    }
  } else if (column.type === 'date') {
    const valueList: Array<string> = [];
    const from = props.conditions.detail[column.queryFrom];
    const to = props.conditions.detail[column.queryTo];
    let result = null;
    if (column.checkbox) {
      for (const val of String(props.conditions.detail[column.query]).split(',')) {
        for (const data of Array.from(column.checkbox ?? [])) {
          // @ts-ignore
          if (data.query === val) {
            // @ts-ignore
            valueList.push(useI18n().t(data.name));
          }
        }
      }
      if (valueList.length) {
        result = valueList.join(', ') + ': ';
      }
    }
    if (from) {
      result = (result ?? '') + formatDate(from) + ' - ' + formatDate(to);
      return result;
    } else {
      return result;
    }
  }
  return null;
}

/**
 * 8桁文字列を日付に変換
 * @param date 日付
 */
function formatDate(date: string) {
  if (!date) {
    return '';
  }
  const year = date.slice(0, 4);
  const month = date.slice(4, 6);
  const day = date.slice(6, 8);
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
