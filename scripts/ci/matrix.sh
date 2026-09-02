#!/bin/bash
#
# unit-tests.yml のマトリクスを唯一の正として読む。
#
# モジュール一覧が「ワークフローの中」と「ローカル実行の手順」に二重に書かれると、
# 必ず片方が古びる。実際 v2.0.5 までの間に weko-notifications / weko-signposting /
# weko-workspace の3モジュールがマトリクスから漏れ、テスト一式(283本)を持ちながら
# 一度も CI で実行されていなかった。
#
#   scripts/ci/matrix.sh list     マトリクスのモジュールを1行1件で出す
#   scripts/ci/matrix.sh check    マトリクスとテスト対象モジュールの食い違いを検出する
#                                 (テストがあるのに未登録 = 失敗 / 逆 = 警告)

set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
WORKFLOW="$ROOT/.github/workflows/unit-tests.yml"

list_matrix() {
  [ -f "$WORKFLOW" ] || { echo "❌ $WORKFLOW が無い" >&2; return 1; }
  # `        module:` の下に続く `          - name` を拾う。
  awk '
    /^[[:space:]]+module:[[:space:]]*$/ { inlist = 1; next }
    inlist && /^[[:space:]]+- [A-Za-z0-9_-]+[[:space:]]*$/ {
      gsub(/^[[:space:]]+- |[[:space:]]+$/, ""); print; next
    }
    inlist { inlist = 0 }
  ' "$WORKFLOW"
}

# テスト一式を持つ = tests/ と tox.ini の両方がある。
# cookiecutter-weko-module(雛形) や resources(証明書置き場) は該当しない。
list_testable() {
  for d in "$ROOT"/modules/*/; do
    m=$(basename "$d")
    [ -d "$d/tests" ] && [ -f "$d/tox.ini" ] && echo "$m"
  done
}

case "${1:-list}" in
  list)
    list_matrix
    ;;
  check)
    tmp_m=$(mktemp) tmp_t=$(mktemp)
    trap 'rm -f "$tmp_m" "$tmp_t"' EXIT
    list_matrix   | sort > "$tmp_m"
    list_testable | sort > "$tmp_t"

    missing=$(comm -13 "$tmp_m" "$tmp_t")
    stale=$(comm -23 "$tmp_m" "$tmp_t")
    rc=0

    # 【失敗させる】テストがあるのにマトリクスに無い = 静かな穴。
    # ジョブが立たないので、赤くならないまま何百本も実行されない状態が続く。
    if [ -n "$missing" ]; then
      echo "❌ tests/ と tox.ini を持つのにマトリクスに無いモジュール:"
      echo "$missing" | sed 's/^/     - /'
      echo "   → .github/workflows/unit-tests.yml の matrix.module に追加してください。"
      echo "     載せない正当な理由があるなら、その旨をワークフローにコメントで残すこと。"
      rc=1
    fi

    # 【警告に留める】マトリクスにあるがテストが無い = ジョブは立って赤くなるので
    # 見えている。消すか足すかは人の判断なので、ここでは黙って落とさない。
    # --strict を付けたときだけ失敗させる。
    if [ -n "$stale" ]; then
      echo "⚠️  マトリクスにあるが tests/ か tox.ini が無いモジュール:"
      echo "$stale" | sed 's/^/     - /'
      echo "   → ジョブは立つが実行するテストが無く、常に失敗し続ける。"
      echo "     テストを足すか、マトリクスから外すか、どちらかに決めてください。"
      [ "${2:-}" = "--strict" ] && rc=1
    fi

    if [ -z "$missing" ] && [ -z "$stale" ]; then
      echo "✓ マトリクス $(wc -l < "$tmp_m") 件がテスト対象モジュールと一致"
    elif [ $rc -eq 0 ]; then
      echo "✓ 静かな漏れは無し(マトリクス $(wc -l < "$tmp_m") 件)"
    fi
    exit $rc
    ;;
  *)
    echo "使い方: $0 {list|check}" >&2
    exit 2
    ;;
esac
