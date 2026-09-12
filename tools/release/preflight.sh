#!/usr/bin/env bash
# リリース／台帳更新を始める前の前提チェック（読み取りだけ。何も書き換えない）
#
#   tools/release/preflight.sh            # public 側のリポジトリルートで実行する
#   tools/release/preflight.sh --base develop_v2.1.0
#
# 手順は docs/OPERATIONS.md（§2 事前準備 / §3 PR / §4 リリース）。ルールは docs/RULE.md。

set -uo pipefail

BASE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --base) BASE="${2-}"; shift 2 ;;
    -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
    *) echo "不明な引数: $1" >&2; exit 2 ;;
  esac
done

if [ -t 1 ] && [ -z "${NO_COLOR-}" ]; then
  OK=$'\033[32m✅\033[0m'; NG=$'\033[31m❌\033[0m'; WARN=$'\033[33m⚠️\033[0m'; DIM=$'\033[2m'; RST=$'\033[0m'
else
  OK="[ OK ]"; NG="[ NG ]"; WARN="[警告]"; DIM=""; RST=""
fi

fail=0
warn=0
ok()   { printf '%s %s\n' "$OK" "$1"; }
ng()   { printf '%s %s\n    %s→ %s%s\n' "$NG" "$1" "$DIM" "$2" "$RST"; fail=$((fail+1)); }
caut() { printf '%s %s\n    %s→ %s%s\n' "$WARN" "$1" "$DIM" "$2" "$RST"; warn=$((warn+1)); }

echo "== 前提チェック =="

# --- 1. コマンド ---
if command -v git >/dev/null 2>&1; then ok "git がある"; else ng "git が無い" "パッケージを入れる"; fi

if command -v python3 >/dev/null 2>&1; then
  ok "python3 がある（$(python3 -V 2>&1)）"
else
  ng "python3 が無い" "台帳スクリプトが動かない。python3 を入れる"
fi

if command -v gh >/dev/null 2>&1; then
  ok "gh がある（$(gh --version 2>/dev/null | head -1)）"
  if gh auth status >/dev/null 2>&1; then
    ok "gh が認証済み（$(gh api user --jq .login 2>/dev/null || echo '?')）"
  else
    ng "gh が未認証" "gh auth login  （HTTPS / ブラウザ認証でよい）"
  fi
else
  ng "gh が無い" "RHEL/Rocky: sudo dnf install -y gh ／ Ubuntu: sudo apt install -y gh ／ 公式: https://github.com/cli/cli#installation"
fi

if command -v docker >/dev/null 2>&1; then ok "docker がある"; else ng "docker が無い" "実機を起動できない。docker を入れる"; fi

# --- 2. public 側リポジトリ ---
if git rev-parse --git-dir >/dev/null 2>&1; then
  BRANCH=$(git rev-parse --abbrev-ref HEAD)
  ok "public 側リポジトリにいる（ブランチ: $BRANCH）"
else
  ng "git リポジトリの中にいない" "WEKO3 のリポジトリルートで実行する"
  BRANCH=""
fi

if [ -f tools/api-inventory/scripts/snapshot.py ]; then
  ok "台帳ツールがこのブランチにある"
else
  ng "tools/api-inventory/ がこのブランチに無い" "git checkout <ツールのあるブランチ> -- tools/api-inventory .github/workflows/api-inventory-drift.yml"
fi

# public 側にデータが紛れていないか（§1 の禁止事項）
if [ -n "$BRANCH" ]; then
  leaked=$(git status --porcelain 2>/dev/null | awk '{print $NF}' \
            | grep -E '(\.tsv|api_snapshot\.json|measure_report\.md|fixtures\.json)$' || true)
  if [ -z "$leaked" ]; then
    ok "public 側に台帳データが出ていない"
  else
    ng "public 側に台帳データが出ている：$(echo "$leaked" | tr '\n' ' ')" "このリポジトリは public。置き場所は private 側（docs/RULE.md §1）"
  fi
fi

# --- 3. private 側（台帳とベースライン） ---
PRIV="${WEKO_API_INVENTORY_DIR-}"
if [ -z "$PRIV" ]; then
  ng "WEKO_API_INVENTORY_DIR が未設定" "git clone https://github.com/RCOSDP/weko-secret.git ~/weko-secret && export WEKO_API_INVENTORY_DIR=~/weko-secret"
elif [ ! -d "$PRIV" ]; then
  ng "WEKO_API_INVENTORY_DIR の先が無い（$PRIV）" "パスを確認する"
else
  ok "private 側がある（$PRIV）"
  for f in weko3_api_list_full.tsv api_snapshot.json; do
    if [ -f "$PRIV/$f" ]; then ok "  $f がある"; else ng "  $f が無い" "clone し直すか、置き場所を確認する"; fi
  done
  if git -C "$PRIV" rev-parse --git-dir >/dev/null 2>&1; then
    PBRANCH=$(git -C "$PRIV" rev-parse --abbrev-ref HEAD)
    if [ -n "$BRANCH" ] && [ "$PBRANCH" = "$BRANCH" ]; then
      ok "private 側のブランチが public と同名（$PBRANCH）"
    else
      caut "private 側のブランチが public と違う（public: ${BRANCH:-?} / private: $PBRANCH）" \
           "台帳を触るなら同名にする（規則 2-1）: git -C \"\$WEKO_API_INVENTORY_DIR\" switch -c ${BRANCH:-<branch>}"
    fi
  else
    ng "private 側が git リポジトリでない" "clone したものを指す"
  fi
fi

# --- 4. 実機 ---
WEB="${WEKO_WEB_CONTAINER:-weko-web-1}"
BASEURL="${WEKO_BASE_URL:-https://localhost:8443}"
HOSTHDR="${WEKO_HOST_HEADER:-weko3.example.org}"
if command -v docker >/dev/null 2>&1; then
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$WEB"; then
    ok "実機コンテナが動いている（$WEB）"
    code=$(curl -sk -o /dev/null -w '%{http_code}' -H "Host: $HOSTHDR" "$BASEURL/" 2>/dev/null || echo 000)
    if [ "$code" = "200" ]; then
      ok "トップページが 200（$BASEURL / Host: $HOSTHDR）"
    else
      caut "トップページが $code（200 でない）" "起動直後なら待つ。続くなら docker logs $WEB を見る"
    fi
  else
    ng "実機コンテナ $WEB が動いていない" "./install.sh で起動する（別名なら export WEKO_WEB_CONTAINER=...）"
  fi
fi

# --- 5. base ブランチ ---
if [ -n "$BASE" ] && [ -n "$BRANCH" ]; then
  if git rev-parse --verify "origin/$BASE" >/dev/null 2>&1; then
    ok "base ブランチ origin/$BASE がある"
  else
    ng "base ブランチ origin/$BASE が無い" "git fetch origin で取り直すか、--base を直す"
  fi
fi

echo
if [ "$fail" -gt 0 ]; then
  printf '%s %d 件そろっていない。上の「→」を片付けてから始めること。\n' "$NG" "$fail"
  exit 1
fi
if [ "$warn" -gt 0 ]; then
  printf '%s 警告 %d 件。意味を分かったうえで進むこと。\n' "$WARN" "$warn"
fi
printf '%s 前提はそろっている。次は docs/OPERATIONS.md §3（PR）／§4（リリース）へ。\n' "$OK"
