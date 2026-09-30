# WEKO3 表示速度パフォーマンス問題まとめ (pref_issues.md)

> トップページ・アイテム詳細(ランディングページ)・検索結果一覧の表示遅延について、
> **WEKO3 に不慣れな人でも読んで理解でき、修正コードを書けること** を目的にまとめたドキュメントです。
> 記載の `file:line` は調査時点(ブランチ `develop_v2.1.0`)のものです。修正前に必ず現物を確認してください。

---

## 実装状況 (2026-07-22 時点 — 全課題対応済み)

下表の全課題を実装・テスト・コミット済み(ブランチ `develop_v2.1.0`)。キャッシュ系はユーザー選択により
**短TTL方式**(既定 300 秒、`*_CACHE_TTL` config で調整可)を採用。テストは稼働中の docker テスト環境で検証。

| 課題 | 内容 | コミット |
|------|------|---------|
| 共通A | `get_search_setting()` を各ビューで3回→1回に集約 | `1288154d4` |
| 共通C | ウィジェット設計取得をリクエスト内メモ化(flask.g) | `a76f6c564` |
| 共通B | `get_search_detail_keyword()` を短TTLキャッシュ(host+lang+auth キー) | `b63d08a73` |
| 3-2 | アイテム詳細の二重N+1インデックスループをメモ化で統合 | `4cde4e05f` |
| 2-1 | `get_ranking()` を短TTLキャッシュ(guest共通 / 認証ユーザー別キーで漏洩防止) | `b412edaa6` |
| 4-3 | 検索一覧のアイテムタイプ由来データをリクエスト内メモ化 | `723ecb7a6` |
| 3-1 | アイテム詳細のOAI XML再構築を oai_id+revision キーでキャッシュ | `6d8e7e2d8` |
| 4-1 | 検索一覧 per-item の O(n²) 照合を O(n) 化 + 未使用ThreadPoolExecutor除去(スレッド並列化は不採用) | `93eab88fa` |

**補足(4-1)**: 本物のスレッド並列化は、Flaskアプリコンテキスト/DBセッションのスレッド安全性、および 4-3 の
`flask.g` メモ化との競合というリスクがあるため**不採用**とし、pref_issues.md 記載どおり同期最適化を実施した。

**支援したテスト基盤修正**(既存の失敗を解消): `71cc1a75e`(theme/records-ui のパーティション・FK順序・文字列引数)、
`3a6530bde`(items-ui のパーティション・InvenioCache初期化)、`406859f34`(invenio-records-rest の FK順序)。

---

## 0. 前提知識(WEKO3 の構造をざっくり)

WEKO3 は **Invenio**(Python/Flask 製のリポジトリフレームワーク)をベースにした、機関リポジトリシステムです。
コードは `modules/` 配下に **機能ごとの独立モジュール(Flask拡張)** として分かれています。1画面の表示に複数モジュールが協調します。

主要モジュールと役割(本ドキュメントで登場するもの):

| モジュール | 役割 |
|-----------|------|
| `weko-theme` | **トップページ**の表示、共通レイアウト |
| `weko-gridlayout` | トップページ等の**ウィジェット**(ランキング枠・新着枠など)設計/表示 |
| `weko-records-ui` | **アイテム詳細ページ(ランディングページ)** の表示、ファイルダウンロード |
| `weko-search-ui` | 検索、**検索結果一覧**、検索条件の生成 |
| `weko-records` | アイテム(レコード)のデータモデルと、表示用メタデータ整形 |
| `weko-items-ui` | アイテムタイプ定義、**ランキング**計算 |
| `weko-index-tree` | インデックス(=カテゴリ/フォルダのツリー) |
| `weko-admin` | 各種管理設定(検索設定・サイト情報など) |
| `invenio-records-rest` | 検索 REST API と、検索結果のシリアライズ(整形) |

### 覚えておくと読みやすい用語

