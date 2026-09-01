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
