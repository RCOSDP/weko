"""post_inline の差分レンジ判定と投稿条件のテスト。"""
import json
import re
import shutil
import subprocess

import pytest

import post_inline


DIFF = """diff --git a/a.py b/a.py
index 111..222 100644
--- a/a.py
+++ b/a.py
@@ -10,3 +10,4 @@ def f():
     x = 1
-    y = 2
+    y = 3
+    z = 4
diff --git a/gone.py b/gone.py
--- a/gone.py
+++ /dev/null
@@ -1,2 +0,0 @@
-a
-b
"""


def test_changed_lines_uses_right_side_ranges():
    out = post_inline.changed_lines(DIFF)
    assert out["a.py"] == {10, 11, 12, 13}


def test_deleted_file_has_no_right_side_lines():
    out = post_inline.changed_lines(DIFF)
    assert "gone.py" not in out


def test_real_diff_parses(diff_text):
    """#1905 の実差分でも落ちないこと。"""
    out = post_inline.changed_lines(diff_text)
    assert out
    assert all(isinstance(v, set) for v in out.values())


def _fx(**kw):
    base = {"kind": "suggestion", "file": "a.py", "start_line": 11,
            "end_line": 12, "replacement": "    y = 3\n    z = 4", "note": ""}
    base.update(kw)
    return base


def _findings(fix, verdict="valid", verified="a.py:1-20"):
    return {"adjudications": [{"thread_id": "T1", "source": "coderabbitai",
                               "file": "a.py", "line": 12, "title": "t",
                               "verdict": verdict, "reason": "r",
                               "verified": verified, "severity": "high",
                               "fix": fix, "_hits": 1, "_verdicts": [verdict],
                               "_split": False}],
            "own_findings": [], "unverified": [], "passes": 1,
            "cost": 0.0, "summary": ""}


def test_valid_suggestion_inside_diff_is_selected():
    changed = post_inline.changed_lines(DIFF)
    out = post_inline.select(_findings(_fx()), changed, set())
    assert len(out) == 1
    assert out[0]["line"] == 12 and out[0]["start_line"] == 11


def test_single_line_omits_start_line():
    """start_line == line で送ると GitHub が 422 を返す。"""
    changed = post_inline.changed_lines(DIFF)
    out = post_inline.select(
        _findings(_fx(start_line=12, end_line=12, replacement="    y = 3")),
        changed, set())
    assert "start_line" not in out[0]


def test_lines_outside_the_diff_are_rejected():
    """差分外の行に inline comment は付けられない。"""
    changed = post_inline.changed_lines(DIFF)
    out = post_inline.select(
        _findings(_fx(start_line=50, end_line=51)), changed, set())
    assert out == []


def test_non_valid_verdict_is_rejected():
    changed = post_inline.changed_lines(DIFF)
    for v in ("false_positive", "needs_context", "already_fixed"):
        assert post_inline.select(_findings(_fx(), verdict=v),
                                  changed, set()) == []


def test_already_posted_hash_is_skipped():
    """push のたびに同じ提案が積み上がらないこと。"""
    changed = post_inline.changed_lines(DIFF)
    first = post_inline.select(_findings(_fx()), changed, set())
    h = post_inline.fix_hash(_fx())
    assert first[0]["body"].startswith("<!-- claude-fix:%s -->" % h)
    assert post_inline.select(_findings(_fx()), changed, {h}) == []


def test_own_finding_needs_verified():
    changed = post_inline.changed_lines(DIFF)
    f = {"adjudications": [], "unverified": [], "passes": 1, "cost": 0.0,
         "summary": "",
         "own_findings": [{"file": "a.py", "line": 12, "severity": "high",
                           "title": "t", "detail": "d", "evidence": "e",
                           "verified": "", "fix": _fx(), "_hits": 1}]}
    assert post_inline.select(f, changed, set()) == []
    f["own_findings"][0]["verified"] = "a.py:1-20"
    assert len(post_inline.select(f, changed, set())) == 1


