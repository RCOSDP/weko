## 概要 (Summary)
<!-- 変更の目的、背景、および実装内容を簡潔に記載してください -->
* 

## 関連Issue / チケット (Related Issues)
* close #

## 変更タイプ (Type of Change)
- [ ] 🚀 新機能追加 (Feature)
- [ ] 🐛 バグ修正 (Bug Fix)
- [ ] 🔒 セキュリティ修正 (Security Fix)
- [ ] 🚫 機能のクローズ・非公開化・削除 (Feature Deprecation/Disable)
- [ ] ⚠️ 破壊的変更・データ移行を伴う修正 (Breaking Change / Migration)
- [ ] 📚 仕様書・マニュアル・APIリストの更新 (Documentation)

---

## 🤖 0. CI 自動チェック (API Inventory Drift)
<!-- .github/workflows/api-inventory-drift.yml が PR ごとに自動実行する。
     手動で確認する必要はないが、FAIL したら下記に従って対処すること。
     詳細な対処表: tools/api-inventory/ci/README.md -->

PR ごとに実機を起動し、url_map のダンプ・台帳との突き合わせ・変更行の到達可否測定を自動実行する。
結果は PR コメントと Actions の artifact (`api-inventory-drift`) に出る。

- [ ] **CI が PASS している**、または FAIL の各項目に対処済み

### API を追加・変更した場合（必須）

- [ ] **秘密側**の `api_snapshot.json` を更新し、対応する PR を出した
      ```bash
      export WEKO_API_INVENTORY_DIR=/path/to/weko-secret
      ./install.sh
      python3 tools/api-inventory/scripts/snapshot.py --out "$WEKO_API_INVENTORY_DIR/api_snapshot.json"
      ```
      更新しないと CI が落ちる。**このリポジトリは public のため台帳もベースラインも
      同梱していない。** 更新は秘密リポジトリ側の PR になる。
- [ ] **秘密側**の `weko3_api_list_full.tsv` に行を追加・更新し、
      `build_checklist.py` で 24 列版を再生成した（未収載だと reconcile が FAIL する）
- [ ] 台帳・スナップショット・実測結果を**この公開リポジトリにコミットしていない**
      （`git status` に `*.tsv` / `api_snapshot.json` が出ていないこと）

### FAIL したときの対処（要約）

| 検出 | 意味 | 対処 |
|---|---|---|
| G1 / G2 | 新規に認証デコレータが無い / 認証デコレータが削除された | 実装を直す。意図的な公開なら台帳に根拠を書いてベースライン更新 |
| G3 | 認証・認可のコメントアウトが増えた | 原則やり直し |
| G4 | `*_PERMISSION_FACTORY` 等が危険側に変わった | 原則やり直し |
| G5 | ModelView の `can_delete` / `can_export` を有効化 | 意図的なら台帳の `data_op` を更新 |
| G6 / G7 | 属性不明の経路が増えた / 依存更新で経路が増減 | 台帳に行を追加してレビューする |
| **G8** | **未認証で到達する書き込み系** | **原則やり直し** |
| **G9** | **台帳では遮断なのに実測で到達（認可の回帰）** | **原則やり直し** |
| reconcile A–D | 台帳と実機の不一致（未収載・メソッド・app 列） | 台帳を実機に合わせる |

実機に存在しないことが正当な行（プラグイン未登録等）は**秘密側**の `reconcile_allow.json` に
**理由付きで**登録する。理由なしの登録は不可。

> CI の出力は件数のみ。該当した経路名は Actions には出ないので、秘密側の完全版レポートで確認すること
> （このリポジトリは public で、ログ・artifact・PR コメントは誰でも読めるため）。

---

## 🔒 1. セキュリティ & API アクセス制御チェック (必須)

### 認証・認可 (Authentication & Authorization)
- [ ] 新規/変更された Blueprint・View・REST リソースに適切なデコレータ / Permission を設定している
  - 例: `@login_required`, `@pass_record`, `need(...)`, Invenio Access Action
  - `/api/*` では `Permission.require(http_exception=403)` を使うこと。
    `@login_required` は API アプリに `security.login` が無いため 401 ではなく **500** になる
  - <sub>CI: G1 / G2 が自動検出（デコレータの有無・削除）</sub>
- [ ] 状態変更・破壊的メソッド (POST / PUT / PATCH / DELETE) の権限が正しく制限されている
  - <sub>CI: G8 が変更行を未認証で実測</sub>
- [ ] 未ログイン（Anonymous）状態でアクセスした際、意図しないデータ取得・変更が拒絶される
  - <sub>CI: G8 / G9 が変更行を実測。ただし測定は変更行のみで、
    ワークフロー系など未解決プレースホルダの行は skip される</sub>
- [ ] 認可を config の permission factory に委ねている場合、`None` で無効化していない
  - <sub>CI: G4 が `*_PERMISSION_FACTORY` 等を監視</sub>

