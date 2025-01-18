from weko_records.models import ItemType
from weko_itemtypes_ui.utils import fix_json_schema, update_required_schema_not_exist_in_form
from sqlalchemy import desc,asc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.attributes import flag_modified
from invenio_db import db
from flask import current_app
import logging

import argparse

UPDATE_DATE = '2024/9/9'


def get_multiple(render_data, item_key):
    return {
        "title": render_data.get("meta_list", {}).get(item_key, {}).get("title", ""),
        "multiple": render_data.get("meta_list", {}).get(item_key, {}).get("option", {}).get("multiple", None)
    }


def replace_schema(schema_old, schema_new):
    _required = []

    if schema_old and schema_old.get("enum") and \
            isinstance(schema_new, dict):
        schema_new["enum"] = schema_old.get("enum")
    if schema_old and schema_old.get("currentEnum") and \
            isinstance(schema_new, dict):
        schema_new["currentEnum"] = schema_old.get("currentEnum")
    if schema_old and schema_old.get("title") and \
            isinstance(schema_new, dict):
        schema_new["title"] = schema_old.get("title")
    if schema_old and schema_old.get("title_i18n") and \
            isinstance(schema_new, dict):
        schema_new["title_i18n"] = schema_old.get("title_i18n")
    if schema_old and schema_old.get("title_i18n_temp") and \
            isinstance(schema_new, dict):
        schema_new["title_i18n_temp"] = schema_old.get("title_i18n_temp")
    if schema_old and schema_old.get("type") == "array" and \
            schema_new and schema_new.get("type") == "array" and \
            "items" in schema_old and \
            "items" in schema_new:
        replace_schema(schema_old["items"], schema_new["items"])
    elif schema_old and schema_old.get("type") == "object" and \
            schema_new and schema_new.get("type") == "object":
        _required = schema_old.get("required", [])
        if schema_new and _required:
            schema_new["required"] = _required
        if "properties" in schema_old and \
                "properties" in schema_new:
            for subkey in schema_old.get("properties", {}).keys():
                if subkey in schema_new["properties"]:
                    replace_schema(
                        schema_old["properties"][subkey],
                        schema_new["properties"][subkey]
                    )
    
def replace_form(item_old, item_new):
    if item_old and item_new:
        if isinstance(item_old, dict) and isinstance(item_new, dict):
            _option = {
                "required": item_old.get("required", False),
                "isShowList": item_old.get("isShowList", False),
                "isSpecifyNewline": item_old.get("isSpecifyNewline", False),
                "isHide": item_old.get("isHide", False),
                "isNonDisplay": item_old.get("isNonDisplay", False),
            }
            _titleMap = item_old.get("titleMap")
            _title = item_old.get("title")
            _title_i18n = item_old.get("title_i18n")
            _title_i18n_temp = item_old.get("title_i18n_temp")
            for k, v in _option.items():
                item_new[k] = v
            if _title:
                item_new["title"] = _title
            if _titleMap:
                item_new["titleMap"] = _titleMap
            if _title_i18n:
                item_new["title_i18n"] = _title_i18n
            if _title_i18n_temp:
                item_new["title_i18n_temp"] = _title_i18n_temp
            if "items" in item_old and "items" in item_new:
                replace_form(item_old["items"], item_new["items"])
        elif isinstance(item_old, list) and isinstance(item_new, list):
            for i in item_old:
                for j in item_new:
                    if i.get("key") == j.get("key"):
                        replace_form(i, j)
                        break

