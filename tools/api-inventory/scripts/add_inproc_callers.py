# -*- coding: utf-8 -*-
"""台帳に `inproc_callers` 列(in-process からの呼び出し元)を付与する。

## なぜ要るのか

台帳は `extract_routes.py` が拾う Flask のルートを単位にしている。
そのため「ビュー関数が HTTP を通らず、別モジュールから直接呼ばれる」
第二の入口はどの列にも現れない。ルート単位で認可を足していく作業では、
この入口が視界に入らないまま素通りする。

issue62807 はその実例。`soft_delete` の行は auth_required=要 /
test_gap=- で穴が無いように見えていたが、実際には
`weko_items_ui.views.prepare_delete_item` が
``soft_delete(del_value)`` と位置引数で直接呼んでおり、
v2.0.4 で足した `record_edit_permission_required` が recid を
見つけられず abort(400) して、全ユーザがアイテムを削除できなくなった。

この列があれば「認可を足す前に、HTTP 以外の呼び出し元を確認する」
判断ができる。

## 値の形式

    -                                    in-process からの呼び出しなし
    位置引数:<file>:<line>;kwargs:<file>:<line>
        呼び出し元を列挙する。位置引数のものを先に置く
        (kwargs しか見ないデコレータが壊れるのは位置引数の側)。

## 使い方

    export WEKO_API_INVENTORY_DIR=/path/to/weko-secret
    WEKO_ROOT=/home/mhaya/wekov2 python3 add_inproc_callers.py

既存値は上書きしない(空欄/TODO のみ埋める)。判定を入れ直したいときは
``WEKO_INVENTORY_OVERWRITE=1`` を付ける。add_cols.py と同じ規約。

CI では台帳に書かず、**台帳がまだ知らない呼び出し元**だけを見る:

    python3 add_inproc_callers.py --check --summary-only --gate

認可を足す PR でこの件数が増えたら、そのビューには HTTP 以外の入口がある。
デコレータがそちらでも成立するかを確かめてからマージすること。
``--summary-only`` は件数だけを出す (CI のログ・artifact・PR コメントは
誰でも読めるため。他のスクリプトと同じ方針)。
"""
import collections
import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from paths import data_path as _data_path                      # noqa: E402
from audit_inprocess_views import (                            # noqa: E402
    collect_imports, collect_views, positional_calls,
)

# 既定は $WEKO_API_INVENTORY_DIR/weko3_api_list_full.tsv。
# 位置引数で別のパスを渡せる (argparse 側の default)。
TSV = _data_path("weko3_api_list_full.tsv")

COL = "inproc_callers"


def load(p):
    return [l.rstrip("\n").split("\t")
            for l in open(p, encoding="utf-8") if l.rstrip("\n")]


def _write(path, hd, data, newcols):
    """add_cols.py の _write と同じ規約。

    既存の同名列はその位置のまま値を差し替え、無い列だけ末尾に足す。
    既存値は人手で精査されているので、空欄/TODO のセルだけ埋める。
    """
    pos = {n: i for i, n in enumerate(hd)}
    out_hd = list(hd) + [n for n in newcols if n not in pos]
    force = _os.environ.get("WEKO_INVENTORY_OVERWRITE") == "1"
    empty = ("", "-", "TODO")
    lines = ["\t".join(out_hd)]
    filled = 0
    for c in data:
        row = list(c) + [""] * (len(hd) - len(c))
        vals = row[len(hd):]
        body = row[:len(hd)]
        for n, v in zip(newcols, vals):
            if n not in pos:
                continue
            cur = body[pos[n]]
            if cur in empty or force:
                if cur != v:
                    filled += 1
                body[pos[n]] = v
        extra = [v for n, v in zip(newcols, vals) if n not in pos]
        lines.append("\t".join(str(x).replace("\t", " ")
                               for x in body + extra))
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("  → 空欄/TODO を埋めたセル: {}{}".format(
        filled,
        "  (WEKO_INVENTORY_OVERWRITE=1 のため既存値も上書き)" if force else ""))


def build_index():
    """{(impl_file, impl_func): [呼び出し元の説明文字列]}"""
    views = collect_views()
    idx = collections.defaultdict(list)
    for mod, name, importer, line in collect_imports():
        v = views.get((mod, name))
        if v is None or importer == v["file"]:
            continue
        pos_lines = positional_calls(importer, {name}).get(name, [])
        if pos_lines:
            for ln in pos_lines:
                idx[(v["file"], v["func"])].append(
                    "位置引数:{}:{}".format(importer, ln))
        else:
            idx[(v["file"], v["func"])].append(
                "kwargs:{}:{}".format(importer, line))
    # 位置引数のものを先に、あとは安定順で
    for k in idx:
        idx[k] = sorted(set(idx[k]),
                        key=lambda s: (not s.startswith("位置引数"), s))
    return idx


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("tsv", nargs="?", default=TSV)
    ap.add_argument("--check", action="store_true",
                    help="台帳に書かず、ソースと台帳のズレだけを報告する(CI 用)")
    ap.add_argument("--summary-only", action="store_true",
                    help="件数だけ出す (CI 用。ログが公開されるため)")
    ap.add_argument("--gate", action="store_true",
                    help="台帳に無い in-process 呼び出しがあれば終了コード1")
    args = ap.parse_args()

    rows = load(args.tsv)
    hd, data = rows[0], rows[1:]
    cache = {n: i for i, n in enumerate(hd)}

    def col(c, name):
        i = cache.get(name)
        return c[i] if i is not None and len(c) > i else ""

    idx = build_index()

    if args.check:
        # 台帳が把握していない in-process 呼び出しを洗う。
        # 認可を足す PR でこれが増えたら、そのビューには第二の入口がある。
        drift = []
        for c in data:
            found = set(idx.get((col(c, "impl_file"), col(c, "impl_func")), []))
            recorded = set(x for x in col(c, COL).split(";") if x and x != "-")
            new_callers = sorted(found - recorded)
            if new_callers:
                drift.append((col(c, "method"), col(c, "uri"), new_callers))
        if args.summary_only:
            print("台帳に無い in-process 呼び出し: {} 件".format(len(drift)))
        else:
            for m, uri, callers in drift:
                print("[新規] {} {}  ← {}".format(m, uri, ";".join(callers)))
            print("\n台帳に無い in-process 呼び出し: {} 件".format(len(drift)))
        return 1 if (args.gate and drift) else 0

    for c in data:
        c.append(";".join(idx.get((col(c, "impl_file"),
                                   col(c, "impl_func")), [])) or "-")

    _write(args.tsv, hd, data, [COL])

    ci = cache.get(COL, len(hd))
    hits = [c for c in data if len(c) > ci and c[ci] not in ("", "-")]
    if args.summary_only:
        print("{}: 呼び出し元あり={} 件 / 全 {} 行".format(
            COL, len(hits), len(data)))
    else:
        print("{}: 呼び出し元あり={} 件 / 全 {} 行".format(
            COL, len(hits), len(data)))
        for c in hits:
            print("  {} {}  ← {}".format(col(c, "method"), col(c, "uri"), c[ci]))
        print("列数:", len(hd) + (0 if COL in cache else 1))
    return 0


if __name__ == "__main__":
    _sys.exit(main())
