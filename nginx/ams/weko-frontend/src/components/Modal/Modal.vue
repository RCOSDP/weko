<script setup>
import ButtonClose from "/images/btn/btn-close.svg";
import { computed, ref, watchEffect } from "vue";
const props = defineProps({
  modalId: { type: String, required: true, default: "" },
  modalTitle: { type: String, required: true, default: "" },
});

console.log(props);
// const emit = defineEmits(["update:modelCode", "update:targetPlace"]);
</script>

<template>
  <dialog class="w-11/12 md:w-full max-w-[728px] mx-auto z-10">
    <div class="bg-miby-light-blue w-full rounded-t relative">
      <p class="text-white leading-[43px] pl-5 text-center font-medium relative">
        {{ props.modalTitle }}
      </p>
      <button id="" type="button" class="btn-close" @click="closeSeachModal">
        <img :src="ButtonClose" alt="×" />
      </button>
    </div>
  </dialog>
</template>