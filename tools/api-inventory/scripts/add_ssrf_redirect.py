# -*- coding: utf-8 -*-
"""redirect_target(オープンリダイレクト面) と ssrf_surface(SSRF面) を実装から機械付与"""
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
    seg=get_src(_col(c,"impl_file"),_col(c,"impl_line")) if (str(_col(c,"impl_line")).isdigit() and _col(c,"impl_line")!="0") else ""
    r=col_redirect(seg); s=col_ssrf(seg)
    if "★" in r: nr+=1
    if "★" in s: ns+=1
    c += [r,s]
_write(TSV, hd, data, ['redirect_target', 'ssrf_surface'])
print(f"redirect_target ★検証なし:{nr}  ssrf_surface ★:{ns}  列数:{len(hd)}")
