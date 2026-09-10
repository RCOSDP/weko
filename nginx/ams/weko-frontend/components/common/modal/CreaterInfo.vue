<template>
  <dialog :class="[modalShowFlag ? 'visible' : 'invisible']" @click="closeModal">
    <div class="modal-info z-50" @click.stop>
      <div class="bg-miby-light-blue flex flex-row">
        <div class="basis-5/6">
          <p class="text-white leading-[43px] pl-10 text-center font-medium">作成者情報</p>
        </div>
        <div class="basis-1/6 flex text-end justify-end pr-3">
          <button type="button" class="btn-close">
            <img :src="`${appConf.amsImage ?? '/img'}/btn/btn-close.svg`" alt="×" @click="closeModal" />
          </button>
        </div>
      </div>
      <div class="modalForm overflow-y-auto scroll-smooth h-full">
        <div class="pt-5 pb-5 h-full">
          <label class="label flex-col">
            <span class="text-sm font-medium mr-auto text-miby-dark-gray">所属</span>
            <a class="pt-2 pl-5 pr-3 w-full break-words">
              {{ '東京大学' }}
            </a>
          </label>
          <label class="label flex-col">
            <span class="text-sm font-medium mr-auto text-miby-dark-gray">氏名</span>
            <a class="pt-2 pl-5 pr-3 w-full break-words">
              {{ '田中 太郎' }}
            </a>
          </label>
          <label class="label flex-col">
            <span class="text-sm font-medium mr-auto text-miby-dark-gray">メールアドレス</span>
            <a class="pt-2 pl-5 pr-3 w-full break-words">
              {{ 'sample@sample.co.jp' }}
            </a>
          </label>
        </div>
      </div>
      <div class="flex justify-center items-center mt-3 mb-5">
        <a class="text-miby-link-blue underline cursor-pointer">Search Repository</a>
      </div>
    </div>
    <div class="backdrop-opacity-0" />
  </dialog>
</template>

<script lang="ts" setup>
/* ///////////////////////////////////
// expose
/////////////////////////////////// */

defineExpose({
  openModal
});

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const modalShowFlag = ref(false);
const appConf = useAppConfig();

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * モーダル表示
 */
function openModal() {
  modalShowFlag.value = true;
}

/**
 * モーダル非表示
 */
function closeModal() {
  modalShowFlag.value = false;
}

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

onMounted(() => {
  window.addEventListener('scroll', closeModal);
});
</script>

<style scoped lang="scss">
.border-collapse {
  th {
    @apply border border-miby-thin-gray text-center align-middle;
    @apply py-1 font-medium;
  }
  td {
    @apply border border-miby-thin-gray text-center align-middle;
    @apply px-2 pt-5 pb-7;
  }
}
</style>
