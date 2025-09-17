import sys
import traceback

from flask import current_app
from invenio_db import db
from properties import property_config
from register_properties import del_properties, get_properties_id, register_properties_from_folder
from tools import updateRestrictedRecords

from weko_records.api import ItemTypes


def main(restricted_item_type_id):
    try:
        current_app.logger.info("run updateRestrictedRecords")
        updateRestrictedRecords.main(restricted_item_type_id)
        current_app.logger.info("run register_properties_only_specified")
        register_properties_only_specified()
        current_app.logger.info("run renew_all_item_types")
        renew_all_item_types()
    except Exception as ex:
        current_app.logger.error(ex)
        db.session.rollback()


def register_properties_only_specified():
    exclusion_list = [int(x) for x in property_config.EXCLUSION_LIST]
    try:
        specified_list = property_config.SPECIFIED_LIST
        del_properties(specified_list)
        exclusion_list += get_properties_id()
        register_properties_from_folder(exclusion_list, specified_list)
        db.session.commit()
    except:
        current_app.logger.error(traceback.format_exc())
        db.session.rollback()


def renew_all_item_types():
    try:
        itemtypes = ItemTypes.get_all()
        for itemtype in itemtypes:
            ret = ItemTypes.reload(itemtype.id)
            current_app.logger.info("itemtype id:{}, itemtype name:{}".format(itemtype.id,itemtype.item_type_name.name))
            current_app.logger.info(ret['msg'])
        db.session.commit()
    except:
        current_app.logger.error(traceback.format_exc())
        db.session.rollback()


if __name__ == "__main__":
    args = sys.argv
    if len(args) > 1:
        restricted_item_type_id = int(args[1])
        main(restricted_item_type_id)
    else:
        print("Please provide restricted_item_type_id as an argument.")
        sys.exit(1)
