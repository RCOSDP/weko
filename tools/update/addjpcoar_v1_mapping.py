from weko_records.models import ItemTypeMapping
from weko_records.api import Mapping
from sqlalchemy.sql import func
from invenio_db import db
import pickle

def main():
    res = db.session.query(ItemTypeMapping.id).all()
    for _id in list(res):
        with db.session.begin_nested():
            item_type = ItemTypeMapping.query.filter(ItemTypeMapping.id==_id).first()
            mapping =  pickle.loads(pickle.dumps(item_type.mapping,-1))
            for key in list(mapping.keys()):
                if 'jpcoar_mapping' in mapping[key]:
                    mapping[key]['jpcoar_v1_mapping']=mapping[key]['jpcoar_mapping']
            item_type.mapping = mapping
        db.session.commit()

if __name__ == '__main__':
    """Main context."""
    main()