- **PID / recid**: アイテムを一意に識別するID(Persistent IDentifier)。`recid` は WEKO のレコード番号。
- **Index / インデックス**: アイテムを分類するツリー構造(フォルダのようなもの)。1アイテムは複数インデックスに属せる。
- **Item Type / アイテムタイプ**: アイテムの入力項目定義(スキーマ)。論文用・データセット用などがある。
- **ES / Elasticsearch**: 検索エンジン。全文検索・集約(集計)を担う。DB(PostgreSQL)とは別。
- **Mapping / JPCOAR**: メタデータ項目を日本の学術メタデータ標準(JPCOAR)に対応づける設定。
- **Widget / ウィジェット**: トップpage等に配置する部品(ランキング・新着・自由テキスト等)。`weko-gridlayout` が管理。

### データストアは2種類

1. **PostgreSQL (DB)**: レコード本体・設定・インデックス定義など。SQLAlchemy 経由でアクセス。
2. **Elasticsearch (ES)**: 検索・ランキング集約。

**パフォーマンス問題のほとんどは「1リクエストの中で DB / ES へのアクセスが必要以上に繰り返される」ことが原因** です。
以下、①全ページ共通の原因 → ②ページ別の原因、の順で説明します。

---

## 1. 全ページ共通の根本原因(まずここを直すと効果が広い)

同じ設定値を取得するために、**1回の画面表示で同じDBクエリを何度も実行**しています。
リクエスト内で1回だけ取得してキャッシュ(使い回し)すれば解消します。

### 共通A: `get_search_setting()` を1リクエストで3〜5回呼ぶ

**関数定義**: `modules/weko-admin/weko_admin/utils.py:109`

```python
def get_search_setting():
    """Get search setting from DB."""
    res = SearchManagement.get()   # ← DBアクセス。しかも内部で2クエリ(下記)
    if res:
        db_obj = res.search_setting_all
        ...
        return db_obj
    else:
        return config.WEKO_ADMIN_MANAGEMENT_OPTIONS
```

`SearchManagement.get()` 自体が **`MAX(id)` を求めるサブクエリ + `filter_by` の2クエリ構成**(`modules/weko-admin/weko_admin/models.py` 付近)で、キャッシュがありません。

**同一リクエスト内での呼び出し箇所(いずれも同じ結果が返る):**

- トップページ: `modules/weko-theme/weko_theme/utils.py:77, 84, 91`(`get_weko_contents` 内で3回)
- アイテム詳細: `modules/weko-records-ui/weko_records_ui/views.py:708, 715, 722`(3回)
- 検索結果一覧: `modules/weko-search-ui/weko_search_ui/views.py:248, 261, 273`(3回)

いずれも `.get("display_control", {}).get("display_xxx", {}).get("status", False)` を取り出すためだけに、
**設定オブジェクト全体を3回取り直しています。**

**修正方針**: 各ビューの冒頭で `search_setting = get_search_setting()` を1回だけ実行し、
以降は `search_setting.get(...)` で参照する。さらに `get_search_setting()` 自体を
リクエストスコープ(`flask.g`)または短時間のRedisキャッシュにするのが望ましい。

```python
# 修正イメージ(各ビュー内)
search_setting = get_search_setting()
display_control = search_setting.get("display_control", {})
display_facet_search = display_control.get("display_facet_search", {}).get("status", False)
display_index_tree  = display_control.get("display_index_tree", {}).get("status", False)
display_community   = display_control.get("display_community", {}).get("status", False)
```

---

### 共通B: `get_search_detail_keyword('')` を毎リクエスト、フル実行

**関数定義**: `modules/weko-search-ui/weko_search_ui/api.py:168`

これは「詳細検索フォーム用のキーワード候補」を組み立てる関数で、内部で以下の重い処理を毎回行います。

- `ItemTypes.get_latest()` で **全アイテムタイプをDBから取得**
- **インデックスツリー全体を `get_childinfo()` で再帰走査** し、トップインデックスごとに全子孫を平坦化
- さらに内部で `SearchManagement.get()`(共通Aと同じ)を呼ぶ

キャッシュはありません。**呼び出し箇所:**

- トップページ: `modules/weko-theme/weko_theme/utils.py:73`(`get_weko_contents` 内)
- アイテム詳細: `modules/weko-records-ui/weko_records_ui/views.py:520`

インデックス数・アイテムタイプ数が多い機関ほど重くなります。

**修正方針**: 結果(アイテムタイプ由来・インデックスツリー由来の部分)は頻繁に変わらないため、
Redis 等でキャッシュし、アイテムタイプ/インデックス更新時に破棄(invalidate)する。

