import argparse
import item_types
import sys
from base_item_type import base_data
from item_types import item_type_config

from invenio_db import db
from weko_itemtypes_ui.utils import fix_json_schema, update_required_schema_not_exist_in_form
from weko_records.api import ItemTypes, Mapping
from weko_records.models import ItemType, ItemTypeName, ItemTypeMapping


def main():
    try:
        exclusion_list = [int(x) for x in item_type_config.EXCLUSION_LIST]
        type_list = ['overwrite_all', 'only_add_new', 'only_specified']
        # Read parameters.
        parser = argparse.ArgumentParser()
        parser.add_argument('reg_type', action='store')
        try:
            args = parser.parse_args()
        except BaseException:
            print('Please input parameter of register type.')
            print('List of valid parameters [{}].'.format(','.join(type_list)))
            sys.exit(0)
        if args.reg_type == 'overwrite_all':
            truncate_table()
            register_item_types_from_folder(exclusion_list)
            update_harvesting_types()
            db.session.commit()
        elif args.reg_type == 'only_add_new':
            exclusion_list += get_item_type_id()
            register_item_types_from_folder(exclusion_list)
            update_harvesting_types()
            db.session.commit()
        elif args.reg_type == 'only_specified':
            specified_list = item_type_config.SPECIFIED_LIST
            exclusion_list += get_item_type_id()
            register_item_types_from_folder(exclusion_list, specified_list, True)
            update_harvesting_types()
            db.session.commit()
        else: 
            print('Please input parameter of register type.')
            print('List of valid parameters [{}].'.format(','.join(type_list)))
            sys.exit(0) 
    except Exception as ex:
        print(ex)


def truncate_table():
    db.session.execute('TRUNCATE item_type, item_type_name, item_type_mapping CASCADE;')
    db.session.commit()


def get_item_type_id():
    item_types = db.session.query(ItemType.id).all()
    return [x.id for x in item_types]


def register_item_types_from_folder(exclusion_list, specified_list=[], update_flag=False):
    reg_list = []
    for i in dir(item_types):
        item_type_def = getattr(item_types, i)
        if getattr(item_type_def, 'item_type_id', None) and item_type_def.item_type_id:
            item_type_id = int(item_type_def.item_type_id)
            if (item_type_id not in exclusion_list) \
                    or (item_type_id in specified_list):                
                item_type = base_data()
                for idx, property in enumerate(item_type_def.property_list):
                    property.add_func(
                        post_data=item_type,
                        key='item_{}'.format(item_type_id).zfill(6) + str(idx).zfill(2),
                        title=property.property_title,
                        title_ja=property.property_title_ja,
                        title_en=property.property_title_en,
                        option=property.option,
                        mapping=property.mapping
                    )
                json_schema = fix_json_schema(item_type['table_row_map']['schema'])
                json_form = item_type['table_row_map']['form']
                json_schema = update_required_schema_not_exist_in_form(json_schema, json_form)
                if update_flag:
                    record = ItemTypes.update(
                        id_=item_type_id,
                        name=item_type_def.item_type_name,
                        schema=json_schema,
                        form=json_form,
                        render=item_type
                    )
                else:
                    db.session.execute("SELECT setval('item_type_id_seq', {}, false)".format(item_type_id))
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

                reg_list.append(item_type_id)

    db.session.execute("SELECT setval('item_type_id_seq', 40000, true);")

    reg_list.sort()
    print('Processed id list: ', reg_list)


def update_harvesting_types():
    """Update harvesting item type flag."""
    if item_type_config.HARVESTING_ITEM_TYPE_LIST:
        harvesting_str = ','.join([str(x) for x in item_type_config.HARVESTING_ITEM_TYPE_LIST])
        query = "UPDATE item_type SET harvesting_type = true WHERE id in ({});".format(
            harvesting_str)
        db.session.execute(query)


if __name__ == '__main__':
    main()