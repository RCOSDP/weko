from weko_records.models import ItemTypeMapping
from invenio_db import db
import pickle

def main():
    with db.session.begin_nested():
        res = db.session.query(ItemTypeMapping).all()
        for item_type in res:
            mapping = pickle.loads(pickle.dumps(item_type.mapping,-1))
            for key in mapping.keys():
                prop=mapping[key]
                if 'jpcoar_mapping' in prop:
                    prop['jpcoar_v1_mapping']=pickle.loads(pickle.dumps(prop['jpcoar_mapping'],-1))
            item_type.mapping=mapping
    db.session.commit()

if __name__ == '__main__':
    """Main context."""
    main()