---

### 共通C: ウィジェット設計(gridlayout)の設定を重複DB照会

トップページとアイテム詳細で `get_design_layout()` を呼びます。
`modules/weko-theme/weko_theme/utils.py:120`:

```python
def get_design_layout(repository_id):
    main_has_main  = main_design_has_main_widget(repository_id)      # DB照会 + JSONパース
    page_with_main = get_widget_design_page_with_main(repository_id) # DB照会 + JSONパース
    ...
```

トップページではさらに `has_widget_design()`(`utils.py:149`)が
`WidgetDesignServices.get_widget_design_setting()` → `select_by_repository_id()` を **再度** 呼びます
(`modules/weko-gridlayout/weko_gridlayout/services.py:636`)。

モデル層 `select_by_repository_id`(`weko_gridlayout/models.py:400`)/ `get_by_repository_id`(`models.py:674`)は
いずれもキャッシュ無しの生クエリで、`settings` の JSON を毎回パースします。

**修正方針**: 同一 `repository_id` の設計取得を1リクエスト1回に集約。設計データはRedisキャッシュしてOK
(WEKO には既に `delete_widget_cache()` という破棄関数があるので、これと対にしてキャッシュを導入できる)。

---

## 2. トップページ (`/`)

**入口**: `modules/weko-theme/weko_theme/views.py:49` `index()`
→ `get_weko_contents()`(theme/utils.py:51)で各種設定を集め、テンプレート `frontpage.html` を描画。

### 2-1.【最重要・条件付き】ランキング表示時に ES集約5連発 + N+1 DBクエリ

管理画面で「初期表示=ランキング」(`init_disp_setting == '1'`)に設定されている場合、
テンプレート描画中に `get_ranking()` が呼ばれます。

**関数**: `modules/weko-items-ui/weko_items_ui/utils.py:3847` `get_ranking(settings)`

```python
def get_ranking(settings):
    ...
    index_json = Indexes.get_browsing_tree_ignore_more()   # インデックスツリー全取得
    index_info = {}
    _get_index_info(index_json, index_info)                # ツリーを再帰で平坦化
    ...
    # この後、以下5種類の Elasticsearch 集約クエリを順に実行:
    #   most_reviewed_items / most_downloaded_items / created_most_items_user
    #   most_searched_keywords / new_items
```

各ランキングの後処理 `get_permission_record()`(`utils.py:411`)が **N+1問題** を起こします:

```python
def get_permission_record(rank_type, es_data, display_rank, has_permission_indexes):
    ...
    for data in es_data:                       # ES結果を1件ずつループ
        ...
        pid_value = data['key'] if 'key' in data else ...
        record = WekoRecord.get_record_by_pid(pid_value)   # ← 1件ごとにDB照会(N+1)
```

**表示件数 + バッファ件数 × ランキング5種** ぶんの個別DBクエリが飛びます。しかもキャッシュ無し。

**なぜ遅いか**: ランキングは全ユーザーで同じ内容(統計は日次程度の更新で十分)なのに、
アクセスのたびに ES集約5回 + 数十件の個別DBクエリを実行している。

**修正方針**:
1. `get_ranking()` の結果を **Redis キャッシュ**(TTL 数時間〜1日、または集計バッチ時に更新)。
2. `get_permission_record()` の `WekoRecord.get_record_by_pid()` を **pid一括取得**(`IN` クエリ)に置き換えてN+1を解消。

### 2-2. 共通B(`get_search_detail_keyword`)/ 共通A(`get_search_setting`×3)/ 共通C(ウィジェット)

前章のとおり。トップページはこれら共通原因の影響を全て受けます。

### 2-3.【条件付き】新着/特定インデックス表示時のファイルI/O・全件走査

「初期表示=インデックス検索結果」(`init_disp_setting == '0'`)の場合:

- `get_journal_info()` が **リクエストごとにスキーマJSONをディスクから読む**:
  `json.load(open(schema_file))`(`modules/weko-search-ui/weko_search_ui/utils.py:332`)。キャッシュ無し。
- 「新着インデックス」モードでは公開インデックスを全件スキャン + ロール判定で全走査。

