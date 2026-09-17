#!/bin/bash
# feature/jgss ブランチのPRレビュー・作業開始時に、
# ビルド手順書と既知の不具合（事象のみ）をすぐ確認できるようにする初期化スクリプト。
#
# 使い方:
#   ./scripts/pr_review_init.sh
set -euo pipefail

cd "$(dirname "$0")/.."

echo "================================================================"
echo " feature/jgss PRレビュー用 初期化ツール"
echo "================================================================"
echo

echo "---------------------------------------------------------------"
echo " [1/2] ビルド〜データリストア手順書: WEKO3_BUILD_RESTORE_MANUAL.md"
echo "---------------------------------------------------------------"
if [ -f "WEKO3_BUILD_RESTORE_MANUAL.md" ]; then
    sed -n '1,20p' WEKO3_BUILD_RESTORE_MANUAL.md
    echo
    echo "  ... (全文はリポジトリ直下の WEKO3_BUILD_RESTORE_MANUAL.md を参照)"
else
    echo "  WEKO3_BUILD_RESTORE_MANUAL.md が見つかりません。"
fi

echo
echo "---------------------------------------------------------------"
echo " [2/2] 既知の不具合（事象）: KNOWN_ISSUE_download_button_not_shown.md"
echo "---------------------------------------------------------------"
if [ -f "KNOWN_ISSUE_download_button_not_shown.md" ]; then
    cat KNOWN_ISSUE_download_button_not_shown.md
else
    echo "  KNOWN_ISSUE_download_button_not_shown.md が見つかりません。"
fi

echo
echo "================================================================"
echo " 初期化確認 完了"
echo "================================================================"
