import properties
import sys
import time
from properties import property_config
from sqlalchemy.dialects.postgresql import Insert
from invenio_db import db
from weko_records.models import ItemTypeProperty
from register_properties import main as register_properties_main
from update_itemtype_full import main as update_itemtype_full_main
from update_item_type import main as update_item_type_main
from addjpcoar_v2_mapping import main as addjpcoar_v2_mapping_main
from renew_all_item_types import main as renew_all_item_types_main

def main():
    print("run register_properties")
    register_properties_main()
    print("run update_itemtype_full")
    update_itemtype_full_main()
    print("run update_item_type")
    update_item_type_main()
    print("run addjpcoar_v2_mapping")
    addjpcoar_v2_mapping_main()
    time.sleep(2)
    print("run renew_all_item_types")
    renew_all_item_types_main()

if __name__ == "__main__":
    main()