<template>
  <div v-if="displayType == 'summary'">
    <div class="w-full overflow-x-auto">
      <div v-for="item in searchResult" :key="item" class="w-full whitespace-nowrap">
        <SummaryStyle :item="item" @click-creater="emits('clickCreater')" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import SummaryStyle from '~/components/search/SummaryStyle.vue';

/* ///////////////////////////////////
// props
/////////////////////////////////// */

defineProps({
  // 表示形式
  displayType: {
    type: String,
    default: ''
  },
  // API Response(JSON)
  searchResult: {
    type: Object,
    default: () => {}
  }
});

/* ///////////////////////////////////
// emits
/////////////////////////////////// */

const emits = defineEmits(['clickCreater']);
</script>
