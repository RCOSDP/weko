# feature/a11y（v0.9.20 ベース）から v2.0.5 への移行ツール

feature/a11y のコードで動いているサイトを v2.0.5 のコードに置き換えるときに使う、データと設定の移行ツールです。
作業の順番と判断の基準は、weko-document の `docs/operation/a11y_v0.9.20_v2.0.5.md` に書いてあります。ツールはその手順書に沿って使ってください。

| ファイル | 役割 |
|---|---|
| `migrate.sh` | PostgreSQL、Elasticsearch、静的ファイルの移行を順に実行する |
| `migrate_config.py` | `instance.cfg` などの設定ファイルを v2.0.5 用にマージし、環境変数を確認する |
| `sql/` | `migrate.sh` が流す SQL。どれも何度流しても同じ結果になる |
| `tests/` | `migrate_config.py` のテスト（`python3 -m pytest tools/migration/v2.0.5/tests`） |

## migrate.sh

docker compose でも Kubernetes でも使えるように、web コンテナと psql を呼ぶコマンドを環境変数で渡します。

```bash
# docker compose の例
export WEKO_MIG_WEB="docker compose -f docker-compose2.yml exec -T web"
export WEKO_MIG_PSQL="docker compose -f docker-compose2.yml exec -T postgresql psql -U invenio invenio"
# Kubernetes の例（DB は更新系の Pod を指定する）
export WEKO_MIG_WEB="kubectl exec -i -n weko3 ${POD} -c web --"
export WEKO_MIG_PSQL="kubectl exec -i -n weko3pg ${DB_POD} -- psql -U invenio ${DBNAME}"

export WEKO_MIG_INDEX_PREFIX=tenant1          # サイトの SEARCH_INDEX_PREFIX
export WEKO_MIG_CODE=/path/to/weko            # v2.0.5 のチェックアウト（SQL ファイルを読む）
export WEKO_MIG_LOG_DIR=./upgrade-logs

tools/migration/v2.0.5/migrate.sh preflight   # 読み取りだけの事前確認
tools/migration/v2.0.5/migrate.sh drain       # 旧コードで、統計とインデクサのキューを処理し切る
tools/migration/v2.0.5/migrate.sh db          # v2.0.5 のコードで DB を移行する
tools/migration/v2.0.5/migrate.sh es          # Elasticsearch を移行して再インデックスする
tools/migration/v2.0.5/migrate.sh assets      # 静的ファイルを作り直す
tools/migration/v2.0.5/migrate.sh verify      # 読み取りだけの事後確認
tools/migration/v2.0.5/migrate.sh status      # 適用済みのステップを表示する
```

その他の環境変数:

| 変数 | 既定値 | 内容 |
|---|---|---|
| `WEKO_MIG_ES_URL` | `http://elasticsearch:9200` | web コンテナから見た Elasticsearch の URL |
| `WEKO_MIG_RESTRICTED_ITEM_TYPE_ID` | `30015` | `update_W2025-29.py` に渡す制限公開用プロパティの ID |
| `WEKO_MIG_BATCH_SIZE` | `500` | `update_W2025-29.py` のバッチサイズ |

- `--dry-run` を付けると、実行するコマンドを表示するだけで何も実行しません（例: `migrate.sh --dry-run db`）。
- 1 回しか流してはいけない処理（`update_v0927()`、`W2025-29.sql` など）は、DB のテーブル `weko_upgrade_v205_steps` に記録します。途中で失敗しても、原因を直して同じコマンドを最初から実行し直せば、済んだステップは飛ばされます。
- `invenio shell` で実行するスクリプトは、エラーをログに書いても終了コード 0 で終わることがあります。そのため、出力に `Traceback` または `[ERROR]` があれば失敗として止めます。
- ログは `WEKO_MIG_LOG_DIR` に出力されます。`migrate.log` は全体のログ、`psql.log`、`invenio.log`、`es.log` は各コマンドの出力です。

## migrate_config.py

標準ライブラリだけで動きます（Python 3.6 以上）。旧コードと v2.0.5 のファイルは、既定では WEKO のリポジトリから `git show` で取り出します。

```bash
# instance.cfg をキー単位でマージする
python3 tools/migration/v2.0.5/migrate_config.py instance-cfg \
    --repo . --site /path/to/site/instance.cfg --out instance.cfg.new

# ほかのファイルを 3-way マージする（衝突は diff3 形式のマーカーで残る）
python3 tools/migration/v2.0.5/migrate_config.py merge \
    --repo . --path nginx/weko.conf --site /path/to/site/weko.conf --out weko.conf.new

# instance.cfg を entrypoint と同じように描画し、環境変数の不足や構文エラーを確認する
python3 tools/migration/v2.0.5/migrate_config.py check-env \
    --cfg instance.cfg.new --env configmap.yaml --env secret.yaml
```

- 比較の元にするコードは `--base-ref`（既定 `origin/feature/a11y_pre`）と `--target-ref`（既定 `origin/develop_v2.0.5`）で変えられます。ファイルを直接渡すときは `--base` と `--target` を使います。
- 指摘は `ACTION`（対応が必要）、`WARN`（確認が必要）、`INFO`（参考）の 3 段階で標準エラーに出力します。`ACTION` が 1 件でもあれば、終了コードは 1 になります。
- `--env` には `KEY=VALUE` 形式のファイルか、Kubernetes の ConfigMap / Secret の YAML を渡します。Secret の `data` は base64 のままでは読めないので、`stringData` にするか、デコードした値を渡してください。

instance.cfg のマージの規則:

- **サイトが変えたキー**（旧コードの値と違うキー）は、サイトの値を残します。
  - v2.0.5 でも同じキーの値が変わっている場合は、`WARN` で知らせます。
- **サイトが変えていないキー**は、v2.0.5 の値にします。
  - ただし `WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED` は例外で、旧コードの既定値（`True`）を残します。v2.0.5 は起動時にこの値で DB の設定を上書きするため、v2.0.5 の値にすると、何も言わずに Shibboleth ログインが無効になるからです。
- **v2.0.5 の instance.cfg にないキー**は、ファイルの末尾にまとめて追加します。
  - v2.0.5 が読まなくなったキーだけは、追加しません。
- **値の形式が変わったキー**（`WEKO_WORKFLOW_ACCESS_ACTIVITY_URL` など）は、サイトの値を残さず `ACTION` で知らせます。
- **綴りを間違えた S3 のキー**（`S3_ACCCESS_KEY_ID`、`S3_SECRECT_ACCESS_KEY`）は削除し、値を正しいキーに移します。
- **v2.0.5 の既定値がテスト用のサービスを指すキー**と、**モジュール側で既定値が変わったキー**は、それぞれ確認を促します。
