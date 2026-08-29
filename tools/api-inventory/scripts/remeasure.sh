#!/usr/bin/env bash
# 非推奨。measure.sh に統合した。
#
# 実測の入口を2つ持つと、バージョン間で条件がずれて比較できなくなる。
# 条件は $WEKO_API_INVENTORY_DIR/measure_profile.json に集約したので、
# 対象を絞りたいときも measure.sh を使うこと。
#
#   ./measure.sh              # 全行
#   ./measure.sh --nos 1,2,3  # 一部だけ
echo "remeasure.sh は measure.sh に統合しました。" >&2
echo "  ./measure.sh [--nos 1,2,3]" >&2
echo "  条件は \$WEKO_API_INVENTORY_DIR/measure_profile.json で指定します。" >&2
exit 2
