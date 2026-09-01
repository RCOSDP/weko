"""render の出力形のテスト。"""
import re

import render


BASE = {"passes": 2, "cost": 0.12, "summary": "S3 の宛先検証を追加してください。",
        "adjudications": [], "own_findings": [], "unverified": []}


def adj(**kw):
    base = {"source": "coderabbitai", "thread_id": "T1",
            "file": "views.py", "line": 1568, "title": "例外文字列の漏洩",
            "verdict": "valid", "reason": "実コードで確認した",
            "verified": "views.py:1560-1580", "severity": "high",
            "fix": {"kind": "none"}, "_hits": 2, "_verdicts": ["valid"] * 2,
            "_split": False}
    base.update(kw)
    return base


def test_empty_result_is_stated_plainly():
    out = render.render(BASE, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert "指摘はありません" in out
    assert "<!-- claude-pr-review -->" not in out   # 目印はワークフロー側で付ける


def test_table_lists_source_and_verdict():
    d = dict(BASE, adjudications=[adj(), adj(thread_id="T2",
             verdict="false_positive", title="db fixture の scope")])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert "| # | 出所 | 箇所 | 指摘 | 判定 | 修正案 |" in out
    assert "coderabbitai" in out
    assert "✅ 妥当" in out
    assert "❌ 誤検知" in out


def test_split_verdict_is_flagged():
    """判定が割れたことを隠さない。"""
    d = dict(BASE, adjudications=[adj(_split=True,
             _verdicts=["valid", "false_positive"])])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert "判定が割れ" in out


def test_dropped_threads_are_reported():
    """容量で落とした件数を必ず出す。黙って落とさない。"""
    out = render.render(BASE, {"dropped_threads": 3, "dropped_other": 1}, "sonnet")
    assert "3" in out and "省略" in out


def test_needs_context_and_unverified_are_folded():
    d = dict(BASE,
             adjudications=[adj(verdict="needs_context")],
             unverified=[{"file": "a.py", "line": 1, "title": "t",
                          "detail": "d", "why": "w", "_hits": 1}])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert out.count("<details>") >= 2


def test_suggestion_fix_shows_plain_ari_when_inline_disabled():
    """所見4: POST_INLINE_SUGGESTIONS=false のとき、'あり(inline)' を出さない。

    render.py は POST_INLINE_SUGGESTIONS を知らないため、既定
    (inline_enabled 省略 = False)では実際には投稿されない inline
    suggestion を「あり(inline)」と誤って告知してはいけない。
    """
    d = dict(BASE, adjudications=[adj(fix={"kind": "suggestion", "file": "a.py",
             "start_line": 1, "end_line": 2, "replacement": "x", "note": ""})])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert "あり(inline)" not in out
    assert "| あり |" in out


def test_suggestion_fix_shows_inline_label_when_inline_enabled():
    d = dict(BASE, adjudications=[adj(fix={"kind": "suggestion", "file": "a.py",
             "start_line": 1, "end_line": 2, "replacement": "x", "note": ""})])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet",
                        inline_enabled=True)
    assert "| あり(inline) |" in out


def test_own_finding_suggestion_fix_cell_respects_inline_enabled():
    own = {"file": "a.py", "line": 1, "title": "t", "detail": "d",
           "severity": "high",
           "fix": {"kind": "suggestion", "file": "a.py", "start_line": 1,
                   "end_line": 2, "replacement": "x", "note": ""},
           "evidence": "", "verified": "", "_hits": 1}
    d = dict(BASE, own_findings=[own])
    out_default = render.render(d, {"dropped_threads": 0, "dropped_other": 0},
                                "sonnet")
    assert "あり(inline)" not in out_default
    out_enabled = render.render(d, {"dropped_threads": 0, "dropped_other": 0},
                                "sonnet", inline_enabled=True)
    assert "あり(inline)" in out_enabled


