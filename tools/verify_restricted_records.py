import json
import logging
import os
import sys
import traceback

from flask import current_app

from invenio_accounts.models import Role
from invenio_mail.models import MailTemplateGenres, MailTemplates
from weko_admin.models import AdminSettings
from weko_index_tree.models import Index
from weko_records.api import ItemTypeNames, ItemTypes
from weko_records.models import ItemTypeMapping, ItemTypeProperty
from weko_workflow.api import WorkFlow
from weko_workflow.models import FlowAction, FlowDefine, WorkflowRole

VERIFY_FILE_PATH = "verify_table.json"

def verify_item_type_name(expected_records):
    """Verify item_type_name records.

    Verify that the item_type_name records for restricted access
    exist and match.
    
    Args:
        expected_records (list): List of expected item_type_name records,
            each record is a dict with keys corresponding to the fields
            of item_type_name.
    
    Returns:
        int: The count of item_type_name records that match the expected records.
    """
    current_app.logger.info("Verifying item_type_name records...")

    verify_ids = [record["id"] for record in expected_records]
    actual_records = ItemTypeNames.get_all_by_id(verify_ids)
    correct_count = 0
    
    for expected in expected_records:
        actual = next((record for record in actual_records 
                       if record.id == expected["id"]), None)
        is_match = True
        if not actual:
            current_app.logger.warning(f"Record with id {expected['id']} not found.")
            continue
        
        for key in expected.keys():
            if getattr(actual, key, None) != expected[key]:
                current_app.logger.warning(f"Mismatch for id {expected['id']} on field '{key}': "
                                           f"expected '{expected[key]}', got '{getattr(actual, key, None)}'")
                is_match = False
        
        if is_match:
            current_app.logger.info(f"Record with id {expected['id']} verified successfully.")
            correct_count += 1

    return correct_count


def verify_item_type(expected_records):
    """Verify item_type records.

    Verify that the item_type records for restricted access
    exist and match.
    
    Args:
        expected_records (list): List of expected item_type records,
            each record is a dict with keys corresponding to the fields
            of item_type.
    
    Returns:
        int: The count of item_type records that match the expected records.
    """
    current_app.logger.info("Verifying item_type records...")

    verify_ids = [record["id"] for record in expected_records]
    actual_records = ItemTypes.get_records(verify_ids)
    parse_columns = ["schema", "form", "render"]
    correct_count = 0
    
    for expected in expected_records:
        actual = next((record.model for record in actual_records 
                       if record.id == expected["id"]), None)
        is_match = True
        if not actual:
            current_app.logger.warning(f"Record with id {expected['id']} not found.")
            continue
        
        for key in expected.keys():
            if key in parse_columns:
                expected_value = expected[key]
                actual_value = getattr(actual, key)
                if isinstance(actual_value, (dict, list)):
                    actual_value = json.dumps(actual_value, ensure_ascii=False).replace("'", "''")
                if actual_value != expected_value:
                    current_app.logger.warning(f"Mismatch for id {expected['id']} on field '{key}': "
                                               f"expected '{expected[key]}', got '{actual_value}'")
                    is_match = False
            else:
                if getattr(actual, key, None) != expected[key]:
                    current_app.logger.warning(f"Mismatch for id {expected['id']} on field '{key}': "
                                               f"expected '{expected[key]}', got '{getattr(actual, key, None)}'")
                    is_match = False
        
        if is_match:
            current_app.logger.info(f"Record with id {expected['id']} verified successfully.")
            correct_count += 1

    return correct_count


