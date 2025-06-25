<template>
  <dialog :class="[modalShowFlag ? 'visible' : 'invisible']" @click="closeModal">
    <div class="modal-confirm z-50" @click.stop>
      <div class="bg-miby-light-blue flex flex-row">
        <div class="basis-1/6" />
        <!-- タイトル -->
        <div class="basis-4/6">
          <p class="text-white leading-[43px] text-center font-medium">{{ $t('requestMail') }}</p>
        </div>
        <!-- 閉じるボタン -->
        <div class="basis-1/6 flex text-end justify-end pr-3">
          <button type="button" class="btn-close">
            <img :src="`${appConf.amsImage ?? '/img'}/btn/btn-close.svg`" alt="×" @click="closeModal" />
          </button>
        </div>
      </div>
      <div class="mt-[-3px] pt-8 pb-8 md:mt-0 md:border-0 rounded-b-md px-2.5">
        <div class="font-medium text-l text-center pb-2">{{ $t('message.inputRequest') }}</div>
        <div class="modalForm overflow-y-auto scroll-smooth h-full">
          <Form id="requestMail" class="max-w-[500px] mx-auto" @submit="send">
            <!-- 送信者メールアドレス -->
            <label class="label flex-col">
              <span class="text-sm text-miby-black font-medium mr-auto">
                {{ $t('senderMailAddress') }}
              </span>
              <Field
                v-model="userMail"
                name="mail"
                type="email"
                :rules="checkUserMail"
                :placeholder="$t('message.placeholder.mail')"
                :class="{
                  'border-miby-form-red': dirtyMail && checkUserMail(userMail) !== true,
                  'border-miby-thin-gray': !(dirtyMail && checkUserMail(userMail) !== true)
                }"
                class="mt-2.5 mb-1 py-2.5 px-5 rounded w-full placeholder:text-miby-thin-gray h-7"
                @click="dirtyMail = true" />
              <ErrorMessage v-slot="message" name="mail">
                <span class="text-xs mr-auto text-miby-form-red">
                  {{ '※' + $t(String(message.message)) }}
                </span>
              </ErrorMessage>
            </label>
            <!-- 件名 -->
            <label class="label flex-col">
              <span class="text-sm text-miby-black font-medium mr-auto">
                {{ $t('mailSubject') }}
              </span>
              <Field
                v-model="userSubject"
                name="subject"
                type="text"
                :rules="checkUserSubject"
                :placeholder="$t('message.placeholder.subject')"
                :class="{
                  'border-miby-form-red': dirtySubject && checkUserSubject(userSubject) !== true,
                  'border-miby-thin-gray': !(dirtySubject && checkUserSubject(userSubject) !== true)
                }"
                class="mt-2.5 mb-1 py-2.5 px-5 rounded w-full placeholder:text-miby-thin-gray h-7"
                @click="dirtySubject = true" />
              <ErrorMessage v-slot="message" name="subject">
                <span class="text-xs mr-auto text-miby-form-red">
                  {{ '※' + $t(String(message.message)) }}
                </span>
              </ErrorMessage>
            </label>
            <!-- リクエスト内容 -->
            <label class="label flex-col">
              <span class="text-sm text-miby-black font-medium mr-auto">
                {{ $t('requestContent') }}
              </span>
              <Field v-model="userContents" name="contents" :rules="checkUserContents">
                <textarea
                  v-model="inputContents"
                  :placeholder="$t('message.placeholder.request')"
                  :class="{
                    'border-miby-form-red': dirtyContents && checkUserContents(userContents) !== true,
                    'border-miby-thin-gray': !(dirtyContents && checkUserContents(userContents) !== true)
                  }"
                  class="mt-2.5 mb-1 py-2.5 px-5 rounded w-full placeholder:text-miby-thin-gray h-44"
                  @blur="userContents = inputContents"
                  @click="dirtyContents = true" />
              </Field>
              <ErrorMessage v-slot="message" name="contents">
                <span class="text-xs mr-auto text-miby-form-red">
                  {{ '※' + $t(String(message.message)) }}
                </span>
              </ErrorMessage>
            </label>
          </Form>
        </div>
        <!-- 文字認証 -->
        <div class="ml-14 pt-3">
          <div class="font-medium text-sm">{{ '[' + $t('crs') + ']' }}</div>
          <div class="flex items-end mb-2">
            <!-- キャプチャ -->
            <div
              class="flex border border-miby-black bg-orange-50 text-sm text-gray-500 items-center justify-center w-[200px] h-[50px] mr-2">
              <img v-if="base64" class="object-fill" :src="base64" />
              <span v-else-if="isCaptcha">
                <!-- キャプチャ取得失敗 -->
                {{ $t('crsFailed') }}
              </span>
              <span v-else>
                <!-- キャプチャ取得中 -->
                {{ $t('crsGetting') }}
              </span>
            </div>
            <!-- キャプチャ更新 -->
            <div class="inline-block underline text-miby-link-blue break-all hover:cursor-pointer" @click="getCaptcha">
              {{ $t('crsUpdating') }}
            </div>
          </div>
          <!-- 説明 -->
          <span class="text-sm text-miby-black font-medium mr-auto">
            {{ $t('crsExplanation') }}
          </span>
          <!-- 解入力フォーム -->
          <div calss="justify-start">
            <Field
              v-model="answer"
              name="answer"
              type="number"
              :placeholder="$t('message.placeholder.subject')"
              :class="{
                'border-miby-form-red': dirtyAnswer && !answeResult,
                'border-miby-thin-gray': !dirtyAnswer || answeResult
              }"
              class="h-7 w-40 mt-1 rounded placeholder:text-miby-thin-gray" />
          </div>
          <span v-if="dirtyAnswer && !answeResult" class="text-xs mr-auto text-miby-form-red">
            {{ '※' + $t('crsAgain') }}
          </span>
        </div>
        <!-- キャンセル/送信 -->
        <div class="flex items-center justify-center pt-5 gap-4">
          <button
            type="button"
            class="text-miby-black text-sm text-center font-medium border border-miby-black hover:bg-gray-200 py-1.5 px-5 block min-w-[96px] rounded"
            @click="closeModal">
            {{ $t('cancel') }}
          </button>
          <button
            type="submit"
            class="text-white text-sm text-center bg-orange-400 hover:bg-miby-orange font-medium py-1.5 px-5 block min-w-[96px] rounded"
            form="requestMail"
            @click="
              dirtyMail = true;
              dirtySubject = true;
              dirtyContents = true;
            ">
            {{ $t('send') }}
          </button>
        </div>
      </div>
    </div>
    <div class="backdrop" />
  </dialog>
