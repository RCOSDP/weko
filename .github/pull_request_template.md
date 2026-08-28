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

PR ごとに WEKO3 コンテナを起動し、`url_map` のダンプ・台帳との突き合わせ・変更行の
到達可否測定を自動実行する。結果は PR コメントと Actions の artifact
(`api-inventory-summary`) に出る。

**このリポジトリは public のため、台帳もベースラインも同梱していない。**
実データは**プライベートリポジトリ `RCOSDP/weko-secret`** にあり、CI は Secret 経由で取得する。
以降この文書では、そこを単に**プライベートリポジトリ**と呼ぶ。

台帳はブランチごとに内容が違うため、CI は **weko 側と同名のブランチ**を
プライベートリポジトリから探して使う（head → base → 既定ブランチ の順）。
採用されたブランチ名は PR コメントの冒頭に出るので、**件数を読む前にそこを見ること**。
対応ブランチが無い場合は既定ブランチと比較され、コメント冒頭に警告が出る。
その件数は当てにならないので、PASS でも「確認済み」と読まないこと。
詳細: `tools/api-inventory/ci/README.md` §3a

- [ ] **CI が PASS している**、または FAIL の各項目に対処済み
      <sub>Secret (`API_INVENTORY_REPO` / `API_INVENTORY_SSH_KEY`) が未設定のリポジトリ、
      および fork からの PR では、このジョブは何もせずスキップされる。</sub>

### API を追加・変更した場合（必須）

- [ ] **プライベートリポジトリ側の作業ブランチを、この PR のブランチと同名で切った**
      <sub>この PR が `fix/issue62569` → `develop_v2.0.4` なら、プライベート側も
      `fix/issue62569` → `develop_v2.0.4`。同名にしておけば台帳 PR が未マージでも
      CI がそれを見るので、2つの PR のマージ順を気にしなくてよい。</sub>
- [ ] **プライベートリポジトリ**の `api_snapshot.json` を更新し、対応する PR を出した
      ```bash
      export WEKO_API_INVENTORY_DIR=/path/to/weko-secret
      ./install.sh
      python3 tools/api-inventory/scripts/snapshot.py --out "$WEKO_API_INVENTORY_DIR/api_snapshot.json"
      ```
      更新しないと CI が落ちる。公開リポジトリのコード変更とは**別の PR**になる。
- [ ] **プライベートリポジトリ**の `weko3_api_list_full.tsv` に行を追加・更新し、
      `build_checklist.py` で 24 列版を再生成した（未収載だと reconcile が FAIL する）
- [ ] 台帳・スナップショット・実測結果を**この公開リポジトリにコミットしていない**
      （`git status` に `*.tsv` / `api_snapshot.json` が出ていないこと）

### FAIL したときの対処（要約）

まず PR コメント冒頭の**台帳ブランチ**を見る。警告が出ていれば、件数を追う前に
プライベートリポジトリ側の対応ブランチを用意すること（比較相手が違うので件数に意味がない）。

ジョブが落ちる条件は 3 つある。PR コメントのどのセクションに件数が出ているかで切り分ける。

| 落ちた場所 | 落ちる条件 |
|---|---|
| ベースラインとの差分 (`drift.md`) | G1〜G7 のいずれかに該当 |
| 台帳との突き合わせ (`reconcile.md`) | A + B + C + D + E の合計が 1 件以上 |
| 変更行の到達可否測定 (probe) | G8 / G9 に該当（結果は artifact に含めないので Actions のログで件数を見る） |

