<template>
  <div class="mt-2.5">
    <h5 class="text-md text-miby-black text-left font-medium icons icon-border">
      {{ subSection.title }}
    </h5>
    <div v-for="element in subSection.text" :key="element">
      <p class="text-sm text-miby-black text-left pt-1 pl-6">
        {{ element }}
      </p>
    </div>
    <div class="flex flex-wrap gap-1 mt-7.5" />
  </div>
</template>

<script lang="ts" setup>
/* ///////////////////////////////////
// props
/////////////////////////////////// */

defineProps({
  // サブセクション情報
  subSection: {
    type: Object,
    default: () => {}
  }
});
</script>
