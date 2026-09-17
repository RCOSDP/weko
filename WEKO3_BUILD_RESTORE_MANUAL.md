# WEKO3 (feature/jgss) ビルド〜データリストア手順書

> このファイルはこの `feature/jgss` ブランチのPRに合わせてリポジトリに同梱したものです。手順書自体の由来・更新は `/home/vagrant/backup_jgss/WEKO3_build_restore_manual.md`（同一環境内）を正本として管理している。
>
> **本文中で参照する `backup_jgss/WEKO3_OPE-9985_*.gz`（PostgreSQL dump・Elasticsearch snapshot）はこのgitリポジトリには含まれない。** サイズが大きい本番バックアップデータのため、別途担当者から入手し、リポジトリと同階層の `backup_jgss/` に配置すること。

## 1. 目的

`feature/jgss` ブランチの WEKO3 Docker Compose 環境を新規にビルドし、JGSS（JGSS データダウンロードシステム／`jgssdds_repo_nii_ac_jp`）の本番バックアップ（PostgreSQL + Elasticsearch snapshot）を復元して動作確認可能な状態にするまでの一連の手順をまとめる。

対象環境: `/home/vagrant/weko`（git branch: `feature/jgss`）
使用 Compose ファイル: `docker-compose2.yml`

> **重要:** `docker compose down -v`、`docker volume prune`、`docker system prune -a --volumes` は、データ入り volume（`es-data` 等）を破壊するため実行しない。

## 2. 事前準備: ブランチ取得

```bash
cd ~/weko
git fetch -p
git checkout feature/jgss
```

以降の章のコード修正は `feature/jgss` に対して行い、完了後にコミットする（本手順で実施したビルド修正・環境設定変更は `feature/jgss` に 2 コミットとして反映済み）。

## 3. ビルド時の修正

`docker-compose -f docker-compose2.yml build` は、リポジトリ内の記述だけでは外部依存の経年劣化により以下 4 点で失敗する。詳細な原因は `BUILD_FIX_NOTES.md` を参照。

### 3.1 Debian Buster APT ミラー消滅（404 Not Found）

Debian buster は EOL となり通常ミラーから削除されているため、`Dockerfile` の `stage_2`（`provision-web.sh` 実行前）で `archive.debian.org` を参照するよう書き換える。

```dockerfile
# Debian buster is EOL: repoint apt sources to archive.debian.org
# so `apt-get update` doesn't 404 against the removed mirrors.
RUN sed -i \
    -e 's|deb.debian.org/debian |archive.debian.org/debian |g' \
    -e 's|security.debian.org/debian-security|archive.debian.org/debian-security|g' \
    -e '/buster-updates/d' \
    /etc/apt/sources.list && \
    echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99no-check-valid-until
```

### 3.2 NodeSource Node.js 4.x リポジトリの GPG 署名検証失敗

`https://deb.nodesource.com/setup_4.x` は EOL で署名鍵が取得できず `apt-get update` が失敗する。`scripts/provision-web.sh` で、セットアップスクリプト実行の失敗を許容しつつ、当該リポジトリのみ `[trusted=yes]` にして再度 `apt-get update` する。

```bash
# NodeSource's Node.js 4.x repo is EOL: its own setup script runs
# `apt-get update` internally and that fails because the repo's GPG
# signature can no longer be verified (key not served anymore), so
# allow this one command to fail (it still writes the sources.list.d
# file before erroring out) rather than aborting the whole build.
curl -sL https://deb.nodesource.com/setup_4.x | $sudo bash - || true
# Trust this single, already-EOL repo explicitly rather than
# weakening apt verification globally, then refresh package lists.
$sudo sed -i 's/\[signed-by=[^]]*\]/[trusted=yes]/' /etc/apt/sources.list.d/nodesource.list
$sudo apt-get -y update
```

### 3.3 npm 間接依存（psl / tough-cookie）が Node.js 4.x で構文エラー

`node-sass@3.8.0` の間接依存 `request → tough-cookie → psl` がバージョン固定なしのため、時間経過で ES5 のみ対応の Node.js 4.x では実行できないモダン構文（スプレッド構文等）を使うバージョンに解決されてしまう。`scripts/provision-web.sh` の該当 `npm install -g` に旧バージョンを明示的に追加する。

```bash
# Pin transitive deps of node-sass@3.8.0 (via request -> tough-cookie -> psl)
# to old, ES5-only versions: newer psl/tough-cookie releases use syntax
# (e.g. spread operator) that Node.js 4.x's runtime cannot parse.
$sudo su -c "npm install -g node-sass@3.8.0 clean-css@3.4.12 requirejs uglify-js psl@1.1.31 tough-cookie@2.3.4"
```

