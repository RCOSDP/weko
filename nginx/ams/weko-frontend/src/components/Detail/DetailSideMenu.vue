<script setup>
const stabMenu = [];

const props = defineProps({
  item: Object
})

</script>

<template>
  <div class="w-full md:max-w-[271px] md:ml-[5px]">
    <div class="bg-miby-light-blue py-3 pl-5">
      <p class="icons icon-statistics text-white font-bold">見られた数</p>
    </div>
    <div class="bg-miby-bg-gray py-10 text-center">
      <p class="text-2xl font-medium mb-12">9,999,999,999</p>
      <a class="block max-w-[130px] mb-3.5 mx-auto border rounded border-miby-black" href=""
        ><span class="icons icon-arrow">total</span></a
      >
      <a class="block text-miby-link-blue underline text-sm font-medium">See details</a>
    </div>
    <div class="bg-miby-light-blue w-full">
      <p class="text-white leading-[43px] pl-5 icons icon-dl-rank font-bold">DLランキング</p>
    </div>
    <div class="bg-miby-bg-gray py-5 px-3.5 w-full">
      <ul class="w-full">
        <li class="flex items-center mb-1.5 icons icon-download after lg:justify-between">
          <p class="ranking-number bg-miby-tag-yellow">1</p>
          <a class="ranking-text font-medium text-clamp" href="">測定1.csv</a>
        </li>
        <li class="flex items-center mb-1.5 icons icon-download after lg:justify-between">
          <p class="ranking-number bg-miby-tag-gray">2</p>
          <a class="ranking-text font-medium text-clamp" href="">aaabbbcccdddeeefkoaaabbbcccdddeeefko.xlsx</a>
        </li>
        <li class="flex items-center mb-1.5 icons icon-download after lg:justify-between">
          <p class="ranking-number bg-miby-tag-orange">3</p>
          <a class="ranking-text font-medium flex items-center" href=""
            ><span class="inline-block text-clamp">aaabbbcccdddeeefkoaaabbbcccdddeeefko</span>
            <span class="inline-block">.png</span></a
          >
        </li>
        <li class="flex items-center mb-1.5 icons icon-download after lg:justify-between">
          <p class="ranking-number bg-miby-border-gray">4</p>
          <a class="ranking-text font-medium text-clamp" href="">画像1.png</a>
        </li>
        <li class="flex items-center mb-1.5 icons icon-download after lg:justify-between">
          <p class="ranking-number bg-miby-border-gray">5</p>
          <a class="ranking-text font-medium text-clamp" href="">画像2.png</a>
        </li>
      </ul>
    </div>
    <div class="bg-miby-light-blue py-3 pl-5">
      <p class="icons icon-export text-white font-bold">エクスポート</p>
    </div>
    <div class="bg-miby-bg-gray py-5 px-3.5 w-full">
      <dl class="mb-5">
        <dt class="text-sm font-medium mb-2">OAI-PMH</dt>
        <dd v-for="file in item.item_1617258105262.attribute_value_mlt" class="flex flex-wrap gap-x-5">
          <a :href="file.resourceuri" class="text-sm text-miby-link-blue icons icon-external after"><span class="mr-2.5 underline">{{ file.resourcetype }}</span></a>
        </dd>
      </dl>
      <dl class="mb-5">
        <dt class="text-sm font-medium mb-2">Other Formats</dt>
        <dd v-for="file in item.item_1617605131499.attribute_value_mlt" class="flex flex-wrap gap-x-5">
          <a :href="file.url.url" class="text-sm text-miby-link-blue icons icon-external after"><span class="mr-2.5 underline">{{ file.format }}</span></a>
        </dd>
      </dl>
    </div>
  </div>
</template>
