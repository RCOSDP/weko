# Running tests locally

## CI と同じ経路で回す（推奨）

```shell
scripts/ci/run-local.sh weko-records      # 1モジュール
scripts/ci/run-local.sh --all             # マトリクス全部
scripts/ci/run-local.sh --list            # 対象モジュール一覧
```

GitHub Actions の Unit Tests ジョブと**同じ部品**を呼びます。

| | ローカル | CI |
|---|---|---|
| compose | `docker-compose2.yml:docker-compose.ci.yml` | 同左 |
| 起動サービス | postgresql / elasticsearch / redis / rabbitmq のみ | 同左 |
| 起動待ち | `scripts/ci/wait-for-services.sh` | 同左 |
| テスト実行 | `scripts/ci/run-module-tests.sh`（= tox） | 同左 |
| モジュール一覧 | `.github/workflows/unit-tests.yml` の matrix | 同左 |
| イメージ | 同じ入力ファイルのハッシュでタグ付け、無ければビルド | 同じ入力で GHCR から pull |

分岐しているのはイメージの入手方法だけです。CI と完全に同一のイメージで
確かめたいときは `WEKO_IMAGE` / `WEKO_ES_IMAGE` で明示してください。

### ローカルだけで回すと踏む罠

**別の回し方をすると、テストは正常なのに落ちます。** 実測した2件:

- **手元の無関係な `weko-web` イメージを流用した** → イメージに焼き付いた古い
  egg-info の entry_point（`weko_theme.bundles:js_preview_widget`。現行の
  `setup.py` には無い）を `invenio_assets` が読みにいって **191件が ImportError**。
  CI は `ci-images.yml` が `modules/*/setup.py` を含むハッシュでタグを決めるので、
  `setup.py` が変われば作り直され発生しません。
  `run-local.sh` は起動直後に entry_point の健全性を確認して落とします。
- **invenio の venv で直接 `pytest` を叩いた** → `pytest-mock` / `mock` が無く
  `fixture 'mocker' not found`。CI は tox が `requirements2.txt` から入れます。

また、別の WEKO スタックを動かしたままだとポート（29201 / 26301 / 24301）が
衝突し、最悪そちらのサービスを掴みます。`run-local.sh` は起動前に検出します。

### 残る差: ホストのアーキテクチャ

CI は `ubuntu-latest`（x86_64）です。**ARM のホストでは1点だけ差が出ます。**

Elasticsearch 6.8 の seccomp 実装は x86_64 専用で、ARM では
`seccomp unavailable: CONFIG_SECCOMP not compiled into kernel` を投げて
bootstrap check に失敗し起動しません。`run-local.sh` はホストが x86_64 でないとき
`scripts/ci/compose.arm64.yml` を重ねて `discovery.type=single-node` にします
（bootstrap check 自体が省かれる。リポジトリの `docker-compose.arm64.yml` と同じ扱い）。
起動時にその旨を表示します。テストの内容には影響しませんが、
**最終的な合否は CI で確認してください。**

なお `Dockerfile.arm64` / `elasticsearch/Dockerfile.arm64` は使いません。
nodesource の `setup_4.x` が消えており現在はビルドできないためで、
標準の `Dockerfile` / `elasticsearch/Dockerfile` は aarch64 でもビルドできます。

### モジュールを増やしたとき

`.github/workflows/unit-tests.yml` の `matrix.module` が唯一の正です。
`tests/` と `tox.ini` を持つのに未登録のモジュールがあると、CI の
`matrix-check` ジョブが落とします（ジョブが立たない＝赤くもならない、という
静かな漏れを防ぐため）。手元では次で確認できます。

```shell
scripts/ci/matrix.sh check
```

---

## 以下は旧手順（CI とは別経路。参考）

> Python 3.5 の venv を自前で組む手順です。**CI とは Python も依存も tox の
> 有無も違う**ため、ここで通っても CI で通る保証はありません。結果を CI と
> 突き合わせたいときは上の `run-local.sh` を使ってください。

## Running with venv

### Install python 3.5.x

I recommend 3.5.9, but older versions may work as well.
To install it you can use pyenv.
It is personal preference,
but I also like to create venv so I can easily delete it and recreate if needed.

```shell
pyenv install 3.5.9
pyenv global 3.5.9
python -m venv venv
pyenv global system
source venv/bin/activate
```

### Install python dependencies

```shell
python -m pip install -U setuptools wheel pip
python -m pip install -r packages.txt
python -m pip install -r packages-invenio.txt
sed -E 's/\/code\///g' requirements-weko-modules.txt | xargs python -m pip install
python -m pip install 'pytest>=4.6.4,<5.0.0' 'coverage>=4.5.3,<5.0.0' 'mock==3.0.5' 'moto==1.3.7' 'pytest-mock==3.6.1' pytest-cov pytest-invenio 'responses==0.10.3'
```

### Run the tests

#### Run all modules

```shell
./run-tests.sh
```

#### Run single module

