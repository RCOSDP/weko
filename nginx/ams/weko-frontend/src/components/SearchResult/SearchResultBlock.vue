<script setup>
import ImageSample from "/images/img-search-sample.png";
import SearchResultBlockCard from './SearchResultBlockCard.vue'
import { ref } from 'vue'

const props = defineProps({
  searchResult: Object
})

</script>

<template>
  <div>
    <div class="grid grid-cols-2 md:grid-cols-5">
      <div class="col-span-1" v-for="result in searchResult">
        <SearchResultBlockCard :result="result" />
      </div>
    </div>
  </div>
</template>
