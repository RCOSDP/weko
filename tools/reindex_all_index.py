import os
import requests
from requests.auth import HTTPBasicAuth
from importlib import import_module
import re
import json

host = os.environ.get('INVENIO_ELASTICSEARCH_HOST','localhost')
port = 9200
auth = ("admin","admin")

#from opensearchpy import OpenSearch
#client = OpenSearch(
#    hosts=[{"host":host,"port":port}],
#    http_auth=auth,
#    use_ssl=True,
#    verify_certs=False
#)
from elasticsearch import Elasticsearch
client = Elasticsearch(host=host,verify_certs=False)

# indexとalias一覧取得
indexes_alias = client.indices.get_alias()
indexes = {}
for index in indexes_alias:
    indexes[index] = indexes_alias[index].get("aliases",{})

#version = "os-v2"
version="v7"
mapping_files = {
    "deposits-deposit-v1.0.0": ("invenio_deposit", f"mappings/{version}/deposits/deposit-v1.0.0.json"),
    "authors-author-v1.0.0": ("weko_authors", f"mappings/{version}/authors/author-v1.0.0.json"),
    "weko-item-v1.0.0": ("weko_schema_ui", f"mappings/{version}/weko/item-v1.0.0.json"),
    "marc21-holdings-hd-v1.0.0": ("invenio_marc21", f"mappings/{version}/marc21/holdings/hd-v1.0.0.json"),
    "marc21-authority-ad-v1.0.0": ("invenio_marc21",f"mappings/{version}/marc21/authority/ad-v1.0.0.json"),
    "marc21-bibliographic-bd-v1.0.0": ("invenio_marc21", f"mappings/{version}/marc21/bibliographic/bd-v1.0.0.json"),
}

template_files = {
    "events-stats-celery-task": ("invenio_stats", f"contrib/celery_task/{version}/celery-task-v1.json"),
    "events-stats-file-download": ("invenio_stats", f"contrib/file_download/{version}/file-download-v1.json"),
    "events-stats-file-preview": ("invenio_stats", f"contrib/file_preview/{version}/file-preview-v1.json"),
    "events-stats-item-create": ("invenio_stats", f"contrib/item_create/{version}/item-create-v1.json"),
    "events-stats-record-view": ("invenio_stats", f"contrib/record_view/{version}/record-view-v1.json"),
    "events-stats-search": ("invenio_stats", f"contrib/search/{version}/search-v1.json"),
    "events-stats-top-view": ("invenio_stats", f"contrib/top_view/{version}/top-view-v1.json"),
    "stats-celery-task": ("invenio_stats", f"contrib/aggregations/aggr_celery_task/{version}/aggr-celery-task-v1.json"),
    "stats-file-download": ("invenio_stats", f"contrib/aggregations/aggr_file_download/{version}/aggr-file-download-v1.json"),
    "stats-file-preview": ("invenio_stats", f"contrib/aggregations/aggr_file_preview/{version}/aggr-file-preview-v1.json"),
    "stats-item-create": ("invenio_stats", f"contrib/aggregations/aggr_item_create/{version}/aggr-item-create-v1.json"),
    "stats-record-view": ("invenio_stats", f"contrib/aggregations/aggr_record_view/{version}/aggr-record-view-v1.json"),
    "stats-search": ("invenio_stats", f"contrib/aggregations/aggr_search/{version}/aggr-search-v1.json"),
    "stats-top-view": ("invenio_stats", f"contrib/aggregations/aggr_top_view/{version}/aggr-top-view-v1.json"),
}

mappings = {}
templates = {}
# ファイルからマッピングデータを取得
print("# get mapping from json file")
for index in indexes:
    index_tmp = index.replace(os.environ.get('SEARCH_INDEX_PREFIX')+"-", "")
    index_tmp = re.sub("-\d{6}$","",index_tmp)
    if index_tmp == "stats-bookmarks":
        mappings[index]={
            "mappings":{
                "date_detection": False,
                "properties":{
                    "date":{
                        "type": "date",
                        "format": "date_optional_time"
                    },
                    "aggregation_type": {
                        "type": "keyword"
                    }
                }
            }
        }
        continue
    if index_tmp not in list(mapping_files.keys())+list(template_files.keys()):
        print("## not exists: {}".format(index, index_tmp))
        continue
    mapping_type=""
    if index_tmp in mapping_files:
        mapping_file_datas = mapping_files
        mapping_type="mapping"
    else:
        mapping_file_datas = template_files
        mapping_type="templates"
    path_data = mapping_file_datas[index_tmp]
    module_name = path_data[0]
    try:
        res = import_module(module_name)
    except ImportError:
        print("##not find: {}".format(module_name))
        continue
    current_path = os.path.dirname(os.path.abspath(res.__file__))
    file_path = os.path.join(current_path, path_data[1])
    
    if not os.path.isfile(file_path):
        print("## not exist file: {}".format(file_path))
        continue

    with open(file_path, "r") as json_file:
        if mapping_type == "mapping":
            mappings[index] = json.loads(json_file.read())
        if mapping_type == "templates":
            templates[index] = json.loads(json_file.read())

