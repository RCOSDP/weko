from invenio_db import db
from weko_records.api import ItemTypes
import traceback

def main():
    try:
        
        itemtypes = ItemTypes.get_all()
        for itemtype in itemtypes:
            ret = ItemTypes.reload(itemtype.id)
            print("itemtype id:{}, itemtype name:{}".format(itemtype.id,itemtype.item_type_name.name))
        db.session.commit()
    except Exception as e:
        print(traceback.format_exc())
        db.session.rollback()

        

if __name__ == '__main__':
    main()