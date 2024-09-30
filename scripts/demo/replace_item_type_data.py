from weko_records.models import ItemType
from weko_itemtypes_ui.utils import fix_json_schema, update_required_schema_not_exist_in_form
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.attributes import flag_modified
from invenio_db import db
from flask import current_app

from properties import checkbox, radiobutton, listbox, property_func

UPDATE_DATE = '2024/9/28'


def get_option(item_type_data, item_key):
    return item_type_data.render.get("meta_list", {}).get(item_key, {}).get("option")

def replace_schema(schema_old, schema_new, item_key, sub_key, multi_flag):
    _required = []

    if schema_old.get("properties", {}).get(item_key, {}).get("type") == "array":
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
        if schema.get("type") == "object":
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

        if schema.get("type") == "object" and multi_flag:
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
        

def replace_form(form_old, form_new, item_key, sub_key, multi_flag):
    for i in form_old.get("items"):
        if sub_key in i.get("key"):
            _titleMap = i.get("titleMap")
            _value = i.get("title_i18n_temp")
            _v_option = {
                "required": i.get("required", False),
                "isShowList": i.get("isShowList", False),
                "isSpecifyNewline": i.get("isSpecifyNewline", False),
                "isHide": i.get("isHide", False),
                "isNonDisplay": i.get("isNonDisplay", False),
            }
        else:
            _lang = i.get("title_i18n_temp")
            _l_option = {
                "required": i.get("required", False),
                "isShowList": i.get("isShowList", False),
                "isSpecifyNewline": i.get("isSpecifyNewline", False),
                "isHide": i.get("isHide", False),
                "isNonDisplay": i.get("isNonDisplay", False),
            }

    for i in form_new.get("items"):
        if sub_key in i.get("key"):
            i["titleMap"] = _titleMap
            i["title_i18n_temp"] = _value
            for k, v in _v_option.items():
                i[k] = v
        else:
            i["title_i18n_temp"] = _lang
            for k, v in _l_option.items():
                i[k] = v

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

def replace_item_type_data(render_old, render_new, item_key, sub_key, prop, option_old):
    if "meta_list" in render_new and \
            item_key in render_new["meta_list"]:
        render_new["meta_list"][item_key]["option"] = option_old
    multi_flag = prop.multiple_flag
    if "multiple" in option_old:
        multi_flag = option_old["multiple"]

    _table_row_schema_old = render_old['table_row_map']['schema']
    _table_row_schema_new = render_new['table_row_map']['schema']
    _schema_old = render_old['schemaeditor']['schema']
    _schema_new = render_new['schemaeditor']['schema']
    _form_old = render_old['table_row_map']['form']
    _form_new = render_new['table_row_map']['form']
    replace_schema(_table_row_schema_old, _table_row_schema_new, item_key, sub_key, multi_flag)
    replace_schema(_schema_old, _schema_new, item_key, sub_key, False)
    for f in _form_old:
        if f.get("key") == item_key:
            _form_prop_old = f
            break
    for f in _form_new:
        if f.get("key") == item_key:
            _form_prop_new = f
            break
    replace_form(_form_prop_old, _form_prop_new, item_key, sub_key, multi_flag)

def main():
    current_app.logger.info('=============== replace_item_type_data ===============')
    current_app.logger.info('start')
    try:
        sql = """
            SELECT schema,
                   form,
                   render
            FROM item_type_version
            WHERE id = :item_type_id
              AND  updated <= :update_date
            ORDER BY version_id DESC;
            """.strip()
        res = db.session.query(ItemType.id).all()
        for _id in res:
            params = {
                "item_type_id": _id,
                "update_date": UPDATE_DATE
            }
            try:
                with db.session.begin_nested():
                    item_type_new = ItemType.query.filter(ItemType.id==_id).order_by(desc(ItemType.created)).first()
                    item_type_old = db.session.execute(sql, params).first()

                    for _k1, _v1 in item_type_old.render["schemaeditor"]["schema"].items():
                        _prop_keys = _v1.get("properties", {}).keys()

                        if "subitem_checkbox_item" in _prop_keys:
                            _option = get_option(item_type_old, _k1)
                            replace_item_type_data(item_type_old.render, item_type_new.render, _k1, "subitem_checkbox_item", checkbox, _option)
                        if "subitem_radio_item" in _prop_keys:
                            _option = get_option(item_type_old, _k1)
                            replace_item_type_data(item_type_old.render, item_type_new.render, _k1, "subitem_radio_item", radiobutton, _option)
                        if "subitem_select_item" in _prop_keys:
                            _option = get_option(item_type_old, _k1)
                            replace_item_type_data(item_type_old.render, item_type_new.render, _k1, "subitem_select_item", listbox, _option)
                    json_schema = fix_json_schema(item_type_new.render['table_row_map']['schema'])
                    json_form = item_type_new.render['table_row_map']['form']
                    json_schema = update_required_schema_not_exist_in_form(json_schema, json_form)
                    item_type_new.schema = json_schema
                    item_type_new.form = json_form
                    flag_modified(item_type_new, "schema")
                    flag_modified(item_type_new, "form")
                    flag_modified(item_type_new, "render")
                    db.session.merge(item_type_new)
                db.session.commit()
                current_app.logger.info('Updated item type (id = {}) successfully.'.format(_id))
            except SQLAlchemyError as e:
                current_app.logger.error('Failed to update item type (id = {}).'.format(_id))
                current_app.logger.error(e)
                db.session.rollback()
            except Exception as e:
                current_app.logger.error('Failed to update item type (id = {}).'.format(_id))
                current_app.logger.error(e)
                db.session.rollback()
    except Exception as ex:
        current_app.logger.error(ex)
    current_app.logger.info('end')
    current_app.logger.info('=============== Finished! ===============')

if __name__ == '__main__':
    """Main context."""
    main()