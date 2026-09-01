#!/usr/bin/env python3
"""PR に付いている既存レビューを集めて JSON にする。

GraphQL を使う理由: レビュースレッドの解決状態(isResolved)は REST では取れない。
決着済みかどうかを渡さないと、Claude が終わった議論を蒸し返す。
"""
from __future__ import annotations

import argparse
import json
import subprocess

QUERY = """
query($owner:String!,$repo:String!,$pr:Int!){
  repository(owner:$owner,name:$repo){
    pullRequest(number:$pr){
      headRefOid
      reviewThreads(first:100){ nodes{
        id isResolved isOutdated path line startLine
        comments(first:30){ nodes{ databaseId author{login} body createdAt } }
      }}
      reviews(last:100){ nodes{ author{login} state body submittedAt } }
      comments(last:100){ nodes{ author{login} body createdAt } }
    }
  }
}
"""

SELF = "github-actions"           # 自分の投稿は入力に混ぜない
MARK = "<!-- claude-pr-review -->"


def _is_self(login: str) -> bool:
    """login が自分(このワークフローの投稿)かどうかを判定する。

    REST の pulls/{n}/comments が返す user.login は "github-actions[bot]"
    (角括弧つき)。GraphQL の author.login がどちらの表記で来るかは
    このリポジトリで実際に確認していなかった(frozen fixture に bot の
    投稿が無く、テストも同じ定数から合成した節がある)。表記が違う場合、
    previous が解決できず自己追跡が壊れるだけでなく、自分の集約コメントが
    「レビュアが書いた指摘」として conversation に混入し、外部データの
    枠に入って Claude に再入力されてしまう。両方の表記を受け付ける。
    """
    return login.removesuffix("[bot]") == SELF


def fetch(owner: str, repo: str, pr: int) -> dict:
    proc = subprocess.run(
        ["gh", "api", "graphql", "-f", "query=" + QUERY,
         "-F", "owner=" + owner, "-F", "repo=" + repo, "-F", "pr=%d" % pr],
        capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def _login(node) -> str:
    return ((node or {}).get("author") or {}).get("login") or "(unknown)"


def normalize(payload: dict) -> dict:
    pr = payload["data"]["repository"]["pullRequest"]

    # reviewThreads(first:100) — スレッド内の最初の指摘本文が必須なため最古側を落とせない。
    # ただし 1 スレッドが 30 コメント超過の場合、末尾の結論が落ちて決着判定を誤る可能性がある。
    threads = []
    for t in pr["reviewThreads"]["nodes"]:
        comments = [{"id": c.get("databaseId"), "author": _login(c),
                     "body": c.get("body") or "", "created_at": c.get("createdAt")}
                    for c in t["comments"]["nodes"]]
        # 自分が付けた suggestion スレッドは裁定対象ではない
        if not comments or all(_is_self(c["author"]) for c in comments):
            continue
        threads.append({
            "id": t["id"], "resolved": bool(t["isResolved"]),
            "outdated": bool(t["isOutdated"]), "path": t["path"],
            "line": t["line"], "start_line": t["startLine"],
            "comments": comments})

    # reviews(last:100) — 最新のレビューを取得する必要があるため last を使う
    reviews = [{"author": _login(r), "state": r["state"],
                "body": r.get("body") or "", "submitted_at": r.get("submittedAt")}
               for r in pr["reviews"]["nodes"]
               if not _is_self(_login(r)) and (r.get("body") or "").strip()]

    # comments(last:100) — 前回の自分の集約コメント（most recent）が必須なため last を使う。
    # last:100 で 100 件に達した場合、古いコメントは落ちる。
    conversation, previous = [], None
    for c in pr["comments"]["nodes"]:
        body = c.get("body") or ""
        if _is_self(_login(c)):
            if MARK in body:
                previous = body        # 前回の自分の集約コメント
            continue
        conversation.append({"author": _login(c), "body": body,
                             "created_at": c.get("createdAt")})

    # limit saturation detection (internal use only, prefixed with _)
    limits = {
        "threads_saturated": len(pr["reviewThreads"]["nodes"]) == 100,
        "thread_comments_saturated": any(
            len(t["comments"]["nodes"]) == 30 for t in pr["reviewThreads"]["nodes"]
        ),
        "reviews_saturated": len(pr["reviews"]["nodes"]) == 100,
        "comments_saturated": len(pr["comments"]["nodes"]) == 100,
    }

    result = {"head_sha": pr["headRefOid"], "threads": threads,
              "reviews": reviews, "conversation": conversation,
              "previous": previous}
    result["_limits"] = limits
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    data = normalize(fetch(a.owner, a.repo, a.pr))

    # Check for limit saturation and emit GitHub Actions warnings
    limits = data.pop("_limits")  # Remove internal key before saving to JSON
    if limits["reviews_saturated"]:
        print("::warning::レビューが上限 100 件に達しました。古いレビューは取得していません")
    if limits["comments_saturated"]:
        print("::warning::issue コメントが上限 100 件に達しました。古いコメントは取得していません")
    if limits["threads_saturated"]:
        print("::warning::レビュースレッドが上限 100 件に達しました。古いスレッドは取得していません")
    if limits["thread_comments_saturated"]:
        print("::warning::1スレッド以上が30コメント上限に達しました。決着の判定を誤る可能性があります")

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("threads=%d reviews=%d conversation=%d previous=%s"
          % (len(data["threads"]), len(data["reviews"]),
             len(data["conversation"]), bool(data["previous"])))


if __name__ == "__main__":
    main()
