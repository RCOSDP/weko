<template>
  <div class="relative flex flex-col justify-center h-screen bg-miby-dark-blue">
    <div class="w-full m-auto mb-5 flex justify-center cursor-pointer">
      <NuxtLink to="" event="" @click="throughDblClick">
        <img class="scale-150" :src="`${appConf.amsImage ?? '/img'}/logo/logo_w.svg`" alt="AMS Logo" />
      </NuxtLink>
    </div>
    <div
      v-if="!isLogout"
      class="w-full mt-5 p-6 m-auto bg-white rounded-md shadow-md ring-2 ring-gray-800/50 lg:max-w-lg">
      <h1 class="text-3xl text-center font-medium">{{ $t('logoutConfirmation') }}</h1>
      <div class="flex justify-center mt-2 p-3">
        <!-- ログアウトボタン -->
        <div class="pt-2">
          <button
            class="btn w-48 mr-5 font-medium text-lg text-white bg-miby-light-blue hover:bg-sky-700"
            @click="logout">
            <img :src="`${appConf.amsImage ?? '/img'}/icon/icon_login.svg`" alt="Logout" />
            {{ $t('logout') }}
          </button>
        </div>
        <!-- キャンセル -->
        <div class="pt-2">
          <button
            class="btn w-48 ml-5 font-medium text-lg text-white bg-gray-400 hover:bg-gray-700"
            @click="$router.back()">
            {{ $t('cancel') }}
          </button>
        </div>
      </div>
    </div>
    <div v-else class="w-full mt-5 p-6 m-auto bg-white rounded-md shadow-md ring-2 ring-gray-800/50 lg:max-w-lg">
      <h1 class="text-3xl text-center font-medium">{{ $t('loggedOut') }}</h1>
      <!-- 戻る -->
      <div class="mt-5">
        <button
          class="btn btn-block font-medium text-lg text-white bg-gray-400 hover:bg-gray-700"
          @click="throughDblClick">
          {{ $t('returnToTop') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const isLogout = ref(false);
const appConf = useAppConfig();

/* ///////////////////////////////////
// function
/////////////////////////////////// */

function logout() {
  $fetch(appConf.wekoApi + '/logout', {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'POST',
    onResponse() {
      localStorage.removeItem('token:type');
      localStorage.removeItem('token:access');
      localStorage.removeItem('token:refresh');
      localStorage.removeItem('token:expires');
      localStorage.removeItem('token:issue');
      sessionStorage.removeItem('login:state');
      isLogout.value = true;
    }
  });
}

/**
 * ダブルクリックを制御する
 */
function throughDblClick() {
  if (location.pathname !== '/') {
    navigateTo('/');
  }
}

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

definePageMeta({
  layout: false
});
</script>
