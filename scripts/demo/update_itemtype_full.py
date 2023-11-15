from invenio_db import db
from flask import current_app
from sqlalchemy.orm.attributes import flag_modified
from weko_records.api import ItemsMetadata, ItemTypeEditHistory, \
    ItemTypeNames, ItemTypeProps, ItemTypes, Mapping
from weko_workflow.api import WorkFlow
import traceback
import copy
import pickle
import time
import json

def checkRegisterdProperty(itemType,new_prop_ids):
    meta_list = itemType.render.get('meta_list',{})
    old_prop_ids = []
    for k in meta_list.keys():
        for id in new_prop_ids:
            if 'cus_{}'.format(id) in itemType.render['meta_list'][k]['input_type']:
                print('cus_{} is already updated.'.format(id))
                old_prop_ids.append(id)
    
    return list(set(new_prop_ids) - set(old_prop_ids)) 
                

def main():
    new_prop_ids = [1048,1049,1050,1051,1052,1053,1054,1055,1056,1057]
    try:
        i = 1
        with db.session.begin_nested():
            # itemType = ItemTypes.get_by_name('デフォルトアイテムタイプ（フル）')
            itemType = ItemTypes.get_by_id(30002)
            cur_prop_ids = checkRegisterdProperty(itemType,new_prop_ids)
            _render = pickle.loads(pickle.dumps(itemType.render, -1))
            for id in cur_prop_ids:
                _prop = ItemTypeProps.get_record(id)
                _prop_id = "item_{}".format(int(time.time())+i)       
                i = i +1
                if _prop:
                    _render['meta_list'][_prop_id] = json.loads('{"input_maxItems": "9999","input_minItems": "1","input_type": "cus_'+str(id)+'","input_value": "","option": {"crtf": false,"hidden": false,"multiple": true,"required": false,"showlist": false},"title": "'+_prop.name+'","title_i18n": {"en": "", "ja": "'+_prop.name+'"}}')
                    _render['schemaeditor']['schema'][_prop_id]=_prop.schema
                    _render['table_row_map']['schema']['properties'][_prop_id]=_prop.schema
                    _form = json.loads(json.dumps(_prop.form).replace('parentkey',_prop_id))
                    _render['table_row_map']['form'].append(_form)
                    _render['table_row_map']['mapping'][_prop_id] = ""
                    _render['table_row'].append(_prop_id)                    
                    print('property cus_{} has been registerd.'.format(id))     

            if len(cur_prop_ids)>0:
                from weko_itemtypes_ui.utils import fix_json_schema,update_required_schema_not_exist_in_form, update_text_and_textarea
                table_row_map = _render.get('table_row_map')
                json_schema = fix_json_schema(table_row_map.get('schema'))
                json_form = table_row_map.get('form')
                json_schema = update_required_schema_not_exist_in_form(
                    json_schema, json_form)
                json_schema, json_form = update_text_and_textarea(
                        itemType.id, json_schema, json_form)
                
                itemType.schema = json_schema
                itemType.form = json_form
                itemType.render = _render
                
                flag_modified(itemType, 'schema')
                flag_modified(itemType, 'form')
                flag_modified(itemType, 'render')
                db.session.merge(itemType)
                print("session merged.")
        db.session.commit()
        print("session commited.")
    except Exception as e:
        print(traceback.format_exc())
        db.session.rollback()

if __name__ == '__main__':
    main()