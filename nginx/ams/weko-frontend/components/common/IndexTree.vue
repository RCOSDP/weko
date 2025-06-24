<template>
  <div v-if="index">
    <details class="index-tree__items">
      <summary>
        <span @click.prevent="searchFromItem(index.cid)">
          {{ index.name }}
        </span>
      </summary>
      <div class="index-tree__detail">
        <div class="index-tree_item">
          <div v-for="child in index.children" :key="child.id">
            <IndexTree v-if="child.children" :index="child" @click-index="emits('clickIndex')" />
          </div>
        </div>
      </div>
    </details>
  </div>
</template>

<script lang="ts" setup>
/* ///////////////////////////////////
// props
/////////////////////////////////// */

defineProps({
  // API Response(JSON)
  index: {
    type: Object,
    default: () => {}
  }
});

/* ///////////////////////////////////
// emits
/////////////////////////////////// */

const emits = defineEmits(['clickIndex']);

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const conditions = reactive({ type: '0', keyword: '' });
const appConf = useAppConfig();

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * インデックス名押下時イベント
 * @param indexId インデックスID
 */
function searchFromItem(indexId: string) {
  conditions.keyword = indexId;

  if (sessionStorage.getItem('conditions')) {
    // @ts-ignore
    const sessConditions = JSON.parse(sessionStorage.getItem('conditions'));
    // 詳細検索条件が設定されている場合は削除
    if (Object.prototype.hasOwnProperty.call(sessConditions, 'detail')) {
      delete sessConditions.detail;
      delete sessConditions.detailData;
    }
    // 検索条件設定
    Object.assign(sessConditions, conditions);
    sessionStorage.setItem('conditions', JSON.stringify(sessConditions));
  } else {
    sessionStorage.setItem('conditions', JSON.stringify(conditions));
  }

  emits('clickIndex');
  navigateTo(`${appConf.amsPath ?? ''}/search/${indexId}`);
}
</script>
