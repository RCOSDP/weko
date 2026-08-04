# WACREN 向けブランチ差分まとめ

`feature/nii_WACREN_pre` と タグ `v2.0.3` の差分をまとめたドキュメント。

| 項目 | 値 |
| --- | --- |
| 対象ブランチ | `feature/nii_WACREN_pre` |
| 比較元 | `v2.0.3` (= `origin/main` 先端, `d2fdc0e3b`, 2026-07-28) |
| v2.0.3 の取り込み | 済 (マージコミット `52ae8bf8a`) |
| コミット数 | 44 (うち非マージ 32) |
| 変更規模 | 84 ファイル / +11,232 / -1,782 |
| うち翻訳ファイル (`messages.po`) | 28 ファイル (新規 21) |
| 翻訳を除いた変更規模 | 56 ファイル / +3,443 / -1,461 |
| 対象期間 | 2024-12-13 〜 2026-08-04 |

差分は大きく **6 つのテーマ** に分かれる。

1. フランス語 (fr) 多言語対応
2. パフォーマンス改善（orjson 移行 / DB クエリ最適化 / フロントエンド / HTTP キャッシュ）
3. ARK 識別子対応
4. WACREN 環境固有の設定（Shibboleth / ロゴ / nginx）
5. Docker イメージ・ビルドの軽量化
6. API レート制限の設定化

---

## 1. フランス語 (fr) 多言語対応

WEKO 全体をフランス語に対応させる変更。UI 表示言語として `fr` を追加した。

- **翻訳リソース**: 28 モジュールに `translations/fr/LC_MESSAGES/messages.po` を追加・更新（21 ファイルが新規）。
  行数の多いもの: `weko-admin` (1,620), `weko-records-ui` (1,211), `weko-search-ui` (790),
  `weko-workflow` (622), `weko-theme` (564), `weko-items-ui` (481), `weko-index-tree` (411), `weko-gridlayout` (384)。
- **言語登録**: `scripts/populate-instance.sh` に `language create --active --registered "fr" "French" 003` を追加。
- **翻訳リソース生成スクリプト**: `make_lang_resource.sh` を新規追加。
  `modules/(invenio-|weko-)*` を走査し、対象外モジュール（`invenio-admin`, `invenio-app`, `invenio-db`,
  `invenio-iiif`, `invenio-indexer`, `invenio-mail`, `invenio-oaiharvester`, `invenio-queues`, `invenio-records` ほか）を
  除外したうえで、指定言語 (`$1`) の `.po` を一括生成する。

---

## 2. パフォーマンス改善

### 2-1. 標準 `json` → `orjson` への移行

`packages.txt` に `orjson==3.6.1`、`requirements-devel.txt` に `orjson==3.9.15` を追加し、
ホットパスの JSON 処理を orjson に置き換えた。

**互換レイヤー（新規）**: `modules/weko-records/weko_records/json_utils.py`
標準 `json` 互換の `dumps` / `loads` / `dump` / `load` / `dumps_bytes` を提供。
`ensure_ascii=True` や `TypeError` 発生時は標準 `json` にフォールバックする。
> **注意**: 現時点で本体コードからは使用されておらず、参照しているのは `tools/test_orjson_migration.py` のみ。
> 実際の移行は各ファイルで `import orjson` を直接呼ぶ形で行われている。

**移行済みファイル (13)**:

| ファイル | 主な置換内容 |
| --- | --- |
| `invenio-records-rest/views.py` | search_after キャッシュの Redis シリアライズ（`.encode('utf-8')` が不要になり削減） |
| `weko-records/api.py` | `ItemTypes` のフォーム定義生成（`parentkey` 置換） |
| `weko-records-ui/api.py` | S3 バケットポリシー生成 |
| `weko-schema-ui/schema.py`, `rest.py` | スキーマキャッシュ（`object_pairs_hook=OrderedDict` を廃止） |
| `weko-search-ui/admin.py`, `rest.py`, `tasks.py`, `utils.py` | 一括エクスポート・インポート、Redis キャッシュ、JSON-LD 読み込み |
| `weko-workflow/views.py`, `utils.py`, `rest.py` | アクティビティの `temp_data`、OA ポリシーキャッシュ、リクエストボディ解析 |

