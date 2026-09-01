#!/usr/bin/env python3
"""集約結果を PR に貼る Markdown にする。"""
from __future__ import annotations

import argparse
import json

import mdsafe

VERDICT_LABEL = {"valid": "✅ 妥当", "false_positive": "❌ 誤検知",
                 "needs_context": "🔎 要文脈", "already_fixed": "☑️ 対応済み"}
SEV_LABEL = {"high": ("🔴", "高"), "medium": ("🟠", "中"), "low": ("🟡", "低")}

# title / source / reason / detail / evidence / note / replacement / why /
# summary / file はすべて Claude の出力由来で、その元は公開 PR に誰でも書ける
# レビューコメント。github-actions[bot] として public リポジトリに投稿される
# ため、コードフェンスの外に置くものは必ずエスケープする。エスケープの実体は
# post_inline.py と共有する tools/claude-review/scripts/mdsafe.py にある。

_esc = mdsafe.esc
_cell = mdsafe.cell
_fence = mdsafe.fence


def _loc(x) -> str:
    # aggregate.py は不正な行番号（辞書・負数・0・非数値文字列）を line=None にして
    # 件数自体は残す。ここでは行番号がないときは file だけを出し、末尾の
    # コロン（`file:None`）を見せない。file はファイルパス由来の外部文字列
    # なのでエスケープする。
    line = x.get("line")
    file = _esc(x.get("file", ""))
    if line is None:
        return "`%s`" % file
    return "`%s:%s`" % (file, line)


def _hits(x, passes) -> str:
    return "" if x["_hits"] == passes else "（%d/%d パス）" % (x["_hits"], passes)


def _fix_cell(fx, inline_enabled: bool) -> str:
    if fx.get("kind") == "suggestion":
        # inline_enabled が False のとき(既定)、または
        # POST_INLINE_SUGGESTIONS='false' で運用しているときは、
        # post_inline.py が実際には inline comment を投稿しない。
        # ここで「あり(inline)」と告知すると、待っても現れない inline
        # suggestion があるかのように著者に誤解させる(所見4)。
        return "あり(inline)" if inline_enabled else "あり"
    return {"description": "あり"}.get(fx.get("kind"), "—")


def _fix_block(fx, out) -> None:
    if fx.get("kind") == "suggestion":
        out.append("**修正案** `%s:%s-%s`\n" % (_esc(fx["file"]), fx["start_line"],
                                               fx["end_line"]))
        fence = _fence(fx["replacement"])
        out.append(fence + "\n" + fx["replacement"] + "\n" + fence + "\n")
        if fx.get("note"):
            out.append(_esc(fx["note"]) + "\n")
    elif fx.get("kind") == "description" and fx.get("note"):
        out.append("**修正案**\n\n" + _esc(fx["note"]) + "\n")


def render(findings: dict, meta: dict, model: str,
           inline_enabled: bool = False) -> str:
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
                    % (i, _cell(a["source"] or "?"), _cell(_loc(a)),
                       _cell(a["title"]), VERDICT_LABEL[a["verdict"]],
                       _fix_cell(a["fix"], inline_enabled)))
    for j, o in enumerate(owns, len(main) + 1):
        mark, label = SEV_LABEL.get(o["severity"], ("⚪", "不明"))
        rows.append("| %d | Claude | %s | %s | %s 追加指摘（%s） | %s |"
                    % (j, _cell(_loc(o)), _cell(o["title"]), mark, label,
                       _fix_cell(o["fix"], inline_enabled)))
    if rows:
        out.append("| # | 出所 | 箇所 | 指摘 | 判定 | 修正案 |")
        out.append("|---|---|---|---|---|---|")
        out.extend(rows)
        out.append("")

    for i, a in enumerate(main, 1):
        out.append("---\n")
        out.append("### %d. %s %s\n" % (i, VERDICT_LABEL[a["verdict"]],
                                        _esc(a["title"])))
        # "出所" の直前に literal な '@' を置かない(所見12-a)。source は
        # 普通は "coderabbitai" のような素の名前で、'@' を前置すると常に
        # 本物のメンションになり、CodeRabbit を呼び出す実在のコマンド
        # 形式("@coderabbitai ...")そのものを作ってしまう。
        out.append("%s ／ 出所 %s %s\n"
                   % (_loc(a), _esc(a["source"] or "?"), _hits(a, passes)))
        if a["_split"]:
            out.append("> パス間で判定が割れました（%s）。安全側の判定を採っています。\n"
                       % " / ".join(a["_verdicts"]))
        if a["reason"]:
            out.append(_esc(a["reason"]) + "\n")
        _fix_block(a["fix"], out)
        if a["verified"]:
            out.append("<details><summary>根拠</summary>\n")
            out.append("確認: %s\n" % _esc(a["verified"]))
            out.append("</details>\n")

    for j, o in enumerate(owns, len(main) + 1):
        mark, label = SEV_LABEL.get(o["severity"], ("⚪", "不明"))
        out.append("---\n")
        out.append("### %d. %s [%s] %s（Claude の追加指摘）\n"
                   % (j, mark, label, _esc(o["title"])))
        out.append("%s %s\n" % (_loc(o), _hits(o, passes)))
        if o["detail"]:
            out.append(_esc(o["detail"]) + "\n")
        _fix_block(o["fix"], out)
        if o["evidence"] or o["verified"]:
            out.append("<details><summary>根拠</summary>\n")
            if o["evidence"]:
                fence = _fence(o["evidence"])
                out.append(fence + "\n" + o["evidence"] + "\n" + fence + "\n")
            if o["verified"]:
                out.append("確認: %s\n" % _esc(o["verified"]))
            out.append("</details>\n")

    if ctx:
        out.append("---\n")
        out.append("<details><summary>🔎 要文脈 — 判断しきれなかった他レビューの指摘 "
                   "%d 件</summary>\n" % len(ctx))
        for a in ctx:
            out.append("- **%s** %s %s" % (_esc(a["title"]), _loc(a),
                                           _esc(a["source"])))
            if a["reason"]:
                out.append("  - %s" % _esc(a["reason"]))
        out.append("\n</details>\n")

    if unver:
        out.append("<details><summary>🔎 未確認 — 裏が取れなかったもの %d 件</summary>\n"
                   % len(unver))
        for x in unver:
            out.append("- **%s** %s %s" % (_esc(x["title"]), _loc(x),
                                           _hits(x, passes)))
            if x["detail"]:
                out.append("  - %s" % _esc(x["detail"]))
            if x["why"]:
                out.append("  - 確認できなかった理由: %s" % _esc(x["why"]))
        out.append("\n</details>\n")

    if findings["summary"]:
        out.append("---\n")
        out.append("**次にすること**: %s\n" % _esc(findings["summary"]))

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
    ap.add_argument("--inline-enabled", action="store_true",
                    help="POST_INLINE_SUGGESTIONS が有効なときに指定する。"
                         "指定しなければ suggestion の修正案は表内で"
                         "「あり(inline)」ではなく「あり」と表示する"
                         "(投稿されない inline suggestion を告知しないため)。")
    a = ap.parse_args()

    findings = json.load(open(a.findings, encoding="utf-8"))
    meta = json.load(open(a.meta, encoding="utf-8"))
    open(a.out, "w", encoding="utf-8").write(
        render(findings, meta, a.model, inline_enabled=a.inline_enabled))
    print("wrote %s" % a.out)


if __name__ == "__main__":
    main()