def verify_item_type_mapping(expected_records):
    """Verify item_type_mapping records.

    Verify that the item_type_mapping records for restricted access
    exist and match.
    
    Args:
        expected_records (list): List of expected item_type_mapping records,
            each record is a dict with keys corresponding to the fields
            of item_type_mapping.

    Returns:
        int: The count of item_type_mapping records that match the expected records.
    """
    current_app.logger.info("Verifying item_type_mapping records...")

    verify_ids = [record["id"] for record in expected_records]
    actual_records = ItemTypeMapping.query.filter(ItemTypeMapping.id.in_(verify_ids)).all()
    parse_columns = ["mapping"]
    correct_count = 0
    
    for expected in expected_records:
        actual = next((record for record in actual_records 
                       if record.id == expected["id"]), None)
        is_match = True
        if not actual:
            current_app.logger.warning(f"Record with id {expected['id']} not found.")
            continue
        
        for key in expected.keys():
            if key in parse_columns:
                expected_value = expected[key]
                actual_value = getattr(actual, key, None)
                if isinstance(actual_value, (dict, list)):
                    actual_value = json.dumps(actual_value, ensure_ascii=False).replace("'", "''")
                if actual_value != expected_value:
                    current_app.logger.warning(f"Mismatch for id {expected['id']} on field '{key}': "
                                               f"expected '{expected[key]}', got '{actual_value}'")
                    is_match = False
            else:
                if getattr(actual, key, None) != expected[key]:
                    current_app.logger.warning(f"Mismatch for id {expected['id']} on field '{key}': "
                                               f"expected '{expected[key]}', got '{getattr(actual, key, None)}'")
                    is_match = False
        
        if is_match:
            current_app.logger.info(f"Record with id {expected['id']} verified successfully.")
            correct_count += 1

    return correct_count


def verify_item_type_property(expected_records):
    """Verify item_type_property records.

    Verify that the item_type_property records for restricted access
    exist and match.
    
    Args:
        expected_records (list): List of expected item_type_property records,
            each record is a dict with keys corresponding to the fields
            of item_type_property.

    Returns:
        int: The count of item_type_property records that match the expected records.
    """
    current_app.logger.info("Verifying item_type_property records...")

    verify_ids = [record["id"] for record in expected_records]
    actual_records = ItemTypeProperty.query.filter(ItemTypeProperty.id.in_(verify_ids)).all()
    parse_columns = ["schema", "form", "forms"]
    correct_count = 0
    
    for expected in expected_records:
        actual = next((record for record in actual_records 
                       if record.id == expected["id"]), None)
        is_match = True
        if not actual:
            current_app.logger.warning(f"Record with id {expected['id']} not found.")
            continue
        
        for key in expected.keys():
            if key in parse_columns:
                expected_value = expected[key]
                actual_value = getattr(actual, key, None)
                if isinstance(actual_value, (dict, list)):
                    actual_value = json.dumps(actual_value, ensure_ascii=False).replace("'", "''")
                if actual_value != expected_value:
                    current_app.logger.warning(f"Mismatch for id {expected['id']} on field '{key}': "
                                               f"expected '{expected[key]}', got '{actual_value}'")
                    is_match = False
            else:
                if getattr(actual, key, None) != expected[key]:
                    current_app.logger.warning(f"Mismatch for id {expected['id']} on field '{key}': "
                                               f"expected '{expected[key]}', got '{getattr(actual, key, None)}'")
                    is_match = False
        
        if is_match:
            current_app.logger.info(f"Record with id {expected['id']} verified successfully.")
            correct_count += 1

    return correct_count


def verify_accounts_role(expected_records):
    """Verify accounts_role records.

    Verify that the accounts_role records for restricted access
    exist and match.
    
    Args:
        expected_records (list): List of expected accounts_role records,
            each record is a dict with keys corresponding to the fields
            of accounts_role.

    Returns:
        int: The count of accounts_role records that match the expected records.
    """
    current_app.logger.info("Verifying accounts_role records...")

    verify_names = [record["name"] for record in expected_records]
    actual_records = Role.query.filter(Role.name.in_(verify_names)).all()
    correct_count = 0

    for expected in expected_records:
        actual = next((record for record in actual_records 
                       if record.name == expected["name"]), None)
        is_match = True
        if not actual:
            current_app.logger.warning(f"Record with name {expected['name']} not found.")
            continue
        
        for key in expected.keys():
            if getattr(actual, key, None) != expected[key]:
                current_app.logger.warning(f"Mismatch for name {expected['name']} on field '{key}': "
                                           f"expected '{expected[key]}', got '{getattr(actual, key, None)}'")
                is_match = False
        
        if is_match:
            current_app.logger.info(f"Record with name {expected['name']} verified successfully.")
            correct_count += 1

    return correct_count