**計測ツール（新規）**:
- `tools/benchmark_json.py` — `json` と `orjson` のシリアライズ／デシリアライズ性能を
  データサイズ・構造別に比較するベンチマーク。
- `tools/test_orjson_migration.py` — 移行の妥当性検証スイート（ベンチマーク実行込み）。

### 2-2. DB クエリ最適化（N+1 解消・重複クエリ削減）

| 対象 | 変更内容 |
| --- | --- |
| `weko-records/api.py` `FeedbackMailList` | `Authors.get_emails_by_id()` のループ呼び出しを廃止し、`Authors.id.in_(...)` で一括取得 → `author_emails_map` に展開 |
| `weko-workflow/api.py` `WorkActivity.init_activity` | フローアクションごとの `get_action_detail()` を `_Action.id.in_(...)` の一括取得に変更 |
| `weko-workflow/api.py` `WorkActivityHistory.get_activity_history_list` | 履歴ごとの `_Action.query...first()` を一括取得＋辞書引きに変更 |
| `weko-workflow/api.py` `get_activity_by_id` | `joinedload(action / workflow / flow_define)` で eager loading 化 |
| `weko-workflow/api.py` `get_activity_steps` | `activity_detail` / `histories` を引数で受け取れるようにし、呼び出し側の再取得を回避。`_FlowAction` は `joinedload(action)` 化。重複していた `get_activity_by_id()` 呼び出しを削除 |
| `weko-items-ui/utils.py` `get_user_information` | `MetaData.reflect()` によるテーブル全件取得をやめ、`User` × `UserProfile` の outer join を `User.id.in_(...)` で 1 クエリに集約 |
| `weko-items-ui/utils.py` `get_workflow_by_item_type_id` | 2 段階クエリ（完全一致 → フォールバック）を `IN` + `CASE` による優先度付き 1 クエリに統合 |
| `weko-items-ui/utils.py` `check_item_is_being_edit` | `PIDVersioning` の重複生成をやめて 1 インスタンスを再利用。`latest_pid` の None チェックを追加 |

### 2-3. フロントエンド描画の改善

- **`content-visibility: auto` / `contain-intrinsic-size`** をアイテム詳細画面の重い領域に適用
  （`body_contents.html`, `item_detail.html`）。ファイル一覧 `<tbody>`、プレビューカルーセル、
  右カラム (`#invenio-csl`)、共有ボックスなど。
- **LCP 優先クラス** `.lcp-priority` を `box/head.html` に追加し、タイトル要素は `content-visibility: visible; contain: none` を維持。
- **JS の `defer` 化**: `weko_theme_js_top_page`, `invenio_deposit_dependencies_js`, `angular.js`,
  Twitter ウィジェットなど（`detail.html`, `file_details.html`, `search.html`, `box/share.html`）。
  `weko-workspace/item_register.html` の Babel browser.min.js は `type="module"` 化。
- **メディアの遅延読み込み**: プレビュー用 `<iframe>` に `loading="lazy"`、`<audio>` の `preload` を
  `auto` → `metadata`、`<video>` に `preload="metadata"` を付与。
- **サムネイル画像**: 先頭画像のみ `loading="eager"` + `fetchpriority="high"`、以降は `lazy`。
  `decoding="async"`、`width` / `height:auto` 指定でレイアウトシフトを抑制。属性値のクォート漏れも修正。
- **パーマリンク表示**: `box/head.html` で `display:inline-block` + `max-width:40ch` + `word-break:break-all` に変更（長い ARK/DOI の折り返し対策）。

### 2-4. HTTP キャッシュ

- **ETag / 条件付き GET**: `weko-records-ui/views.py` の `default_view_method` が
  `make_response()` + `set_etag()` + `make_conditional(request)` を返すようになった。
  ETag は `recid` / `updated` / `revision_id` / ユーザ ID（未ログインは `anon`）/ `request.full_path` から生成。
