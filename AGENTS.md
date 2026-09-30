# AGENTS.md

## プロジェクト概要 / Overview
- WEKO3は研究成果の公開を行うためのリポジトリソフトウェアである。Git等の所謂コードのためのリポジトリとは異なるソフトウェアで、ウェブデータベースアプリケーションに近い概念のソフトウェアである。基本的な機能は研究成果とメタデータと呼ばれる研究成果の説明情報を一緒に保存し、表示、検索、配布する機能がある。外部システム連携のためのAPIを備える。
- **フレームワーク(バックエンド)**: Invenio 3. Invenio3は　Flask 1.0.4 をベースにしている。(Python 3.6)
- **フレームワーク（フロントエンド）**: React, Anguler JS, JQuery
- **利用ミドルウェア**: PostgreSQL 12.x(データベース), Pgpool-II 4.2.2(データベースクラスタ用), Elasticsearch 6.8.23(検索用),Redis 7.4.1(セッション、キャッシュ管理用),RabbitMQ 4.0.2(メッセージキューイング用), nginx 1.20.1(ウェブサーバ用), shibboleth-sp(認証用),CNRI Handle Server(CNRIハンドル発行用) 
- **主要ライブラリ**: Invenio 3 Framework(API,Web API用), Celery + RabbitMQ（タスクキュー）
- **環境設定**: 環境変数は `docker-compose2.yml` ファイルで管理（機密情報はコードに直書きしない）。サーバ固有の設定は `scripts/instance.cfg` に記載する。

## 開発環境セットアップ / Development Setup
- dockerを利用する。
- リポジトリのクローン後、`install.sh` コマンドを実行すると、環境構築が開始される。
- 環境構築後、`https://127.0.0.1/` でサーバにアクセスすることができる。

## テストの実行方法 / Testing

### 手元で回す — **CI と同じ経路を使うこと**

```bash
scripts/ci/run-local.sh weko-records      # 1モジュール
scripts/ci/run-local.sh --all             # マトリクス全部
scripts/ci/run-local.sh --list            # 対象モジュール一覧
```

GitHub Actions の Unit Tests ジョブと同じ compose オーバレイ・同じ待ち受け
スクリプト・同じ `run-module-tests.sh`(= tox)・同じモジュール一覧を使う。
**別の回し方をしないこと。** 違う回し方をすると、テストは正常なのに落ちる:

- 手元の無関係な `weko-web` イメージを流用 → イメージに焼き付いた古い egg-info の
  entry_point を `invenio_assets` が読みにいって大量の ImportError
- invenio の venv で直接 `pytest` → `pytest-mock` / `mock` が無く
  `fixture 'mocker' not found`

`run-local.sh` は起動前に「別の WEKO スタックとのポート衝突」と
「イメージの egg-info が古くないか」を確認して、この2つを事前に落とす。

CI との差は Elasticsearch を `discovery.type=single-node` で起動する1点だけ
(AMD / ARM を問わず同じ。理由は `scripts/ci/compose.local.yml`)。
**最終的な合否は CI で確認する。**

詳細は `README-TEST.md`。

### 台帳ツール(tools/api-inventory)のテスト

```bash
cd tools/api-inventory && python3 -m pytest    # 数秒。Docker も台帳も不要
```

### 新しいモジュールを足したとき

`.github/workflows/unit-tests.yml` の `matrix.module` が**モジュール一覧の唯一の正**。
`tests/` と `tox.ini` を持つのに未登録だと、CI の `matrix-check` ジョブが落とす
(ジョブが立たない = 赤くもならない、という静かな漏れを防ぐため。実際に3モジュール
283本がこの状態で放置されていた)。手元では次で確認する。

```bash
scripts/ci/matrix.sh check
```

### 変更を確定する前に

- 新機能を追加した際は必ず対応するテストコードを追加する
- 触ったモジュールを `run-local.sh` で回し、パスすることを確認する
- 既存の失敗と自分の変更による失敗を必ず区別する。develop_v2.0.5 時点で
  ベースラインに複数の失敗が残っているため、「赤い = 自分のせい」とは限らない

## コードスタイル / Code Style
- コーディング規約: **PEP8**に準拠 (スタイルガイドの遵守)
- フォーマッター: **Black** を使用（`black .` でソースコードを整形）
- リンター: **Flake8** を使用（`flake8` で静的解析チェック）
- インポート順の整理: **isort** を使用（`isort .` でインポート並び替え）
- これらのフォーマットチェックはコミット前に必ず実行し、指摘がない状態にしてください

## セキュリティ方針 / Security
- **秘密情報は厳重に管理**: APIキーやパスワードなど秘密情報は`.env`や環境変数から読み込み、絶対にGitに含めないでください
- **ユーザ入力の検証**: フォームやAPIで受け取る入力は Flask-WTF / marshmallow / JSON Schema など、そのモジュールで既に使われている検証機構で必ず検証してください(本プロジェクトは Django ではありません)
- **デバッグ設定**: 開発中以外では `FLASK_ENV=production` / `DEBUG = False` とし、エラーページや機密情報が漏洩しないようにします
- **依存パッケージ**: 新しいパッケージを導入する際はセキュリティ面を確認し、必要に応じてチームの承認を得てください

## プルリクエストガイドライン / PR Guidelines
- **タイトル形式**: `feat: 機能概要` のように、プレフィックスと簡潔な説明を書いてください
- **事前チェック**: コードを提出する前に `flake8` と `scripts/ci/run-local.sh <触ったモジュール>` を実行し、エラーやテスト失敗がないことを確認しましょう
- **差分の範囲**: 1つのPRは関連する変更に留め、小さくまとまった変更を心がけてください（大規模な変更は分割を検討）
- **説明コメント**: PRの説明欄には変更内容と目的、動作確認の方法を簡潔に記述してください