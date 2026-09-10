#!/bin/bash
#
# コンテナ内で1モジュール分の tox を実行する。
# 使い方: docker compose run --rm --no-deps -T web bash /code/scripts/ci/run-module-tests.sh weko-records
#         docker compose run ... run-module-tests.sh weko-workflow 3/8   ← 8分割の3本目だけ
#
# 第2引数を渡すと pytest-split でテストを N 等分し、そのうち1本だけを回す。
# weko-workflow は 794 本で 5 時間近くかかり、GitHub Actions のジョブ上限
# (6時間) に収まらない。1ファイルに 447 本あるためファイル単位では割れず、
# 本数で機械的に割っている。分割を使うモジュールは tox.ini の c1 の deps に
# pytest-split を足してある。

set -e

MODULE=${1:?モジュール名を指定してください}
SHARD=${2:-}

# tox が張る子 venv の pip にもダウンロードキャッシュを効かせる。
# 環境変数は tox の passenv (このリポジトリでは LANG のみ) で落ちるため、
# 設定ファイルで渡す。/code/.ci-cache は CI 側でキャッシュされている。
pip_home=${HOME:-/home/invenio}
mkdir -p "${pip_home}/.config/pip"
printf '[global]\ncache-dir = /code/.ci-cache/pip\n' > "${pip_home}/.config/pip/pip.conf"

pip install --upgrade pip
pip install tox tox-setuptools-version pytest-timeout

cd "/code/modules/${MODULE}"

if [ -n "$SHARD" ]; then
  case "$SHARD" in
    [0-9]*/[0-9]*) ;;
    *) echo "第2引数は 3/8 の形式で指定してください: $SHARD" >&2; exit 2 ;;
  esac
  exec tox -- --splits "${SHARD##*/}" --group "${SHARD%%/*}"
fi

exec tox