- **静的ファイル**: `nginx/weko.conf` の `location /static` に
  `expires 1y` と `Cache-Control: public, max-age=31536000, immutable` を追加。

### 2-5. 処理時間の計測ログ

- `weko-records-ui/views.py`: 設定 `WEKO_RECORDS_UI_PERF_LOG`（`scripts/instance.cfg` で既定 `False`）が有効なときのみ、
  `default_view_method` 内の 20 箇所超（`path_name_dict`, `pid_versioning`, `oai_getrecord_and_meta`,
  `meta_options_and_mapping`, `billing_files`, `files_and_thumbnails`, `total` ほか）を
  `perf_counter` で計測し `INFO` ログに出力する。
- `weko-items-ui/views.py`: `prepare_edit_item` の各ステップ
  （`lock_item_will_be_edit` / `resolver.resolve` / `permission_check` / `itemtype_lookup` /
  `check_an_item_is_locked` / `check_item_is_being_edit` / `prepare_edit_workflow` / `db_commit` / `total`）を
  `DEBUG` ログで計測。あわせて、`latest_activity` が無い場合の重複した
  `get_workflow_activity_by_item_id()` 呼び出しを削除。

### 2-6. その他の性能関連

- `modules/weko-redis/weko_redis/redis.py`: Redis Sentinel 接続に `socket_timeout` を指定。
  値は設定 `REDIS_SOCKET_TIMEOUT`、**既定 0.1 秒**。
- `scripts/instance.cfg`: `CELERY_GET_STATUS_TIMEOUT` を `3.0` → `1.0` に短縮。
- `modules/invenio-communities/invenio_communities/utils.py`:
  `invenio_files_rest.models` のトップレベル import をやめ、`save_and_validate_logo` /
  `initialize_communities_bucket` の関数内 import に移動（起動時の循環 import / import コスト回避）。

---

## 3. ARK 識別子対応

DOI / CNRI(Handle) に加えて **ARK** を第三の永続識別子として登録・表示できるようにした。

**設定 (`modules/weko-handle/weko_handle/config.py`)**

| 設定キー | 既定値 | 用途 |
| --- | --- | --- |
| `WEKO_HANDLE_ALLOW_REGISTER_ARK` | `False` | ARK 登録の有効化 |
| `WEKO_HANDLE_ARK_LOGIN_URL` | `None` | ARK サーバのログイン API |
| `WEKO_HANDLE_ARK_LOGIN_USER` | `None` | ログインユーザ |
| `WEKO_HANDLE_ARK_LOGIN_PASSWD` | `None` | ログインパスワード |
| `WEKO_HANDLE_ARK_MINT_URL` | `None` | ARK 発行 (mint) API |
| `WEKO_HANDLE_ARK_NAAN` | `None` | NAAN |
| `WEKO_HANDLE_ARK_SHOULDER` | `None` | Shoulder |
| `WEKO_HANDLE_ARK_TIMEOUT` | `30` | リクエストタイムアウト（秒） |

**実装 (`modules/weko-workflow/weko_workflow/utils.py`)** — 新規関数 5 つ

- `is_ark_registration_allowed()` — 有効化フラグと必須設定 6 項目が揃っているかを検査。
  不足があれば `ERROR` ログを出して `False`（「未設定」を「無効」と誤認させない設計）。
- `mint_ark(record_url)` — ログイン → トークン取得 → mint の 2 段階 API 呼び出し。
  **すべての失敗を握りつぶして `None` を返す**ため、ARK サーバ障害がアイテム登録自体を止めない。
- `_register_ark_pidstore(item_uuid, ark)` — `IdentifierHandle(item_uuid).register_pidstore('ark', ark)` で PID 登録。
- `register_ark(activity_id)` — ワークフローのアクティビティ単位で登録。
- `register_ark_by_item_id(deposit_id, item_uuid, url_root)` — アイテム ID 指定で登録。

**連携箇所**

