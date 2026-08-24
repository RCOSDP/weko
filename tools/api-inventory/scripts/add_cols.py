# -*- coding: utf-8 -*-
"""3観点列(csrf_protection/input_validation/audit_logged/triggers_task/resource_limit)をAST+実装から機械付与"""
import ast,re,os,collections
R="/home/mhaya/wekov2/"
def load(p): return [l.rstrip("\n").split("\t") for l in open(p,encoding="utf-8") if l.rstrip("\n")]
rows=load(R+"weko3_api_list.tsv"); hd=rows[0]; data=rows[1:]

# 実装関数のソース断片をキャッシュ
srccache={}
def get_src(fp,ln):
    key=(fp,ln)
    if key in srccache: return srccache[key]
    full=os.path.join(R,fp)
    if not os.path.isfile(full): srccache[key]=""; return ""
    try:
        lines=open(full,encoding="utf-8",errors="replace").read().splitlines()
        tree=ast.parse("\n".join(lines))
    except Exception:
        srccache[key]=""; return ""
    best=None
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            s=n.lineno; e=getattr(n,"end_lineno",n.lineno)
            if s<=int(ln)<=e and (best is None or (e-s)<(best[1]-best[0])):
                best=(s,e)
    seg="\n".join(lines[best[0]-1:best[1]]) if best else "\n".join(lines[max(0,int(ln)-1):int(ln)+30])
    srccache[key]=seg; return seg

def col_csrf(c,seg):
    m=c[4]; 
    if not re.search(r"POST|PUT|DELETE|PATCH",m): return "N/A(参照系)"
    if "csrf_random" in seg or "validate_csrf" in seg: return "手動csrf照合あり"
    # このアプリはCSRFProtect未初期化 → session認証の状態変更は無防備
    if c[21] in("session","session+guest") or "session" in c[21] or c[20]=="要":
        if "oauth" in c[21] or "Bearer" in seg or "require_api_auth" in seg: return "OAuth(CSRF非該当)"
        return "★CSRF保護なし(CSRFProtect未初期化・状態変更)"
    return "CSRF該当外(未認証public)"

def col_input(seg):
    has_schema = bool(re.search(r"\bSchema\(\)\.load|marshmallow|\.validate\(|use_kwargs|use_args", seg))
    raw_json = bool(re.search(r"get_json\(|request\.json|request\.form\.get|request\.values\.get|request\.data", seg))
    force = "force=True" in seg
    extract = "extractall(" in seg
    pathjoin = bool(re.search(r"os\.path\.join\([^)]*request|PyFSFileStorage\(|\.save\(", seg)) and "secure_filename" not in seg
    tags=[]
    if extract: tags.append("ZIP展開(slip検証要確認)")
    if pathjoin: tags.append("パス連結(secure_filename無)")
    if has_schema: tags.append("Schema検証あり")
    elif raw_json: tags.append("生入力(スキーマ検証なし"+("・force=True" if force else "")+")")
    return ";".join(tags) if tags else "-"

def col_audit(seg):
    m=re.findall(r"UserActivityLogger\.\w+\(\s*operation\s*=\s*[\"']?(\w+)", seg)
    if m: return "記録あり:"+",".join(sorted(set(m)))
    if "UserActivityLogger" in seg: return "記録あり(operation動的)"
    return "-"

def col_task(seg):
    t=re.findall(r"(\w+)\.(?:delay|apply_async|s)\(", seg)
    return ";".join(sorted(set(t))) if t else "-"

def col_reslimit(seg):
    if re.search(r"size\s*=\s*10000|WEKO_SEARCH_MAX_RESULT|max_result_window", seg): return "size=10000(全走査懸念)"
    if re.search(r"\.scan\(|scan_iter|for .* in .*all\(\)", seg): return "全走査/scan"
    return "-"

newcols=["csrf_protection","input_validation","audit_logged","triggers_task","resource_limit"]
for c in data:
    seg=get_src(c[13],c[14]) if c[14].isdigit() else ""
    c += [col_csrf(c,seg), col_input(seg), col_audit(seg), col_task(seg), col_reslimit(seg)]
open(R+"weko3_api_list.tsv","w",encoding="utf-8").write("\t".join(hd+newcols)+"\n"+
    "\n".join("\t".join(x.replace("\t"," ") for x in c) for c in data)+"\n")
# サマリ
for i,name in enumerate(newcols):
    ci=len(hd)+i
    cnt=collections.Counter()
    for c in data:
        v=c[ci] if len(c)>ci else "-"
        cnt["有" if v not in("-","N/A(参照系)","CSRF該当外(未認証public)","OAuth(CSRF非該当)") else "無/N-A"]+=1
    print(f"{name}: 有効値={cnt['有']}")
print("列数:",len(hd)+len(newcols))
