#!/usr/bin/env python3
"""render.py と post_inline.py が共有する Markdown 安全化ヘルパー。

title / source / reason / detail / evidence / note / replacement / why /
summary / file はすべて Claude の出力由来で、その元は公開 PR に誰でも書ける
レビューコメント。github-actions[bot] として public リポジトリに投稿される
ため、コードフェンスの外に置くものは必ずここを通す。

以前は render.py と post_inline.py がこのロジックをバイト同一のまま複製
していた。3 行程度のうちは許容できたが、行頭の構造記号を無害化する
セキュリティ修正を一箇所にまとめる必要が出たため、ここに集約する。
"""
from __future__ import annotations

import re


def esc(s) -> str:
    """コードフェンスの外に置く外部由来文字列をエスケープする。

    - `<`/`>` を実体参照に変換し、`<details>` などの HTML タグとしての解釈を
      防ぐ（`&` は変換しない — Claude が既に `&lt;` 等を出力していた場合の
      二重エスケープになるため）。
    - 改行（`\\r\\n`/`\\n`/`\\r`）を半角スペース 1 つに畳み込む。CommonMark は
      見出し・箇条書き・引用・区切り線の前に空行を要求しないため、改行を
      残すと偽の見出しや箇条書き、区切り線をトップレベルの文書構造に
      注入できてしまう（表示崩れではなく構造の偽装）。ここで扱う文字列は
      いずれも 1〜3 文の短い要約で、意図的な改行が失われても情報は落ちない。
      コードフェンスの中身（`replacement`/`evidence`）にはこの関数を通さない
      ——改行はコードの一部であり、保持する。
    """
    s = str(s)
    s = s.replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"\r\n|\r|\n", " ", s)


def cell(s) -> str:
    """Markdown 表のセルに置く文字列を作る。

    `esc()` に加えて、`\\`（バックスラッシュ）と `|` をエスケープする。
    GFM の行分割は `|` の直前に連続するバックスラッシュの個数の偶奇で
    「エスケープ済みか」を判定する（奇数個なら区切りではない）。そのため
    バックスラッシュを先に、パイプを後にエスケープする必要があり、ここでは
    1 回の正規表現でどちらの文字も置換することで順序を保証する
    （`s.replace("|", "\\|")` を先に呼ぶと、入力に既にあるバックスラッシュを
    2 本ペアと誤認させ、パイプが区切りとして復活する回帰を生む）。
    """
    return re.sub(r"([\\|])", r"\\\1", esc(s))


def fence(content: str) -> str:
    """内容を安全に囲めるコードフェンスを返す。

    中身に含まれるバッククォートの連続の最大長 + 1（最小 3）の長さにする
    （CommonMark の標準的なやり方）。内容そのものはエスケープしない —
    コードとして読ませるのが目的で、フェンス長で囲めば十分なため。

    post_inline.py で使う場合、フェンスの本数を増やしても直後に続く
    info string（`suggestion`）自体は変えないこと。GitHub が one-click
    apply の対象として解釈するのは info string がちょうど "suggestion"
    の場合のみなので、ここを崩してはならない。
    """
    runs = re.findall(r"`+", content)
    longest = max((len(r) for r in runs), default=0)
    return "`" * max(3, longest + 1)