### 3.4 GitHub 上の依存リポジトリ削除（angular-schema-form-ckeditor）

元リポジトリ `webcanvas/angular-schema-form-ckeditor` が GitHub 上から削除されており `npm install` 中の clone が 401 で失敗する。同一コミットを含むフォーク `nvdnkpr/angular-schema-form-ckeditor` の tarball URL に参照先を変更する（npm v2 系のシャロークローンはフォークのデフォルトブランチ tip 以外に到達できないため、`git+commit` 参照ではなく tarball URL を使う）。

`modules/invenio-deposit/invenio_deposit/bundles.py`:

```python
# Original repo (webcanvas/angular-schema-form-ckeditor) was deleted
# from GitHub; this fork carries the exact same commit. Use a
# tarball URL (not a git+commit ref) since npm's shallow git clone
# can't reach a commit outside the fork's default branch tip.
'angular-schema-form-ckeditor':
    'https://github.com/nvdnkpr/angular-schema-form-ckeditor'
    '/archive/b213fa934759a18b1436e23bfcbd9f0f730f1296.tar.gz',
```

### 3.5 ビルド実行

```bash
cd ~/weko
docker compose -f docker-compose2.yml build
```

`weko-web` イメージのビルド完了・exit code 0 を確認する。

補足: 旧いディスク不足・PostgreSQL ポート競合（旧 `weko-pgpool-1` の `25401` 占有）・RabbitMQ 4.x の `transient_nonexcl_queues` 非推奨警告など、ホスト環境要因の問題が発生する場合は本書末尾「9. 過去に遭遇したホスト環境要因の問題」を参照。

## 4. Elasticsearch イメージのバージョン合わせ

リストア対象の Elasticsearch snapshot は `6.8.23` で取得されているため、`elasticsearch/Dockerfile` のベースイメージを合わせておく（snapshot は同一または新しい ES バージョンにしかリストアできない）。

```dockerfile
# Pinned to 6.8.23 to match the version the JGSS ES snapshot backup was
# created with (a snapshot cannot be restored onto an older ES node).
FROM docker.elastic.co/elasticsearch/elasticsearch-oss:6.8.23
```

`docker-compose2.yml` の worker サービスの `image:` が `weko3_b_web` のような誤った（ビルドされない）タグになっている場合は、web と同じ `weko-web` に修正する。

## 5. 環境起動

```bash
cd ~/weko
docker compose -f docker-compose2.yml up -d
docker compose -f docker-compose2.yml ps
```

全サービス（postgresql, elasticsearch, redis, rabbitmq, web, worker, nginx, flower）が `Up` であることを確認する。

```bash
curl -k -I https://localhost/
```

`HTTP/1.1 200 OK` を確認する（この時点ではまだ初期データ／`tenant1-*` のデモデータ状態）。

## 6. PostgreSQL 復元（JGSS 本番データ）

対象ファイル: `backup_jgss/WEKO3_OPE-9985_jgssdds_repo_nii_ac_jp.sql.gz`（※このgitリポジトリには含まれない。上記の注記を参照）

このファイルは **plain-text 形式**の `pg_dump` 出力を gzip 圧縮したものであり（`pg_restore` 用の custom-format ではない）、`psql` にパイプしてリストアする。

### 6.1 dump の正常性確認

```bash
zcat backup_jgss/WEKO3_OPE-9985_jgssdds_repo_nii_ac_jp.sql.gz | head -c 300
```

`-- PostgreSQL database dump` で始まることを確認する。

### 6.2 public schema 初期化

**破壊的操作。dump の正常性を確認してから実行する。**

```bash
docker exec weko-postgresql-1 \
  psql -U invenio -d invenio -v ON_ERROR_STOP=1 -c \
  "DROP SCHEMA public CASCADE; CREATE SCHEMA public AUTHORIZATION invenio; GRANT ALL ON SCHEMA public TO invenio; GRANT ALL ON SCHEMA public TO public;"
```

### 6.3 復元

```bash
zcat backup_jgss/WEKO3_OPE-9985_jgssdds_repo_nii_ac_jp.sql.gz \
  | docker exec -i weko-postgresql-1 psql -U invenio -d invenio -v ON_ERROR_STOP=1
```

### 6.4 復元後バックアップ（custom format で取得し直す）

```bash
docker exec weko-postgresql-1 \
  pg_dump -U invenio -Fc invenio > ~/weko/after_restore_jgssdds.dump
```

