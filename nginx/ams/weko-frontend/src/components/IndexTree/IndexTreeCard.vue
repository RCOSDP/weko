<template>
  <div v-for="children in indexes.children" :key="children.id">
    <details class="index-tree__items">
      <summary><span @click.prevent="searchFromItem(children.id)">{{ children.name }}</span></summary>
      <div class="index-tree__detail">
        <ul v-if="children.children.length == 0">
          <li>
            <!-- <a class="hover:cursor-pointer" @click="searchFromItem(children.id)"><span class="align-top underline">{{ children.link_name }}</span></a> -->
            <span class="hover:cursor-pointer" @click="searchFromItem(children.id)"><span class="align-top underline"></span></span>
          </li>
        </ul>
        <div class="index-tree_item">
          <IndexTreeCard v-if="children.children" :indexes="children" />
        </div>
      </div>
    </details>
  </div>
</template>

<script setup>
import { reactive } from 'vue';

const props = defineProps({
    indexes: Object
})

const searchConditions = reactive({
  keyWord: ''
})

const searchFromItem = (id) => {
  searchConditions.keyWord = id
  sessionStorage.setItem('search-conditions', JSON.stringify(searchConditions))
  window.location = '/search/summary'
}


//ダイヤモンドは<a>
</script>

<style scoped>

</style>