def verify_index(expected_records):
    """Verify index records.

    Verify that the index records for restricted access
    exist and match.
    
    Args:
        expected_records (list): List of expected index records,
            each record is a dict with keys corresponding to the fields
            of index.

    Returns:
        int: The count of index records that match the expected records.
    """
    current_app.logger.info("Verifying index records...")

    verify_ids = [record["id"] for record in expected_records]
    actual_records = Index.query.filter(Index.id.in_(verify_ids)).all()
    correct_count = 0

    general_role = Role.query.filter_by(name="General").first()
    general_id = general_role.id if general_role else 0

    for expected in expected_records:
        actual = next((record for record in actual_records 
                       if record.id == expected["id"]), None)
        is_match = True
        if not actual:
            current_app.logger.warning(f"Record with id {expected['id']} not found.")
            continue
        
        for key in expected.keys():
            expected_value = expected[key]
            if type(expected[key]) == str and "xxx" in expected[key]:
                expected_value = expected[key].replace("xxx", str(general_id))
            if getattr(actual, key, None) != expected_value:
                current_app.logger.warning(f"Mismatch for id {expected['id']} on field '{key}': "
                                           f"expected '{expected_value}', got '{getattr(actual, key, None)}'")
                is_match = False
        
        if is_match:
            current_app.logger.info(f"Record with id {expected['id']} verified successfully.")
            correct_count += 1

    return correct_count


def verify_workflow_flow_define(expected_records):
    """Verify workflow_flow_define records.

    Verify that the workflow_flow_define records for restricted access
    exist and match.
    
    Args:
        expected_records (list): List of expected workflow_flow_define records,
            each record is a dict with keys corresponding to the fields
            of workflow_flow_define.

    Returns:
        int: The count of workflow_flow_define records that match the expected records.
    """
    current_app.logger.info("Verifying workflow_flow_define records...")

    verify_ids = [record["id"] for record in expected_records]
    actual_records = FlowDefine.query.filter(FlowDefine.id.in_(verify_ids)).all()
    correct_count = 0

    for expected in expected_records:
        actual = next((record for record in actual_records 
                       if record.id == expected["id"]), None)
        is_match = True
        if not actual:
            current_app.logger.warning(f"Record with id {expected['id']} not found.")
            continue
        
        for key in expected.keys():
            actual_value = getattr(actual, key, None)
            if key == "flow_id":
                actual_value = str(actual_value)
            if actual_value != expected[key]:
                current_app.logger.warning(f"Mismatch for id {expected['id']} on field '{key}': "
                                           f"expected '{expected[key]}', got '{actual_value}'")
                is_match = False
        
        if is_match:
            current_app.logger.info(f"Record with id {expected['id']} verified successfully.")
            correct_count += 1

    return correct_count


