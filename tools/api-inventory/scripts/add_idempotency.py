import ast,re,os
R="/home/mhaya/wekov2/"
def load(p): return [l.rstrip("\n").split("\t") for l in open(p,encoding="utf-8") if l.rstrip("\n")]
rows=load(R+"weko3_api_list.tsv"); hd=rows[0]; data=rows[1:]
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
open(R+"weko3_api_list.tsv","w",encoding="utf-8").write("\t".join(hd+["idempotency"])+"\n"+
    "\n".join("\t".join(str(x).replace("\t"," ") for x in c) for c in data)+"\n")
print("idempotency ★状態遷移:",nc,"列数:",len(hd)+1)
