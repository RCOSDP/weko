<template>
  <div>
    <!-- タイトル -->
    <div class="bg-MainBg bg-no-repeat bg-center bg-cover pt-[180px] pb-16 mt-[-180px] mb-5 text-center text-white">
      <h1 class="mt-16 mb-2.5 font-black text-5xl">CONTACT</h1>
      <p class="text-sm pb-14">お問い合わせ</p>
    </div>
    <div class="px-2.5 pt-1">
      <div class="max-w-[748px] mx-auto mt-4 border-2 border-miby-link-blue rounded">
        <div class="bg-miby-link-blue py-3 pl-5">
          <p class="text-white text-center font-bold">{{ $t('contact') }}</p>
        </div>
        <div class="bg-miby-bg-gray py-10 px-5">
          <Form class="max-w-[500px] mx-auto" @submit="sendConfirm">
            <!-- お名前 -->
            <label class="label flex-col">
              <span class="text-sm text-miby-black font-medium mr-auto">
                {{ $t('name') }}
              </span>
              <Field
                v-model="userName"
                name="name"
                type="text"
                :rules="checkUserName"
                :placeholder="$t('message.placeholder.name')"
                :class="{
                  'border-miby-form-red': dirtyName && checkUserName(userName) !== true,
                  'border-miby-thin-gray': !(dirtyName && checkUserName(userName) !== true)
                }"
                class="mt-2.5 mb-1 py-2.5 px-5 rounded w-full placeholder:text-miby-thin-gray h-7"
                @click="dirtyName = true" />
              <ErrorMessage v-slot="message" name="name">
                <span class="text-xs mr-auto text-miby-form-red">
                  {{ '※' + $t(String(message.message)) }}
                </span>
              </ErrorMessage>
            </label>
            <!-- メールアドレス -->
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
            <!-- お問い合わせ種別 -->
            <label class="label flex-col">
              <span class="text-sm text-miby-black font-medium mr-auto">
                {{ $t('contactType.title') }}
              </span>
              <div class="flex-col items-start w-full mt-2 mb-1">
                <div>
                  <label class="radio cursor-pointer w-auto">
                    <input id="site" v-model="contactType" value="site" type="radio" name="form-type" />
                    <span class="text-sm radio-label" for="type1" checked>
                      {{ $t('contactType.site') }}
                    </span>
                  </label>
                </div>
                <div>
                  <label class="radio cursor-pointer w-auto">
                    <input id="contents" v-model="contactType" value="contents" type="radio" name="form-type" />
                    <span class="text-sm radio-label" for="type2">
                      {{ $t('contactType.contents') }}
                    </span>
                  </label>
                </div>
                <div lass="flex-col">
                  <label class="radio cursor-pointer w-auto">
                    <input id="etc" v-model="contactType" value="etc" type="radio" name="form-type" />
                    <span class="text-sm radio-label" for="type3">
                      {{ $t('contactType.etc') }}
                    </span>
                  </label>
                  <div>
                    <Field
                      v-if="contactType == 'etc'"
                      v-model="contactEtc"
                      name="etc"
                      type="text"
                      :rules="checkContactEtc"
                      :placeholder="$t('message.placeholder.contactType')"
                      :class="{
                        'border-miby-form-red': dirtyContactEtc && checkContactEtc(contactEtc) !== true,
                        'border-miby-thin-gray': !(dirtyContactEtc && checkContactEtc(contactEtc) !== true)
                      }"
                      class="mt-1 py-2.5 px-5 rounded w-full placeholder:text-miby-thin-gray h-7"
                      @click="dirtyContactEtc = true" />
                    <ErrorMessage v-slot="message" name="etc">
                      <span class="text-xs mr-auto text-miby-form-red">
                        {{ '※' + $t(String(message.message)) }}
                      </span>
                    </ErrorMessage>
                  </div>
                </div>
              </div>
            </label>
            <!-- お問い合わせ -->
            <label class="label flex-col">
              <span class="text-sm text-miby-black font-medium mr-auto">
                {{ $t('contactContents') }}
              </span>
              <Field v-model="userContents" name="contents" :rules="checkUserContents">
                <textarea
                  v-model="inputContents"
                  :placeholder="$t('message.placeholder.contents')"
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
            <!-- 確認ボタン -->
            <button
              class="text-white text-sm text-center bg-orange-400 hover:bg-miby-orange font-medium py-1.5 px-5 mt-3 mx-auto block min-w-[96px] rounded"
              @click="
                dirtyContactEtc = true;
                dirtyName = true;
                dirtyMail = true;
                dirtyContents = true;
              ">
              {{ $t('confirm') }}
            </button>
          </Form>
        </div>
      </div>
    </div>
    <!-- 入力内容確認モーダル -->
    <ContactConfirm
      ref="confirm"
      class="z-50"
      :type="getContactType()"
      :name="userName"
      :email="userMail"
      :contents="userContents"
      @click-send="openSending"
      @complete-send="checkSendingResponse"
      @failed-crs="closeSending()" />
    <!-- Sending -->
    <dialog id="loading_modal" class="modal bg-black bg-opacity-50">
      <form class="modal-middle h-full">
        <div class="font-bold text-2xl text-white h-full flex justify-center items-center content-center">
          <span class="loading loading-bars loading-lg mr-4" />
          {{ $t('message.sending') }}
        </div>
      </form>
    </dialog>
    <!-- トースト -->
    <Alert
      v-if="isToast"
      :type="toastType"
      :message="toastMessage"
      position="toast-top pt-20"
      width="w-auto"
      @click-close="isToast = !isToast" />
  </div>
