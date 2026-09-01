"""aggregate の和集合・検証・判定衝突のテスト。"""
import json

import aggregate


def raw(payload, cost=0.01):
    """claude -p --output-format json の出力を模す。"""
    return {"result": "前置き\n" + json.dumps(payload, ensure_ascii=False),
            "total_cost_usd": cost}


def adj(**kw):
    base = {"source": "coderabbitai", "thread_id": "T_1", "file": "a.py",
            "line": 10, "title": "x", "verdict": "valid", "reason": "r",
            "verified": "a.py:1-20", "severity": "high",
            "fix": {"kind": "none"}}
    base.update(kw)
    return base


def test_union_counts_hits():
    """1 回でも挙がったものは残し、何回挙がったかを数える。"""
    out = aggregate.aggregate([
        raw({"adjudications": [adj()], "own_findings": [], "unverified": [],
             "summary": "s"}),
        raw({"adjudications": [adj()], "own_findings": [], "unverified": [],
             "summary": "s"}),
    ])
    assert out["passes"] == 2
    assert len(out["adjudications"]) == 1
    assert out["adjudications"][0]["_hits"] == 2
    assert out["adjudications"][0]["_split"] is False


def test_conflicting_verdict_takes_the_heavier():
    """判定が割れたら安全側(重いほう)を採り、割れたことを残す。"""
    out = aggregate.aggregate([
        raw({"adjudications": [adj(verdict="false_positive")],
             "own_findings": [], "unverified": [], "summary": ""}),
        raw({"adjudications": [adj(verdict="valid")],
             "own_findings": [], "unverified": [], "summary": ""}),
    ])
    a = out["adjudications"][0]
    assert a["verdict"] == "valid"
    assert a["_split"] is True
    assert sorted(a["_verdicts"]) == ["false_positive", "valid"]


def test_unknown_verdict_is_dropped():
    """列挙外の値は捨てる。モデル出力をそのまま信用しない。"""
    out = aggregate.aggregate([
        raw({"adjudications": [adj(verdict="probably_ok")],
             "own_findings": [], "unverified": [], "summary": ""})])
    assert out["adjudications"] == []


def test_valid_without_verified_falls_back_to_needs_context():
    """裏取りの記録が無い valid は格下げする。"""
    out = aggregate.aggregate([
        raw({"adjudications": [adj(verified="  ")],
             "own_findings": [], "unverified": [], "summary": ""})])
    assert out["adjudications"][0]["verdict"] == "needs_context"


def test_broken_suggestion_becomes_none():
    """行番号が壊れた suggestion は投稿対象から外す。"""
    bad = [{"kind": "suggestion", "file": "a.py", "start_line": 9,
            "end_line": 3, "replacement": "x"},
           {"kind": "suggestion", "file": "", "start_line": 1,
            "end_line": 2, "replacement": "x"},
           {"kind": "suggestion", "file": "a.py", "start_line": 1,
            "end_line": 2, "replacement": None}]
    for fx in bad:
        out = aggregate.aggregate([
            raw({"adjudications": [adj(fix=fx)], "own_findings": [],
                 "unverified": [], "summary": ""})])
        assert out["adjudications"][0]["fix"]["kind"] == "none", fx


def test_own_findings_keyed_by_file_line_title():
    out = aggregate.aggregate([
        raw({"adjudications": [], "unverified": [], "summary": "",
             "own_findings": [{"file": "b.py", "line": 3, "severity": "high",
                               "title": "認可 が 抜けている", "detail": "d",
                               "evidence": "e", "verified": "b.py:1-9",
                               "fix": {"kind": "none"}}]}),
        raw({"adjudications": [], "unverified": [], "summary": "",
             "own_findings": [{"file": "b.py", "line": 3, "severity": "high",
                               "title": "認可が抜けている", "detail": "d",
                               "evidence": "e", "verified": "b.py:1-9",
                               "fix": {"kind": "none"}}]}),
    ])
    assert len(out["own_findings"]) == 1        # 空白の揺れを吸収する
    assert out["own_findings"][0]["_hits"] == 2


def test_unparsable_pass_is_skipped_not_fatal():
    """1 パスが壊れても残りで集計する。"""
    out = aggregate.aggregate([
        {"result": "JSON ではない"},
        raw({"adjudications": [adj()], "own_findings": [], "unverified": [],
             "summary": "s"}),
    ])
    assert out["passes"] == 2
    assert len(out["adjudications"]) == 1


def test_cost_is_summed():
    out = aggregate.aggregate([
        raw({"adjudications": [], "own_findings": [], "unverified": [],
             "summary": ""}, cost=0.02),
        raw({"adjudications": [], "own_findings": [], "unverified": [],
             "summary": ""}, cost=0.03)])
    assert abs(out["cost"] - 0.05) < 1e-9