### 6.5 復元確認

```bash
docker exec weko-postgresql-1 psql -U invenio -d invenio -tAc \
  "SELECT name FROM site_info;"
```

`JGSSデータダウンロードシステム` / `JGSS Data Download System` が返ることを確認する（サイト名にリストアしたテナントの情報が入っていることの確認）。

```bash
docker exec weko-postgresql-1 psql -U invenio -d invenio -tAc \
  "SELECT count(*) FROM pidstore_pid WHERE pid_value LIKE '%jgssdds%';"
```

## 7. Elasticsearch snapshot 復元（JGSS 本番データ）

対象ファイル: `backup_jgss/WEKO3_OPE-9985_WEKO3_OPE-9985-jgssdds_repo_nii_ac_jp-esbackup.tar.gz`（※このgitリポジトリには含まれない）

これは Elasticsearch filesystem snapshot repository である。`/usr/share/elasticsearch/data`（＝ `es-data` volume）へ直接展開しない。

### 7.1 展開

tar 内部に `WEKO3_OPE-9985/` という 1 階層のディレクトリが含まれるため、これを取り除いて展開する。

```bash
cd ~/weko
rm -rf es_snapshot_restore_new
mkdir -p es_snapshot_restore_new
tar -xzf backup_jgss/WEKO3_OPE-9985_WEKO3_OPE-9985-jgssdds_repo_nii_ac_jp-esbackup.tar.gz \
  -C es_snapshot_restore_new --strip-components=1
```

展開後、直下に `index-0` / `index.latest` / `indices/` / `meta-*.dat` / `snap-*.dat` があることを確認する。

### 7.2 snapshot repository をマウント

`docker-compose2.yml` の `elasticsearch` サービス:

```yaml
elasticsearch:
  volumes:
    - es-data:/usr/share/elasticsearch/data
    - ./es_snapshot_restore_new:/usr/share/elasticsearch/backups:ro
```

反映:

```bash
docker compose -f docker-compose2.yml up -d --force-recreate elasticsearch
docker exec weko-elasticsearch-1 ls -lah /usr/share/elasticsearch/backups
```

### 7.3 repository 登録

```bash
curl -X PUT 'http://localhost:29201/_snapshot/jgssdds_restore' \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "fs",
    "settings": {
      "location": "/usr/share/elasticsearch/backups",
      "readonly": true
    }
  }'
```

### 7.4 snapshot 確認

```bash
curl -s 'http://localhost:29201/_snapshot/jgssdds_restore/_all?pretty'
```

- Elasticsearch: `6.8.23`
- インデックス名は本番接頭辞 `jgssdds_repo_nii_ac_jp-*`

### 7.5 restore（本番接頭辞のまま：参照用）

```bash
curl -X POST \
  'http://localhost:29201/_snapshot/jgssdds_restore/snapshot/_restore?pretty' \
  -H 'Content-Type: application/json' \
  -d '{
    "indices": "jgssdds_repo_nii_ac_jp-*",
    "include_global_state": false
  }'
```

### 7.6 restore（`tenant1-*` へリネームして復元：Web アプリが実際に参照する側）

WEKO3 の `SEARCH_INDEX_PREFIX` は環境で汎用の `tenant1` を使う運用のため、同じ snapshot をもう一度、インデックス名を `tenant1-*` にリネームして復元する（再インデックスではなく ES の snapshot restore の `rename_pattern`/`rename_replacement` 機能を使うことで、データをコピーし直さずに別名で復元できる）。

```bash
curl -X POST \
  'http://localhost:29201/_snapshot/jgssdds_restore/snapshot/_restore?pretty' \
  -H 'Content-Type: application/json' \
  -d '{
    "indices": "jgssdds_repo_nii_ac_jp-*",
    "rename_pattern": "jgssdds_repo_nii_ac_jp-(.+)",
    "rename_replacement": "tenant1-$1",
    "include_global_state": false
  }'
```

> 既存の初期デモデータ由来の `tenant1-*` インデックスがある場合は、リネーム復元前に削除するか `include_global_state`/`indices` の対象を絞るなどして、復元対象と名前が衝突しないようにする。

### 7.7 復元確認

```bash
curl -s 'http://localhost:29201/_cat/recovery?v' | grep -E "jgssdds_repo_nii_ac_jp-weko-item|tenant1-weko-item"
```

`stage=done`、`files_percent=100.0%`、`bytes_percent=100.0%` であることを確認する。

```bash
curl -s 'http://localhost:29201/_cat/indices/tenant1-weko-item-v1.0.0?v'
```

