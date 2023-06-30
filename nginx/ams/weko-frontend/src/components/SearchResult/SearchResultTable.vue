<script setup>
import ImageSample from "/images/img-search-sample.png";
import SearchResultTableCard from './SearchResultTableCard.vue'
import { ref, watch, reactive } from 'vue'

const emit = defineEmits(['table-sort'])
const props = defineProps({
  searchResult: Object
})
// const id = ref({id: 'id', value: ''})
// const setId = (value) => {
//   id.value.value = value
//   setTableSort(id.value)
// }
// const createDate = ref({id: 'createDate', value: ''})
// const setCreateDate = (value) => {
//   createDate.value.value = value
//   setTableSort(createDate.value)
// }
// const title = ref({id: 'title', value: ''})
// const setTitle = (value) => {
//   title.value.value = value
//   setTableSort(title.value)
// }

// const tableSort = ref([
//   id.value,
//   createDate.value,
//   title.value
// ])

// const sorting = ref(null)
// function setTableSort(value) {
//   sorting.value = !sorting.value
//   let index = tableSort.value.findIndex((item) => item.id == value.id)
//   tableSort.value[index].value = value.value
// }
// watch(sorting, () => {
//   emit('table-sort', tableSort.value)
// })

const sortItem = ref('')
const toggleSort = (value) => {
  sortItem.value = value
}

watch(sortItem, () => {
  emit('table-sort', sortItem.value)
})

</script>

<template>
  <div class="w-full">
    <div class="w-full overflow-x-auto">
      <table class="search-lists w-[1274px] border-collapse border border-slate-500 table-auto">
        <thead>
          <tr class="bg-[#F9F9F9]">
            <th class="w-[44px]">選択</th>
            <th class="w-[110px]"><div class="flex justify-center">No <div class="flex flex-col"><span @click="toggleSort('controlnumber')" class="-my-1.5 hover:cursor-pointer">&#x25B4;</span><span @click="toggleSort('-controlnumber')" class="-my-1.5 hover:cursor-pointer">&#x25BE;</span></div></div></th>
            <th class="w-[100px]"><div class="flex justify-center">公開区分 <div class="flex flex-col"><span class="-my-1.5 hover:cursor-pointer">&#x25B4;</span><span class="-my-1.5 hover:cursor-pointer">&#x25BE;</span></div></div></th>
            <th class="w-[250px]"><div class="flex justify-center">タイトル <div class="flex flex-col"><span @click="toggleSort('wtl')" class="-my-1.5 hover:cursor-pointer">&#x25B4;</span><span @click="toggleSort('-wtl')" class="-my-1.5 hover:cursor-pointer">&#x25BE;</span></div></div></th>
            <th class="w-[140px]"><div class="flex justify-center">分野 <div class="flex flex-col"><span class="-my-1.5 hover:cursor-pointer">&#x25B4;</span><span class="-my-1.5 hover:cursor-pointer">&#x25BE;</span></div></div></th>
            <th class="w-[120px]"><div class="flex justify-center">作成者 <div class="flex flex-col"><span @click="toggleSort('creator')" class="-my-1.5 hover:cursor-pointer">&#x25B4;</span><span @click="toggleSort('-creator')" class="-my-1.5 hover:cursor-pointer">&#x25BE;</span></div></div></th>
            <th class="w-[120px]"><div class="flex justify-center">掲載日 <div class="flex flex-col"><span @click="toggleSort('-createdate')" class="-my-1.5 hover:cursor-pointer">&#x25B4;</span><span @click="toggleSort('createdate')" class="-my-1.5 hover:cursor-pointer">&#x25BE;</span></div></div></th>
            <th class="w-[120px]"><div class="flex justify-center">更新日 <div class="flex flex-col"><span class="-my-1.5 hover:cursor-pointer">&#x25B4;</span><span class="-my-1.5 hover:cursor-pointer">&#x25BE;</span></div></div></th>
            <th class="w-[145px]"><div class="flex justify-center">ヒト/動物/その他 <div class="flex flex-col"><span class="-my-1.5 hover:cursor-pointer">&#x25B4;</span><span class="-my-1.5 hover:cursor-pointer">&#x25BE;</span></div></div></th>
            <th class="w-[120px]"><div class="flex justify-center">ファイル <div class="flex flex-col"><span class="-my-1.5 hover:cursor-pointer">&#x25B4;</span><span class="-my-1.5 hover:cursor-pointer">&#x25BE;</span></div></div></th>
          </tr>
        </thead>
        <tbody v-for="result in searchResult">
          <SearchResultTableCard :result="result" />
        </tbody>
      </table>
    </div>
  </div>
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

    &.text-left {
      text-align: left;
    }

    .title {
      @apply underline;
    }

    .create-user {
      @apply underline block whitespace-nowrap;
    }
  }
}
</style>