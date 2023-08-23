
from collections import OrderedDict
from invenio_db import db
from invenio_records.models import RecordMetadata
from weko_records.api import ItemTypes,Mapping
from weko_records.models import ItemMetadata
from weko_deposit.api import WekoIndexer
from sqlalchemy.orm.attributes import flag_modified
from weko_schema_ui.schema import  SchemaTree
from weko_records.serializers.utils import get_mapping

def handle_get_all_sub_id_and_name(items, root_id=None):
    ids = []
    for key in sorted(items.keys()):
        if key == "iscreator":
            pass
        item = items.get(key)
        if item.get("items") and item.get("items").get("properties"):
            _ids = handle_get_all_sub_id_and_name(item.get("items").get("properties"))
            ids += [key+"[]."+_id for _id in _ids]
        elif item.get("type") == "object" and item.get("properties"):
            _ids = handle_get_all_sub_id_and_name(item.get("properties"))
            ids += [str(key)+"."+str(_id) for _id in _ids]
        elif item.get("format") == "checkboxes":
            ids.append(str(key) + "[]")
        else:
            ids.append(str(key))
    if root_id:
        ids = [root_id+"."+_id for _id in ids]
    
    return ids

def get_itemtype_fields(itemtype_id):
    
    item_type = ItemTypes.get_by_id(id_=itemtype_id, with_deleted=True)
    item_type = item_type.render
    meta_system = [key for key in item_type.get("meta_system", {})]
    schema = (
        item_type.get("table_row_map", {})
        .get("schema", {})
        .get("properties", {})
    )
    ids_line=list()
    for key in [*item_type.get("table_row", [])]:
        if key in meta_system:
            continue
        
        item = schema.get(key)
        root_id=key
        # have not sub item
        if not (item.get("properties") or item.get("items")):
            ids_line.append(root_id)
        else:
            sub_items = (
                item.get("properties")
                if item.get("properties")
                else item.get("items").get("properties")
            )

            _ids = handle_get_all_sub_id_and_name(
                sub_items, root_id
            )
            ids_line+=_ids
    return ids_line

def replace_item(data, paths, _target, _from,_to):
    if paths[0] == _target:
        if _from == data.get(paths[0]):
            data[paths[0]] = _to
    elif len(paths) > 1:
        if "[]" in paths[0]:
            _data = data.get(paths[0].replace("[]",""))
            for _d in _data:
                replace_item(_d,paths[1:],_target,_from,_to)
        else:
            _data = data.get(paths[0])
            replace_item(_data,paths[1:],_target,_from,_to)

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

if __name__ == "__main__":

    field="subitem_description_type" # field to replace
    target="isIdenticalTo" # the value to replace
    to="Other" # the value to use for replacement

    try:
        records = (
            db.session.query(
                RecordMetadata
            ).all()
        )
        item_type_props = dict()
        item_type_mapping=dict()
        count=0
        result = {}
        for r in records:
            _record = RecordMetadata.query.filter_by(id=r.id).one()
            record = _record.json
            _item_metadata = ItemMetadata.query.filter_by(id=r.id).one()
            item_metadata = _item_metadata.json
            indexer = WekoIndexer()
            es_data = indexer.get_metadata_by_item_id(r.id).get("_source") # esのデータ
            item_type_id = record.get("item_type_id")
            if item_type_id not in item_type_props:
                item_type_props[item_type_id] = get_itemtype_fields(item_type_id)
            if item_type_id not in item_type_mapping:
                mapping = Mapping.get_record(item_type_id).dumps()
                item_type_mapping[item_type_id] = {value:key for key, value in get_mapping(mapping, "jpcoar_mapping").items()}
            target_props = [prop for prop in item_type_props[item_type_id] if field in prop.split(".")[-1]]
            for prop in target_props:
                paths = prop.split(".")
                record_ele = record.get(paths[0])
                if record_ele:
                    attr_lst = record_ele.get("attribute_value_mlt")
                    for d in attr_lst:
                        replace_item(d,paths[1:],field,target,to)
                item_ele = item_metadata.get(paths[0])
                if item_ele:
                    if isinstance(item_ele,dict):
                        replace_item(item_ele,paths[1:],field,target,to)
                    elif isinstance(item_ele,list):
                        for d in item_ele:
                            replace_item(d,paths[1:],field,target,to)
                es_ele= es_data.get("_item_metadata").get(paths[0])
                if es_ele:
                    meta_ds = es_ele.get("attribute_value_mlt")
                    for d in meta_ds:
                        replace_item(d,paths[1:],field,target,to)
            # replace es data
            new_es_data, dc = get_jpcoar_mapping(item_type_id,item_metadata)
            target_props_replace_arr = [prop.replace("[]","") for prop in target_props]
            field_lst = [value.split(".")[0] for key, value in item_type_mapping[item_type_id].items() 
                         if key in target_props_replace_arr]
            for f in field_lst:
                if f in es_data and f in new_es_data:
                    es_data[f] = new_es_data[f]
            for key,value in dc.items():
                if key in es_data:
                    es_data[key] = value
            indexer.client.update(index=indexer.es_index,doc_type=indexer.es_doc_type,
                                  id=str(r.id),body={'doc':es_data})
            # merge
            flag_modified(_record,'json')
            db.session.merge(_record)
            flag_modified(_item_metadata,'json')
            db.session.merge(_item_metadata)
            count+=1
            
        db.session.commit()
            
        print("Update {} items successful".format(count))
    except:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        
