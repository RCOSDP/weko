<template>
  <dialog :class="[modalShowFlag ? 'visible' : 'invisible']" @click="closeModal">
    <div class="modal-confirm z-50" @click.stop>
      <div class="bg-miby-light-blue flex flex-row">
        <div class="basis-1/6" />
        <!-- タイトル -->
        <div class="basis-4/6">
          <p class="text-white leading-[43px] text-center font-medium">{{ $t('contactContentsConfirm') }}</p>
        </div>
        <!-- 閉じるボタン -->
        <div class="basis-1/6 flex text-end justify-end pr-3">
          <button type="button" class="btn-close">
            <img :src="`${appConf.amsImage ?? '/img'}/btn/btn-close.svg`" alt="×" @click="closeModal" />
          </button>
        </div>
      </div>
      <div class="mt-[-3px] pt-8 pb-8 md:mt-0 md:border-0 rounded-b-md px-2.5">
        <div class="font-medium text-l text-center pb-2">{{ $t('message.contactSendConfirm') }}</div>
        <div class="modalForm overflow-y-auto scroll-smooth h-full">
          <div class="pt-4 pb-4 h-full">
            <!-- お名前 -->
            <label class="label flex-col">
              <span class="text-sm font-medium mr-auto text-miby-dark-gray">
                {{ $t('name') }}
              </span>
              <a class="pt-2 pl-5 pr-3 w-full break-words">
                {{ name }}
              </a>
            </label>
            <!-- メールアドレス -->
            <label class="label flex-col">
              <span class="text-sm font-medium mr-auto text-miby-dark-gray">
                {{ $t('senderMailAddress') }}
              </span>
              <a class="pt-2 pl-5 pr-3 w-full break-words">
                {{ email }}
              </a>
            </label>
            <!-- お問い合わせ種別 -->
            <label class="label flex-col">
              <span class="text-sm font-medium mr-auto text-miby-dark-gray">
                {{ $t('contactType.title') }}
              </span>
              <a class="pt-2 pl-5 pr-3 w-full break-words">
                {{ $t(type) }}
              </a>
            </label>
            <!-- お問い合わせ内容 -->
            <label class="label flex-col">
              <span class="text-sm font-medium mr-auto text-miby-dark-gray">
                {{ $t('contactContents') }}
              </span>
              <a class="pt-2 pl-5 pr-3 w-full break-words">
                {{ contents }}
              </a>
            </label>
          </div>
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
            @click="send">
            {{ $t('send') }}
          </button>
        </div>
      </div>
    </div>
    <div class="backdrop" />
  </dialog>
</template>

<script lang="ts" setup>
import { Field } from 'vee-validate';
import { useI18n } from 'vue-i18n';

/* ///////////////////////////////////
// expose
/////////////////////////////////// */

defineExpose({
  getCaptcha,
  openModal
});

/* ///////////////////////////////////
// props
/////////////////////////////////// */

const props = defineProps({
  // お問い合わせ種別(i18n)
  type: {
    type: String,
    default: ''
  },
  // お名前
  name: {
    type: String,
    default: ''
  },
  // メールアドレス
  email: {
    type: String,
    default: ''
  },
  // お問い合わせ内容
  contents: {
    type: String,
    default: ''
  }
});

/* ///////////////////////////////////
// emits
/////////////////////////////////// */

const emits = defineEmits(['clickSend', 'completeSend', 'failedCrs']);

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const { t, locale } = useI18n();
const appConf = useAppConfig();
const modalShowFlag = ref(false);
const isCaptcha = ref(false);
const base64 = ref('');
const dirtyAnswer = ref(false);
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
 * 問い合わせ送信
 */
async function send() {
  emits('clickSend');

  locale.value = String(localStorage.getItem('locale'));
  const contactType = t(props.type);

  await useFetch(`${appConf.amsApi ?? '/api'}/mail/send`, {
    method: 'POST',
    body: JSON.stringify({
      key: captchaKey,
      answer: answer.value,
      mailType: useRuntimeConfig().public.contact.use,
      type: contactType,
      name: props.name,
      address: props.email,
      contents: props.contents
    })
  })
    .then((response) => {
      if (response.data.value === 'Complete sending') {
        answeResult.value = true;
        emits('completeSend', true);
        closeModal();
      } else if (response.data.value === 'Failed certification') {
        emits('failedCrs');
      } else {
        emits('completeSend', false);
        closeModal();
      }
      dirtyAnswer.value = true;
    })
    .catch(() => {
      emits('completeSend', false);
      closeModal();
    });
}

/**
 * モーダル表示
 */
function openModal() {
  answer.value = 0;
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