def verify_workflow_flow_action(expected_records):
    """Verify workflow_flow_action records.

    Verify that the workflow_flow_action records for restricted access
    exist and match.
    
    Args:
        expected_records (list): List of expected workflow_flow_action records,
            each record is a dict with keys corresponding to the fields
            of workflow_flow_action.

    Returns:
        int: The count of workflow_flow_action records that match the expected records.
    """
    current_app.logger.info("Verifying workflow_flow_action records...")

    verify_ids = [record["id"] for record in expected_records]
    actual_records = FlowAction.query.filter(FlowAction.id.in_(verify_ids)).all()
    correct_count = 0

    for expected in expected_records:
        actual = next((record for record in actual_records 
                       if record.id == expected["id"]), None)
        is_match = True
        if not actual:
            current_app.logger.warning(f"Record with id {expected['id']} not found.")
            continue
        
        for key in expected.keys():
            actual_value = getattr(actual, key, None)
            if key == "flow_id":
                actual_value = str(actual_value)
            if actual_value != expected[key]:
                current_app.logger.warning(f"Mismatch for id {expected['id']} on field '{key}': "
                                           f"expected '{expected[key]}', got '{actual_value}'")
                is_match = False
        
        if is_match:
            current_app.logger.info(f"Record with id {expected['id']} verified successfully.")
            correct_count += 1

    return correct_count


def verify_workflow_workflow(expected_records):
    """Verify workflow_workflow records.

    Verify that the workflow_workflow records for restricted access
    exist and match.
    
    Args:
        expected_records (list): List of expected workflow_workflow records,
            each record is a dict with keys corresponding to the fields
            of workflow_workflow.

    Returns:
        int: The count of workflow_workflow records that match the expected records.
    """
    current_app.logger.info("Verifying workflow_workflow records...")

    verify_ids = [record["id"] for record in expected_records]
    actual_records = WorkFlow.get_workflow_by_ids(verify_ids)
    correct_count = 0

    for expected in expected_records:
        actual = next((record for record in actual_records 
                       if record.id == expected["id"]), None)
        is_match = True
        if not actual:
            current_app.logger.warning(f"Record with id {expected['id']} not found.")
            continue
        
        for key in expected.keys():
            actual_value = getattr(actual, key, None)
            if key == "flows_id":
                actual_value = str(actual_value)
            if actual_value != expected[key]:
                current_app.logger.warning(f"Mismatch for id {expected['id']} on field '{key}': "
                                           f"expected '{expected[key]}', got '{actual_value}'")
                is_match = False
        
        if is_match:
            current_app.logger.info(f"Record with id {expected['id']} verified successfully.")
            correct_count += 1

    return correct_count


def verify_workflow_userrole(expected_records):
    """Verify workflow_userrole records.

    Verify that the workflow_userrole records for restricted access
    exist and match.
    
    Args:
        expected_records (list): List of expected workflow_userrole records,
            each record is a dict with keys corresponding to the fields
            of workflow_userrole.

    Returns:
        int: The count of workflow_userrole records that match the expected records.
    """
    current_app.logger.info("Verifying workflow_userrole records...")

    verify_ids = [record["workflow_id"] for record in expected_records]
    actual_records = WorkflowRole.query.filter(WorkflowRole.workflow_id.in_(verify_ids)).all()
    correct_count = 0

    general_role = Role.query.filter_by(name="General").first()
    general_id = general_role.id if general_role else 0

    for expected in expected_records:
        expected_role_id = expected["role_id"]
        if type(expected_role_id) == str and "xxx" in expected_role_id:
            expected_role_id = int(expected_role_id.replace("xxx", str(general_id)))
        actual = next((record for record in actual_records 
                       if record.workflow_id == expected["workflow_id"] 
                       and record.role_id == expected_role_id), None)
        is_match = True
        if not actual:
            current_app.logger.warning(f"Record with workflow_id {expected['workflow_id']} "
                                       f"and role_id {expected_role_id} not found.")
            continue
        
        for key in expected.keys():
            expected_value = expected[key]
            if key == "role_id" and type(expected_value) == str and "xxx" in expected_value:
                expected_value = int(expected_value.replace("xxx", str(general_id)))
            actual_value = getattr(actual, key, None)
            if actual_value != expected_value:
                current_app.logger.warning(f"Mismatch for workflow_id {expected['workflow_id']} "
                                           f"and role_id {expected_role_id} on field '{key}': "
                                           f"expected '{expected_value}', got '{actual_value}'")
                is_match = False
        
        if is_match:
            current_app.logger.info(f"Record with workflow_id {expected['workflow_id']} "
                                    f"and role_id {expected_role_id} verified successfully.")
            correct_count += 1

    return correct_count