| 検出 | 意味 | 対処 |
|---|---|---|
| G1 / G2 | 新規経路に認証系デコレータが無い / 認証系デコレータが削除された | 実装を直す。意図的な公開なら台帳に根拠を書いてベースライン更新 |
| G3 | 認証・認可デコレータのコメントアウトが増えた | 原則やり直し。残す場合は理由をコード中のコメントに明記する |
| G4 | `*_PERMISSION_FACTORY` / CSRF 保護 等が危険側の値に変わった | 原則やり直し |
| G5 | ModelView の `can_delete` / `can_export` が `False` → `True` | 意図的なら台帳の `data_op` を更新 |
| G6 | 静的解析で属性が取れない経路が追加された | 台帳に行を追加してレビューする（外部ライブラリ由来など） |
| G7 | 依存パッケージの更新で経路が増減した | 増えた経路は台帳に追加。消えた経路は行を削除するか allow に登録 |
| **G8** | **台帳で `data_op` が作成/更新/削除の経路に、未認証で到達した** | **原則やり直し。意図的な公開なら台帳の根拠を更新。`data_op` の記載誤りなら台帳を直す** |
| **G9** | **台帳では遮断なのに実測で到達（認可の回帰）** | **原則やり直し** |
| reconcile A / E | 実機にあるが台帳に無い（A: URI 単位 / E: 同一 URI の endpoint 単位） | 台帳に行を追加する |
| reconcile B | 台帳にあるが実機の `url_map` に無い | 理由を確認し、正当なら allow に登録する |
| reconcile C / D | メソッド・app 列の記載誤り | 台帳を実機に合わせる |

reconcile B のうち、実機に存在しないことが正当な行（プラグイン未登録・config で無効等）は
**プライベートリポジトリ**の `reconcile_allow.json` に**理由付きで**登録する。理由なしの登録は不可。
登録済みの行は B'（既知・許容）として集計され、E'（endpoint が実機に無い）と併せてゲート対象外になる。

W1〜W6 は WARN でゲートは通るが、レビューでは見ること
（ModelView の追加 / 実装本体の変化 / HTTP メソッド・URL の変化 / 監視対象 config の変化 /
依存パッケージの版の変化）。特に W6（依存の版）は、ベースラインを CI と異なる環境で作ると
毎回出続けて形骸化するため、ベースラインは `install.sh` で作った環境から生成する。

> CI の出力は件数のみ。該当した経路名は Actions には出ないので、プライベートリポジトリ側の
> 完全版レポート（`--summary-only` なしで再実行したもの）で確認すること
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
  - <sub>CI: G8 が変更行を未認証で実測（使い捨て環境なので `--allow-writes` 付きで
    GET / HEAD 以外も叩く）</sub>
- [ ] 未ログイン（Anonymous）状態でアクセスした際、意図しないデータ取得・変更が拒絶される
  - <sub>CI: G8 / G9 が変更行を実測。ただし測定対象は変更行のみ、かつ既定プロファイルで
    起動した経路のみ。ワークフロー系など未解決プレースホルダの行は skip される</sub>
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
      **台帳・調査記録はプライベートリポジトリ**（public リポジトリには置かない）。
      §0 のチェック項目で対応済みなら、ここは確認のみ。
  - エンドポイントの追加・変更・廃止、メソッド、認証・認可要件、リクエスト/レスポンス仕様を更新した
  - 調査記録（`weko3_api_auth_findings.md`）もプライベートリポジトリに置く。台帳は二重管理しない
- [ ] **WEKO3 機能仕様書**:
  - 対象機能の仕様追加・変更・クローズ（非公開化）内容を反映した
- [ ] **各種マニュアル (管理者 / 利用者マニュアル)**:
  - 画面導線・操作手順・権限仕様の変更を反映した
- [ ] *更新不要な場合（理由）*: 

---

## 📋 6. 動作検証エビデンス (Verification Evidence)

### テスト実行結果
<!-- テストはモジュール単位で動かす。CI (unit-tests.yml) と同じ手順:
     docker compose run --rm --no-deps -T web bash /code/scripts/ci/run-module-tests.sh <モジュール名>
     コンテナ内で個別に流すなら cd /code/modules/<モジュール名> && pytest -->
```bash
cd modules/<対象モジュール> && pytest
# -> PASS
```

### CI の成果物 (artifact: `api-inventory-summary`)
<!-- 手で貼る必要はない。レビュアが見る場所の案内 -->

| ファイル | 内容 |
|---|---|
| `drift.md` | ベースラインとの差分（**件数のみ**） |
| `reconcile.md` | 台帳と実機の突き合わせ（**件数のみ**） |

明細（該当した経路名・実測結果）は公開できないため artifact に含めていない。
プライベートリポジトリ側で同じコマンドを `--summary-only` なしで実行して確認する。

### 手動で確認したこと
<!-- CI が測れない範囲（ワークフロー経由の操作、画面導線、外部連携など）を記載 -->
* 
