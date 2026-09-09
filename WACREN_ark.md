# ARK付与機能 調査メモ

対象ブランチ: `feature/nii_WACREN_pre`
調査日: 2026-08-04

ARK識別子の自動付与機能について、実装箇所・ON/OFF制御の網羅性を調査し、
防御的な実装への修正を行った記録。

---

## 1. 全体構成

ARK付与は既存のCNRI(Handle)付与と同じ枠組みに乗っており、
**設定値の定義は `weko-handle`、実処理は `weko-workflow`** に分かれている。

| 役割 | 場所 |
|---|---|
| 設定値の定義・読み込み | `modules/weko-handle/weko_handle/config.py`, `ext.py` |
| 払い出し処理本体 | `modules/weko-workflow/weko_workflow/utils.py` |
| ワークフローからの呼び出し | `modules/weko-workflow/weko_workflow/views.py` |
| 一括インポートからの呼び出し | `modules/weko-search-ui/weko_search_ui/utils.py` |
| 付与後の参照 | `weko-deposit`, `weko-records-ui`, `invenio-oaiserver` |

---

## 2. 設定 (`weko-handle/weko_handle/config.py`)

| 設定キー | 既定値 | 意味 |
|---|---|---|
| `WEKO_HANDLE_ALLOW_REGISTER_ARK` | `False` | ARK付与のON/OFF |
| `WEKO_HANDLE_ARK_LOGIN_URL` | `None` | ARKサーバの認証エンドポイント |
| `WEKO_HANDLE_ARK_LOGIN_USER` | `None` | 認証ユーザ |
| `WEKO_HANDLE_ARK_LOGIN_PASSWD` | `None` | 認証パスワード |
| `WEKO_HANDLE_ARK_MINT_URL` | `None` | ARK払い出し(mint)エンドポイント |
| `WEKO_HANDLE_ARK_NAAN` | `None` | 払い出しに使うNAAN |
| `WEKO_HANDLE_ARK_SHOULDER` | `None` | 払い出しに使うshoulder |
| `WEKO_HANDLE_ARK_TIMEOUT` | `30` | ARKサーバへの1リクエストあたりのタイムアウト秒 |
| `WEKO_HANDLE_ARK_API_KEY` | `None` | API key。設定するとログイン手順を省略する |
| `WEKO_HANDLE_ARK_API_KEY_HEADER` | `'Authorization'` | API key を載せるヘッダ名 |
| `WEKO_HANDLE_ARK_API_KEY_PREFIX` | `'Bearer '` | API key の前置詞。`''` で生のキーを送る |

`weko_handle/ext.py` の `init_config` が `dir(config)` をループして
`WEKO_HANDLE_` 接頭辞のキーを一括で `app.config.setdefault` する。
entry point (`invenio_base.apps` / `invenio_base.api_apps`) にも登録済み。

**管理画面のUIは無い。** インスタンス設定ファイル（`invenio.cfg` 等）で上書きする方式。
リポジトリ内に実値の定義は無く、既定値はすべて `None` / `False`。

---

## 3. 払い出し処理 (`weko-workflow/weko_workflow/utils.py`)

### 処理の流れ

1. `WEKO_HANDLE_ALLOW_REGISTER_ARK` と必須設定をチェック
   （`MINT_URL` / `NAAN` / `SHOULDER` は常に必須。`API_KEY` が無いときだけ
   `LOGIN_URL` / `LOGIN_USER` / `LOGIN_PASSWD` も必須）
2. 既に `record.pid_ark` があれば何もしない（二重付与防止）
3. 公開URL `<host>/records/<deposit_id>` を組み立て
4. 認証ヘッダを用意する
   - **API key方式**: `<API_KEY_HEADER>: <API_KEY_PREFIX><API_KEY>` を組むだけ（HTTP不要）
   - **パスワード方式**: `LOGIN_URL` に `{"query": user, "password": passwd}` を
     POST → JSONの `token` を取得し `Authorization: Bearer <token>` にする
5. `MINT_URL` に上記ヘッダ付きで `{"naan", "shoulder", "url"}` をPOST
6. レスポンスの `data.ark` を `IdentifierHandle.register_pidstore('ark', ...)` で
   PIDStoreに `pid_type='ark'`, `status=REGISTERED` として登録

対象UUIDは `get_record_without_version` で得た**バージョン無しPID**のUUID。

### 関数構成（修正後）

