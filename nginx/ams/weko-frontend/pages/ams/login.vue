<template>
  <div class="relative flex flex-col justify-center h-screen bg-miby-dark-blue">
    <div class="w-full m-auto mb-5 flex justify-center cursor-pointer">
      <NuxtLink to="" event="" @click="throughDblClick">
        <img class="scale-150" :src="`${appConf.amsImage ?? '/img'}/logo/logo_w.svg`" alt="AMS Logo" />
      </NuxtLink>
    </div>
    <div
      v-if="!forgetPassFlag"
      class="w-full mt-5 p-6 m-auto bg-white rounded-md shadow-md ring-2 ring-gray-800/50 lg:max-w-lg">
      <h1 class="text-3xl text-center font-medium">
        {{ $t('login') }}
      </h1>
      <Form class="space-y-2 mt-3" @submit="login">
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
            :class="{ 'border-miby-form-red': dirtyEmail && checkEmail(email) !== true }"
            class="w-full input input-bordered mt-2 hover:[&:focus]:border-sky-700"
            @click="dirtyEmail = true" />
          <ErrorMessage v-slot="message" name="email">
            <span class="mr-auto text-miby-form-red">
              {{ '※' + $t(String(message.message)) }}
            </span>
          </ErrorMessage>
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
            :class="{ 'border-miby-form-red': dirtyPassword && checkPassword(password) !== true }"
            class="w-full input input-bordered mt-2 hover:[&:focus]:border-sky-700"
            @click="dirtyPassword = true" />
          <ErrorMessage v-slot="message" name="password">
            <span class="mr-auto text-miby-form-red">
              {{ '※' + $t(String(message.message)) }}
            </span>
          </ErrorMessage>
        </label>
        <!-- ログイン -->
        <div class="pt-3">
          <button
            class="btn btn-block font-medium text-lg text-white bg-miby-light-blue hover:bg-sky-700"
            @click="
              dirtyEmail = true;
              dirtyPassword = true;
            ">
            <img :src="`${appConf.amsImage ?? '/img'}/icon/icon_login.svg`" alt="Login" />
            {{ $t('login') }}
          </button>
        </div>
        <div class="flex">
          <!-- アカウント作成 -->
          <!-- <div class="flex justify-start flex-1">
            <a class="text-sm text-gray-600 hover:underline hover:text-sky-700 cursor-pointer">
              {{ $t('createAccount') }}
            </a>
          </div> -->
          <!-- パスワードを忘れた方はこちら -->
          <!-- <div class="flex justify-end flex-1">
            <a
              class="text-sm text-gray-600 hover:underline hover:text-sky-700 cursor-pointer"
              @click="
                forgetPassFlag = true;
                dirtyReset = false;
              ">
              {{ $t('forgetPassword') }}
            </a>
          </div> -->
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
              :class="{ 'border-miby-form-red': dirtyReset && checkEmail(reset) !== true }"
              class="w-full input input-bordered mt-2 hover:[&:focus]:border-sky-700"
              @click="dirtyReset = true" />
            <ErrorMessage v-slot="message" name="reset">
              <span class="mr-auto text-miby-form-red">
                {{ '※' + $t(String(message.message)) }}
              </span>
            </ErrorMessage>
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
    <Alert
      v-if="visibleAlert"
      :type="alertType"
      :message="alertMessage"
      :code="alertCode"
      @click-close="visibleAlert = !visibleAlert" />
  </div>
</template>

<script lang="ts" setup>
import { Form, Field, ErrorMessage } from 'vee-validate';

import Alert from '~/components/common/Alert.vue';

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const email = ref('');
const password = ref('');
const reset = ref('');
const forgetPassFlag = ref(false);
const visibleAlert = ref(false);
const alertType = ref('info');
const alertMessage = ref('');
const alertCode = ref(0);
const dirtyEmail = ref(false);
const dirtyPassword = ref(false);
const dirtyReset = ref(false);
const appConf = useAppConfig();

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * ログイン
 */
async function login() {
  let statusCode = 0;
    // 先にログアウト
    await $fetch(appConf.wekoApi + '/logout', {
      timeout: useRuntimeConfig().public.apiTimeout,
      method: 'POST',
    });
    // ログイン
    await $fetch(appConf.wekoApi + '/login', {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'POST',
    body: {
      email: email.value,
      password: password.value
    },
    onResponse({ response }) {
      if (response.status === 200) {
        const url = new URL(appConf.wekoOrigin + '/oauth/authorize');
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
      alertCode.value = 0;
      statusCode = response.status;
      if (statusCode === 400) {
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
      } else if (statusCode >= 500 && statusCode < 600) {
        // サーバーエラー
        alertMessage.value = 'message.error.server';
        alertCode.value = statusCode;
      } else {
        // リクエストエラー
        alertMessage.value = 'message.error.login';
        alertCode.value = statusCode;
      }
      alertType.value = 'error';
      visibleAlert.value = true;
    }
  }).catch(() => {
    if (statusCode === 0) {
      // fetchエラー
      alertMessage.value = 'message.error.fetch';
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
  // 未入力チェック
  if (!value) {
    return 'message.alert.requiredMail';
  }
  // 形式チェック
  // RFC5322準拠
  const regex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
  if (!regex.test(value)) {
    return 'message.alert.requiredMailType';
  }
  return true;
}

/**
 * パスワードのバリデーション
 * @param value 入力されたパスワード
 */
function checkPassword(value: any) {
  // 未入力チェック
  if (!value) {
    return 'message.alert.requiredPass';
  }
  return true;
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