def test_replacement_with_triple_backtick_escalates_fence():
    """replacement に ``` が含まれても fence がエスケープされず閉じ込められる。"""
    changed = post_inline.changed_lines(DIFF)
    fx = _fx(replacement="```\nrm -rf /\n```")
    out = post_inline.select(_findings(fx), changed, set())
    assert len(out) == 1
    body = out[0]["body"]
    # 4 本以上のバッククォートで開始・終了していること
    assert "````suggestion" in body
    # replacement 自体はそのまま（無加工）で本文に含まれる
    assert "```\nrm -rf /\n```" in body
    # 4 本のバッククォートのフェンスはちょうど開始・終了の 2 回しか
    # 出現しない（= replacement の中身が途中でフェンスを閉じていない）
    assert body.count("````") == 2


def test_title_and_reason_cannot_inject_structure():
    """title / reason に含まれる HTML タグ・改行が本文の構造に注入されない。"""
    changed = post_inline.changed_lines(DIFF)
    fx = _fx()
    findings = _findings(fx)
    findings["adjudications"][0]["title"] = "evil</details>\ninjected"
    findings["adjudications"][0]["reason"] = "line1\nline2<script>"
    out = post_inline.select(findings, changed, set())
    body = out[0]["body"]
    assert "</details>" not in body
    assert "<script>" not in body
    assert "&lt;/details&gt;" in body
    assert "&lt;script&gt;" in body
    # 改行が畳み込まれ、injected という語が独立した行として出現しない
    assert "\ninjected" not in body
    assert "line1 line2" in body


def test_title_and_reason_at_mentions_are_defanged():
    """所見12: title / reason に含まれる '@' が生きたメンションとして
    本文に残らない(--dry-run で確認できる body 自体をここで検証する)。"""
    changed = post_inline.changed_lines(DIFF)
    fx = _fx()
    findings = _findings(fx)
    findings["adjudications"][0]["title"] = "@someone please check"
    findings["adjudications"][0]["reason"] = "coderabbitai full review"
    out = post_inline.select(findings, changed, set())
    body = out[0]["body"]
    assert "@someone" not in body
    # reason 自体には '@' が無いが、念のため実在コマンド文字列が
    # 単体で本文に出ないことも確認する(title 側の検証が主眼)。
    assert "@coderabbitai full review" not in body


def test_reason_leading_suggestion_fence_cannot_forge_a_second_block():
    """所見2: reason 自体が ```suggestion で始まっても、one-click apply の
    対象になる本文を偽造できない。

    改行を畳むだけの旧実装では reason="```suggestion" が本物の
    ```suggestion フェンスの直前に独立した行として現れ、info string
    "suggestion" を持たない内側のフェンスが外側を閉じない一方で GitHub は
    単一の suggestion として解釈してしまい、reason の残りの行 +
    replacement の内容がそのまま 1 クリックでソースに書き込まれる。
    """
    changed = post_inline.changed_lines(DIFF)
    fx = _fx()
    findings = _findings(fx)
    findings["adjudications"][0]["reason"] = "```suggestion"
    out = post_inline.select(findings, changed, set())
    body = out[0]["body"]
    lines = body.splitlines()
    # ```suggestion で始まる行は BODY テンプレートが作る本物の 1 箇所だけ。
    suggestion_openers = [l for l in lines if l == "```suggestion"]
    assert len(suggestion_openers) == 1
    assert not any(re.match(r"^ {0,3}`{3,}suggestion", l) for l in lines
                   if l != "```suggestion")


def test_title_leading_structural_char_cannot_open_a_block():
    """title 自体が先頭 # / ``` などでも、独立したブロック開始行にならない。"""
    changed = post_inline.changed_lines(DIFF)
    fx = _fx()
    findings = _findings(fx)
    findings["adjudications"][0]["title"] = "## 偽の見出し"
    out = post_inline.select(findings, changed, set())
    body = out[0]["body"]
    assert not any(re.match(r"^ {0,3}#{1,6}(\s|$)", l)
                   for l in body.splitlines())


def test_description_fix_kind_is_rejected_without_keyerror():
    """kind != 'suggestion' のとき file/start_line 等を持たなくても落ちない。

    aggregate.py は description/none の fix に file/start_line/end_line を
    要求しない。_candidate() が kind を見る前に fx["file"] 等へアクセスして
    いないことを確認する（ガードの順序を保証する回帰テスト）。
    """
    changed = post_inline.changed_lines(DIFF)
    fx = {"kind": "description", "note": "説明のみで inline 化できない修正案"}
    assert post_inline.select(_findings(fx), changed, set()) == []