| 関数 | 役割 |
|---|---|
| `is_ark_registration_allowed()` | フラグ + 認証方式に応じた必須設定の判定。欠落キーをログ出力 |
| `_ark_auth_header()` | mint用の認証ヘッダ組み立て。API key優先、無ければログイン |
| `mint_ark(record_url)` | ARKサーバへの払い出し。失敗時は `None` |
| `_register_ark_pidstore(item_uuid, ark)` | PIDStoreへの登録 |
| `register_ark(activity_id)` | ワークフロー経由のエントリポイント |
| `register_ark_by_item_id(deposit_id, item_uuid, url_root)` | インポート経由のエントリポイント。払い出したARK文字列を返す |

`register_ark` は `request.url` から公開URLを組むためリクエストコンテキストが必要。
`register_ark_by_item_id` は `url_root` を引数で受け取るため不要。

---

## 4. 呼び出し箇所

ARKを払い出す経路は**全体で2箇所のみ**。両方ともフラグでガードされている。

| 呼び出し元 | 条件 |
|---|---|
| `weko_workflow/views.py` の `next_action` | アクションが `item_login` / `item_login_application` かつ `record.pid_ark is None` かつフラグON |
| `weko_search_ui/utils.py` の一括インポート | フラグON（`if not is_gakuninrdm:` ブロック内）→ `register_item_ark(item)` |

REST API・CLI・index-tree・communities からARKを叩く経路は存在しない。
（`weko_workflow/cli.py` はアクションのマスタ投入、`weko_workflow/api.py` は
画面遷移URLの組み立てで、いずれも登録処理ではない）

---

## 5. 付与後のARKの参照先

| 用途 | 場所 |
|---|---|
| レコードからの取得 | `weko_deposit/api.py` の `WekoRecord.pid_ark` プロパティ（バージョン無しrecidのUUIDに紐づく `REGISTERED` な `ark` PIDを最新順で1件） |
| パーマリンク表示 | `weko_records_ui/utils.py` の `get_record_permalink` — `doi → cnri → ark` の優先順でフォールバック |
| OAI-PMH出力 | `invenio_oaiserver/response.py` — `systemidt` に `identifier_type="ARK"` として出力 |

アイテム詳細画面のテンプレートにARK専用の表示は無い（パーマリンク経由のみ）。

---

## 6. ON/OFF制御の検証結果

### OFF側: 問題なし

`register_ark()` / `register_ark_by_item_id()` の呼び出し元は上記2箇所のみで、
両方ともフラグでガードされている。設定の既定値も `False` で確実に入る。
**フラグを立てなければARKが払い出されることはない。**

### ON側: CNRIと比べて抜けがある

1. **フラグがTrueでも設定不足で無言スキップされうる**（→ 今回修正）
   必須6項目のうち1つでも欠けると何も起きず、ログにも痕跡が残らなかった。
2. **インポート時のARK列バリデーションが存在しない**（未対応）
   CNRIには `handle_check_cnri` があるが、ARK版の検査関数は無い。
3. **手動ARK指定が未実装**（未対応）
   `register_item_ark` の `is_change_identifier` 分岐は
   `# TODO: implement manual register ark` のまま。TSVでARKを明示指定しても
   検証も登録もされない。→ 今回、警告ログだけは出すようにした。
4. **インデックス・コミュニティにはARKの概念がない**（未対応）
   `weko_index_tree/api.py` と `invenio_communities/admin.py` はCNRIのみ。
   過去に `WEKO_INDEX_USE_ARK_IDENTIFIER` という作業履歴があるが現ブランチには無い。
5. **GakuNin RDM経由のインポートは対象外**（CNRIと同じ挙動なので意図的と思われる）

---

## 7. 実施した修正（防御的実装）

### `modules/weko-workflow/weko_workflow/utils.py`

- **`is_ark_registration_allowed()` を新設** — フラグと必須設定6項目を一箇所で判定。
  フラグONで設定が欠けている場合は**欠落キー名を列挙して `logger.error`** を出す。
- **両エントリポイントの冒頭にガードを追加** — 呼び出し元のガード漏れがあっても
  ARKは払い出されない（呼び出し元側の既存ガードもそのまま残置）。
- **`mint_ark(record_url)` に払い出し処理を集約** — 重複していた2関数分のHTTP処理を1本化。
  - `timeout` 指定（ARKサーバ無応答によるワーカーのハングを防止）
  - login / mint それぞれの失敗時にステータスコードとレスポンス本文をログ出力
  - `token` 無し・`data.ark` 無しを個別にエラーログ
  - 全体を `try/except` で保護し、通信例外やJSONパース失敗でも
    **アイテム登録自体は落とさない**
  - 未使用の `import pprint` を削除、`import requests` をモジュール先頭へ移動
- **`_register_ark_pidstore()` を新設** — `IdentifierHandle` の生成をmint成功後に遅延
  （従来はmint結果を見る前に生成していた）。PID登録の成否をログに残す。
