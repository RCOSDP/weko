<script setup>
import VueDatePicker from "@vuepic/vue-datepicker";
import "@vuepic/vue-datepicker/dist/main.css";
import { computed, ref, watchEffect, onMounted, reactive } from "vue";
import { onClickOutside } from "@vueuse/core";
import searchColumns from "../../data/data-search.json";
import ButtonClose from "/images/btn/btn-close.svg";

import FormDate from "../Form/FormDate.vue";

const props = defineProps({
  isFormModalShow: { type: Boolean, required: true, default: "" },
});
const onCloseFormModal = () => {
  props.isFormModalShow.value = false;
};
const emit = defineEmits(["update:isFormModalShow", 'close-modal']);

watchEffect(() => {
  // emit("update:isFormModalShow", onCloseFormModal());
});

/**
 * 初期表示検索項目用
 */
const setFormColumns = computed(() => {
  const columns = [];
  searchColumns.forEach((column) => {
    if (column.default) {
      columns.push(column);
    }
  });
  return columns;
});

/**
 * 追加項目セレクトボックス用
 */
const setAddColumns = computed(() => {
  const addColumns = [];
  searchColumns.forEach((column) => {
    if (!column.default) {
      addColumns.push(column);
    }
  });
  return addColumns;
});

/**
 * form
 */

const forms = ref([]);
const addForm = (index) => {
  searchColumns.forEach((column) => {
    if (column.id === index) {
      console.log(column.name);
    }
  });
};

const deleteForm = (index) => {
  console.log(index);
  forms.value.splice(index, 1);
  // setFormColumns.splice(index, 1);
};

const date = ref();
const timezones = ["Asia/Tokyo"];

onMounted(() => {
  const startDate = new Date();
  const endDate = new Date(new Date().setDate(startDate.getDate() + 7));
  date.value = [startDate, endDate];
});

const previousConditions = ref(JSON.parse(sessionStorage.getItem('search-conditions')))
const searchConditions = reactive({
  searchType: previousConditions.value?.searchType ?? '',
  keyWord: previousConditions.value?.keyWord ?? '',
  date: previousConditions.value?.date ?? null,
  checkbox: previousConditions.value?.checkbox ?? [],
  text: previousConditions.value?.text ?? [],
  addCondition: previousConditions.value?.addCondition || 'default'
})

const submit = async () => {
  await sessionStorage.setItem('search-conditions', JSON.stringify(searchConditions))
  location = '/search/summary'
}
 
</script>

