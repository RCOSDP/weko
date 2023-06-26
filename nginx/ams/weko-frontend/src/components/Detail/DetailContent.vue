<script setup>
const stabMenu = [];
import ImageSample from "/images/img-search-sample.png";
import ImageSample1 from "/images/img-sample01.png";
import ImageSample2 from "/images/img-sample02.png";
import ImageSample3 from "/images/img-sample03.png";
import ImageSample4 from "/images/img-sample04.png";
import Pager from "../Pager.vue";
import {computed} from 'vue'

const props = defineProps({
  item: Object,
})

// console.log(props.item)

const keyWords = computed(() => {
  return props.item.item_1685585100256.attribute_value_mlt[0].subitem_1685583657917.subitem_1685583664589.split(',')
})


//todo FIX COMMA
</script>

<template>
  <div class="detail__wrapper">
    <div class="bg-miby-light-blue py-3 pl-5">
      <p class="icons icon-item text-white font-bold">アイテム</p>
    </div>
    <div class="bg-miby-bg-gray text-center">
      <Pager :itemId="item._deposit.id" />
      <hr class="border-miby-dark-gray" />
      <div class="detail__head">
        <div class="detail__head-image"><img :src="ImageSample" alt="" /></div>
        <div class="detail__head-text">
          <div class="flex flex-wrap mb-1.5 gap-2 md:gap-5 items-center">
            <p class="icons-type icon-group"><span>グループ内公開</span></p>
            <p class="date-upload icons icon-publish">{{ item.item_1685585050910.attribute_value_mlt[0].subitem_1685583626611.subitem_1685583628794 }}</p>
            <p class="date-update icons icon-update">{{ item.item_1685585050910.attribute_value_mlt[0].subitem_1685583626611.subitem_1685583633388 }}</p>
          </div>
          <a class="data-title text-left" href=""
            >{{ item.title.join(',') }}</a
          >
          <div class="flex mb-1">
            <p class="data-note">分野：<span class="">{{ item.item_1685585121449.attribute_value_mlt[0].subitem_1685583691205 }}</span></p>
            <p class="data-note author">
              作成者：<span v-for="person in item.item_1685585204873.attribute_value_mlt[0].subitem_1685584180890" class="">
                <span><a class="underline" href="">{{ person }}</a></span>
              </span>
            </p>
          </div>
          <div class="flex flex-wrap">
            <p class="data-note">ヒト/動物/その他：<span class="font-medium">{{ item.item_1685585235282.attribute_value_mlt[0].subitem_1685584345785 }}</span></p>
            <p class="data-note access-type">アクセス権：<span v-for="accessType in item.item_1685585170888.attribute_value_mlt[0].subitem_1685583776261" class="font-medium">{{ accessType }}</span></p>
            <p class="data-note">
              ファイル：<span class="font-medium"
                ><a class="underline text-miby-link-blue" href="/filelist">あり（250）</a></span
              >
            </p>
          </div>
          <div class="data-tags">
            <span class="tag-link key-word" v-for="keyWord in keyWords">
              <a><span>{{ keyWord }}</span></a>
            </span>
          </div>
        </div>
      </div>
      <div class="detail-tab">
        <ul class="tab-btn__wrap">
          <li class="tab-btn__item">
            <input class="tab-btn__radio hidden" type="radio" name="tab" id="tab-btn1" checked />
            <label class="tab-btn__label" for="tab-btn1">概要</label>
          </li>
          <li class="tab-btn__item">
            <input class="tab-btn__radio hidden" type="radio" name="tab" id="tab-btn2" />
            <label class="tab-btn__label" for="tab-btn2">データ</label>
          </li>
        </ul>
        <div class="tab-content__wrap">
          <div id="tab-content1" class="tab-content">
            <div class="">
              <div class="flex flex-wrap justify-between items-center">
                <h3 class="text-miby-black text-xl font-bold">研究概要</h3>
                <div class="inline-block">
                  <label class="text-sm text-miby-black" for="section">セクション：</label>
                  <select id="section" class="border border-miby-dark-gray text-sm text-center p-1">
                    <option selected>その他情報</option>
                  </select>
                </div>
              </div>
              <div class="mt-2.5">
                <h5 class="text-md text-miby-black text-left font-medium icons icon-border">
                  実験の説明
                </h5>
                <div>
                  <p class="text-sm text-miby-black text-left pt-1 pl-6">
                    {{ item.item_1685585100256.attribute_value_mlt[0].subitem_1685583657917.subitem_1685583662235 }}
                  </p>
                </div>
                <div class="flex flex-wrap gap-1 mt-7.5">
                  <div class="">
                    <img :src="ImageSample1" alt="画像" />
                  </div>
                  <div class="">
                    <img :src="ImageSample2" alt="画像" />
                  </div>
                  <div class="">
                    <img :src="ImageSample3" alt="画像" />
                  </div>
                  <div class="">
                    <img :src="ImageSample4" alt="画像" />
                  </div>
                </div>
              </div>
            </div>
            <div class="mt-15">
              <div class="flex flex-wrap justify-between items-center">
                <h3 class="text-miby-black text-xl font-bold">追加情報</h3>
                <div class="inline-block">
                  <label class="text-sm text-miby-black" for="section">セクション：</label>
                  <select id="section" class="border border-miby-dark-gray text-sm text-center p-1">
                    <option selected>その他情報</option>
                  </select>
                </div>
              </div>
              <div class="mt-2.5">
                <h5 class="text-md text-miby-black text-left font-medium icons icon-border">
                  追加情報の説明
                </h5>
                <p class="text-sm text-miby-black text-left pt-1 pl-6">
                  {{ item.item_1685585100256.attribute_value_mlt[0].subitem_1685583657917.subitem_1685583663389 }}
                </p>
              </div>
            </div>
            <div class="mt-15">
              <div class="flex flex-wrap justify-between items-center">
                <h3 class="text-miby-black text-xl font-bold">その他の情報</h3>
                <div class="inline-block">
                  <label class="text-sm text-miby-black" for="section">セクション：</label>
                  <select id="section" class="border border-miby-dark-gray text-sm text-center p-1">
                    <option selected>その他情報</option>
                  </select>
                </div>
              </div>
              <div class="mt-2.5">
                <h5 class="text-md text-miby-black text-left font-medium icons icon-border">
                  リポジトリ
                </h5>
                <p class="text-sm text-miby-black text-left pt-1 pl-6">
                  リポジトリ情報：{{ item.item_1685585189225.attribute_value_mlt[0].subitem_1685584149443.subitem_1685584151682 }}<br />
                  リポジトリURL：aaa/bbb/ccc/...<br />
                  DOIリンク：doi.org/...
                </p>
              </div>
              <div class="mt-5">
                <h5 class="text-md text-miby-black text-left font-medium icons icon-border">
                  利益相反の有無
                </h5>
                <p class="text-sm text-miby-black text-left pt-1 pl-6">{{ item.item_1685585292154.attribute_value_mlt[0].subitem_1685584593021.subitem_1685584596756 }}</p>
              </div>
            </div>
          </div>
          <div id="tab-content2" class="tab-content"></div>
        </div>
      </div>
      <div class="pt-2.5 pb-28">
      <Pager :itemId="item._deposit.id" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.author span,
.access-type span {
  display: inline-block;
}
.author span::before,
.access-type span::before {
  content: ", ";
}
.author span:first-child::before,
.access-type span:first-child::before {
  content: "";
}

.key-word span {
  display: inline-block;
}
.key-word span::before {
  content: "/";
}
.key-word span:first-child::before{
  content: "";
}
</style>