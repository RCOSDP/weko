import argparse
import properties

from invenio_db import db
from weko_records.models import ItemTypeProperty


def main():
    # Read parameters.
    #parser = argparse.ArgumentParser()
    #parser.add_argument('--add_only', action='store_true')
    #args = parser.parse_args()

    #if not args.add_only:
    #    delete_properties()
    register_properties_from_folder()
    db.session.commit()


#def delete_properties():

def register_properties_from_folder():
    prop_list = list()
    for i in dir(properties):
        prop = getattr(properties, i)
        if getattr(prop, 'property_id', None) and prop.property_id:
            prop_id = int(prop.property_id)
            prop_list.append(dict(
                id=prop_id,
                name=prop.name_ja,
                schema=prop.schema(multi_flag=False),
                form=prop.form(multi_flag=False),
                forms=prop.form(multi_flag=True),
                delflg=False
            ))
    db.session.execute(ItemTypeProperty.__table__.insert(), prop_list)
    db.session.execute("SELECT setval('item_type_property_id_seq', 10000, true);")



if __name__ == '__main__':
    main()