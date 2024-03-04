<template>
  <header class="top-0 inset-x-0">
    <div
      class="flex md:items-center justify-between relative p-2.5 md:p-[5px] bg-gradient-to-b from-miby-header-blue to-bg-miby-light-blue">
      <div class="flex items-end flex-wrap sm:flex-nowrap">
        <p class="mr-[5px]">
          <NuxtLink to="/">
            <img src="/img/logo/logo01.png" alt="AMS Logo" />
          </NuxtLink>
        </p>
        <p class="text-white text-xs w-full md:w-auto mt-2 pb-1 md:mt-auto">
          {{ $t('serviceName') }}
          <!-- <br class="hidden md:block" />
          {{ $t('catchCopy') }} -->
        </p>
      </div>
    </div>
    <HeaderMenu />
  </header>
</template>

<script setup>
import HeaderMenu from '~/components/common/HeaderMenu.vue';
</script>
