#!/usr/bin/env python3
"""確度の高い修正案を inline suggestion として投稿する。

GitHub は差分の右側に現れる行にしか inline comment を付けられない。
どの行が対象かは diff.patch のハンク見出しから機械的に決める。
Claude の自己申告した行番号は検証に使うだけで、そのまま信用しない。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
FIX_MARK = re.compile(r"<!-- claude-fix:([0-9a-f]{12}) -->")

# REST の pulls/{n}/comments が返す user.login は "github-actions[bot]"
# （角括弧つき）。GraphQL の author.login で使う "github-actions" とは
# 表記が異なるので混同しないこと。
#
# 本文全体ではなく 1 行目だけを取り出す。`replacement` はコードとして
# エスケープせずにそのまま本文に埋め込むため、そこに
# `# <!-- claude-fix:<他の提案のhash> -->` のようなコメントを混ぜられると、
# 投稿者フィルタ（bot 自身の投稿）を通過したうえで別の提案のハッシュを
# 偽装できてしまう（本物の bot コメントの中に偽マーカーが混入する）。
# マーカーは BODY テンプレートで必ず 1 行目に置いているので、1 行目だけを
# 対象にすればこの経路は塞げる。本文が \r\n 区切りでも split("\n")[0] の
# 結果の末尾に \r が残るだけで、FIX_MARK の正規表現はその手前のマーカーに
# 一致する。
EXISTING_COMMENTS_JQ = ('.[] | select(.user.login=="github-actions[bot]") '
                        '| .body | split("\\n")[0]')

BODY = """<!-- claude-fix:%s -->
**%s**

%s