</template>

<script lang="ts" setup>
import { Form, Field, ErrorMessage } from 'vee-validate';

/* ///////////////////////////////////
// expose
/////////////////////////////////// */

defineExpose({
  getCaptcha,
  openModal,
  initInput
});

/* ///////////////////////////////////
// props
/////////////////////////////////// */

const props = defineProps({
  itemId: {
    type: Number,
    default: 0
  }
});

/* ///////////////////////////////////
// emits
/////////////////////////////////// */

const emits = defineEmits(['clickSend', 'completeSend']);

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const appConf = useAppConfig();
const userMail = ref('');
const userSubject = ref('');
const userContents = ref('undefined'); // 初期フォーカス時バリデーション用の初期値
const inputContents = ref('');
const dirtyMail = ref(false);
const dirtySubject = ref(false);
const dirtyContents = ref(false);
const dirtyAnswer = ref(false);
const modalShowFlag = ref(false);
const isCaptcha = ref(false);
const base64 = ref('');
const answer = ref(0);
const answeResult = ref(false);
let captchaKey = '';

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * 文字認証用の画像取得
 */
function getCaptcha() {
  isCaptcha.value = false;
  dirtyAnswer.value = false;
  answeResult.value = false;

  $fetch(`${appConf.amsApi ?? '/api'}/captcha/image`, {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'GET',
    headers: {
      'Cache-Control': 'no-store',
      Pragma: 'no-cache',
      'Accept-Language': localStorage.getItem('locale') ?? 'ja'
    },
    onResponse({ response }) {
      if (response.status === 200) {
        base64.value = 'data:image/png;base64,' + response._data.image;
        captchaKey = response._data.key;
      }
      isCaptcha.value = true;
    },
    onResponseError() {
      base64.value = '';
      captchaKey = '';
    }
  }).catch(() => {
    base64.value = '';
    captchaKey = '';
    isCaptcha.value = true;
  });
}