#base_url = "https://"+host +":9200/"
base_url = "http://"+host +":9200/"
reindex_url = base_url + "_reindex?pretty&refresh=true&wait_for_completion=true"
template_url = base_url + "_index_template/{}"
auth = HTTPBasicAuth("admin","admin")
verify=False
headers = {"Content-Type":"application/json"}
percolator_body = {"properties": {"query": {"type": "percolator"}}}
for index in indexes:
    print("# start reindex: {}".format(index))
    tmpindex = index+"-tmp"
    
    # target index is weko-item-v1.0.0
    is_weko_item = index.replace(os.environ.get('SEARCH_INDEX_PREFIX')+"-","") == "weko-item-v1.0.0"
    
    # target index mapping
    if index in mappings:
        base_index_definition = mappings[index]
    elif index in templates:
        base_index_definition = templates[index]
    
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
    for alias in indexes[index]:
        alias_info = {"index": index, "alias": alias}
        if "is_write_index" in indexes[index][alias]:
            alias_info["is_write_index"] = indexes[index][alias]["is_write_index"]
        json_data_set_aliases["actions"].append({"add":alias_info})

    try:
        # 一時保存用インデックス作成
        if index in mappings:
            #res = requests.put(base_url+tmpindex+"?pretty",headers=headers,json=base_index_definition,auth=auth,verify=verify)
            res = requests.put(base_url+tmpindex+"?pretty",headers=headers,json=base_index_definition)
        elif index in templates:
            template_url.format(index+"/"+version)
            res = requests.put(template_url,headers=headers,json=base_index_definition)
            res = requests.put(base_url+tmpindex+"?pretty",headers=headers)
            
        if res.status_code!=200:
            raise Exception(res.text)
        
        if is_weko_item:
            #res = requests.put(base_url+tmpindex+"/_mapping",headers=headers,json=percolator_body,auth=auth,verify=verify)
            res = requests.put(base_url+tmpindex+"/_mapping/",headers=headers,json=percolator_body)
            if res.status_code!=200:
                raise Exception(res.text)
        print("## create tmp index")
        
        # 高速化のための設定
        #res = requests.put(base_url+tmpindex+"/_settings?pretty",headers=headers,json=performance_setting_body,auth=auth,verify=verify)
        res = requests.put(base_url+tmpindex+"/_settings?pretty",headers=headers,json=performance_setting_body)
        if res.status_code!=200:
            raise Exception(res.text)
        print("## speed-up setting for tmp_index")
        
        # 一時保存用インデックスに元のインデックスの再インデックス
        #res = requests.post(url=reindex_url,headers=headers,json=json_data_to_tmp,auth=auth,verify=verify)
        res = requests.post(url=reindex_url,headers=headers,json=json_data_to_tmp)
        if res.status_code!=200:
            raise Exception(res.text)
        print("## reindex to tmp_index")

        # 再インデックス前のインデックスを削除
        #res = requests.delete(base_url+index,headers=headers,auth=auth,verify=verify)
        res = requests.delete(base_url+index)
        if res.status_code!=200:
            raise Exception(res.text)
        print("## delete old index")
        
        # 新しくインデックス作成
        
        if index in mappings:
            #res = requests.put(base_url+tmpindex+"?pretty",headers=headers,json=base_index_definition,auth=auth,verify=verify)
            res = requests.put(base_url+index+"?pretty",headers=headers,json=base_index_definition)
        elif index in templates:
            template_url.format(index+"/"+version)
            res = requests.put(template_url,headers=headers,json=base_index_definition)
            res = requests.put(base_url+index+"?pretty",headers=headers)

        if is_weko_item:
            #res = requests.put(base_url+tmpindex+"/_mapping",headers=headers,json=percolator_body,auth=auth,verify=verify)
            res = requests.put(base_url+tmpindex+"/_mapping/",headers=headers,json=percolator_body)
            if res.status_code!=200:
                raise Exception(res.text)
        print("## create new index")
        
        # 高速化のための設定
        #res = requests.put(base_url+index+"/_settings?pretty",headers=headers,json=performance_setting_body,auth=auth,verify=verify)
        res = requests.put(base_url+index+"/_settings?pretty",headers=headers,json=performance_setting_body)
        if res.status_code!=200:
            raise Exception(res.text)
        print("## speed-up setting for new index")
        
        # aliasの設定
        if json_data_set_aliases["actions"]:
            #res = requests.post(base_url+"_aliases",headers=headers,json=json_data_set_aliases,auth=auth,verify=verify)
            res = requests.post(base_url+"_aliases",headers=headers,json=json_data_set_aliases)
            if res.status_code!=200:
                raise Exception(res.text)
        print("## setting alias for new index")
        
        # アイテムの再挿入
        #res = requests.post(url=reindex_url, headers=headers,json=json_data_to_dest,auth=auth,verify=verify)
        res = requests.post(url=reindex_url, headers=headers,json=json_data_to_dest)
        if res.status_code!=200:
            raise Exception(res.text)
        print("## put into new index")
        
        # 高速化のための設定を元に戻す
        #res = requests.put(base_url+index+"/_settings?pretty",headers=headers,json=restore_setting_body,auth=auth,verify=verify)
        res = requests.put(base_url+index+"/_settings?pretty",headers=headers,json=restore_setting_body)
        if res.status_code!=200:
            raise Exception(res.text)

        # 一時保存用のインデックスを削除
        #res = requests.delete(base_url+tmpindex,auth=auth,verify=verify)
        res = requests.delete(base_url+tmpindex)
        if res.status_code!=200:
            raise Exception(res.text)
        print("## delete tmp_index")
        
        print("# end reindex: {}\n".format(index))
    except Exception as e:
        import traceback
        print("raise error: {}".format(index))
        print(traceback.format_exc())
