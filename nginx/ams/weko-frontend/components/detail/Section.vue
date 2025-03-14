<template>
  <div class="">
    <div class="flex flex-wrap justify-between items-center">
      <h3 :id="targetId" class="text-miby-black text-xl font-bold">
        {{ section.name }}
      </h3>
      <div class="inline-block">
        <label class="text-sm text-miby-black" for="section-outline">
          {{ $t('detailSection') + '：' }}
        </label>
        <select
          v-model="sectionName"
          class="border border-miby-dark-gray text-sm text-left pl-2 p-1 cursor-pointer"
          @change="scrollToSection(sectionName)">
          <option v-for="element in titleList" :key="element" :value="element">
            {{ element }}
          </option>
        </select>
      </div>
    </div>
    <SubSection v-for="element in subSection" :key="element.id" :sub-section="element" />
  </div>
</template>

<script lang="ts" setup>
import SubSection from '~/components/detail/SubSection.vue';

/* ///////////////////////////////////
// interface
/////////////////////////////////// */

interface ISubSection {
  id: string;
  name: string;
  text: string;
}

/* ///////////////////////////////////
// props
/////////////////////////////////// */

const props = defineProps({
  // セクションスクロール用のセクションタイトルリスト
  titleList: {
    type: Array<string>,
    default: () => []
  },
  // セクション情報
  section: {
    type: Object,
    default: () => {}
  },
  // サブセクション情報
  subSection: {
    type: Array<ISubSection>,
    default: () => []
  }
});

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const targetId = ref(props.section.name);
const sectionName = ref(props.section.name);

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * 選択されたセクションまでスクロール
 * @param selectedSection 選択されたセクション
 */
function scrollToSection(selectedSection: string) {
  const element = document.getElementById(selectedSection);
  if (element) {
    element.scrollIntoView({ block: 'start', behavior: 'instant' });
    scrollTo(0, window.scrollY - 65);
    sectionName.value = props.section.name;
  }
}
</script>
