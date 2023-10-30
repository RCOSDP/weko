const weko = 'ams-dev.ir.rcos.nii.ac.jp';

export default defineAppConfig({
  wekoOrigin: 'https://' + weko,
  wekoApi: 'https://' + weko + '/api/v1',
  export: {
    jpcoar:
      'https://' + weko + '/oai?verb=GetRecord&metadataPrefix=jpcoar_1.0&identifier=oai:ams-dev.ir.rcos.nii.ac.jp:',
    dublincore:
      'https://' + weko + '/oai?verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:ams-dev.ir.rcos.nii.ac.jp:',
    ddi: 'https://' + weko + '/oai?verb=GetRecord&metadataPrefix=ddi&identifier=oai:ams-dev.ir.rcos.nii.ac.jp:'
  },
  roCrate: {
    info: {
      thumbnail: 'thumbnail', // サムネイル
      index: 'index', // インデックスID
      releaseRange: 'accessMode', // 公開区分
      reelaseDate: 'dateCreated', // 公開日
      updateDate: 'datePublished', // 更新日
      title: 'title', // タイトル
      field: 'genre', // 分野
      authorName: 'creatorName', // 作成者氏名
      authorAffiliation: 'creatorAffiliation', // 作成者所属
      target: 'target', // ヒト/動物/その他
      accessMode: 'accessMode', // アクセス権
      keywords: 'keywords' // キーワード
    },
    file: {
      url: 'url',
      size: 'size',
      licenseType: 'license',
      licenseWrite: 'test',
      format: 'encodingFormat'
    },
    contents: {
      tab: 'tab',
      section: 'section',
      subsection: 'subsection'
    },
    selector: {
      // 公開区分
      releaseRange: {
        public: 'Public',
        shared: 'Shared',
        private: 'Private',
        unshared: 'Unshared'
      }
    }
  },
  cc: {
    free: 'license_free',
    zero: 'license_12',
    by_3: 'license_6',
    by_4: 'license_0',
    by_sa_3: 'license_7',
    by_sa_4: 'license_1',
    by_nd_3: 'license_8',
    by_nd_4: 'license_2',
    by_nc_3: 'license_9',
    by_nc_4: 'license_3',
    by_nc_sa_3: 'license_10',
    by_nc_sa_4: 'license_4',
    by_nc_nd_3: 'license_11',
    by_nc_nd_4: 'license_5',
    link: {
      zero: 'https://creativecommons.org/publicdomain/zero/1.0/',
      zero_ja: 'https://creativecommons.org/publicdomain/zero/1.0/deed.ja',
      by_3: 'https://creativecommons.org/licenses/by/3.0/',
      by_3_ja: 'https://creativecommons.org/licenses/by/3.0/deed.ja',
      by_4: 'https://creativecommons.org/licenses/by/4.0/',
      by_4_ja: 'https://creativecommons.org/licenses/by/4.0/deed.ja',
      by_sa_3: 'https://creativecommons.org/licenses/by-sa/3.0/',
      by_sa_3_ja: 'https://creativecommons.org/licenses/by-sa/3.0/deed.ja',
      by_sa_4: 'https://creativecommons.org/licenses/by-sa/4.0/',
      by_sa_4_ja: 'https://creativecommons.org/licenses/by-sa/4.0/deed.ja',
      by_nd_3: 'https://creativecommons.org/licenses/by-nd/3.0/',
      by_nd_3_ja: 'https://creativecommons.org/licenses/by-nd/3.0/deed.ja',
      by_nd_4: 'https://creativecommons.org/licenses/by-nd/4.0/',
      by_nd_4_ja: 'https://creativecommons.org/licenses/by-nd/4.0/deed.ja',
      by_nc_3: 'https://creativecommons.org/licenses/by-nc/3.0/',
      by_nc_3_ja: 'https://creativecommons.org/licenses/by-nc/3.0/deed.ja',
      by_nc_4: 'https://creativecommons.org/licenses/by-nc/4.0/',
      by_nc_4_ja: 'https://creativecommons.org/licenses/by-nc/4.0/deed.ja',
      by_nc_sa_3: 'https://creativecommons.org/licenses/by-nc-sa/3.0/',
      by_nc_sa_3_ja: 'https://creativecommons.org/licenses/by-nc-sa/3.0/deed.ja',
      by_nc_sa_4: 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
      by_nc_sa_4_ja: 'https://creativecommons.org/licenses/by-nc-sa/4.0/deed.ja',
      by_nc_nd_3: 'https://creativecommons.org/licenses/by-nc-nd/3.0/',
      by_nc_nd_3_ja: 'https://creativecommons.org/licenses/by-nc-nd/3.0/deed.ja',
      by_nc_nd_4: 'https://creativecommons.org/licenses/by-nc-nd/4.0/',
      by_nc_nd_4_ja: 'https://creativecommons.org/licenses/by-nc-nd/4.0/deed.ja'
    }
  }
});
