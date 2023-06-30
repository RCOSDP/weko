<script setup>
import ButtonClose from "/images/btn/btn-close.svg";
import columns from "../../data/data-column.json";

const closeDisplayItemModal = () => {
  document.body.classList.remove("overflow-hidden");
  document.getElementById('modalDisplayItem').close()
}

const submit = () => {
  //submit機能
  closeDisplayItemModal()
}
</script>
<template>
  <dialog @click="closeDisplayItemModal" id="modalDisplayItem" class="w-11/12 md:w-full max-w-[728px] mx-auto z-10">
    <div @click.stop class="bg-miby-light-blue w-full rounded-t relative">
      <p class="text-white leading-[43px] pl-5 text-center font-medium relative">項目表示</p>
      <button id="" type="button" class="btn-close" @click="closeDisplayItemModal">
        <img :src="ButtonClose" alt="×" />
      </button>
    </div>
    <form
      @click.stop
      method="dialog"
      class="border-4 border-miby-light-blue mt-[-3px] md:mt-0 md:border-0 rounded-b-md px-2.5"
    >
      <div class="modalForm pt-5 pb-10 overflow-y-auto scroll-smooth h-full">
        <div class="max-w-[566px] mx-auto flex flex-wrap">
          <div v-for="column in columns" :key="column.name" class="checkbox">
            <input
              class="absolute"
              type="checkbox"
              name="field"
              :key="column.code"
              :value="column"
              :id="'category-' + column.name"
            />
            <label class="text-sm checkbox-label" :for="'category-' + column.name">{{
              column.value
            }}</label>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-center py-5 gap-4">
        <a
          id="seachClear"
          class="text-miby-black text-sm text-center font-medium border border-miby-black py-1.5 px-5 block min-w-[96px] rounded"
        >
          クリア
        </a>

        <button
          @click="submit"
          id="filtersubmit"
          class="text-white text-sm text-center bg-miby-orange border border-miby-orange font-medium py-1.5 px-5 block min-w-[96px] rounded"
        >
          適用
        </button>
      </div>
    </form>
  </dialog>
</template>

<style scoped lang="scss">
.btn-close {
  @apply absolute w-3.5 right-5;
  top: calc(50% - 7px);
}
.modalForm {
  max-height: calc(100vh - 200px);
}
</style>
