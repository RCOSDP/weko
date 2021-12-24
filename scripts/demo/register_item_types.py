import argparse
import item_types
from base_item_type import base_data

from invenio_db import db
from weko_itemtypes_ui.utils import fix_json_schema, update_required_schema_not_exist_in_form
from weko_records.api import ItemTypes, Mapping


def main():
    # Read parameters.
    #parser = argparse.ArgumentParser()
    #parser.add_argument('--add_only', action='store_true')
    #args = parser.parse_args()

    #if not args.add_only:
    #    delete_properties()
    register_item_types_from_folder()
    db.session.commit()


#def delete_properties():

def register_item_types_from_folder():
    for i in dir(item_types):
        item_type_def = getattr(item_types, i)
        if getattr(item_type_def, 'item_type_id', None) and item_type_def.item_type_id:
            item_type_id = int(item_type_def.item_type_id)
            db.session.execute("SELECT setval('item_type_id_seq', {}, false)".format(item_type_id))
            
            item_type = base_data()
            for idx, property in enumerate(item_type_def.property_list):
                property.add_func(
                    post_data=item_type,
                    key='item_{}'.format(item_type_id).zfill(6) + str(idx).zfill(2),
                    title=property.property_title,
                    title_ja=property.property_title_ja,
                    title_en=property.property_title_en,
                    option=property.option
                )
            json_schema = fix_json_schema(item_type['table_row_map']['schema'])
            json_form = item_type['table_row_map']['form']
            json_schema = update_required_schema_not_exist_in_form(json_schema, json_form)
            record = ItemTypes.create(
                name=item_type_def.item_type_name,
                schema=json_schema,
                form=json_form,
                render=item_type
            )

            Mapping.create(
                item_type_id=record.model.id,
                mapping=item_type['table_row_map']['mapping']
            )

    db.session.execute("SELECT setval('item_type_id_seq', 40000, true);")



if __name__ == '__main__':
    main()