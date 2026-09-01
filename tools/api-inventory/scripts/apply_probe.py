# [参考実装] 動的検証用。セッション固有の絶対パス(scratchpad/ck等)を含むため、
# 再利用時は BASE/HOST/Cookie保存先/probe対象TSVパスを環境に合わせて修正すること。
# 手順は tools/api-inventory/README.md の Phase 3 を参照。
# -*- coding: utf-8 -*-
import json,re
ROOTF="/home/mhaya/wekov2/"
def load(p): return [l.rstrip("\n").split("\t") for l in open(p,encoding="utf-8") if l.rstrip("\n")]
rows=load(ROOTF+"weko3_api_list.tsv"); hd=rows[0]; data=rows[1:]
res=json.load(open(ROOTF.replace("/home/mhaya/wekov2/","")+"/tmp/claude-1000/-home-mhaya-wekov2/a8119b60-023e-4882-84ac-a0edcfb5627e/scratchpad/api/probe_results.json"))

def cls(st):
    if st in ("302","401","403"): return "遮断"
    if st in ("404","405"): return "経路なし/不許可"
    if st=="000" or st=="ERR": return "無応答"
    if st.startswith("2"): return "到達/成功"
    if st.startswith("4"): return "到達(handler4xx)"
    if st.startswith("5"): return "到達(handler5xx)"
    return st

# 既存の統合列(42-46)はそのまま残し、動的実測を上書き強化する47列目相当は作らず
# 46 dynamic_verified を実測ベースで全面的に書き換える
DVI=45  # 0-based index of dynamic_verified (46th col)
for i,c in enumerate(data):
    key=str(i)
    if key not in res:
        continue
    r=res[key]
    parts=[]
    for ident in ("anon","general","comadmin","repoadmin"):
        if ident in r:
            parts.append(f"{ident}={r[ident]}({cls(r[ident])})")
    measured="; ".join(parts)
    # 判定サマリ
    anon=r.get("anon",""); gen=r.get("general","")
    def reached(s): return s.startswith("2") or s.startswith("4") and s not in("401","403","404","405") or s.startswith("5")
    verdict=""
    if reached(anon): verdict="未認証で到達"
    elif gen and reached(gen): verdict="ログインのみで到達"
    elif r.get("comadmin","") and reached(r["comadmin"]): verdict="Community管理者で到達"
    elif r.get("repoadmin","") and reached(r["repoadmin"]): verdict="Repository管理者で到達"
    else: verdict="全ロールで遮断/未到達"
    # 既存のdynamic_verified(実機で個別確認済みの詳細)があれば前置
    prev=c[DVI] if len(c)>DVI and c[DVI]!="-" else ""
    combined=(prev+" || " if prev else "")+f"[実測] {verdict} : {measured}"
    while len(c)<=DVI: c.append("-")
    c[DVI]=combined

with open(ROOTF+"weko3_api_list.tsv","w",encoding="utf-8") as f:
    f.write("\t".join(hd)+"\n")
    for c in data: f.write("\t".join(x.replace("\t"," ") for x in c)+"\n")

# サマリ
import collections
cnt=collections.Counter()
for i,c in enumerate(data):
    if str(i) in res:
        v=c[DVI]
        for k in ("未認証で到達","ログインのみで到達","Community管理者で到達","Repository管理者で到達","全ロールで遮断"):
            if k in v: cnt[k]+=1; break
for k,n in cnt.most_common(): print(f"{n:4d}  {k}")
print("total measured:",sum(cnt.values()))
