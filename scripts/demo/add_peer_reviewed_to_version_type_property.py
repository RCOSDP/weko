import traceback
from invenio_db import db
from weko_records.api import ItemTypes
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
        itemtypes = ItemTypes.get_all()
        for itemtype in itemtypes:
                ret = ItemTypes.reload(itemtype.id, mapping)
                current_app.logger.info(f"  itemtype id:{itemtype.id}, itemtype name:{itemtype.item_type_name.name}")
                current_app.logger.info(f"  {ret['msg']}")
        
        db.session.commit()
        for itemtype in itemtypes:
            current_app.logger.info(f"[FIX] item_type:{itemtype.id}")
        current_app.logger.info("  Successfully reloaded all itemtypes")

        current_app.logger.info("Completed!")
    except Exception as e:
        current_app.logger.error(traceback.format_exc())
        db.session.rollback()
        current_app.logger.error("Failed to update itemtype property.")

if __name__ == "__main__":
    main()