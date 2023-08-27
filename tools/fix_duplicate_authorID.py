
import json
from sqlalchemy import create_engine
from flask import current_app

from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_records.models import RecordMetadata
from weko_authors.models import Authors
from weko_records.models import ItemMetadata

engine = create_engine(current_app.config["SQLALCHEMY_DATABASE_URI"])
connection = engine.connect()

authors_index = current_app.config['WEKO_AUTHORS_ES_INDEX_NAME']
authors_doc_type = current_app.config['WEKO_AUTHORS_ES_DOC_TYPE']


def get_author_link(author_id, db_data, value):
    
    def _compare_author_data(author_data, metadata):
        """Compare author data and metadata familyName, GivenName"""
        flg_gn=False
        if metadata.get("givenNames"):
            givenName_list_metadata = [d["givenName"] for d in metadata.get("givenNames")]
            firstName_list_author = [d["firstName"] for d in author_data["authorNameInfo"]]
            for gn in givenName_list_metadata:
                if gn in firstName_list_author:
                    flg_gn=True
                    break
        flg_fn=False
        if metadata.get("familyNames"):
            familyName_list_metadata = [d["familyName"] for d in metadata.get("familyNames")]
            familylyName_list_author = [d["familyName"] for d in author_data["authorNameInfo"]]
            for fn in familyName_list_metadata:
                if fn in familylyName_list_author:
                    flg_fn=True
                    break
        if flg_gn and flg_fn:
            return True
        else:
            return False
    
    if isinstance(value, list):
        for v in value:
            if (
                "nameIdentifiers" in v
                and len(v["nameIdentifiers"]) > 0
                and "nameIdentifierScheme" in v["nameIdentifiers"][0]
                and v["nameIdentifiers"][0]["nameIdentifierScheme"]=="WEKO"
                and v["nameIdentifiers"][0]["nameIdentifier"]==author_id
            ):
                if _compare_author_data(db_data, v):
                    return True
    elif (
        isinstance(value, dict)
        and "nameIdentifiers" in value
        and len(value["nameIdentifiers"]) > 0
        and "nameIdentifierScheme" in value["nameIdentifiers"][0]
        and value["nameIdentifiers"][0]["nameIdentifierScheme"]=="WEKO"
        and value["nameIdentifiers"][0]["nameIdentifier"]==author_id
    ):
        if _compare_author_data(db_data, value):
            return True
    
    return False

def check_records_metadata(author_id,es_data, metadata):
    data = metadata.json
    for k, v in data.items():
        if isinstance(v, dict):
            attr = v.get("attribute_value_mlt")
            if isinstance(attr,list):
                if len(attr)>0 and isinstance(attr[0], dict):
                    if get_author_link(author_id,es_data, attr):
                        return True
    return False

def check_item_metadata(author_id,es_data,metadata):
    data = metadata.json
    for k,v in data.items():
        if isinstance(v,list):
            if len(v)>0 and isinstance(v[0],dict):
                if get_author_link(author_id,es_data, v):
                    return True
    return False

if __name__=="__main__":
    
    # 重複可能性IDを取得
    sql = "SELECT last_value FROM authors_id_seq;"
    authors_id_seq = connection.execute(sql).scalar()

    # 重複の可能性があるESのデータを取得
    body={
        "query":{
            "bool":{
                "must":[
                    {"terms":{"pk_id":[str(i) for i in range(1,authors_id_seq+1)]}}
                ]
            }
        },
        "_source":["pk_id","authorNameInfo"],
        "size":authors_id_seq*3
    }
    indexer = RecordIndexer()
    result = indexer.client.search(
        index=authors_index,
        doc_type=authors_doc_type,
        body=body
    )
    
    # ESのpk_idに対応するauthorsのデータをdbから取得
    result = result["hits"]["hits"]
    duplicate={}
    for doc in result:
        es_data = doc.get("_source")
        id = es_data.get("pk_id")
        
        db_data = Authors.query.filter_by(id=id).one_or_none()
        if id not in duplicate:
            duplicate[id]=[]
        duplicate[id].append({"db":db_data,"es":doc})
    targets = [id for id,datas in duplicate.items() if len(datas)>1]

    deleted={}
    error={}
    for target in targets:
        for data in duplicate[target]:
            db_data = data["db"]
            db_metadata = json.loads(db_data.json)
            es_data = data["es"]
            es_metadata = es_data["_source"]
            delete_flg=False
            
            # dbとesのデータの差異を判定
            for key in db_metadata.keys():
                if key == "id":
                    continue
                if es_metadata["authorNameInfo"] != db_metadata["authorNameInfo"]:
                    delete_flg=True
                    break
            if delete_flg:
                # 削除されるデータがrecords_metadataで使用されているか検証
                conflict_metadatas=[]
                sql_records_metadata = "SELECT id, json->'author_link' FROM records_metadata WHERE json->>'author_link' LIKE '\[%%\"{}\"%%\]';".format(target)
                records_metadata = connection.execute(sql_records_metadata).fetchall()
                if len(records_metadata)>0:
                    for metadata in records_metadata:
                        id = metadata[0]
                        data = RecordMetadata.query.filter_by(id=id).one()
                        if check_records_metadata(target, es_metadata, data):
                            conflict_metadatas.append(id)
                            
                # 削除されるデータがitem_metadataで使用されているか検証
                sql_item_metadata = "SELECT id, json->'author_link' FROM item_metadata WHERE json->>'author_link' LIKE '\[%%\"{}\"%%\]';".format(target)
                item_metadata = connection.execute(sql_item_metadata).fetchall()
                if len(records_metadata)>0:
                    for metadata in item_metadata:
                        id = metadata[0]
                        data = ItemMetadata.query.filter_by(id=id).one()
                        if check_records_metadata(target, es_metadata, data):
                            if id not in conflict_metadatas:
                                conflict_metadatas.append(id)
                if len(conflict_metadatas) == 0:
                    indexer.client.delete(
                        index=authors_index,
                        doc_type=authors_doc_type,
                        id=es_data["_id"]
                    )
                    if target not in deleted:
                        deleted[target]=[]
                    deleted[target].append(es_data["_id"])
                else:
                    if target not in error:
                        error[target]={}
                    error[target][es_data["_id"]]=conflict_metadatas
    # ログ出力
    for target in targets:
        print("pk_id: {}".format(target))
        if deleted.get(target):
            print("* deleted")
            for d in deleted.get(target):
                print("{}".format(d))
        if error.get(target):
            print("* conflict author_link")
            for k in error.get(target):
                conflicts = error[target][k]
                print("{}: {}".format(k,[str(c) for c in conflicts]))
                