**修正方針**: スキーマファイルはモジュールロード時に一度読んでメモリ保持。公開インデックス取得はキャッシュ化。

### 2-4.(軽微)ロジックの無駄

`modules/weko-theme/weko_theme/views.py:68` で `page = None` と再代入し、
直前の `get_design_layout()` で得た `page` を捨てています。意図が不明な場合は要確認
(`get_design_layout` 内のDB処理は実行済みなので、取得コストだけ払って結果を捨てている)。

---

## 3. アイテム詳細ページ / ランディングページ (`/records/<recid>`)

**入口**: `modules/weko-records-ui/weko_records_ui/views.py:391` `default_view_method()`

**3ページの中で最も処理が重い**ページです。1リクエストで多数のDB/ES/XML処理を直列実行します。

### 3-1.【最重要】OAI-PMH の JPCOAR XML を表示のたびにフル再構築

`views.py:529-538`:

```python
recstr = etree.tostring(
    getrecord(                                   # ← OAI-PMH の getrecord を実行
        identifier=record['_oai'].get('id'),
        metadataPrefix='jpcoar',
        verb='getrecord'
    )
)
et = etree.fromstring(recstr)                     # ← 生成したXML文字列を再パース
google_scholar_meta = get_google_scholar_meta(record, record_tree=et)
google_dataset_meta = get_google_detaset_meta(record, record_tree=et)
```

Google Scholar / Google Dataset 用の `<meta>` タグを作るためだけに、
**OAI-PMH の完全な JPCOAR XML レコードを毎回シリアライズ→再パース** しています。
OAIシリアライザはマッピング変換を伴う重い処理で、これをページ表示のたびに実行するのは高コストです。

**修正方針**:
- Google用メタは限られた項目(タイトル・著者・日付・DOI等)だけあれば十分なので、
  OAI XML全体を作らず `record` から直接生成できないか検討する。
- どうしてもXMLが必要なら、生成済みXMLを recid + 更新日時をキーに **キャッシュ**。

### 3-2.【重要】インデックスパスの N+1 クエリを「二重に」実行

同じ `record.navi`(所属インデックスのパス一覧)を **2回別々にループ** し、
その都度 `Indexes.get_index(path)` をDB照会しています。

**1回目** — `views.py:450-461`(表示名 `path_name_dict` の構築):

```python
for navi in record.navi:
    path_arr = navi.path.split('/')
    for path in path_arr:
        index = Indexes.get_index(index_id=path)   # ← path ごとにDB照会(N+1)
        idx_name = index.index_name or ""
        ...
```

**2回目** — `views.py:753-761`(所属コミュニティ `belonging_community` の構築):

```python
for navi in record.navi:
    path_arr = navi.path.split('/')
    for path in path_arr:
        index = Indexes.get_index(index_id=path)   # ← 同じ index を再度DB照会
        communities = GetCommunity.get_community_by_root_node_id(index.id)  # ← さらにN+1
        ...
```

深い階層 × 複数インデックス所属のアイテムほど、`get_index` の呼び出し回数が増えます。

**修正方針**:
1. 2つのループを1つに統合し、`Indexes.get_index()` の結果を dict にメモ化して使い回す。
2. `record.navi` に登場する全 path を集めて **一括取得**(`IN` クエリ)する。

### 3-3. 共通B(`get_search_detail_keyword('')`)

`views.py:520`。トップページと同じ重い関数をアイテム詳細でも毎回実行。前章の修正方針を参照。

### 3-4. 単発の設定・DBクエリが多数、直列に並ぶ

アイテム詳細ビューは、下記のような「単発だが積み重なる」DBアクセスが直列に並びます:

| 箇所 | 処理 |
|------|------|
| `views.py:523` | `ItemLink.get_item_link_info()`(関連アイテム) |
| `views.py:621` | `PDFCoverPageSettings.find(1)` |
| `views.py:646` | `AdminSettings.get('display_stats_settings')` |
| `views.py:653` | `AdminSettings.get('items_display_settings')` |
| `views.py:670` | `get_design_layout()`(共通C) |
| `views.py:688` | `get_file_info_list()`(ファイル情報整形) |
| `views.py:708/715/722` | `get_search_setting()` ×3(共通A) |
| `views.py:768` | `AdminSettings.get('restricted_access')` |