### 機能クローズ・非公開化の場合 (Feature Disable)
- [ ] UI（画面・ボタン）の非表示だけでなく、**バックエンド API（ルーティング・View）も完全に遮断**されている
- [ ] 無効化状態で直接 API を叩いた場合、`404 Not Found` または `403 Forbidden` が返ることを確認した

---

## 🧪 2. テストコード観点チェック (pytest / Invenio Test Suite)

### 権限・異常系テスト (Negative & Authorization Tests)
- [ ] **未認証アクセス (Anonymous)**: トークン/セッションなしのリクエストで `401 Unauthorized` または `403 Forbidden` / `404 Not Found` が返ることを検証するテストがある
- [ ] **権限不足ユーザー (Forbidden)**: 閲覧権限のみのユーザーが更新/削除 API を叩いた際に `403` になるテストがある
- [ ] **無効化/非公開機能の遮断テスト**: 対象機能が無効化されている場合、エンドポイントが `404` / `403` を返すテストがある

### 境界値・入力バリデーションテスト (Boundary & Validation)
- [ ] 不正なパラメータ（巨大ファイル、異常な MIME タイプ、無効な JSON/XML スキーマ、SQLi/XSS ペイロード等）で適切に `400 Bad Request` / バリデーションエラーが返るテストがある

### データ整合性・トランザクションテスト (Integrity & Rollback)
- [ ] ファイルストレージ（S3/ローカル）書き込み失敗時や DB エラー時に、中途半端なレコードやゴミファイルが残らずロールバックされるテストがある

---

## 🛡️ 3. データ保護 & 破壊的変更防止チェック (Data Safety)

- [ ] **物理削除・上書きの安全性**:
  - ファイル・アイテム・メタデータの完全削除/置換処理に、意図しない一括削除や別レコードへの誤適用リスクがない
  - 論理削除、バージョン管理、バックアップ等のロールバック機構が考慮されている
- [ ] **トランザクション整合性**:
  - DB 更新とストレージ操作がアトミックに管理されている

---

## ⚙️ 4. マイグレーション & システム影響チェック (Invenio / WEKO3 Stack)

### データベース (DB / Alembic)
- [ ] `invenio alembic upgrade`（適用）および `downgrade`（ロールバック）スクリプトを作成・検証した
- [ ] 既存データに対する破壊的変更（カラム削除、型変更、NOT NULL 制約追加等）の移行スクリプト/データパッチを用意した

### 検索インデックス (Elasticsearch / OpenSearch)
- [ ] マッピング定義変更の有無を確認した
- [ ] インデックス再作成（Reindex）やエイリアス切り替え手順を準備・検証した

### 設定 & 非同期処理 (Config / Celery / Cache)
- [ ] `invenio.cfg` / 環境変数のデフォルト値を設定した
- [ ] Celery タスクのシグネチャ変更によるキュー滞留・不整合が発生しない
- [ ] キャッシュ（Redis/Memcached）のパージが必要か確認した

---

## 📚 5. ドキュメント・仕様書更新チェック (weko-document)
<!-- https://github.com/RCOSDP/weko-document への反映確認 -->

- [ ] **API インベントリ**: ツールは本リポジトリの `tools/api-inventory/`、
      **台帳・調査記録は秘密の場所**（public リポジトリには置かない）。
      §0 のチェック項目で対応済みなら、ここは確認のみ。
  - エンドポイントの追加・変更・廃止、メソッド、認証・認可要件、リクエスト/レスポンス仕様を更新した
  - 調査記録（`weko3_api_auth_findings.md`）も秘密側に置く。台帳は二重管理しない
- [ ] **WEKO3 機能仕様書**:
  - 対象機能の仕様追加・変更・クローズ（非公開化）内容を反映した
- [ ] **各種マニュアル (管理者 / 利用者マニュアル)**:
  - 画面導線・操作手順・権限仕様の変更を反映した
- [ ] *更新不要な場合（理由）*: 

---

## 📋 6. 動作検証エビデンス (Verification Evidence)

### テスト実行結果
```bash
pytest tests/ -k <対象モジュール>
# -> PASS
```

### CI の成果物 (artifact: `api-inventory-drift`)
<!-- 手で貼る必要はない。レビュアが見る場所の案内 -->

| ファイル | 内容 |
|---|---|
| `drift.md` | ベースラインとの差分（**件数のみ**） |
| `reconcile.md` | 台帳と実機の突き合わせ（**件数のみ**） |

明細（該当した経路名・実測結果）は公開できないため artifact に含めていない。
秘密側で同じコマンドを `--summary-only` なしで実行して確認する。

### 手動で確認したこと
<!-- CI が測れない範囲（ワークフロー経由の操作、画面導線、外部連携など）を記載 -->
* 