def test_none_fix_kind_is_rejected_without_keyerror():
    changed = post_inline.changed_lines(DIFF)
    fx = {"kind": "none"}
    assert post_inline.select(_findings(fx), changed, set()) == []


def test_existing_hashes_filters_to_own_bot_comments(monkeypatch):
    """existing_hashes は github-actions[bot] 以外のコメント本文を見ない。

    誰でも書ける PR コメントに `<!-- claude-fix:<hash> -->` を仕込むだけで
    ハッシュを偽造でき、本物の修正案が「投稿済み」として黙って抑止される
    （select() のログには一切残らない）。jq のフィルタ段階で自分（bot）が
    書いたコメントだけに絞る。
    """
    calls = {}

    class _Result:
        stdout = "<!-- claude-fix:abcdef123456 -->"
        returncode = 0

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        return _Result()

    monkeypatch.setattr(post_inline.subprocess, "run", fake_run)
    result = post_inline.existing_hashes("o", "r", 1)

    assert result == {"abcdef123456"}
    jq_arg = calls["cmd"][calls["cmd"].index("--jq") + 1]
    # フィルタ全体を厳密一致で確認する（余計な条件が紛れ込む変更にも
    # 反応するように、部分一致ではなく完全一致にする）。
    assert jq_arg == post_inline.EXISTING_COMMENTS_JQ


def test_body_first_line_is_the_marker():
    """アンカー方式（1 行目だけを投稿済み判定に使う）の前提条件を固定する。

    replacement はコードとしてエスケープせず本文に埋め込むため、そこに
    偽の `<!-- claude-fix:... -->` を混ぜられても投稿者フィルタは通過して
    しまう。本文の 1 行目だけを既投稿判定に使うことでこの経路を塞いでいる
    （EXISTING_COMMENTS_JQ 参照）が、これは BODY テンプレートが常に
    マーカーを 1 行目に置いていることが前提になる。ここでその前提を固定する。
    """
    changed = post_inline.changed_lines(DIFF)
    out = post_inline.select(_findings(_fx()), changed, set())
    first_line = out[0]["body"].splitlines()[0]
    assert post_inline.FIX_MARK.fullmatch(first_line)


@pytest.mark.skipif(shutil.which("jq") is None,
                    reason="jq が見つからない環境ではスキップ")
def test_existing_comments_jq_only_extracts_first_line_of_body():
    """EXISTING_COMMENTS_JQ を実物の jq に食わせ、各本文の 1 行目だけが
    出力されることを検証する（replacement 内の偽マーカーが混ざらない
    ことの直接の根拠）。

    gh api --jq は実行時に GitHub API のレスポンス（コメントオブジェクトの
    配列）にこのフィルタを適用する。ここでは synthetic な配列を作り、
    実際の jq バイナリで同じフィルタ文字列を実行して出力の形を確認する。
    """
    real_hash = "3d1b9f0df4f0"
    forged_hash_in_replacement = "1ee3616294a9"
    non_bot_hash = "000000000000"
    payload = [
        {"user": {"login": "github-actions[bot]"},
         "body": ("<!-- claude-fix:%s -->\n**t**\n\n```suggestion\n"
                  "    y = 3\n    # <!-- claude-fix:%s -->\n    z = 4\n"
                  "```\n") % (real_hash, forged_hash_in_replacement)},
        {"user": {"login": "attacker"},
         "body": "<!-- claude-fix:%s -->\nnot a bot" % non_bot_hash},
    ]
    proc = subprocess.run(
        ["jq", "-r", post_inline.EXISTING_COMMENTS_JQ],
        input=json.dumps(payload), capture_output=True, text=True, check=True)

    assert proc.stdout.splitlines() == ["<!-- claude-fix:%s -->" % real_hash]
    hashes = set(post_inline.FIX_MARK.findall(proc.stdout))
    assert hashes == {real_hash}
