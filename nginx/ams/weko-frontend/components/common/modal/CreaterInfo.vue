<template>
  <dialog :class="[modalShowFlag ? 'visible' : 'invisible']" @click="closeModal">
    <div class="modal-info z-50" @click.stop>
      <div class="bg-miby-light-blue flex flex-row">
        <div class="basis-5/6">
          <p class="text-white leading-[43px] pl-10 text-center font-medium">作成者情報</p>
        </div>
        <div class="basis-1/6 flex text-end justify-end pr-3">
          <button type="button" class="btn-close">
            <img src="/img/btn/btn-close.svg" alt="×" @click="closeModal" />
          </button>
        </div>
      </div>
      <form action="/search" method="dialog" class="mt-[-3px] pt-10 pb-10 md:mt-0 md:border-0 rounded-b-md px-2.5">
        <div class="modalForm overflow-y-auto scroll-smooth h-full">
          <div class="modalForm pt-5 pb-10 overflow-y-auto scroll-smooth h-full">
            <div class="max-w-[500px] mx-auto" />
            <table class="table">
              <tbody>
                <tr>
                  <th>所属</th>
                  <td>東京大学</td>
                </tr>
                <tr>
                  <th>氏名</th>
                  <td>鈴木 一郎</td>
                </tr>
                <tr>
                  <th>メールアドレス</th>
                  <td>email@sample.com</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </form>
      <div class="flex justify-center items-center mb-5">
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
