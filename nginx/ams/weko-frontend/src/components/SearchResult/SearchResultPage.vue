<script setup>
import SearchConditions from "../../components/SearchResult/SearchConditions.vue";
import SearchResultBlock from "../../components/SearchResult/SearchResultBlock.vue";
import SearchResultSummary from "../../components/SearchResult/SearchResultSummary.vue";
import SearchResultTable from "../../components/SearchResult/SearchResultTable.vue";
import Pagination from './Pagination.vue'
import ModalFilter from "../../components/Modal/ModalFilter.vue";
import ModalDisplayItem from "../../components/Modal/ModalDisplayItem.vue";
import { ref, watch, computed } from 'vue'

const props = defineProps({
    page: String
})
const searchStorage = JSON.parse(sessionStorage.getItem('search-conditions'))
const displayAmount = JSON.parse(sessionStorage.getItem('display-value'))
const sortConditions = JSON.parse(sessionStorage.getItem('sort'))
const searchConditions = ref({})

const matchSearches = () => {
    if(searchStorage){
        Object.assign(searchConditions?.value, searchStorage)
    }
}
matchSearches()

const searchResult = ref({})
const displayValue = ref(displayAmount ?? 20)
const typePublic = ref([])
const typeDownload = ref([])
const category = ref([])
const sort = ref(sortConditions ?? '-createdate')

const sortCheckBoxes = () => {
  if(!searchConditions?.value.checkbox){
    return
  }
  searchConditions?.value.checkbox.forEach((item) => {
    if(item.type == 'type_public'){
      typePublic.value.push(item.value)
    }
    if(item.type == 'type_download'){
      typeDownload.value.push(item.value)
    }
    if(item.type == 'category'){
      category.value.push(item.value)
    }
  })
}
sortCheckBoxes()

const setDisplayValue = (value) => {
    displayValue.value = value
    sessionStorage.setItem('display-value', JSON.stringify(displayValue.value))
    if(currentPage.value != 1){
        currentPage.value = 1
        history.pushState(null, '', '?page=1')
    }
}

const setSort = (value) => {
    sort.value = value
    sessionStorage.setItem('sort', JSON.stringify(sort.value))
}

// const tableSortValues = ref([])
const tableSortValue = ref('')
const setTableSort = (values) => {
    tableSortValue.value = values
    // tableSortValues.value = []
    // values.forEach((value) => {
    //     tableSortValues.value.push(value.value)
    // })
}

const sortToUse = computed(() => {
    if(props.page == 'table'){
        // return tableSortValues.value
        return tableSortValue.value
    }else{
        return sort.value
    }
})

const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);

const currentPage = ref(+urlParams.get('page') || 1)
const total = ref('')
const loadSearchData = async () => {
  const res = await fetch(`https://ams-dev.ir.rcos.nii.ac.jp/api/v1.0/search?` + new URLSearchParams({
    q: searchConditions?.value.keyWord,
    search_type: searchConditions?.value.searchType,
    size: displayValue.value,
    page: currentPage.value,
    sort: sortToUse.value,
    // title: searchConditions?.value?.text ? searchConditions?.value?.text[3] : '',
    // creator: searchConditions?.value.text[7],
    // category: searchConditions?.value.text[8],
    // repository: searchConditions?.value.text[9],
    }));
  const data = await res.json()
  searchResult.value = await data.hits.hits
  total.value = await data.hits.total
  sessionStorage.setItem('page', JSON.stringify(currentPage.value))
}
loadSearchData()

watch([displayValue, sort, tableSortValue], () => {
    loadSearchData()
})

const modalFilter = ref()
const modalDisplayItem = ref()

const openFilterModal = () => {
    document.getElementById('modalFilter').showModal();
    document.body.classList.add("overflow-hidden");
    modalFilter.value.showCheckBoxesWhenOpen()
}

const openDisplayItem = () => {
    document.getElementById('modalDisplayItem').showModal();
    document.body.classList.add("overflow-hidden");
    modalDisplayItem.value.showCheckBoxesWhenOpen()
}
</script>

<template>
    <div>
        <main class="max-w-[1024px] mx-auto px-2.5">
            <div class="breadcrumb flex flex-wrap w-full">
            <a class="text-miby-link-blue" href="/"><span class="font-medium underline">TOP</span></a>
            <p class="text-miby-dark-gray">検索結果リスト</p>
            </div>
            <div class="w-full">
            <div class="w-full">
                <div class="bg-miby-light-blue w-full">
                <p class="text-white leading-[43px] pl-5 icons icon-list font-bold">
                    検索結果
                </p>
                </div>
                <SearchConditions 
                @displayValue="setDisplayValue"
                @sort="setSort"
                @open-filter="openFilterModal"
                @open-display="openDisplayItem" 
                :page=page
                :typePublic="typePublic"
                :typeDownload="typeDownload"
                :category="category"
                :searchConditions="searchConditions" 
                :total="+total"
                />
                
                <div class="p-5 bg-miby-bg-gray">
                <div class="flex flex-wrap justify-between items-center">
                    <div class="checkbox">
                    <input
                        class="absolute"
                        type="checkbox"
                        name="checkList"
                        id="checkAllResult"
                    />
                    <label class="text-sm checkbox-label text-miby-black" for="checkAllResult"
                        >全てをマイリストに登録</label
                    >
                    </div>
                    <a class="pl-1.5 md:pl-0 icons icon-download after" href=""
                    ><span class="underline text-sm text-miby-link-blue pr-1"
                        >検索結果全てをDLする</span
                    ></a
                    >
                </div>
                <div class="max-w-[500px] ml-auto mt-4 mb-8 text-center">
                    <div class="w-full flex flex-wrap gap-5 justify-end">
                    <p class="icons-type icon-published">
                        <span>一般公開</span>
                    </p>
                    <p class="icons-type icon-group">
                        <span>グループ内公開</span>
                    </p>
                    <p class="icons-type icon-private">
                        <span>非公開</span>
                    </p>
                    <p class="icons-type icon-limited">
                        <span>制限公開</span>
                    </p>
                    </div>
                </div>
                <SearchResultBlock :searchResult="searchResult" v-if="page == 'block'" />
                <SearchResultSummary :searchResult="searchResult" v-if="page == 'summary'" />
                <SearchResultTable @table-sort="setTableSort" :searchResult="searchResult" v-if="page == 'table'" />
                <div class="max-w-[300px] mx-auto mt-3.5 mb-16">
                    <div v-if="total">
                        <Pagination :key="displayValue" :display-value="String(displayValue)" :currentPage="currentPage" :total="total" />
                    </div>
                </div>
                </div>
                </div>
            </div>
        </main>
        <ModalFilter ref="modalFilter" />
        <ModalDisplayItem ref="modalDisplayItem" />
    </div>
</template>

<style scoped>

</style>