- `modules/weko-deposit/weko_deposit/api.py`: `WekoRecord.pid_ark` プロパティを追加。
- `modules/weko-records-ui/weko_records_ui/utils.py`: `get_record_permalink()` の優先順位を
  **DOI → CNRI → ARK** に変更（従来の `doi or cnri` の三項演算子を明示的な分岐に書き換え）。
- `modules/invenio-oaiserver/invenio_oaiserver/response.py`: `get_identifier()` が
  ARK を `subitem_systemidt_identifier` として OAI-PMH レスポンスに含めるよう追加。
- `modules/weko-search-ui/weko_search_ui/utils.py`: `register_item_ark(item)` を新規追加し、
  `import_items_to_system()` から `WEKO_HANDLE_ALLOW_REGISTER_ARK` 有効時に呼び出し。
  手動 ARK 指定 (`is_change_identifier`) は **未実装**（警告ログを出して無視）。

---

## 4. WACREN 環境固有の設定

> このセクションの変更は WACREN のデモ／検証環境に固有の値であり、
> 本家 (`main`) へ持ち帰る際はそのまま取り込めない。

### `nginx/shibboleth2.xml`

- `<Host name>` / `entityID` を `weko3.example.org` → **`research.ren.ng`** に変更。
- IdP を WACREN のフェデレーション **`https://wacren.wacren.eduid.africa/saml2/idp/metadata.php`** に固定。
  `discoveryProtocol` / `discoveryURL` (SAMLDS/WAYF) の指定を削除。
- `<Handler type="Status">` の ACL から `0.0.0.0/0` を削除し `127.0.0.1 ::1` に戻した（**セキュリティ改善**）。
- `CredentialResolver` を署名／暗号化の 2 本立てからコメントアウトし、`server.key` / `server.crt` の単一指定に変更。
- ローカルメタデータのコメント例を整理、インデント統一。

### `nginx/login.php`

- `SHIB_ATTR_USER_NAME` の取得元を `HTTP_WEKOID` → **`mail`** に変更。
- `SHIB_ATTR_ROLE_AUTHORITY_NAME` を `HTTP_WEKOSOCIETYAFFILIATION` → **固定文字列 `"管理者"`** に変更。

> ⚠️ **要確認**: 後者は SSO でログインした全ユーザに管理者ロールを与える挙動になる。
> 検証目的と思われるが、本番投入前に必ず見直しが必要。

### `modules/weko-theme/weko_theme/config.py`

- `THEME_LOGO` / `THEME_LOGO_ADMIN` を `images/jairocloud-logo.png` → **`images/Rumbu_logo_white2.png`** に変更。
- 画像 `modules/weko-theme/weko_theme/static/images/Rumbu_logo_white2.png` (32KB) を追加。

---

## 5. Docker イメージ・ビルドの軽量化

### `Dockerfile`

- **runtime ステージを新設** (`FROM python:3.6-slim-buster AS runtime`)。
  ビルドツールを含まないランタイムライブラリのみ（`libpq5`, `libxml2`, `libxslt1.1`, `libffi6`,
  `libssl1.1`, `libjpeg62-turbo`, `libfreetype6`, `libtiff5`, `libzip4`, `libpcre3`, `supervisor`,
  `ca-certificates`）をインストールし、`build-env` から venv と `/code` のみを `COPY --from` する。
- Debian buster がアーカイブ入りしたため、apt ソースを `archive.debian.org` に書き換え。
- **ビルド時トグル (ARG)** を導入し、用途別に不要コンポーネントを外せるようにした。
  - `WITH_LIBREOFFICE` / `WITH_JRE` / `WITH_JA_FONTS` / `WITH_NODE`
- `build-env` ステージで pip/npm キャッシュと `__pycache__` / `*.pyc` を削除。
- `CMD` を `invenio run` から **`uwsgi --ini /code/scripts/uwsgi.ini`** に変更。

### `docker-compose2.yml`

