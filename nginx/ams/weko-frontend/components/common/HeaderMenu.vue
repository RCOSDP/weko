<template>
  <div :class="isScrolled ? 'scroll z-10' : ''" class="index-tree w-full">
    <div
      class="flex absolute gap-4 min-[1022px]:gap-0 top-3 right-3 min-[1022px]:top-6"
      :class="{ 'scrolled-header': isScrolled == true }">
      <!-- 言語選択 -->
      <div class="relative mr-1 cursor-pointer">
        <details id="dropdown_lang" class="dropdown">
          <summary class="min-[1022px]:block btn-lang icons icon-lang text-sm text-white px-3 py-1">
            {{ selectedLocale }}
          </summary>
          <ul class="p-2 shadow menu dropdown-content z-[1] bg-base-100 rounded-box w-18">
            <li v-for="item in langList" :key="item.id" @click="selectLocal(item.lang)">
              <a class="block px-3 py-1 text-miby-black w-full">
                {{ item.lang }}
              </a>
            </li>
          </ul>
        </details>
      </div>
      <!-- ログイン/ログアウト -->
      <button
        v-if="!isLogin"
        class="hidden min-[1022px]:block h-5 min-[1022px]:h-auto min-[1022px]:border min-[1022px]:py-1 pl-2 pr-2.5 rounded text-white text-xs font-light icons icon-in"
        @click="navigateTo(`${appConf.amsPath ?? ''}/login`)">
        {{ $t('login') }}
      </button>
      <button
        v-else
        class="hidden min-[1022px]:block h-5 min-[1022px]:h-auto min-[1022px]:border min-[1022px]:py-1 pl-2 pr-2.5 rounded text-white text-xs font-light icons icon-out"
        @click="navigateTo(`${appConf.amsPath ?? ''}/logout`)">
        {{ $t('logout') }}
      </button>
      <!-- ログイン/ログアウト（縮小版） -->
      <button
        v-if="!isLogin"
        class="block min-[1022px]:hidden h-5 min-[1022px]:h-auto min-[1022px]:border min-[1022px]:py-1 pl-2 pr-2.5 rounded icons icon-in"
        @click="navigateTo(`${appConf.amsPath ?? ''}/login`)" />
      <button
        v-else
        class="block min-[1022px]:hidden h-5 min-[1022px]:h-auto min-[1022px]:border min-[1022px]:py-1 pl-2 pr-2.5 rounded icons icon-out"
        @click="navigateTo(`${appConf.amsPath ?? ''}/logout`)" />
      <!-- インデックスツリーボタン -->
      <button
        class="hidden min-[1022px]:block ml-4 h-5 min-[1022px]:h-auto min-[1022px]:border min-[1022px]:py-1 pl-2 pr-2.5 text-white text-xs font-light icons icon-menu indexbutton"
        @click="changeModalState">
        {{ $t('index') }}
      </button>
      <!-- インデックスツリーボタン（縮小版） -->
      <button ref="menuBtn" class="btn-sp-menu block min-[1022px]:hidden" @click="changeModalState">
        <span class="inline-block h-[1px] w-full bg-white" />
        <span class="inline-block h-[1px] w-full bg-white" />
        <span class="inline-block h-[1px] w-full bg-white" />
      </button>
    </div>
    <!-- インデックスツリー（モーダル） -->
    <dialog id="MobileMenu" @click="changeModalState">
      <div class="modal-left">
        <button
          id="mobile_close_btn"
          class="btn-close min-[1022px]:mr-6 min-[1022px]:mt-6"
          @click.stop="changeModalState">
          <img :src="`${appConf.amsImage ?? '/img'}/btn/btn-close.svg`" alt="Close" />
        </button>
        <div class="wrapper" @click.stop>
          <div class="index-tree__list p-2.5">
            <div v-for="item in indexes" :key="item">
              <IndexTree :index="item" @click-index="changeModalState" />
            </div>
          </div>
        </div>
      </div>
    </dialog>
  </div>
</template>

<script lang="ts" setup>
import { useI18n } from 'vue-i18n';

import IndexTree from '~/components/common/IndexTree.vue';

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const { t, locale } = useI18n({ useScope: 'global' }); // eslint-disable-line
const langList = [
  { id: 1, lang: 'ja' },
  { id: 2, lang: 'en' }
];
const isScrolled = ref(false);
const isLogin = ref(false);
const selectedLocale = ref(localStorage.getItem('locale') ?? locale.value);
const menuBtn = ref();
let indexes = {};
const appConf = useAppConfig();

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * 言語選択時イベント
 * @param lang 選択した言語
 */
function selectLocal(lang: string) {
  if (selectedLocale.value !== lang) {
    selectedLocale.value = lang;
    locale.value = lang;
    localStorage.setItem('locale', String(locale.value));
    location.reload();
  }
  (document.getElementById('dropdown_lang') as HTMLDataElement).removeAttribute('open');
}

/**
 * インデックスツリーのモーダル表示状態変更
 */
function changeModalState() {
  menuBtn.value.classList.toggle('active');
  if (menuBtn.value.classList.contains('active')) {
    (document.getElementById('MobileMenu') as HTMLDialogElement).showModal();
    document.body.classList.add('overflow-hidden');
  } else {
    document.body.classList.remove('overflow-hidden');
    (document.getElementById('MobileMenu') as HTMLDialogElement).close();
  }
}

/* ///////////////////////////////////
// main
/////////////////////////////////// */

try {
  await $fetch(useAppConfig().wekoApi + '/tree/index', {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'GET',
    credentials: 'omit',
    headers: {
      'Cache-Control': 'no-store',
      Pragma: 'no-cache',
      'Accept-Language': localStorage.getItem('locale') ?? 'ja',
      Authorization: localStorage.getItem('token:type') + ' ' + localStorage.getItem('token:access')
    },
    onResponse({ response }) {
      if (response.status === 200) {
        indexes = response._data.index.children;
      }
    }
  });
} catch (error) {
  // console.log(error);
}

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

onMounted(() => {
  // ログイン/ログアウト
  const expires = Number(localStorage.getItem('token:expires'));
  const issue = Number(localStorage.getItem('token:issue')) ?? 0;
  if (expires) {
    if (issue + expires * 1000 >= Date.now()) {
      isLogin.value = true;
    } else {
      isLogin.value = false;
    }
  } else {
    isLogin.value = false;
  }
  // 言語設定
  if (localStorage.getItem('locale')) {
    locale.value = String(localStorage.getItem('locale'));
  }
  // スクロール設定
  document.addEventListener('scroll', () => {
    if (window.innerWidth > 1023 && window.scrollY >= 140) {
      isScrolled.value = true;
    } else {
      isScrolled.value = false;
    }
  });
});
</script>

<style scoped>
.scrolled-header {
  top: 12px;
}
</style>
