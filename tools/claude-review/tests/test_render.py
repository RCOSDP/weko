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

    エスケープされた `\\|` はセル区切りとして数えない。素朴な
    `line.split("|")` では区別できないため、テストの側でこのパーサを持つ。
    """
    cells, cur, i = [], [], 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if ch == "|":
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
