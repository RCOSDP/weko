#!/usr/bin/env python3
"""集約結果を PR に貼る Markdown にする。"""
from __future__ import annotations

import argparse
import json

VERDICT_LABEL = {"valid": "✅ 妥当", "false_positive": "❌ 誤検知",
                 "needs_context": "🔎 要文脈", "already_fixed": "☑️ 対応済み"}
SEV_LABEL = {"high": ("🔴", "高"), "medium": ("🟠", "中"), "low": ("🟡", "低")}


def _loc(x) -> str:
    # aggregate.py は不正な行番号（辞書・負数・0・非数値文字列）を line=None にして
    # 件数自体は残す。ここでは行番号がないときは file だけを出し、末尾の
    # コロン（`file:None`）を見せない。
    line = x.get("line")
    if line is None:
        return "`%s`" % x.get("file", "")
    return "`%s:%s`" % (x.get("file", ""), line)


def _hits(x, passes) -> str:
    return "" if x["_hits"] == passes else "（%d/%d パス）" % (x["_hits"], passes)


def _fix_cell(fx) -> str:
    return {"suggestion": "あり(inline)", "description": "あり"}.get(
        fx.get("kind"), "—")


def _fix_block(fx, out) -> None:
    if fx.get("kind") == "suggestion":
        out.append("**修正案** `%s:%s-%s`\n" % (fx["file"], fx["start_line"],
                                               fx["end_line"]))
        out.append("```\n" + fx["replacement"] + "\n```\n")
        if fx.get("note"):
            out.append(fx["note"] + "\n")
    elif fx.get("kind") == "description" and fx.get("note"):
        out.append("**修正案**\n\n" + fx["note"] + "\n")


def render(findings: dict, meta: dict, model: str) -> str:
    passes = findings["passes"]
    adjs = findings["adjudications"]
    owns = findings["own_findings"]
    unver = findings["unverified"]

    main = [a for a in adjs if a["verdict"] != "needs_context"]
    ctx = [a for a in adjs if a["verdict"] == "needs_context"]

    out = ["## 🔍 Claude レビュー統合\n"]

    if not adjs and not owns and not unver:
        out.append("指摘はありません。\n")
    else:
        n = {k: sum(1 for a in adjs if a["verdict"] == k) for k in VERDICT_LABEL}
        if adjs:
            out.append("**他レビューの指摘 %d 件** → ✅ 妥当 %d ／ ❌ 誤検知 %d ／ "
                       "🔎 要文脈 %d ／ ☑️ 対応済み %d\n"
                       % (len(adjs), n["valid"], n["false_positive"],
                          n["needs_context"], n["already_fixed"]))
        if owns:
            s = {k: sum(1 for o in owns if o["severity"] == k)
                 for k in SEV_LABEL}
            out.append("**Claude の追加指摘 %d 件** — 🔴 高 %d ／ 🟠 中 %d ／ "
                       "🟡 低 %d\n"
                       % (len(owns), s["high"], s["medium"], s["low"]))

    rows = []
    for i, a in enumerate(main, 1):
        rows.append("| %d | %s | %s | %s | %s | %s |"
                    % (i, a["source"] or "?", _loc(a), a["title"],
                       VERDICT_LABEL[a["verdict"]], _fix_cell(a["fix"])))
    for j, o in enumerate(owns, len(main) + 1):
        mark, label = SEV_LABEL.get(o["severity"], ("⚪", "不明"))
        rows.append("| %d | Claude | %s | %s | %s 追加指摘（%s） | %s |"
                    % (j, _loc(o), o["title"], mark, label, _fix_cell(o["fix"])))
    if rows:
        out.append("| # | 出所 | 箇所 | 指摘 | 判定 | 修正案 |")
        out.append("|---|---|---|---|---|---|")
        out.extend(rows)
        out.append("")

    for i, a in enumerate(main, 1):
        out.append("---\n")
        out.append("### %d. %s %s\n" % (i, VERDICT_LABEL[a["verdict"]],
                                        a["title"]))
        out.append("%s ／ 出所 @%s %s\n"
                   % (_loc(a), a["source"] or "?", _hits(a, passes)))
        if a["_split"]:
            out.append("> パス間で判定が割れました（%s）。安全側の判定を採っています。\n"
                       % " / ".join(a["_verdicts"]))
        if a["reason"]:
            out.append(a["reason"] + "\n")
        _fix_block(a["fix"], out)
        if a["verified"]:
            out.append("<details><summary>根拠</summary>\n")
            out.append("確認: %s\n" % a["verified"])
            out.append("</details>\n")

    for j, o in enumerate(owns, len(main) + 1):
        mark, label = SEV_LABEL.get(o["severity"], ("⚪", "不明"))
        out.append("---\n")
        out.append("### %d. %s [%s] %s（Claude の追加指摘）\n"
                   % (j, mark, label, o["title"]))
        out.append("%s %s\n" % (_loc(o), _hits(o, passes)))
        if o["detail"]:
            out.append(o["detail"] + "\n")
        _fix_block(o["fix"], out)
        if o["evidence"] or o["verified"]:
            out.append("<details><summary>根拠</summary>\n")
            if o["evidence"]:
                out.append("```\n" + o["evidence"] + "\n```\n")
            if o["verified"]:
                out.append("確認: %s\n" % o["verified"])
            out.append("</details>\n")

    if ctx:
        out.append("---\n")
        out.append("<details><summary>🔎 要文脈 — 判断しきれなかった他レビューの指摘 "
                   "%d 件</summary>\n" % len(ctx))
        for a in ctx:
            out.append("- **%s** %s @%s" % (a["title"], _loc(a), a["source"]))
            if a["reason"]:
                out.append("  - %s" % a["reason"])
        out.append("\n</details>\n")

    if unver:
        out.append("<details><summary>🔎 未確認 — 裏が取れなかったもの %d 件</summary>\n"
                   % len(unver))
        for x in unver:
            out.append("- **%s** %s %s" % (x["title"], _loc(x),
                                           _hits(x, passes)))
            if x["detail"]:
                out.append("  - %s" % x["detail"])
            if x["why"]:
                out.append("  - 確認できなかった理由: %s" % x["why"])
        out.append("\n</details>\n")

    if findings["summary"]:
        out.append("---\n")
        out.append("**次にすること**: %s\n" % findings["summary"])

    dropped = meta.get("dropped_threads", 0) + meta.get("dropped_other", 0)
    if dropped:
        out.append("> ⚠️ 入力の容量上限により、レビュースレッド %d 件 / その他 %d 件 を"
                   "省略しました。裁定の対象外です。\n"
                   % (meta.get("dropped_threads", 0), meta.get("dropped_other", 0)))

    out.append("---\n")
    note = "モデル %s ／ %d 回実行して和集合 ／ コスト $%.4f" % (
        model, passes, findings["cost"])
    if passes > 1:
        note += ("。同じ入力でも結果が揺れるため複数回まわし、"
                 "一部のパスでしか挙がらなかったものには回数を添えています")
    out.append("<sub>%s</sub>" % note)
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--findings", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    findings = json.load(open(a.findings, encoding="utf-8"))
    meta = json.load(open(a.meta, encoding="utf-8"))
    open(a.out, "w", encoding="utf-8").write(render(findings, meta, a.model))
    print("wrote %s" % a.out)


if __name__ == "__main__":
    main()
