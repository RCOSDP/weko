from collections import OrderedDict
import re
from flask import current_app

from invenio_db import db
from invenio_records.models import RecordMetadata
from weko_records.api import ItemTypes,Mapping
from weko_records.utils import set_timestamp
from weko_deposit.api import WekoIndexer
from sqlalchemy.orm.attributes import flag_modified
from weko_schema_ui.schema import  SchemaTree
from weko_records.serializers.utils import get_mapping
from sqlalchemy import types
from invenio_pidstore.models import PersistentIdentifier
from weko_search_ui.utils import handle_get_all_id_in_item_type

from weko_records.api import ItemsMetadata


def replace_item(data, paths, _target, _from,_to):
    result = False
    if paths[0] == _target:
        if _from == data.get(paths[0]):
            data[paths[0]] = _to
            result = True
    elif len(paths) > 1:
        if "[]" in paths[0]:
            _data = data.get(paths[0].replace("[]",""))
            for _d in _data:
                result |= replace_item(_d,paths[1:],_target,_from,_to)
        else:
            _data = data.get(paths[0])
            result |= replace_item(_data,paths[1:],_target,_from,_to)
    return result

def get_jpcoar_mapping(item_type_id, data):
    def _get_author_link(author_link, value):
        """Get author link data."""
        if isinstance(value, list):
            for v in value:
                if (
                    "nameIdentifiers" in v
                    and len(v["nameIdentifiers"]) > 0
                    and "nameIdentifierScheme" in v["nameIdentifiers"][0]
                    and v["nameIdentifiers"][0]["nameIdentifierScheme"] == "WEKO"
                ):
                    author_link.append(v["nameIdentifiers"][0]["nameIdentifier"])
        elif (
            isinstance(value, dict)
            and "nameIdentifiers" in value
            and len(value["nameIdentifiers"]) > 0
            and "nameIdentifierScheme" in value["nameIdentifiers"][0]
            and value["nameIdentifiers"][0]["nameIdentifierScheme"] == "WEKO"
        ):
            author_link.append(value["nameIdentifiers"][0]["nameIdentifier"])
    dc = OrderedDict()
    jpcoar = OrderedDict()
    ojson = ItemTypes.get_record(item_type_id)
    mjson = Mapping.get_record(item_type_id)
    mp = mjson.dumps()
    data.get("$schema")
    author_link = []
    item=dict()
    ar=[]
    pubdate = None
    for k, v in data.items():
        if k != "pubdate":
            if k == "$schema" or mp.get(k) is None:
                continue

        item.clear()
        try:
            item["attribute_name"] = (
                ojson["properties"][k]["title"]
                if ojson["properties"][k].get("title") is not None
                else k
            )
        except Exception:
            pub_date_setting = {
                "type": "string",
                "title": "Publish Date",
                "format": "datetime",
            }
            ojson["properties"]["pubdate"] = pub_date_setting
            item["attribute_name"] = "Publish Date"
        iscreator = False
        creator = ojson["properties"][k]
        if "object" == creator["type"]:
            creator = creator["properties"]
            if "iscreator" in creator:
                iscreator = True
        elif "array" == creator["type"]:
            creator = creator["items"]["properties"]
            if "iscreator" in creator:
                iscreator = True
        if iscreator:
            item["attribute_type"] = "creator"

        item_data = ojson["properties"][k]
        if "array" == item_data.get("type"):
            properties_data = item_data["items"]["properties"]
            if "filename" in properties_data:
                item["attribute_type"] = "file"

        if isinstance(v, list):
            if len(v) > 0 and isinstance(v[0], dict):
                item["attribute_value_mlt"] = v
                _get_author_link(author_link, v)
            else:
                item["attribute_value"] = v
        elif isinstance(v, dict):
            ar.append(v)
            item["attribute_value_mlt"] = ar
            ar = []
            _get_author_link(author_link, v)
        else:
            item["attribute_value"] = v

        dc[k] = item.copy()
        if k != "pubdate":
            item.update(mp.get(k))
        else:
            pubdate = v
        jpcoar[k] = item.copy()
    jrc = SchemaTree.get_jpcoar_json(jpcoar)
    if dc:
        dc.update(dict(author_link=author_link))
    return jrc, dc

