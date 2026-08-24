# [参考実装] 動的検証用。セッション固有の絶対パス(scratchpad/ck等)を含むため、
# 再利用時は BASE/HOST/Cookie保存先/probe対象TSVパスを環境に合わせて修正すること。
# 手順は tools/api-inventory/README.md の Phase 3 を参照。
import json,re,sys,collections
ROOTF="/home/mhaya/wekov2/"
P="/tmp/claude-1000/-home-mhaya-wekov2/a8119b60-023e-4882-84ac-a0edcfb5627e/scratchpad/api"
def load(p): return [l.rstrip("\n").split("\t") for l in open(p,encoding="utf-8") if l.rstrip("\n")]
rows=load(ROOTF+"weko3_api_list.tsv"); hd=rows[0]; data=rows[1:]
res=json.load(open(P+"/probe_results.json"))
# 500判定(method+urlキー)
byp=set()
for l in open(P+"/status500_verdict.tsv",encoding="utf-8"):
    a=l.rstrip("\n").split("\t")
    if len(a)>=3 and "到達" in a[2]: byp.add((a[0],a[1]))
def resolve(uri):
    u=uri
    for pat,val in [(r"<string:version>","v1"),(r"<uuid>","x:y:secret.png"),(r"<[^>]*api_code>","crf"),
      (r"<[^>]*index_id>","100100"),(r"<[^>]*journal_id>","1"),(r"<event>","top_page_access"),
      (r"<year>","2026"),(r"<month>","8"),(r"<[^>]*(file_name|filename|key)>","secret.png"),
      (r"<path:[^>]+>","secret.png"),(r"<[^>]*(pid_value|recid|identifier)>","1001"),
      (r"<[^>]*activity_id>","A-1"),(r"<[^>]*community_id>","comm1"),(r"<[^>]*(id|Id)>","1"),(r"<[^>]+>","1")]:
        u=re.sub(pat,val,u)
    return u

def kind(status, method=None, url=None):
    if status in ("302","401","403"): return "遮断"
    if status=="500":
        return "到達" if (method,url) in byp else "遮断"
    if status in ("404","405"): return "検証不能"
    if status in ("000","ERR"): return "無応答"
    if status and status[0] in "245": return "到達"   # 2xx/400/415/308
    return "?"

DVI=45
summary=collections.Counter()
for i,c in enumerate(data):
    if str(i) not in res: continue
    r=res[str(i)]; method=(c[4] or "GET").split(",")[0]; url=resolve(c[5])
    parts=[]; kinds={}
    for ident in ("anon","general","comadmin","repoadmin"):
        if ident in r:
            k=kind(r[ident],method,url); kinds[ident]=k
            parts.append(f"{ident}={r[ident]}({k})")
    # 判定: 最小権限で到達したものを重大度順に
    if kinds.get("anon")=="到達": v="未認証で到達"
    elif kinds.get("general")=="到達": v="ログインのみで到達"
    elif kinds.get("comadmin")=="到達": v="Community管理者で到達"
    elif kinds.get("repoadmin")=="到達": v="Repository管理者で到達"
    elif "検証不能" in kinds.values() and "到達" not in kinds.values(): v="検証不能(テストURL未解決)"
    else: v="測定範囲では遮断"
    summary[v]+=1
    while len(c)<=DVI: c.append("-")
    c[DVI]=f"[実測] {v} | "+"; ".join(parts)
with open(ROOTF+"weko3_api_list.tsv","w",encoding="utf-8") as f:
    f.write("\t".join(hd)+"\n")
    for c in data: f.write("\t".join(x.replace("\t"," ") for x in c)+"\n")
print("=== 実測判定サマリ(223フラグ付き) ===")
for k,n in summary.most_common(): print(f"  {n:4d}  {k}")
