import traceback
from invenio_db import db
from weko_records.api import ItemTypes

def main():
    try:
        print("Add 'peer_reviewed' to version_type property. (id = 1016)")
        query = """
            UPDATE item_type_property 
            SET schema = schema || jsonb_set(schema, '{"properties","subitem_peer_reviewed"}', '{"editAble": true,"type": ["null", "string"],"format": "select","enum": [null, "Peer reviewed", "Not peer reviewed"],"currentEnum": ["Peer reviewed", "Not peer reviewed"],"title": "査読の有無","title_i18n": {"en": "Peer reviewed/Not peer reviewed", "ja": "査読の有無"}}'),
            form = form || jsonb_set(form, '{"items",2}', '{"key": "parentkey.subitem_peer_reviewed","type": "select","title": "査読の有無","title_i18n": {"en": "Peer reviewed/Not peer reviewed","ja": "査読の有無"},"titleMap": [{"name": "Peer reviewed","value": "Peer reviewed","name_i18n": {"en": "Peer reviewed","ja": "査読あり"}},{"name": "Not peer reviewed","value": "Not peer reviewed","name_i18n": {"en": "Not peer reviewed","ja": "査読なし"}}]}'),
            forms = forms || jsonb_set(forms, '{"items",2}', '{"key": "parentkey[].subitem_peer_reviewed","type": "select","title": "査読の有無","title_i18n": {"en": "Peer reviewed/Not peer reviewed","ja": "査読の有無"},"titleMap": [{"name": "Peer reviewed","value": "Peer reviewed","name_i18n": {"en": "Peer reviewed","ja": "査読あり"}},{"name": "Not peer reviewed","value": "Not peer reviewed","name_i18n": {"en": "Not peer reviewed","ja": "査読なし"}}]}')
            WHERE id = 1016;
        """
        db.session.execute(query)
        db.session.flush()
        print("  Successfully added 'peer_reviewed' to version_type property. (id = 1016)")

        import properties
        mapping = {}
        for i in dir(properties):
            prop = getattr(properties, i)
            if getattr(prop, 'property_id', None) and prop.property_id == 1016:
                mapping[int(prop.property_id)] = prop.mapping
        print("Reload all itemtypes")
        itemtypes = ItemTypes.get_all()
        for itemtype in itemtypes:
                ret = ItemTypes.reload(itemtype.id, mapping)
                print(f"  itemtype id:{itemtype.id}, itemtype name:{itemtype.item_type_name.name}")
                print(f"  {ret['msg']}")
        
        db.session.commit()
        print("  Successfully reloaded all itemtypes")

        print("Completed!")
    except Exception as e:
        print(traceback.format_exc())
        db.session.rollback()
        print("Failed to update itemtype property.")

if __name__ == "__main__":
    main()