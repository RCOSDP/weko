<template>
  <div class="w-full border-miby-thin-gray border-[1px]">
    <div class="search-block__head">
      <input class="" type="checkbox" name="publish-type" />
      <p class="icons-type icon-published"><span>一般公開</span></p>
    </div>
    <div class="search-block__content">
      <div class="image"><img class="" :src="ImageSample" alt="" /></div>
      <a class="title break-all" :href="`/detail/${result._source.control_number}`"
        >{{ result._source.title[0] }}</a
      >
    </div>
    <p class="text-[10px] pb-[10px] pl-[10px]">{{ result._source.publish_date }}</p>
  </div>
</template>

<script setup>
import ImageSample from "/images/img-search-sample.png";
const props = defineProps({
  result: Object
})

//TODO publishTypeはどこ？
</script>

<style scoped>

</style>

