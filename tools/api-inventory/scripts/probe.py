# [参考実装] 動的検証用。セッション固有の絶対パス(scratchpad/ck等)を含むため、
# 再利用時は BASE/HOST/Cookie保存先/probe対象TSVパスを環境に合わせて修正すること。
# 手順は tools/api-inventory/README.md の Phase 3 を参照。
# -*- coding: utf-8 -*-
"""全フラグ付きエンドポイントを実機で叩き、未認証+各ロールの実測結果を得る。"""
import re, subprocess, sys, json
ROOTF="/home/mhaya/wekov2/"
CK=ROOTF and "/tmp/claude-1000/-home-mhaya-wekov2/a8119b60-023e-4882-84ac-a0edcfb5627e/scratchpad/api/ck/"
BASE="https://localhost:8443"; HOST="weko3.example.org"

def load(p): return [l.rstrip("\n").split("\t") for l in open(p,encoding="utf-8") if l.rstrip("\n")]
rows=load(ROOTF+"weko3_api_list.tsv"); hd=rows[0]; data=rows[1:]

# プレースホルダ→実値
def resolve(uri):
    u=uri
    u=re.sub(r"<string:version>","v1",u)
    u=re.sub(r"<uuid>","6e74ad33-e886-4c27-8d10-45a160fae30c:c7718302-39fa-472b-92aa-81e61a9d9f4d:secret.png",u)
    u=re.sub(r"<[^>]*api_code>","crf",u)
    u=re.sub(r"<[^>]*version[^>]*>","v1",u)
    u=re.sub(r"<[^>]*index_id>","100100",u)
    u=re.sub(r"<[^>]*journal_id>","1",u)
    u=re.sub(r"<event>","top_page_access",u); u=re.sub(r"<year>","2026",u); u=re.sub(r"<month>","8",u)
    u=re.sub(r"<[^>]*(file_name|filename|key)>","secret.png",u)
    u=re.sub(r"<path:[^>]+>","secret.png",u)
    u=re.sub(r"<[^>]*(pid_value|recid|identifier)>","1001",u)
    u=re.sub(r"<[^>]*activity_id>","A-00000000-0000",u)
    u=re.sub(r"<[^>]*community_id>","comm1",u)
    u=re.sub(r"<[^>]*(id|Id)>","1",u)
    u=re.sub(r"<[^>]+>","1",u)   # 残り
    return u

def curl(method, url, cookie):
    args=["curl","-sk","-o","/dev/null","-w","%{http_code}","--max-time","12","-X",method.split(",")[0],
          "-H","Host: "+HOST]
    if cookie: args+=["-b",cookie]
    m=method.split(",")[0]
    if m in ("POST","PUT","PATCH"):
        args+=["-H","Content-Type: application/json","-d","{}"]
    args.append(BASE+url)
    try:
        return subprocess.run(args,capture_output=True,text=True,timeout=20).stdout.strip() or "000"
    except Exception:
        return "ERR"

IDN={"anon":None,"general":CK+"general.txt","comadmin":CK+"comadmin.txt","repoadmin":CK+"repoadmin.txt"}

results={}  # idx -> {ident:status}
flagged=[i for i,c in enumerate(data) if len(c)>=42 and c[41]!="-"]
print("flagged endpoints:",len(flagged),file=sys.stderr)
for n,i in enumerate(flagged):
    c=data[i]; method=c[4] or "GET"; url=resolve(c[5])
    admin = ("/admin" in c[5]) or ("/api/admin" in c[5])
    idents=["anon","general"] + (["comadmin","repoadmin"] if admin else [])
    # 破壊的メソッドは general までに留め、管理系のみ repoadmin も(環境は使い捨て)
    r={}
    for ident in idents:
        r[ident]=curl(method,url,IDN[ident])
    results[i]=r
    if n%25==0: print(f"  {n}/{len(flagged)}",file=sys.stderr)

json.dump({str(k):v for k,v in results.items()}, open(sys.argv[1],"w"))
print("done",len(results),file=sys.stderr)
