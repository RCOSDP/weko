"""render の出力形のテスト。"""
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
