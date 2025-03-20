<template>
  <div>
    <div class="max-w-[300px] mx-auto mt-3.5 mb-16 flex justify-center">
      <div v-for="page in pages" :key="page">
        <a v-if="page == String(currentPage)" :class="{ current: true }" class="page-numbers">
          {{ page }}
        </a>
        <a v-else-if="page == '...'" :class="{ current: false }" class="page-numbers">
          {{ page }}
        </a>
        <a v-else :class="{ current: false }" class="page-numbers cursor-pointer" @click="emits('clickPage', page)">
          {{ page }}
        </a>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
/* ///////////////////////////////////
// props
/////////////////////////////////// */

const props = defineProps({
  // 検索結果総数
  total: {
    type: Number,
    default: 1,
    require: true
  },
  // 表示ページ
  currentPage: {
    type: Number,
    default: 1,
    require: true
  },
  // 表示件数
  displayPerPage: {
    type: Number,
    default: 20,
    require: true
  }
});

/* ///////////////////////////////////
// emits
/////////////////////////////////// */

const emits = defineEmits(['clickPage']);

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const pages = ref<string[]>([]);

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * 表示するページ番号を抽出
 * @param current 表示ページ
 * @param maxPage 最大ページ数
 */
function pagination(current: number, maxPage: number) {
  let dotsFlg = false;
  for (let i = 1; i <= maxPage; i++) {
    if (i === 1 || i === maxPage || (i >= current - 2 && i <= current + 2)) {
      pages.value.push(String(i));
      dotsFlg = false;
    } else if (!dotsFlg) {
      pages.value.push('...');
      dotsFlg = true;
    }
  }
}

/* ///////////////////////////////////
// main
/////////////////////////////////// */

try {
  pagination(props.currentPage, Math.ceil(props.total / props.displayPerPage));
} catch (error) {
  // console.log(error);
}
</script>
