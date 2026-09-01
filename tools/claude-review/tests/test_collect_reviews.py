"""collect_reviews の正規化のテスト。"""
import collect_reviews


def test_threads_keep_replies_and_resolution(graphql_payload):
    """スレッドは返信ごと、解決状態つきで残る。

    親コメントだけ渡すと決着済みの議論を蒸し返すため。
    """
    out = collect_reviews.normalize(graphql_payload)
    by_path = {t["path"]: t for t in out["threads"]}

    conf = by_path["modules/weko-records-ui/tests/conftest.py"]
    assert conf["resolved"] is True
    assert [c["author"] for c in conf["comments"]] == [
        "coderabbitai", "ivis-kuroda", "coderabbitai"]
    assert conf["start_line"] == 383 and conf["line"] == 385

    assert by_path["modules/weko-records-ui/weko_records_ui/views.py"] is not None
    assert any(t["resolved"] is False for t in out["threads"])


def test_head_sha_is_present(graphql_payload):
    out = collect_reviews.normalize(graphql_payload)
    assert len(out["head_sha"]) == 40


def test_own_output_is_excluded(graphql_payload):
    """自分の集約コメントは入力から外し、previous に回す。

    自分の出力を自分の入力に混ぜると、同じ指摘を裏取りせず再生産する。
    """
    payload = graphql_payload
    pr = payload["data"]["repository"]["pullRequest"]
    pr["comments"]["nodes"].append({
        "author": {"login": "github-actions"},
        "body": "<!-- claude-pr-review -->\n## 前回の結果",
        "createdAt": "2026-09-01T02:00:00Z"})
    pr["reviewThreads"]["nodes"].append({
        "id": "T_self", "isResolved": False, "isOutdated": False,
        "path": "a.py", "line": 1, "startLine": None,
        "comments": {"nodes": [{
            "databaseId": 1, "author": {"login": "github-actions"},
            "body": "<!-- claude-fix:abc123abc123 -->", "createdAt": "x"}]}})

    out = collect_reviews.normalize(payload)
    assert out["previous"].startswith("<!-- claude-pr-review -->")
    assert all(t["id"] != "T_self" for t in out["threads"])
    assert all(c["author"] != "github-actions" for c in out["conversation"])


def test_deleted_user_does_not_crash(graphql_payload):
    """アカウント削除済みユーザは author が null になる。"""
    pr = graphql_payload["data"]["repository"]["pullRequest"]
    pr["reviewThreads"]["nodes"][0]["comments"]["nodes"][0]["author"] = None
    out = collect_reviews.normalize(graphql_payload)
    assert out["threads"][0]["comments"][0]["author"] == "(unknown)"