- `web` / `worker` サービスに build args を指定。
  両方とも LibreOffice / JRE / 日本語フォントを無効化 (`0`)。Node は web のみ有効 (`WITH_NODE: "1"`)、worker は無効。

### `scripts/create-instance2.sh`

- webassets 用フィルタ (`node-sass@9.0.0`, `clean-css@3.4.12`, `requirejs`, `uglify-js`) を明示インストールし、
  `node_modules/.bin` を `PATH` に追加。
- アセットビルド後に `var/instance/static/node_modules` を削除してイメージサイズを削減。

### `scripts/provision-web.sh`

- すべての `apt-get install` に `--no-install-recommends` を付与。
- `build-essential` を明示追加（recommends 無効化に伴う不足対応）。
- クリーンアップで `/var/lib/apt/lists/*` を削除。

### `tools/runtime-libs-report.sh`（新規）

venv 配下の `*.so` と `uwsgi` に `ldd` をかけ、実際に必要な共有ライブラリ名を一覧出力する。
runtime ステージに入れるパッケージを決めるための調査ツール。

### `packages.txt`

- `orjson==3.6.1` 追加。
- `Pillow` を `8.1.2` → `8.4.0` に更新。

---

## 6. API レート制限の設定化

`@limiter.limit('')`（空文字＝実質無制限）だった **33 箇所** を、設定値を読む lambda に置き換えた。

```python
@limiter.limit(lambda: (current_app.config.get("WEKO_API_LIMIT_RATE_DEFAULT") or ["100 per minute"])[0])
```

- 29 箇所が `WEKO_API_LIMIT_RATE_DEFAULT`（`weko-accounts/config.py` に `['100 per minute']` として定義済み）。
- 4 箇所が `WEKO_WORKFLOW_API_LIMIT_RATE_DEFAULT`（`weko-workflow/config.py` に定義済み）。
- 対象モジュール: `weko-accounts`, `weko-authors`, `weko-index-tree`, `weko-items-ui`, `weko-records`,
  `weko-records-ui`, `weko-schema-ui`, `weko-search-ui`, `weko-swordserver`, `weko-workflow`。

---

## 7. 新規追加ファイル

| ファイル | 内容 |
| --- | --- |
| `make_lang_resource.sh` | 言語リソース (`.po`) 一括生成スクリプト |
| `modules/weko-records/weko_records/json_utils.py` | orjson 互換レイヤー（現状は未使用） |
| `modules/weko-theme/weko_theme/static/images/Rumbu_logo_white2.png` | WACREN 向けロゴ |
| `tools/benchmark_json.py` | json / orjson 性能ベンチマーク |
| `tools/test_orjson_migration.py` | orjson 移行の検証スイート |
| `tools/runtime-libs-report.sh` | 共有ライブラリ依存の調査ツール |
| `modules/*/translations/fr/LC_MESSAGES/messages.po` | フランス語翻訳（新規 21 ファイル） |

---

## 8. レビュー・本家取り込み時の注意点

### 環境固有のため切り離しが必要
1. **`nginx/login.php` のロール固定** — `SHIB_ATTR_ROLE_AUTHORITY_NAME` が `"管理者"` にハードコードされており、
   SSO ログインした全員が管理者になる。**本番投入前に必ず修正**。
2. **`nginx/shibboleth2.xml`** — ホスト名・entityID・IdP が WACREN 固定。
3. **`weko-theme/config.py` のロゴ** — `Rumbu_logo_white2.png` 固定。JAIRO Cloud 環境ではそのまま使えない。

### 動作確認が必要
4. **`json` → `orjson` の非互換**
   - `object_pairs_hook=OrderedDict` の指定が削除された（`weko-schema-ui/schema.py` ほか）。
     Python 3.7+ の `dict` は挿入順を保持するため通常は問題ないが、`isinstance(x, OrderedDict)` や
     `move_to_end()` / `popitem(last=False)` に依存する箇所があれば破綻する。
   - `json.dumps` は非文字列キーを文字列化するが、orjson は `OPT_NON_STR_KEYS` なしでは `TypeError`。
     コード全体で `OPT_NON_STR_KEYS` は未使用。
   - `orjson.dumps()` は `bytes` を返す。文字列が必要な箇所は `.decode('utf-8')` が付いているか要確認。
   - `ensure_ascii` の既定挙動が異なるため、生成される JSON 文字列のバイト列が変わる
     （Redis キャッシュや保存済みデータとの突き合わせがある場合は注意）。
   - `json_utils.py` はフォールバック付きの安全なラッパーだが**本体から使われていない**。
     ラッパー経由に統一するか、`json_utils.py` を削除するかの方針決めを推奨。
