# テスト実行ガイド

本リポジトリ (WEKO3) のユニットテスト実行方法をまとめます。
テストは `modules/(invenio-*|weko-*)/tests/` 配下に配置された pytest ベースの
テストで、原則として **各モジュールの `tox.ini` に従って `tox` 経由で実行**
します。リポジトリには 2 種類のドライバスクリプトが用意されています。

| スクリプト | 用途 | 実行方式 |
| --- | --- | --- |
| `run-tox.sh` | 公式テスト実行 (各モジュールの `tox.ini` を尊重) | `tox` がモジュール単位で隔離環境を作って実行 |
| `run-tests.sh` | 軽量に pytest を流したいとき | スクリプトが自前で venv を構築し `pytest` を直接実行 |

本ドキュメントは **`run-tox.sh` をベースに記述**します。`run-tests.sh` との
差分は最後の節を参照してください。

## `run-tox.sh` の概要

`run-tox.sh` は次の順で動作します。

1. 先頭で `date --iso-8601="minutes"` をログ出力。
2. 現在の Python 環境に対して以下をインストール。
   - `tox`
   - `tox-setuptools-version`
   - `pytest-timeout`
3. `modules/*/` を走査し、ディレクトリ名が `invenio-*` または `weko-*` で、
   かつ `tests/` ディレクトリを含むモジュールを対象に、
   `(cd <module> && tox; rm -rf .tox)` を実行。
4. 終わりにもう一度 `date --iso-8601="minutes"` をログ出力。

ポイント:

- **`tox.ini` がテスト実行の中心**。各モジュールの `envlist` / `deps` /
  `commands` に従って `.tox/<env>/` 配下に隔離環境を作って実行します。
- **モジュール間で Python 環境が独立**しているため、モジュール固有の依存
  バージョン差分の影響を受けにくい構成です。
- **venv の自動構築は行いません**。スクリプトを実行する前に、WEKO3 が想定する
  Python (Python 3.6 系) と `pip` が `PATH` に通った状態にしておいてください。
- **集計・終了コード判定はありません**。失敗モジュールがあってもスクリプト
  自体は exit 0 で終わるので、ログを目視 (もしくは tee/grep) で確認します。
- 各モジュールの実行後に `rm -rf .tox` を行うため、再実行のたびに tox 環境は
  ゼロから作り直されます。

## 事前準備

### ホストで実行する場合

WEKO3 が想定する Python (3.6 系) を `pyenv` 等で有効化し、`pip` から書き込める
状態にしてください。クリーンに保ちたい場合は、テスト専用の venv を切って
そこで `run-tox.sh` を実行することを推奨します。

```shell
# 例: テスト用 venv を /tmp/weko-tox に作って利用する
python -m venv /tmp/weko-tox
source /tmp/weko-tox/bin/activate
python -m pip install -U 'setuptools' wheel pip
./run-tox.sh
```

### Docker コンテナで実行する場合

`docker-compose.yml` の `web` サービス内で実行します。`pytest-cov` がソース
ツリーへの書き込みを行うため、コンテナ内 (`invenio` ユーザ / GID 1000 の
`invenio` グループ) が書き込み可能であることを確認してください。

```shell
# 書き込み可否を確認
docker-compose exec web touch test.txt
```

失敗する場合は、ホスト側で GID 1000 のグループに作業ユーザを追加し、
ソースツリーの所有権・パーミッションを付与します。

```shell
getent group                   # GID 1000 のグループ名を確認
gpasswd -a weko-devXX centos   # グループに追加 (要再ログイン)
# リポジトリのルートで:
chown -R weko-devXX:centos .
chmod g+w .
```

## 実行方法

### 全モジュールを実行

ホスト上:

```shell
./run-tox.sh
```

Docker コンテナ上:

```shell
docker-compose exec web ./run-tox.sh
```

実行ログを残したい場合:

```shell
./run-tox.sh 2>&1 | tee run-tox.log
```

### 一部モジュールだけ実行 / スキップする

