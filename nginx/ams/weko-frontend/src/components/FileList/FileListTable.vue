<script setup>
import LicensePD from "/images/license-sample01.png";
import LicenseCC from "/images/license-sample02.png";
import Download from "/images/icon/icon_dl-rank.svg";
import FileListTableCard from "./FileListTableCard.vue";
import Pagination from "../../components/SearchResult/Pagination.vue";
import ButtonFilter from "/images/btn/btn-filter.svg";
import { computed, onMounted, ref, watch } from "vue";
import ModalFilterFileList from "../Modal/ModalFilterFileList.vue";

const props = defineProps({
  id: String,
});

const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const currentPage = ref(+urlParams.get('page') || 1)
const displayValue = ref(20);
const files = ref([])
const item = ref([])
const total = ref();
const loadItems = async () => {
  const res = await fetch(`https://ams-dev.ir.rcos.nii.ac.jp/api/v1.0/records/${props.id}/detail`);
  item.value = await res.json();
}
loadItems()

watch([displayValue, item], () => {
  if(item.value){
    files.value = item.value.item_1617605131499.attribute_value_mlt
    paginate()
  }
})

watch(item, () => {
  if(item.value){
    total.value = item.value.item_1617605131499.attribute_value_mlt.length
  }
})


function paginate() {
  files.value = files.value.slice((currentPage.value - 1) * displayValue.value, currentPage.value * displayValue.value);
}

const filterModal = ref()

onMounted(() => {
  filterModal.value = document.getElementById('modalFilterFileList')
})

const openModal = () => {
  filterModal.value.showModal()
}
</script>

<template>
  <div class="w-full bg-miby-searchtags-blue p-5">
    <div class="flex flex-wrap justify-between items-center">
      <div class="flex flex-wrap gap-5 items-center">
        <div class="text-miby-black text-sm font-medium flex items-center">
          <span>表示件数：</span>
          <select
            v-model="displayValue"
            class="cursor-pointer bg-white border border-gray-300 text-miby-black py-0 text-[10px] pr-1 rounded block"
          >
            <option value="20" selected>20</option>
            <option value="40">40</option>
            <option value="60">60</option>
            <option value="80">80</option>
            <option value="100">100</option>
            <option value="150">150</option>
            <option value="200">200</option>
          </select>
          <span class="ml-1">/{{ total }}</span>
        </div>
        <div class="text-miby-black text-sm font-medium flex items-center">
          <span>DL回数統計対象期間：</span>
          <select
            class="cursor-pointer bg-white border border-gray-300 text-miby-black py-0 text-[10px] pr-1 rounded block"
          >
            <option value="" selected>全期間</option>
          </select>
        </div>
      </div>

      <div class="flex gap-2.5">
        <button
          @click="openModal"
          class="btn-modal block cursor-pointer"
          data-target="FilterFileList"
        >
          <img :src="ButtonFilter" alt="フィルター" />
        </button>
      </div>
    </div>
  </div>
  <div class="p-5 bg-miby-bg-gray">
    <div class="w-full">
      <div class="flex flex-wrap justify-end items-center mb-10">
        <a class="pl-1.5 md:pl-0 icons icon-download after" href=""
          ><span class="underline text-sm text-miby-link-blue font-medium pr-1"
            >検索結果全てをDLする</span
          ></a
        >
      </div>
      <div class="w-full overflow-x-auto">
        <table
          class="search-lists w-[1274px] border-collapse border border-slate-500 table-auto"
        >
          <thead>
            <tr>
              <th class="max-w-[44px]">選択</th>
              <th class="max-w-[130px]">ファイル名</th>
              <th class="max-w-[86px]">サイズ</th>
              <th class="max-w-[137px]">DL区分</th>
              <th class="max-w-[110px]">ライセンス</th>
              <th class="max-w-[134px]">アクション</th>
              <th class="max-w-[210px]">格納場所</th>
              <th class="max-w-[130px]">DL回数</th>
            </tr>
          </thead>
          <tbody v-for="file in files">
            <FileListTableCard :file="file" />
          </tbody>
        </table>
      </div>
      <div class="flex justify-center mt-2 mb-4">
        <button
          class="flex gap-1 bg-miby-link-blue text-white px-4 py-2 rounded"
        >
          <img :src="Download" alt="" />ダウンロード
        </button>
      </div>
      <div class="max-w-[300px] mx-auto mt-3.5 mb-16">
        <div v-if="total">
          <Pagination
            :key="displayValue"
            :display-value="String(displayValue)"
            :currentPage="currentPage"
            :total="total"
          />
        </div>
      </div>
    </div>
  </div>
  <ModalFilterFileList />
</template>

<style scoped lang="scss">
.border-collapse {
  th,
  td {
    @apply border border-miby-thin-gray text-center align-middle;
  }

  th {
    @apply py-1 font-medium;
  }

  td {
    @apply px-2 pt-5 pb-7;
  }
}
</style>
