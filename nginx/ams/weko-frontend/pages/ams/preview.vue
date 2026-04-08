<template>
  <div>
    <div
      v-if="useRoute().query.type === 'image/png' || useRoute().query.type === 'image/jpeg'"
      class="h-screen w-screen flex justify-center items-center bg-black">
      <img class="object-scale-down h-full m-auto" :src="String(useRoute().query.blob)" />
    </div>
    <div
      v-if="useRoute().query.type === 'application/pdf'"
      class="h-screen w-screen flex justify-center items-center bg-neutral-600">
      <iframe class="h-full w-full" :src="String(useRoute().query.blob)" />
    </div>
  </div>
</template>

<script lang="ts" setup>
definePageMeta({
  layout: false
});
</script>