`run-tox.sh` には対象モジュールを絞る環境変数はありません。代わりに、
スクリプト内に各モジュールごとの `if [[ ${module_path} =~ … ]]; then continue; fi`
ブロックがコメントアウトで並んでいるので、**スキップしたいモジュールの
ブロックを uncomment** して使います。

```bash
# 例: invenio-accounts をスキップしたい
if [[ ${module_path} =~ ^modules/(invenio-accounts).+$ ]]; then
  echo "### skip tests for ${module_path%?} ###"
  continue
fi
```

逆に「特定の 1 モジュールだけ実行したい」場合は、スクリプトを使わず直接
`tox` を呼ぶのが手早いです。

```shell
cd modules/weko-bulkupdate
tox
# もしくは tox.ini 内の特定環境のみ
tox -e c1
```

### 単一テストだけ実行する

`tox` 環境を介す場合、`--` 以降に pytest オプションを渡せます。

```shell
cd modules/weko-bulkupdate
tox -- tests/test_examples_app.py::test_example_app_role_admin
```

`tox` を経由せず、すでにアクティブな venv 上で直接 pytest を走らせることも
可能です (依存関係が満たされている前提)。

```shell
python -m pytest modules/weko-bulkupdate/tests/test_examples_app.py::test_example_app_role_admin
```

## トラブルシューティング

- **`INTERNALERROR> sqlite3.OperationalError: unable to open database file`**
  Docker コンテナ内に書き込み権限がありません。上記「事前準備 > Docker
  コンテナで実行する場合」の手順でパーミッションを調整してください。
- **`tox: command not found`**
  `run-tox.sh` が冒頭で `pip install tox` を行いますが、`pip` がアクティブな
  Python 環境を指していない場合に失敗することがあります。`which pip` /
  `python -m pip --version` で利用中の環境を確認してください。
- **`.tox` の再構築に時間がかかる**
  `run-tox.sh` は毎回 `rm -rf .tox` を行うため、繰り返し実行ではモジュール
  ごとに環境が再構築されます。試行錯誤中の単一モジュールについては、
  該当ディレクトリで直接 `tox` を実行 (`rm -rf .tox` をしない) すれば
  キャッシュが効きます。
- **失敗モジュールに気付きにくい**
  `run-tox.sh` は集計を出力しないので、ログを `tee` してから
  `grep -E "FAILED|ERROR|### Running tests" run-tox.log` などで突き合わせる
  運用が便利です。

## 補足: `run-tests.sh` の使い方

`run-tests.sh` は `tox` を使わず、リポジトリ直下に専用 venv を構築して
`pytest` を直接実行する軽量ランナーです。CI で pass/fail を判定したい
ケースや、各モジュールの `tox.ini` を介さず統一環境で素早く走らせたい
ケースで利用します。

### `run-tests.sh` の動作

1. `WEKO_TEST_VENV_DIR` (既定 `/tmp/weko-test-venv`) に venv を作成。
2. 以下を pin バージョンでインストール。
   - 基盤: `setuptools==57.5.0` / `pip==20.2.4` / `wheel` / `coveralls` / `PyYAML`
   - 依存: `packages.txt` / `packages-invenio.txt` /
     `requirements-weko-modules.txt` の内容
   - テストツール: `pytest==5.4.3` / `pytest-cov==2.10.1` /
     `pytest-invenio==1.3.4` / `pytest-mock==3.2.0` /
     `pytest-timeout==1.4.2` / `coverage==4.5.4` / `mock==3.0.5` /
     `responses==0.10.3` / `moto==1.3.5` / `urllib3==1.21.1` /
     `tox==3.28.0` / `tox-setuptools-version==0.0.0.3`
3. venv は上記依存ファイルとツール pin のハッシュをキーにキャッシュされ、
   変化がなければ 2 回目以降は再利用される。
4. `modules/(invenio-*|weko-*)/` のうち `tests/` を含むものに対し、
   `pip install .` → `pytest tests --basetemp=… -o cache_dir=…` を実行。
