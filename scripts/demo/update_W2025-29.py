import sys

from invenio_db import db
from properties import property_config
from register_properties import del_properties, get_properties_id, register_properties_from_folder
from tools import updateRestrictedRecords
import renew_all_item_types

def main(restricted_item_type_id):
    print("run updateRestrictedRecords")
    updateRestrictedRecords.main(restricted_item_type_id)
    print("run register_properties_only_specified")
    register_properties_only_specified()
    print("run renew_all_item_types")
    renew_all_item_types.main()


def register_properties_only_specified():
    exclusion_list = [int(x) for x in property_config.EXCLUSION_LIST]
    try:
        specified_list = property_config.SPECIFIED_LIST
        del_properties(specified_list)
        exclusion_list += get_properties_id()
        register_properties_from_folder(exclusion_list, specified_list)
        db.session.commit()
    except Exception as ex:
        print(ex)
        db.session.rollback()


if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1:
        restricted_item_type_id = int(args[1])
        main()
    else:
        print("Please provide restricted_item_type_id as an argument.")
        sys.exit(1)
