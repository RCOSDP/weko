<script setup>
import { onMounted, ref } from "vue";
import ButtonClose from "/images/btn/btn-close.svg";

const fileListCheckboxes = ref([])
const fileListRef = ref()
onMounted(() => {
  fileListCheckboxes.value = document.querySelectorAll('.filelist-checkbox')
})

const hideCheckBoxesThenClose = () => {
  fileListCheckboxes.value.forEach((checkbox) => {
    checkbox.style.display = 'none'
  })
}

const showCheckBoxesWhenOpen = () => {
  fileListCheckboxes.value.forEach((checkbox) => {
    checkbox.style.display = 'flex'
  })
}

function closeFilterModal() {
  hideCheckBoxesThenClose()
  document.getElementById("modalFilterFileList").close();
  showCheckBoxesWhenOpen()
  document.body.classList.remove("overflow-hidden");
}

</script>
<template>
  <dialog ref="fileListRef" @click.stop="closeFilterModal" id="modalFilterFileList" class="w-11/12 md:w-full max-w-[728px] mx-auto z-10">
    <div class="bg-miby-light-blue w-full rounded-t relative">
      <p class="text-white leading-[43px] pl-5 text-center font-medium relative">フィルター</p>
      <button id="" type="button" class="btn-close" @click="closeFilterModal">
        <img :src="ButtonClose" alt="×" />
      </button>
    </div>
    <form
      method="dialog"
      class="max-w-[500px] mx-auto border-4 border-miby-light-blue mt-[-3px] md:mt-0 md:border-0 rounded-b-md"
    >
      <div class="modalForm pt-5 pb-10 overflow-y-auto scroll-smooth h-full">
        <div class="max-w-full mx-auto p-5">
          <div class="my-[15px] flex flex-wrap items-center gap-1">
            <input class="" type="checkbox" name="publish-type" checked />
            <label class="text-sm text-miby-black font-medium">ファイル名</label>
            <input
              type="text"
              class="py-2.5 px-5 text-sm text-miby-black rounded w-[348px] placeholder:text-miby-thin-gray h-10 border border-miby-thin-gray"
              placeholder="テキストテキストテキストテキストテキストテキ..."
            />
          </div>
          <div class="my-[15px] flex flex-wrap items-center gap-1">
            <input class="" type="checkbox" name="publish-type" checked />
            <label class="text-sm text-miby-black font-medium">ファイルサイズ</label>
            <input
              type="text"
              class="py-2.5 px-2.5 text-sm text-miby-black rounded w-[70px] placeholder:text-miby-thin-gray h-10 border border-miby-thin-gray"
              placeholder=""
              value="999KB"
            />
            <span class="w-full lg:w-[34px] px-2.5 align-top">—</span>
            <input
              type="text"
              class="py-2 px-2.5 text-sm text-miby-black rounded w-[70px] placeholder:text-miby-thin-gray h-10 border border-miby-thin-gray"
              placeholder=""
              value="999KB"
            />
          </div>
          <div class="my-[15px] flex flex-wrap items-center gap-1">
            <input class="" type="checkbox" name="publish-type" />
            <label class="text-sm text-miby-dark-gray font-medium">ファイル形式</label>
            <div class="flex flex-wrap ml-2.5 w-full">
              <div class="checkbox">
                <input class="absolute" type="checkbox" name="publish-type" id="type-group" />
                <label class="text-sm checkbox-label filelist-checkbox miby-dark-gray" for="type-group">csv</label>
              </div>
              <div class="checkbox">
                <input class="absolute" type="checkbox" name="publish-type" id="type-publish" />
                <label class="text-sm checkbox-label filelist-checkbox miby-dark-gray" for="type-publish">xlsx</label>
              </div>
              <div class="checkbox">
                <input class="absolute" type="checkbox" name="publish-type" id="type-private" />
                <label class="text-sm checkbox-label filelist-checkbox miby-dark-gray" for="type-private">png</label>
              </div>
              <div class="checkbox">
                <input class="absolute" type="checkbox" name="publish-type" id="type-limited" />
                <label class="text-sm checkbox-label filelist-checkbox miby-dark-gray" for="type-limited"
                  >mpeg4</label
                >
              </div>
            </div>
          </div>
          <div class="my-[15px] flex flex-wrap items-center gap-1">
            <input class="" type="checkbox" name="publish-type" checked />
            <label class="text-sm text-miby-black font-medium">ダウンロード区分</label>
            <div class="flex flex-wrap ml-2.5 w-full">
              <div class="checkbox">
                <input class="absolute" type="checkbox" name="publish-type" id="type-group" />
                <label class="text-sm checkbox-label filelist-checkbox miby-dark-gray" for="type-group">無制限</label>
              </div>
              <div class="checkbox">
                <input class="absolute" type="checkbox" name="publish-type" id="type-publish" checked />
                <label class="text-sm checkbox-label filelist-checkbox miby-black" for="type-publish">利用許可申請必要</label>
              </div>
              <div class="checkbox">
                <input class="absolute" type="checkbox" name="publish-type" id="type-private" />
                <label class="text-sm checkbox-label filelist-checkbox miby-dark-gray" for="type-private">守秘義務契約必要</label>
              </div>
            </div>
          </div>
          <div class="my-[15px] flex flex-wrap items-center gap-1">
            <input class="" type="checkbox" name="publish-type" checked />
            <label class="text-sm text-miby-black font-medium">ライセンス</label>
            <div class="flex flex-wrap ml-2.5 w-full">
              <div class="checkbox">
                <input class="absolute" type="checkbox" name="publish-type" id="type-group" />
                <label class="text-sm checkbox-label filelist-checkbox miby-dark-gray" for="type-group">あり</label>
              </div>
              <div class="checkbox">
                <input class="absolute" type="checkbox" name="publish-type" id="type-private" />
                <label class="text-sm checkbox-label filelist-checkbox miby-dark-gray" for="type-private">なし</label>
              </div>
            </div>
          </div>
          <div class="my-[15px] flex flex-wrap items-center gap-1">
            <input class="" type="checkbox" name="publish-type" checked />
            <label class="text-sm text-miby-black font-medium">ダウンロード回数</label>
            <input
              type="text"
              class="py-2.5 px-2.5 text-sm text-miby-black rounded w-[120px] placeholder:text-miby-thin-gray h-10 border border-miby-thin-gray"
              placeholder=""
              value="9,999,999,999"
            />
            <span class="w-full lg:w-[34px] px-2.5 align-top">—</span>
            <input
              type="text"
              class="py-2 px-2.5 text-sm text-miby-black rounded w-[120px] placeholder:text-miby-thin-gray h-10 border border-miby-thin-gray"
              placeholder=""
              value="9,999,999,999"
            />
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
