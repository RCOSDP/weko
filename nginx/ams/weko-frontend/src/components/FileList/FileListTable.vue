<script setup>
import LicensePD from "/images/license-sample01.png";
import LicenseCC from "/images/license-sample02.png";
import Download from "/images/icon/icon_dl-rank.svg"
</script>

<template>
  <div class="w-full">
    <div class="w-full overflow-x-auto">
      <table class="search-lists w-[1274px] border-collapse border border-slate-500 table-auto">
        <thead>
          <tr>
            <th class="max-w-[44px]">選択</th>
            <th class="max-w-[130px]">ファイル名</th>
            <th class="max-w-[86px]">サイズ</th>
            <th class="max-w-[137px]">DL区分</th>
            <th class="max-w-[110px]">ライセンス</th>
            <th class="max-w-[134px]">アクション</th>
            <th class="max-w-[210px]">格納場所</th>
            <th class="max-w-[130px]">DL回数</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>データ.xlsx</td>
            <td>999KB</td>
            <td><span class="dl-tags permission">利用許可申請必要</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicenseCC" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>画像1.png</td>
            <td>999KB</td>
            <td><span class="dl-tags contract">守秘義務契約必要</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td class="w-[150px] break-all">aaabbbcccdddeeefffggghhhiiijjjkkklllmmmnnnooopppqqqrrrssstttuuu.png</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
          <tr>
            <td>
              <input class="" type="checkbox" name="publish-type" />
            </td>
            <td>測定1.csv</td>
            <td>999KB</td>
            <td><span class="dl-tags unlimited">無制限</span></td>
            <td><div class="w-[68px] mx-auto"><img :src="LicensePD" alt /></div></td>
            <td class="w-[190px]">
              <a class="btn-action icons-action icon-preview" href="/preview">プレビュー</a>
              <a class="btn-action icons-action icon-download" href="/download">ダウンロード</a>
              <a class="btn-action icons-action icon-info-bk" href="/infomation">インフォメーション</a>
              <a class="btn-action icons-action icon-approval" href="/application">利用許可申請</a>
              <p class="text-miby-black text-sm text-left">※承認後30日かつ5回まで</p>
            </td>
            <td class="w-[190px]"><a class="inline-block max-w-[180px] underline text-miby-link-blue break-all">/aaa/bbb/ccc/ddd/dauihsvzioaldzhvuizhzvuhdalivuddfuivzdhvuzhi/ashcuiahdjilsDcaikhvliuhdiajo;ijiajdijc/Jiodjs/nvakjiodfj.png</a></td>
            <td>9,999,999,999</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="flex justify-center mt-2 mb-4">
      <button class="flex gap-1 bg-miby-link-blue text-white px-4 py-2 rounded">
        <img :src="Download" alt="">ダウンロード
      </button>
    </div>
    <div class="max-w-[300px] mx-auto mt-3.5 mb-16">
      <a class="page-numbers" href="?paged=1">1</a>
      <span class="page-numbers dots">…</span>
      <a class="page-numbers current" href="?paged=1">12</a>
      <a class="page-numbers" href="?paged=1">13</a>
      <a class="page-numbers" href="?paged=1">14</a>
      <a class="page-numbers" href="?paged=1">15</a>
      <a class="page-numbers" href="?paged=1">16</a>
      <span class="page-numbers dots">…</span>
      <span class="page-numbers">986</span>
    </div>
  </div>
</template>


<style scoped lang="scss">
.border-collapse {
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

    .title {
      @apply underline;
    }

    .create-user {
      @apply underline block whitespace-nowrap;
    }
  }

  .btn-action {
    @apply w-[160px] relative mx-auto text-xs p-1 mb-1.5 block border-2 border-miby-black rounded bg-miby-tag-white;
    &::before {
      @apply absolute left-1.5 top-1.5;
    }
  }
}
</style>