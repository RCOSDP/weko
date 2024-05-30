
import json

from sqlalchemy.sql import func
import pickle
import os
from elasticsearch import Elasticsearch


from invenio_files_rest.models import FileInstance
from invenio_records.models import RecordMetadata
from invenio_db import db
from weko_admin.models import SearchManagement
from weko_records.api import ItemTypes
from weko_records.models import ItemMetadata, ItemTypeProperty, ItemTypeMapping
from weko_workflow.models import Activity

es = Elasticsearch("http://"+os.environ.get('INVENIO_ELASTICSEARCH_HOST','localhost')+":9200")
record_index = "{}-weko".format(os.environ.get('SEARCH_INDEX_PREFIX', ''))
doc_type = "item-v1.0.0"

# search_management
try:
    is_fixed = False
    sm_id = db.session.query(func.max(SearchManagement.id)).first()[0]
    if sm_id is not None:
        sm = SearchManagement.query.filter_by(id=sm_id).one_or_none()
        search_setting = pickle.loads(pickle.dumps(sm.search_setting_all,-1))
        for search_condition in search_setting.get("detail_condition",[]):
            if not search_condition.get("id") == "license":
                continue
            check_vals = search_condition.get("check_val",[])
            check_vals = [{**val, "id":"license_note"} if val["id"] == "license_free" else val for val in check_vals]
            search_condition["check_val"] = check_vals
            is_fixed = True
        sm.search_conditions = search_setting.get("detail_condition")
        sm.search_setting_all=search_setting
        if is_fixed:
            db.session.merge(sm)
            db.session.commit()
            print("complete update search_management.")
    if not is_fixed:
        print("not update search_management")
except BaseException as es:
    import traceback
    db.session.rollback()
    print("raise error with search_management update.")
    traceback.print_exc()

def replace_schema(data):
    is_fixed = False
    if "licensefree" in data:
        license_value = data.pop("licensefree")
        data["licensenote"] = license_value
        is_fixed = True
    return is_fixed

def replace_form(data):
    for d in data:
        for type in d:
            if isinstance(d[type],str):
                if "licensefree" in d[type]:
                    d[type] = d[type].replace("licensefree","licensenote")
                elif "license_free" in d[type]:
                    d[type] = d[type].replace("license_free", "license_note")

# item_type_property
item_type_prop_ids = [props.id for props in ItemTypeProperty.query.all()]
for prop_id in item_type_prop_ids:
    try:
        is_fixed = False
        item_type_prop = ItemTypeProperty.query.filter_by(id=prop_id).one()
        # schema
        schema = item_type_prop.schema
        schema_str=json.dumps(schema)
        if "license_free" in schema_str or "licensefree" in schema_str:
            schema = pickle.loads(pickle.dumps(item_type_prop.schema,-1))
            properties = schema.get("properties")
            is_fixed = replace_schema(properties)
            if is_fixed:
                item_type_prop.schema = schema
                # form
                form = pickle.loads(pickle.dumps(item_type_prop.form,-1))
                items = form.get("items",[])
                replace_form(items)
                item_type_prop.form=form
                # forms
                forms = pickle.loads(pickle.dumps(item_type_prop.forms,-1))
                items = forms.get("items",[])
                replace_form(items)
                item_type_prop.forms = forms
                db.session.merge(item_type_prop)
                db.session.commit()
                print("item_type_property(id: {}): updated".format(prop_id))
        #if not is_fixed:
        #    print("item_type_property(id: {}): not updated".format(prop_id))
    except BaseException as e:
        import traceback
        db.session.rollback()
        print("item_type_property(id: {}): error".format(prop_id))
        traceback.print_exc()


