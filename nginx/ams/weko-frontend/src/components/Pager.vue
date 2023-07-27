<script setup>
import {computed, ref, watch} from 'vue'
const props = defineProps({
  itemId: String,
})

const searchStorage = JSON.parse(sessionStorage.getItem('search-conditions'))
const displayAmount = JSON.parse(sessionStorage.getItem('display-value'))
const sortConditions = JSON.parse(sessionStorage.getItem('sort'))
const page = JSON.parse(sessionStorage.getItem('page'))
const searchConditions = ref({})
const searchResult = ref({})
const displayValue = ref(displayAmount ?? 20)
const sort = ref(sortConditions ?? '-createdate')

const matchSearches = () => {
    if(searchStorage){
        Object.assign(searchConditions?.value, searchStorage)
    }
}
matchSearches()

const currentPage = ref(page)
const total = ref('')
const loadSearchData = async () => {
  const res = await fetch(`https://ams-dev.ir.rcos.nii.ac.jp/api/v1.0/search?` + new URLSearchParams({
    q: searchConditions?.value.keyWord,
    search_type: searchConditions?.value.searchType,
    size: displayValue.value,
    page: currentPage.value,
    sort: sort.value,
    // title: searchConditions?.value?.text ? searchConditions?.value?.text[3] : '',
    // creator: searchConditions?.value.text[7],
    // category: searchConditions?.value.text[8],
    // repository: searchConditions?.value.text[9],
    }));
  const data = await res.json()
  searchResult.value = await data.hits.hits
  total.value = await data.hits.total
}
loadSearchData()
const ids = ref([])
watch([searchResult, total], () => {
  ids.value = []
  if(searchResult.value){
      Object.values(searchResult.value).forEach((item) => {
      ids.value.push(item._source.control_number)
    })
    total.value = total.value
  }
  findNextAndPrev()
})
const next = ref('')
const prev = ref('')
const currentIndex = ref('')
const findNextAndPrev = () => {
  currentIndex.value = ids.value.indexOf(props.itemId)
  next.value = ids.value[currentIndex.value + 1]
  prev.value = ids.value[currentIndex.value - 1]
}

const goNext = async () => {
  if(currentPage.value == Math.ceil(total.value / displayValue.value) && currentIndex.value == (ids.value.length - 1)){
    return
  }
  if(!next.value && currentPage.value != Math.ceil(total.value / displayValue.value)){
    sessionStorage.setItem('page', JSON.stringify(currentPage.value + 1))
    currentPage.value = currentPage.value + 1
    await loadSearchData()
    findNextAndPrev()
    window.location = `/detail/${next.value}`
  }else{
    window.location = `/detail/${next.value}`
  }
}
const goPrev = async () => {
  if(currentPage.value == 1 && currentIndex.value == 0){
    return
  }
  if(!prev.value && currentPage.value > 1){
    sessionStorage.setItem('page', JSON.stringify(currentPage.value - 1))
    currentPage.value = currentPage.value - 1
    await loadSearchData()
    findNextAndPrev()
    prev.value = ids.value[ids.value.length - 1]
    window.location = `/detail/${prev.value}`
  }else{
    window.location = `/detail/${prev.value}`
  }
}
</script>

<template>
  <div class="flex justify-between p-5">
    <a @click="goPrev" class="text-sm font-medium icons icon-arrow-l hover:cursor-pointer"><span class="hidden md:inline-block">前のアイテムを表示</span></a>
    <a class="text-sm font-medium text-miby-link-blue underline" href="/search/summary">検索結果リストに戻る</a>
    <a @click="goNext" class="text-sm font-medium icons icon-arrow-r hover:cursor-pointer"><span class="hidden md:inline-block">次のアイテムを表示</span></a>
  </div>
</template>
