import ast,re,os
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from paths import data_path as _data_path

# 入出力: 既定は $WEKO_API_INVENTORY_DIR/weko3_api_list_full.tsv を in-place 更新。
# 以前は R+"weko3_api_list.tsv"(24列版)を読み書きしており、いま実行すると
# 台帳を壊す状態だった(当時これが作業用中間ファイルだったころの名残)。
TSV = _sys.argv[1] if len(_sys.argv) > 1 else _data_path("weko3_api_list_full.tsv")


def _write(path, hd, data, newcols):
    """既存の同名列は **その位置のまま値を差し替える**。無い列だけ末尾に足す。

    末尾に付け直すと列順が変わり、README の awk 例や他スクリプトの
    列位置前提(c[13]=impl_file 等)が壊れる。
    """
    pos = {n: i for i, n in enumerate(hd)}
    add_cols = [n for n in newcols if n not in pos]
    out_hd = list(hd) + add_cols
    force = _os.environ.get("WEKO_INVENTORY_OVERWRITE") == "1"
    empty = ("", "-", "TODO")
    lines = ["\t".join(out_hd)]
    filled = 0
    for c in data:
        row = list(c) + [""] * (len(hd) - len(c))
        vals = row[len(hd):]              # このスクリプトが今回算出した値
        body = row[:len(hd)]
        for n, v in zip(newcols, vals):
            if n not in pos:
                continue
            cur = body[pos[n]]
            # 既存値は人手で精査されている。空欄/TODO のセルだけ埋める。
            # 一括再生成すると判定が劣化する(bola_risk が逆転、data_op_detail の
            # 論理/物理の区別が失われる、CSRF の指摘が消える等を実測で確認済み)。
            if cur in empty or force:
                if cur != v:
                    filled += 1
                body[pos[n]] = v
        extra = [v for n, v in zip(newcols, vals) if n not in pos]
        lines.append("\t".join(str(x).replace("\t", " ") for x in body + extra))
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"  → 空欄/TODO を埋めたセル: {filled}"
          + ("  (WEKO_INVENTORY_OVERWRITE=1 のため既存値も上書き)" if force else ""))
R = _os.environ.get("WEKO_ROOT", "/home/mhaya/wekov2") + "/"
def load(p): return [l.rstrip("\n").split("\t") for l in open(p,encoding="utf-8") if l.rstrip("\n")]
rows=load(TSV); hd=rows[0]; data=rows[1:]
srccache={}
def get_src(fp,ln):
    key=(fp,ln)
    if key in srccache: return srccache[key]
    full=os.path.join(R,fp)
    if not os.path.isfile(full) or not str(ln).isdigit() or ln=="0": srccache[key]=""; return ""
    try:
        lines=open(full,encoding="utf-8",errors="replace").read().splitlines(); tree=ast.parse("\n".join(lines))
    except: srccache[key]=""; return ""
    best=None
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            s=n.lineno; e=getattr(n,"end_lineno",n.lineno)
            if s<=int(ln)<=e and (best is None or (e-s)<(best[1]-best[0])): best=(s,e)
    seg="\n".join(lines[best[0]-1:best[1]]) if best else ""; srccache[key]=seg; return seg
def col_idem(c,seg):
    m=c[4].split(",")[0]
    if m in("GET","HEAD"): return "N/A(参照系)"
    if m in("PUT","DELETE"):
        # 状態チェックあれば冪等
        if re.search(r"status\s*!=|status\s*==|already|if.*exists|get_or_404|ActionStatus",seg): return "状態チェックあり(概ね冪等)"
        return "冪等性未確認(状態遷移PUT/DELETE)"
    if m=="POST":
        if re.search(r"action_status|ActionStatusPolicy|activity.*status|check_authority",seg): return "★状態遷移POST:二重送信で多重遷移の懸念(冪等性なし)"
        if re.search(r"\.create\(|insert|add\(",seg): return "作成POST:二重送信で重複作成の懸念"
        return "-"
    return "-"
nc=0
for c in data:
    seg=get_src(c[13],c[14]) if (len(c)>14) else ""
    v=col_idem(c,seg); c.append(v)
    if "★" in v: nc+=1
_write(TSV, hd, data, ['idempotency'])
print("idempotency ★状態遷移:",nc,"列数:",len(hd)+1)
