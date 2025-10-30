import json
import sys
import traceback

from flask import current_app

from invenio_db import db
from weko_records.api import ItemTypes
from weko_records.models import ItemType, ItemTypeName, ItemTypeProperty

def main(target_item_type_property_id, update_type):
    """Update restricted access property and item types.
    
    Args:
        target_item_type_property_id (int): The ID of the target item type property to update.
        update_type (str): The type of update to perform, either "enable" or "disable".
    """
    try:
        with db.session.begin_nested():
            update_item_type_property(target_item_type_property_id, update_type)
            update_item_type()
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        current_app.logger.error(str(ex))
        current_app.logger.error("Failed to update restricted access property.")
        current_app.logger.error(traceback.format_exc())

def update_item_type_property(target_item_type_property_id, update_type):
    """Update the schema, form, and forms of a specific item type property.
    
    Args:
        target_item_type_property_id (int): The ID of the target item type property to update.
        update_type (str): The type of update to perform, either "enable" or "disable".
    """
    target_property = ItemTypeProperty.query.filter_by(id=target_item_type_property_id).one_or_none()
    if target_property:
        with open(f"tools/switch_restricted_access/{update_type}/schema.json", "r") as schema_file:
            target_property.schema = json.load(schema_file)
        with open(f"tools/switch_restricted_access/{update_type}/form.json", "r") as form_file:
            target_property.form = json.load(form_file)
        with open(f"tools/switch_restricted_access/{update_type}/forms.json", "r") as forms_file:
            target_property.forms = json.load(forms_file)
    else:
        current_app.logger.error(f"id: {target_item_type_property_id} not found")
    
    current_app.logger.info("Update item_type_property record successfully.")

def update_item_type():
    """Reload item types that contain the restricted access property."""
    def _check_restricted_item_type(item_type):
        """Check if the item type contains the restricted access property.
        
        Args:
            item_type (ItemType): The item type to check.
        Returns:
            bool: True if the item type contains the restricted access property, False otherwise.
        """
        target_nested_props = ["filename", "provide", "terms", "termsDescription"]
        props = item_type.schema.get("properties", {})
        for _, value in props.items():
            if value.get("type") != "array" or value["items"].get("type") != "object":
                continue
            nested_props = value["items"].get("properties", {})
            if all([prop in nested_props.keys() for prop in target_nested_props]):
                return True
        return False

    # get all item_type ids which is not deleted
    query = db.session.query(ItemType.id).filter(
        ItemType.is_deleted.is_(False)
    ).order_by(ItemType.name_id, ItemType.tag).statement
    results = db.engine.execution_options(stream_results=True).execute(query)
    item_type_ids = [r[0] for r in results]
    current_app.logger.info("target item_type count: " + str(len(item_type_ids)))

    # reload all item_type
    for item_type_id in item_type_ids:
        item_type = ItemType.query.get(item_type_id)
        if not _check_restricted_item_type(item_type):
            continue
        
        ret = ItemTypes.reload(item_type_id, renew_value='ALL')
        item_type_name = ItemTypeName.query.get(item_type_id)
        current_app.logger.info("itemtype id:{}, itemtype name:{}".format(item_type_id,item_type_name.name))
        current_app.logger.info(ret['msg'])
    
    current_app.logger.info("Update item_type records successfully.")

if __name__ == '__main__':
    args = sys.argv
    if len(args) == 3:
        target_item_type_property_id = int(args[1])
        update_type = args[2]
        main(target_item_type_property_id, update_type)