**修正方針**: `AdminSettings.get()` 系の管理設定は変更頻度が低いのでまとめてキャッシュ化。
共通A/Cを解消するだけでも数クエリ削減できる。

### 3-5. バージョン取得で `WekoRecord.get_record()` を複数回

`views.py:470, 473` で active/all バージョンの draft 判定のために `WekoRecord.get_record()` を都度実行。
影響は小さめだが、上記と合わせて見直し対象。

---

## 4. 検索結果一覧 (`/search`)

**入口**: `modules/weko-search-ui/weko_search_ui/views.py:80` `search()`
このビューは **HTMLの外枠だけ** を返し、実データは REST 検索 API(`recid` エンドポイント)が JSON で返します。
JSはその整形済みフィールドを描画するだけで、**1件ごとの追加AJAXはありません**。
→ **重い per-item 処理はすべてサーバ側の整形関数に集約** されています。

### 4-1.【最重要】「並列化したつもり」で実際は逐次実行

検索結果は1ヒットごとに `sort_meta_data_by_options()` で表示用に整形されます。

**呼び出し側**: `modules/invenio-records-rest/invenio_records_rest/serializers/response.py:106` 付近

```python
with ThreadPoolExecutor(max_workers=10):        # ← 生成するだけで、実際には使っていない
    task = asyncio.gather(
        __format_item_list(search_result['hits']['hits'])
    )
    loop.run_until_complete(task)
```

`__format_item_list` は各ヒットに対し `asyncio.ensure_future(sort_meta_data_by_options(...))` を積んで
`asyncio.gather` します。ところが —

**整形関数本体**: `modules/weko-records/weko_records/utils.py:958`

```python
async def sort_meta_data_by_options(record_hit, settings, item_type_data):
    ...
    # 関数の中に `await` が一つも無く、中身はすべて同期的な CPU/DB 処理
```

`async def` でも **`await` が無ければ並行にはならず**、単一イベントループ上で **全ヒットが逐次実行** されます。
さらに `ThreadPoolExecutor(max_workers=10)` は `with` で生成されるだけで **タスク投入に使われていません**。

**結果**: 下記4-2〜4-4の per-item コストが、**ページ表示件数ぶん直列に加算** されます
(通常20件、INDEX表示 `display_format==2` では最大100件 — `views.py:242` 付近)。

**修正方針**(いずれか):
- (堅実)`sort_meta_data_by_options` を通常の同期関数として `ThreadPoolExecutor` に **実際に `submit` して並列化**する。
  中身がDB/CPU処理なのでスレッドプールが適切(GIL下でもDB待ちは並行化できる)。
- (根本)per-item コスト自体を4-2〜4-4のとおり削減する。

> 注意: この関数はDBセッションや Flask の `current_app` コンテキストに触れるため、
> スレッド化する場合は **アプリケーションコンテキストの push とDBセッションのスレッド安全性** に注意すること。

### 4-2. ヒットごとにメタデータを pickle で2回ディープコピー

`modules/weko-records/weko_records/utils.py:1573-1574`:

```python
src_default    = pickle.loads(pickle.dumps(record_hit["_source"].get("_item_metadata"), -1))
_item_metadata = pickle.loads(pickle.dumps(record_hit["_source"], -1))
```

各ヒットで `_item_metadata` と `_source` 全体を丸ごと複製。メタデータが大きいアイテムほど重く、これを全件分繰り返します。

**修正方針**: 実際に書き換える必要がある範囲だけを浅くコピーする。全体ディープコピーを避ける。

### 4-3. アイテムタイプ関連データをヒットごとに再取得・再計算(プリフェッチ済みなのに使わない)

`modules/weko-records/weko_records/utils.py:1583-1591`(`sort_meta_data_by_options` 内):

```python
item_type = ItemTypes.get_by_id(item_type_id)              # ← 1件ごとにDB照会
solst, meta_options = get_options_and_order_list(
    item_type_id, item_type_data=ItemTypes(item_type.schema, model=item_type))
hide_list = get_hide_list_by_schema_form(schemaform=item_type.render...)
item_map  = get_mapping(item_type_id, "jpcoar_mapping", item_type=item_type)  # DB + 再帰構築
```