```shell
python -m pytest modules/weko-bulkupdate
# OR
cd modules/weko-bulkupdate && python setup.py test
```

#### Run single test

```shell
python -m pytest modules/weko-bulkupdate/tests/test_examples_app.py::test_example_app_role_admin
```

## Running inside docker container

### Adjust file permissions

First of all,
we need to adjust the file permissions of the source code.

Because of `pytest-cov`,
we need write access to the weko folder.
At the time I write this,
by default there is no write access inside the docker container.
So the first step is to adjust this.

To check if there is write access inside the docker container,
try running the following command:

```shell
docker-compose exec web touch test.txt
```

If it doesn't fail for you,
probably there is no need to change any files permission.

Inside the docker container,
the user is `invenio`, group `invenio`.
The group `invenio` is GID 1000.
On your development server,
you have to join a group with GID 1000.
Use the command `getent group` to list groups.
Lets suppose the the group `centos` is GID 1000.
Then you have to run the following command:

```shell
gpasswd -a weko-devXX centos
```

You have to logoff and login to apply this change.

After that,
you must update the source code files and folders access permission.
`cd` to your weko folder and then:

```shell
chown -R weko-devXX:centos .
chmod g+w .
```

### Install test packages

Run the following command to install test packages inside your docker container.

```shell
docker-compose exec web sh -c "pip install 'pytest>=4.6.4,<5.0.0' 'coverage>=4.5.3,<5.0.0' 'mock==3.0.5' 'moto==1.3.7' 'pytest-mock==3.6.1' pytest-cov pytest-invenio 'responses==0.10.3'"
```

> **Do not use `moto==1.3.5`.** It requires `botocore<1.11` and pip silently
> downgrades `boto3` to 1.7.84 to satisfy it. `invenio-s3` requires
> `boto3>=1.9.83`, so the application then fails to start with
> `pkg_resources.VersionConflict` and uwsgi logs `unable to load app 0`.
> `moto==1.3.7` requires `botocore>=1.12.13`, which the pinned
> `boto3==1.9.83` / `botocore==1.12.209` in `modules/*/requirements2.txt`
> already satisfy.
>
> `pytest-mock` is needed too. Without it the tests that use the `mocker`
> fixture (weko-items-ui and others) fail at setup with
> `fixture 'mocker' not found`.
>
> If you hit this, restore the pinned versions:
>
> ```shell
> docker-compose exec web pip install 'boto3==1.9.83' 'botocore==1.12.209'
> ```

### Run the tests

#### Run all modules

```shell
docker-compose exec web ./run-tests.sh
```

#### Run single module

```shell
docker-compose exec web pytest modules/weko-bulkupdate
# OR
docker-compose exec web sh -c 'cd modules/weko-bulkupdate && python setup.py test'
```

#### Run single test

```shell
docker-compose exec web pytest modules/weko-bulkupdate/tests/test_examples_app.py::test_example_app_role_admin
```

### Known errors

If after running the tests,
you receive an error like

```
INTERNALERROR> sqlite3.OperationalError: unable to open database file
```

It means that you don't have write access inside the docker container.
Follow the steps written at the beginning of this manual.

## Reproducing the CI unit-test environment

`.github/workflows/unit-tests.yml` does not use `install.sh`. Unit tests create
their own `wekotest` database and use a temporary `instance_path`, so the demo
SQL, `invenio assets build` / `invenio collect` and the nginx/pgpool/worker/
inbox/mongo/flower containers are not needed.

The image itself is built once per dependency change and reused: modules are
installed with `-e` (see `requirements-weko-modules.txt`) and `.` is bind
mounted to `/code`, so a source change never requires a rebuild.

To run the same thing locally:

```console
$ export COMPOSE_FILE=docker-compose2.yml:docker-compose.ci.yml
$ export WEKO_IMAGE=<prebuilt image>       # e.g. ghcr.io/rcosdp/weko-ci-web:<hash>
$ export WEKO_ES_IMAGE=<prebuilt es image>
$ docker compose up -d postgresql elasticsearch redis rabbitmq
$ bash scripts/ci/wait-for-services.sh
$ docker compose run --rm --no-deps -T web \
    bash /code/scripts/ci/run-module-tests.sh weko-records
$ docker compose down -v
```

Omit `WEKO_IMAGE` / `WEKO_ES_IMAGE` to build locally instead (the overlay then
falls back to `weko-ci-web:local` / `weko-ci-es:local`, which you can build with
`docker compose build web elasticsearch`).

`ui-tests.yml` uses the same images (plus `WEKO_NGINX_IMAGE`) but still needs the
full instance, so it runs `install.sh` with the build step skipped:

```console
$ export COMPOSE_FILE=docker-compose2.yml:docker-compose.ci.yml
$ export WEKO_IMAGE=... WEKO_ES_IMAGE=... WEKO_NGINX_IMAGE=...
$ WEKO_SKIP_BUILD=1 ./install.sh
```

The images themselves are prepared by `.github/workflows/ci-images.yml`; see the
comment at the top of that file for how to replace them.