def verify_mail_template_genres(expected_records):
    """Verify mail_template_genres records.

    Verify that the mail_template_genres records for restricted access
    exist and match.
    
    Args:
        expected_records (list): List of expected mail_template_genres records,
            each record is a dict with keys corresponding to the fields
            of mail_template_genres.

    Returns:
        int: The count of mail_template_genres records that match the expected records.
    """
    current_app.logger.info("Verifying mail_template_genres records...")

    verify_ids = [record["id"] for record in expected_records]
    actual_records = MailTemplateGenres.query.filter(MailTemplateGenres.id.in_(verify_ids)).all()
    correct_count = 0

    for expected in expected_records:
        actual = next((record for record in actual_records 
                       if record.id == expected["id"]), None)
        is_match = True
        if not actual:
            current_app.logger.warning(f"Record with id {expected['id']} not found.")
            continue
        
        for key in expected.keys():
            if getattr(actual, key, None) != expected[key]:
                current_app.logger.warning(f"Mismatch for id {expected['id']} on field '{key}': "
                                           f"expected '{expected[key]}', got '{getattr(actual, key, None)}'")
                is_match = False
        
        if is_match:
            current_app.logger.info(f"Record with id {expected['id']} verified successfully.")
            correct_count += 1

    return correct_count


def verify_mail_templates(expected_records):
    """Verify mail_templates records.

    Verify that the mail_templates records for restricted access
    exist and match.
    
    Args:
        expected_records (list): List of expected mail_templates records,
            each record is a dict with keys corresponding to the fields
            of mail_templates.

    Returns:
        int: The count of mail_templates records that match the expected records.
    """
    current_app.logger.info("Verifying mail_templates records...")

    verify_ids = [record["id"] for record in expected_records]
    actual_records = MailTemplates.query.filter(MailTemplates.id.in_(verify_ids)).all()
    correct_count = 0

    for expected in expected_records:
        actual = next((record for record in actual_records 
                       if record.id == expected["id"]), None)
        is_match = True
        if not actual:
            current_app.logger.warning(f"Record with id {expected['id']} not found.")
            continue
        
        for key in expected.keys():
            if key == "genre_id":
                actual_value = getattr(actual, "mail_genre_id", None)
            else:
                actual_value = getattr(actual, key, None)
            if actual_value != expected[key]:
                current_app.logger.warning(f"Mismatch for id {expected['id']} on field '{key}': "
                                           f"expected '{expected[key]}', got '{actual_value}'")
                is_match = False
        
        if is_match:
            current_app.logger.info(f"Record with id {expected['id']} verified successfully.")
            correct_count += 1

    return correct_count


