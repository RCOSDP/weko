<template>
  <dialog :class="[modalShowFlag ? 'visible' : 'invisible']" class="bg-black" @click="closeModal">
    <div class="modal-center z-50" @click.stop>
      <div class="bg-miby-light-blue flex flex-row">
        <div class="basis-1/6" />
        <!-- タイトル -->
        <div class="basis-4/6">
          <p class="text-white leading-[43px] text-center font-medium">{{ $t('filter') }}</p>
        </div>
        <!-- 閉じるボタン -->
        <div class="basis-1/6 flex text-end justify-end pr-3">
          <button type="button" class="btn-close">
            <img src="/img/btn/btn-close.svg" alt="×" @click="closeModal" />
          </button>
        </div>
      </div>
      <form
        v-if="modalShowFlag"
        class="mt-[-3px] pt-8 pb-8 md:mt-0 md:border-0 rounded-b-md px-2.5"
        @submit.prevent="filter">
        <div class="modalForm h-full">
          <TransitionGroup name="list" tag="ul" class="h-full">
            <div v-for="column in filterColumn" :key="column.id">
              <!-- 項名 -->
              <div class="mb-2.5 flex text-miby-black font-medium">
                <span v-if="column.i18n">
                  {{ $t(column.i18n) }}
                </span>
                <span v-else>
                  {{ column.comment }}
                </span>
              </div>
              <!--入力フォーム形式 -->
              <div v-if="column.type == 'text'" class="mb-7 ml-5">
                <input v-model="column.data" type="text" class="rounded h-8 w-full" />
              </div>
              <!-- チェックボックス形式 -->
              <div v-else-if="column.type == 'checkbox'" class="flex flex-wrap mb-7 ml-5 items-center">
                <div v-for="item in column.data" :key="item.id">
                  <label class="flex items-center text-sm checkbox-label mr-5 w-32">
                    <input v-model="item.value" type="checkbox" class="mr-1" />
                    <span v-if="item.i18n">
                      {{ $t(item.i18n) }}
                    </span>
                    <span v-else>
                      {{ item.comment }}
                    </span>
                  </label>
                </div>
              </div>
              <!-- 日付形式 -->
              <div
                v-else-if="column.type == 'date'"
                class="mb-7 ml-5 flex-col flex-wrap md:flex-nowrap items-center md:justify-start max-w-[345px]">
                <VueDatePicker
                  v-model="column.data"
                  format="yyyy/MM/dd"
                  model-type="yyyy-MM-dd"
                  :enable-time-picker="false"
                  range />
              </div>
            </div>
          </TransitionGroup>
        </div>
        <!-- 検索/クリア -->
        <div class="flex items-center justify-center pt-5 gap-4">
          <button
            type="button"
            class="text-miby-black text-sm text-center font-medium border hover:bg-gray-200 border-miby-black py-1.5 px-5 block min-w-[96px] rounded"
            @click="clear">
            {{ $t('clear') }}
          </button>
          <button
            type="submit"
            class="text-white text-sm text-center bg-orange-400 hover:bg-miby-orange font-medium py-1.5 px-5 block min-w-[96px] rounded">
            {{ $t('filtering') }}
          </button>
        </div>
      </form>
    </div>
    <div class="backdrop" />
  </dialog>
</template>

<script lang="ts" setup>
import VueDatePicker from '@vuepic/vue-datepicker';

import FilterColumn from '~/assets/data/filesFilter.json';

/* ///////////////////////////////////
// expose
/////////////////////////////////// */

defineExpose({
  openModal
});

/* ///////////////////////////////////
// emits
/////////////////////////////////// */

const emits = defineEmits(['filtering']);

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const modalShowFlag = ref(false);
const filterColumn = ref(JSON.parse(JSON.stringify(FilterColumn)));

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * フィルタリング実行
 */
function filter() {
  emits('filtering', filterColumn.value);
  closeModal();
}

/**
 * フィルタリング条件の初期化
 */
function clear() {
  filterColumn.value = JSON.parse(JSON.stringify(FilterColumn));
}

/**
 * モーダル表示
 */
function openModal() {
  modalShowFlag.value = true;
  document.body.classList.add('overflow-hidden');
}

/**
 * モーダル非表示
 */
function closeModal() {
  modalShowFlag.value = false;
  document.body.classList.remove('overflow-hidden');
}
</script>

<style scoped lang="scss">
.border-collapse {
  th {
    @apply border border-miby-thin-gray text-center align-middle;
    @apply py-1 font-medium;
  }
  td {
    @apply border border-miby-thin-gray text-center align-middle;
    @apply px-2 pt-5 pb-7;
  }
}
</style>
