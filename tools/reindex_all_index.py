
import sys
import os
import requests
from requests.auth import HTTPBasicAuth
from importlib import import_module
import re
import json

args = sys.argv
if len(args) == 4:
    http_method = "https" if args[1] == "https" else "http"
    user = args[2]
    password = args[3]
    auth = HTTPBasicAuth(user,password)
elif len(args) == 2:
    http_method = "https" if args[1] == "https" else "http"
    auth = None
else:
    print("Usage: python reindex_all_index.py [http_method] [user] [password]")
    sys.exit(1)

host = os.environ.get('INVENIO_ELASTICSEARCH_HOST','localhost')
version="v7"

base_url = http_method + "://" + host +":9200/"
reindex_url = base_url + "_reindex?pretty&refresh=true&wait_for_completion=true"
bulk_url = base_url + "_bulk"
template_url = base_url + "_template/{}"
verify=False
headers = {"Content-Type":"application/json"}
bulk_headers = {"Content-Type":"application/x-ndjson"}


req_args = {"headers":headers,"verify":verify}
bulk_req_args = {"headers":bulk_headers,"verify":verify}
if auth:
    req_args["auth"] = auth 
    bulk_req_args["auth"] = auth

mapping_files = {
    "authors-author-v1.0.0": f"weko-authors/weko_authors/mappings/{version}/authors/author-v1.0.0.json",
    "weko-item-v1.0.0": f"weko-schema-ui/weko_schema_ui/mappings/{version}/weko/item-v1.0.0.json",
}
template_files = {
    "events-stats-index": f"invenio-stats/invenio_stats/contrib/events/{version}/events-v1.json",
    "stats-index": f"invenio-stats/invenio_stats/contrib/aggregations/{version}/aggregation-v1.json",
}
stats_indexes = ["events-stats-celery-task", "events-stats-file-download", "events-stats-file-preview", "events-stats-item-create", "events-stats-record-view", "events-stats-search", "events-stats-top-view", "stats-celery-task", "stats-file-download", "stats-file-preview", "stats-item-create", "stats-record-view", "stats-search", "stats-top-view"]

delete_indexes = [
    "stats-bookmarks",
    "deposits-deposit-v1.0.0",
    "marc21-holdings-hd-v1.0.0",
    "marc21-authority-ad-v1.0.0",
    "marc21-bibliographic-bd-v1.0.0",
]

prefix = os.environ.get('SEARCH_INDEX_PREFIX')

def replace_prefix_index(index_name):
    index_tmp = re.sub(f"^{prefix}-", "", index_name)
    index_tmp = re.sub("-\d{6}$","",index_tmp)
    return index_tmp

# indexとalias一覧取得
print("# get indexes and aliases")
organization_aliases = prefix+"-*"
indexes = requests.get(f"{base_url}{organization_aliases}",**req_args).json()
indexes_alias = {} # indexとaliasのリスト
write_indexes = [] # is_write_indexがtrueのindexとaliasのリスト
delete_target_stats = [] # 削除対象となるinvenio_statsのindexリスト
for index in indexes:
    aliases = indexes[index].get("aliases",{})
    indexes_alias[index] = aliases
    
    index_tmp = replace_prefix_index(index)
    if index_tmp not in stats_indexes:
        continue
    delete_target_stats.append(index)
    for alias, alias_info in aliases.items():
        if alias_info.get("is_write_index", False) is True:
            write_indexes.append(
                {"index":index,"alias":alias}
            )

modules_dir = "/code/modules/"
mappings = {}
templates = {}

# ファイルからマッピングデータを取得
print("# get mapping from json file")
for index in indexes_alias:
    index_tmp = replace_prefix_index(index)
    if index_tmp in stats_indexes:
        continue
    if index_tmp not in list(mapping_files.keys()):
        print("## not exists: {}, {}".format(index, index_tmp))
        continue
    path_data = mapping_files[index_tmp]
    file_path = os.path.join(modules_dir, path_data)
    
    if not os.path.isfile(file_path):
        print("## not exist file: {}".format(file_path))
        continue

    with open(file_path, "r") as json_file:
        mappings[index] = json.loads(json_file.read())
        
print("# get template from json files")
for index, path in template_files.items():
    file_path = os.path.join(modules_dir, path)
    if not os.path.isfile(file_path):
        print("## not exist file: {}".format(file_path))
        continue
    with open(file_path, "r") as json_file:
        templates[index] = json.loads(
            json_file.read().\
                replace("__SEARCH_INDEX_PREFIX__",prefix+"-")
        )

