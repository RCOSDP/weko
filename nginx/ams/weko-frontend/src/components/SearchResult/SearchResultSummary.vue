<script setup>
import ImageSample from "/images/img-search-sample.png";
import SearchResultSummaryCard from './SearchResultSummaryCard.vue'
import { ref } from 'vue'

const props = defineProps({
  searchResult: Object
})

</script>

<template>
  <div class="w-full overflow-x-auto">
    <div v-for="result in searchResult" class="w-full whitespace-nowrap">
      <SearchResultSummaryCard :result="result" />
    </div>
  </div>
</template>
