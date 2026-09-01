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
    """1 パスが壊れても残りで集計する。

    壊れたパスは _hits/passes の分母に数えない(所見3)。数えると、
    実際には 1 パスしか結果を出していないのに「2 パス中 1 パスで検出」
    という誤った分母を表示することになる。
    """
    out = aggregate.aggregate([
        {"result": "JSON ではない"},
        raw({"adjudications": [adj()], "own_findings": [], "unverified": [],
             "summary": "s"}),
    ])
    assert out["passes"] == 1
    assert len(out["adjudications"]) == 1
    assert out["adjudications"][0]["_hits"] == 1


def test_error_envelope_pass_does_not_inflate_passes_denominator():
    """所見3: JSON を含まない(エラー)パスは passes の分母に数えない。

    1 良好パス + 1 エラーパスなら passes == 1 ・ _hits == 1 になり、
    render.py の（1/2 パス）のような誤った注記が付かないことを保証する。
    """
    out = aggregate.aggregate([
        raw({"adjudications": [adj()], "own_findings": [], "unverified": [],
             "summary": "s"}),
        {"result": "エラー: 実行に失敗しました", "total_cost_usd": 0.01},
    ])
    assert out["passes"] == 1
    assert out["adjudications"][0]["_hits"] == 1


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


def test_invalid_lines_do_not_collide():
    """異なる不正な line 値は衝突しない。raw が違えば別鍵になる。"""
    out = aggregate.aggregate([
        raw({"adjudications": [],
             "own_findings": [
                 {"file": "b.py", "line": -5, "severity": "high",
                  "title": "SQL injection", "detail": "detail A",
                  "evidence": "e", "verified": "b.py:1-9",
                  "fix": {"kind": "none"}},
                 {"file": "b.py", "line": "garbage", "severity": "high",
                  "title": "SQL injection", "detail": "detail B",
                  "evidence": "e", "verified": "b.py:1-9",
                  "fix": {"kind": "none"}}
             ],
             "unverified": [], "summary": ""}),
    ])
    assert len(out["own_findings"]) == 2, "異なる不正な line 値が衝突している"
    details = {item["detail"] for item in out["own_findings"]}
    assert details == {"detail A", "detail B"}


def test_same_invalid_lines_merge():
    """同じ不正な line 値なら併合される。"""
    out = aggregate.aggregate([
        raw({"adjudications": [],
             "own_findings": [{"file": "b.py", "line": -5, "severity": "high",
                               "title": "issue", "detail": "d",
                               "evidence": "e", "verified": "b.py:1-9",
                               "fix": {"kind": "none"}}],
             "unverified": [], "summary": ""}),
        raw({"adjudications": [],
             "own_findings": [{"file": "b.py", "line": -5, "severity": "high",
                               "title": "issue", "detail": "d",
                               "evidence": "e", "verified": "b.py:1-9",
                               "fix": {"kind": "none"}}],
             "unverified": [], "summary": ""}),
    ])
    assert len(out["own_findings"]) == 1
    assert out["own_findings"][0]["_hits"] == 2


def test_valid_and_invalid_lines_do_not_collide():
    """正当な行と不正な行は絶対に衝突しない。"""
    out = aggregate.aggregate([
        raw({"adjudications": [],
             "own_findings": [
                 {"file": "b.py", "line": None, "severity": "high",
                  "title": "issue", "detail": "detail invalid",
                  "evidence": "e", "verified": "b.py:1-9",
                  "fix": {"kind": "none"}},
                 {"file": "b.py", "line": 12, "severity": "high",
                  "title": "issue", "detail": "detail valid",
                  "evidence": "e", "verified": "b.py:1-9",
                  "fix": {"kind": "none"}}
             ],
             "unverified": [], "summary": ""}),
    ])
    assert len(out["own_findings"]) == 2
    details = {item["detail"] for item in out["own_findings"]}
    assert details == {"detail invalid", "detail valid"}


def test_string_line_and_int_line_merge():
    """正当な行は "12" と 12 が同じ鍵に併合される。"""
    out = aggregate.aggregate([
        raw({"adjudications": [],
             "own_findings": [{"file": "b.py", "line": "12", "severity": "high",
                               "title": "issue", "detail": "d",
                               "evidence": "e", "verified": "b.py:1-9",
                               "fix": {"kind": "none"}}],
             "unverified": [], "summary": ""}),
        raw({"adjudications": [],
             "own_findings": [{"file": "b.py", "line": 12, "severity": "high",
                               "title": "issue", "detail": "d",
                               "evidence": "e", "verified": "b.py:1-9",
                               "fix": {"kind": "none"}}],
             "unverified": [], "summary": ""}),
    ])
    assert len(out["own_findings"]) == 1
    assert out["own_findings"][0]["_hits"] == 2


def test_adjudications_invalid_lines_no_thread_id():
    """adjudications でも thread_id が空なら、異なる不正な line 値は衝突しない。"""
    out = aggregate.aggregate([
        raw({"adjudications": [
                 {"source": "c", "thread_id": "", "file": "a.py",
                  "line": 0, "title": "x", "verdict": "valid", "reason": "r1",
                  "verified": "a.py:1-20", "severity": "high",
                  "fix": {"kind": "none"}},
                 {"source": "c", "thread_id": "", "file": "a.py",
                  "line": "nope", "title": "x", "verdict": "valid", "reason": "r2",
                  "verified": "a.py:1-20", "severity": "high",
                  "fix": {"kind": "none"}}
             ],
             "own_findings": [], "unverified": [], "summary": ""}),
    ])
    assert len(out["adjudications"]) == 2, "異なる不正な line 値の adjudications が衝突している"
    reasons = {item["reason"] for item in out["adjudications"]}
    assert reasons == {"r1", "r2"}


def test_adjudications_with_thread_id_ignores_line_for_key():
    """adjudications で thread_id がある場合、line は鍵に影響しない（従来どおり）。"""
    out = aggregate.aggregate([
        raw({"adjudications": [
                 {"source": "c", "thread_id": "T_1", "file": "a.py",
                  "line": 10, "title": "x", "verdict": "valid", "reason": "r",
                  "verified": "a.py:1-20", "severity": "high",
                  "fix": {"kind": "none"}}
             ],
             "own_findings": [], "unverified": [], "summary": ""}),
        raw({"adjudications": [
                 {"source": "c", "thread_id": "T_1", "file": "a.py",
                  "line": 20, "title": "x", "verdict": "valid", "reason": "r",
                  "verified": "a.py:1-20", "severity": "high",
                  "fix": {"kind": "none"}}
             ],
             "own_findings": [], "unverified": [], "summary": ""}),
    ])
    assert len(out["adjudications"]) == 1
    assert out["adjudications"][0]["_hits"] == 2
