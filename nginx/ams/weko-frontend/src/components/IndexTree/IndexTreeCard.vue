<template>
    <ul >
        <li v-for="children in indexes.children" :key="children.id">
            <details class="index-tree__items">
              <summary>{{ children.name }}</summary>
              <div class="index-tree__detail">
                <IndexTreeCard v-if="children.children" :indexes="children"/>
              </div>
            </details>
        </li>
    </ul>
</template>

<script setup>
const props = defineProps({
    indexes: Object
})

</script>

<style scoped>

</style>