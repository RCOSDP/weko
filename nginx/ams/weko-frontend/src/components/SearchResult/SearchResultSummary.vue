<script setup>
import ImageSample from "/images/img-search-sample.png";
import SearchResultSummaryCard from './SearchResultSummaryCard.vue'
import { ref } from 'vue'

const props = defineProps({
  searchResult: Object
})

</script>

<template>
  <div class="w-full">
    <div v-for="result in searchResult" class="w-full">
      <SearchResultSummaryCard :result="result" />
    </div>
  </div>
</template>