def verify_admin_settings(expected_records):
    """Verify admin_settings records.

    Verify that the admin_settings records for restricted access
    exist and match.
    
    Args:
        expected_records (list): List of expected admin_settings records,
            each record is a dict with keys corresponding to the fields
            of admin_settings.

    Returns:
        int: The count of admin_settings records that match the expected records.
    """
    def _verify_value(expected, actual, parent_key=""):
        """Recursively verify expected and actual values, handling nested dicts.
        
        Args:
            expected: The expected value, which can be a dict or a simple value.
            actual: The actual value to compare against the expected value.
            parent_key: The key path leading to the current value, used for logging.
            
        Returns:
            bool: True if the actual value matches the expected value, False otherwise.
        """
        if isinstance(expected, dict):
            for key in expected.keys():
                expected_value = expected[key]
                if isinstance(actual, dict):
                    actual_value = actual.get(key, None)
                else:
                    actual_value = getattr(actual, key, None)
                full_key = f"{parent_key}.{key}" if parent_key else key
                if isinstance(expected_value, dict):
                    if not _verify_value(expected_value, actual_value, full_key):
                        return False
                else:
                    if actual_value != expected_value:
                        current_app.logger.warning(f"Mismatch for name {expected_records['name']} on field '{full_key}': "
                                                   f"expected '{expected_value}', got '{actual_value}'")
                        return False
        else:
            if actual != expected:
                current_app.logger.warning(f"Mismatch for name {expected_records['name']} on field '{parent_key}': "
                                           f"expected '{expected}', got '{actual}'")
                return False
        return True

    current_app.logger.info("Verifying admin_settings records...")

    verify_name = expected_records["name"]
    actual_records = AdminSettings.get(verify_name)

    if not actual_records:
        current_app.logger.warning(f"Record with name {verify_name} not found.")
        return 0
    
    actual = actual_records
    is_match = True
    for key in expected_records["settings"].keys():
        expected_value = expected_records["settings"][key]
        actual_value = getattr(actual, key, None)
        if isinstance(expected_value, dict):
            if not _verify_value(expected_value, actual_value, key):
                is_match = False
        else:
            if actual_value != expected_value:
                current_app.logger.warning(f"Mismatch for name {verify_name} on field '{key}': "
                                           f"expected '{expected_value}', got '{actual_value}'")
                is_match = False

    if is_match:
        current_app.logger.info(f"Record with name {verify_name} verified successfully.")
        return 1
    return 0


def main():
    """Main function to verify records."""
    def _put_status_list(table_name, expected_count, actual_count):
        """Put table name into corresponding status list based on expected and actual count.
        
        Args:
            table_name (str): The name of the table being verified.
            expected_count (int): The count of expected records for the table.
            actual_count (int): The count of actual records that match the expected records.
        """
        if actual_count == 0:
            tables_none.append(table_name)
        elif actual_count < expected_count:
            tables_partial.append(table_name)
        elif actual_count == expected_count:
            tables_all.append(table_name)

    # for logging set to info level
    format = '[%(asctime)s,%(msecs)03d][%(levelname)s] \033[32mweko\033[0m - '\
            '%(message)s [file %(pathname)s line %(lineno)d in %(funcName)s]'
    datefmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter(fmt=format, datefmt=datefmt)

    current_app.logger.setLevel("INFO")
    if current_app.logger.handlers:
        # if app.logger has handlers, set level and formatter
        for h in current_app.logger.handlers:
            h.setLevel("INFO")
            h.setFormatter(formatter)

    args = sys.argv
    if len(args) == 2:
        enable_flag = args[1]
        with open(os.path.join("tools/switch_restricted_access", 
                               str(enable_flag), VERIFY_FILE_PATH), 'r') as f:
            expected_records = json.load(f)

        tables_none = []
        tables_partial = []
        tables_all = []

        # Iterate JSON keys and call corresponding verifier function named verify_<key>
        for key, records in expected_records.items():
            func_name = f"verify_{key}"
            verifier = globals().get(func_name)
            if not verifier or not callable(verifier):
                current_app.logger.warning(f"No verifier implemented for key '{key}'")
                continue
            try:
                result = verifier(records)
                # If verifier returns matched count, update status lists
                if isinstance(result, int):
                    expected_count = len(records) if isinstance(records, list) else 1
                    _put_status_list(key, expected_count, result)
            except Exception as ex:
                current_app.logger.error(str(ex))
                current_app.logger.exception(f"Error while verifying '{key}'")
                current_app.logger.error(traceback.format_exc())

        current_app.logger.info(f"Verification completed. \n"
                                f"Tables with all records correct: {tables_all}, \n"
                                f"Tables with some records correct: {tables_partial}, \n"
                                f"Tables with no records correct: {tables_none}.")


if __name__ == "__main__":
    main()