5. **`REDIS_SOCKET_TIMEOUT` の既定 0.1 秒** — 設定ファイルにキー定義がなく、ハードコードされた既定値のみ。
   ネットワーク遅延時に Sentinel 接続が落ちやすい可能性があるため、値の妥当性を実環境で確認したい。
6. **`CELERY_GET_STATUS_TIMEOUT` の 3.0 → 1.0 短縮** — タスク状態取得のタイムアウトが 1/3。
   負荷時に状態取得が失敗しないか確認が必要。
7. **ETag 条件付き GET** — ETag に `request.full_path` とユーザ ID を含めているが、
   権限や表示設定の変更（例: 公開範囲の切り替え）は ETag に反映されない。
   304 応答で古い内容が返らないか要確認。
8. **`get_user_information` の戻り値変更** — `userid` が `int` に固定され、
   ユーザ名／氏名の取得元が `UserProfile.get_by_userid()` から `User` × `UserProfile` の join に変わった。
   `username` は `UserProfile._displayname` を参照する。プロフィール未作成ユーザの挙動差に注意。
9. **ARK 手動指定が未実装** — `register_item_ark()` の `is_change_identifier` 分岐は
   警告ログのみで、指定された ARK は無視される。

### レビュー上の課題
10. **`weko-workflow/views.py` の大規模整形** — 2,888 行の差分のうち大半が
    black 相当のフォーマット変更（シングル→ダブルクォート、import の折り返し、関数シグネチャの改行）。
    実質的なロジック変更は orjson 置換 9 箇所とロギング追加 33 箇所程度。
    レビュー時は `git diff -w` や整形コミットの分離を検討したい。

---

## 9. 変更ファイル一覧（翻訳を除く 56 ファイル）

<details>
<summary>クリックして展開</summary>

```
Dockerfile
docker-compose2.yml
make_lang_resource.sh                                              (新規)
nginx/login.php
nginx/shibboleth2.xml
nginx/weko.conf
packages.txt
requirements-devel.txt
scripts/create-instance2.sh
scripts/instance.cfg
scripts/populate-instance.sh
scripts/provision-web.sh
tools/benchmark_json.py                                            (新規)
tools/runtime-libs-report.sh                                       (新規)
tools/test_orjson_migration.py                                     (新規)
modules/invenio-communities/invenio_communities/utils.py
modules/invenio-oaiserver/invenio_oaiserver/response.py
modules/invenio-records-rest/invenio_records_rest/views.py
modules/weko-accounts/weko_accounts/rest.py
modules/weko-authors/weko_authors/rest.py
modules/weko-deposit/weko_deposit/api.py
modules/weko-handle/weko_handle/config.py
modules/weko-index-tree/weko_index_tree/rest.py
modules/weko-items-ui/weko_items_ui/rest.py
modules/weko-items-ui/weko_items_ui/utils.py
modules/weko-items-ui/weko_items_ui/views.py
modules/weko-records/weko_records/api.py
modules/weko-records/weko_records/json_utils.py                    (新規)
modules/weko-records/weko_records/rest.py
modules/weko-records-ui/weko_records_ui/api.py
modules/weko-records-ui/weko_records_ui/rest.py
modules/weko-records-ui/weko_records_ui/utils.py
modules/weko-records-ui/weko_records_ui/views.py
modules/weko-records-ui/weko_records_ui/templates/weko_records_ui/body_contents.html
modules/weko-records-ui/weko_records_ui/templates/weko_records_ui/box/head.html
modules/weko-records-ui/weko_records_ui/templates/weko_records_ui/box/preview_carousel.html
modules/weko-records-ui/weko_records_ui/templates/weko_records_ui/box/share.html
modules/weko-records-ui/weko_records_ui/templates/weko_records_ui/detail.html
modules/weko-records-ui/weko_records_ui/templates/weko_records_ui/file_details.html
modules/weko-records-ui/weko_records_ui/templates/weko_records_ui/item_detail.html
modules/weko-redis/weko_redis/redis.py
modules/weko-schema-ui/weko_schema_ui/rest.py
modules/weko-schema-ui/weko_schema_ui/schema.py
modules/weko-search-ui/weko_search_ui/admin.py
modules/weko-search-ui/weko_search_ui/rest.py
modules/weko-search-ui/weko_search_ui/tasks.py
modules/weko-search-ui/weko_search_ui/utils.py
modules/weko-search-ui/weko_search_ui/templates/weko_search_ui/search.html
modules/weko-swordserver/weko_swordserver/views.py
modules/weko-theme/weko_theme/config.py
modules/weko-theme/weko_theme/static/images/Rumbu_logo_white2.png  (新規)
modules/weko-workflow/weko_workflow/api.py
modules/weko-workflow/weko_workflow/rest.py
modules/weko-workflow/weko_workflow/utils.py
modules/weko-workflow/weko_workflow/views.py
modules/weko-workspace/weko_workspace/templates/weko_workspace/item_register.html
```

