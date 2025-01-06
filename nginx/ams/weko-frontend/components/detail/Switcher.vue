<template>
  <div class="flex justify-between p-5">
    <!-- 前のアイテムを表示 -->
    <a
      v-if="prevNum !== 0"
      class="text-sm font-medium icons icon-arrow-l hover:cursor-pointer"
      @click="emits('clickPrev', 'prev')">
      <span class="hidden md:inline-block">
        {{ $t('prevItem') }}
      </span>
    </a>
    <a v-else class="text-sm icons icon-arrow-l">
      <span class="hidden md:inline-block text-gray-400">
        {{ $t('prevItem') }}
      </span>
    </a>
    <!-- 検索結果に戻る -->
    <a class="text-sm font-medium text-miby-link-blue underline cursor-pointer" @click="goBack">
      {{ $t('returnResult') }}
    </a>
    <!-- 次のアイテムを表示 -->
    <a
      v-if="nextNum !== 0"
      class="text-sm font-medium icons icon-arrow-r hover:cursor-pointer"
      @click="emits('clickNext', 'next')">
      <span class="hidden md:inline-block">
        {{ $t('nextItem') }}
      </span>
    </a>
    <a v-else class="text-sm icons icon-arrow-r">
      <span class="hidden md:inline-block text-gray-400">
        {{ $t('nextItem') }}
      </span>
    </a>
  </div>
</template>

<script setup>
/* ///////////////////////////////////
// props
/////////////////////////////////// */

const props = defineProps({
  // API Response(JSON)
  sess: {
    type: String,
    default: ''
  },
  // 前のアイテムID
  prevNum: {
    type: Number,
    default: 0
  },
  // 次のアイテムID
  nextNum: {
    type: Number,
    default: 0
  }
});

/* ///////////////////////////////////
// emits
/////////////////////////////////// */

const emits = defineEmits(['clickPrev', 'clickNext']);

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * 検索結果に戻る用イベント
 */
function goBack() {
  if (props.sess === 'search') {
    useRouter().back();
  } else {
    navigateTo('/search');
  }
}
</script>
