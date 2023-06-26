<template>
    <div class="search-rows">
        <div class="rows-checkbox">
          <input class="" type="checkbox" name="publish-type" />
        </div>
        <div class="rows-index">9,999,999,999</div>
        <div class="rows-image"><img :src="ImageSample" alt="" /></div>
        <div class="rows-detail">
          <div class="flex flex-wrap mb-1.5 gap-5 items-center">
            <p class="icons-type icon-group"><span>グループ内公開</span></p>
            <p class="date-upload icons icon-publish">{{ result._source.publish_date }}</p>
            <p class="date-update icons icon-update">{{ result._source._item_metadata.item_1685585050910.attribute_value_mlt[0].subitem_1685583626611.subitem_1685583633388 }}</p>
          </div>
          <a class="data-title" :href="`/detail/${result._source.control_number}`"
            >{{ result._source.title.join(',') }}</a
          >
          <div class="flex mb-1">
            <p class="data-note">分野：<span class="">{{ result._source._item_metadata.item_1685585121449.attribute_value_mlt[0].subitem_1685583691205 }}</span></p>
            <p class="data-note author">
              作成者：<span v-for="person in result._source._item_metadata.item_1685585204873.attribute_value_mlt[0].subitem_1685584180890" class="">
                <span><a class="underline" href="">{{ person }}</a></span>
              </span>
            </p>
          </div>
          <div class="flex flex-wrap">
            <p class="data-note">ヒト/動物/その他：<span class="font-medium">{{ result._source._item_metadata.item_1685585235282.attribute_value_mlt[0].subitem_1685584345785 }}</span></p>
            <p class="data-note access-type">アクセス権：<span v-for="accessType in result._source._item_metadata.item_1685585170888.attribute_value_mlt[0].subitem_1685583776261" class="font-medium">{{ accessType }}</span></p>
            <p class="data-note">
              ファイル：<span class="font-medium"
                ><a class="underline text-miby-link-blue" href="/filelist">あり（250）</a></span
              >
            </p>
          </div>
        </div>
      </div>
</template>

<script setup>
import ImageSample from "/images/img-search-sample.png";

const props = defineProps({
    result: Object
})
</script>

<style scoped>
.author span,
.access-type span {
  display: inline-block;
}
.author span::before,
.access-type span::before {
  content: ", ";
}
.author span:first-child::before,
.access-type span:first-child::before {
  content: "";
}

</style>