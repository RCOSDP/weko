<template>
    <div>
        <div class="max-w-[300px] mx-auto mt-3.5 mb-16 flex justify-center">
            <div v-for="page in pages">
                <a :class="{'current': page == currentPage}" class="page-numbers" :href="page == '...' ? null : `?page=${page}`">{{ page }}</a>
            </div>
      </div>
    </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
    total: Number,
    currentPage: Number,
    displayValue: String,
})

const pages = ref([])
const pagination = (c, m) => {
    let current = c,
        last = m,
        delta = 2,
        left = current - delta,
        right = current + delta + 1,
        range = [],
        rangeWithDots = [],
        l;

    for (let i = 1; i <= last; i++) {
        if (i == 1 || i == last || i >= left && i < right) {
            range.push(i);
        }
    }

    for (let i of range) {
        if (l) {
            if (i - l === 2) {
                rangeWithDots.push(l + 1);
            } else if (i - l !== 1) {
                rangeWithDots.push('...');
            }
        }
        rangeWithDots.push(i);
        l = i;
    }

    pages.value = rangeWithDots;
}
pagination(props.currentPage, (Math.ceil(+props.total / +props.displayValue)))

</script>

<style scoped>

</style>