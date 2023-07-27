<script setup>
import { onMounted, ref } from "vue";
import ButtonClose from "/images/btn/btn-close.svg";

const filterCheckboxes = ref([])

onMounted(() => {
  filterCheckboxes.value = document.querySelectorAll('.filter-checkbox')
})

const hideCheckBoxesThenClose = () => {
  filterCheckboxes.value.forEach((checkbox) => {
    checkbox.style.display = 'none'
  })
}
const showCheckBoxesWhenOpen = () => {
  filterCheckboxes.value.forEach((checkbox) => {
    checkbox.style.display = 'flex'
  })
}
async function closeFilterModal() {
  hideCheckBoxesThenClose()
  document.body.classList.remove("overflow-hidden");
  document.getElementById("modalFilter").close();
}
const submit = () => {
  //submit機能
  closeFilterModal()
}

defineExpose({
  showCheckBoxesWhenOpen
})
</script>
<template>
  <dialog @click="closeFilterModal" id="modalFilter" class="w-11/12 md:w-full max-w-[728px] mx-auto z-10">
    <div @click.stop class="bg-miby-light-blue w-full rounded-t relative">
      <p class="text-white leading-[43px] pl-5 text-center font-medium relative">フィルター</p>
      <button id="" type="button" class="btn-close" @click="closeFilterModal">
        <img :src="ButtonClose" alt="×" />
      </button>
    </div>
    <form
      @click.stop
      method="dialog"
      class="border-4 border-miby-light-blue mt-[-3px] md:mt-0 md:border-0 rounded-b-md px-2.5"
    >
      <div class="modalForm pt-2.5 overflow-y-auto scroll-smooth h-full">
        <div class="max-w-full mx-auto p-5">
          <div id="" class="mb-5">
            <button class="block mb-2 removeForm text-miby-black text-sm font-medium">
              <span class="icons icon-minus align-middle">配布者</span>
            </button>
            <div class="pl-5">
              <div class="block checkbox filter-checkbox">
                <input
                  class="absolute"
                  type="checkbox"
                  name="publish-type"
                  id="type-group"
                  checked
                />
                <label class="text-sm checkbox-label" for="type-group"
                  >〇〇大学経済研究所（34293）</label
                >
              </div>
              <div class="block checkbox filter-checkbox">
                <input class="absolute" type="checkbox" name="publish-type" id="type-publish" />
                <label class="text-sm checkbox-label" for="type-publish"
                  >〇〇大学史料編纂所（1799）</label
                >
              </div>
              <div class="block checkbox filter-checkbox">
                <input class="absolute" type="checkbox" name="publish-type" id="type-private" />
                <label class="text-sm checkbox-label" for="type-private"
                  >JGSS研究センター（75）</label
                >
              </div>
              <div class="block checkbox filter-checkbox">
                <input class="absolute" type="checkbox" name="publish-type" id="type-limited" />
                <label class="text-sm checkbox-label" for="type-limited"
                  >〇〇大学パネルデータ設計・解析センター（47）</label
                >
              </div>
            </div>
          </div>
          <div id="" class="mb-5">
            <button class="block mb-2 removeForm text-miby-black text-sm font-medium">
              <span class="icons icon-minus align-middle">データの言語</span>
            </button>
            <div class="pl-5">
              <div class="block checkbox filter-checkbox">
                <input
                  class="absolute"
                  type="checkbox"
                  name="publish-type"
                  id="type-group"
                  checked
                />
                <label class="text-sm checkbox-label" for="type-group">jp（34293）</label>
              </div>
              <div class="block checkbox filter-checkbox">
                <input class="absolute" type="checkbox" name="publish-type" id="type-publish" />
                <label class="text-sm checkbox-label" for="type-publish">en（1799）</label>
              </div>
            </div>
          </div>
          <div id="" class="mb-5">
            <button class="block mb-2 removeForm text-miby-black text-sm font-medium">
              <span class="icons icon-minus align-middle">アクセス権</span>
            </button>
            <div class="pl-5">
              <div class="block checkbox filter-checkbox">
                <input
                  class="absolute"
                  type="checkbox"
                  name="publish-type"
                  id="type-group"
                  checked
                />
                <label class="text-sm checkbox-label" for="type-group"
                  >metadata only（34293）</label
                >
              </div>
              <div class="block checkbox filter-checkbox">
                <input class="absolute" type="checkbox" name="publish-type" id="type-publish" />
                <label class="text-sm checkbox-label" for="type-publish">open（1799）</label>
              </div>
              <div class="block checkbox filter-checkbox">
                <input class="absolute" type="checkbox" name="publish-type" id="type-publish" />
                <label class="text-sm checkbox-label" for="type-publish">restricted（75）</label>
              </div>
            </div>
          </div>
          <div id="" class="mb-5">
            <button class="block mb-2 removeForm text-miby-black text-sm font-medium">
              <span class="icons icon-minus align-middle">対象地域</span>
            </button>
            <div class="pl-5 mt-5">
              <select id="" class="border border-miby-dark-gray rounded text-sm block w-[160px]">
                <option selected>選択してください</option>
                <option value="">北海道</option>
                <option value="">岩手県</option>
                <option value="">青森県</option>
              </select>
            </div>
          </div>
          <div id="" class="mb-5">
            <button class="block mb-2 removeForm text-miby-black text-sm font-medium">
              <span class="icons icon-minus align-middle">対象時期</span>
            </button>
            <div class="pl-5 mt-5 flex flex-wrap items-center">
              <div class="relative">
                <input
                  name="start"
                  type="text"
                  value="1875"
                  class="border border-miby-thin-gray text-miby-black text-sm py-2.5 px-5 h-7 w-[160px] rounded focus:ring-miby-orange focus:border-miby-orange"
                />
              </div>
              <span class="hidden sm:block pl-1.5 align-top w-full md:w-[24px]">— </span>
              <span class="sm:hidden pl-1.5 align-top w-full md:w-[24px] mb-0.5">|</span>
              <div class="relative">
                <input
                  name="end"
                  type="text"
                  value="2023"
                  class="border border-miby-thin-gray text-miby-black text-sm py-2.5 px-5 h-7 w-[160px] rounded focus:ring-miby-orange focus:border-miby-orange"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-center pb-15 gap-4">
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
