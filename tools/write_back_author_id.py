"""
ログ例
* <機関名>,重複していたWEKO_ID,オリジナルのfull_name,オリジナルのfirst_name,オリジナルのfamily_name,重複分の新WEKO_ID,重複分のfull_name,重複分のfirst_name,重複分のfamily_name    (複数言語の場合最初のもの)
# <機関名>,recid,重複していたWEKO_ID,メタデータのfull_name,メタデータのfirst_name,メタデータのfamily_name    (複数言語の場合最初のもの)
"""
import sys, os
from os.path import dirname, join
import json
import csv
from elasticsearch.exceptions import NotFoundError
from flask import current_app

from invenio_db import db
from invenio_indexer.api import RecordIndexer
from weko_authors.models import Authors

def get_original_data(filename, institution):
    original_data = []
    with open(filename, "r") as f:
        reader = csv.reader(f)
        l = [row for row in reader]
        for ll in l[1:]:
            if institution in ll[0]:
                original_data.append((ll[1],ll[2]))
    return original_data

def get_name_data(data):
    if "authorNameInfo" in data\
        and isinstance(data.get("authorNameInfo"),list)\
            and len(data.get("authorNameInfo")) > 0:
        return data.get("authorNameInfo")[0]

    return {}

def write_back_oringinal_data(origin_data, institution):
    indexer = RecordIndexer()
    author_index = current_app.config['WEKO_AUTHORS_ES_INDEX_NAME']
    author_doc_type = current_app.config['WEKO_AUTHORS_ES_DOC_TYPE']
    record_index = current_app.config['SEARCH_UI_SEARCH_INDEX']
    record_doc_type = current_app.config['INDEXER_DEFAULT_DOCTYPE']

    for pk_id, origin_es_id in origin_data:
        try:
            # オリジナルデータの取得
            result = indexer.client.get(index=author_index,doc_type=author_doc_type,id=origin_es_id)
            origin_data = result["_source"]

            # オリジナルデータの書き戻し
            author = Authors.query.filter_by(id=pk_id).one()
            author.json = json.dumps(origin_data)
            db.session.merge(author)

            duplicate_es_data = indexer.client.search(
                index=author_index, doc_type=author_doc_type,
                body={
                    "query":{
                        "term":{
                            "pk_id":{"value": str(pk_id)}
                        }
                    }
                }
            )
            
            is_update = False
            new_data = {}
            new_id = ""
            for es_data in duplicate_es_data["hits"]["hits"]:
                # オリジナルデータだった場合はスキップ
                if es_data.get("_id") == origin_es_id:
                    continue
                
                # PGで新しいWEKO_IDを取得
                new_id = Authors.get_sequence(db.session)
                new_data = es_data["_source"]
                # Elasticsearchの重複データを新しいWEKO_IDとしてPGに保存する
                new_data["pk_id"] = str(new_id)
                for id_info in new_data["authorIdInfo"]:
                    if id_info["idType"] == "1":
                        id_info["authorId"] = str(new_id)
                new_data["id"] = es_data.get("_id")
                gather_flg = new_data.get("gather_flg", 0)
                is_deleted = True if new_data.get("is_deleted") == "true" else False
                author = Authors(id=new_id, is_deleted=is_deleted, gather_flg=gather_flg, json=json.dumps(new_data))
                db.session.add(author)
                # Elasticsearchのデータの更新
                indexer.client.update(
                    index=author_index,doc_type=author_doc_type,
                    id=es_data.get("_id"),
                    body={"doc":new_data}
                )
                is_update=True
                
            db.session.commit()
            
            origin_name = get_name_data(origin_data)
            duplicate_name = get_name_data(new_data)
            print("* {institution},{duplicate_weko_id},{original_full_name},{original_first_name},{original_family_name},{duplicate_new_id},{duplicate_full_name},{duplicate_first_name},{duplicate_family_name}".format(
                institution=institution,
                duplicate_weko_id=pk_id,
                original_full_name=origin_name.get("fullName"),
                original_first_name=origin_name.get("firstName"),
                original_family_name=origin_name.get("familyName"),
                duplicate_new_id=new_id,
                duplicate_full_name=duplicate_name.get("fullName"),
                duplicate_first_name=duplicate_name.get("firstName"),
                duplicate_family_name=duplicate_name.get("familyName"),
            ))
        
            # 重複したWEKO_IDになっているアイテムの一覧、および著者情報を洗い出し、ログに記録する。
            if is_update:
                query = {
                    "query": {
                        "bool": {
                            "must": [
                                { "match": { "relation_version_is_last": "true" } },
                                {"terms": {"author_link.raw": [str(pk_id)]}}
                            ]
                        }
                    }
                }
                search_result = indexer.client.search(
                    index=record_index,doc_type=record_doc_type,body=query
                )
                if search_result["hits"]["total"]>0:
                    hits = search_result["hits"]["hits"]
                    for result in hits:
                        recid = result.get("_source").get("control_number")
                        metadata = result.get("_source",{}).get("_item_metadata")
                        for k, v in metadata.items():
                            if isinstance(v, dict) \
                                and v.get("attribute_value_mlt") \
                                    and isinstance(v["attribute_value_mlt"], list):
                                data_list = v["attribute_value_mlt"]
                                for data in data_list:
                                    is_duplicate = False
                                    # WEKO IDが対象と同じ
                                    if isinstance(data, dict) and "nameIdentifiers" in data:
                                        for id in data["nameIdentifiers"]:
                                            if id["nameIdentifierScheme"] == "WEKO":
                                                if id["nameIdentifier"] == str(pk_id):
                                                    is_duplicate=True
                                                    break
                                    if is_duplicate:
                                        full_name = data.get("creatorNames")[0].get("creatorName","") if len(data.get("creatorNames",[])) > 0 else ""
                                        given_name = data.get("givenNames")[0].get("givenName","") if len(data.get("creatorNames",[])) > 0 else ""
                                        family_name = data.get("familyNames")[0].get("familyName","") if len(data.get("creatorNames",[])) > 0 else ""
                                        print("# {institution},{recid},{pk_id},'{full_name}',{first_name},{family_name}".format(
                                            institution=institution,
                                            recid=recid,
                                            pk_id=pk_id,
                                            full_name=full_name,
                                            first_name=given_name,
                                            family_name=family_name
                                        ))
        except NotFoundError:
            db.session.rollback()
            print("No data exists in elasticsearch.(pk_id: {}, es_id: {})".format(pk_id,origin_es_id))
        except:
            db.session.rollback()
            import traceback
            print(traceback.print_exc())


if __name__ == '__main__':
    args = sys.argv

    original_data_path = args[1] if len(args) == 2 else join(dirname(__file__), "duplicate_author_id_original.csv")
    institution = os.environ.get('SEARCH_INDEX_PREFIX', '')
    original_data = get_original_data(original_data_path, institution)
    
    write_back_oringinal_data(original_data, institution)
