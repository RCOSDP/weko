from weko_records.models import ItemType
from sqlalchemy import desc
from invenio_db import db
from flask import current_app

from properties import checkbox, radiobutton, listbox, property_func

UPDATE_DATE = '2024/9/14'


def get_option(item_type_data, item_key):
    return item_type_data.render.get("meta_list", {}).get(item_key, {}).get("option")

def replace_schema(schema_old, schema_new, item_key, sub_key, prop, option_old):
    multi_flag = prop.multiple_flag
    _required = []

    if "multiple" in option_old:
        multi_flag = option_old["multiple"]
    if schema_old.get("type") == "array":
        _enum = schema_old.get("properties", {}) \
            .get(item_key, {}).get("items", {}) \
            .get("properties", {}).get(sub_key, {}) \
            .get("items", {}).get("enum", [])
        _required = schema_old.get("properties", {}) \
            .get(item_key, {}).get("items", {}).get("required", [])
    else:
        _enum = schema_old.get("properties", {}) \
            .get(item_key, {}).get("properties", {}).get(sub_key, {}) \
            .get("items", {}).get("enum", [])
        _required = schema_old.get("properties", {}) \
            .get(item_key, {}).get("required", [])

    if schema_new \
            and "properties" in schema_new \
            and item_key in schema_new["properties"]:
        schema = schema_new["properties"][item_key]
        if schema.get("type") == "option":
            if "properties" in schema \
                    and sub_key in schema["properties"] \
                    and "items" in schema["properties"][sub_key]:
                schema["properties"][sub_key]["items"]["enum"] = _enum
            if _required:
                schema["required"] = _required
        else:
            if "items" in schema:
                if "properties" in schema["items"] \
                        and sub_key in schema["items"]["properties"] \
                        and "items" in schema["items"]["properties"][sub_key]:
                    schema["items"]["properties"][sub_key]["items"]["enum"] = _enum
                if _required:
                    schema["items"]["required"] = _required

        if schema.get("type") == "option" and multi_flag:
            _title = schema.pop("title")
            schema_new["properties"][item_key] = {
                "type": "array",
                "title": _title,
                "minItems": "1",
                "maxItems": "9999",
                "items": schema,
            }
        elif schema.get("type") == "array" and not multi_flag:
            _title = schema.pop("title")
            _schema = schema.get("items", {})
            _schema["title"] = _title
            schema_new["properties"][item_key] = _schema

def replace_form(form_old, form_new, item_key, sub_key, prop, option_old):
    multi_flag = prop.multiple_flag

    if "multiple" in option_old:
        multi_flag = option_old["multiple"]
    for i in form_old.get("items"):
        if sub_key in i.get("key"):
            _titleMap = i.get("titleMap")
            _value = i.get("title_i18n_temp")
        else:
            _lang = i.get("title_i18n_temp")

    for i in form_new.get("items"):
        if sub_key in i.get("key"):
            i["titleMap"] = _titleMap
            i["title_i18n_temp"] = _value
        else:
            i["title_i18n_temp"] = _lang

    if form_new.get("add", None) == None and multi_flag:
        form_new["add"] = "New"
        form_new["style"] = {"add": "btn-success"}
        for i in form_new.get("items"):
            i.get("key").replace(item_key, "{}[]".format(item_key))
    elif form_new.get("add", None) == "New" and not multi_flag:
        form_new["type"] = "fieldset"
        form_new.pop("add")
        form_new.pop("style")
        for i in form_new.get("items"):
            i.get("key").replace("{}[]".format(item_key), item_key)

def main():
    current_app.logger.info('start')
    try:
        sql = """
            SELECT schema,
                   form,
                   render
            FROM item_type_version
            WHERE id = :item_type_id
              AND  updated < :update_date
            ORDER BY version_id DESC;
            """.strip()
        res = db.session.query(ItemType.id).all()
        for _id in res:
            params = {
                "item_type_id": _id,
                "update_date": UPDATE_DATE
            }
            _checkbox_key = None
            _radiobtn_key = None
            _listbox_key = None
            with db.session.begin_nested():
                item_type_new = ItemType.query.filter(ItemType.id==_id).order_by(desc(ItemType.created)).first()
                item_type_old = db.session.execute(sql, params).first()

                if item_type_old and "properties" in item_type_old.schema:
                    for _k1, _v1 in item_type_old.schema["properties"].items():
                        if _v1.get("type") == "object":
                            _prop_keys = _v1.get("properties", {}).keys()
                        elif _v1.get("type") == "array":
                            _prop_keys = _v1.get("items", {}).get("properties", {}).keys()
                        
                        if "subitem_checkbox_item" in _prop_keys:
                            _checkbox_key = _k1
                            _option = get_option(item_type_old, _checkbox_key)
                        if "subitem_radio_item" in _prop_keys:
                            _radiobtn_key = _k1
                            _option = get_option(item_type_old, _radiobtn_key)
                        if "subitem_select_item" in _prop_keys:
                            _listbox_key = _k1
                            _option = get_option(item_type_old, _listbox_key)

                if _option:
                    # schema
                    if _checkbox_key:
                        replace_schema(item_type_old.schema, item_type_new.schema, _checkbox_key, "subitem_checkbox_item", checkbox, _option)
                    if _radiobtn_key:
                        replace_schema(item_type_old.schema, item_type_new.schema, _radiobtn_key, "subitem_radio_item", radiobutton, _option)
                    if _listbox_key:
                        replace_schema(item_type_old.schema, item_type_new.schema, _listbox_key, "subitem_select_item", listbox, _option)

                    # form
                    _form_old = None
                    _form_new = None
                    for f in item_type_old.form:
                        if _checkbox_key and f.get("key") == _checkbox_key:
                            _form_old = f
                        if _radiobtn_key and f.get("key") == _radiobtn_key:
                            _form_old = f
                        if _listbox_key and f.get("key") == _listbox_key:
                            _form_old = f
                    for f in item_type_new.form:
                        if _checkbox_key and f.get("key") == _checkbox_key:
                            _form_new = f
                        if _radiobtn_key and f.get("key") == _radiobtn_key:
                            _form_new = f
                        if _listbox_key and f.get("key") == _listbox_key:
                            _form_new = f
                    if _form_old and _form_new:
                        if _checkbox_key:
                            replace_form(_form_old, _form_new, _checkbox_key, "subitem_checkbox_item", checkbox, _option)
                        if _radiobtn_key:
                            replace_form(_form_old, _form_new, _radiobtn_key, "subitem_radio_item", radiobutton, _option)
                        if _listbox_key:
                            replace_form(_form_old, _form_new, _listbox_key, "subitem_select_item", listbox, _option)

                current_app.logger.info(_k1)
                current_app.logger.info(_v1)
            break
        db.session.commit()
    except Exception as ex:
        current_app.logger.error(ex)
        db.session.rollback()
    current_app.logger.info('end')
    current_app.logger.info('Finished!')

if __name__ == '__main__':
    """Main context."""
    main()