def test_within_pass_duplicate_counts_as_one_hit():
    """1 パスの adjudications に同じキーの項目が 2 つあっても _hits == 1。"""
    out = aggregate.aggregate([
        raw({"adjudications": [adj(), adj()],
             "own_findings": [], "unverified": [], "summary": ""}),
    ])
    assert out["passes"] == 1
    assert len(out["adjudications"]) == 1
    assert out["adjudications"][0]["_hits"] == 1


def test_within_pass_duplicate_own_findings_counts_as_one_hit():
    """1 パスの own_findings に同じキーの項目が 2 つあっても _hits == 1。"""
    out = aggregate.aggregate([
        raw({"adjudications": [],
             "own_findings": [
                 {"file": "b.py", "line": 3, "severity": "high",
                  "title": "認可が抜けている", "detail": "d",
                  "evidence": "e", "verified": "b.py:1-9",
                  "fix": {"kind": "none"}},
                 {"file": "b.py", "line": 3, "severity": "high",
                  "title": "認可が抜けている", "detail": "d",
                  "evidence": "e", "verified": "b.py:1-9",
                  "fix": {"kind": "none"}}
             ],
             "unverified": [], "summary": ""}),
    ])
    assert len(out["own_findings"]) == 1
    assert out["own_findings"][0]["_hits"] == 1


def test_within_pass_verdict_conflict_takes_heavier():
    """1 パスの中で同じキーが違う verdict を持つときは重い方を採る。"""
    out = aggregate.aggregate([
        raw({"adjudications": [
                 adj(verdict="false_positive"),
                 adj(verdict="valid")
             ],
             "own_findings": [], "unverified": [], "summary": ""}),
    ])
    assert len(out["adjudications"]) == 1
    a = out["adjudications"][0]
    assert a["verdict"] == "valid"
    assert a["_hits"] == 1
    assert len(a["_verdicts"]) == 1
    assert a["_verdicts"][0] == "valid"


def test_cross_pass_duplicate_counts_as_two_hits():
    """2 パスそれぞれが同じ項目を 1 つずつ出したら _hits == 2（従来どおり）。"""
    out = aggregate.aggregate([
        raw({"adjudications": [adj()], "own_findings": [], "unverified": [],
             "summary": ""}),
        raw({"adjudications": [adj()], "own_findings": [], "unverified": [],
             "summary": ""}),
    ])
    assert out["passes"] == 2
    assert len(out["adjudications"]) == 1
    assert out["adjudications"][0]["_hits"] == 2


def test_line_field_validation_converts_to_int():
    """line フィールドは正の整数に変換される。"""
    out = aggregate.aggregate([
        raw({"adjudications": [adj(line="12")], "own_findings": [],
             "unverified": [], "summary": ""}),
    ])
    assert out["adjudications"][0]["line"] == 12


def test_line_field_validation_invalid_becomes_none():
    """line が無効な値（dict, 負数, 0, 非数字文字列）なら None になり項目は残る。"""
    invalid_lines = [
        {"start": 1, "end": 2},  # dict
        -5,                       # 負数
        0,                        # 0
        "abc",                    # 非数字文字列
        None,                     # None
    ]
    for line_val in invalid_lines:
        out = aggregate.aggregate([
            raw({"adjudications": [adj(line=line_val)], "own_findings": [],
                 "unverified": [], "summary": ""}),
        ])
        assert len(out["adjudications"]) == 1, f"line={line_val} で項目が捨てられた"
        assert out["adjudications"][0]["line"] is None, f"line={line_val} が None に変換されていない"


def test_own_findings_line_validation():
    """own_findings の line も同じく検証される。"""
    out = aggregate.aggregate([
        raw({"adjudications": [],
             "own_findings": [{"file": "b.py", "line": {"a": 1}, "severity": "high",
                               "title": "x", "detail": "d", "evidence": "e",
                               "verified": "b.py:1-9", "fix": {"kind": "none"}}],
             "unverified": [], "summary": ""}),
    ])
    assert len(out["own_findings"]) == 1
    assert out["own_findings"][0]["line"] is None


def test_unverified_line_validation():
    """unverified の line も同じく検証される。"""
    out = aggregate.aggregate([
        raw({"adjudications": [], "own_findings": [],
             "unverified": [{"file": "b.py", "line": -10, "title": "x",
                             "detail": "d", "why": "w"}],
             "summary": ""}),
    ])
    assert len(out["unverified"]) == 1
    assert out["unverified"][0]["line"] is None
