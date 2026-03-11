import traceback
from invenio_db import db
from weko_records.api import ItemTypes
from weko_records.models import ItemType
from flask import current_app
def main():
    try:
        current_app.logger.info("Add 'peer_reviewed' to version_type property. (id = 1016)")
        query = """
            UPDATE item_type_property 
            SET schema = schema || jsonb_set(schema, '{"properties","subitem_peer_reviewed"}', '{"editAble": true,"type": ["null", "string"],"format": "select","enum": [null, "Peer reviewed", "Not peer reviewed"],"currentEnum": ["Peer reviewed", "Not peer reviewed"],"title": "査読の有無","title_i18n": {"en": "Peer reviewed/Not peer reviewed", "ja": "査読の有無"}}'),
            form = form || jsonb_set(form, '{"items",2}', '{"key": "parentkey.subitem_peer_reviewed","type": "select","title": "査読の有無","title_i18n": {"en": "Peer reviewed/Not peer reviewed","ja": "査読の有無"},"titleMap": [{"name": "Peer reviewed","value": "Peer reviewed","name_i18n": {"en": "Peer reviewed","ja": "査読あり"}},{"name": "Not peer reviewed","value": "Not peer reviewed","name_i18n": {"en": "Not peer reviewed","ja": "査読なし"}}]}'),
            forms = forms || jsonb_set(forms, '{"items",2}', '{"key": "parentkey[].subitem_peer_reviewed","type": "select","title": "査読の有無","title_i18n": {"en": "Peer reviewed/Not peer reviewed","ja": "査読の有無"},"titleMap": [{"name": "Peer reviewed","value": "Peer reviewed","name_i18n": {"en": "Peer reviewed","ja": "査読あり"}},{"name": "Not peer reviewed","value": "Not peer reviewed","name_i18n": {"en": "Not peer reviewed","ja": "査読なし"}}]}')
            WHERE id = 1016;
        """
        db.session.execute(query)
        db.session.flush()
        current_app.logger.info("  Successfully added 'peer_reviewed' to version_type property. (id = 1016)")

        import properties
        mapping = {}
        for i in dir(properties):
            prop = getattr(properties, i)
            if getattr(prop, 'property_id', None) and prop.property_id == 1016:
                mapping[int(prop.property_id)] = prop.mapping

        current_app.logger.info("Reload all itemtypes")
        fix_ids = []
        query = db.session.query(ItemType.id).statement
        results = db.engine.execution_options(stream_results=True).execute(query)
        item_type_ids = [r[0] for r in results]

        for itemtype_id in item_type_ids:
            ret = ItemTypes.reload(itemtype_id, mapping)
            if ret.get("code") != 0:
                current_app.logger.error("Failed to renew item_type_id:{}".format(itemtype_id))
                current_app.logger.error(ret.get("msg"))
                continue
            current_app.logger.info(f"  itemtype id:{itemtype_id}")
            current_app.logger.info(f"  {ret['msg']}")
            is_fix_mapping = False
            if "mapping" in ret.get("msg",""):
                is_fix_mapping = True
            else:
                is_fix_mapping = False
            fix_ids.append((itemtype_id, is_fix_mapping))
        
        db.session.commit()
        for (itemtype_id, is_fix_mapping) in fix_ids:
            current_app.logger.info(f"[FIX] item_type:{itemtype_id}")
            if is_fix_mapping:
                current_app.logger.info(f"[FIX] item_type_mapping:{itemtype_id}(item_type_id)")
        current_app.logger.info("  Successfully reloaded all itemtypes")

        current_app.logger.info("Completed!")
    except Exception as e:
        current_app.logger.error(traceback.format_exc())
        db.session.rollback()
        current_app.logger.error("Failed to update itemtype property.")

if __name__ == "__main__":
    main()