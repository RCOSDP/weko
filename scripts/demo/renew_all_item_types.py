from invenio_db import db
from weko_records.api import ItemTypes
from properties import property_config

import traceback
import argparse

def main(args=None):
    try:
        _renew_type = args.renew_type if args else ''
        _renew_value = args.renew_value if args else 'None'
        specified_list = property_config.SPECIFIED_LIST if _renew_type == 'only_specified' else []
        itemtypes = ItemTypes.get_all()
        print("Process property id list:{}".format(specified_list))
        for itemtype in itemtypes:
            if _renew_type == 'only_specified':
                ret = ItemTypes.reload(itemtype.id, specified_list, _renew_value)
            else:
                ret = ItemTypes.reload(itemtype.id)
            print("itemtype id:{}, itemtype name:{}".format(itemtype.id,itemtype.item_type_name.name))
            print(ret['msg'])
        db.session.commit()
        # db.session.rollback()
    except Exception as e:
        print(traceback.format_exc())
        db.session.rollback()

        

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('renew_type', action='store')
        parser.add_argument('renew_value', action='store')
        args = parser.parse_args()
    except:
        args = None
    main(args)