- **`register_ark()` 個別の防御**
  - activity・レコード取得を `try/except` で保護（`PIDDoesNotExistError` 等で500になっていた）
  - `activity.item_id` が無い場合、`record.pid_parent` が None の場合を
    エラーログ付きで早期return（後者は従来 `AttributeError`）
  - docstring と debugログの文言が "HDL" / "register_hdl" のままだったのをARKに修正

### `modules/weko-search-ui/weko_search_ui/utils.py`

- `register_item_ark()` のレコード取得を `try/except` で保護、`pid` が None のケースを早期return
- 未実装の手動ARK指定を `logger.debug` で黙殺していたのを
  **`logger.warning` で「指定されたARKは無視された」と明示**

### `modules/weko-handle/weko_handle/config.py`

- `WEKO_HANDLE_ARK_TIMEOUT = 30` を追加

### 確認事項

- 3ファイルとも `py_compile` 成功
  （search-ui に出る `SyntaxWarning` は 1568行目等の既存箇所で、今回の変更とは無関係）
- `register_ark*` を参照するテストは存在しないため、テストの修正は不要だった
- 呼び出し規約（引数・戻り値）は変更していない

---

## 7-2. API key 認証への対応（2026-09-09 追記）

ARKサーバが `Authorization: Bearer` と `X-API-Key` の両方を受け付けるため、
毎回のログイン往復を省ける**API key方式**を追加した。従来のパスワード方式は
そのまま残してあり、`WEKO_HANDLE_ARK_API_KEY` の有無だけで切り替わる。

### `modules/weko-handle/weko_handle/config.py`

- `WEKO_HANDLE_ARK_API_KEY` / `_HEADER` / `_PREFIX` の3キーを追加（§2の表を参照）。
  `ext.py` は `WEKO_HANDLE_` 接頭辞を総なめするので登録側の変更は不要。

### `modules/weko-workflow/weko_workflow/utils.py`

- **`_ark_auth_header()` を新設** — mint用の認証ヘッダを一箇所で組み立てる。
  API keyがあれば `<HEADER>: <PREFIX><KEY>` を返し（HTTPリクエスト無し）、
  無ければ従来のログインPOSTでトークンを取得して `Authorization: Bearer` を返す。
  失敗時は `None`。キーが数値でも `format` で文字列化される
  （`INVENIO_` 環境変数は `ast.literal_eval` を通るため数字だけだとintになる）。
- **`mint_ark()` からログイン処理を分離** — `_ark_auth_header()` を呼ぶだけにした。
  `try/except` の内側で呼ぶので、ログイン時の通信例外も従来どおり握りつぶす。
- **`is_ark_registration_allowed()` の必須項目を認証方式で分岐** —
  `MINT_URL` / `NAAN` / `SHOULDER` は常に必須、`LOGIN_*` の3項目は
  API key未設定のときだけ必須。API key方式で `LOGIN_*` を空にしても
  「未設定」エラーで弾かれない。

### 設定例（`invenio.cfg`）

```python
WEKO_HANDLE_ALLOW_REGISTER_ARK = True
WEKO_HANDLE_ARK_MINT_URL = 'https://ark.example.org/api/mint'
WEKO_HANDLE_ARK_NAAN = '12345'
WEKO_HANDLE_ARK_SHOULDER = 'x1'
WEKO_HANDLE_ARK_API_KEY = 'xxxxxxxxxxxx'
# X-API-Key で送る場合のみ以下を追加
# WEKO_HANDLE_ARK_API_KEY_HEADER = 'X-API-Key'
# WEKO_HANDLE_ARK_API_KEY_PREFIX = ''
```

`WEKO_HANDLE_ARK_LOGIN_*` は残しておけば、API keyを外すだけで
パスワード方式にフォールバックできる。

### 確認事項

- 2ファイルとも `py_compile` 成功、変更行は79桁以内
- 実ソースの関数定義を抜き出し、`current_app` / `requests` を差し替えて
  7ケース（パスワード方式・Bearer・X-API-Key・数値キー・設定不足2種・フラグOFF）
  を確認済み。リポジトリ内の自動テストは未追加（§8の残課題のまま）
- 呼び出し規約（`mint_ark` の引数・戻り値）は変更していない

---

## 8. 残課題

- [ ] `mint_ark` / `is_ark_registration_allowed` の単体テスト追加（モック使用）
- [ ] インポート時のARK列バリデーション（CNRIの `handle_check_cnri` 相当）
- [ ] 手動ARK指定の実装（`register_item_ark` の `is_change_identifier` 分岐）
- [ ] CNRI側（`register_hdl` 系）にも同様の防御的修正を適用するか検討
- [ ] レコードURL変更時にARKのターゲットURLを更新する処理（現状なし）
