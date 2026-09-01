# -*- coding: utf-8 -*-
"""3観点列(csrf_protection/input_validation/audit_logged/triggers_task/resource_limit)をAST+実装から機械付与"""
import ast,re,os,collections
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
    m=_col(c,"method"); 
    if not re.search(r"POST|PUT|DELETE|PATCH",m): return "N/A(参照系)"
    if "csrf_random" in seg or "validate_csrf" in seg: return "手動csrf照合あり"
    # このアプリはCSRFProtect未初期化 → session認証の状態変更は無防備
    if _col(c,"auth_method") in("session","session+guest") or "session" in _col(c,"auth_method") or _col(c,"auth_required")=="要":
        if "oauth" in _col(c,"auth_method") or "Bearer" in seg or "require_api_auth" in seg: return "OAuth(CSRF非該当)"
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
    seg=get_src(_col(c,"impl_file"),_col(c,"impl_line")) if _col(c,"impl_line").isdigit() else ""
    c += [col_csrf(c,seg), col_input(seg), col_audit(seg), col_task(seg), col_reslimit(seg)]
_write(TSV, hd, data, ['csrf_protection', 'input_validation', 'audit_logged', 'triggers_task', 'resource_limit'])
# サマリ
for i,name in enumerate(newcols):
    ci=len(hd)+i
    cnt=collections.Counter()
    for c in data:
        v=c[ci] if len(c)>ci else "-"
        cnt["有" if v not in("-","N/A(参照系)","CSRF該当外(未認証public)","OAuth(CSRF非該当)") else "無/N-A"]+=1
    print(f"{name}: 有効値={cnt['有']}")
print("列数:", len(hd))
