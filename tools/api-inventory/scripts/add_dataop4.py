# -*- coding: utf-8 -*-
"""data_op列: 取得/作成/更新/物理削除/論理削除 を実装から4区分評価

(旧 data_op_detail。data_op と統合したため書き込み先を data_op に変更)"""
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
    列位置前提(_col(c,"impl_file")=impl_file 等)が壊れる。
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

def _col(c, name, _cache={}):
    """列名で引く。列の統合・追加で位置がずれても壊れないようにするため。"""
    if not _cache:
        _cache.update({n: i for i, n in enumerate(hd)})
    i = _cache.get(name)
    return c[i] if i is not None and len(c) > i else ""


# ファイル全体をキャッシュし、関数本体＋同ファイル内で呼ぶヘルパも1段追う
filecache={}
def get_file(fp):
    if fp in filecache: return filecache[fp]
    full=os.path.join(R,fp)
    if not os.path.isfile(full): filecache[fp]=(None,None); return (None,None)
    try:
        txt=open(full,encoding="utf-8",errors="replace").read(); tree=ast.parse(txt)
    except: filecache[fp]=(None,None); return (None,None)
    lines=txt.splitlines()
    funcs={}
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            funcs[n.name]=(n.lineno,getattr(n,"end_lineno",n.lineno))
    filecache[fp]=(lines,funcs); return (lines,funcs)

def func_src(fp,ln):
    lines,funcs=get_file(fp)
    if not lines: return ""
    best=None
    for name,(s,e) in funcs.items():
        if s<=int(ln)<=e and (best is None or (e-s)<(best[2]-best[1])): best=(name,s,e)
    if not best: return ""
    seg="\n".join(lines[best[1]-1:best[2]])
    # 呼び出すヘルパ(同ファイル定義)を1段展開
    called=set(re.findall(r"\b([a-z_][a-z0-9_]*)\s*\(", seg))
    for cn in called:
        if cn in funcs and cn!=best[0]:
            s,e=funcs[cn]; 
            if e-s<200: seg+="\n"+"\n".join(lines[s-1:e])
    return seg

# パターン
PHYS=re.compile(r"db\.session\.delete\(|\.query\b[^\n]*\.delete\(\)|session\.execute\([^\n]*delete|os\.remove\(|shutil\.rmtree|storage\.delete\(|file_storage\.delete\(|\.remove\(\)|bucket\.remove|ObjectVersion[^\n]*\.remove")
LOGIC=re.compile(r"is_deleted\s*=\s*True|soft_delete|PIDStatus\.DELETED|\.delete\(\)\s*#?\s*soft|status\s*=\s*['\"]?D|delete_flag\s*=\s*True|mark.*deleted|logical")
CREATE=re.compile(r"\.create\(|db\.session\.add\(|\binsert\b|\.append\(.*db|new_|Create")
UPDATE=re.compile(r"\.update\(|db\.session\.merge\(|setattr\(|\.commit\(\)[^\n]*update|= request\.(form|json|values)")
READ=re.compile(r"\.get\(|\.query\b|\.filter|search|\.first\(\)|\.all\(\)|jsonify\(")

def eval4(c,seg,method):
    ops=[]
    if READ.search(seg) or method in("GET","HEAD"): ops.append("取得")
    if method in("POST","PUT","PATCH","DELETE"):
        if CREATE.search(seg): ops.append("作成")
        if UPDATE.search(seg): ops.append("更新")
        if LOGIC.search(seg): ops.append("論理削除")
        if PHYS.search(seg): ops.append("物理削除")
    # DELETEメソッドで何も拾えない場合
    if method=="DELETE" and not any(x in ops for x in("論理削除","物理削除")):
        ops.append("削除(方式不明)")
    return ";".join(dict.fromkeys(ops)) if ops else ("取得" if method in("GET","HEAD") else "-")

nc=0
for c in data:
    method=(_col(c,"method") or "GET").split(",")[0]
    fp=_col(c,"impl_file") if (len(c)>13) else ""; ln=_col(c,"impl_line") if len(c)>14 else "0"
    # ModelView/frameworkは実パス無し→methodベース
    if "ModelView" in _col(c,"api_type") or _col(c,"api_type")=="フレームワーク" or not str(ln).isdigit() or ln=="0":
        act=_col(c,"endpoint").split(".")[-1] if len(c)>11 else ""
        if act=="delete_view": v="物理削除(Flask-Admin ModelView.delete_model=db.session.delete)"
        elif act=="create_view": v="作成"
        elif act=="edit_view": v="更新"
        elif act in("index_view","details_view","export","ajax_lookup"): v="取得"
        elif method in("GET","HEAD"): v="取得"
        else: v="-"
    else:
        seg=func_src(fp,ln)
        v=eval4(c,seg,method)
    c.append(v)
    if "論理削除" in v or "物理削除" in v: nc+=1
_write(TSV, hd, data, ['data_op'])
print("data_op付与。削除系(論理/物理):",nc,"列数:",len(hd))