# 削除対象のインデックスの削除
print("# delete indexes")
delete_target_index = [index for index in indexes if re.sub(f"^{prefix}-", "", index) in delete_indexes]
for target in delete_target_index:
    delete_url = f"{base_url}{target}"
    res = requests.delete(delete_url,**req_args)
    if res.status_code!=200:
        print("## raise error: delete index:{}".format(target))
        raise Exception(res.text)

percolator_body = {"properties": {"query": {"type": "percolator"}}}
# for index in indexes_alias:
for index, mapping in mappings.items():
    print("# start reindex: {}".format(index))
    tmpindex = index+"-tmp"
    
    # target index is weko-item-v1.0.0
    is_weko_item = re.sub(f"^{prefix}-", "", index) == "weko-item-v1.0.0"
    
    # target index mapping
    base_index_definition = mappings[index]

    # create speed up setting body
    defalut_number_of_replicas = base_index_definition.get("settings",{}).get("index",{}).get("number_of_replicas",1)
    default_refresh_interval = base_index_definition.get("settings",{}).get("index",{}).get("refresh_interval","1s")
    performance_setting_body = {"index": {"number_of_replicas": 0, "refresh_interval": "-1"}}
    restore_setting_body = {"index": {"number_of_replicas": defalut_number_of_replicas, "refresh_interval": default_refresh_interval}}
    
    # body for reindex
    json_data_to_tmp = {"source":{"index":index},"dest":{"index":tmpindex}}
    json_data_to_dest = {"source":{"index":tmpindex},"dest":{"index":index}}
    
    # body for setting alias
    json_data_set_aliases = {
        "actions":[]
    }
    for alias in indexes_alias[index]:
        alias_info = {"index": index, "alias": alias}
        if "is_write_index" in indexes_alias[index][alias]:
            alias_info["is_write_index"] = indexes_alias[index][alias]["is_write_index"]
        json_data_set_aliases["actions"].append({"add":alias_info})

    try:
        # 一時保存用インデックス作成
        res = requests.put(base_url+tmpindex+"?pretty",json=base_index_definition,**req_args)
        if res.status_code!=200:
            raise Exception(res.text)
        
        if is_weko_item:
            res = requests.put(base_url+tmpindex+"/_mapping/",json=percolator_body,**req_args)
            
            if res.status_code!=200:
                raise Exception(res.text)
        print("## create tmp index")
        
        # 高速化のための設定
        res = requests.put(base_url+tmpindex+"/_settings?pretty",json=performance_setting_body,**req_args)
        if res.status_code!=200:
            raise Exception(res.text)
        print("## speed-up setting for tmp_index")
        
        # 一時保存用インデックスに元のインデックスの再インデックス
        res = requests.post(url=reindex_url,json=json_data_to_tmp,**req_args)
        if res.status_code!=200:
            raise Exception(res.text)
        print("## reindex to tmp_index")

        # 再インデックス前のインデックスを削除
        res = requests.delete(base_url+index,**req_args)
        if res.status_code!=200:
            raise Exception(res.text)
        print("## delete old index")
        
        # 新しくインデックス作成
        res = requests.put(base_url+index+"?pretty",json=base_index_definition,**req_args)

        if is_weko_item:
            res = requests.put(base_url+tmpindex+"/_mapping/",json=percolator_body,**req_args)
            if res.status_code!=200:
                raise Exception(res.text)
        print("## create new index")
        
        # 高速化のための設定
        res = requests.put(base_url+index+"/_settings?pretty",json=performance_setting_body,**req_args)
        if res.status_code!=200:
            raise Exception(res.text)
        print("## speed-up setting for new index")
        
        # aliasの設定
        if json_data_set_aliases["actions"]:
            res = requests.post(base_url+"_aliases",json=json_data_set_aliases,**req_args)
            if res.status_code!=200:
                raise Exception(res.text)
        print("## setting alias for new index")
        
        # アイテムの再挿入
        res = requests.post(url=reindex_url,json=json_data_to_dest,**req_args)
        if res.status_code!=200:
            raise Exception(res.text)
        print("## put into new index")
        
        # 高速化のための設定を元に戻す
        res = requests.put(base_url+index+"/_settings?pretty",json=restore_setting_body,**req_args)
        if res.status_code!=200:
            raise Exception(res.text)

        # 一時保存用のインデックスを削除
        res = requests.delete(base_url+tmpindex,**req_args)
        if res.status_code!=200:
            raise Exception(res.text)
        print("## delete tmp_index")
        
        print("# end reindex: {}\n".format(index))
    except Exception as e:
        import traceback
        print("##raise error: {}".format(index))
        print(traceback.format_exc())

