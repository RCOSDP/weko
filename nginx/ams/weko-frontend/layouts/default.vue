<template>
  <body class="font-notoSans bg-miby-border-gray h-full">
    <div class="bg-miby-gray">
      <HeaderCompo />
      <slot />
      <FooterCompo />
    </div>
  </body>
</template>

<script setup>
import FooterCompo from '~/components/common/Footer.vue';
import HeaderCompo from '~/components/common/Header.vue';
</script>
