#!/usr/bin/env bash
# 未測定/指定範囲のエンドポイントを実機で測り直し、台帳に反映する。
#
#   ./remeasure.sh                 # dynamic_verified が空の P1/P2 を測る
#   ./remeasure.sh --all-unmeasured  # 未測定を全件
#   ./remeasure.sh --nos 607,618     # no を直接指定
#   ./remeasure.sh --allow-writes    # 書き込み系も測る(実機データが変わる)
#
# 前提: $WEKO_API_INVENTORY_DIR(台帳) と WEKO スタックが起動していること。
#
# 既定は **読み取り専用**(GET/HEAD のみ)で副作用がない。
# 書き込み系まで測るには --allow-writes を明示すること。実機のデータ
# (著者DB・サイト情報・ワークフローの状態など)が書き換わるため、
# 使い捨て環境で回すか、終了後に環境を作り直すこと。
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${WEKO_API_INVENTORY_DIR:?台帳の場所を指定してください (export WEKO_API_INVENTORY_DIR=...)}"
: "${WEKO_ROOT:=$(cd "$HERE/../../.." && pwd)}"
export WEKO_ROOT
WORK="${WORK:-$(mktemp -d)}"
mkdir -p "$WORK"
TSV="$WEKO_API_INVENTORY_DIR/weko3_api_list.tsv"

SCOPE=p12; WRITES=""; NOS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --all-unmeasured) SCOPE=all ;;
    --nos) NOS="$2"; SCOPE=nos; shift ;;
    --allow-writes) WRITES=--allow-writes ;;
    *) echo "不明な引数: $1" >&2; exit 2 ;;
  esac; shift
done

echo "== 1. フィクスチャ投入 =="
python3 "$HERE/fixtures.py" --out "$WORK/fixtures.json"

echo "== 2. 対象の抽出 =="
case "$SCOPE" in
  p12) awk -F'\t' 'NR>1 && $25 ~ /^P[12]$/ && $16=="-" {print $1}' "$TSV" > "$WORK/nos.txt" ;;
  all) awk -F'\t' 'NR>1 && $16=="-" {print $1}' "$TSV" > "$WORK/nos.txt" ;;
  nos) tr ',' '\n' <<< "$NOS" > "$WORK/nos.txt" ;;
esac
echo "  対象: $(wc -l < "$WORK/nos.txt") 件"
[ -s "$WORK/nos.txt" ] || { echo "  対象なし。終了"; exit 0; }

echo "== 3. 実測 =="
python3 "$HERE/probe_ci.py" --fixtures "$WORK/fixtures.json" \
  --only "$WORK/nos.txt" $WRITES --out "$WORK/probe.json" | tail -20

echo "== 4. 台帳へ反映 =="
python3 "$HERE/apply_probe_results.py" "$WORK/probe.json"

echo "== 5. 再計算 =="
python3 "$HERE/prioritize.py" | tail -12
python3 "$HERE/build_checklist.py" > /dev/null
python3 "$HERE/reconcile.py" --gate > /dev/null && echo "  reconcile: 差分なし"

echo
echo "成果物: $WORK/probe.json (明細)"
if [ -n "$WRITES" ]; then
  echo "※ 書き込み系を実測したため実機のデータが変わっています。fixtures.py は冪等ですが"
  echo "   著者DB等の副作用は残ります。クリーンな状態が要るなら ./install.sh で作り直してください。"
fi