## item_type
itemtypes = ItemTypes.get_all() 
for itemtype in itemtypes:
    try:
        fixed_items = []
        # schema
        schema_str = json.dumps(itemtype.schema)
        if "licensefree" in schema_str or "license_free" in schema_str:
            schema = pickle.loads(pickle.dumps(itemtype.schema,-1))
            properties = schema.get("properties")
            for key, prop in properties.items():
                if "items" in prop.keys():
                    data = prop["items"].get("properties",{})
                else:
                    data = prop.get("properties",{})
                if replace_schema(data):
                    fixed_items.append(key)
            itemtype.schema = schema
            print(fixed_items)
            # form
            form = pickle.loads(pickle.dumps(itemtype.form,-1))
            target_indexes = [i for i,prop in enumerate(form) if prop.get("key") in fixed_items]
            print(target_indexes)
            for target_index in target_indexes:
                if form[target_index].get("key") not in fixed_items:
                    continue
                items = form[target_index].get("items",[])
                for item in items:
                    for key, value in item.items():
                        if isinstance(value, str):
                            if "licensefree" in value:
                                item[key] = value.replace("licensefree","licensenote")
                            elif "license_free" in value:
                                item[key] = value.replace("license_free", "license_note")
            itemtype.form = form
            
            # render
            render = pickle.loads(pickle.dumps(itemtype.render,-1))
            table_row_map = render.get("table_row_map")
            table_row_map["form"] = form
            schema = table_row_map.get("schema")
            properties = schema.get("properties")
            for key in fixed_items:
                prop = properties.get(key)
                if "items" in prop.keys():
                    data = prop["items"].get("properties",{})
                else:
                    data = prop.get("properties",{})
                replace_schema(data)
            table_row_map["schema"] = schema

            #schemaeditor
            schema = render.get("schemaeditor",{}).get("schema")
            for key in fixed_items:
                properties = schema.get(key).get("properties")
                replace_schema(properties)

            itemtype.render = render
            db.session.merge(itemtype)
        
            # item_type_mapping
            fixed_mappings = []
            item_type_mappings = ItemTypeMapping.query.filter_by(item_type_id=itemtype.id).all()
            for item_type_mapping in item_type_mappings:
                mapping = item_type_mapping.mapping
                mapping_str = json.dumps(mapping)
                if 'license_free' in mapping_str or 'licensefree' in mapping_str:
                    mapping = pickle.loads(pickle.dumps(item_type_mapping.mapping,-1))
                    for key in fixed_items:
                        mappings = mapping.get(key,{})
                        for key, data in mappings.items():
                            data_str = json.dumps(data)
                            if 'license_free' in data_str:
                                data_str = data_str.replace("license_free", "license_note")
                            if 'licensefree' in data_str:
                                data_str = data_str.replace("licensefree", "licensenote")
                            mappings[key] = data_str
                    item_type_mapping.mapping = mapping
                    db.session.merge(item_type_mapping)
                    fixed_mappings.append(item_type_mapping.id)
            db.session.commit()
            print("itemtype(id: {}): updated)".format(itemtype.id))
            print("mapping(id:{}) updated".format(fixed_mappings))
        #if not fixed_items:
        #    print("itemtype(id: {}): not updated".format(itemtype.id))
    except BaseException as e:
        import traceback
        db.session.rollback()
        print("itemtype(id: {}): error".format(itemtype.id))
        traceback.print_exc()


def replace_license(data, is_fixed):
    if data.get("licensetype") in ["license_free", "license_note"]:
        is_fixed |= True
        data["licensetype"] = "license_note"
        replace_schema(data)
    return is_fixed

