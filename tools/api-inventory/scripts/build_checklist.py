# -*- coding: utf-8 -*-
"""詳細版(62列) → チェックリスト版(32列) に統合する。

出力列は schema.CHECKLIST_COLUMNS。列定義は schema.py を直す。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import data_path
from schema import CHECKLIST_COLUMNS
SRC = sys.argv[1] if len(sys.argv) > 1 else data_path("weko3_api_list_full.tsv")
DST = sys.argv[2] if len(sys.argv) > 2 else data_path("weko3_api_list.tsv")
def load(p): return [l.rstrip("\n").split("\t") for l in open(p,encoding="utf-8") if l.rstrip("\n")]
rows=load(SRC); hd=rows[0]; data=rows[1:]
H={name:i for i,name in enumerate(hd)}
def g(c,name): 
    i=H[name]; return c[i] if len(c)>i and c[i] not in("","-","不明") else ""

# 出力列は schema.py が唯一の正。ここに直接並べると README・テスト・台帳の
# どれかと必ずずれる(実測: 「24列」と書かれたまま実体は32列になっていた)。
NEW = CHECKLIST_COLUMNS

out=[NEW]
for c in data:
    def j(parts,sep=" | "): return sep.join(p for p in parts if p)
    impl = j([g(c,"impl_func"), (g(c,"impl_file")+(":"+g(c,"impl_line") if g(c,"impl_line") and g(c,"impl_line")!="0" else ""))], " @")
    # auth: 要否+方式+仕組み
    auth = j([g(c,"auth_required"), g(c,"auth_method"), "["+g(c,"auth_mechanism").split("(")[0]+"]" if g(c,"auth_mechanism") else ""])
    roles_scope = j([g(c,"roles"), ("scope:"+g(c,"oauth_scope")) if g(c,"oauth_scope") else ""])
    access_var = g(c,"access_variance")
    data_op = g(c,"data_op")
    data_store = g(c,"data_store")
    side = j([g(c,"side_effects"), ("task:"+g(c,"triggers_task")) if g(c,"triggers_task") else ""])
    # security_finding: sec_pattern中心にexposed/detail/evidenceを要約
    sf_parts=[g(c,"sec_pattern")]
    if g(c,"sec_exposed"): sf_parts.append("露出:"+g(c,"sec_exposed"))
    if g(c,"sec_evidence"): sf_parts.append(g(c,"sec_evidence"))
    security_finding=j(sf_parts, " ; ")
    # security_flags: 7観点を該当のみ集約
    flags=[]
    for col,label in [("csrf_protection","CSRF"),("input_validation","INPUT"),("audit_logged","AUDIT"),
                      ("resource_limit","RESLIMIT"),("redirect_target","REDIRECT"),("ssrf_surface","SSRF"),
                      ("idempotency","IDEMP"),("bola_risk","BOLA")]:
        v=g(c,col)
        if v and ("★" in v or "なし" in v or "slip" in v.lower() or "生入力" in v or "外部" in v or "冪等性なし" in v or "多重遷移" in v or "全走査" in v or "検証なし" in v):
            flags.append(f"{label}:{v[:40]}")
    security_flags=j(flags, " ; ")
    last_change=j([g(c,"last_commit"), g(c,"last_commit_date"), g(c,"release_tag")], " ")
    notes=j([g(c,"notes"), ("例外:"+g(c,"exceptions")) if g(c,"exceptions") else ""], " || ")
    resp=j([g(c,"response"), g(c,"status_codes")], " / ")

    out.append([
        g(c,"no"),g(c,"module"),g(c,"api_type"),g(c,"method"),g(c,"uri"),impl or "-",g(c,"summary") or "-",
        auth or "-", roles_scope or "-", access_var or "-", data_op or "-", data_store or "-", side or "-",
        security_finding or "-", security_flags or "-", g(c,"dynamic_verified") or "-",
        g(c,"api_version") or "-", g(c,"deprecated") or "-", g(c,"test_file") or "-", last_change or "-",
        g(c,"category_tags") or "-", notes or "-", g(c,"config_deps") or "-", resp or "-",
        g(c,"priority") or "-", g(c,"priority_reason") or "-",
        g(c,"test_normal") or "-", g(c,"test_abnormal") or "-",
        g(c,"test_boundary") or "-", g(c,"test_exception") or "-",
        g(c,"test_gap") or "-", g(c,"cleanup") or "-"
    ])
with open(DST,"w",encoding="utf-8") as f:
    for r in out: f.write("\t".join(str(x).replace("\t"," ").replace("\n"," ") for x in r)+"\n")
print("チェックリスト版:",len(out)-1,"行 ×",len(NEW),"列")
print("列:",NEW)