</template>

<script lang="ts" setup>
import { Form, Field, ErrorMessage } from 'vee-validate';

import Alert from '~/components/common/Alert.vue';
import ContactConfirm from '~/components/contact/modal/ContactConfirm.vue';

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const confirm = ref();
const contactType = ref('site');
const contactEtc = ref('');
const userName = ref('');
const userMail = ref('');
const userContents = ref('undefined'); // 初期フォーカス時バリデーション用の初期値
const inputContents = ref('');
const dirtyContactEtc = ref(false);
const dirtyName = ref(false);
const dirtyMail = ref(false);
const dirtyContents = ref(false);
const isToast = ref(false);
const toastType = ref('');
const toastMessage = ref('');

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * 確認ボタン押下時イベント
 */
function sendConfirm() {
  confirm.value.getCaptcha();
  confirm.value.openModal();
}

/**
 * お問い合わせ種別バリデーション
 * @param value 入力された内容
 */
function checkContactEtc(value: any) {
  if (!dirtyContactEtc.value) {
    return true;
  }

  // 未入力チェック
  if (!value && contactType.value === 'etc') {
    return 'message.alert.requiredContactType';
  }
  return true;
}

/**
 * 名前バリデーション
 * @param value 入力された名前
 */
function checkUserName(value: any) {
  if (!dirtyName.value) {
    return true;
  }

  // 未入力チェック
  if (!value) {
    return 'message.alert.requiredName';
  }
  return true;
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
 * 問い合わせ内容バリデーション
 * @param value 入力された問い合わせ内容
 */
function checkUserContents(value: any) {
  if (!dirtyContents.value) {
    return true;
  }

  // 未入力チェック
  if (!value || value === 'undefined') {
    return 'message.alert.requiredContents';
  }
  return true;
}

/**
 * 問い合わせ送信完了時イベント
 * @param val true:送信成功 / false:送信失敗
 */
function checkSendingResponse(val: boolean) {
  if (val) {
    toastType.value = 'success';
    toastMessage.value = 'message.sendingSuccess';
    // 入力内容初期化
    contactType.value = 'site';
    contactEtc.value = '';
    userName.value = '';
    userMail.value = '';
    userContents.value = 'undefined';
    inputContents.value = '';
    dirtyContactEtc.value = false;
    dirtyName.value = false;
    dirtyMail.value = false;
    dirtyContents.value = false;
  } else {
    toastType.value = 'error';
    toastMessage.value = 'message.sendingFailed';
  }
  closeSending();
  isToast.value = true;
}

/**
 * お問い合わせ種別の取得
 */
function getContactType() {
  if (contactType.value === 'site') {
    return 'contactType.site';
  } else if (contactType.value === 'contents') {
    return 'contactType.contents';
  } else {
    return ' ' + contactEtc.value;
  }
}

/**
 * 送信中モーダル表示
 */
function openSending() {
  (document.getElementById('loading_modal') as HTMLDialogElement).showModal();
}

/**
 * 送信中モーダル非表示
 */
function closeSending() {
  (document.getElementById('loading_modal') as HTMLDialogElement).close();
}
</script>