<template>
  <dialog @click="emit('close-modal');" :class="[isFormModalShow ? 'visible z-50' : 'invisible']">
    <div @click.stop class="modal modal-center">
      <div class="bg-miby-light-blue w-full rounded-t relative">
        <p class="text-white leading-[43px] pl-5 text-center font-medium relative">詳細検索</p>
        <button id="" type="button" class="btn-close" @click="emit('close-modal')">
          <img :src="ButtonClose" alt="×" />
        </button>
      </div>
      <form
        @submit="submit"
        action="/search"
        method="dialog"
        class="mt-[-3px] pt-10 pb-10 md:mt-0 md:border-0 rounded-b-md px-2.5"
      >
        <div class="modalForm overflow-y-auto scroll-smooth h-full">
          <TransitionGroup name="list" tag="ul" class="h-full">
            <li v-for="(column, index) in setFormColumns" :key="column.id" class="mb-5">
              <div v-if="column.name == 'word'">
                <div class="mb-2.5 flex justify-between items-center">
                  <div>
                    <div class="radio">
                      <input
                        v-model="searchConditions.searchType" 
                        value="type-full-text"
                        class="absolute"
                        type="radio"
                        name="form-type"
                        id="modal-text-full"
                        checked
                      />
                      <label class="text-sm radio-label" for="modal-text-full">全文</label>
                    </div>
                    <div class="radio">
                      <input v-model="searchConditions.searchType" value="type-key-word" type="radio" name="form-type" id="modal-text-keyword" />
                      <label class="text-sm radio-label" for="modal-text-keyword"
                        >キーワード
                      </label>
                    </div>
                  </div>
                  <button id="addMyList" class="text-miby-blue text-sm">
                    <span class="icons icon-mylist-b align-middle text-miby-link-blue"
                      >マイリスト</span
                    >
                  </button>
                </div>
                <div class="mb-10">
                  <input
                    type="text"
                    class="h-10 w-full"
                    placeholder="入力後、ENTERを押して検索してください"
                    v-model="searchConditions.keyWord"
                  />
                </div>
              </div>

              <div v-else>
                <button
                  @click="deleteForm(column.id)"
                  class="block mb-2 removeForm text-miby-black text-sm font-medium"
                >
                  <span class="icons icon-remove align-middle">
                    {{ column.label }}
                  </span>
                </button>
                <div v-if="column.multiple == false">
                  <div v-if="column.form_type == 'text'" class="ml-9">
                    <input v-model="searchConditions.text[index]" type="text" class="h-8 w-full" :placeholder="column.placeholder" />
                  </div>
                  <div v-else-if="column.form_type == 'checkbox'" class="flex flex-wrap ml-7">
                    <div
                      v-for="checkbox_item in column.data"
                      :key="checkbox_item.id"
                      class="checkbox"
                    >
                      <input
                        class="absolute"
                        type="checkbox"
                        :name="column.name"
                        :id="checkbox_item.value"
                        :value="{type: column.name, value: checkbox_item.label}"
                        v-model="searchConditions.checkbox"
                      />
                      <label class="text-md min-[769px]:text-sm checkbox-label" :for="checkbox_item.value">
                        {{ checkbox_item.label }}
                      </label>
                    </div>
                  </div>
                </div>

                <div
                  v-else-if="column.form_type == 'date'"
                  class="ml-9 flex flex-wrap md:flex-nowrap items-center md:justify-start max-w-[345px]"
                >
                  <VueDatePicker v-model="searchConditions.date" range />
                  <!-- <FormDate /> -->
                  <!-- <VueDatePicker v-model="date" model-auto text-input class="h-[30px]"></VueDatePicker> -->
                  <!-- <span class="w-full md:w-[34px] px-2.5 align-top">—</span> -->
                  <!-- <VueDatePicker v-model="date" model-auto text-input class="h-[30px]"></VueDatePicker> -->
                </div>
              </div>
            </li>
          </TransitionGroup>

          <div class="modalForm pt-5 pb-10 overflow-y-auto scroll-smooth h-full">
            <div class="max-w-[500px] mx-auto">
              <div class="flex justify-end pt-5">
                <!-- selectがないとv-model効かなかった -->
                <TransitionGroup>
                  <select
                    name="list"
                    tag="select"
                    id="AddCondition"
                    v-model="searchConditions.addCondition"
                    class="bg-miby-link-blue border border-miby-link-blue text-white text-sm block w-[138px] pl-4"
                  >
                    <option value="default" disabled>検索条件追加</option>
                    <option
                      v-for="column in setAddColumns"
                      :key="column.id"
                      @change="addForm(column.id)"
                      :value="column.label"
                    >
                      {{ column.label }}
                    </option>
                  </select>
                </TransitionGroup>
              </div>
            </div>
          </div>
        </div>

        <div class="flex items-center justify-center pt-5 gap-4">
          <button
            id="seachClear"
            class="text-miby-black text-sm text-center font-medium border border-miby-black py-1.5 px-5 block min-w-[96px] rounded"
          >
            クリア
          </button>

          <button
            type="submit"
            id="seachSubmit"
            class="text-white text-sm text-center bg-miby-orange border border-miby-orange font-medium py-1.5 px-5 block min-w-[96px] rounded"
          >
            検索
          </button>
        </div>
      </form>
    </div>
    <div class="backdrop"></div>
  </dialog>
</template>
<style scoped lang="scss">
input[type="text"] {
  @apply py-2.5 px-5 rounded placeholder:text-miby-thin-gray border border-miby-thin-gray focus:ring focus:ring-miby-orange focus:border-none focus:outline-none;
}
.btn-close {
  @apply absolute w-3.5 right-5;
  top: calc(50% - 7px);
}
</style>
