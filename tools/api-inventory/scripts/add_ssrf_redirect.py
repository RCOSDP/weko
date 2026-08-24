# -*- coding: utf-8 -*-
"""redirect_target(オープンリダイレクト面) と ssrf_surface(SSRF面) を実装から機械付与"""
import ast,re,os
R="/home/mhaya/wekov2/"
def load(p): return [l.rstrip("\n").split("\t") for l in open(p,encoding="utf-8") if l.rstrip("\n")]
rows=load(R+"weko3_api_list.tsv"); hd=rows[0]; data=rows[1:]

srccache={}
def get_src(fp,ln):
    key=(fp,ln)
    if key in srccache: return srccache[key]
    full=os.path.join(R,fp)
    if not os.path.isfile(full) or not str(ln).isdigit(): srccache[key]=""; return ""
    try:
        lines=open(full,encoding="utf-8",errors="replace").read().splitlines()
        tree=ast.parse("\n".join(lines))
    except Exception: srccache[key]=""; return ""
    best=None
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            s=n.lineno; e=getattr(n,"end_lineno",n.lineno)
            if s<=int(ln)<=e and (best is None or (e-s)<(best[1]-best[0])): best=(s,e)
    seg="\n".join(lines[best[0]-1:best[1]]) if best else ""
    srccache[key]=seg; return seg

REDIR_UNSAFE=re.compile(r"redirect\([^)]*(request\.(args|values|form|referrer|full_path)|session\[['\"]next)")
REDIR_ANY=re.compile(r"\bredirect\(")
URLVALIDATE=re.compile(r"is_safe_url|url_has_allowed_host|validate_redirect|urlparse.*netloc")
SSRF=re.compile(r"requests\.(get|post|put|delete|head)\(|urlopen\(|urllib.*urlopen")
SSRF_USERURL=re.compile(r"requests\.\w+\(\s*[^)]*(request\.|_url|list_url|base_url|\+ *index|\+ *tmpindex|format\()")

def col_redirect(seg):
    if not REDIR_ANY.search(seg): return "-"
    if REDIR_UNSAFE.search(seg):
        safe="(host検証あり)" if URLVALIDATE.search(seg) else "★検証なし"
        return f"外部入力でリダイレクト先決定{safe}"
    return "内部リダイレクト(固定/url_for)"

def col_ssrf(seg):
    if not SSRF.search(seg): return "-"
    if SSRF_USERURL.search(seg):
        return "★外部/設定URLへHTTP発行(SSRF面)"
    return "外部HTTP(固定URL)"

newcols=["redirect_target","ssrf_surface"]
nr=ns=0
for c in data:
    seg=get_src(c[13],c[14]) if (len(c)>14 and str(c[14]).isdigit() and c[14]!="0") else ""
    r=col_redirect(seg); s=col_ssrf(seg)
    if "★" in r: nr+=1
    if "★" in s: ns+=1
    c += [r,s]
open(R+"weko3_api_list.tsv","w",encoding="utf-8").write("\t".join(hd+newcols)+"\n"+
    "\n".join("\t".join(str(x).replace("\t"," ") for x in c) for c in data)+"\n")
print(f"redirect_target ★検証なし:{nr}  ssrf_surface ★:{ns}  列数:{len(hd)+2}")