def replace_item_type_data(render_old, render_new, _form_prop_old, item_key):
    try:
        _table_row_schema_old = render_old['table_row_map']['schema']["properties"][item_key] \
            if item_key in render_old['table_row_map']['schema']["properties"] else None
        _table_row_schema_new = render_new['table_row_map']['schema']["properties"][item_key] \
            if item_key in render_new['table_row_map']['schema']["properties"] else None
        _schema_old = render_old['schemaeditor']['schema'][item_key] \
            if item_key in render_old['schemaeditor']['schema'] else None
        _schema_new = render_new['schemaeditor']['schema'][item_key] \
            if item_key in render_new['schemaeditor']['schema'] else None
        _form_new = render_new['table_row_map']['form']
        _form_old = render_old['table_row_map']['form']
        replace_schema(_table_row_schema_old, _table_row_schema_new)
        replace_schema(_schema_old, _schema_new)
        for f in _form_new:
            if f.get("key") == item_key and "items" in f:
                for j in _form_old:
                    if j.get("key") == item_key and "items" in j:
                        _titleMap = j.get("titleMap")
                        _title = j.get("title")
                        _title_i18n = j.get("title_i18n")
                        _title_i18n_temp = j.get("title_i18n_temp")
                        if _title:
                            f["title"] = _title
                        if _titleMap:
                            f["titleMap"] = _titleMap
                        if _title_i18n:
                            f["title_i18n"] = _title_i18n
                        if _title_i18n_temp:
                            f["title_i18n_temp"] = _title_i18n_temp
                        replace_form(j["items"], f["items"])
                        break
    except Exception as e:
        import traceback
        current_app.logger.error(traceback.format_exc())
        current_app.logger.error(e)

def main():
    current_app.logger.setLevel(logging.INFO)
    current_app.logger.info('=============== replace_item_type_data ===============')
    try:
        _update_date = args.update_date if args else UPDATE_DATE
        sql = """
            SELECT schema,
                   form,
                   render,
                   version_id
            FROM item_type_version
            WHERE id = :item_type_id
              AND  updated < :update_date
            ORDER BY version_id DESC;
            """.strip()
        res = db.session.query(ItemType.id).all()
        current_app.logger.info('{} (update_date = {})'.format(sql.strip(), _update_date))
        current_app.logger.info('Updates to {} item types begin.'.format(len(res)))
        for _id in res:
            params = {
                "item_type_id": _id,
                "update_date": _update_date
            }
            try:
                with db.session.begin_nested():
                    item_type_new = ItemType.query.filter(ItemType.id==_id).order_by(desc(ItemType.created)).first()
                    item_type_old = db.session.execute(sql, params).first()

                    if item_type_old:
                        for _form_data_old in item_type_old.render['table_row_map']['form']:
                            _key = _form_data_old.get("key")
                            if _key and _key not in [
                                "pubdate",
                                "system_file",
                                "system_identifier_doi",
                                "system_identifier_hdl",
                                "system_identifier_uri"
                            ]:
                                multiple_old = get_multiple(item_type_old.render, _key)
                                multiple_new = get_multiple(item_type_new.render, _key)
                                if multiple_old["multiple"] is None or \
                                        multiple_new["multiple"] is None or \
                                        multiple_old["multiple"] == multiple_new["multiple"]:
                                    replace_item_type_data(item_type_old.render, item_type_new.render, _form_data_old.get("items"), _key)
                                else:
                                    _t = multiple_new["title"] if multiple_new["title"] else multiple_old["title"]
                                    current_app.logger.info('Skip element "{}" (id = {}) in item type (id = {}).'.format(_t, _key, _id.id))
                        json_schema = fix_json_schema(item_type_new.render['table_row_map']['schema'])
                        json_form = item_type_new.render['table_row_map']['form']
                        json_schema = update_required_schema_not_exist_in_form(json_schema, json_form)
                        item_type_new.schema = json_schema
                        item_type_new.form = json_form
                        flag_modified(item_type_new, "schema")
                        flag_modified(item_type_new, "form")
                        flag_modified(item_type_new, "render")
                        db.session.merge(item_type_new)
                if item_type_old:
                    db.session.commit()
                    current_app.logger.info('Updated item type (id = {}) successfully from version_id = {}.'.format(_id.id, item_type_old.version_id))
                else:
                    current_app.logger.info('The version of item type (id = {}) does not exist.'.format(_id.id))
            except SQLAlchemyError as e:
                current_app.logger.error('Failed to update item type (id = {}).'.format(_id.id))
                current_app.logger.error(e)
                db.session.rollback()
            except Exception as e:
                current_app.logger.error('Failed to update item type (id = {}).'.format(_id.id))
                current_app.logger.error(e)
                db.session.rollback()
    except Exception as ex:
        current_app.logger.error(ex)
    current_app.logger.info('=============== Finished! ===============')

if __name__ == '__main__':
    """Main context."""
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('update_date', type=str)
        args = parser.parse_args()
    except:
        args = None
    main()