</details>

---

## 10. コミット履歴（`v2.0.3..HEAD`、マージコミットを除く / 古い順）

| 日付 | コミット | 内容 |
| --- | --- | --- |
| 2024-12-13 | `03a918f15` | fix |
| 2024-12-13 | `272674ce5` | fix update func |
| 2024-12-14 | `0b9e35cb8` | fix Dockerfile |
| 2024-12-14 | `2bdad62db` | fix |
| 2024-12-14 | `d25eedf85` | fix |
| 2024-12-20 | `80158bcf0` | add fr |
| 2024-12-20 | `5b26fbccb` | add fr |
| 2024-12-21 | `bd4c3437b` | Add French lang resource |
| 2024-12-21 | `0dea87e82` | Modify populate-instance.sh |
| 2025-04-30 | `e0357dd29` | Add redis-sentinel socket timeout value |
| 2025-10-20 | `02378dc92` | fix |
| 2026-01-25 | `464b84a02` | change json to orjson |
| 2026-01-25 | `4262166ea` | check build |
| 2026-01-25 | `8723cf0a5` | improve performance |
| 2026-01-25 | `141b819c6` | improve prepare_edit performance |
| 2026-01-25 | `75ac939e6` | improve prepare_edit performance |
| 2026-01-25 | `c94cb3641` | improve performance |
| 2026-01-25 | `f8207234e` | improve performance serch.html |
| 2026-01-25 | `01fc2a6d4` | improve performance file_details |
| 2026-01-25 | `338842596` | update |
| 2026-01-26 | `c7509336b` | reduce image size |
| 2026-01-26 | `f8ca2e7fc` | Add curl into runtime image |
| 2026-01-26 | `f4b2d449e` | fix node error |
| 2026-01-26 | `60bcd1b0e` | add reporting tool |
| 2026-01-26 | `d8cde8e1c` | add build option |
| 2026-01-28 | `ee4240942` | fix |
| 2026-01-30 | `f78a4684f` | fix |
| 2026-04-23 | `cb8c54760` | fix |
| 2026-04-23 | `54cd882f4` | fix |
| 2026-04-23 | `02f9c0774` | fix |
| 2026-08-04 | `21f6554dc` | fix |

---

## 差分の再現方法

```bash
# 全体の統計
git diff --stat v2.0.3 HEAD

# 翻訳ファイルを除いた差分
git diff v2.0.3 HEAD -- . ':!*messages.po'

# コミット一覧
git log --oneline --no-merges v2.0.3..HEAD
```
