<template>
  <div class="relative flex flex-col justify-center h-screen bg-miby-dark-blue">
    <div class="w-full m-auto mb-5 flex justify-center">
      <NuxtLink to="/">
        <img class="scale-150" src="/img/logo/logo_w.svg" alt="AMS Logo" />
      </NuxtLink>
    </div>
    <div
      v-if="!forgetPassFlag"
      class="w-full mt-5 p-6 m-auto bg-white rounded-md shadow-md ring-2 ring-gray-800/50 lg:max-w-lg">
      <h1 class="text-3xl text-center font-medium">
        {{ $t('login') }}
      </h1>
      <form class="space-y-4 mt-2" @submit.prevent="login">
        <!-- メールアドレス -->
        <div>
          <label class="label">
            <span class="font-medium text-base label-text">
              {{ $t('mailAddress') }}
            </span>
          </label>
          <input
            v-model="email"
            type="text"
            :placeholder="$t('enterMailAddress')"
            class="w-full input input-bordered hover:border-sky-700 focus:border-sky-700" />
        </div>
        <!-- パスワード -->
        <div>
          <label class="label">
            <span class="font-medium text-base label-text">
              {{ $t('password') }}
            </span>
          </label>
          <input
            v-model="password"
            type="password"
            :placeholder="$t('enterPassword')"
            class="w-full input input-bordered hover:border-sky-700 focus:border-sky-700" />
        </div>
        <!-- ログイン -->
        <div class="pt-2">
          <button class="btn btn-block font-medium text-lg text-white bg-miby-light-blue hover:bg-sky-700">
            <img src="/img/icon/icon_login.svg" alt="Login" />
            {{ $t('login') }}
          </button>
        </div>
        <div class="flex">
          <!-- アカウント作成 -->
          <div class="flex justify-start flex-1">
            <a class="text-sm text-gray-600 hover:underline hover:text-sky-700 cursor-pointer">
              {{ $t('createAccount') }}
            </a>
          </div>
          <!-- パスワードを忘れた方はこちら -->
          <div class="flex justify-end flex-1">
            <a
              class="text-sm text-gray-600 hover:underline hover:text-sky-700 cursor-pointer"
              @click="forgetPassFlag = true">
              {{ $t('forgetPassword') }}
            </a>
          </div>
        </div>
      </form>
    </div>
    <div v-else class="w-full mt-5 p-6 m-auto bg-white rounded-md shadow-md ring-2 ring-gray-800/50 lg:max-w-lg">
      <h1 class="text-3xl text-center font-medium">
        {{ $t('resetPassword') }}
      </h1>
      <form class="space-y-4" @submit.prevent="login">
        <!-- メールアドレス -->
        <div>
          <div class="text-base label-text mt-5 mb-5">
            {{ $t('sendEmailResetPassword') }}
          </div>
          <label class="label">
            <span class="font-medium text-base label-text">
              {{ $t('mailAddress') }}
            </span>
          </label>
          <input
            type="text"
            :placeholder="$t('enterMailAddress')"
            class="w-full input input-bordered hover:border-sky-700 focus:border-sky-700" />
        </div>
        <!-- 送信 -->
        <div class="pt-2">
          <button class="btn btn-block font-medium text-lg text-white bg-miby-light-blue hover:bg-sky-700">送信</button>
        </div>
        <div>
          <a
            class="text-sm text-gray-600 hover:underline hover:text-sky-700 flex justify-center cursor-pointer"
            @click="forgetPassFlag = false">
            {{ $t('returnToLogin') }}
          </a>
        </div>
      </form>
    </div>
    <!-- アラート -->
    <Alert v-if="visibleAlert" :type="alertType" :message="alertMessage" @click-close="visibleAlert = !visibleAlert" />
  </div>
</template>

<script lang="ts" setup>
import Alert from '~/components/common/Alert.vue';

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const email = ref('');
const password = ref('');
const forgetPassFlag = ref(false);
const visibleAlert = ref(false);
const alertType = ref('info');
const alertMessage = ref('');

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * ログイン
 */
function login() {
  $fetch(useAppConfig().wekoApi + '/login', {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'POST',
    body: {
      email: email.value,
      password: password.value
    },
    onResponse({ response }) {
      if (response.status === 200) {
        const url = new URL(useAppConfig().wekoOrigin + '/oauth/authorize');
        const random = Math.random().toString(36);
        url.searchParams.append('response_type', 'code');
        url.searchParams.append('client_id', useRuntimeConfig().public.clientId);
        url.searchParams.append('scope', 'item:read index:read ranking:read file:read user:email');
        url.searchParams.append('state', random);
        sessionStorage.setItem('login:state', random);
        window.open(url.href, '_self');
      }
    },
    onResponseError({ response }) {
      if (response.status === 400) {
        // ログイン済の場合、認可画面に遷移
        // TODO: ログイン済専用のステータスコードが必要
        // const url = new URL(useAppConfig().wekoOrigin + '/oauth/authorize');
        // const random = Math.random().toString(36);
        // url.searchParams.append('response_type', 'code');
        // url.searchParams.append('client_id', useRuntimeConfig().public.clientId);
        // url.searchParams.append('scope', 'item:read index:read ranking:read file:read user:email');
        // url.searchParams.append('state', random);
        // sessionStorage.setItem('login:state', random);
        // window.open(url.href, '_self');
      } else if (Number(response.status) >= 500 && Number(response.status) < 600) {
        alertMessage.value =
          '(Status Code : ' + response.status + ')' + ' サーバエラーが発生しました。管理者に連絡してください。';
      } else {
        alertMessage.value = '(Status Code : ' + response.status + ')' + ' ログインに失敗しました。';
      }
      alertType.value = 'error';
      visibleAlert.value = true;
    }
  });
}

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

definePageMeta({
  layout: false
});
</script>
