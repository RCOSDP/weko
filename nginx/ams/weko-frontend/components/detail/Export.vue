<template>
  <div class="bg-miby-bg-gray py-7 px-3.5 w-full">
    <dl class="mb-5">
      <dt class="text-sm font-medium mb-2">OAI-PMH</dt>
      <dd class="flex flex-col gap-x-5">
        <NuxtLink
          :to="useAppConfig().export.jpcoar + props.currentNumber"
          target="_blank"
          class="text-sm text-miby-link-blue icons icon-external after truncate">
          <span class="mr-2.5 underline">JPCOAR</span>
        </NuxtLink>
        <NuxtLink
          :to="useAppConfig().export.dublincore + props.currentNumber"
          target="_blank"
          class="text-sm text-miby-link-blue icons icon-external after truncate">
          <span class="mr-2.5 underline">DublinCore</span>
        </NuxtLink>
        <NuxtLink
          :to="useAppConfig().export.ddi + props.currentNumber"
          target="_blank"
          class="text-sm text-miby-link-blue icons icon-external after truncate">
          <span class="mr-2.5 underline">DDI</span>
        </NuxtLink>
      </dd>
    </dl>
    <dl>
      <dt class="text-sm font-medium mb-2">Other Formats</dt>
      <dd class="flex flex-col gap-x-5">
        <NuxtLink
          :to="useAppConfig().wekoOrigin + '/records/' + props.currentNumber + '/export/json'"
          target="_blank"
          class="text-sm text-miby-link-blue icons icon-external after truncate">
          <span class="mr-2.5 underline">JSON</span>
        </NuxtLink>
        <NuxtLink
          :to="useAppConfig().wekoOrigin + '/records/' + props.currentNumber + '/export/bibtex'"
          target="_blank"
          class="text-sm text-miby-link-blue icons icon-external after truncate">
          <span class="mr-2.5 underline">BIBTEX</span>
        </NuxtLink>
      </dd>
    </dl>
  </div>
</template>

<script lang="ts" setup>
/* ///////////////////////////////////
// props
/////////////////////////////////// */

const props = defineProps({
  // 検索結果総数
  currentNumber: {
    type: Number,
    default: 0
  }
});
</script>
