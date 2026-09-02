#!/bin/bash
#
# GitHub Actions の Unit Tests ジョブを、手元で同じ経路で回す。
#
#     scripts/ci/run-local.sh weko-records
#     scripts/ci/run-local.sh --all
#     scripts/ci/run-local.sh --list
#
# 【なぜ要るか】
# ローカルとCIで違う回し方をすると、どちらかでしか出ない失敗が生まれ、
# 結果を突き合わせられなくなる。実測した2件:
#
#   - 手元にあった無関係な weko-web イメージを流用したところ、イメージに
#     焼き付いた古い egg-info の entry_point (weko_theme.bundles:js_preview_widget。
#     現行の setup.py には無い) を invenio_assets が読みにいって 191件が
#     ImportError になった。CI は ci-images.yml が modules/*/setup.py を含む
#     ハッシュでタグを決め、変われば作り直すので発生しない。
#   - invenio の venv で直接 pytest を叩いたところ pytest-mock / mock が無く、
#     「fixture 'mocker' not found」でテストが落ちた。CI は tox が
#     requirements2.txt から入れるので発生しない。
#
# どちらも**テストは正常なのに落ちる**。原因の切り分けに時間を取られるだけなので、
# このスクリプトは CI と同じ部品をそのまま呼ぶ:
#
#   COMPOSE_FILE          docker-compose2.yml:docker-compose.ci.yml   (CI と同一)
#   起動するサービス       postgresql / elasticsearch / redis / rabbitmq のみ (CI と同一)
#   起動待ち               scripts/ci/wait-for-services.sh            (CI と同一)
#   テスト実行             scripts/ci/run-module-tests.sh             (CI と同一 = tox)
#   モジュール一覧         .github/workflows/unit-tests.yml の matrix (CI と同一)
#
# イメージだけは GHCR から引けないことがあるので、同じ入力ファイル集合の
# ハッシュでローカルタグを作り、無ければビルドする。CI と同じイメージを
# 使いたいときは WEKO_IMAGE / WEKO_ES_IMAGE で明示する。

set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT" || exit 1

KEEP=0
REBUILD=0
MODULES=()

usage() {
  cat <<'USAGE'
使い方: scripts/ci/run-local.sh [オプション] <モジュール名>...

  --all        マトリクスの全モジュールを回す
  --list       マトリクスのモジュール一覧を出して終了
  --keep       終了後もサービスを落とさない(続けて回すとき)
  --rebuild    イメージを作り直す
  -h, --help   これ

環境変数:
  WEKO_IMAGE      本体イメージを明示する(CI と同一のものを使いたいとき)
  WEKO_ES_IMAGE   Elasticsearch イメージを明示する
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --all)     MODULES=(__ALL__) ;;
    --list)    exec "$ROOT/scripts/ci/matrix.sh" list ;;
    --keep)    KEEP=1 ;;
    --rebuild) REBUILD=1 ;;
    -h|--help) usage; exit 0 ;;
    -*)        echo "❌ 不明なオプション: $1" >&2; usage >&2; exit 2 ;;
    *)         MODULES+=("$1") ;;
  esac
  shift
done

