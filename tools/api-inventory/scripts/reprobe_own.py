# [参考実装] 動的検証用。セッション固有の絶対パス(scratchpad/ck等)を含むため、
# 再利用時は BASE/HOST/Cookie保存先/probe対象TSVパスを環境に合わせて修正すること。
# 手順は tools/api-inventory/README.md の Phase 3 を参照。
import subprocess,sys,re,json
S="/tmp/claude-1000/-home-mhaya-wekov2/a8119b60-023e-4882-84ac-a0edcfb5627e/scratchpad/api"
BASE="https://localhost:8443";HOST="weko3.example.org"
def resolve(uri):
    u=uri
    for pat,val in [(r"<string:version>","v1"),(r"<uuid>","6e74ad33-e886-4c27-8d10-45a160fae30c:c7718302-39fa-472b-92aa-81e61a9d9f4d:secret.png"),
      (r"<[^>]*api_code>","crf"),(r"<[^>]*index_id>","100100"),(r"<[^>]*journal_id>","1"),
      (r"<event>","top_page_access"),(r"<year>","2026"),(r"<month>","8"),
      (r"<[^>]*(file_name|filename|key)>","secret.png"),(r"<path:[^>]+>","secret.png"),
      (r"<[^>]*group_id>","1"),(r"<[^>]*(resync_id|repo_id|resource_id)>","1"),
      (r"<[^>]*(pid_value|recid|identifier)>","1001"),(r"<[^>]*activity_id>","A-1"),
      (r"<[^>]*community_id>","comm1"),(r"<[^>]*(id|Id)>","1"),(r"<[^>]+>","1")]:
        u=re.sub(pat,val,u)
    return u
def login(name,email):
    subprocess.run(["curl","-sk","-c",f"{S}/ck/{name}.txt","-o","/dev/null","--max-time","10","-H","Host: "+HOST,
      "-X","POST",BASE+"/api/v1/login","-H","Content-Type: application/json",
      "-d",json.dumps({"email":email,"password":"Passw0rd!123"})],capture_output=True,timeout=15)
def curl(method,url,ck):
    a=["curl","-sk","-o","/dev/null","-w","%{http_code}","--max-time","12","-X",method,"-H","Host: "+HOST]
    if ck:a+=["-b",ck]
    if method in("POST","PUT","PATCH"):a+=["-H","Content-Type: application/json","-d","{}"]
    a.append(BASE+url)
    try:return subprocess.run(a,capture_output=True,text=True,timeout=18).stdout.strip() or "000"
    except:return "ERR"
USERS={"general":"user@example.org","contributor":"contributor@example.org","comadmin":"comadmin@example.org","repoadmin":"repoadmin@example.org"}
items=[l.rstrip("\n").split("\t") for l in open(S+"/own83.tsv")]
out={}
# identityごとに: 直前ログイン→全件パス（sentinelで鮮度確認）
for ident,email in USERS.items():
    login(ident,email); ck=f"{S}/ck/{ident}.txt"
    sent=curl("GET","/accounts/settings/groups/1/manage",ck)  # sentinel(200期待)
    for idx,method,uri,ep in items:
        out.setdefault(idx,{})[ident]=curl(method.split(",")[0],resolve(uri),ck)
    sent2=curl("GET","/accounts/settings/groups/1/manage",ck)
    print(f"{ident}: sentinel start={sent} end={sent2}",file=sys.stderr)
# anon
for idx,method,uri,ep in items:
    out.setdefault(idx,{})["anon"]=curl(method.split(",")[0],resolve(uri),None)
json.dump(out,open(sys.argv[1],"w"))
print("done",len(out),file=sys.stderr)
