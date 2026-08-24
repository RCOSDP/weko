# WEKO3 API インベントリ/セキュリティチェックリスト 作成手順

> **【重要】このリポジトリは public。データを置かないこと。**
> 台帳(`weko3_api_list*.tsv`)は「どの経路を・どう叩けば・何が取れるか」と実証結果を
> 持つため、公開領域には置かない。ツールは環境変数で秘密の場所を参照する。
>
> ```bash
> export WEKO_API_INVENTORY_DIR=/path/to/api-inventory-private
> ```
>
> CI の出力は `--summary-only` で件数のみ(Actions のログ・artifact・PR コメントは
> 誰でも読めるため)。置き場所と設置手順は `../ci/README.md` を参照。



> **重要（このディレクトリの配置について）**
> 本ツール群は成果物とともに `weko-document/docs/spec/tools/api-inventory/` に配置されている。
> 解析対象は **WEKO3 本体リポジトリ**(`/home/mhaya/wekov2` 等)なので、実行時は解析対象を明示すること:
> ```bash
> WEKO_ROOT=/home/mhaya/wekov2 python3 scripts/extract_routes.py routes.json
> ```
> 成果物TSV/MDは一つ上の階層(`../weko3_api_list.tsv` 等)にある。


`weko3_api_list.tsv`(24列・チェックリスト版)と `weko3_api_list_full.tsv`(57列・詳細版)を
**バージョンアップのたびに再生成**するための手順とスクリプト一式。

## 全体の考え方

3層で構築する:
1. **静的抽出** — ソースコードから全HTTPエンドポイントと属性を機械抽出(AST)
2. **静的解析** — 認証/認可/データ操作/セキュリティ観点を実装読解＋AST解析で付与
3. **動的検証** — 実際にDocker起動しHTTPリクエストを送って机上の結論を実測で裏取り

「デコレータの有無」だけでなく **実測での到達可否** まで取ることで、
「認可が実際に効いているか」を確定できる(静的解析だけでは分からない)。

---

## Phase 0: 対象リビジョンの確定
```bash
cd /home/mhaya/wekov2
git rev-parse --short HEAD              # 生成元リビジョンを記録
git describe --tags                     # タグ
```

## Phase 1: 静的抽出(エンドポイント発見)

### 1-1. blueprint route を AST 抽出
```bash
python3 tools/api-inventory/extract_routes.py routes.json
```
`@blueprint.route` / `add_url_rule` を全 modules から収集。357件程度。

### 1-2. config駆動 REST エンドポイントを抽出
```bash
python3 tools/api-inventory/extract_endpoints.py endpoints.json
```
`*_REST_ENDPOINTS` config の route 文字列(`/<string:version>/...`)を展開。

### 1-3. 実機の url_map と突合(取りこぼし検出) ★重要
静的抽出は Flask-Admin ModelView(自動生成CRUD 253件)や framework 由来ルートを取りこぼす。
**実際にアプリを起動して url_map をダンプし、差分を追記する**(Phase 3 で起動後):
```bash
# コンテナ内で
docker exec weko-web-1 bash -lc 'source ~/.virtualenvs/invenio/bin/activate; cd /code; \
  invenio shell -c "from flask import current_app; \
  [print(r.endpoint, sorted(r.methods), str(r)) for r in current_app.url_map.iter_rules()]"'
```
これと Phase1-1/1-2 の抽出結果を endpoint 名で照合し、未収載を追記する。
※ @route/@expose だけを見ると ModelView と framework(security.login等)が漏れる。

### URI 算出ルール(重要)
- `invenio_base.blueprints`/`apps` 経由 → `bp.url_prefix` + route
- `invenio_base.api_blueprints`/`api_apps` 経由 → **`/api`** + `bp.url_prefix` + route
- Flask-Admin → `/admin/<endpoint>/<@expose path>`
- 根拠: `invenio_app.factory` が API アプリを DispatcherMiddleware で `/api` にマウント

## Phase 2: 静的解析(観点の付与)

各エンドポイントの実装関数(+呼び出しヘルパ1段)を AST で解析し、列を付与。

