<script setup>
import Logo1 from "/images/logo/logo_b.png";
import Logo2 from "/images/logo/logo02.png";
import ButtonClose from "/images/btn/btn-close.svg";
import BtnLogout from "/images/btn/btn-logout.svg"
import ButtonIndex from "/images/btn/btn-index.svg";
import IndexTreeCard from "../IndexTree/IndexTreeCard.vue"
import debounce from "lodash.debounce";
import throttle from "lodash.throttle";
import { onMounted, ref } from 'vue'

const res = await fetch('https://ams-dev.ir.rcos.nii.ac.jp/api/v1.0/tree/index/0')
const allItems = await res.json()

const isScrolled = ref(false)
const handleScroll = throttle(() => {
  if (window.innerWidth > 1023 && window.scrollY >= 140) {
    isScrolled.value = true;
  } else {
    isScrolled.value = false;
  }
}, 200)

onMounted(() => {
  document.addEventListener('scroll', handleScroll)
})

const mobileMenuBtn = ref()

const toggleTree = () => {
  mobileMenuBtn.value.classList.toggle("active");
  if (mobileMenuBtn.value.classList.contains("active")) {
      document.getElementById("MobileMenu").showModal();
      document.body.classList.add("overflow-hidden");
    } else {
      document.body.classList.remove("overflow-hidden");
      document.getElementById("MobileMenu").close();
    }
}

const linkLang = ref()
const toggleLang = () => {
  linkLang.value.classList.toggle("hidden");
}
// const closeButton = document.getElementById('mobile-close-btn')
//   closeButton.addEventListener('click', closeModal)
//   function closeModal() {
//     document.getElementById('MobileMenu').close();
//     mobileMenuBtn?.classList.toggle("active");
//     document.body.classList.remove("overflow-hidden");
//   }
</script>

<template>
  <div :class="isScrolled ? 'scroll z-10' : ''" class="index-tree w-full">
    <div class="flex absolute gap-4 min-[1022px]:gap-0 top-3 right-3 min-[1022px]:top-6" :class="{'scrolled-header': isScrolled == true}">
      <div class="relative">
        <button @click="toggleLang" class="hidden min-[1022px]:block btn-lang icons icon-lang text-sm text-white py-1 px-3">JP</button>
        <button @click="toggleLang" class="min-[1022px]:hidden btn-lang icons icon-lang text-sm text-white py-1 w-auto mr-2"></button>
        <div ref="linkLang" class="absolute w-12 top-full mt-1 bg-white text-sm rounded hidden">
          <p class="px-3 py-1 text-white bg-miby-orange w-full rounded-tl rounded-tr">JP</p>
          <a class="block px-3 py-1 text-miby-black w-full" href="/en">EN</a>
        </div>
      </div>
      <button class="hidden min-[1022px]:block h-5 min-[1022px]:h-auto min-[1022px]:border min-[1022px]:py-1 pl-2 pr-2.5 rounded">
        <img :src="BtnLogout" alt="ログアウト" />
      </button>
      <button class="block min-[1022px]:hidden h-5 min-[1022px]:h-auto min-[1022px]:border min-[1022px]:py-1 pl-2 pr-2.5 rounded icons icon-logout">
      </button>
      <button ref="mobileMenuBtn" @click="toggleTree" class="btn-sp-menu block min-[1022px]:hidden">
        <span class="inline-block h-[1px] w-full bg-white"></span>
        <span class="inline-block h-[1px] w-full bg-white"></span>
        <span class="inline-block h-[1px] w-full bg-white"></span>
      </button>
      <button @click="toggleTree" class="hidden min-[1022px]:block ml-4">
        <img :src="ButtonIndex" alt="インデックス">
      </button>
    </div>
  </div>
  
  <dialog @click="toggleTree" id="MobileMenu">
    <div class="modal-left">
      <button @click.stop="toggleTree" id="mobile-close-btn" class="btn-close min-[1022px]:mr-6 min-[1022px]:mt-6">
        <img :src=ButtonClose alt="close" />
      </button>
      <div @click.stop class="wrapper">
        <!-- <div class="flex flex-wrap items-end border-b border-miby-thin-gray p-2.5 mb-2.5">
          <p class="mr-[5px]">
            <a href="/"><img src={Logo1} alt="MIBY" /></a>
          </p>
          <p class="mr-[5px]">
            <a href="/"><img src={Logo2} alt="MIBY" /></a>
          </p>
          <p class="text-miby-black text-xs w-full">未病データベースタイトル＆キャッチコピー</p>
        </div>
        <div class="p-5">
          <i class="icons icon-lang-b"></i>
          <span class="ml-2.5 mr-5 text-miby-orange underline">JP</span>
          <a class="text-miby-thin-gray" href="/en">EN</a>
        </div>
        <div class="w-full bg-miby-mobile-blue py-1 pl-5">
          <img src={ButtonIndex} alt="インデックスツリー">
        </div> -->
        <div class="index-tree__list p-2.5">
          <div v-for="item in allItems.children">
              <IndexTreeCard :indexes="item" />
          </div>
        </div>
      </div>
    </div>
  </dialog>
</template>

<style scoped>
.scrolled-header{
  top: 12px;
}
</style>