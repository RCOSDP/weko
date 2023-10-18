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
      <Form class="space-y-4 mt-2" @submit="login">
        <!-- メールアドレス -->
        <label class="label flex-col">
          <span class="font-medium text-base label-text mr-auto">
            {{ $t('mailAddress') }}
          </span>
          <Field
            v-model="email"
            name="email"
            type="email"
            :rules="checkEmail"
            :placeholder="$t('enterMailAddress')"
            :class="{ 'border-red-600': dirtyEmail && checkEmail(email) !== true }"
            class="w-full input input-bordered mt-2 hover:[&:focus]:border-sky-700"
            @click="dirtyEmail = true" />
          <ErrorMessage name="email" class="mr-auto text-red-600" />
        </label>
        <!-- パスワード -->
        <label class="label flex-col">
          <span class="font-medium text-base label-text mr-auto">
            {{ $t('password') }}
          </span>
          <Field
            v-model="password"
            name="password"
            type="password"
            :rules="checkPassword"
            :placeholder="$t('enterPassword')"
            :class="{ 'border-red-600': dirtyPassword && checkPassword(password) !== true }"
            class="w-full input input-bordered mt-2 hover:[&:focus]:border-sky-700"
            @click="dirtyPassword = true" />
          <ErrorMessage name="password" class="mr-auto text-red-600" />
        </label>
        <!-- ログイン -->
        <div class="pt-3">
          <button
            class="btn btn-block font-medium text-lg text-white bg-miby-light-blue hover:bg-sky-700"
            @click="
              dirtyEmail = true;
              dirtyPassword = true;
            ">
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
              @click="
                forgetPassFlag = true;
                dirtyReset = false;
              ">
              {{ $t('forgetPassword') }}
            </a>
          </div>
        </div>
      </Form>
    </div>
    <div v-else class="w-full mt-5 p-6 m-auto bg-white rounded-md shadow-md ring-2 ring-gray-800/50 lg:max-w-lg">
      <h1 class="text-3xl text-center font-medium">
        {{ $t('resetPassword') }}
      </h1>
      <Form class="space-y-4">
        <!-- メールアドレス -->
        <div>
          <div class="text-base label-text mt-5 mb-5">
            {{ $t('sendEmailResetPassword') }}
          </div>
          <label class="label flex-col">
            <span class="font-medium text-base label-text mr-auto">
              {{ $t('mailAddress') }}
            </span>
            <Field
              v-model="reset"
              name="reset"
              type="text"
              :rules="checkEmail"
              :placeholder="$t('enterMailAddress')"
              :class="{ 'border-red-600': dirtyReset && checkEmail(reset) !== true }"
              class="w-full input input-bordered mt-2 hover:[&:focus]:border-sky-700"
              @click="dirtyReset = true" />
            <ErrorMessage name="reset" class="mr-auto text-red-600" />
          </label>
        </div>
        <!-- 送信 -->
        <div class="pt-2">
          <button
            class="btn btn-block font-medium text-lg text-white bg-miby-light-blue hover:bg-sky-700"
            @click="dirtyReset = true">
            {{ $t('send') }}
          </button>
        </div>
        <div>
          <a
            class="text-sm text-gray-600 hover:underline hover:text-sky-700 flex justify-center cursor-pointer"
            @click="
              forgetPassFlag = false;
              dirtyEmail = false;
              dirtyPassword = false;
            ">
            {{ $t('returnToLogin') }}
          </a>
        </div>
      </Form>
    </div>
    <!-- アラート -->
    <Alert v-if="visibleAlert" :type="alertType" :message="alertMessage" @click-close="visibleAlert = !visibleAlert" />
  </div>
</template>

<script lang="ts" setup>
import { Form, Field, ErrorMessage } from 'vee-validate';
import { useI18n } from 'vue-i18n';

import Alert from '~/components/common/Alert.vue';

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const mRequiredField = useI18n().t('requiredField');
const mRequiredEmail = useI18n().t('requiredEmail');
const email = ref('');
const password = ref('');
const reset = ref('');
const forgetPassFlag = ref(false);
const visibleAlert = ref(false);
const alertType = ref('info');
const alertMessage = ref('');
const dirtyEmail = ref(false);
const dirtyPassword = ref(false);
const dirtyReset = ref(false);

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

/**
 * メールアドレスのバリデーション
 * @param value 入力されたメールアドレス
 */
function checkEmail(value: any) {
  if (!value) {
    return mRequiredField;
  }
  // RFC5322準拠
  const regex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
  if (!regex.test(value)) {
    return mRequiredEmail;
  }
  return true;
}

/**
 * パスワードのバリデーション
 * @param value 入力されたパスワード
 */
function checkPassword(value: any) {
  if (!value) {
    return mRequiredField;
  }
  return true;
}

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

definePageMeta({
  layout: false
});
</script>
