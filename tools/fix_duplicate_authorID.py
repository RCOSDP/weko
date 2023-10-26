
import json
from sqlalchemy import create_engine
from flask import current_app

from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier
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
        # esとitemに同じfirstname(givenname)が存在しているか判定
        if metadata.get("givenNames"):
            givenName_list_metadata = [d["givenName"] for d in metadata.get("givenNames")]
            firstName_list_author = [d["firstName"] for d in author_data["authorNameInfo"]]
            for gn in givenName_list_metadata:
                if gn in firstName_list_author:
                    flg_gn=True
                    break
        # esとitemに同じfamilyNameが存在しているか判定
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
    targets_author_id = [id for id, datas in duplicate.items() if len(datas)>1] # 重複があるauthor_idのリスト

    deleted={}
    error={}
    for target in targets_author_id:
        print("* pk_id: {}".format(target))
        for data in duplicate[target]:
            db_data = data["db"]
            db_metadata = json.loads(db_data.json)
            es_data = data["es"]
            es_metadata = es_data["_source"]
            delete_flg=False
            # dbとesのデータの差異を判定
            if es_metadata["authorNameInfo"] != db_metadata["authorNameInfo"]:
                delete_flg=True
            
            if delete_flg:
                # 削除されるデータがrecords_metadataで使用されているか検証
                conflict_metadatas=[]
                sql_records_metadata = "SELECT id, json->'author_link' FROM records_metadata WHERE json->>'author_link' LIKE '\[%%\"{}\"%%\]';".format(target)
                records_metadata = connection.execute(sql_records_metadata).fetchall()
                if len(records_metadata)>0:
                    for metadata in records_metadata:
                        id = metadata[0]
                        recid = PersistentIdentifier.get_by_object("recid","rec",id).pid_value
                        data = RecordMetadata.query.filter_by(id=id).one()
                        if check_records_metadata(target, es_metadata, data):
                            conflict_metadatas.append(recid)
                            
                # 削除されるデータがitem_metadataで使用されているか検証
                sql_item_metadata = "SELECT id, json->'author_link' FROM item_metadata WHERE json->>'author_link' LIKE '\[%%\"{}\"%%\]';".format(target)
                item_metadata = connection.execute(sql_item_metadata).fetchall()
                if len(records_metadata)>0:
                    for metadata in item_metadata:
                        id = metadata[0]
                        recid = PersistentIdentifier.get_by_object("recid","rec",id).pid_value
                        data = ItemMetadata.query.filter_by(id=id).one()
                        if check_records_metadata(target, es_metadata, data):
                            if recid not in conflict_metadatas:
                                conflict_metadatas.append(recid)

                indexer.client.delete(
                    index=authors_index,
                    doc_type=authors_doc_type,
                    id=es_data["_id"]
                )
                print("- delete: {}".format(es_metadata))
                print("# conflict: {}".format(conflict_metadatas))
