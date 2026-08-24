# -*- coding: utf-8 -*-
"""auth_mechanism(認証の付け方3分類) と bola_risk(object-level認可の有無) を付与"""
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
    at=_col(c,"api_type")  # api_type
    am=_col(c,"auth_method") # auth_method
    if "ModelView" in at: return "modelview(Flask-Admin is_accessible/role_has_access)"
    if at=="フレームワーク": return "framework(invenio/flask-security既定)"
    # config駆動REST判定: uriに<string:version>やREST系、blueprintが*_rest
    bp=_col(c,"blueprint")
    if bp.endswith("_rest") or bp.endswith("_rest2") or "REST" in _col(c,"endpoint") or "_options" in _col(c,"endpoint"):
        return "config-factory(*_REST_ENDPOINTS permission_factory_imp)"
    if am=="admin-role-table": return "modelview/admin(role_has_access)"
    if am in("none","rate-limit-only","不要") or _col(c,"auth_required")=="不要": return "none(デコレータ無し・公開)"
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
    m=(_col(c,"method") or "GET").split(",")[0]
    # パスにリソースID(<...pid/id/recid...>)があるか
    has_id=bool(re.search(r"<[^>]*(pid_value|recid|id|identifier|bucket_id|activity_id|group_id|key)", _col(c,"uri")))
    if not has_id: return "N/A(リソースID無し)"
    if "ModelView" in _col(c,"api_type"): return "admin-role-tableのみ(オブジェクト単位判定なし=管理者は全件)"
    if OWNER.search(seg): return "object-level認可あり(所有者/対象単位)"
    # sec_patternに所有者チェック欠落があれば実証済み
    if "所有者チェック欠落" in _col(c,"sec_pattern"): return "★object-level認可なし(BOLA・実証済)"
    return "★object-level認可なし(要確認・ID直指定で他リソース操作の懸念)"

mech_c=collections.Counter() if False else {}
nb=0
import collections
mc=collections.Counter(); bc=collections.Counter()
for c in data:
    seg=func_src(_col(c,"impl_file"),_col(c,"impl_line")) if (str(_col(c,"impl_line")).isdigit() and _col(c,"impl_line")!="0") else ""
    mech=col_mech(c); bola=col_bola(c,seg)
    c += [mech,bola]
    mc[mech.split("(")[0]]+=1; bc[bola.split("(")[0]]+=1
    if "★" in bola: nb+=1
_write(TSV, hd, data, ['auth_mechanism', 'bola_risk'])
print("=== auth_mechanism 分布 ==="); [print(f"  {n:4d} {k}") for k,n in mc.most_common()]
print("=== bola_risk 分布 ==="); [print(f"  {n:4d} {k}") for k,n in bc.most_common()]
print("列数:",len(hd)+2)
