<template>
  <div v-for="children in indexes.children" :key="children.id">
    <details class="index-tree__items">
      <summary>{{ children.name }}</summary>
      <div class="index-tree__detail">
        <ul v-if="children.children.length == 0">
          <li>
            <a href=""><span class="align-top underline">{{ children.link_name }}</span></a>
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
const props = defineProps({
    indexes: Object
})

</script>

<style scoped>

</style>