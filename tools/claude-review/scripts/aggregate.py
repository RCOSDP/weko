#!/usr/bin/env python3
"""複数パスの Claude 出力を 1 つにまとめる。

同じ差分でも実行のたびに結果が揺れる(同一 PR で 0件/1件に割れた実績あり)。
見逃しのほうが痛いので和集合を取り、何回挙がったかを添える。
モデルの出力はそのまま信用せず、列挙値とフィールドをここで検証する。
"""
from __future__ import annotations

import argparse
import glob
import json
import re

# 重い順。パス間で判定が割れたら安全側(先頭に近いほう)を採る。
VERDICT_ORDER = ["valid", "needs_context", "already_fixed", "false_positive"]
SEVERITIES = {"high", "medium", "low"}
FIX_KINDS = {"suggestion", "description", "none"}


def _norm(s) -> str:
    return re.sub(r"\s+", "", str(s or ""))[:60]


def _validate_line(val) -> int | None:
    """行番号を検証する。正の整数に変換できたら返す。"""
    try:
        line = int(val)
        return line if line >= 1 else None
    except (TypeError, ValueError):
        return None


def clean_fix(fix) -> dict:
    """修正案を検証する。壊れているものは投稿対象から外す。"""
    if not isinstance(fix, dict):
        return {"kind": "none", "note": ""}
    kind = fix.get("kind")
    if kind not in FIX_KINDS:
        return {"kind": "none", "note": ""}
    if kind != "suggestion":
        return {"kind": kind, "note": str(fix.get("note") or "")}
    try:
        start = int(fix["start_line"])
        end = int(fix["end_line"])
    except (KeyError, TypeError, ValueError):
        return {"kind": "none", "note": ""}
    repl = fix.get("replacement")
    if not fix.get("file") or not isinstance(repl, str) or start < 1 or end < start:
        return {"kind": "none", "note": ""}
    return {"kind": "suggestion", "file": str(fix["file"]), "start_line": start,
            "end_line": end, "replacement": repl,
            "note": str(fix.get("note") or "")}


def clean_adj(x) -> dict | None:
    if not isinstance(x, dict):
        return None
    verdict = x.get("verdict")
    if verdict not in VERDICT_ORDER:
        return None
    # 裏取りの記録が無い valid は格下げする。件数より確度を優先する。
    if verdict == "valid" and not str(x.get("verified") or "").strip():
        verdict = "needs_context"
    sev = x.get("severity")
    return {"source": str(x.get("source") or ""),
            "thread_id": str(x.get("thread_id") or ""),
            "file": str(x.get("file") or ""), "line": _validate_line(x.get("line")),
            "title": str(x.get("title") or ""), "verdict": verdict,
            "reason": str(x.get("reason") or ""),
            "verified": str(x.get("verified") or ""),
            "severity": sev if sev in SEVERITIES else "low",
            "fix": clean_fix(x.get("fix"))}


def clean_own(x) -> dict | None:
    if not isinstance(x, dict) or not str(x.get("title") or "").strip():
        return None
    sev = x.get("severity")
    return {"file": str(x.get("file") or ""), "line": _validate_line(x.get("line")),
            "severity": sev if sev in SEVERITIES else "low",
            "title": str(x.get("title") or ""),
            "detail": str(x.get("detail") or ""),
            "evidence": str(x.get("evidence") or ""),
            "verified": str(x.get("verified") or ""),
            "fix": clean_fix(x.get("fix"))}


def clean_unver(x) -> dict | None:
    if not isinstance(x, dict) or not str(x.get("title") or "").strip():
        return None
    return {"file": str(x.get("file") or ""), "line": _validate_line(x.get("line")),
            "title": str(x.get("title") or ""),
            "detail": str(x.get("detail") or ""),
            "why": str(x.get("why") or "")}


def adj_key(x) -> str:
    if x["thread_id"]:
        return "t:" + x["thread_id"]
    return "k:%s:%s:%s" % (x["file"], x["line"], _norm(x["title"]))


