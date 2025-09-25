from invenio_db import db
from flask import current_app
from sqlalchemy.orm.attributes import flag_modified
from weko_records.models import ItemTypeMapping
from sqlalchemy import desc
from weko_records.api import (
    ItemsMetadata,
    ItemTypeEditHistory,
    ItemTypeNames,
    ItemTypeProps,
    ItemTypes,
    Mapping,
)
from weko_workflow.api import WorkFlow
import traceback
import copy
import pickle
import argparse
import time
from datetime import datetime
import json

from properties import (
    jpcoar_catalog,
    jpcoar_dataset_series,
    jpcoar_holding_agent,
    jpcoar_format,
    dcterms_extent,
    dcndl_original_language,
    dcndl_volume_title,
    dcndl_edition,
    date_literal,
    publisher_info,
)


def checkRegisterdProperty(itemType, new_prop_ids):
    meta_list = itemType.render.get("meta_list", {})
    old_prop_ids = []
    for k in meta_list.keys():
        for id in new_prop_ids:
            if "cus_{}".format(id) in itemType.render["meta_list"][k]["input_type"]:
                print("cus_{} is already updated.".format(id))
                old_prop_ids.append(id)

    return list(set(new_prop_ids) - set(old_prop_ids))


def main():

    new_prop_ids = [
        publisher_info.property_id,
        jpcoar_catalog.property_id,
        jpcoar_dataset_series.property_id,
        jpcoar_holding_agent.property_id,
        jpcoar_format.property_id,
        dcterms_extent.property_id,
        dcndl_original_language.property_id,
        dcndl_volume_title.property_id,
        dcndl_edition.property_id,
        date_literal.property_id,
    ]
    
    new_prop_mapping = {
        publisher_info.property_id:publisher_info.mapping,
        jpcoar_catalog.property_id:jpcoar_catalog.mapping,
        jpcoar_dataset_series.property_id:jpcoar_dataset_series.mapping,
        jpcoar_holding_agent.property_id:jpcoar_holding_agent.mapping,
        jpcoar_format.property_id:jpcoar_format.mapping,
        dcterms_extent.property_id:dcterms_extent.mapping,
        dcndl_original_language.property_id:dcndl_original_language.mapping,
        dcndl_volume_title.property_id:dcndl_volume_title.mapping,
        dcndl_edition.property_id:dcndl_edition.mapping,
        date_literal.property_id:date_literal.mapping,
    }

    try:
        i = 1
        with db.session.begin_nested():
            itemType = ItemTypes.get_by_name('Multiple')
            if itemType is None:
                itemType = ItemTypes.get_by_id(12,with_deleted=True)
                if itemType is None:
                    raise Exception("itemType is not found.")
            if itemType:
                cur_prop_ids = checkRegisterdProperty(itemType, new_prop_ids)
                _render = pickle.loads(pickle.dumps(itemType.render, -1))
                _mapping = (
                    ItemTypeMapping.query.filter(ItemTypeMapping.item_type_id == itemType.id)
                    .order_by(desc(ItemTypeMapping.created))
                    .first()
                )
                for id in cur_prop_ids:
                    _prop = ItemTypeProps.get_record(id)
                    _prop_id = "item_{}".format(int(datetime(2023,10,30,0,0).strftime('%s')) + i)
                    i = i + 1
                    if _prop:
                        _render["meta_list"][_prop_id] = json.loads(
                            '{"input_maxItems": "9999","input_minItems": "1","input_type": "cus_'
                            + str(id)
                            + '","input_value": "","option": {"crtf": false,"hidden": false,"multiple": true,"required": false,"showlist": false},"title": "'
                            + _prop.name
                            + '","title_i18n": {"en": "", "ja": "'
                            + _prop.name
                            + '"}}'
                        )
                        _render["schemaeditor"]["schema"][_prop_id] = _prop.schema
                        _render["table_row_map"]["schema"]["properties"][
                            _prop_id
                        ] = _prop.schema
                        _form = json.loads(
                            json.dumps(_prop.form).replace("parentkey", _prop_id)
                        )
                        _render["table_row_map"]["form"].append(_form)
                        _render["table_row_map"]["mapping"][_prop_id] = pickle.loads(pickle.dumps(new_prop_mapping.get(str(id),""),-1))
                        _mapping.mapping[_prop_id] = pickle.loads(pickle.dumps(new_prop_mapping.get(str(id),""),-1))
                        _render["table_row"].append(_prop_id)
                        if _prop_id in _mapping.mapping and _mapping.mapping[_prop_id] and "=" not in _mapping.mapping[_prop_id]:
                            _mapping.mapping[_prop_id] = pickle.loads(pickle.dumps(_render["table_row_map"]["mapping"][_prop_id],-1))
                        print("property cus_{} has been registerd.".format(id))

                if len(cur_prop_ids) > 0:
                    from weko_itemtypes_ui.utils import (
                        fix_json_schema,
                        update_required_schema_not_exist_in_form,
                        update_text_and_textarea,
                    )

                    table_row_map = _render.get("table_row_map")
                    json_schema = fix_json_schema(table_row_map.get("schema"))
                    json_form = table_row_map.get("form")
                    json_schema = update_required_schema_not_exist_in_form(
                        json_schema, json_form
                    )
                    json_schema, json_form = update_text_and_textarea(
                        itemType.id, json_schema, json_form
                    )

                    itemType.schema = json_schema
                    itemType.form = json_form
                    itemType.render = _render

                    flag_modified(itemType, "schema")
                    flag_modified(itemType, "form")
                    flag_modified(itemType, "render")
                    db.session.merge(itemType)
                    
                    flag_modified(_mapping, 'mapping')
                    db.session.merge(_mapping)
                    Mapping.create(item_type_id=itemType.id,
                               mapping=_mapping.mapping)
                    print("session merged.")

        db.session.commit()
        
        
        print("session commited.")
    except Exception as e:
        print(traceback.format_exc())
        db.session.rollback()


if __name__ == "__main__":
    main()