single-node で replica=1 のため `yellow` でも復元失敗ではない。

## 8. Web/Worker 設定と最終確認

### 8.1 SEARCH_INDEX_PREFIX

`docker-compose2.yml` の `web` / `worker` サービス（`environment`）を確認する。今回は `tenant1-*` へリネーム復元しているため、`SEARCH_INDEX_PREFIX=tenant1` のままでよい（本番接頭辞 `jgssdds_repo_nii_ac_jp` に変更しない）。

```bash
docker compose -f docker-compose2.yml config | grep -n -A2 -B2 SEARCH_INDEX_PREFIX
```

### 8.2 反映

```bash
docker compose -f docker-compose2.yml up -d --force-recreate web worker
docker compose -f docker-compose2.yml restart nginx
```

### 8.3 確認

```bash
docker exec weko-web-1 sh -c 'echo $SEARCH_INDEX_PREFIX'
# => tenant1

curl -k -I https://localhost/
# => HTTP/1.1 200 OK
```

- PostgreSQL: `site_info.name` が JGSS のもの、`pidstore_pid` に `jgssdds` を含む PID が存在する。
- Elasticsearch: `jgssdds_repo_nii_ac_jp-*`（参照用）と `tenant1-*`（Web 参照用）の両方が `recovery` で `done`。
- `tenant1-weko-item-v1.0.0` の `docs.count` が `jgssdds_repo_nii_ac_jp-weko-item-v1.0.0` と一致する。
- ブラウザから検索・アイテム詳細・添付ファイル・管理画面・登録更新処理を確認する。

## 9. 過去に遭遇したホスト環境要因の問題（参考）

以前、今回とは無関係な別テナントのバックアップを復元した際に遭遇した、ホスト環境固有の問題と対処。今回のビルドでは必須ではないが、再発時の参考として残す。

- **ディスク不足**: `sudo lvextend -l +100%FREE -r /dev/ubuntu-vg/ubuntu-lv` で LVM のルート LV を拡張。
- **PostgreSQL ポート競合**: 旧 `weko-pgpool-1` が `25401` を使用していた場合、`docker stop weko-pgpool-1 && docker rm weko-pgpool-1` で不要なコンテナのみ削除。
- **RabbitMQ 4.x / Celery-Kombu の `transient_nonexcl_queues` 非推奨警告**: `rabbitmq/rabbitmq.conf` に `deprecated_features.permit.transient_nonexcl_queues = true` を設定し、`docker-compose2.yml` の `rabbitmq` に `./rabbitmq/rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf:ro` をマウント。無害な警告であり必須対応ではない。
- **Web 再作成後の Nginx 502**: `docker compose restart nginx` で解消することが多い。

## 10. 注意事項

- `docker compose down -v` を実行しない。
- `docker volume prune` を実行しない。
- `docker system prune -a --volumes` を実行しない。
- Elasticsearch snapshot を `es-data` に直接コピーしない。
- PostgreSQL の `public` schema 削除前に dump の正常性（ヘッダ）を確認する。
- `jgssdds_repo_nii_ac_jp-*`（本番接頭辞・参照用）は、`tenant1-*` 側での動作確認が完了するまで削除しない。
- 旧バックアップ由来の別テナントのインデックスや `after_restore.dump`（旧バックアップの復元後ダンプ）は、今回の JGSS 復元とは無関係の別テナントのものであり、削除是非は別途判断する。
- orphan の `weko-inbox-1` / `weko-mongo-1` を確認なしで `--remove-orphans` により削除しない。
- Elasticsearch snapshot はアップロード済みバイナリファイルそのもののバックアップではない。添付ファイルについては `data_data` 等のファイルストレージを別途確認する。

## 11. 最終確認チェックリスト

- [ ] `feature/jgss` ブランチで `docker compose -f docker-compose2.yml build` が成功する。
- [ ] 全サービスが `Up` で起動する。
- [ ] PostgreSQL `public` に JGSS データ（`site_info`、`pidstore_pid` 等）が復元されている。
- [ ] `after_restore_jgssdds.dump` が取得済み。
- [ ] Elasticsearch `jgssdds_restore` リポジトリの snapshot が `jgssdds_repo_nii_ac_jp-*` と `tenant1-*` の両方に復元され、`recovery` が `done`/`100.0%`。
- [ ] `SEARCH_INDEX_PREFIX=tenant1` で Web/Worker が起動している。
- [ ] HTTPS が `200 OK`。
- [ ] ブラウザから検索、アイテム詳細、添付ファイル、管理画面、登録・更新処理を確認する。
