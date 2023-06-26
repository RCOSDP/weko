<script setup>
import {computed} from 'vue'
const props = defineProps({
  itemId: String,
})

const next = computed(() => {
  if(props.itemId){
    return Number(props.itemId) + 1
  }
})
const last = computed(() => {
  if(props.itemId){
    return Number(props.itemId) - 1
  }
})

//todo GET DATA LENGTH
</script>

<template>
  <div class="flex justify-between p-5">
    <a v-if="last > 0" class="text-sm font-medium icons icon-arrow-l" :href="`/detail/${last}`"><span class="hidden md:inline-block">前のアイテムを表示</span></a>
    <a class="text-sm font-medium text-miby-link-blue underline" href="/search">検索結果リストに戻る</a>
    <a class="text-sm font-medium icons icon-arrow-r" :href="`/detail/${next}`"><span class="hidden md:inline-block">次のアイテムを表示</span></a>
  </div>
</template>
