#!/bin/bash
#
# コンテナ内で1モジュール分の tox を実行する。
# 使い方: docker compose run --rm --no-deps -T web bash /code/scripts/ci/run-module-tests.sh weko-records

set -e

MODULE=${1:?モジュール名を指定してください}

# tox が張る子 venv の pip にもダウンロードキャッシュを効かせる。
# 環境変数は tox の passenv (このリポジトリでは LANG のみ) で落ちるため、
# 設定ファイルで渡す。/code/.ci-cache は CI 側でキャッシュされている。
pip_home=${HOME:-/home/invenio}
mkdir -p "${pip_home}/.config/pip"
printf '[global]\ncache-dir = /code/.ci-cache/pip\n' > "${pip_home}/.config/pip/pip.conf"

pip install --upgrade pip
pip install tox tox-setuptools-version pytest-timeout

cd "/code/modules/${MODULE}"
exec tox