5. 末尾で `Selected modules / Passed modules / Failed modules` を集計表示し、
   失敗モジュールがあれば exit 1、`WEKO_TEST_MODULES` の空マッチでも exit 1。

### 環境変数

| 変数 | 既定値 | 用途 |
| --- | --- | --- |
| `WEKO_TEST_VENV_DIR` | `/tmp/weko-test-venv` | テスト用 venv の作成先 |
| `WEKO_TEST_TMPDIR` | `/tmp/weko-pytest` | pytest の `--basetemp` / cache 出力先 |
| `WEKO_TEST_MODULES` | (未設定) | 空白区切りで対象モジュールを限定 |

### 全モジュールを実行

ホスト上:

```shell
./run-tests.sh
```

Docker コンテナ上:

```shell
docker-compose exec web ./run-tests.sh
```

### 対象モジュールを絞る

```shell
WEKO_TEST_MODULES="invenio-communities weko-workspace" ./run-tests.sh
```

Docker コンテナ上では `sh -c` でクオートして渡します。

```shell
docker-compose exec web sh -c 'WEKO_TEST_MODULES="invenio-communities weko-workspace" ./run-tests.sh'
```

### 単一モジュールを実行

`run-tests.sh` で作成済みの venv をそのまま利用できます。

```shell
source /tmp/weko-test-venv/bin/activate
python -m pytest modules/weko-bulkupdate
# もしくは setup.py 経由
cd modules/weko-bulkupdate && python setup.py test
```

Docker 上ではコンテナ内のテスト用環境で直接 `pytest` を呼びます。

```shell
docker-compose exec web pytest modules/weko-bulkupdate
docker-compose exec web sh -c 'cd modules/weko-bulkupdate && python setup.py test'
```

### 単一テストを実行

```shell
source /tmp/weko-test-venv/bin/activate
python -m pytest modules/weko-bulkupdate/tests/test_examples_app.py::test_example_app_role_admin
```

Docker 上:

```shell
docker-compose exec web pytest modules/weko-bulkupdate/tests/test_examples_app.py::test_example_app_role_admin
```

任意の pytest オプション (`-k`, `-x`, `-vv`, `--pdb` 等) も同様に渡せます。

### `run-tests.sh` のトラブルシューティング

- **venv を作り直したい**
  `rm -rf /tmp/weko-test-venv` (もしくは `WEKO_TEST_VENV_DIR` で指定したパス)
  を削除して `run-tests.sh` を再実行すれば再構築されます。
- **pytest の一時ファイルが残る**
  `WEKO_TEST_TMPDIR` (既定 `/tmp/weko-pytest`) 以下にモジュール単位で出力
  されます。不要なら削除して問題ありません。
- **`No modules matched WEKO_TEST_MODULES=…` で終了する**
  指定モジュール名が `modules/` 配下のディレクトリ名と一致していません。
  接頭辞 `modules/` の有無やタイポを確認してください。

### `run-tox.sh` との違い (再掲)

| 観点 | `run-tox.sh` (本ガイド主) | `run-tests.sh` |
| --- | --- | --- |
| 実行手段 | 各モジュールの `tox.ini` に従い `tox` 経由 | `pytest tests` を直接実行 |
| Python 環境 | 現在の環境にそのまま `pip install tox …` | `/tmp/weko-test-venv` に venv を自動構築・キャッシュ |
| 依存解決 | モジュールごとに `.tox/<env>/` で隔離 | リポジトリ統一の `packages*.txt` を一括導入 + テストツールは pin バージョン |
| モジュール選択 | スクリプト内コメントの uncomment で個別スキップ | 環境変数 `WEKO_TEST_MODULES="invenio-foo weko-bar"` で絞り込み |
| 集計/exit code | なし (常に exit 0) | 成功・失敗数を集計、失敗があれば exit 1 |
| `.tox` / venv の再利用 | 毎回削除して再構築 | venv 自体は依存ハッシュで再利用 |

「公式テスト」として `tox.ini` を尊重するなら `run-tox.sh`、CI などで
高速かつ pass/fail で判定したい場合は `run-tests.sh`、という使い分けが
想定されています。