/**
 * リクエストメール送信
 */
async function send() {
  let token;

  // 文字認証の照合
  await $fetch(`${appConf.amsApi ?? '/api'}/captcha/validate`, {
    timeout: useRuntimeConfig().public.apiTimeout,
    method: 'POST',
    headers: {
      'Cache-Control': 'no-store',
      Pragma: 'no-cache',
      'Accept-Language': localStorage.getItem('locale') ?? 'ja'
    },
    body: {
      key: captchaKey,
      calculation_result: answer.value
    },
    onResponse({ response }) {
      if (response.status === 200) {
        answeResult.value = true;
        token = response._data.authorization_token;
      }
      dirtyAnswer.value = true;
    }
  });

  // リクエスト送信
  if (answeResult && token) {
    emits('clickSend');

    await $fetch(`${appConf.amsApi ?? '/api'}/captcha/${props.itemId}/request-mail`, {
      timeout: useRuntimeConfig().public.apiTimeout,
      method: 'POST',
      credentials: 'omit',
      headers: {
        'Cache-Control': 'no-store',
        Pragma: 'no-cache',
        'Accept-Language': localStorage.getItem('locale') ?? 'ja',
        Authorization: localStorage.getItem('token:type') + ' ' + localStorage.getItem('token:access')
      },
      body: {
        from: userMail.value,
        subject: userSubject.value,
        message: userContents.value,
        key: captchaKey,
        authorization_token: token
      },
      onResponse({ response }) {
        if (response.status === 200) {
          emits('completeSend', true);
        } else {
          emits('completeSend', false);
        }
      }
    }).finally(() => {
      closeModal();
    });
  }
}

/**
 * メールアドレスバリデーション
 * @param value 入力されたメールアドレス
 */
function checkUserMail(value: any) {
  if (!dirtyMail.value) {
    return true;
  }

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
 * 件名バリデーション
 * @param value 入力された件名
 */
function checkUserSubject(value: any) {
  if (!dirtySubject.value) {
    return true;
  }

  // 未入力チェック
  if (!value) {
    return 'message.alert.requiredSubject';
  }
  return true;
}

/**
 * リクエスト内容バリデーション
 * @param value 入力されたリクエスト内容
 */
function checkUserContents(value: any) {
  if (!dirtyContents.value) {
    return true;
  }

  // 未入力チェック
  if (!value || value === 'undefined') {
    return 'message.alert.requiredRequest';
  }
  return true;
}

/**
 * 入力フォームの初期化
 */
function initInput() {
  userMail.value = '';
  userSubject.value = '';
  userContents.value = 'undefined';
  inputContents.value = '';
  answer.value = 0;
  dirtyMail.value = false;
  dirtySubject.value = false;
  dirtyContents.value = false;
  dirtyAnswer.value = false;
}

/**
 * モーダル表示
 */
function openModal() {
  modalShowFlag.value = true;
  document.body.classList.add('overflow-hidden');
}

/**
 * モーダル非表示
 */
function closeModal() {
  modalShowFlag.value = false;
  document.body.classList.remove('overflow-hidden');
}
</script>

<style scoped lang="scss">
.border-collapse {
  th {
    @apply border border-miby-thin-gray text-center align-middle;
    @apply py-1 font-medium;
  }
  td {
    @apply border border-miby-thin-gray text-center align-middle;
    @apply px-2 pt-5 pb-7;
  }
}
</style>
