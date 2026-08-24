# -*- coding: utf-8 -*-
"""data_op_detail列: 取得/作成/更新/物理削除/論理削除 を実装から4区分評価"""
import ast,re,os
R="/home/mhaya/wekov2/"
def load(p): return [l.rstrip("\n").split("\t") for l in open(p,encoding="utf-8") if l.rstrip("\n")]
rows=load(R+"weko3_api_list.tsv"); hd=rows[0]; data=rows[1:]

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
    method=(c[4] or "GET").split(",")[0]
    fp=c[13] if (len(c)>13) else ""; ln=c[14] if len(c)>14 else "0"
    # ModelView/frameworkは実パス無し→methodベース
    if "ModelView" in c[2] or c[2]=="フレームワーク" or not str(ln).isdigit() or ln=="0":
        act=c[11].split(".")[-1] if len(c)>11 else ""
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
open(R+"weko3_api_list.tsv","w",encoding="utf-8").write("\t".join(hd+["data_op_detail"])+"\n"+
    "\n".join("\t".join(str(x).replace("\t"," ") for x in c) for c in data)+"\n")
print("data_op_detail付与。削除系(論理/物理):",nc,"列数:",len(hd)+1)
