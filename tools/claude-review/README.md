# Claude PR レビュー

`.github/workflows/claude-pr-review.yml` から呼ばれるスクリプト群。
PR に付いている他レビュー(CodeRabbit・人間)を集めて Claude に裁定させ、
結果を 1 枚の集約コメントと inline suggestion として投稿する。

## 実行順

1. `collect_reviews.py` — GraphQL でレビューを集める → `reviews.json`
2. `build_input.py` — 差分と `reviews.json` を Claude への標準入力にまとめる
3. `claude -p "$(cat prompt.md)" < claude_input.txt` を `REVIEW_PASSES` 回
4. `aggregate.py` — `raw_*.json` を和集合にまとめる → `findings.json`
5. `render.py` — `findings.json` → `review.md`
6. `post_inline.py` — 条件を満たす修正案を inline suggestion として投稿

## テスト

    pip install pytest
    python3 -m pytest tools/claude-review/tests -q

fixture は PR #1905 の実データ。CodeRabbit の指摘、人間の反論、
解決済み/未解決スレッドがすべて含まれる。
