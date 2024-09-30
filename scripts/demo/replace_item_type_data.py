from weko_records.models import ItemType
from weko_itemtypes_ui.utils import fix_json_schema, update_required_schema_not_exist_in_form
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.attributes import flag_modified
from invenio_db import db
from flask import current_app

UPDATE_DATE = '2024/9/30'


def replace_schema(schema_old, schema_new):
    _required = []

    if schema_old and schema_old.get("enum") and \
            isinstance(schema_new, dict):
        schema_new["enum"] = schema_old.get("enum")
    if schema_old and schema_old.get("currentEnum") and \
            isinstance(schema_new, dict):
        schema_new["currentEnum"] = schema_old.get("currentEnum")
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
    
        

def replace_form(form_old, form_new):
    if form_old and form_new:
        for i in form_old:
            _k = i.get("key")
            _option = {
                "required": i.get("required", False),
                "isShowList": i.get("isShowList", False),
                "isSpecifyNewline": i.get("isSpecifyNewline", False),
                "isHide": i.get("isHide", False),
                "isNonDisplay": i.get("isNonDisplay", False),
            }
            _titleMap = i.get("titleMap")
            for j in form_new:
                if j.get("key") == _k:
                    for k, v in _option.items():
                        j[k] = v
                    if _titleMap:
                        j["titleMap"] = _titleMap
                    if "items" in form_old and "items" in form_new:
                        replace_form(form_old["items"], form_new["items"])
                    break


def replace_item_type_data(render_old, render_new, _form_prop_old, item_key):
    _table_row_schema_old = render_old['table_row_map']['schema']["properties"][item_key] \
        if item_key in render_old['table_row_map']['schema']["properties"] else None
    _table_row_schema_new = render_new['table_row_map']['schema']["properties"][item_key] \
        if item_key in render_new['table_row_map']['schema']["properties"] else None
    _schema_old = render_old['schemaeditor']['schema'][item_key] \
        if item_key in render_old['schemaeditor']['schema'] else None
    _schema_new = render_new['schemaeditor']['schema'][item_key] \
        if item_key in render_new['schemaeditor']['schema'] else None
    _form_new = render_new['table_row_map']['form']
    replace_schema(_table_row_schema_old, _table_row_schema_new)
    replace_schema(_schema_old, _schema_new)
    for f in _form_new:
        if f.get("key") == item_key and "items" in f:
            _form_prop_new = f["items"]
            break
    replace_form(_form_prop_old, _form_prop_new)

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
              AND  updated < :update_date
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

                    for _form_data_old in item_type_old.render['table_row_map']['form']:
                        _key = _form_data_old.get("key")
                        if _key and _key not in [
                            "pubdate",
                            "system_file",
                            "system_identifier_doi",
                            "system_identifier_hdl",
                            "system_identifier_uri"
                        ]:
                            replace_item_type_data(item_type_old.render, item_type_new.render, _form_data_old.get("items"), _key)
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