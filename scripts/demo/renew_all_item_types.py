from invenio_db import db
from weko_records.api import ItemTypes
import traceback

def main():
    try:
        
        itemtypes = ItemTypes.get_all()
        for itemtype in itemtypes:
            ret = ItemTypes.renew(itemtype.id)
    except Exception as e:
        print(traceback.format_exc())
        db.session.rollback()

        
    except Exception as e:
        print(traceback.format_exc())
        db.session.rollback()    

        

if __name__ == '__main__':
    main()