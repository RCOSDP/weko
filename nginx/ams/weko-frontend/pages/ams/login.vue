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
      <div class="flex justify-center items-center">
        <label>{{ $t('Institutional Login for institutions in Japan.') }}</label>
        <img src="https://www.gakunin.jp/themes/custom/gakunin/logo.svg" style="vertical-align: baseline; width: 100px !important" />
      </div>

      <!-- EMBEDDED-WAYF-START -->
      <div id="wayf_div" ref="scriptContainer"></div>
      <!-- EMBEDDED-WAYF-END -->

      <div class="text-divider">OR</div>
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
const alertCode = ref('');
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
      alertCode.value = '';
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
        alertCode.value = 'E_LOGIN_0001';
      } else {
        // リクエストエラー
        alertMessage.value = 'message.error.login';
        alertCode.value = 'E_LOGIN_0002';
      }
        alertType.value = 'error';
        visibleAlert.value = true;
    },
  }).catch(() => {
    if (statusCode === 0) {
      // fetchエラー
      alertMessage.value = 'message.error.fetch';
      alertCode.value = 'E_LOGIN_0003';
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

/**
 * Shibbolethログインエラーの処理
  * @param route
 */
function shibbolethLoginError(route: any) {
  const error = route.query.error || '';
  if (error) {
    if (error === 'Login is blocked.') {
      // statusCode 403 Loginがブロックされている
      alertMessage.value = 'message.error.loginFailed';
      alertCode.value = 'E_LOGIN_0004';
    } else if (error === 'There is no user information.') {
      // statusCode 403 ユーザ情報がない
      alertMessage.value = 'message.error.noUserInformation';
      alertCode.value = 'E_LOGIN_0005';
    } else if (
      error ===
      'Server error has occurred. Please contact server administrator.'
    ) {
      // statusCode 500 サーバーエラー
      alertMessage.value = 'message.error.server';
      alertCode.value = 'E_LOGIN_0006';
    } else {
      // statusCode 400
      alertMessage.value = 'message.error.loginFailed';
      if (error === 'Missing SHIB_CACHE_PREFIX!') {
        // Redisにcache_keyがない
        alertCode.value = 'E_LOGIN_0007';
      } else if (error === 'Missing Shib-Session-ID!') {
        // Shibboleth-Session-IDが​取得出来ない
        alertCode.value = 'E_LOGIN_0008';
      } else if (error === 'Missing SHIB_ATTRs!') {
        // shib_eppnが取得出来ない
        alertCode.value = 'E_LOGIN_0009';
      } else if (error === 'FAILED bind_relation_info!') {
        // 関連情報作成に失敗
        alertCode.value = 'E_LOGIN_0010';
      } else if (error === 'Can't get relation Weko User.') {
        // WEKOのユーザー関連情報が​取得出来ない
        alertCode.value = 'E_LOGIN_0011';
      } else {
        // その他例外エラー
        alertCode.value = 'E_LOGIN_0012';
      }
    }
    alertType.value = 'error';
    visibleAlert.value = true;
  }
}

/* ///////////////////////////////////
// life cycle
/////////////////////////////////// */

definePageMeta({
  layout: false
});

onMounted(() => {
  // 埋め込みDS用のiframeを作成
  const wayfContainer = document.getElementById('wayf_div');

  if (wayfContainer && wayfContainer.parentNode) {
    const iframe = document.createElement('iframe');

    // 本番とテスト環境を切り替える
    const dsURL = 'https://ds.gakunin.nii.ac.jp/WAYF';
    // const dsURL = 'https://test-ds.gakunin.nii.ac.jp/WAYF';

    const webHostName = useAppConfig().wekoOrigin;
    const entityID = webHostName + '/shibboleth';
    const handlerURL = webHostName + '/Shibboleth.sso';
    const returnURL = webHostName + '/secure/login.py?next=ams';

    // iframe内に埋め込むHTML
    iframe.srcdoc = `
      <script>
        window.wayf_URL = '${dsURL}';
        window.wayf_sp_entityID = '${entityID}';
        window.wayf_sp_handlerURL = '${handlerURL}';
        window.wayf_return_url = '${returnURL}';
        window.wayf_width = 'auto';
        window.wayf_height = 'auto';
        window.wayf_show_remember_checkbox = true;
        window.wayf_force_remember_for_session = false;
        window.wayf_use_small_logo = true;
        window.wayf_font_size = 12;
        window.wayf_font_color = '#000000';
        window.wayf_border_color = '#00247d';
        window.wayf_background_color = '#f4f7f7';
        window.wayf_auto_login = true;
        window.wayf_hide_after_login = false;
        window.wayf_show_categories = true;
        window.addEventListener('load', () => {
          let iHeight = document.documentElement.offsetHeight;
          if (!'${dsURL}'.includes('test')) {
            const extraHeight = window.innerHeight * 0.3; // NOTE:テスト環境ではない場合、画面高さの30%を加算する
            iHeight += extraHeight;
          }
          window.parent.document.querySelector('iframe').style.height = iHeight + 'px';
        });
      <\/script>
      <script src='${dsURL}/embedded-wayf.js'><\/script>
      <noscript>
        <!--
        Fallback to Shibboleth DS session initiator for non-JavaScript users
        You should set the value of the target GET parameter to an URL-encoded
        absolute URL that points to a Shibboleth protected web page where the user
        is logged in into your application.
        -->
        <p>
          <strong>Login:</strong> Javascript is not available for your web browser. Therefore, please <a
            href='/Shibboleth.sso/DS?target='>proceed manually</a>.
        <\/p>
      <\/noscript>
      <style>
        #view_incsearch_animate,
        #view_incsearch_scroll {
          font-size: 12px;
          max-height: 5rem;
        }
      <\/style>
      `;
    wayfContainer.parentNode.replaceChild(iframe, wayfContainer);
    iframe.width = '100%';
  }
});

onBeforeMount(() => {
  const route = useRoute();
  // アイテム詳細画面以外からのログインの場合、sessionStorage を削除
  if (route.query.source !== 'detail') {
    sessionStorage.removeItem('item-url');
  }

  shibbolethLoginError(route);
});
</script>
