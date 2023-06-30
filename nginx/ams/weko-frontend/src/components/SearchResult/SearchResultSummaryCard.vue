<template>
    <div class="search-rows">
        <div class="rows-checkbox">
          <input class="" type="checkbox" name="publish-type" />
        </div>
        <div class="rows-index">9,999,999,999</div>
        <div class="rows-image"><img :src="ImageSample" alt="" /></div>
        <div class="rows-detail">
          <div class="flex flex-nowrap mb-1.5 gap-5 items-center">
            <p class="icons-type icon-group"><span>{{ result._source._item_metadata.item_1685585170888.attribute_value_mlt[0].subitem_1685583776261.subitem_1685583784534 }}</span></p>
            <p class="date-upload icons icon-publish">{{ result._source.publish_date }}</p>
            <p class="date-update icons icon-update">{{ result._source._item_metadata.item_1685585050910.attribute_value_mlt[0].subitem_1685583626611.subitem_1685583633388 }}</p>
          </div>
          <a class="data-title whitespace-normal" :href="`/detail/${result._source.control_number}`"
            >{{ result._source.title.join(',') }}</a
          >
          <div class="flex mb-1">
            <p class="data-note">分野：<span class="">{{ result._source._item_metadata.item_1685585121449.attribute_value_mlt[0].subitem_1685583691205 }}</span></p>
            <p class="data-note author">
              作成者：<span><a class="underline" href="">{{ result._source._item_metadata.item_1685585204873.attribute_value_mlt[0].subitem_1685584180890.subitem_1685584186042 }}</a></span>
                <span><a class="underline" href="">{{ result._source._item_metadata.item_1685585204873.attribute_value_mlt[0].subitem_1685584180890.subitem_1685584185026 }}</a></span>
            </p>
          </div>
          <div class="flex flex-nowrap">
            <p class="data-note">ヒト/動物/その他：<span class="font-medium">{{ result._source._item_metadata.item_1685585235282.attribute_value_mlt[0].subitem_1685584345785 }}</span></p>
            <p class="data-note access-type">アクセス権：<span>{{ result._source._item_metadata.item_1685585170888.attribute_value_mlt[0].subitem_1685583776261.subitem_1685583784534 }}</span></p>
            <p class="data-note">
              ファイル：<span class="font-medium"
                ><a class="underline text-miby-link-blue" href="/filelist">{{+result._source._item_metadata.item_1685585153905.attribute_value_mlt[0].subitem_1685583723733.subitem_1685583728790 < 1 ? 'なし' : `あり（${result._source._item_metadata.item_1685585153905.attribute_value_mlt[0].subitem_1685583723733.subitem_1685583728790}）`}}</a></span
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
console.log(props.result._source._item_metadata.item_1685585204873.attribute_value_mlt[0].subitem_1685584180890)
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