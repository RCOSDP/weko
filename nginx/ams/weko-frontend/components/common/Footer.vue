<template>
  <footer class="sticky top-[100vh] bg-gradient-to-r from-miby-blue to-miby-dark-blue mt-24 pt-16 px-5 pb-10">
    <div class="flex flex-wrap gap-10 lg:gap-20 items-end justify-between">
      <div class="flex">
        <ul class="text-white text-sm mr-20">
          <li class="mb-1.5 cursor-pointer">
            <NuxtLink class="underline" to="" event="" @click="throughDblClick('/')">
              <span>TOP</span>
            </NuxtLink>
          </li>
          <!-- <li class="mb-1.5">
            <NuxtLink class="underline" to="#">
              <span>ABOUT</span>
            </NuxtLink>
          </li> -->
          <!-- <li class="mb-1.5">
            <NuxtLink class="underline" to="#">
              <span>HELP</span>
            </NuxtLink>
          </li> -->
          <!-- <li class="mb-1.5">
            <NuxtLink class="underline" to="#">
              <span>FAQ</span>
            </NuxtLink>
          </li> -->
          <li class="cursor-pointer">
            <NuxtLink class="underline" to="" event="" @click="throughDblClick('/contact')">
              <span>CONTACT</span>
            </NuxtLink>
          </li>
        </ul>
        <ul class="text-white text-sm">
          <!-- <li class="mb-1.5">
            <NuxtLink class="underline" to="#">
              <span>
                {{ $t('fotterRequestUsePermission') }}
              </span>
            </NuxtLink>
          </li> -->
          <!-- <li class="mb-1.5">
            <NuxtLink class="underline" to="#">
              <span>
                {{ $t('fotterOrganization') }}
              </span>
            </NuxtLink>
          </li> -->
          <!-- <li>
            <NuxtLink class="underline" to="#">
              <span>
                {{ $t('fotterPrivacyPolicy') }}
              </span>
            </NuxtLink>
          </li> -->
        </ul>
      </div>
      <div class="flex flex-wrap lg:flex-nowrap items-center max-w-[245px] lg:max-w-full mx-auto md:mr-0">
        <p class="mr-[5px] cursor-pointer">
          <NuxtLink to="" event="" @click="throughDblClick('/')">
            <img src="/img/logo/logo01.png" alt="AMS Logo" />
          </NuxtLink>
        </p>
        <p class="text-white text-xs leading-6 mt-auto">
          {{ $t('serviceName') }}
          <!-- {{ $t('catchCopy') }} -->
          <span class="block text-[10px]">Copyright 2023 NII inc.</span>
        </p>
      </div>
    </div>
  </footer>
</template>

<script setup>
/* ///////////////////////////////////
// function
/////////////////////////////////// */
/**
 * ダブルクリックを制御する
 */
function throughDblClick(route) {
  if (route === '/contact') {
    navigateTo('/contact');
  } else if (location.pathname !== '/') {
    navigateTo('/');
  }
}
</script>
