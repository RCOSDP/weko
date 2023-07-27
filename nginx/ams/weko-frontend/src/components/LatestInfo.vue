<template>
  <div class="w-full">
    <div class="bg-miby-bg-gray">
      <div class="p-5">
        <!-- <LatestInfoCard /> -->
        <div class="border-b-2 border-dashed border-miby-border-black pb-5">
          <div class="flex flex-wrap mb-1.5 gap-5 items-center">
            <p class="icons-type icon-group"><span>{{ item._source._item_metadata.item_1685585170888.attribute_value_mlt[0].subitem_1685583776261.subitem_1685583784534 }}</span></p>
            <p class="date-upload icons icon-publish">{{ item._source._item_metadata.item_1685585050910.attribute_value_mlt[0].subitem_1685583626611.subitem_1685583628794 }}</p>
            <p class="date-update icons icon-update">{{ item._source._item_metadata.item_1685585050910.attribute_value_mlt[0].subitem_1685583626611.subitem_1685583633388 }}</p>
          </div>
          <a class="data-title" :href="`/detail/${item._source.control_number}`"
            >{{ item._source._item_metadata.title.join(',') }}</a
          >
          <div class="flex mb-1">
            <p class="data-note">分野：<span class="">{{ item._source._item_metadata.item_1685585121449.attribute_value_mlt[0].subitem_1685583691205 }}</span></p>
            <p class="data-note author">
              作成者：<span><a class="underline" href="">{{ item._source._item_metadata.item_1685585204873.attribute_value_mlt[0].subitem_1685584180890.subitem_1685584186042 }}</a></span>
                <span><a class="underline" href="">{{ item._source._item_metadata.item_1685585204873.attribute_value_mlt[0].subitem_1685584180890.subitem_1685584185026 }}</a></span>
            </p>
          </div>
          <div class="flex flex-wrap">
            <p class="data-note">ヒト/動物/その他：<span class="font-medium">{{ item._source._item_metadata.item_1685585235282.attribute_value_mlt[0].subitem_1685584345785 }}</span></p>
            <p class="data-note access-type">アクセス権：<span>{{ item._source._item_metadata.item_1685585170888.attribute_value_mlt[0].subitem_1685583776261.subitem_1685583784534 }}</span></p>
            <p class="data-note">
              ファイル：<span class="font-medium"
                ><a class="underline text-miby-link-blue" :href="`/filelist/${item._source.control_number}`">{{+item._source._item_metadata.item_1685585153905.attribute_value_mlt[0].subitem_1685583723733.subitem_1685583728790 < 1 ? 'なし' : `あり（${item._source._item_metadata.item_1685585153905.attribute_value_mlt[0].subitem_1685583723733.subitem_1685583728790}）`}}</a></span
              >
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  item: Object
})
</script>

<style scoped lang="scss">

.data-title {
  @apply text-miby-black;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.data-note {
  @apply mr-4 font-medium text-sm;
  span {
    font-weight: normal;
  }
}

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