[ ${#MODULES[@]} -eq 0 ] && { echo "❌ モジュール名か --all が要る" >&2; usage >&2; exit 2; }

mapfile -t MATRIX < <("$ROOT/scripts/ci/matrix.sh" list)
[ ${#MATRIX[@]} -eq 0 ] && { echo "❌ マトリクスを読めない" >&2; exit 1; }

if [ "${MODULES[0]}" = "__ALL__" ]; then
  MODULES=("${MATRIX[@]}")
else
  # CI に無いモジュールを手元だけで回しても、結果を突き合わせられない。
  for m in "${MODULES[@]}"; do
    printf '%s\n' "${MATRIX[@]}" | grep -qx "$m" || {
      echo "❌ '$m' は unit-tests.yml のマトリクスに無い。" >&2
      echo "   CI で回らないモジュールを手元だけで回しても結果を比べられない。" >&2
      echo "   先にマトリクスへ追加すること。一覧は --list。" >&2
      exit 2
    }
  done
fi

export COMPOSE_FILE=docker-compose2.yml:docker-compose.ci.yml

# --- compose の重ね方 --------------------------------------------------------
# install.sh と同じく COMPOSE_FILE を唯一の調整点にする(アーキで分岐しない)。
#
# Dockerfile は CI と同じものを使う。x86_64 用の Dockerfile /
# elasticsearch/Dockerfile は aarch64 でもビルドできる。リポジトリには
# Dockerfile.arm64 もあるが、nodesource の setup_4.x が消えており現在は
# ビルドできないので使わない。
DOCKERFILE_WEB=Dockerfile
DOCKERFILE_ES=elasticsearch/Dockerfile

# 手元では Elasticsearch の bootstrap check を外す。**アーキテクチャで分岐しない**:
# 分岐すると「片方のアーキでしか再現しない失敗」を作ることになり、ローカルと CI を
# 揃えるという目的に反する。理由は scripts/ci/compose.local.yml に書いてある。
export COMPOSE_FILE="$COMPOSE_FILE:scripts/ci/compose.local.yml"
echo "ℹ️  ホスト: $(uname -m)。CI(x86_64)との差は1点だけ:"
echo "     Elasticsearch を discovery.type=single-node で起動する"
echo "     (bootstrap check はホストのカーネル/sysctl に依存し、開発機では環境しだいで落ちる)"
echo "     テストの内容には影響しないが、最終的な合否は CI で確認すること。"

# --- イメージ ---------------------------------------------------------------
# CI(ci-images.yml)がタグの元にしているのと同じファイル集合。ここが変われば
# 別タグになり、作り直される。egg-info が古いまま使い回される事故を防ぐ要。
web_hash() {
  { sha256sum "$DOCKERFILE_WEB" scripts/provision-web.sh scripts/create-instance.sh \
      scripts/create-instance2.sh scripts/instance.cfg packages.txt \
      packages-invenio.txt requirements-weko-modules.txt requirements-devel.txt \
      package.json 2>/dev/null
    sha256sum modules/*/setup.py 2>/dev/null | sort
  } | sha256sum | cut -c1-16
}
es_hash() {
  sha256sum "$DOCKERFILE_ES" scripts/provision-elasticsearch.sh \
    elasticsearch/dic/character/kui.txt 2>/dev/null | sha256sum | cut -c1-16
}

export WEKO_IMAGE=${WEKO_IMAGE:-weko-ci-web:local-$(web_hash)}
export WEKO_ES_IMAGE=${WEKO_ES_IMAGE:-weko-ci-es:local-$(es_hash)}


build_if_missing() {
  local ref=$1 file=$2 ctx=$3
  if [ "$REBUILD" = 1 ] || ! docker image inspect "$ref" >/dev/null 2>&1; then
    echo "▶ ビルド: $ref  ($file)"
    docker build -f "$file" -t "$ref" "$ctx" || return 1
  else
    echo "▶ 既存イメージを使う: $ref"
  fi
}

build_if_missing "$WEKO_IMAGE"    "$DOCKERFILE_WEB" . || exit 1
build_if_missing "$WEKO_ES_IMAGE" "$DOCKERFILE_ES"  . || exit 1

# --- 他の WEKO スタックとの衝突 ---------------------------------------------
# docker-compose2.yml は 29201 / 26301 / 24301 を publish する。別の WEKO を
# 動かしたままだと起動に失敗するか、最悪そちらのサービスを掴む。
for p in 29201 26301 24301; do
  if (exec 3<>"/dev/tcp/127.0.0.1/$p") 2>/dev/null; then
    exec 3<&- 2>/dev/null
    running=$(docker ps --filter "publish=$p" --format '{{.Names}}' | head -1)
    echo "❌ ポート $p が既に使われている${running:+ (${running})}。"
    echo "   別の WEKO スタックが動いていると、テストがそちらのサービスを掴む。"
    echo "   先に止めること:  cd <その WEKO> && docker compose stop"
    exit 1
  fi
done

# --- サービス起動 ------------------------------------------------------------
echo "▶ サービス起動 (postgresql / elasticsearch / redis / rabbitmq)"
docker compose up -d --no-build postgresql elasticsearch redis rabbitmq || exit 1

cleanup() {
  if [ "$KEEP" = 1 ]; then
    echo "▶ --keep のためサービスは起動したまま。止めるとき:"
    echo "    COMPOSE_FILE='$COMPOSE_FILE' docker compose down -v"
  else
    echo "▶ 後片付け"
    docker compose down -v >/dev/null 2>&1
  fi
}
trap cleanup EXIT

bash "$ROOT/scripts/ci/wait-for-services.sh" || exit 1

# --- 事前確認: 古い egg-info を掴んでいないか --------------------------------
# WEKO_IMAGE を手で指定したときに効く。ここで落としておかないと、テストの失敗と
# 見分けがつかない ImportError が何百件も出る。
echo "▶ entry_point の健全性を確認"
docker compose run --rm --no-deps -T web bash -c '
/home/invenio/.virtualenvs/invenio/bin/python - <<PY
import sys, pkg_resources
bad = []
for ep in pkg_resources.iter_entry_points("invenio_assets.bundles"):
    try:
        ep.load()
    except Exception as exc:
        bad.append("%s (%s)" % (ep, type(exc).__name__))
if bad:
    print("❌ 壊れた entry_point が %d 件。イメージの egg-info がソースより古い。" % len(bad))
    for b in bad[:5]:
        print("   ", b)
    print("   --rebuild で作り直すか、WEKO_IMAGE の指定を外すこと。")
    sys.exit(1)
print("✓ entry_point は健全")
PY' || exit 1

# --- 実行 --------------------------------------------------------------------
failed=()
for m in "${MODULES[@]}"; do
  echo
  echo "==================== $m ===================="
  # CI が呼ぶのと同じスクリプト。ここを分岐させないこと。
  if docker compose run --rm --no-deps -T web \
       bash /code/scripts/ci/run-module-tests.sh "$m"; then
    echo "✓ $m"
  else
    echo "✗ $m"
    failed+=("$m")
  fi
done

echo
echo "==================== まとめ ===================="
echo "実行 ${#MODULES[@]} / 失敗 ${#failed[@]}"
if [ ${#failed[@]} -gt 0 ]; then
  printf '  ✗ %s\n' "${failed[@]}"
  exit 1
fi
echo "  すべて成功"
