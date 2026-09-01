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


def test_own_output_is_excluded_with_bot_suffixed_login(graphql_payload):
    """所見8: GraphQL の author.login が "github-actions[bot]" 表記でも
    自分の投稿として除外できる。

    SELF = "github-actions" と完全一致でしか比較していなかった。REST の
    user.login は "github-actions[bot]"(角括弧つき)、GraphQL の
    author.login がどちらの表記で来るかは実測で確認していない前提だった
    (frozen fixture に bot の投稿が無い)。表記が違えば previous が
    永遠に解決せず、かつ自分の集約コメントが会話として Claude に
    再入力されてしまう。
    """
    payload = graphql_payload
    pr = payload["data"]["repository"]["pullRequest"]
    pr["comments"]["nodes"].append({
        "author": {"login": "github-actions[bot]"},
        "body": "<!-- claude-pr-review -->\n## 前回の結果(bot表記)",
        "createdAt": "2026-09-01T02:00:00Z"})
    pr["reviewThreads"]["nodes"].append({
        "id": "T_self_bot", "isResolved": False, "isOutdated": False,
        "path": "a.py", "line": 1, "startLine": None,
        "comments": {"nodes": [{
            "databaseId": 2, "author": {"login": "github-actions[bot]"},
            "body": "<!-- claude-fix:abc123abc123 -->", "createdAt": "x"}]}})
    pr["reviews"]["nodes"].append({
        "author": {"login": "github-actions[bot]"}, "state": "COMMENTED",
        "body": "test review from bot-suffixed self",
        "submittedAt": "2026-09-01T00:00:00Z"})

    out = collect_reviews.normalize(payload)
    assert out["previous"].startswith("<!-- claude-pr-review -->")
    assert all(t["id"] != "T_self_bot" for t in out["threads"])
    assert all(c["author"] != "github-actions[bot]" for c in out["conversation"])
    assert all(r["author"] != "github-actions[bot]" for r in out["reviews"])


def test_deleted_user_does_not_crash(graphql_payload):
    """アカウント削除済みユーザは author が null になる。"""
    pr = graphql_payload["data"]["repository"]["pullRequest"]
    pr["reviewThreads"]["nodes"][0]["comments"]["nodes"][0]["author"] = None
    out = collect_reviews.normalize(graphql_payload)
    assert out["threads"][0]["comments"][0]["author"] == "(unknown)"


def test_reviews_structure_and_filtering(graphql_payload):
    """reviews 出力は author/state/body/submitted_at の 4 キーを持つ。

    body が空・空白のレビューは除外し、github-actions も除外される。
    fixture には非空 body のレビューが 3 件ある。
    """
    payload = graphql_payload
    pr = payload["data"]["repository"]["pullRequest"]

    # fixture のレビューで非空 body のものを数える
    original_reviews = pr["reviews"]["nodes"]
    expected_count = len([
        r for r in original_reviews
        if (r.get("body") or "").strip() and r.get("author", {}).get("login") != "github-actions"
    ])

    out = collect_reviews.normalize(payload)

    # 各レビューが 4 つのキーを持つこと
    assert len(out["reviews"]) == expected_count, \
        f"Expected {expected_count} reviews, got {len(out['reviews'])}"

    for r in out["reviews"]:
        assert set(r.keys()) == {"author", "state", "body", "submitted_at"}, \
            f"Unexpected keys in review: {r.keys()}"
        assert r["author"] != "github-actions", "github-actions review should be excluded"
        assert r["body"].strip(), "Empty body reviews should be excluded"
        assert r["state"], "state field should be preserved"

    # github-actions のレビューが含まれないこと（テスト用に追加してテスト）
    payload2 = graphql_payload
    pr2 = payload2["data"]["repository"]["pullRequest"]
    pr2["reviews"]["nodes"].append({
        "author": {"login": "github-actions"},
        "state": "COMMENTED",
        "body": "test review",
        "submittedAt": "2026-09-01T00:00:00Z"
    })

    out2 = collect_reviews.normalize(payload2)
    assert all(r["author"] != "github-actions" for r in out2["reviews"]), \
        "github-actions review should be excluded"


def test_limit_detection(graphql_payload):
    """取得件数が上限に達したら _limits に記録される。

    first:100 で最古の N 件を取るため、issue コメントが 100 件超過の
    PR では previous が落ちる。warnings は normalize() でなく
    main() 側で出す。
    """
    payload = graphql_payload
    pr = payload["data"]["repository"]["pullRequest"]

    # comments を 100 件まで充足
    original_comments = pr["comments"]["nodes"]
    while len(pr["comments"]["nodes"]) < 100:
        pr["comments"]["nodes"].append({
            "author": {"login": "test-user"},
            "body": "filler comment",
            "createdAt": "2026-09-01T00:00:00Z"
        })

    out = collect_reviews.normalize(payload)

    # _limits キーが存在する
    assert "_limits" in out, "_limits key should be present"

    # comments が 100 に達した状態を記録
    assert out["_limits"]["comments_saturated"] is True, \
        "comments_saturated should be True when at 100"

    # 既存の 5 つのキーは変わらない
    assert set(k for k in out.keys() if not k.startswith("_")) == \
           {"head_sha", "threads", "reviews", "conversation", "previous"}, \
           "Contract keys should not change"
