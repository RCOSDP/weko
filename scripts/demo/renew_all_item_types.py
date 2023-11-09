from invenio_db import db
from weko_records.api import ItemTypes
import traceback

def main():
    try:
        with db.session.begin_nested():
            itemtypes = ItemTypes.get_all()
            for itemtype in itemtypes:
                ItemTypes.renew(itemtype.id)
        db.session.commit()
    except Exception as e:
        print(traceback.format_exc())
        db.session.rollback()

if __name__ == '__main__':
    main()