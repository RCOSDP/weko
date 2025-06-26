<template>
  <div class="detail-tab">
    <ul class="tab-btn__wrap">
      <li v-for="tab in tabList" :key="tab.id" class="tab-btn__item">
        <input
          :id="tab.id"
          v-model="selectedTab"
          :value="tab"
          class="tab-btn__radio hidden"
          type="radio"
          name="tab"
          :checked="tab.name === tabList[0].name" />
        <label class="tab-btn__label" :for="tab.id">
          {{ tab.name }}
        </label>
      </li>
    </ul>
    <div class="tab-content__wrap">
      <Section
        v-for="section in getSections(selectedTab)"
        :key="section.id"
        :title-list="getSectionsTitle(selectedTab)"
        :section="section"
        :subSection="getSubSections(section)" />
    </div>
  </div>
</template>

<script lang="ts" setup>
import Section from '~/components/detail/Section.vue';

/* ///////////////////////////////////
// interface
/////////////////////////////////// */

interface IDivision {
  id: string;
  name: string;
  hasPart: object[];
}
interface ISubSection {
  id: string;
  name: string;
  text: string;
  material: object;
}

/* ///////////////////////////////////
// props
/////////////////////////////////// */

const props = defineProps({
  // アイテム情報
  item: {
    type: Object,
    default: () => {}
  }
});

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const appConf = useAppConfig();
const selectedTab = ref();
const tabList = ref<IDivision[]>([]);
const sectionList = ref<IDivision[]>([]);
const subSectionList = ref<ISubSection[]>([]);

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * 表示要素を tab, section, subsection に切り分ける
 */
function setContentsList() {
  tabList.value = [];
  sectionList.value = [];
  subSectionList.value = [];

  if (Object.prototype.hasOwnProperty.call(props.item, 'rocrate')) {
    props.item.rocrate['@graph'].forEach((obj: any) => {
      if (obj['@type'] === 'Dataset') {
        if (!Object.prototype.hasOwnProperty.call(obj, 'additionalType')) {
          return;
        }

        // 'プロジェクトURL'が含まれている場合はスキップ
        if (obj['@id'] && obj['@id'].includes('プロジェクトURL')) {
          return;
        }

        if (obj.additionalType === appConf.roCrate.layer.tab) {
          const tab: IDivision = { id: obj['@id'], name: obj.name, hasPart: obj.hasPart };
          tabList.value.push(tab);
        } else if (obj.additionalType === appConf.roCrate.layer.section) {
          const section: IDivision = { id: obj['@id'], name: obj.name, hasPart: obj.hasPart };
          sectionList.value.push(section);
        } else if (obj.additionalType === appConf.roCrate.layer.subsection) {
          const subSection: ISubSection = {
            id: obj['@id'],
            name: obj.name,
            text: obj.text,
            material: Object.prototype.hasOwnProperty.call(obj, 'material')
              ? { type: obj.material, data: props.item[obj.material] }
              : {}
          };
          subSectionList.value.push(subSection);
        }
      }
    });
  }

  selectedTab.value = tabList.value[0];
}

/**
 * セクション名リストを取得する
 * @param tab 選択状態のタブ
 */
function getSectionsTitle(tab: IDivision) {
  const titleList: string[] = [];

  if (tab && tab.hasPart) {
    const sectionTitleList: string[] = [];

    tab.hasPart.forEach((sectionTitle: any) => {
      sectionTitleList.push(sectionTitle['@id']);
    });
    sectionList.value.forEach((section: IDivision) => {
      if (sectionTitleList.includes(section.id)) {
        titleList.push(section.name);
      }
    });
  }

  return titleList;
}

/**
 * タブに表示するセクションを取得する
 * @param tab 選択状態のタブ
 */
function getSections(tab: IDivision) {
  const targetSection: IDivision[] = [];

  if (tab && tab.hasPart) {
    const sectionTitleList: string[] = [];

    tab.hasPart.forEach((sectionTitle: any) => {
      sectionTitleList.push(sectionTitle['@id']);
    });
    sectionList.value.forEach((section: IDivision) => {
      if (sectionTitleList.includes(section.id)) {
        targetSection.push(section);
      }
    });
  }

  return targetSection;
}

/**
 * セクションに表示するサブセクションを取得する
 * @param section 対象セクション
 */
function getSubSections(section: IDivision) {
  const targetSubSection: ISubSection[] = [];

  if (section && section.hasPart) {
    const subSectionTitleList: string[] = [];

    section.hasPart.forEach((subSectionTitle: any) => {
      subSectionTitleList.push(subSectionTitle['@id']);
    });
    subSectionList.value.forEach((subSection: ISubSection) => {
      if (subSectionTitleList.includes(subSection.id)) {
        targetSubSection.push(subSection);
      }
    });
  }

  return targetSubSection;
}

/* ///////////////////////////////////
// main
/////////////////////////////////// */

try {
  setContentsList();
} catch (error) {
  // console.log(error);
}
</script>
