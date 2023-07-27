<template>
    <tr>
        <td>
            <input class="" type="checkbox" name="publish-type" />
        </td>
        <td class="max-w-[130px] text-left">{{ file.filename }}</td>
        <td>{{ file.filesize[0].value }}</td>
        <td><span class="dl-tags unlimited">無制限</span></td>
        <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
        <td class="w-[190px] text-left">
            <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
            <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
            <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
            <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
            <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
        </td>
        <td class="w-[190px] text-left"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all hover:cursor-pointer">{{ file.url.url }}</a></td>
        <td>9,999,999,999</td>
    </tr>
</template>

<script setup>
import LicensePD from "/images/license-sample01.png";
import LicenseCC from "/images/license-sample02.png";
import Download from "/images/icon/icon_dl-rank.svg"

const props = defineProps({
    file: Object
})

</script>

<style lang="scss" scoped>
th,
  td {
    @apply border border-miby-thin-gray text-center align-middle;
  }

  th {
    @apply py-1 font-medium;
  }

  td {
    @apply px-2 pt-5 pb-7;

    &.text-left {
      text-align: left;
    }
  }

  .btn-action {
    @apply w-[160px] relative mx-auto text-xs p-1 mb-1.5 block border-2 border-miby-black rounded bg-miby-tag-white;
    &::before {
      @apply absolute left-1.5 top-1.5;
    }
  }
</style>