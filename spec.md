# WEKO3 表示速度改善 機能仕様書 (spec.md)

対象ブランチ: `develop_v2.1.0` / 作成日: 2026-07-22

本書は、トップページ・アイテム詳細(ランディングページ)・検索結果一覧の表示遅延に対する各修正を、
**ファンクション(関数)レベル**でまとめた機能仕様書です。関連調査は [pref_issues.md](./pref_issues.md)、
テスト結果は [unittest_result.md](./unittest_result.md) を参照してください。

## 共通事項

- **キャッシュ方式**: クロスリクエストのキャッシュは全て **短TTL方式**(既定 300 秒)。厳密な無効化フックに依存せず、
  ステールは最大 TTL 秒に限定される。TTL は各 `*_CACHE_TTL` config で調整可(0 で無期限)。
- **キャッシュ基盤**: `invenio_cache.current_cache`(flask-caching、バックエンドは Redis)。
  拡張未設定の環境では該当処理を**スキップ**して素の計算にフォールバックする(防御的実装)。
- **リクエストスコープのメモ化**: `flask.g` を使用。リクエスト終了時に自動破棄されるため無効化フック不要。
- **後方互換性**: 全修正は**入出力(戻り値)の意味を変えない**。キャッシュ/メモ化はヒット時に同一結果を返す。

---

## 共通A — `get_search_setting()` の重複呼び出し集約

| 項目 | 内容 |
|------|------|
| 対象関数 | `weko_theme.utils.get_weko_contents()`、`weko_records_ui.views.default_view_method()`、`weko_search_ui.views.search()` |
| 依存関数 | `weko_admin.utils.get_search_setting()` → `SearchManagement.get()`(2クエリ/回) |
| コミット | `1288154d4` |

- **変更前**: 各ビューが `display_facet_search` / `display_index_tree` / `display_community` を取り出すために
  `get_search_setting().get("display_control", {})` を**3回**呼び、1リクエストで同一設定を3回DB取得していた。
- **変更後**: 各ビュー冒頭で `display_control = get_search_setting().get("display_control", {})` を**1回**取得し、
  3つのサブ設定はこの `display_control` から参照する。
- **効果**: 1ページあたり `get_search_setting()` 3→1回(=約4クエリ削減)。3ページ計で約12クエリ削減。
- **リスク**: なし(返り値は参照のみ、意味論同一)。クロスリクエストキャッシュ不使用のため無効化不要。

---

## 共通C — ウィジェット設計取得のリクエスト内メモ化

| 項目 | 内容 |
|------|------|
| 対象関数 | `weko_gridlayout.models.WidgetDesignSetting.select_by_repository_id()` |
| 追加関数 | `WidgetDesignSetting._clear_request_cache()`（新規） |
| 影響呼び出し元 | `get_design_layout()`→`main_design_has_main_widget()`、`has_widget_design()`→`WidgetDesignServices.get_widget_design_setting()` |
| コミット | `a76f6c564` |

- **変更前**: トップページ描画中に同一 `repository_id` の設計を最低2回DB取得し、`settings` JSON を毎回パース。
- **変更後**: `select_by_repository_id()` の結果を `flask.g._widget_design_setting_cache`(dict, キー=repository_id)に
  メモ化。同一リクエスト内2回目以降はDBクエリを行わない。
- **無効化**: `update()` / `create()` 成功時に `_clear_request_cache(repository_id)` を呼び、同一リクエスト内の
  更新後参照が古い値を返さないようにする。`g` はリクエスト終了で破棄されるためクロスリクエストの無効化は不要。
- **リスク**: 返り値は呼び出し元で読み取り専用(json.loads で新オブジェクト生成)。共有汚染なし。

---

## 共通B — `get_search_detail_keyword()` の短TTLキャッシュ

| 項目 | 内容 |
|------|------|
| 対象関数 | `weko_search_ui.api.get_search_detail_keyword(str_)` |
| 新規config | `WEKO_SEARCH_DETAIL_KEYWORD_CACHE_TTL = 300`(`weko_search_ui/config.py`) |
| コミット | `b63d08a73` |

- **変更前**: トップページ/アイテム詳細の描画毎に、全アイテムタイプ取得(`ItemTypes.get_latest()`)+ブラウジングツリー
  走査で詳細検索条件を再構築していた。
