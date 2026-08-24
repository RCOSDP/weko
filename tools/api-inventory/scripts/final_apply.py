# [参考実装] 動的検証用。セッション固有の絶対パス(scratchpad/ck等)を含むため、
# 再利用時は BASE/HOST/Cookie保存先/probe対象TSVパスを環境に合わせて修正すること。
# 手順は tools/api-inventory/README.md の Phase 3 を参照。
import json,re,sys,collections
R="/home/mhaya/wekov2/"; P="/tmp/claude-1000/-home-mhaya-wekov2/a8119b60-023e-4882-84ac-a0edcfb5627e/scratchpad/api"
def load(p): return [l.rstrip("\n").split("\t") for l in open(p,encoding="utf-8") if l.rstrip("\n")]
rows=load(R+"weko3_api_list.tsv"); hd=rows[0]; data=rows[1:]
res=json.load(open(P+"/probe_results2.json"))
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
def kind(st,mth,url):
    if st in("302","401","403"): return "遮断"
    if st=="500": return "到達" if (mth,url) in byp else "遮断"
    if st in("404","405"): return "検証不能"
    if st in("000","ERR"): return "無応答"
    if st and st[0] in "245": return "到達"
    return "?"
# 25補正(正URLで再測済み) endpoint+method -> 文字列
fix={
 ("invenio_communities_rest.communities_item","GET"):"未認証で到達|anon=200; general=200 ※コミュニティ詳細を未認証取得",
 ("invenio_files_rest.object_api","GET"):"測定範囲では遮断|anon=404(files-rest hidden権限拒否)",
 ("invenio_files_rest.object_api","DELETE"):"測定範囲では遮断|anon=404(hidden)",
 ("invenio_files_rest.object_api","POST"):"測定範囲では遮断|anon=404(hidden)",
 ("invenio_files_rest.object_api","PUT"):"測定範囲では遮断|anon=404(hidden)",
 ("invenio_files_rest.object_thumbnail_api","GET"):"到達|anon=500(認可通過後クラッシュ)",
 ("invenio_files_rest.object_thumbnail_api","POST"):"到達|anon=500(handler)",
 ("invenio_files_rest.object_thumbnail_api","PUT"):"到達|anon=500(handler)",
 ("invenio_files_rest.object_thumbnail_api","DELETE"):"到達|anon=500(handler)",
 ("invenio_records_rest.recid_suggest","GET"):"経路なし(404)=SuggestResource未登録。指摘『未使用』を裏付け",
 ("weko_groups.manage","GET"):"測定範囲では遮断|anon=302; general=302",
 ("weko_groups.accept","POST"):"測定範囲では遮断|anon=302; general=302",
 ("weko_groups.new_member","POST"):"測定範囲では遮断|anon=302; general=302",
 ("invenio_deposit_rest.depid_actions","POST"):"検証不能(実URL要確認)",
 ("community.edit_view","GET"):"検証不能(ModelView実URL要確認・admin-role-table対象)",
 ("weko_plugins.setting","GET"):"検証不能(実URL要確認)",
 ("pluginsetting.disable","GET"):"検証不能(実URL要確認)",
 ("pluginsetting.enable","GET"):"検証不能(実URL要確認)",
 ("pluginsetting.delete","GET"):"検証不能(実URL要確認)",
}
resync={"invenio_resourcesyncserver.file_content","invenio_resourcesyncserver.resource_dump_manifest",
 "invenio_resourcesyncserver.change_list","invenio_resourcesyncserver.change_dump",
 "invenio_resourcesyncserver.change_dump_manifest","invenio_resourcesyncserver.change_dump_content"}
conf=[("/record/<pid_value>/publish","POST","★E2E確定:未認証でpublish_status 0→1改変(recid1003・DB確認)"),
 ("/api/iiif/v2/<uuid>","GET","★確定:未認証で非公開ファイル画像取得(image/png 200)"),
 ("get_curr_api_cert","GET","★確定:未認証でcert_data(account+password)漏洩"),
 ("validate_user_info","POST","★確定:未認証でuser_id/email返却"),
 ("/api/schemas/","POST","★確定:未認証でスキーマ作成201"),
 ("/api/schemas/put/","PUT","★確定:未認証で任意パス名ファイル書込200"),
 ("/api/records/<pid(recid):pid_value>","PUT","★確定:update factory=None素通り実行"),
 ("/api/deposits/publish/","PUT","★確定:未認証でpublish handler到達"),]
DVI=45; summ=collections.Counter()
for i,c in enumerate(data):
    if str(i) not in res: continue
    ep=c[11]; mth=(c[4] or "GET").split(",")[0]; url=resolve(c[5]); r=res[str(i)]
    kb=(ep,mth)
    if kb in fix: body="[実測·正URL] "+fix[kb]
    elif ep in resync: body="[実測·正URL] 検証不能(resync実URL要確認)"
    else:
        kinds={};parts=[]
        for ident in("anon","general","comadmin","repoadmin"):
            if ident in r: k=kind(r[ident],mth,url);kinds[ident]=k;parts.append(f"{ident}={r[ident]}({k})")
        if kinds.get("anon")=="到達":v="未認証で到達"
        elif kinds.get("general")=="到達":v="ログインのみで到達"
        elif kinds.get("comadmin")=="到達":v="Community管理者で到達"
        elif kinds.get("repoadmin")=="到達":v="Repository管理者で到達"
        elif "検証不能" in kinds.values() and "到達" not in kinds.values():v="検証不能(テストURL未解決)"
        else:v="測定範囲では遮断"
        body=f"[実測] {v} | "+"; ".join(parts)
    # ★確定を前置
    for us,mm,note in conf:
        if us in c[5] and mm in c[4]: body=note+" || "+body; break
    while len(c)<=DVI:c.append("-")
    c[DVI]=body
    # サマリ
    for kk in("★確定","未認証で到達","ログインのみで到達","Community管理者で到達","Repository管理者で到達","測定範囲では遮断","検証不能","経路なし","到達"):
        if kk in body: summ[kk]+=1;break
open(R+"weko3_api_list.tsv","w",encoding="utf-8").write("\t".join(hd)+"\n"+"\n".join("\t".join(x.replace("\t"," ") for x in c) for c in data)+"\n")
print("=== 最終実測サマリ(223) ==="); [print(f"  {n:4d}  {k}") for k,n in summ.most_common()]
print("列数:",len(hd))
