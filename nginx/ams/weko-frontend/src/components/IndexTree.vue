<script setup>
const stabMenu = [];
import ButtonClose from "/images/btn/btn-close.svg";
import ButtonIndex from "/images/btn/btn-indextree.svg";
import IndexTreeCard from './IndexTree/IndexTreeCard.vue'
import { defineComponent, onMounted } from "vue";
import { onKeyStroke, onClickOutside } from "@vueuse/core";
import { ref } from "vue";

const isIndexTreeBtnViewFlg = ref(false);
const isIndexTreeModalShow = ref(false);
const IndexTreeRef = ref(null);

const handleIndexValue = () => {
  if (window.innerWidth > 768 && window.scrollY >= 140) {
    isIndexTreeBtnViewFlg.value = true;
  } else {
    isIndexTreeBtnViewFlg.value = false;
  }
};

// const onOpenIndexTree = (bool = false) => {
//  if(bool){
//   isIndexTreeBtnViewFlg.value = ref(true);
//  }

//  console.log(isIndexTreeBtnViewFlg);
//  return isIndexTreeBtnViewFlg;
// }

const onOpenIndexTree = () => {
  isIndexTreeBtnViewFlg.value = true;
  isIndexTreeModalShow.value = true;
  loadIndexTree()
};

const onCloseIndexTree = () => {
  // todo is-openを削除→ダイアログを非表示、#IndexTreeからshowをなくす
  isIndexTreeModalShow.value = false;
  handleIndexValue();
};

onMounted(() => {
  window.addEventListener("scroll", handleIndexValue);
});

onKeyStroke("Escape", (e) => {
  onCloseIndexTree();
});

onClickOutside(IndexTreeRef, () => {
  onClose();
});
const allItems = ref([])
const loadIndexTree = async () => {
  const res = await fetch('https://ams-dev.ir.rcos.nii.ac.jp/api/v1.0/tree/index/0')
  allItems.value = await res.json()
}
</script>

<template>
  <dialog id="IndexTreeContent" :class="[isIndexTreeModalShow ? 'visible z-5 relative is-open' : 'invisible']">
    <div class="modal-left" :class="[isIndexTreeModalShow ? 'is-open' : '']">
      <button class="btn-close" @click="onCloseIndexTree">
        <img :src="ButtonClose" alt="close" />
      </button>
      <div class="wrapper">
        <div v-for="item in allItems.children" :key="item.id">
          <IndexTreeCard :indexes="item" />
        </div>
      </div>
    </div>
    <div class="backdrop"></div>
  </dialog>
  <div
    id="IndexTree"
    class="hidden md:block index-tree w-full"
    :class="[isIndexTreeModalShow ? 'show z-10' : (isIndexTreeBtnViewFlg ? 'scroll' : '')]"
  >
    <button class="pl-5 pt-1.5" @click="onOpenIndexTree(true)">
      <img :src="ButtonIndex" alt="インデックスツリー" />
    </button>
  </div>
</template>