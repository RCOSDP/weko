const weko = 'ams-dev.ir.rcos.nii.ac.jp';

export default defineAppConfig({
  wekoOrigin: 'https://' + weko,
  wekoApi: 'https://' + weko + '/api/v1',
  amsImage: '/img/ams',
  amsPath: '/ams',
  amsApi: '/api/ams',
  export: {
    jpcoar:
      'https://' + weko + '/oai?verb=GetRecord&metadataPrefix=jpcoar_1.0&identifier=oai:ams-dev.ir.rcos.nii.ac.jp:',
    dublincore:
      'https://' + weko + '/oai?verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:ams-dev.ir.rcos.nii.ac.jp:',
    ddi: 'https://' + weko + '/oai?verb=GetRecord&metadataPrefix=ddi&identifier=oai:ams-dev.ir.rcos.nii.ac.jp:'
  },
  /** RO-Crate Mapping setting */
  roCrate: {
    /**
     * WEKOのRO-Crate Mapping画面で指定したMappingのkey値を未病画面上のどの枠に表示するか設定
     * key: 未病画面上の表示位置
     * value: RO-Crate Mapping画面で設定したkey値
     */
    root: {
      // サムネイル
      thumbnail: 'thumbnail',
      // 公開区分
      releaseRange: 'accessMode',
      // 公開日
      releaseDate: 'dateCreated',
      // メタデータ作成日
      createDate: 'dateCreated',
      // メタデータ更新日
      updateDate: 'reviews',
      // データセットの名称
      title: 'subjectOf',
      // データセットの分野
      field: 'genre',
      // データ作成者氏名
      authorName: 'creator',
      // データ作成者所属
      authorAffiliation: 'creativeWorkStatus',
      // 取得データの対象種別
      target: 'character',
      // アクセス権
      accessMode: 'accessMode',
      // キーワード
      keywords: 'keywords',
      // ファイル情報
      file: {
        // 格納場所
        url: 'url',
        // サイズ
        size: 'size',
        // ライセンス種別
        licenseType: 'license',
        // ライセンス自由入力
        licenseWrite: 'text',
        // ファイル形式
        format: 'encodingFormat',
        // コメント
        comment: 'comment'
      }
    },
    /**
     * WEKOのRO-Crate Mapping画面で指定したLayerを設定
     * ※3階層以下のみ表示可能
     */
    layer: {
      tab: 'tab',
      section: 'section',
      subsection: 'subsection'
    },
    /**
     * WEKO側で扱っている選択形式の値を設定
     */
    selector: {
      // 公開区分
      releaseRange: {
        // 一般公開
        public: 'Public',
        // グループ内公開
        group: 'Shared',
        // 制限公開
        member: 'Private',
        // 非公開
        private: 'Unshared'
      },
      accessMode: {
        // 公開
        public: 'open access',
        // 共有
        group: 'restricted access',
        // 非共有・非公開
        member: 'embargoed access',
        // 公開期間猶予
        private: 'metadata only access'
      }
    }
  },
  grdm: {
    url: '',
    relationType: 'isVersionOf'
  },
  /** CC license setting */
  cc: {
    /**
     * WEKO側で扱っているライセンス種別の値を設定
     */
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
    /**
     * ライセンスのリンクを設定
     */
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
  },
  /**
   * 閲覧権限が必要なアイテム詳細画面からログイン画面へ遷移するまでの時間設定
   */
  transitionTimeMs: 10000, // ミリ秒
  /**
   * フロントのShibboleth Login設定
   */
  shibLogin: {
    // 本番環境
    dsURL: 'https://ds.gakunin.nii.ac.jp/WAYF',
    orthrosURL: 'https://core.orthros.gakunin.nii.ac.jp/idp',
    // テスト環境
    // dsURL: 'https://test-ds.gakunin.nii.ac.jp/WAYF',
    // orthrosURL: 'https://core-stg.orthros.gakunin.nii.ac.jp/idp',
    entityID: 'https://' + weko + '/shibboleth',
    handlerURL: 'https://' + weko + '/Shibboleth.sso',
    returnURL: 'https://' + weko + '/secure/login.py?next=ams'
  }
});