def own_key(x) -> str:
    return "%s:%s:%s" % (x["file"], x["line"], _norm(x["title"]))


def _extract(raw) -> dict | None:
    text = raw.get("result") or raw.get("text") or ""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def aggregate(raw_list: list) -> dict:
    passes = 0
    cost = 0.0
    adjs, owns, unvers = {}, {}, {}
    summary = ""

    for raw in raw_list:
        passes += 1
        cost += raw.get("total_cost_usd") or 0
        data = _extract(raw)
        if data is None:
            continue
        if not summary and str(data.get("summary") or "").strip():
            summary = str(data["summary"]).strip()

        # 1 パス内での重複排除（同じキーが複数回出ていたら重い方を採る）
        pass_adjs = {}
        for x in data.get("adjudications") or []:
            c = clean_adj(x)
            if not c:
                continue
            k = adj_key(c)
            if k in pass_adjs:
                # パス内でも重い方を採用
                if (VERDICT_ORDER.index(c["verdict"])
                        < VERDICT_ORDER.index(pass_adjs[k]["verdict"])):
                    pass_adjs[k] = c
            else:
                pass_adjs[k] = c

        # クロスパスへのマージ
        for k, c in pass_adjs.items():
            if k in adjs:
                adjs[k]["_hits"] += 1
                adjs[k]["_verdicts"].append(c["verdict"])
                # 安全側に倒す
                if (VERDICT_ORDER.index(c["verdict"])
                        < VERDICT_ORDER.index(adjs[k]["verdict"])):
                    kept = {"_hits": adjs[k]["_hits"],
                            "_verdicts": adjs[k]["_verdicts"]}
                    adjs[k] = dict(c, **kept)
            else:
                adjs[k] = dict(c, _hits=1, _verdicts=[c["verdict"]])

        # own_findings の重複排除
        pass_owns = {}
        for x in data.get("own_findings") or []:
            c = clean_own(x)
            if not c:
                continue
            k = own_key(c)
            if k not in pass_owns:
                pass_owns[k] = c

        # クロスパスへのマージ
        for k, c in pass_owns.items():
            if k in owns:
                owns[k]["_hits"] += 1
            else:
                owns[k] = dict(c, _hits=1)

        # unverified の重複排除
        pass_unvers = {}
        for x in data.get("unverified") or []:
            c = clean_unver(x)
            if not c:
                continue
            k = own_key(c)
            if k not in pass_unvers:
                pass_unvers[k] = c

        # クロスパスへのマージ
        for k, c in pass_unvers.items():
            if k in unvers:
                unvers[k]["_hits"] += 1
            else:
                unvers[k] = dict(c, _hits=1)

    a = list(adjs.values())
    for x in a:
        x["_split"] = len(set(x["_verdicts"])) > 1

    order = {"high": 0, "medium": 1, "low": 2}
    a.sort(key=lambda x: (VERDICT_ORDER.index(x["verdict"]),
                          order.get(x["severity"], 9), -x["_hits"]))
    o = sorted(owns.values(),
               key=lambda x: (order.get(x["severity"], 9), -x["_hits"]))
    u = sorted(unvers.values(), key=lambda x: -x["_hits"])

    return {"passes": passes, "cost": cost, "summary": summary,
            "adjudications": a, "own_findings": o, "unverified": u}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default="raw_*.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    raws = []
    for path in sorted(glob.glob(a.glob)):
        try:
            raws.append(json.load(open(path, encoding="utf-8")))
        except Exception:
            print("skip (読めません): %s" % path)

    out = aggregate(raws)
    json.dump(out, open(a.out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("passes=%d adjudications=%d own=%d unverified=%d cost=$%.4f"
          % (out["passes"], len(out["adjudications"]),
             len(out["own_findings"]), len(out["unverified"]), out["cost"]))


if __name__ == "__main__":
    main()