%ssuggestion
%s
%s
"""

# title / reason / detail はすべて Claude の出力由来で、その元は公開 PR に
# 誰でも書けるレビューコメント。github-actions[bot] として public リポジトリに
# 投稿されるため、コードフェンスの外に置くものは必ずエスケープする。
# （render.py の _esc() / _fence() と同じ考え方。post_inline.py は独立した
# CLI スクリプトのため import はせず、同じロジックをここに複製する。）


def _esc(s) -> str:
    """コードフェンスの外に置く外部由来文字列をエスケープする。

    `<`/`>` を変換して HTML タグとしての解釈を防ぐ（`&` は変換しない —
    二重エスケープになるため）。改行は半角スペース 1 つに畳み込み、
    偽の見出しや区切り線を本文の構造に注入できないようにする。
    """
    s = str(s)
    s = s.replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"\r\n|\r|\n", " ", s)


def _fence(content: str) -> str:
    """内容を安全に囲めるコードフェンスを返す。

    中身に含まれるバッククォートの連続の最大長 + 1（最小 3）の長さにする。
    GitHub が suggestion ブロックとして解釈するのは info string が
    ちょうど "suggestion" の場合のみなので、フェンスの本数を増やしても
    直後に続く "suggestion" という文字列自体は変えない。
    replacement 自体はエスケープしない（コードとして読ませるため、
    フェンス長を計算で確保することが封じ込めの手段になる）。
    """
    runs = re.findall(r"`+", content)
    longest = max((len(r) for r in runs), default=0)
    return "`" * max(3, longest + 1)


def changed_lines(diff_text: str) -> dict:
    """ファイルごとに、差分の右側に現れる行番号の集合を返す。"""
    out, path = {}, None
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            p = line[4:].strip()
            if p == "/dev/null":
                path = None                    # 削除されたファイル
            else:
                path = p[2:] if p.startswith("b/") else p
                out.setdefault(path, set())
            continue
        if line.startswith("--- "):
            continue
        m = HUNK.match(line)
        if m and path:
            start = int(m.group(1))
            count = 1 if m.group(2) is None else int(m.group(2))
            out[path].update(range(start, start + count))
    return {k: v for k, v in out.items() if v}


def fix_hash(fx: dict) -> str:
    key = "%s:%s:%s:%s" % (fx["file"], fx["start_line"], fx["end_line"],
                           fx["replacement"])
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def _candidate(fx: dict, title: str, reason: str, changed: dict,
               existing: set):
    if fx.get("kind") != "suggestion":
        return None
    lines = changed.get(fx["file"])
    if not lines:
        return None
    if not all(n in lines for n in range(fx["start_line"], fx["end_line"] + 1)):
        return None                            # 差分外には付けられない
    h = fix_hash(fx)
    if h in existing:
        return None                            # 投稿済み
    fence = _fence(fx["replacement"])
    item = {"path": fx["file"], "line": fx["end_line"], "side": "RIGHT",
            "body": BODY % (h, _esc(title), _esc(reason or fx.get("note") or ""),
                            fence, fx["replacement"], fence),
            "_hash": h}
    if fx["start_line"] != fx["end_line"]:
        # start_line == line で送ると GitHub が 422 を返す
        item["start_line"] = fx["start_line"]
        item["start_side"] = "RIGHT"
    return item


def select(findings: dict, changed: dict, existing: set) -> list:
    out, seen = [], set(existing)
    for a in findings.get("adjudications") or []:
        if a["verdict"] != "valid":
            continue
        c = _candidate(a["fix"], a["title"], a.get("reason", ""), changed, seen)
        if c:
            seen.add(c["_hash"])
            out.append(c)
    for o in findings.get("own_findings") or []:
        if not str(o.get("verified") or "").strip():
            continue                           # 裏取りの記録が無いものは出さない
        c = _candidate(o["fix"], o["title"], o.get("detail", ""), changed, seen)
        if c:
            seen.add(c["_hash"])
            out.append(c)
    return out


def existing_hashes(owner: str, repo: str, pr: int) -> set:
    """投稿済みハッシュを集める。

    PR には誰でもコメントできる。フィルタを付けずに全コメントの本文から
    マーカーを拾うと、攻撃者が自分のコメントに `<!-- claude-fix:<hash> -->`
    を書き込むだけでハッシュを偽造できてしまい、`select()` が本物の修正案を
    「投稿済み」として黙って抑止してしまう（file/start_line/end_line/
    replacement から決定的に計算されるハッシュは、差分から公開されている
    情報だけで事前計算できる）。そのため、この bot 自身
    （`github-actions[bot]`）が投稿したコメントだけに絞る。
    """
    proc = subprocess.run(
        ["gh", "api", "--paginate",
         "repos/%s/%s/pulls/%d/comments" % (owner, repo, pr),
         "--jq", EXISTING_COMMENTS_JQ],
        capture_output=True, text=True, check=True)
    return set(FIX_MARK.findall(proc.stdout))


def post(owner: str, repo: str, pr: int, head_sha: str, item: dict) -> bool:
    payload = {k: v for k, v in item.items() if not k.startswith("_")}
    payload["commit_id"] = head_sha
    proc = subprocess.run(
        ["gh", "api", "--method", "POST",
         "repos/%s/%s/pulls/%d/comments" % (owner, repo, pr), "--input", "-"],
        input=json.dumps(payload), capture_output=True, text=True)
    if proc.returncode != 0:
        # 1 件の失敗で全体を落とさない。集約コメントの投稿は必ず行う。
        print("::warning::inline 投稿に失敗 %s:%s — %s"
              % (item["path"], item["line"], proc.stderr.strip()[:300]))
        return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--owner", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--findings", required=True)
    ap.add_argument("--diff", required=True)
    ap.add_argument("--reviews", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    findings = json.load(open(a.findings, encoding="utf-8"))
    diff = open(a.diff, encoding="utf-8", errors="replace").read()
    head_sha = json.load(open(a.reviews, encoding="utf-8"))["head_sha"]

    changed = changed_lines(diff)
    existing = set() if a.dry_run else existing_hashes(a.owner, a.repo, a.pr)
    items = select(findings, changed, existing)
    print("投稿候補 %d 件 (既投稿 %d 件)" % (len(items), len(existing)))

    if a.dry_run:
        for it in items:
            print("--- %s:%s\n%s" % (it["path"], it["line"], it["body"]))
        return

    ok = sum(1 for it in items if post(a.owner, a.repo, a.pr, head_sha, it))
    print("投稿 %d / %d" % (ok, len(items)))


if __name__ == "__main__":
    main()
