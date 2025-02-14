<template>
  <div class="mt-2.5">
    <!-- タイトル -->
    <h5 class="text-md text-miby-black text-left font-medium icons icon-border">
      {{ subSection.name }}
    </h5>
    <!-- 内容 -->
    <div v-for="element in subSection.text" :key="element">
      <p class="text-sm text-miby-black text-left pt-1 pl-6">
        {{ $t(element) }}
      </p>
    </div>
    <!-- メタデータ -->
    <div v-if="subSection.material.type === 'metadata'">
      <div class="collapse collapse-arrow m-aout pl-1">
        <input class="w-28" type="checkbox" :checked="showMeta" @change="showMeta = !showMeta" />
        <div class="collapse-title flex items-start w-28">
          {{ $t('detail') }}
        </div>
        <div class="collapse-content">
          <table class="table table-xs border-double border-4 border-neutral m-auto">
            <thead class="border border-b-2">
              <tr>
                <th class="w-1/3 bg-stone-100 border-r-2">Key</th>
                <th class="w-2/3">Value</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="data in metadata" :key="data.key">
                <th
                  :class="
                    'bg-stone-100 border-r-2' + (data.padding === plList[0] ? ' border-t-2 ' : ' ') + data.padding
                  ">
                  {{ data.key ? data.key : '-' }}
                </th>
                <th class="border border-t-2">{{ data.value }}</th>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
    <div class="flex flex-wrap gap-1 mt-7.5" />
  </div>
</template>

<script lang="ts" setup>
/* ///////////////////////////////////
// interface
/////////////////////////////////// */

interface IJson {
  key: string;
  value: string;
  padding: string;
}

/* ///////////////////////////////////
// props
/////////////////////////////////// */

const props = defineProps({
  // サブセクション情報
  subSection: {
    type: Object,
    default: () => {}
  }
});

/* ///////////////////////////////////
// const and let
/////////////////////////////////// */

const metadata: IJson[] = [];
const plList = ['pl-2', 'pl-8', 'pl-16', 'pl-24', 'pl-32', 'pl-40', 'pl-48', 'pl-56'];
const showMeta = ref(false);

/* ///////////////////////////////////
// function
/////////////////////////////////// */

/**
 * メタデータ整形
 * @param json jsonオブジェクト
 * @param tier 階層数(段落用)
 */
function convertFlat(json: object, tier = 0) {
  for (const element in json) {
    // @ts-ignore
    if (typeof json[element] === 'object') {
      const data: IJson = { key: element, value: '', padding: plList[tier] };
      metadata.push(data);
      // @ts-ignore
      if (Array.isArray(json[element])) {
        // @ts-ignore
        for (const val of json[element]) {
          // @ts-ignore
          convertFlat(val, tier + 1);
        }
      } else {
        // @ts-ignore
        convertFlat(json[element], tier + 1);
      }
    } else {
      // @ts-ignore
      const data: IJson = { key: element, value: String(json[element]), padding: plList[tier] };
      metadata.push(data);
    }
  }
}

/* ///////////////////////////////////
// main
/////////////////////////////////// */

try {
  if (props.subSection.material.type === 'metadata') {
    convertFlat(props.subSection.material.data);
  }
} catch (error) {
  // console.log(error);
}
</script>