| スクリプト | 付与する列 |
|---|---|
| (extract_routes内) | summary/response/exceptions/data操作の一次抽出 |
| `audit_decorators.py` | コメントアウトされた認証/デコレータ不揃い/roles_required無効化 |
| `audit_injection.py` | eval/exec, ZIP-slip, SQLi連結, パストラバーサル |
| `add_cols.py` | csrf_protection, input_validation, audit_logged, triggers_task, resource_limit |
| `add_ssrf_redirect.py` | redirect_target(オープンリダイレクト), ssrf_surface |
| `add_idempotency.py` | idempotency(冪等性) |
| `add_dataop4.py` | data_op_detail(取得/作成/更新/**論理削除/物理削除**) |
| `add_authmech.py` | auth_mechanism(decorator/config-factory/modelview), bola_risk |

### 認証・認可の参照辞書(手動で維持)
- ロール: System/Repository/Community Administrator, Contributor, General
- スコープ: `*/scopes.py`(item:read, file:read, index:*, author:*, oa_status:update等)
- permission factory: `weko-records-ui/permissions.py`(page/file_permission_factory)
- `WEKO_ADMIN_ACCESS_TABLE`(weko-admin/config.py) = Flask-Admin のロール制御

### git情報の付与
```bash
python3 tools/api-inventory/enrich_git.py body.tsv body_enriched.tsv
```
`git log -L <開始>,<終了>:<file>` で**実装関数の行範囲**の最終コミットを取得(ファイル単位より正確)。
`git tag --sort=creatordate --contains <sha>` で導入リリースタグ。

## Phase 3: 動的検証(実測で裏取り) ★静的だけでは不正確

### 3-1. Docker 環境起動
```bash
# 既存の初期化済みボリュームを再利用(プロジェクト名 weko)
docker compose -p weko up -d postgresql pgpool redis elasticsearch rabbitmq
docker compose -p weko up -d web
# egg-info がソースと食い違うと起動失敗 → 全モジュール再生成
docker exec -u root weko-web-1 bash -lc 'source ~/.virtualenvs/invenio/bin/activate; cd /code; \
  for d in modules/weko-* modules/invenio-*; do (cd "$d" && python setup.py egg_info -q); done'
docker compose -p weko restart web
# nginx(80/443競合時は remap して起動、web は uwsgi プロトコルで直叩き不可)
docker compose -p weko -f docker-compose.yml -f nginx-override.yml up -d nginx
# → https://localhost:8443 (Host: weko3.example.org)
```

### 3-2. テストデータ・アカウント準備
- 全ユーザにパスワード設定 → `/api/v1/login` でロール別セッションCookie取得
- 公開/非公開アイテム、グループ・コミュニティ(所有者を変えて)、OAuthトークン(全スコープ)
- ファイル実体(ObjectVersion)を非公開アイテムに添付

### 3-3. 全フラグ付きエンドポイントを実測
```bash
python3 tools/api-inventory/probe.py probe_results.json    # 未認証+各ロールで叩く
```
- プレースホルダ(`<pid_value>`等)を実値に解決
- ★**Cookie失効に注意**: セッションは短時間で失効する。identityごとに直前ログイン＋
  sentinel(既知の200エンドポイント)で鮮度確認してから測定する(`reprobe_own.py`/`asuser.sh`方式)。
  失効Cookieは認証ユーザに大量の偽「遮断」を生む。
- ★**500の切り分け**: `security.login`のBuildErrorなら login_required による遮断、
  それ以外は認可通過後のクラッシュ=到達。ログで個別判定する。

### 3-4. 実測結果を dynamic_verified 列へ
`apply_probe.py`/`final_apply.py` で判定(未認証で到達/ログインのみ/管理者のみ/遮断/検証不能)を付与。
本文取得・DB改変・ファイル露出まで確認できたものは `★確定` とする。

## Phase 4: マージ・整形
```bash
python3 tools/api-inventory/merge.py out/ merged.tsv       # 分割TSVを結合・重複排除・採番
```

## Phase 5: チェックリスト版(24列)を生成
```bash
python3 tools/api-inventory/build_checklist.py             # 57列 full → 24列 に統合
```
派生列を統合: impl(func+file+line), auth(required+method+mechanism),
security_flags(CSRF/BOLA/SSRF等8観点を該当のみ), last_change(commit系4列) 等。

---

## 観点の網羅性(OWASP API Security Top 10 対応)
| OWASP API(2023) | 対応列 |
|---|---|
| API1 BOLA | bola_risk / security_finding:所有者チェック欠落 |
| API2 Broken Auth | auth / dynamic_verified |
| API3 Property-Level Auth | access_variance |
| API4 Resource Consumption | security_flags:RESLIMIT |
| API5 Function-Level Auth | roles_scope / security_finding:権限過小 |
| API6 Business Flow | security_flags:IDEMP |
| API7 SSRF | security_flags:SSRF |
| API8 Misconfiguration | security_flags:CSRF / config_deps |
| API9 Inventory Mgmt | deprecated / api_version / test_file |
| API10 Unsafe Consumption | side_effects |

## 差分レビューの勘所(バージョンアップ時)
1. Phase1で新url_mapを取り、前回の `no`/`uri` と**差分**を取る(新規/削除エンドポイント)
2. 新規・変更行だけ Phase2-3 を回す(全部再測定は不要)
3. `auth`が`不要`(公開)に変わった行、`security_flags`に★が付いた行を重点確認
4. `data_op`が`物理削除`(不可逆)の新規エンドポイントは特に注意

## 既知の限界
- SSRF検出は関数本体＋1段ヘルパまで。route→Celery→utils の間接SSRFは triggers_task で追跡。
- ModelView 253件は代表実測。全個別測定ではない。
- 動的検証はテストデータ依存。完全な end-to-end(ワークフロー経由の正規deposit)は一部のみ。

---

# Phase 6: 差分検知(バージョンアップ時の機械的チェック)

Phase 1-5 が「作る」手順なのに対し、Phase 6 は **「変わったことを検知する」** 手順。
CI に組み込んで、API の追加・仕様変更を人手のレビュー前に機械で拾う。

## なぜ実機 url_map が正なのか

**ブループリント(`@bp.route`)を見ても半分しか分からない。** 実測値:

```
AST抽出(@bp.route + add_url_rule) : 357ルート / 77ブループリント
実機url_map(static除く)           : 903ルート (UI 724 + API 248)
ASTで説明できない                 : 472件 (52%)
```

漏れの内訳:

| 種別 | 件数 | 理由 |
|---|---:|---|
| Flask-Admin ModelView 自動生成 | 223 | `index_view`/`create_view`/`edit_view`/`delete_view`/`details_view`/`action_view`/`ajax_lookup`/`ajax_update`。ModelView を1つ定義すると8ルート生える |
| `@expose`(Flask-Admin BaseView) | 約100 | `@bp.route` ではないので route 抽出の対象外。リポジトリ内に `@expose` 205箇所 |
| config駆動 REST(`*_REST_ENDPOINTS`) | 約30 | route 文字列が config の dict の中 |
| `modules/` に無い pip パッケージ | — | `extract_routes.py` は `ROOT/modules` しか walk しない |
| route が式の `add_url_rule` | — | 357件中75件が add_url_rule、`options.pop('rdc_route')` 等は literal_eval 不可 |
| framework 由来 | — | flask_security / flask-oauthlib(9) / invenio_i18n |

したがって **役割を分ける**:

- **経路の集合(何が存在するか)** → 実機 url_map ダンプが唯一の正
- **各経路の属性(誰が叩けるか)** → AST + ソース読解

## 6-1. スナップショット生成

```bash
python3 scripts/snapshot.py --out api_snapshot.json --container weko-web-1
# → endpoints=860 (AST結合=495 / 属性不明=365) modelviews=30 config=33
```

やっていること:

1. 実機 url_map を **UIアプリと APIアプリの両方**ダンプ
   (APIアプリは `current_app.wsgi_app.mounts['/api']` を辿らないと出てこない)
2. ModelView の権限属性(`can_delete`/`can_export`/`column_export_list`)を併せて取得
   — url_map には現れないが、`can_export` が有効化されると DB 全件 CSV 出力面が開く
3. AST で全 def を索引化し、`(module, funcname)` で url_map に左結合してデコレータを付与
4. **結合できなかったものは `attrs: "unknown"` として残す**(黙って落とさない)

出力の構造:

```jsonc
{
  "meta":       { "revision": "d2fdc0e3b", "tag": "v2.0.3", "profile": "default", "counts": {...} },
  "endpoints":  { "api:weko_admin.get_curr_api_cert": {
                    "rules": ["/admin/get_curr_api_cert/<string:api_code>"],
                    "methods": ["GET"],
                    "auth_decorators": [],          // ← 認証デコレータ無し
                    "auth_hash": "da39a3ee5e6b",
                    "body_hash": "…" } },
  "modelviews": { "actionroles": { "can_delete": true, "can_export": false, … } },
  "config":     { "…/config.py::RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY": {…} },
  "commented_auth": { "invenio_iiif.handlers": [{ "line": 39, "text": "#g.obj = ObjectResource.get_object(…)" }] }
}
```

キーは **`<app>:<endpoint>`**。URL ではなく Flask の endpoint 名にすることで、
URL だけ変わった場合を「新規＋削除」ではなく `RULE_CHANGED` と正しく分類できる。
1エンドポイントが複数ルールを持つ場合(末尾スラッシュ違い等・36件)は `rules` 配列で保持する。

### プロファイル

条件付きで blueprint を登録している箇所が実在する
(`weko-notifications/ext.py:41`, `invenio-accounts/ext.py:168` 等)ため、
**1プロファイルのダンプでは他の設定で有効になる経路を見落とす。**

```bash
python3 scripts/snapshot.py --out api_snapshot.json      --profile default
python3 scripts/snapshot.py --out api_snapshot.full.json --profile full-features
```

比較は同一プロファイル同士で行う(異なる場合は差分レポートが警告する)。

### 外部ライブラリが登録する経路(動的抽出でしか見えないもの)

実機ダンプの最大の効き目はここ。**860経路のうち 291件(34%)は `modules/` に存在しない
外部ライブラリが登録している。**

| provider | 経路数 | 例 |
|---|---:|---|
| Flask-Admin==1.5.4 | 254 | `/admin/actionroles/action/` |
| invenio-records-ui==1.0.0 | 20 | `/item/edit/<pid_value>` |
| invenio-oauthclient==1.0.0 | 5 | `/oauth/authorized/<remote_app>/` |
| Flask-Security==3.0.0 | 4 | `/confirm/<token>` |
| **Flask-IIIF==0.6.1** | **3** | `/iiif/<version>/<uuid>/<region>/<size>/<rotation>/<quality>.<format>` |
| invenio-i18n / invenio-jsonschemas / invenio-csl-rest | 5 | `/lang/`, `/schema/<path>`, `/csl/styles` |

**no.34(非公開ファイルの実体を未認証で取得できることを実証した経路)は Flask-IIIF が
登録している。** リポジトリのソースをいくら走査しても出てこない。動的抽出が必須である
最も強い実例。

各エンドポイントには `provider: "<配布物>==<版>"` を付与し、`meta.packages` に
インストール済み302パッケージの版を丸ごと保持する。これにより
**「依存を上げたら経路が増えた」を機械的に帰着できる**(ゲート G7)。

```jsonc
"api:iiifimageapi": {
  "rules": ["/iiif/<string:version>/<string:uuid>/<string:region>/…"],
  "view": "flask_iiif.restful.iiifimageapi",
  "provider": "Flask-IIIF==0.6.1",
  "attrs": "unknown", "reason": "framework 由来"
}
```

## 6-2. 差分とゲート

```bash
python3 scripts/diff_snapshot.py OLD.json NEW.json --out drift.md --gate
# FAIL があれば exit 1
```

分類:

| 分類 | 意味 |
|---|---|
| `ADDED` / `REMOVED` | 経路の増減 → **インベントリへの追加/削除が必要** |
| `RULE_CHANGED` | endpoint 同一で URL が変化 |
| `METHODS_CHANGED` | HTTPメソッドの増減 |
| `AUTH_CHANGED` | 認証・認可デコレータの変化(最優先) |
| `IMPL_CHANGED` | デコレータ据置きで実装本体のみ変化 |
| `ATTRS_UNKNOWN_NEW` | 経路はあるが静的解析で属性が取れない新規 |

`IMPL_CHANGED` は「デコレータは同じだが中身が変わった」を拾う。
no.480(`page_permission_factory` が `flg='Edit'` を無視)のような
**ロジック内認可**の変化はここでしか捕まらない。

### ゲート(いずれも過去の実際の穴から導出)

| ID | 条件 | 由来 |
|---|---|---|
| G1 | 新規エンドポイントに認証系デコレータが無い | no.200/201/389/390/393 |
| G2 | 認証系デコレータが削除された | — |
| G3 | 認証/認可デコレータのコメントアウトが増えた | **no.34(IIIF `protect_api`)** |
| G4 | 認可を左右する config が危険側に変わった | **no.10/269/271/519/520(`factory=None`)** |
| G5 | ModelView の `can_delete`/`can_export` が False→True | CSV export 22件 |
| G6 | 属性不明のまま追加された経路がある | 手動レビュー必須 |
| G7 | 依存パッケージの更新で外部ライブラリ由来の経路が増減した | **no.34(Flask-IIIF)** |
| W1 | ModelView が追加された | 1つにつき自動生成8ルート(削除系を含む) |
| W2 | 実装本体が変化 | data_op / 情報露出の再確認 |
| W6 | 依存パッケージの版が変化した | 経路据置きでも既存経路の挙動が変わりうる |

G3 は **エンドポイントに紐付かないコメントアウトも検知する**。
no.34 の `protect_api` はビュー関数ではなくハンドラフックなので、
エンドポイント単位の検査だけでは捕まらない。

## 6-3. 再レビュー対象行の絞り込み

```bash
python3 scripts/changed_rows.py v2.0.2 v2.0.3 --out rerun_nos.txt
# v2.0.2..v2.0.3
#   変更ファイル(modules/*.py): 9
#   再レビュー対象行: 1 / 全918行
#   no=21    GET  /admin/location/   modules/invenio-files-rest/invenio_files_rest/admin.py:178
```

`git diff -U0` の変更行を AST で def/class 範囲に広げ、
インベントリの `impl_file`/`impl_line` と突き合わせる(`enrich_git.py` と同じ関数単位の考え方)。
918行すべてを Phase2-3 に回す必要がなくなる。

`views.py`/`rest.py`/`admin.py`/`ext.py`/`config.py` が変更されたのに
インベントリに未登録のファイルは「新規エンドポイントの可能性」として別途警告する。

## 6-4. CI への組み込み

**設置手順は `ci/README.md`**(移設するファイル・導入順序・ベースライン更新ルール・
ゲートFAIL時の対処・プロファイル・トラブルシュート)。ワークフロー本体は
`ci/api-inventory-drift.yml`。

CI が触るファイルは WEKO3 リポジトリの `tools/api-inventory/` に移設して
**単一リポジトリで完結**させる。別リポジトリの checkout もトークンも不要。

WEKO3 側には `ui-tests.yml` が既にあり、**push/PR ごとに `install.sh` で
WEKO スタック全体を起動している**。実機 url_map を取る土台は既に存在するので、
ジョブを1つ足すだけでよい。

**`api_snapshot.json` を git 管理するのが肝。**
API を変えた PR は必ずスナップショット更新を伴い、**差分がコードレビューに乗る**。
人手の運用ルールではなく、diff が目に入る仕組みになる。

## 6-5. さらに強くしたい場合

**アクセスログからの実在経路収集。** nginx のアクセスログから `(method, パステンプレート)`
の distinct を取り、インベントリと突き合わせる。プラグインや動的登録で
**コードにも url_map スナップショットにも出ない経路**が本番で叩かれていないかの最終確認になる。
(インベントリに「経路なし(プラグイン未登録)」と記録した4件は、逆に本番では有効な可能性がある)

## 6-6. インベントリとの突き合わせ(reconcile)

スナップショットは「実機に何があるか」、インベントリTSVは「調査済みの台帳」。
**この2つがズレていないかを機械的に検証する**のが `reconcile.py`。

```bash
python3 scripts/reconcile.py --gate --out reconcile_report.md
# A=0 B=0 C=0 D=0 B'(既知)=11   → exit 0
```

| 検出 | 意味 |
|---|---|
| A. インベントリ未収載 | 実機にあるが台帳に無い = **抽出漏れ** |
| B. 実機に無いインベントリ行 | 台帳にあるが url_map に無い(未登録/条件付き) |
| C. メソッド不一致 | 同一URIでHTTPメソッドが食い違う |
| D. app列の不一致 | UI/API どちらに登録されているかの記載誤り |

B のうち正当な理由があるもの(プラグイン未登録・config で無効・動的登録のプレースホルダ)は
`reconcile_allow.json` に**理由付きで**登録して既知扱いにする。理由なしの登録は禁止。

### URI の正規化規則(ここを間違えると偽の差分が大量に出る)

- **スナップショット**: APIアプリのルールには `/api` を前置する。
  APIアプリは DispatcherMiddleware で `/api` にマウントされるため、その url_map 側には prefix が出ない。
- **インベントリ**: `uri` セルの `;` 区切りを展開する。`app=両方` の行は `/api` 側も展開する。
- **末尾スラッシュ**は除去して比較する。
- **HEAD / OPTIONS** は比較対象外。werkzeug が GET ルールに自動付与するため、
  実装が HEAD を意識しているかを区別できない。

### メソッドは必ずルール単位で比較する

同じ `view_func` を `add_url_rule` で複数回登録すると **endpoint 名が同一になる**。
このとき endpoint 単位でメソッドを union すると、実際には POST しか受けないルールが
`DELETE,GET,POST,PUT` を受けるように見えてしまう(初版で偽の不一致17件を出した)。

```python
# weko-index-tree/rest.py:217-232 — 同じ view_func `ima` を別ルール・別メソッドで登録
blueprint.add_url_rule(options.get('api_create_index'), view_func=ima, methods=['POST'])
blueprint.add_url_rule(options.get('api_update_index'), view_func=ima, methods=['PUT'])
blueprint.add_url_rule(options.get('api_delete_index'), view_func=ima, methods=['DELETE'])
```

このため `snapshot.py` は `routes: [{rule, methods}, …]` とルール単位で保持する
(`rules` / `methods` は概観用の派生値)。

### CI での位置づけ

`diff_snapshot.py`(前回スナップショットとの差分)と `reconcile.py`(台帳との差分)は目的が違う。
両方を回す:

- `diff_snapshot.py` … **バージョン間**で何が変わったか
- `reconcile.py` … **今の実機と台帳**が一致しているか(＝調査漏れが無いか)

---

# Phase 7: 到達可否の実測を CI に載せる

Phase 6 は**構造の変化**(経路・デコレータ・config)を検知するが、
`dynamic_verified`(誰が到達できるか)は更新しない。新規APIが増えても
「未認証で本当に到達するか」は測られず、認証を追加して直しても
「修正が効いているか」を確認できない。Phase 7 がそこを埋める。

## 7-0. なぜフィクスチャが要るか

`install.sh` は `scripts/populate-instance.sh:179` の

```bash
#${INVENIO_WEB_INSTANCE} demo init      ← コメントアウトされている
```

によって **レコードを1件も作らない**。CI 環境で入るのは次のとおり。

| 項目 | CI環境 |
|---|---|
| ロール4種 + action 付与 / ユーザ5人 | あり |
| アイテムタイプ / インデックスツリー / ワークフロー定義 / ファイルロケーション | あり |
| **recid / depid のレコード** | **0件** |
| **ファイル実体(ObjectVersion)** | **なし** |
| **公開/非公開の区別、他人所有のリソース** | **なし** |
| **OAuthトークン / Community / Group** | **なし** |

この状態では認可判定を通せず、到達可否を測れない。

## 7-1. `fixtures.py` — 最小テストコーパスの投入

```bash
python3 scripts/fixtures.py --out fixtures.json
# users=5 records=3 index=900001 file=あり token=あり community=あり group=あり
```

投入するもの:

- 既知パスワード(`Passw0rd!123`)に揃えたユーザ5人
- 公開インデックス(`900001`)
- レコード3件 — いずれもバケット付き
  - `public` (recid 900001, publish_status=0, owner=Contributor)
  - `private` (recid 900002, publish_status=1, owner=Contributor, **ファイル実体付き**)
  - `other_owner` (recid 900003, publish_status=1, owner=General, **ファイル実体付き**)
- 全19スコープの個人アクセストークン
- Community / Group

**冪等かつ自己修復。** 既存があれば再利用しつつ `path` / `owner` / `publish_status` を
毎回入れ直す。先行ステップ(インデックス作成など)が失敗した回に作られたレコードは
`path` が空のままになり `check_index_permissions` を通らないため、再実行で直るようにしてある。

生成物 `fixtures.json` は **`.gitignore` 済み**。OAuthアクセストークンと平文パスワードを
含むのでリポジトリには入れない。CI では毎回生成する。

### フィクスチャで再現できること(検証済み)

```
未認証 IIIF info.json                    → 200          (no.925)
未認証 IIIF 画像本体                      → 200 / 70バイト (no.34)
未認証 files-rest 直                      → 404          (露出がIIIF経路限定であることも再現)
Contributor → 他人所有のファイル           → 200 / 70バイト (no.25 の BOLA)
未認証 POST /api/deposits/items          → 200          (no.920)
```

### 限界(正直に)

合成レコードのためアイテムタイプ固有フィールドを持たない。詳細画面の
レンダリングは 404/500 になりうる。**ワークフロー経由の正規 deposit は作っていない。**
`probe_ci.py` はこれを「判定不能」として明示するので、誤った安心にはならないが、
レンダリングまで通す必要がある行は測れない。ワークフローの activity も未整備のため
no.601-636 は未解決プレースホルダとして skip される。

## 7-2. `probe_ci.py` — フィクスチャ駆動の実測

```bash
python3 scripts/probe_ci.py --only rerun_nos.txt --allow-writes --gate --out probe.json
```

`probe.py`(参考実装)はセッション固有のUUIDとパスがハードコードされている。
`probe_ci.py` は `fixtures.json` からプレースホルダを解決するため、まっさらな環境で動く。

- 測定 identity: anon / general / contributor / comadmin / repoadmin / sysadmin
- 測定対象は `--only` で渡した `no` に限定する(全926行を毎PR測ると時間がかかりすぎる)
- **安全装置**: GET/HEAD 以外は既定でスキップ。`--allow-writes` を明示したときだけ測る
  (CI のコンテナは使い捨てなので許可してよいが、実環境では既定のままにすること)

### 判定の切り分け

| 応答 | 判定 | 根拠 |
|---|---|---|
| 401 / 403 | 遮断 | |
| 3xx でログイン画面へ | 遮断 | |
| **3xx でログイン画面以外** | **到達** | no.480 は未認証 302 で `publish_status` が実際に書き換わる。302を一律「遮断」にすると取りこぼす |
| 500 (本文に `security.login` / `BuildError`) | 遮断 | APIアプリの `login_required` は BuildError で 500 になる |
| 500 (それ以外) | 到達 | 認可通過後のクラッシュ |
| 404 | 判定不能 | `hidden=True` の権限NGか、対象が無いだけか区別できない |
| 2xx / 400 / 405 / 415 | 到達 | |

### アイテムIDは公開/非公開の両方で測る

`<pid_value>` 等は `public` と `private` の**両方**に解決して2回測る。
どちらを入れるかで結論が変わるため(no.480 は非公開だとログインへ転送されるが、
公開アイテムでは未認証で書き換えが成立することを実証済み)。

`<string:version>` は文脈依存で、IIIF なら `v2`、WEKO の REST API なら `v1` に解決する。

## 7-3. ゲート

| ID | 条件 |
|---|---|
| **G8** | 未認証で到達し、かつ `data_op` が作成/更新/削除 |
| **G9** | 台帳が「遮断」なのに実測で「到達」(回帰) |

CI では `changed_rows.py` が出す `rerun_nos.txt`(変更が触れた行)だけを測る。
全件測定はリリース前の棚卸しで行う。

---

# Phase 8: 対応優先度の付与

```bash
python3 scripts/prioritize.py          # 台帳に priority / priority_reason を付与
python3 scripts/build_checklist.py     # 24列版(=26列)へ引き継ぐ
```

`security_finding` / `security_flags` / `dynamic_verified` / `data_op` / `method` /
`auth` から、対応優先度を機械判定して台帳に書き戻す。判定基準・凡例・限界は
秘密側の `weko3_api_list_README.md`「priority の凡例」に記載。

**この判定は着手順を決めるための粗い仕分けであって、リスク評価の代替ではない。**
`method` ベースで判定するため副作用のある GET を落とすこと、`data_op` の文字列で
「データ破壊」を判定するため設計上の自己クリーンアップも拾うこと、読み取り系は
露出内容の重大さ(認証情報か公開情報か)を見ていないこと──いずれも目視補正が要る。