def get_item_type_mapping(field):
    """置換対象となるフィールドを含むパスと、そのパスがマッピングされたesのフィールドのリストを取得"""
    item_types = ItemTypes.get_all()
    target_paths = {} # item_type_idと置換対象となるフィールドを含むパスのリスト
    target_es_field = {} # item_type_idと置換対象のパスがマッピングされたesのフィールドのリスト
    with current_app.test_request_context(headers=[('Accept-Language','ja')]):
        for item_type in item_types:
            paths = handle_get_all_id_in_item_type(item_type.id)
            paths = [re.sub('\[\d\]','[]',p.replace(".metadata.","")) for p in paths]
            paths = [p for p in paths if field in p.split(",")[-1]]
            if len(paths)>0:
                target_paths[item_type.id]=paths
                mapping = Mapping.get_record(item_type.id)
                if mapping:
                    mapping = mapping.dumps()
                    mapp = {value:key for key, value in get_mapping(mapping, "jpcoar_mapping").items()}
                    paths_replace_arr = [p.replace("[]","") for p in paths]
                    field_lst = [value.split(".")[0] for key, value in mapp.items() if key in paths_replace_arr]
                    target_es_field[item_type.id] = field_lst
    return target_paths, target_es_field

def get_target_record(paths):
    """置換対象となるアイテムタイプに所属、かつ置換対象のフィールドを持つプロパティを含むレコードの取得"""
    res=list()

    item_type_ids = list(paths.keys())
    for item_type_id in item_type_ids:
        item_metadatas = ItemsMetadata.get_by_item_type_id(item_type_id)
        root_keys = [p.split(".")[0].replace("[]","") for p in paths[item_type_id]]
        data = [d for d in item_metadatas if any(key in d.json for key in root_keys)]
        res+=(data)
    return res

if __name__ == "__main__":

    field="subitem_description_type" # field to replace
    target="isIdenticalTo" # the value to replace
    to="Other" # the value to use for replacement

    paths, target_es_fields = get_item_type_mapping(field)
    records = get_target_record(paths)
    indexer = WekoIndexer()
    count = 0
    for r in records:
        try:
            pid = PersistentIdentifier.query.filter_by(object_uuid=r.id).filter_by(pid_type='recid').one_or_none()
            _record = RecordMetadata.query.filter_by(id=r.id).one_or_none()
            record = _record.json
            item_metadata = r.json
            es_data = indexer.get_metadata_by_item_id(r.id).get("_source")
            
            item_type_id=r.item_type_id
            target_paths = paths[item_type_id]
            is_changed = False
            
            for path in target_paths:
                props = path.split(".")
                root_prop = props[0].replace("[]","")
                record_ele = record.get(root_prop)
                if record_ele:
                    attr_lst = record_ele.get("attribute_value_mlt")
                    for attr in attr_lst:
                        is_changed |= replace_item(attr,props[1:],field,target,to)
                item_ele = item_metadata.get(root_prop)
                if item_ele:
                    if isinstance(item_ele,dict):
                        is_changed |= replace_item(item_ele,props[1:],field,target,to)
                    elif isinstance(item_ele,list):
                        for e in item_ele:
                            is_changed |= replace_item(e,props[1:],field,target,to)
                es_ele= es_data.get("_item_metadata").get(root_prop)
                if es_ele:
                    attr_lst = es_ele.get("attribute_value_mlt")
                    for attr in attr_lst:
                        is_changed |= replace_item(attr,props[1:],field,target,to)
            if is_changed:
                # merge
                flag_modified(_record,'json')
                db.session.merge(_record)
                flag_modified(r,'json')
                db.session.merge(r)
                # update es data
                new_es_data, dc = get_jpcoar_mapping(item_type_id,item_metadata)
                for f in target_es_fields[item_type_id]:
                    if f in es_data and f in new_es_data:
                        es_data[f] = new_es_data[f]
                for key,value in dc.items():
                    if key in es_data:
                        es_data[key] = value
                set_timestamp(es_data, _record.created, _record.updated)
                indexer.client.update(index=indexer.es_index,doc_type=indexer.es_doc_type,
                                      id=str(r.id),body={'doc':es_data})
                db.session.commit()
                print("fixed: {}".format(pid.pid_value))
                count+=1
        except:
            db.session.rollback()
            print("raise error: {}".format(pid.pid_value if pid is not None else ""))
    print("fixed {} items.".format(count))
