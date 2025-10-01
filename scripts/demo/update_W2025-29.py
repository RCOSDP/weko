import sys
import time
import traceback

from flask import current_app
from invenio_db import db
from properties import property_config
from register_properties import del_properties, get_properties_id, register_properties_from_folder
from tools import updateRestrictedRecords, update_weko_links

from invenio_files_rest.models import (
    timestamp_before_update as ifr_timestamp_before_update,
    Timestamp as ifr_Timestamp
)
from invenio_mail.models import (
    timestamp_before_update as im_timestamp_before_update,
    Timestamp as im_Timestamp
)
from invenio_records.models import (
    timestamp_before_update as ir_timestamp_before_update,
    Timestamp as ir_Timestamp
)
from weko_records.api import ItemTypes
from weko_records.models import (
    timestamp_before_update as weko_timestamp_before_update,
    Timestamp as Weko_Timestamp,
)

from scripts.demo import update_feedback_mail_list_to_db

def main(restricted_item_type_id, start_time):
    try:
        current_app.logger.info("run updateRestrictedRecords")
        updateRestrictedRecords.main(restricted_item_type_id)
        current_time = show_exec_time(start_time, "update_restricted_records")
        current_app.logger.info("run register_properties_only_specified")
        register_properties_only_specified()
        current_time = show_exec_time(current_time, "register_properties_only_specified")
        current_app.logger.info("run renew_all_item_types")
        renew_all_item_types()
        current_time = show_exec_time(current_time, "renew_all_item_types")
        current_app.logger.info("run update_weko_links")
        update_weko_links.main()
        current_time = show_exec_time(current_time, "update_weko_links")
        current_app.logger.info("run update_feedback_mail_list_to_db")
        update_feedback_mail_list_to_db.main()
        current_time = show_exec_time(current_time, "update_feedback_mail_list_to_db")
        current_app.logger.info("All updates completed successfully.")
    except Exception as ex:
        current_app.logger.error(ex)
        traceback.print_exc()
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


def show_exec_time(start_time, process_name):
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    current_app.logger.info(
        f"{process_name} elapsed time: {elapsed_time:.2f} seconds"
    )
    return end_time


if __name__ == "__main__":
    # Log start time
    current_app.logger.info("Start update_W2025-29.py")
    start_time = time.perf_counter()

    args = sys.argv
    db.event.remove(ifr_Timestamp, 'before_update', ifr_timestamp_before_update)
    db.event.remove(im_Timestamp, 'before_update', im_timestamp_before_update)
    db.event.remove(ir_Timestamp, 'before_update', ir_timestamp_before_update)
    db.event.remove(Weko_Timestamp, 'before_update', weko_timestamp_before_update)
    try:
        if len(args) > 1:
            restricted_item_type_id = int(args[1])
            main(restricted_item_type_id, start_time)
        else:
            print("Please provide restricted_item_type_id as an argument.")
            sys.exit(1)
    finally:
        db.event.listen(
            ifr_Timestamp, "before_update",
            ifr_timestamp_before_update, propagate=True
        )
        db.event.listen(
            im_Timestamp, "before_update",
            im_timestamp_before_update, propagate=True
        )
        db.event.listen(
            ir_Timestamp, "before_update",
            ir_timestamp_before_update, propagate=True
        )
        db.event.listen(
            Weko_Timestamp, "before_update",
            weko_timestamp_before_update, propagate=True
        )

    # Log end time
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    current_app.logger.info(
        f"End update_W2025-29.py, elapsed time: {elapsed_time:.2f} seconds"
    )
