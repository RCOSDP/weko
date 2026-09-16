# docker-compose2.yml ビルド修正メモ（feature/jgss）

`docker-compose -f docker-compose2.yml build` を実行した際、外部依存の経年劣化により
複数の段階でビルドが失敗した。原因と対応を記録する。

## 1. Debian buster のミラー消滅（404 Not Found）

- **症状**: `apt-get update` が `deb.debian.org` / `security.debian.org` に対して
  404 Not Found で失敗する。
- **原因**: Debian buster は EOL となり、通常のミラーから削除され
  `archive.debian.org` に移動済み。
- **対応**: `Dockerfile` の `stage_2` で、`provision-web.sh` 実行前に
  `/etc/apt/sources.list` を `archive.debian.org` を参照するよう書き換え、
  `Acquire::Check-Valid-Until "false"` を設定した。

## 2. NodeSource Node.js 4.x リポジトリの GPG 署名検証失敗

- **症状**: `https://deb.nodesource.com/setup_4.x` が追加するリポジトリの
  `InRelease` が `NO_PUBKEY 1655A0AB68576280` で検証できず、
  `apt-get update` が失敗する。
- **原因**: Node.js 4.x 用リポジトリは EOL で、署名鍵が NodeSource 側の
  鍵配布エンドポイントから既に取得できない。
- **対応**: `scripts/provision-web.sh` で、NodeSource セットアップスクリプト
  実行後に `sources.list.d/nodesource.list` の `[signed-by=...]` オプションを
  `[trusted=yes]` に置き換え、このリポジトリのみ検証をスキップするようにした
  （他の apt ソースの検証には影響しない）。セットアップスクリプト自体が
  内部で実行する `apt-get update` の失敗で `set -o errexit` により
  スクリプト全体が止まらないよう `|| true` を付与し、その後
  明示的に `apt-get -y update` を再実行している。

## 3. npm 間接依存（psl）が Node.js 4.x で構文エラー

- **症状**: `npm install -g node-sass@3.8.0 ...` の実行中、
  `node-sass/node_modules/request/node_modules/tough-cookie/node_modules/psl`
  で `SyntaxError: Unexpected token ...`（スプレッド構文）が発生する。
- **原因**: `package.json` にバージョン固定（lockfile）がなく、
  `npm install` 実行時点の npm レジストリ最新版の間接依存を解決するため、
  時間経過とともに `psl` が Node.js 4.x では実行できないモダンな構文を
  使うバージョンに更新されてしまっていた。
- **対応**: `scripts/provision-web.sh` の該当 `npm install -g` コマンドに
  `psl@1.1.31 tough-cookie@2.3.4`（Node.js 4.x 互換の古いバージョン）を
  明示的に追加し、間接依存として新しいバージョンが解決されないようにした。

## 4. GitHub 上の依存リポジトリ削除（angular-schema-form-ckeditor）

- **症状**: `create-instance2.sh` の npm install 中、
  `https://github.com/webcanvas/angular-schema-form-ckeditor.git` の clone で
  `Invalid username or token. Password authentication is not supported for
  Git operations.` が発生する。
- **原因**: 元リポジトリ `webcanvas/angular-schema-form-ckeditor` が
  GitHub 上から削除（または非公開化）されており、匿名アクセスで
  401 Unauthorized となっていた。
- **対応**: 同一コミット（`b213fa934759a18b1436e23bfcbd9f0f730f1296`）を
  含むフォーク `nvdnkpr/angular-schema-form-ckeditor` を発見し、
  `modules/invenio-deposit/invenio_deposit/bundles.py` の参照先を
  そちらに変更した。また、npm（v2系）のシャロークローンでは
  フォーク側のデフォルトブランチ tip 以外のコミットに到達できず
  `fatal: bad object` となったため、`git+commit` 参照ではなく
  GitHub の tarball URL
  （`.../archive/<commit>.tar.gz`）を指定する方式に変更した。

## 変更ファイル

- `Dockerfile`
- `scripts/provision-web.sh`
- `modules/invenio-deposit/invenio_deposit/bundles.py`

## 結果

上記 4 点の修正により `docker-compose -f docker-compose2.yml build` が
成功することを確認済み（`weko-web` イメージのビルド完了、exit code 0）。
