import csv
import sys

from sqlalchemy.orm.attributes import flag_modified
import pytz
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidrelations.models import PIDRelation
from invenio_records.models import RecordMetadata
from invenio_records_files.models import RecordsBuckets
from invenio_files_rest.models import FileInstance,ObjectVersion
from weko_deposit.api import WekoIndexer
from weko_records.models import ItemMetadata
from weko_records.api import ItemTypes

target_value = "open_no"
fix_value = "open_login"

def read_file(filename):
    files = dict()
    with open(filename, encoding='utf-8', newline="") as f:
        for cols in csv.reader(f, delimiter='\t'):
            if cols[0] not in files:
                files[cols[0]] = list()
            files[cols[0]].append(cols[1])
    return files

def get_records(data):
    records=dict()
    for recid in data:
        parent = PersistentIdentifier.query.filter_by(pid_type='recid', pid_value=recid).one_or_none()
        if parent and parent.status != PIDStatus.DELETED:
            pv=PIDVersioning(child=parent)
            children=PIDVersioning(parent=pv.parent, child=parent).get_children(
                PIDRelation.relation_type==2).order_by(
                    PIDRelation.index.desc()).all()
            #for child in children:
            #    record_children[child]=PIDVersioning(child=child).parent
            if children:
                records[recid] = children
    return records

def get_file_key(item_type_id):
    """アイテムタイプ内のattribute_type=fileとなるプロパティのキーを取得"""
    item_type = ItemTypes.get_record(item_type_id)
    file_keys = [ key for key, properties in item_type["properties"].items() 
                 if properties.get("type")=="array" and 
                 "filename" in properties["items"]["properties"]] if item_type else []
    return file_keys


def fix_metadata(records, fix_target):
    file_keys = {}
    for recid in records:
        items = records.get(recid)
        target_files = fix_target.get(recid)
        for pid in items:
            try:
                record_metadata = RecordMetadata.query.filter_by(id=pid.object_uuid).one_or_none()
                item_metadata = ItemMetadata.query.filter_by(id=pid.object_uuid).one_or_none()
                item_type_id=item_metadata.item_type_id
                if item_type_id not in file_keys:
                    file_keys[item_type_id] = get_file_key(item_type_id)
                file_items = file_keys[item_type_id]
                flg = False
                fixed = list()
                
                # fix db data
                flg, fixed = fix_record_metadata(file_items, record_metadata, target_files, flg, fixed)
                flg, fixed = fix_item_metadata(file_items, item_metadata, target_files, flg, fixed)
                flg, fixed = fix_file_contents(pid.object_uuid, target_files, flg, fixed)
                flg, fixed = fix_es_data(file_items, record_metadata, target_files, flg, fixed)
                db.session.commit()
                
                for f in fixed:
                    print("*fixed {recid}: {filename}".format(recid=pid.pid_value,filename=f))
                
                for f in [file for file in target_files if file not in fixed]:
                    print("#not_fixed {recid}: {filename}".format(recid=pid.pid_value,filename=f))


            except Exception as e:
                import traceback
                print("#raise_error {recid}: {error}".format(recid=pid.pid_value,error=e))
                print(traceback.format_exc())
                db.session.rollback()

def fix_es_data(file_items, record, target_files, flg, fixed):
    indexer = WekoIndexer()
    indexer.get_es_index()
    search_query = {
        "_source": ["_item_metadata", "content"],
        "query": {
            "term": {
                "_id": record.id
            }
        }
    }
    es_data = indexer.client.search(index=indexer.es_index,doc_type=indexer.es_doc_type,body=search_query)
    if es_data["hits"]["total"] > 0:
        es_data = es_data["hits"]["hits"][0]["_source"]
        metadata = es_data.get("_item_metadata",{})
        new_metadata = {}
        changed_file_list = []
        for key in file_items:
            file_item = metadata.get(key,{})
            files = file_item.get("attribute_value_mlt",[])
            attribute_name = file_item.get("attribute_name","")
            attribute_type = file_item.get("attribute_type","")
            if files:
                is_changed = False
                for file_data in files:
                    filename = file_data.get("filename")
                    if filename in target_files:
                        if file_data.get("accessrole") == target_value:
                            file_data["accessrole"] = fix_value
                            is_changed = True
                            flg|=True
                            if filename not in fixed:
                                fixed.append(filename)
                            if filename not in changed_file_list:
                                changed_file_list.append(filename)
                if is_changed:
                    new_metadata.update(
                        {
                            key:{"attribute_name":attribute_name, "attribute_type":attribute_type, "attribute_value_mlt":files}
                        }
                    )

        if new_metadata:
            content = es_data.get("content",[])
            is_new_content = False
            for file in content:
                if file.get("filename") in changed_file_list:
                    file["accessrole"] = fix_value
                    is_new_content|=True
            body = {
                "doc":{
                    "_item_metadata":new_metadata,
                    "_updated":pytz.utc.localize(record.updated).isoformat()
                }
            }
            if is_new_content:
                body["doc"]["content"] = content
            
            indexer.client.update(
                index=indexer.es_index,
                doc_type=indexer.es_doc_type,
                id=str(record.id),
                body=body
            )

    return flg, fixed
    
    
def fix_record_metadata(file_items, record, target_files, flg, fixed):
    data = record.json
    for item in file_items:
        file_metadatas = data.get(item,{}).get("attribute_value_mlt",[])
        idx_list = [i for i,d in enumerate(file_metadatas) if d.get("filename") in target_files]
        for i in idx_list:
            file_data = file_metadatas[i]
            if file_data.get("accessrole") == target_value:
                file_data["accessrole"] = fix_value
                flg |= True
                if file_data.get("filename") not in fixed:
                    fixed.append(file_data.get("filename"))
    if flg:
        flag_modified(record, 'json')
        db.session.merge(record)
    return flg, fixed

def fix_item_metadata(file_items, record, target_files, flg, fixed):
    data = record.json
    for item in file_items:
        files_metadata = data.get(item)
        idx_list = [i for i,d in enumerate(files_metadata) if d.get("filename") in target_files]
        for i in idx_list:
            file_data = files_metadata[i]
            if file_data.get("accessrole") == target_value:
                file_data["accessrole"] = fix_value
                flg |= True
                if file_data.get("filename") not in fixed:
                    fixed.append(file_data.get("filename"))

    if flg:
        flag_modified(record,'json')
        db.session.merge(record)
    return flg, fixed

def fix_file_contents(rec_uuid, target_files, flg, fixed):
    files = FileInstance.query.filter(
        FileInstance.json.op('->>')('filename').in_(target_files)).filter(
            FileInstance.id.in_( 
                ObjectVersion.query.with_entities(ObjectVersion.root_file_id).filter(
                    ObjectVersion.bucket_id.in_( 
                        RecordsBuckets.query.with_entities(RecordsBuckets.bucket_id).filter(RecordsBuckets.record_id==rec_uuid) 
                    )
                )
            )
        ).all()
    for f in files:
        f_data = f.json
        if f_data.get("accessrole") == target_value:
            f_data["accessrole"] = fix_value
            flg|=True
            if f_data.get("filename") not in fixed:
                fixed.append(f_data.get("filename"))

        if flg:
            flag_modified(f,'json')
            db.session.merge(f)
    return flg, fixed

if __name__ == "__main__":
    args = sys.argv
    filename=args[1]
    data = read_file(filename)
    records = get_records(data)
    fix_metadata(records, data)
    