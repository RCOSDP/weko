from weko_records.models import ItemTypeMapping
from weko_records.api import Mapping
from sqlalchemy.sql import func
from sqlalchemy import desc
from invenio_db import db
import pickle

def main():
    try:
        res = db.session.query(ItemTypeMapping.id).all()
        for _id in list(res):
            with db.session.begin_nested():
                item_type = ItemTypeMapping.query.filter(ItemTypeMapping.id==_id).order_by(desc(ItemTypeMapping.created)).first()
                mapping =  pickle.loads(pickle.dumps(item_type.mapping,-1))
                for key in list(mapping.keys()):
                    if 'jpcoar_mapping' in mapping[key] and mapping[key]['jpcoar_mapping'] is not "":
                        mapping[key]['jpcoar_v1_mapping']=mapping[key]['jpcoar_mapping']
                item_type.mapping = mapping
        db.session.commit()
    except Exception as ex:
        print(ex)
        db.session.rollback()

if __name__ == '__main__':
    """Main context."""
    main()