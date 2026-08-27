#!/usr/bin/env bash
# 台帳の実測を「毎回まったく同じ手順・同じ出力」で回す唯一の入口。
#
#   ./measure.sh                # 全行
#   ./measure.sh --nos 1,2,3    # 一部だけ
#
# ★バージョンが増えてもこのスクリプトは増えない・変えない。
#   - 対象リビジョンは git から自動で読む(引数で渡さない)
#   - 測定条件は $WEKO_API_INVENTORY_DIR/measure_profile.json に置く
#     (無ければ既定値で自動生成する)。条件を変えたいときはコードではなく
#     この JSON を直す。レポートにプロファイルのハッシュを載せるので、
#     2回の測定が同一条件だったかを後から確認できる。
#
# 出力は毎回 $WEKO_API_INVENTORY_DIR/measure_report.md に同じ書式で書く。
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${WEKO_API_INVENTORY_DIR:?台帳の場所を指定してください (export WEKO_API_INVENTORY_DIR=...)}"
: "${WEKO_ROOT:=$(cd "$HERE/../../.." && pwd)}"
export WEKO_ROOT

NOS=""; SKIP_VERIFY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --nos) NOS="$2"; shift ;;
    --skip-verify) SKIP_VERIFY=1 ;;
    *) echo "不明な引数: $1 (条件は measure_profile.json で指定します)" >&2; exit 2 ;;
  esac; shift
done

REV="$(git -C "$WEKO_ROOT" describe --tags --always 2>/dev/null || echo unknown)"
HEAD_REV="$(git -C "$WEKO_ROOT" rev-parse --short HEAD)"
PROFILE="$WEKO_API_INVENTORY_DIR/measure_profile.json"
"$HERE/_ensure_profile.py" "$PROFILE"
eval "$("$HERE/_read_profile.py" "$PROFILE")"
export WEKO_WEB_CONTAINER="$WEB_CONTAINER"

WORK="$(mktemp -d)"
FULL="$WEKO_API_INVENTORY_DIR/weko3_api_list_full.tsv"
REPORT="$WEKO_API_INVENTORY_DIR/measure_report.md"
STAMP="$(date +%Y-%m-%d)"
say() { printf '%s\n' "$*"; }

say "[0/6] 前提を確認する"
say "  WEKO_ROOT      : $WEKO_ROOT ($HEAD_REV)"
say "  リビジョン     : $REV"
say "  台帳           : $WEKO_API_INVENTORY_DIR"
say "  web コンテナ   : $WEB_CONTAINER"
say "  プロファイル   : sha256:$PROFILE_HASH"
say "  書き込み       : ${WRITES:-なし(読み取り専用)}"

if [ -z "$SKIP_VERIFY" ]; then
  # 稼働中の uwsgi が本当にこのリビジョンを読んでいるかを確かめる。
  # snapshot.py は毎回新プロセスなので即反映されるが、probe は uwsgi を叩くため
  # egg-info の再生成と restart をしないと別バージョンを測ることになる。
  code="$(curl -sk --max-time 20 -o /dev/null -w '%{http_code}' -H "Host: $HOSTHDR" "$BASE/" || true)"
  if [ "$code" != "200" ]; then
    say "  ★トップページが $code。egg-info を再生成して web を再起動してください。"
    say "     docker exec $WEB_CONTAINER bash -lc 'cd /code && for d in modules/*/; do (cd \"\$d\" && python setup.py -q egg_info); done'"
    say "     docker restart $WEB_CONTAINER"
    exit 1
  fi
  say "  トップページ   : 200"
fi

say "[1/6] スナップショットを取り直す"
python3 "$HERE/snapshot.py" --out "$WEKO_API_INVENTORY_DIR/api_snapshot.json" >"$WORK/snapshot.log" 2>&1
tail -1 "$WORK/snapshot.log" | sed 's/^/  /'

say "[2/6] 台帳と突き合わせる"
python3 "$HERE/reconcile.py" > "$WORK/reconcile.md" 2>&1 || true
head -1 "$WORK/reconcile.md" | sed 's/^/  /'

say "[3/6] フィクスチャを投入する"
# 測定は最低限のフィクスチャで足りる(--scale は既定 0)。
# デモ用の件数を積むのは環境構築時に別途 --scale を付けて実行する。
python3 "$HERE/fixtures.py" --out "$WEKO_API_INVENTORY_DIR/fixtures.json" \
        >"$WORK/fixtures.log" 2>&1
grep -E '^  (users|※|    )' "$WORK/fixtures.log" | sed 's/^/  /' || true

say "[4/6] 実測する"
if [ -n "$NOS" ]; then
  echo "$NOS" | tr ',' '\n' | sed '/^$/d' > "$WORK/targets.txt"
else
  "$HERE/_targets.py" "$FULL" "$PROFILE" > "$WORK/targets.txt"
fi
say "  対象: $(wc -l < "$WORK/targets.txt") 行"
python3 -u "$HERE/probe_ci.py" --only "$WORK/targets.txt" \
  --fixtures "$WEKO_API_INVENTORY_DIR/fixtures.json" \
  --web-container "$WEB_CONTAINER" \
  --base "$BASE" --host "$HOSTHDR" \
  --refresh-fixtures "$REFRESH" \
  $WRITES --out "$WORK/probe.json" > "$WORK/probe.log" 2>&1
grep -E '^測定' "$WORK/probe.log" | sed 's/^/  /'

say "[5/6] 台帳へ反映して派生列を再計算する"
python3 "$HERE/apply_probe_results.py" "$WORK/probe.json" --overwrite --keep-history \
  --date "$STAMP" | tail -3 | sed 's/^/  /'
python3 "$HERE/test_coverage.py"   >"$WORK/tc.log" 2>&1;  tail -1 "$WORK/tc.log" | sed 's/^/  /'
python3 "$HERE/prioritize.py"      >"$WORK/pr.log" 2>&1;  grep -E '^  (P[1-5]|整理|環境|対象外)' "$WORK/pr.log" | sed 's/^/  /'
python3 "$HERE/build_checklist.py" >"$WORK/bc.log" 2>&1;  head -1 "$WORK/bc.log" | sed 's/^/  /'

say "[6/6] ゲートを通してレポートを書く"
GATE=0
python3 "$HERE/reconcile.py" --gate > "$WORK/reconcile_after.md" 2>&1 || GATE=$?
"$HERE/_report.py" "$FULL" "$WORK/probe.json" "$WORK/reconcile_after.md" "$REPORT" \
  "$REV" "$HEAD_REV" "$STAMP" "${WRITES:-none}" "$PROFILE_HASH"
say ""
say "完了。ゲート: $([ $GATE -eq 0 ] && echo '✅ 通過' || echo "❌ 差分あり (exit $GATE)")"
say "作業ファイル: $WORK"
exit $GATE