# is_write_indexをfalseに切り替え
print("# Start of invenio-stats index consolidation")
print("## Change is_write_index to False")
json_data_toggle_aliases={"actions":[]}
for index in write_indexes:
    json_data_toggle_aliases["actions"].append({
        "remove":{
            "index": index["index"],
            "alias": index["alias"],
        }
    })
    json_data_toggle_aliases["actions"].append({
        "add":{
            "index": index["index"],
            "alias": index["alias"],
            "is_write_index": False
        }
    })
res = requests.post(base_url+"_aliases",json=json_data_toggle_aliases,**req_args)
if res.status_code!=200:
    print("##raise error: toggle is_write_index")
    raise Exception(res.text)

def create_stats_index(index_name, stats_prefix, stats_types):
    print("## start create stats index: {}".format(index_name))
    index_with_prefix = f"{prefix}-{index_name}"
    new_index_name = f"{index_with_prefix}-000001"
    filename_without_ext = template_files[index_name].split("/")[-1].replace(".json","")
    template_name = f"{prefix}-{filename_without_ext}"
    template_url_event_stats = template_url.format(template_name)
    # template登録
    print("### put template")
    res = requests.put(template_url_event_stats,json=templates[index_name],**req_args)
    if res.status_code!=200:
        print("### raise error: put template")
        raise Exception(res.text)
    # index作成
    print("### craete index")
    res = requests.put(base_url+new_index_name+"?pretty",**req_args)
    if res.status_code!=200:
        print("## raise error: create index")
        raise Exception(res.text)

    # エイリアス登録用データ作成
    alias_actions = []
    alias_actions.append(
        {
            "add": {
                "index":new_index_name,
                "alias":index_with_prefix,
                "is_write_index":True
            }
        }
    )
    for stats_type in stats_types:
        event_type = stats_type.replace(f"{stats_prefix}-","")
        alias_info = {
            "index": new_index_name,
            "alias": f"{prefix}-{stats_prefix}-{event_type}",
            "is_write_index": True,
            "filter":{
                "term":{"event_type":event_type}
            }
        }
        alias_actions.append({"add":alias_info})
    return alias_actions

def stats_reindex(stats_types, stats_prefix):
    print("## start reindex stats index: {}".format(stats_prefix))
    stats_indexes = [index for index in indexes_alias if replace_prefix_index(index) in stats_types]
    for index in stats_indexes:
        print("### reindex: {}".format(index))
        from_reindex = index
        to_reindex = f"{prefix}-{stats_prefix}-index"
        event_type = replace_prefix_index(index).replace(f"{stats_prefix}-","")
        body = {
            "source": {"index": from_reindex},
            "dest": {"index": to_reindex},
            "script": {
                "source": f"ctx._source['event_type'] = '{event_type}'",
                "lang": "painless"
            }
        }
        res = requests.post(url=reindex_url,json=body,**req_args)
        if res.status_code!=200:
            print("### raise error: reindex: {}".format(index))
            raise Exception(res.text)

event_stats_types = [
    "events-stats-celery-task",
    "events-stats-file-download",
    "events-stats-file-preview",
    "events-stats-item-create",
    "events-stats-record-view",
    "events-stats-search",
    "events-stats-top-view",
]

stats_types = [
    "stats-celery-task",
    "stats-file-download",
    "stats-file-preview",
    "stats-item-create",
    "stats-record-view",
    "stats-search",
    "stats-top-view",
]

alias_actions = []
alias_actions += create_stats_index("events-stats-index", "events-stats", event_stats_types)
alias_actions += create_stats_index("stats-index", "stats", stats_types)

res = requests.post(base_url+"_aliases",json={"actions":alias_actions},**req_args)
if res.status_code!=200:
    print("## raise error: put aliases")
    raise Exception(res.text)

stats_reindex(event_stats_types, "events-stats")
stats_reindex(stats_types, "stats")

# delete stats index
print("# delete stats index")
delete_bulk = ""
for target in delete_target_stats:
    delete_url = f"{base_url}{target}"
    res = requests.delete(delete_url,**req_args)
    if res.status_code!=200:
        print("## raise error: delete stats index:{}".format(target))
        raise Exception(res.text)