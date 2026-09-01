"""mdsafe (esc/cell/fence) の直接テスト。

render.py / post_inline.py は Claude の出力（元は公開 PR に誰でも書ける
レビューコメント）を github-actions[bot] として public リポジトリに
貼り付ける。ここでは実装の共有先である mdsafe を直接検証する
（render.render() / post_inline.select() を経由した構造レベルの検証は
test_render.py / test_post_inline.py に残す）。
"""
import re

import mdsafe


# --- 基本のエスケープ -----------------------------------------------------


def test_esc_converts_angle_brackets():
    assert mdsafe.esc("<script>") == "&lt;script&gt;"


def test_esc_does_not_double_escape_ampersand():
    assert mdsafe.esc("&lt;already&gt;") == "&lt;already&gt;"


def test_esc_folds_newlines_to_space():
    assert mdsafe.esc("a\nb\r\nc\rd") == "a b c d"


def test_cell_escapes_backslash_and_pipe():
    assert mdsafe.cell("a|b") == "a\\|b"


def test_cell_backslash_pipe_pairing_is_order_safe():
    """入力に元からバックスラッシュがあっても | の直前のペアリングが崩れない。"""
    out = mdsafe.cell("x\\|y end")
    # 生成結果を GFM のペアリング規則で読み戻しても区切りにならない
    # （直前の連続バックスラッシュが奇数個ならエスケープ済み）。
    idx = out.index("|")
    j = idx - 1
    bs = 0
    while j >= 0 and out[j] == "\\":
        bs += 1
        j -= 1
    assert bs % 2 == 1


def test_fence_grows_to_contain_backticks():
    assert mdsafe.fence("plain") == "```"
    assert mdsafe.fence("```\nx\n```") == "````"
    assert mdsafe.fence("`````") == "``````"


def test_fence_does_not_alter_content():
    # fence() はフェンスの長さだけを返す。内容そのものには触れない。
    content = "```suggestion\nrm -rf /"
    f = mdsafe.fence(content)
    assert content in content  # sanity: 呼び出し側が内容をそのまま使う契約
    assert f == "````"


# --- 所見1/2: 行頭の構造記号を無害化する -----------------------------------
#
# _esc() は改行を空白に畳んで「1 文字の途中への注入」は防いでいたが、
# 呼び出し側の多くはこの戻り値をそのまま独立した行（段落・見出し・箇条書き）
# として出力する。畳み込んだ結果の**先頭**が構造記号なら、その記号は
# 行の 0 列目に来て単独でブロックを開いてしまう。


def test_leading_fence_marker_is_neutralized():
    """先頭のコードフェンス開始記号が無害化される（未閉フェンスでの以降の
    吸い込みを防ぐ）。"""
    out = mdsafe.esc("```\nrest hidden")
    assert not out.startswith("```")
    assert out.startswith("\\```") or out.lstrip().startswith("\\```")
    # 独立した行として見たときにフェンスを開かない
    assert not re.match(r"^ {0,3}`{3,}", out)


def test_leading_heading_marker_is_neutralized():
    """先頭の # が独立したトップレベル見出しを偽造できない。"""
    out = mdsafe.esc("## 🔍 Claude レビュー統合")
    assert not re.match(r"^ {0,3}#{1,6}(\s|$)", out)
    assert out.startswith("\\#")


def test_leading_blockquote_marker_is_neutralized():
    out = mdsafe.esc("> quoted")
    assert not re.match(r"^ {0,3}>", out)


def test_leading_bullet_markers_are_neutralized():
    for ch in ("-", "+", "*"):
        out = mdsafe.esc("%s item" % ch)
        assert not re.match(r"^ {0,3}[\-+*](\s|$)", out), out


def test_leading_bullet_marker_survives_two_space_indent():
    """箇条書きの入れ子表現（2 space インデント）でもフェンス開始記号として
    解釈されない。"""
    out = mdsafe.esc("  ```\nhidden")
    assert not re.match(r"^ {0,3}`{3,}", out)


def test_leading_thematic_break_markers_are_neutralized():
    for ch in ("~", "=", "_"):
        out = mdsafe.esc("%s%s%s%s%s rest" % (ch, ch, ch, ch, ch))
        assert not out.startswith(ch * 3), out


def test_leading_ordered_list_marker_is_neutralized():
    """番号付きリストは数字自体でなく区切り文字をエスケープする
    （CommonMark は \\1 のようなバックスラッシュ+数字を素通りする）。"""
    out = mdsafe.esc("1. rest hidden")
    assert not re.match(r"^ {0,3}\d+[.)](\s|$)", out)
    assert out.startswith("1\\.")


def test_leading_ordered_list_marker_with_paren_is_neutralized():
    out = mdsafe.esc("42) rest hidden")
    assert not re.match(r"^ {0,3}\d+[.)](\s|$)", out)
    assert out.startswith("42\\)")


def test_leading_digit_without_delimiter_is_untouched():
    """区切り文字が無ければリストマーカーにならないので触らない。"""
    assert mdsafe.esc("123 rest") == "123 rest"


def test_non_leading_structural_chars_are_untouched():
    """行頭でなければエスケープしない（文中の書式には触れない）。"""
    assert mdsafe.esc("safe text # not a heading") == "safe text # not a heading"
    assert mdsafe.esc("safe - not a bullet") == "safe - not a bullet"


def test_plain_text_is_unaffected():
    assert mdsafe.esc("普通の一文です。") == "普通の一文です。"


def test_leading_marker_after_newline_fold_is_neutralized():
    """改行を畳んだ結果として先頭に来た記号も無害化する
    （改行そのものは残っていないが、畳み込み後に行頭になるケース）。"""
    out = mdsafe.esc("\n# heading-like")
    assert not re.match(r"^ {0,3}#{1,6}(\s|$)", out)


def test_cell_also_neutralizes_leading_structural_char():
    """cell() は esc() を経由するため同じ保護を受ける。"""
    out = mdsafe.cell("```\nhidden")
    assert not re.match(r"^ {0,3}`{3,}", out)