- **変更後**: 結果(JSON文字列)を `current_cache` にキャッシュ。
  - **キー**: `search_detail_keyword_{host}_{lang}_{auth}`
    - `host` = `INVENIO_WEB_HOST_NAME`、`lang` = `current_i18n.language`、`auth` = `'auth'`/`'guest'`
  - 結果はこの3要素にのみ依存(引数 `str_` は本体で未使用のためキーに含めない)。
  - **TTL**: `WEKO_SEARCH_DETAIL_KEYWORD_CACHE_TTL`(既定300秒)。
- **理由**: ゲスト/認証で異なるブラウジングツリーを返すため `auth` をキーに含める。アイテムタイプ/インデックスの
  変更は最大TTL秒でキャッシュ失効。
- **リスク**: 短TTL分のステール(検索条件ドロップダウンが最大数分古い)。影響軽微。

---

## 3-2 — アイテム詳細の二重N+1インデックスループ統合

| 項目 | 内容 |
|------|------|
| 対象関数 | `weko_records_ui.views.default_view_method()` |
| 追加ヘルパー | ローカル関数 `_get_index_by_path(path)`（クロージャ） |
| コミット | `4cde4e05f` |

- **変更前**: `record.navi` のパスを2回別々にループ(`path_name_dict` 構築 と `belonging_community` 構築)し、
  各ループで `Indexes.get_index(index_id=path)` を呼んでいた(同一 index を2回DB取得=N+1×2)。
- **変更後**: リクエストローカルの dict `_index_by_path` にメモ化する `_get_index_by_path()` を導入し、両ループが同一
  結果を再利用。同一パスの `Indexes.get_index` は1回のみ。
- **効果**: 「所属インデックス数 × 階層深さ」分の重複DBクエリを削減。
- **リスク**: なし(関数ローカルのメモ化、返り値の意味論同一)。

---

## 2-1 — `get_ranking()` の短TTLキャッシュ(ユーザー別)

| 項目 | 内容 |
|------|------|
| 対象関数 | `weko_items_ui.utils.get_ranking(settings)` |
| 新規config | `WEKO_ITEMS_UI_RANKING_CACHE_TTL = 300`(`weko_items_ui/config.py`) |
| 追加import | `hashlib` |
| コミット | `b412edaa6`(テスト基盤: `3a6530bde`) |

- **変更前**: トップページがランキング表示設定の場合、描画毎に最大5種のES集約 + 候補毎の権限チェック
  (`get_permission_record()` 内の `WekoRecord.get_record_by_pid` N+1)を実行。
- **変更後**: `get_ranking()` の結果(dict)を `current_cache` にキャッシュ。
  - **キー**: `get_ranking_{host}_{date}_{user}_{sig}`
    - `date` = 当日(日次で自然失効)、`sig` = 設定シグネチャ(statistical_period/display_rank/new_item_period/rankings)の MD5
    - `user` = **ゲストは `guest`(共通キー=高ヒット率)、認証ユーザーは `u{user_id}`(個別キー)**
  - **TTL**: `WEKO_ITEMS_UI_RANKING_CACHE_TTL`(既定300秒)。
  - キャッシュ拡張未設定時はキャッシュをスキップ(`ranking_cache_key = None`)。
- **セキュリティ上の要点**: 権限フィルタ(`check_created_id`)は「ユーザー自身の未公開アイテム」をランキングに出しうるため、
  結果は**ユーザー依存**。認証ユーザーを user_id 別キーにすることで、他ユーザーへの非公開アイテム漏洩を防ぐ。
- **副次効果**: N+1 のレコード取得も「TTL・ユーザーコンテキストあたり1回」に緩和。
- **リスク**: 短TTL分のステール(統計・新着が最大数分古い)。ランキング表示設定の機関のみ影響。

---

## 4-3 — 検索一覧アイテムタイプ由来データのリクエスト内メモ化

| 項目 | 内容 |
|------|------|
| 対象関数 | `weko_records.utils.sort_meta_data_by_options(record_hit, settings, item_type_data)` |
| 追加import | `flask.g`, `flask.has_app_context` |
| コミット | `723ecb7a6` |

- **変更前**: 検索結果の**ヒット1件ごと**に、`ItemTypes.get_by_id()` / `get_options_and_order_list()` /
  `get_hide_list_by_schema_form()` / `get_mapping()`(DB+再帰構築)を再実行。同一アイテムタイプの行が多数並ぶ一覧で重複。
