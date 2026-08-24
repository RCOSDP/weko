# -*- coding: utf-8 -*-
"""auth_mechanism(認証の付け方3分類) と bola_risk(object-level認可の有無) を付与"""
import ast,re,os
R="/home/mhaya/wekov2/"
def load(p): return [l.rstrip("\n").split("\t") for l in open(p,encoding="utf-8") if l.rstrip("\n")]
rows=load(R+"weko3_api_list.tsv"); hd=rows[0]; data=rows[1:]

filecache={}
def get_file(fp):
    if fp in filecache: return filecache[fp]
    full=os.path.join(R,fp)
    if not os.path.isfile(full): filecache[fp]=(None,None); return (None,None)
    try:
        txt=open(full,encoding="utf-8",errors="replace").read(); tree=ast.parse(txt)
    except: filecache[fp]=(None,None); return (None,None)
    lines=txt.splitlines(); funcs={}
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
    called=set(re.findall(r"\b([a-z_][a-z0-9_]*)\s*\(", seg))
    for cn in called:
        if cn in funcs and cn!=best[0]:
            s,e=funcs[cn]
            if e-s<150: seg+="\n"+"\n".join(lines[s-1:e])
    return seg

# --- auth_mechanism: この行の認証はどこで定義されるか ---
def col_mech(c):
    at=c[2]  # api_type
    am=c[21] # auth_method
    if "ModelView" in at: return "modelview(Flask-Admin is_accessible/role_has_access)"
    if at=="フレームワーク": return "framework(invenio/flask-security既定)"
    # config駆動REST判定: uriに<string:version>やREST系、blueprintが*_rest
    bp=c[10]
    if bp.endswith("_rest") or bp.endswith("_rest2") or "REST" in c[11] or "_options" in c[11]:
        return "config-factory(*_REST_ENDPOINTS permission_factory_imp)"
    if am=="admin-role-table": return "modelview/admin(role_has_access)"
    if am in("none","rate-limit-only","不要") or c[20]=="不要": return "none(デコレータ無し・公開)"
    if "action-need" in am: return "decorator(@x_permission.require)"
    if "record-permission" in am: return "decorator(@need_record_permission)"
    if "files-action" in am: return "decorator(@need_permissions)+ActionRole(グローバル付与注意)"
    if "oauth" in am: return "decorator(@require_api_auth/@require_oauth_scopes)"
    if "session" in am: return "decorator(@login_required系)"
    if "custom" in am: return "decorator(@check_authority等カスタム)"
    return "decorator(その他)"

# --- bola_risk: object-level認可(所有者/対象単位チェック)が実装にあるか ---
OWNER=re.compile(r"created_by|check_created_id|owner|current_user\.(id|get_id)|weko_shared|can_edit|is_himself|has_permission|check_authority|activity_login_user|check_index_permission|permission_factory|need_record_permission|get_or_404|filter_by\([^)]*user")
def col_bola(c,seg):
    m=(c[4] or "GET").split(",")[0]
    # パスにリソースID(<...pid/id/recid...>)があるか
    has_id=bool(re.search(r"<[^>]*(pid_value|recid|id|identifier|bucket_id|activity_id|group_id|key)", c[5]))
    if not has_id: return "N/A(リソースID無し)"
    if "ModelView" in c[2]: return "admin-role-tableのみ(オブジェクト単位判定なし=管理者は全件)"
    if OWNER.search(seg): return "object-level認可あり(所有者/対象単位)"
    # sec_patternに所有者チェック欠落があれば実証済み
    if len(c)>41 and "所有者チェック欠落" in c[41]: return "★object-level認可なし(BOLA・実証済)"
    return "★object-level認可なし(要確認・ID直指定で他リソース操作の懸念)"

mech_c=collections.Counter() if False else {}
nb=0
import collections
mc=collections.Counter(); bc=collections.Counter()
for c in data:
    seg=func_src(c[13],c[14]) if (len(c)>14 and str(c[14]).isdigit() and c[14]!="0") else ""
    mech=col_mech(c); bola=col_bola(c,seg)
    c += [mech,bola]
    mc[mech.split("(")[0]]+=1; bc[bola.split("(")[0]]+=1
    if "★" in bola: nb+=1
open(R+"weko3_api_list.tsv","w",encoding="utf-8").write("\t".join(hd+["auth_mechanism","bola_risk"])+"\n"+
    "\n".join("\t".join(str(x).replace("\t"," ") for x in c) for c in data)+"\n")
print("=== auth_mechanism 分布 ==="); [print(f"  {n:4d} {k}") for k,n in mc.most_common()]
print("=== bola_risk 分布 ==="); [print(f"  {n:4d} {k}") for k,n in bc.most_common()]
print("列数:",len(hd)+2)