def test_footer_has_model_passes_cost():
    out = render.render(BASE, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert "sonnet" in out and "2 回" in out and "0.12" in out


def test_loc_with_valid_line_renders_file_and_line():
    """line が正当な int のときは file:line で表示する。"""
    assert render._loc({"file": "views.py", "line": 1568}) == "`views.py:1568`"


def test_loc_with_none_line_renders_file_only():
    """aggregate.py は不正な行番号を line=None にして件数を残す。
    render は file だけを表示し、末尾のコロンを付けない。"""
    assert render._loc({"file": "views.py", "line": None}) == "`views.py`"
    assert render._loc({"file": "views.py"}) == "`views.py`"


# --- Markdown 注入対策 ---------------------------------------------------
#
# title / source / reason / detail / evidence / note / replacement / why /
# summary はすべて Claude の出力由来で、その元は公開 PR に誰でも書けるレビュー
# コメント。この節のテストは「部分文字列の有無」ではなく、表の列数や
# <details>/コードフェンスの対応が崩れていないかという「構造」で検証する。


def _split_cells(line):
    """GFM の表の 1 行をセルに分割する（検証用の簡易パーサ）。

    GFM の実際のペアリング規則に合わせる: `|` の直前に連続する
    バックスラッシュの個数を数え、奇数ならエスケープ済み（セル区切りでは
    ない）、偶数（0 を含む）ならセル区切りとして扱う。単に「直前の 1 文字が
    `\\` か」だけを見る素朴な実装では、入力に元からバックスラッシュが
    含まれる場合（`x\\|y` など）にペアリングを誤り、レンダラの実際の
    挙動と食い違う。
    """
    cells, cur, i = [], [], 0
    while i < len(line):
        ch = line[i]
        if ch == "|":
            bs = 0
            j = len(cur) - 1
            while j >= 0 and cur[j] == "\\":
                bs += 1
                j -= 1
            if bs % 2 == 1:
                cur.append(ch)
            else:
                cells.append("".join(cur))
                cur = []
            i += 1
            continue
        cur.append(ch)
        i += 1
    cells.append("".join(cur))
    return cells


def test_table_pipe_in_title_does_not_shift_columns():
    """title に | が入っても表の列がずれない。"""
    d = dict(BASE, adjudications=[adj(title="a | b | c")])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    header = next(l for l in out.splitlines() if l.startswith("| # |"))
    row = next(l for l in out.splitlines() if l.startswith("| 1 |"))
    assert len(_split_cells(row)) == len(_split_cells(header))


def test_table_newline_in_title_stays_one_line():
    """title に改行が入っても表がその行で終わらない。"""
    d = dict(BASE, adjudications=[adj(title="line1\nline2")])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    header = next(l for l in out.splitlines() if l.startswith("| # |"))
    rows = [l for l in out.splitlines() if l.startswith("| 1 |")]
    assert len(rows) == 1
    assert len(_split_cells(rows[0])) == len(_split_cells(header))


def test_details_close_tag_in_title_cannot_escape_the_fold():
    """title に </details> が入っても畳みから早期脱出できない。"""
    d = dict(BASE, adjudications=[adj(verdict="needs_context",
             title="逃げる</details>その他は全部見える")])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert out.count("<details>") == out.count("</details>")


def test_fence_grows_to_contain_backticks_in_replacement():
    """修正案の中身に ``` が入っていても、そのフェンスの外に出られない。"""
    payload = "safe\n```\nmalicious markdown here\n```\nend"
    d = dict(BASE, adjudications=[adj(fix={"kind": "suggestion", "file": "a.py",
             "start_line": 1, "end_line": 2, "replacement": payload, "note": ""})])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    m = re.search(r"^(`{4,})\n(.*?)\n\1$", out, re.MULTILINE | re.DOTALL)
    assert m is not None
    assert m.group(2) == payload


def test_fence_grows_to_contain_backticks_in_evidence():
    """own_findings の evidence に ``` が入っていても外に出られない。"""
    payload = "```\nrm -rf /\n```"
    own = {"file": "a.py", "line": 1, "title": "t", "detail": "d",
           "severity": "high", "fix": {"kind": "none"},
           "evidence": payload, "verified": "", "_hits": 1}
    d = dict(BASE, own_findings=[own])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    m = re.search(r"^(`{4,})\n(.*?)\n\1$", out, re.MULTILINE | re.DOTALL)
    assert m is not None
    assert m.group(2) == payload


def test_plain_input_is_rendered_unchanged():
    """特殊文字を含まない通常の入力では、エスケープの痕跡が出力に現れない。"""
    out = render.render(BASE, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert "&lt;" not in out and "&gt;" not in out
    assert "\\|" not in out


# --- ラウンド 2: バックスラッシュのペアリング回帰 + 改行によるブロック注入 ---
#
# 所見1の初回修正（`.replace("|", "\\|")` を先に適用）は、入力に元から
# バックスラッシュが含まれる場合（Windows パス、正規表現、エスケープ済み
# JSON など）に GFM のペアリング規則で「区切り」に戻ってしまう回帰を
# 生んでいた。また `_esc()` が改行を畳んでいなかったため、見出し・箇条書き
# のトップレベル文書構造を偽装できた（<details> の中には限らない）。


def test_table_backslash_pipe_pairing_does_not_shift_columns():
    """バックスラッシュ+パイプが GFM のペアリング規則どおり 1 セルに収まる。

    以前の実装（パイプを先にエスケープしてからバックスラッシュに触れない）
    では、この入力が偶数個のバックスラッシュに見えてしまい、区切りとして
    復活していた。
    """
    d = dict(BASE, adjudications=[adj(title="path x\\|y end")])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    header = next(l for l in out.splitlines() if l.startswith("| # |"))
    row = next(l for l in out.splitlines() if l.startswith("| 1 |"))
    assert len(_split_cells(row)) == len(_split_cells(header))


def test_table_lone_backslashes_do_not_shift_columns():
    """パイプを伴わない素のバックスラッシュ（Windows パスなど）でも列数が変わらない。"""
    d = dict(BASE, adjudications=[adj(title="C:\\path\\to\\file")])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    header = next(l for l in out.splitlines() if l.startswith("| # |"))
    row = next(l for l in out.splitlines() if l.startswith("| 1 |"))
    assert len(_split_cells(row)) == len(_split_cells(header))


def test_heading_title_newline_cannot_inject_a_fake_heading():
    """見出しに使われる title の改行 + `#` が、独立した見出し行を作らない。"""
    d = dict(BASE, adjudications=[adj(verdict="valid",
             title="evil\n# 偽の見出し")])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert not any(l.startswith("# 偽の見出し") for l in out.splitlines())


def test_summary_paragraph_newline_cannot_inject_a_fake_heading():
    """段落として出る summary の改行 + `#` が、独立した見出し行を作らない。"""
    d = dict(BASE, summary="ok\n## 偽のセクション")
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert not any(l.startswith("## 偽のセクション") for l in out.splitlines())


def test_ctx_reason_newline_cannot_inject_a_fake_bullet():
    """要文脈の reason の改行 + `-` が、独立した箇条書き行を作らない。"""
    d = dict(BASE, adjudications=[adj(verdict="needs_context",
             reason="a\n- 偽の項目")])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert not any(l.startswith("- 偽の項目") for l in out.splitlines())


# --- 所見1: 行頭に来た構造記号でブロックを開けない ------------------------
#
# _esc() は改行を畳むだけでは足りない。畳んだ結果の文字列そのものが
# 独立した行として出力される呼び出し箇所（reason / detail / note の
# 段落、ctx/unverified の箇条書き）では、先頭の 1 文字がそのまま列 0 に
# 来てブロックを開いてしまう。


def test_reason_paragraph_leading_fence_cannot_open_an_unclosed_block():
    """reason 自体が先頭 ``` のときも、独立したフェンス開始行にならない。

    改行を畳むだけの旧実装では "```\\nrest hidden" が "``` rest hidden" に
    なり、その行自体が未閉のコードフェンスとして以降をすべて呑み込んで
    いた（このケースでは末尾の <sub> 注記まで消える）。
    """
    d = dict(BASE, adjudications=[adj(verdict="valid",
             reason="```\nrest hidden")])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    lines = out.splitlines()
    assert not any(re.match(r"^ {0,3}`{3,}", l) for l in lines)
    assert "rest hidden" in out
    assert "<sub>" in out          # 呑み込まれず末尾の注記まで残っている


def test_own_finding_detail_leading_heading_cannot_forge_a_section():
    """detail 自体が偽のトップレベル見出しでも、独立した見出し行にならない。

    render() 自身が出す本物の見出し（"## 🔍 Claude レビュー統合"）以外に
    見出し行が増えないことを確認する。
    """
    own = {"file": "a.py", "line": 1, "title": "t",
           "detail": "## 🔍 Claude レビュー統合",
           "severity": "high", "fix": {"kind": "none"},
           "evidence": "", "verified": "", "_hits": 1}
    d = dict(BASE, own_findings=[own])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    headings = [l for l in out.splitlines()
                if re.match(r"^ {0,3}#{1,6}(\s|$)", l)]
    # 本物の見出しは冒頭のタイトルと own_findings の項目見出しの 2 本だけ。
    # 偽の "## 🔍 Claude レビュー統合" が detail から独立した見出しとして
    # 追加されていないこと。
    assert headings == ["## 🔍 Claude レビュー統合",
                        "### 1. 🔴 [高] t（Claude の追加指摘）"]


def test_fix_note_leading_marker_cannot_open_a_block():
    d = dict(BASE, adjudications=[adj(fix={
        "kind": "description", "note": "```\nrest hidden"})])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert not any(re.match(r"^ {0,3}`{3,}", l) for l in out.splitlines())
    assert "rest hidden" in out
    assert "<sub>" in out


def test_ctx_reason_leading_marker_cannot_open_a_block():
    d = dict(BASE, adjudications=[adj(verdict="needs_context",
             reason="# 偽の見出し")])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert not any(l.startswith("# 偽の見出し") for l in out.splitlines())
    headings = [l for l in out.splitlines()
                if re.match(r"^ {0,3}#{1,6}(\s|$)", l)]
    assert headings == ["## 🔍 Claude レビュー統合"]


def test_unverified_detail_and_why_leading_marker_cannot_open_a_block():
    d = dict(BASE, unverified=[{"file": "a.py", "line": 1, "title": "t",
             "detail": "```\nhidden", "why": "- 偽の項目", "_hits": 1}])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    lines = out.splitlines()
    assert not any(re.match(r"^ {0,3}`{3,}", l) for l in lines)
    assert not any(l.startswith("- 偽の項目") for l in lines)
    assert "<sub>" in out


# --- 所見12: @ メンションを作らない -----------------------------------------
#
# 12-a: render.py 自身が "出所 @%s" という形で literal な '@' を組み立てて
#       いた。source が普通に "coderabbitai" だけの場合でも、これは常に
#       @coderabbitai という本物のメンションになり、CodeRabbit を呼び出す
#       実在のコマンド形式にもなる。テンプレート自身から '@' を削る。
# 12-b: source/title などに埋め込まれた '@' も esc()/cell() 経由で
#       ゼロ幅スペースにより無害化される(test_mdsafe.py 側で検証済み)。
#       ここでは render() の出力全体としてメンションが残らないことを見る。


def test_source_label_has_no_leading_at_sign():
    """出所ラベルは "@coderabbitai" ではなく "coderabbitai" と表示する。"""
    d = dict(BASE, adjudications=[adj(source="coderabbitai")])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert "／ 出所 coderabbitai" in out
    assert "@coderabbitai" not in out


def test_ctx_bullet_source_has_no_leading_at_sign():
    d = dict(BASE, adjudications=[adj(verdict="needs_context",
             source="coderabbitai")])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert "@coderabbitai" not in out


def test_source_field_command_string_cannot_reach_coderabbit():
    """所見12-b: source に埋め込まれた 'coderabbitai full review' が
    そのまま '@coderabbitai full review' という実在コマンドとして
    公開コメントに出ない。"""
    d = dict(BASE, adjudications=[adj(source="coderabbitai full review")])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert "@coderabbitai full review" not in out


def test_title_at_mention_cannot_notify_an_arbitrary_user():
    d = dict(BASE, adjudications=[adj(title="@someone please look")])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert "@someone" not in out


def test_fence_content_newlines_are_preserved():
    """コードフェンスの中身の改行は畳み込まれず、そのまま残る。"""
    payload = "line1\nline2\nline3"
    d = dict(BASE, adjudications=[adj(fix={"kind": "suggestion", "file": "a.py",
             "start_line": 1, "end_line": 3, "replacement": payload,
             "note": ""})])
    out = render.render(d, {"dropped_threads": 0, "dropped_other": 0}, "sonnet")
    assert payload in out