# records
record_uuids = [r.id for r in RecordMetadata.query.all()]
for record_uuid in record_uuids:
    try:
        is_fixed = False
        ## records_metadata
        record = RecordMetadata.query.filter_by(id=record_uuid).one()

        file_props = [key for key, value in record.json.items() if isinstance(value,dict) and value.get("attribute_type") == "file"]
        if file_props:
            record_metadata = pickle.loads(pickle.dumps(record.json,-1))
            for prop in file_props:
                file_datas = record_metadata[prop].get("attribute_value_mlt",[])
                for file_data in file_datas:
                    is_fixed = replace_license(file_data,is_fixed)
            if is_fixed:
                record.json = record_metadata
                db.session.merge(record)


            if is_fixed:
                ## item_metadata
                item = ItemMetadata.query.filter_by(id=record_uuid).one()
                item_metadata = pickle.loads(pickle.dumps(item.json,-1))
                for prop in file_props:
                    file_datas = item_metadata.get(prop,[])
                    if isinstance(file_datas,dict):
                        replace_license(file_datas,is_fixed)
                    elif isinstance(file_datas,list):
                        for file_data in file_datas:
                            replace_license(file_data,is_fixed)
                item.json = item_metadata
                db.session.merge(item)

                ## elasticsearch
                es_data = es.get_source(index=record_index, doc_type=doc_type, id=record_uuid)
                es_metadata = es_data.get("_item_metadata",{})
                for prop in file_props:
                    file_datas = es_metadata[prop].get("attribute_value_mlt",[])
                    for file_data in file_datas:
                        replace_license(file_data, is_fixed)

                es_contents = es_data.get("content",[])
                for content in es_contents:
                    replace_license(content, is_fixed)
                query = {"doc":es_data}
                es.update(index=record_index,doc_type=doc_type,id=record_uuid,body=query)
                db.session.commit()
                print("record_metadata, item_metadata, elasticsearch(id: {}): updated".format(record_uuid))
        #if not is_fixed:
        #    print("record_metadata, item_metadata, elasticsearch(id: {}): not update".format(record_uuid))
    except BaseException as e:
        import traceback
        db.session.rollback()
        print("record_metadata, item_metadata, elasticsearch(id: {}): error".format(record_uuid))
        traceback.print_exc()

# workflow_activity
activities = Activity.query.filter(Activity.temp_data!=None).filter(Activity.temp_data!={}).all()
for activity in activities:
    try:
        is_fixed = False
        temp_data_str = activity.temp_data
        if "license_free" in temp_data_str or "licensefree" in temp_data_str:
            temp_data = json.loads(pickle.loads(pickle.dumps(activity.temp_data, -1)))
            metainfo = temp_data.get("metainfo",{})
            for key, prop in metainfo.items():
                if isinstance(prop, list):
                    for p in prop:
                        is_fixed = replace_license(p, is_fixed)
                elif isinstance(prop, dict):
                    is_fixed = replace_license(p, is_fixed)
                else:
                    continue
            files = temp_data.get("files",[])
            for file in files:
                if file.get("licensetype") == "license_free":
                    file["licensetype"] = "license_note"
                    is_fixed = True
            if is_fixed:
                activity.temp_data = json.dumps(temp_data)
                db.session.merge(activity)
                db.session.commit()
                print("activity(id: {}): updated".format(activity.id))
        
        #if not is_fixed:
        #    print("activity(id: {}): not update".format(activity.id))
    except BaseException as e:
        import traceback
        db.session.rollback()
        print("activity(id: {}): error".format(activity.id))
        traceback.print_exc()


# files_files
files = FileInstance.query.all()
for file in files:
    try:
        is_fixed = False
        if file.json.get("licensetype") in ["license_free", "license_note"]:
            file_data = pickle.loads(pickle.dumps(file.json,-1))
            file_data["licensetype"] = "license_note"
            if "licensefree" in file_data:
                license_value = file_data.pop("licensefree")
                file_data["licensenote"] = license_value
                is_fixed = True
                file.update_json(file_data)
                db.session.commit()
                print("files_files(id: {}): update".format(file.id))
        #if is_fixed:
        #    print("files_files(id: {}): not update".format(file.id))
    except BaseException as e:
        import traceback
        db.session.rollback()
        print("files_files(id: {}): error".format(file.id))
        traceback.print_exc()
