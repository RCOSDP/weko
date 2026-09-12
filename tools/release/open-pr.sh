#!/usr/bin/env bash
# PR を出す（public 側と、台帳を触ったなら private 側の 2 本）
#
#   tools/release/open-pr.sh --base develop_v2.1.0                 # 何をするか表示するだけ
#   tools/release/open-pr.sh --base develop_v2.1.0 --run           # 実際に PR を作る
#   tools/release/open-pr.sh --base develop_v2.1.0 --inventory --run   # private 側の台帳 PR も作る
#
# 既定は表示だけ（dry-run）。--run を付けたときだけ push と PR 作成を行う。
# 手順の説明は docs/OPERATIONS.md §3。ルールは docs/RULE.md。

set -uo pipefail

BASE=""; RUN=0; INVENTORY=0; TITLE=""
PUB_REPO="${WEKO_PUBLIC_REPO:-RCOSDP/weko}"
PRIV_REPO="${WEKO_PRIVATE_REPO:-RCOSDP/weko-secret}"

while [ $# -gt 0 ]; do
  case "$1" in
    --base)      BASE="${2-}"; shift 2 ;;
    --title)     TITLE="${2-}"; shift 2 ;;
    --inventory) INVENTORY=1; shift ;;
    --run)       RUN=1; shift ;;
    -h|--help)   sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "不明な引数: $1" >&2; exit 2 ;;
  esac
done

die() { echo "❌ $1" >&2; [ $# -gt 1 ] && echo "   → $2" >&2; exit 1; }
say() { echo "$*"; }
show() { printf '$'; printf ' %q' "$@"; printf '\n'; }
run() { show "$@"; [ "$RUN" = 1 ] && { "$@" || die "失敗: $*"; }; return 0; }

command -v gh >/dev/null 2>&1 || die "gh が無い" "RHEL/Rocky: sudo dnf install -y gh ／ Ubuntu: sudo apt install -y gh"
gh auth status >/dev/null 2>&1 || die "gh が未認証" "gh auth login"

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || die "git リポジトリの中にいない"
[ "$BRANCH" != "HEAD" ] || die "detached HEAD" "ブランチに切り替える"
[ -n "$BASE" ] || die "--base が要る" "例: --base develop_v2.1.0"
[ "$BRANCH" != "$BASE" ] || die "作業ブランチと base が同じ（$BRANCH）" "作業ブランチを切る"

[ -n "$TITLE" ] || TITLE=$(git log -1 --pretty=%s)

# public 側にデータが紛れていないか（§1）
leaked=$(git status --porcelain | awk '{print $NF}' | grep -E '(\.tsv|api_snapshot\.json|measure_report\.md|fixtures\.json)$' || true)
[ -z "$leaked" ] || die "public 側に台帳データがある：$(echo "$leaked" | tr '\n' ' ')" "public リポジトリにデータは置かない（docs/RULE.md §1）"

dirty=$(git status --porcelain | grep -v '^??' || true)
[ -z "$dirty" ] || die "コミットしていない変更がある" "先に commit する"

if [ "$INVENTORY" = 0 ]; then
  apidiff=$(git diff --name-only "origin/$BASE...HEAD" -- 'modules/**/views.py' 'modules/**/rest.py' 2>/dev/null | head -3)
  [ -z "$apidiff" ] || say "⚠️  API の定義ファイルに差分がある（$(echo "$apidiff" | tr '\n' ' ')…）。
   台帳の更新と private 側の PR（--inventory）が要らないか確認すること（docs/RULE.md §3-1）。
"
fi

say "== public 側の PR =="
say "  リポジトリ: $PUB_REPO"
say "  $BRANCH → $BASE"
say "  タイトル: $TITLE"
say

run git push -u origin "$BRANCH"

BODY_ARG=(--body "PR テンプレートのチェックリストを埋めること（docs/OPERATIONS.md §3）")
[ -f .github/pull_request_template.md ] && BODY_ARG=(--body-file .github/pull_request_template.md)

run gh pr create --repo "$PUB_REPO" --base "$BASE" --head "$BRANCH" --title "$TITLE" "${BODY_ARG[@]}"

if [ "$INVENTORY" = 1 ]; then
  PRIV="${WEKO_API_INVENTORY_DIR-}"
  [ -n "$PRIV" ] && [ -d "$PRIV" ] || die "WEKO_API_INVENTORY_DIR が未設定" "export WEKO_API_INVENTORY_DIR=~/weko-secret"
  PBRANCH=$(git -C "$PRIV" rev-parse --abbrev-ref HEAD)
  [ "$PBRANCH" = "$BRANCH" ] || die "private 側のブランチ名が違う（$PBRANCH）" \
    "同名にする（規則 2-1）: git -C \"\$WEKO_API_INVENTORY_DIR\" switch -c $BRANCH"
  pdirty=$(git -C "$PRIV" status --porcelain | grep -v '^??' || true)
  [ -z "$pdirty" ] || die "private 側にコミットしていない変更がある" "先に commit する"

  say
  say "== private 側（台帳）の PR =="
  say "  リポジトリ: $PRIV_REPO"
  say "  $BRANCH → $BASE"
  say
  run git -C "$PRIV" push -u origin "$BRANCH"
  run gh pr create --repo "$PRIV_REPO" --base "$BASE" --head "$BRANCH" \
    --title "台帳: $TITLE" \
    --body "$PUB_REPO の $BRANCH に対応する台帳更新。マージ順は問わない（同名ブランチを CI が見る）。"
fi

say
if [ "$RUN" = 1 ]; then
  say "次にやること:"
  say "  1. PR テンプレートのチェックボックスを埋める（特に「🤖 0. CI 自動チェック」）"
  say "  2. gh pr checks --watch   # Unit Tests / UI Tests / API Inventory Drift が緑になるまで"
  say "  3. API Inventory Drift のコメント冒頭で、採用された台帳ブランチ名を確認する"
  say "  4. レビュー指摘には全部反応を残す（docs/RULE.md §5-2）"
else
  say "（表示だけ。実行するなら --run を付ける）"
fi