- **変更後**: `(item_type, solst, meta_options, hide_list, item_map)` のタプルを
  `flask.g._sort_meta_item_type_cache`(キー=item_type_id)にメモ化。同一 item_type_id は初回のみ計算。
- **安全性の根拠**: これらは item_type_id にのみ依存し、関数の残処理で**読み取り専用**であることをコード解析で確認
  (`to_orderdict()` は order list を読み取りのみ、`solst_dict_array` は新規リストに構築)。よって複数ヒット間で共有可。
- **リスク**: なし(`g` はリクエスト終了で破棄)。app コンテキスト不在時はメモ化をスキップ。

---

## 3-1 — アイテム詳細のOAI XML再構築キャッシュ

| 項目 | 内容 |
|------|------|
| 対象関数 | `weko_records_ui.views.default_view_method()`(`getrecord()`/`etree.tostring` 部分) |
| 新規config | `WEKO_RECORDS_UI_GOOGLE_XML_CACHE_TTL = 300`(`weko_records_ui/config.py`) |
| コミット | `6d8e7e2d8` |

- **変更前**: Google Scholar / Dataset メタ生成のためだけに、描画毎に完全な JPCOAR OAI-PMH XML を
  `etree.tostring(getrecord(...))` で再構築 → `etree.fromstring` で再パース。
- **変更後**: XML 文字列(`recstr`)を `current_cache` にキャッシュ。
  - **キー**: `record_jpcoar_xml_{oai_id}_{revision_id}`
    - `revision_id` はレコードのリビジョン。**編集でリビジョンが上がるため即時失効**。
  - **TTL**: `WEKO_RECORDS_UI_GOOGLE_XML_CACHE_TTL`(既定300秒。リビジョンに現れない変更=アイテムタイプ
    マッピング編集等のためのバックストップ)。
  - キャッシュ拡張未設定時 or `oai_id` 無しの場合はスキップ。
- **不変性**: XML はレコード内容にのみ依存(ユーザー非依存・言語非依存)。グローバルキャッシュで安全。
- **リスク**: リビジョンに現れない変更は最大TTL秒ステール。影響軽微。

---

## 4-1 — 検索一覧 per-item 処理の同期最適化

| 項目 | 内容 |
|------|------|
| 対象関数 | `weko_records.utils.sort_meta_data_by_options()`(値照合ループ)、`invenio_records_rest.serializers.response.py`(`view`/import) |
| コミット | `93eab88fa`(テスト基盤: `406859f34`) |

**方針**: 本物のスレッド並列化は、Flask アプリコンテキスト/DBセッションのスレッド安全性、および 4-3 の
`flask.g` メモ化(スレッド毎に分断される)との競合というリスクがあるため**不採用**。pref_issues.md の推奨どおり
**同期最適化**を実施。

- **4-4 相当(O(n²)→O(n))**: `sort_meta_data_by_options` 内で、メタデータ各項目に対し `solst_dict_array` 全体を
  線形走査していた二重ループ(しかも `for lst in solst` の内側)を、`solst_dict_array` を key で引ける dict
  `solst_dict_by_key`(初出優先)を一度だけ構築し **O(1) 参照**に置換。first-match-then-break の挙動を維持。
- **デッドコード除去**: `response.py` の `view()` にあった `with ThreadPoolExecutor(max_workers=10):`(生成のみで
  タスク投入に未使用)と、その import を削除。ヒットは引き続きイベントループ上で逐次整形(挙動不変)。
  `sort_meta_data_by_options` はテストが `await` するため `async def` のまま維持。
- **リスク**: なし(出力不変。スレッド化していないためスレッド安全性問題も発生しない)。

---

## 付随したテスト基盤修正(既存の失敗を解消)

パフォーマンス修正の検証を可能にするため、既存のテストフィクスチャ不具合も修正した(本番コードには影響しない)。

| 内容 | 対象 | コミット |
|------|------|---------|
| `user_activity_logs` 当月パーティション作成、`item_type_mapping` FK挿入順(Continuum)、文字列引数テスト | weko-theme, weko-records-ui | `71cc1a75e` |
| `user_activity_logs` パーティション作成、`InvenioCache` 初期化 | weko-items-ui | `3a6530bde` |
| `item_type_mapping` FK挿入順(Continuum) | invenio-records-rest | `406859f34` |