呼び出し元(`response.py` 側)が `ItemTypes.get_records()` で **アイテムタイプを一括プリフェッチして
`item_type_data` として渡している** のに、関数内で `ItemTypes.get_by_id` を再取得し、
`get_options_and_order_list` / `get_hide_list_by_schema_form` / `get_mapping` を **毎ヒット再計算** しています。

検索結果は同じアイテムタイプの行が多数並ぶのが普通なので、**同一 `item_type_id` の同一計算が件数ぶん重複** します。

**修正方針**: `item_type_id` をキーに、これら4つの計算結果を **リクエスト内でメモ化**(辞書キャッシュ)。
プリフェッチ済み `item_type_data` を実際に使う。

### 4-4. フィールド突き合わせが per-hit で準二次ループ

`modules/weko-records/weko_records/utils.py:1706-1730` 付近:

```python
meta_data = get_all_items2(mlt, solst)
for m in meta_data:                       # メタデータ各項目
    for s in solst_dict_array:            # × アイテムタイプの全フィールド定義
        s_key = s.get("key")
        tmp = m.get(s_key)
        ...
```

`O(メタデータ項目数 × フィールド定義数)` のループを各ヒットで実行。フィールドの多いアイテムタイプで肥大化。

**修正方針**: `solst_dict_array` を `key` で引ける dict に前処理し、内側ループを O(1) 参照に置き換える。

### 4-5. ファイル情報整形でファイルごとに権限チェック

`utils.py:1664` → `get_file_comments()`(`utils.py:1323-1367`)→ `check_file_download_permission()`。
`check_file_download_permission`(`modules/weko-records-ui/weko_records_ui/permissions.py`)は内部で
`User.query`(ユーザ/ロール解決)やサイトライセンス判定を行い、**ヒット × ファイル** ごとに実行されます。

**修正方針**: ユーザ/ロール解決結果とサイトライセンス判定を **リクエスト内でメモ化**(同一ユーザーなら1回)。

### 4-6.(参考)検索クエリ生成側

`get_permission_filter()`(`modules/weko-search-ui/weko_search_ui/query.py:56`)が毎検索で
`Indexes.get_browsing_tree_paths()` を呼び、**閲覧可能な全インデックスパス**(数百件になりうる)を構築します。
factory 内で複数回呼ばれ、キャッシュがありません。

**修正方針**: 閲覧可能インデックスパスをリクエスト内(またはユーザー×短TTL)でキャッシュ。

---

## 5. 修正の進め方(おすすめ順)

「費用対効果(効果 ÷ 改修リスク)」の高い順:

| 順 | 対応 | 効果範囲 | リスク | 期待改善(推定) |
|----|------|---------|--------|----------------|
| 1 | **共通A**: `get_search_setting()` を各ビューで1回に集約 | 全3ページ | 小 | 小(数ms〜十数ms) |
| 2 | **共通C**: ウィジェット設計取得をリクエスト内で共有/キャッシュ | トップ・詳細 | 小 | 小(数ms〜十数ms) |
| 3 | **共通B**: `get_search_detail_keyword` をキャッシュ | トップ・詳細 | 中 | 中〜大(数十ms〜数百ms) |
| 4 | **3-2**: アイテム詳細のインデックス二重N+1ループを統合・一括取得 | 詳細 | 小〜中 | 小〜中(数ms〜数十ms) |
| 5 | **2-1**: ランキングを Redisキャッシュ + N+1解消 | トップ(ランキング時) | 中 | 大(数百ms〜数秒) |
| 6 | **4-3**: 検索一覧のアイテムタイプデータを item_type_id 単位でメモ化 | 一覧 | 中 | 大(一覧の主要因) |
| 7 | **3-1**: アイテム詳細のOAI XML再構築を回避/キャッシュ | 詳細 | 中 | 中〜大(数十ms〜数百ms) |
| 8 | **4-1**: 検索一覧の per-item 処理を実並列化 or 同期最適化 | 一覧 | 大(要検証) | 中〜大(DB待ちが多いほど) |

### 5-1. 期待できる速度改善の見積もり(詳細)

