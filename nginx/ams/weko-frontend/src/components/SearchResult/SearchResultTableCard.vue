<script setup>
const props = defineProps({
    result: Object
})

</script>

<template>
    <tr>
        <td>
            <input class="" type="checkbox" name="publish-type" />
        </td>
        <td>{{ result._source.control_number }}</td>
        <!-- <i class="icons-type icon-published"></i> -->
        <td>{{ result._source._item_metadata.item_1685585170888.attribute_value_mlt[0].subitem_1685583776261.subitem_1685583784534 }}</td>
        <td class="text-left">
            <a class="title" :href="`/detail/${result._source.control_number}`"
            >{{ result._source.title.join(',') }}</a
            >
        </td>
        <td><p class="field">{{ result._source._item_metadata.item_1685585121449.attribute_value_mlt[0].subitem_1685583691205 }}</p></td>
        <td>
          <p class="author create-user">
              <span><a class="underline" href="">{{ result._source._item_metadata.item_1685585204873.attribute_value_mlt[0].subitem_1685584180890.subitem_1685584186042 }}</a></span>
              <span><a class="underline" href="">{{ result._source._item_metadata.item_1685585204873.attribute_value_mlt[0].subitem_1685584180890.subitem_1685584185026 }}</a></span>
            </p>
        </td>
        <td><p class="publish-date">{{ result._source.publish_date }}</p></td>
        <td><p class="update-date">{{ result._source._item_metadata.item_1685585050910.attribute_value_mlt[0].subitem_1685583626611.subitem_1685583633388 }}</p></td>
        <td><p class="category">{{ result._source._item_metadata.item_1685585235282.attribute_value_mlt[0].subitem_1685584345785 }}</p></td>
        <td><p class="underline hover:cursor-pointer number-files text-miby-link-blue">{{+result._source._item_metadata.item_1685585153905.attribute_value_mlt[0].subitem_1685583723733.subitem_1685583728790 < 1 ? 'なし' : `あり（${result._source._item_metadata.item_1685585153905.attribute_value_mlt[0].subitem_1685583723733.subitem_1685583728790}）`}}</p></td>
        </tr>
</template>

<style scoped lang="scss">
// .border-collapse {
//   th,
  td {
    @apply border border-miby-thin-gray text-center align-middle;
  }

  th {
    @apply py-1 font-medium;
  }

  td {
    @apply px-2 pt-5 pb-7;

    &.text-left {
      text-align: left;
    }

    .title {
      @apply underline;
    }

    .create-user {
      @apply underline block whitespace-nowrap;
    }
  }
// }
//後でaccess-typeを使うかな
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