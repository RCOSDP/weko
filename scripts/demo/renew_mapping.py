from invenio_db import db
from weko_records.api import ItemTypes
from properties import property_config
import properties

import traceback
import argparse

def main():
    try:
        _renew_type = args.renew_type if args else ''
        mapping_list = args.mapping_list if args else ["oai_dc_mapping","jpcoar_v1_mapping","jpcoar_mapping"]
        specified_list = property_config.SPECIFIED_LIST if _renew_type == 'only_specified' else []
        itemtypes = ItemTypes.get_all()
        prop_mapping = properties_mapping()
        print("Process property id list:{}".format(specified_list))
        print("Process mapping list:{}".format(mapping_list))
        for itemtype in itemtypes:
            if _renew_type == 'only_specified':
                ret = ItemTypes.reset_itemtype_mapping(itemtype.id, specified_list, prop_mapping, mapping_list)
            print("itemtype id:{}, itemtype name:{}".format(itemtype.id,itemtype.item_type_name.name))
            print(ret['msg'])
        db.session.commit()
    except Exception as e:
        print(traceback.format_exc())
        db.session.rollback()


def properties_mapping():
    prop_mapping = dict()
    for i in dir(properties):
        prop = getattr(properties, i)
        if getattr(prop, 'property_id', None) and prop.property_id:
            prop_mapping[str(prop.property_id)] = prop.mapping
    return prop_mapping
        

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('renew_type', action='store')
        parser.add_argument('mapping_list', action='store',nargs="*",type=str,default=[])
        args = parser.parse_args()
    except:
        args = None
    main()