> ⚠️ **重要**: 以下は **実測値ではなく、コードから導いた工学的推定** です。実際の数値は
> **アイテムタイプ数・インデックス数・レコードサイズ・DB/ESのレイテンシ・キャッシュヒット率** に大きく依存します。
> 確定には §5「修正時の共通注意」のとおり Before/After の計測が必須です。
> 目安として想定した基準値: **DB1クエリ ≒ 0.5〜2ms(同一ホスト/LAN)、ES集約1回 ≒ 20〜100ms**。
> DBがネットワーク越し(往復2〜5ms)の環境では、クエリ数削減の効果はこの数倍になります。

#### 共通A(`get_search_setting` ×3→1): **小**

- 削減量: 1ページあたり `get_search_setting()` 3回 → 1回。1回=2クエリなので **約4クエリ削減**。
- 推定: 同一ホストで **数ms〜十数ms**、DBがネットワーク越しなら十数ms〜数十ms。
- 位置づけ: 単体の効果は小さいが **改修が容易でリスクが低く、全3ページに効く**。最初に着手する価値がある。

#### 共通B(`get_search_detail_keyword` キャッシュ): **中〜大(環境依存)**

- 削減量: 全アイテムタイプ取得 + **インデックスツリー全体の再帰走査** + 内部の設定取得を、キャッシュヒット時はほぼ0に。
- 推定: 小規模機関(アイテムタイプ数点・インデックス数十)なら **数十ms**、
  **大規模機関(アイテムタイプ多数・インデックス数千)では数百ms** に達しうる。トップ・詳細の両方で毎回発生している点が大きい。
- 注意: キャッシュミス時(初回・破棄直後)は従来どおりの時間がかかる。効果は **ヒット率次第**。

#### 共通C(ウィジェット設計の共有/キャッシュ): **小**

- 削減量: 同一 `repository_id` の設計取得(DB照会 + JSONパース)を1リクエスト2回前後 → 1回。
- 推定: **数ms〜十数ms**。JSONが大きい設計ほど、パース削減分が効く。

#### 3-2(アイテム詳細のインデックス二重N+1統合): **小〜中(アイテムの所属状況依存)**

- 削減量: `record.navi` を2回ループ→1回に統合し、`Indexes.get_index()` を一括取得化。
  「所属インデックス数 × パス階層の深さ」ぶんの個別クエリ(+ `GetCommunity` 呼び出し)を削減。
- 推定: 所属が浅く1〜2件なら **数ms**、深い階層 × 複数インデックス所属のアイテムでは **数十ms**。
  アイテムによってばらつきが大きい。

#### 2-1(ランキングの Redisキャッシュ + N+1解消): **大(ランキング表示時)**

- 削減量: **ES集約5回**(各20〜100ms)+ `get_permission_record` の **N+1 DBクエリ数十件** を、キャッシュヒット時はほぼ0に。
- 推定: この処理だけで **数百ms〜数秒**。トップページがランキング表示設定の場合、**体感で最も効く改善**。
- 補足: キャッシュ導入前でも N+1解消(pid一括取得)だけで数十件のクエリを1件に減らせ、ES部分を除いても効果あり。
- 注意: 「初期表示=ランキング」設定でない機関には影響しない(条件付き)。

#### 4-3(検索一覧のアイテムタイプデータ メモ化): **大(一覧遅延の主要因)**

- 削減量: 1ページの各ヒットで実行していた `ItemTypes.get_by_id` / `get_options_and_order_list` /
  `get_mapping`(DB + 再帰構築)/ `get_hide_list_by_schema_form` を、**item_type_id 単位で1回に集約**。
- 推定: 検索結果は同一アイテムタイプの行が多数並ぶため、20件中18件が同一タイプなら **その18件分の再計算がほぼ消える**。
  1件あたりの整形コストの相当部分を占めるので、**一覧全体の描画時間を大きく短縮**できる可能性が高い。
- 位置づけ: 4-1(並列化)より **リスクが低く効果が確実**。一覧改善はまずここから。

#### 3-1(アイテム詳細の OAI XML 再構築を回避/キャッシュ): **中〜大(レコードサイズ依存)**

- 削減量: `getrecord()` による **JPCOAR XML の完全シリアライズ + 再パース** を、
  record からの直接生成またはキャッシュで回避。
- 推定: メタデータ項目の少ないアイテムで **数十ms**、項目の多い/添付の多いアイテムで **数百ms**。
  詳細ページを開くたびに毎回発生しているため、詳細ページ全体では大きな割合を占めうる。

#### 4-1(検索一覧の per-item 処理の実並列化/同期最適化): **中〜大(要検証)**

- 前提: 現状は「並列化したつもりで逐次実行」。per-item コストが **表示件数ぶん直列に加算**(最大100件)。
- 推定: 各 per-item 処理に **DB待ちが多いほど**、スレッド並列化の効果が出る(DB往復を重ねられる)。
  ただし Python の GIL によりCPU処理部分は並列化されないため、**理論上の N倍にはならない**。現実的には数倍程度が上限。
- 位置づけ: **リスクが最も高い(アプリコンテキスト/DBセッションのスレッド安全性)**。
  まず 4-3(メモ化)・4-2(pickle削減)・4-4(ループ改善)で per-item コスト自体を下げ、
  それでも足りなければ並列化を検討するのが安全。

### 5-2. まとめ:効果の大きい順(推定)

1. **ランキング表示時**は 2-1 が最大(数百ms〜数秒)。ただし該当設定の機関のみ。
2. **検索結果一覧**は 4-3 → 4-1 の順で、件数 × アイテムタイプ由来の再計算削減が効く。
3. **アイテム詳細**は 3-1(XML)と 3-2(N+1)、および共通A/B/Cの合算で効く。
4. **共通A/B/C**は単体では中〜小だが、**全ページに効き、低リスクで着手しやすい**ため最初のステップに最適。

> **結論**: 「まず共通A/C(低リスク・低コスト)で足場を固め、次に各ページの最大要因
> (トップ=2-1、一覧=4-3、詳細=3-1)に取り組む」のが、リスクを抑えつつ体感改善を得やすい進め方です。
> 繰り返しになりますが、**着手前後で必ず計測** し、推定値を実測で裏付けてください。

### 修正時の共通注意

- **測って直す**: まず遅い画面で「発行されたSQL数」「ES呼び出し数」「各処理の所要時間」を計測する
  (Flask-SQLAlchemy のクエリログ、`flask_debugtoolbar`、`current_app.logger` での区間計測など)。
  推測で直さず、Before/After を数値で比較する。
- **キャッシュには破棄(invalidate)をセットで**: 設定・アイテムタイプ・インデックス・ウィジェットを
  キャッシュする場合は、対応する管理画面の更新処理でキャッシュを破棄する
  (gridlayout には既に `delete_widget_cache()` がある)。
- **並列化は慎重に**: 4-1 のスレッド化は、Flask アプリケーションコンテキストとDBセッションの
  スレッド安全性を確認したうえで行うこと。まずは 4-2〜4-4 の同期最適化で効果が出るか確認するのが安全。

---

## 6. 主要ファイル早見表

| ページ | ファイル |
|--------|---------|
| トップ入口 | `modules/weko-theme/weko_theme/views.py:49` |
| トップ集約 | `modules/weko-theme/weko_theme/utils.py:51` (`get_weko_contents`) |
| ランキング | `modules/weko-items-ui/weko_items_ui/utils.py:3847` (`get_ranking`) / `:411` (`get_permission_record`) |
| 詳細入口 | `modules/weko-records-ui/weko_records_ui/views.py:391` (`default_view_method`) |
| 検索一覧入口 | `modules/weko-search-ui/weko_search_ui/views.py:80` (`search`) |
| 一覧整形(逐次) | `modules/invenio-records-rest/invenio_records_rest/serializers/response.py:106` 付近 |
| 一覧 per-item 整形 | `modules/weko-records/weko_records/utils.py:958` (`sort_meta_data_by_options`) |
| 検索設定(共通A) | `modules/weko-admin/weko_admin/utils.py:109` (`get_search_setting`) |
| 詳細検索候補(共通B) | `modules/weko-search-ui/weko_search_ui/api.py:168` (`get_search_detail_keyword`) |
| ウィジェット設計(共通C) | `modules/weko-gridlayout/weko_gridlayout/services.py:622` / `models.py:400,674` |

---

_調査ブランチ: `develop_v2.1.0` / 作成日: 2026-07-22_
