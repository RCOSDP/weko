# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-swordserver."""

import bagit
import json
import traceback
from flask import current_app, request
from zipfile import BadZipFile

from weko_search_ui.utils import (
    handle_check_date,
    handle_check_exist_record,
    handle_check_file_metadata,
    handle_check_id,
    handle_fill_system_item,
    handle_item_title,
    handle_set_change_identifier_flag,
    handle_validate_item_import
)

from weko_records.api import ItemTypes
from weko_workflow.api import WorkFlow
from .errors import ErrorType, WekoSwordserverException
from .mapper import WekoSwordMapper
from .utils import (
    check_rocrate_required_files,
    check_swordbagit_required_files,
    get_record_by_token,
    unpack_zip,
    process_json
)


def check_import_items(file, is_change_identifier = False):
    from weko_search_ui.utils import check_import_items
    return check_import_items(file, is_change_identifier), "TSV"



def check_bagit_import_items(file, packaging):
    """Check bagit import items.

    Check that the actual file contents match the recorded hashes stored
    in the manifest files and mapping metadata to the item type.

    Args:
        file (FileStorage | str): File object or file path.
        header_info (dict):
            Request header information. It should contain "access_token".
        file_format (str): File format. "ROCRATE" or "SWORD".

    Returns:
        dict: Result of mapping to item type
        str: Registration type "Direct" or "Workflow"

        example when register_format is "Direct":
            check_result = {
                "data_path": "/tmp/xxxxx",
                "list_record": [
                    # metadata
                ]
                "register_format": "Direct",
                "item_type_id": 1,
            }


        example when register_format is "Workflow":
            check_result = {
                "data_path": "/tmp/xxxxx",
                "list_record": [
                    # metadata
                ]
                "register_format": "Workflow",
                "workflow_id": 1,
                "item_type_id": 2,
            }
    """
    check_result = {}
    if "On-Behalf-Of" in request.headers:
        # FIXME: How to handle on-behalf-of
        check_result.update({
            "On-Behalf-Of": request.headers.get("On-Behalf-Of")
        })

    if isinstance(file, str):
        filename = file.split("/")[-1]
    else:
        filename = file.filename

    try:
        # TODO: extension zip in temporary directory
        data_path, file_list = unpack_zip(file)
        check_result.update({"data_path": data_path})

        # get json file name
        json_name = (
            current_app.config['WEKO_SWORDSERVER_METADATA_FILE_SWORD']
                if packaging == "SWORDBagIt"
                else current_app.config['WEKO_SWORDSERVER_METADATA_FILE_ROCRATE']
        )

        # Check if the bag is valid
        bag = bagit.Bag(data_path)
        bag.validate()

        access_token = request.headers.get("Authorization").split("Bearer ")[1]
        sword_client, sword_mapping = get_record_by_token(access_token)
        if sword_mapping is None:
            current_app.logger.error(f"Mapping not defined for sword client.")
            raise WekoSwordserverException(
                "Metadata mapping not defined for registration your item.",
                errorType=ErrorType.MappingNotDefined
            )

        # Check workflow and item type
        register_format = sword_client.registration_type
        if register_format == "Workflow":
            # TODO: check if workflow exists
            workflow = WorkFlow.get_workflow_by_id(sword_client.workflow_id)
            if workflow is None or workflow.is_deleted:
                current_app.logger.error(f"Workflow not found for sword client.")
                raise WekoSwordserverException(
                    "Workflow not found for registration your item.",
                    errorType=ErrorType.WorkflowNotFound
                )
            # Check if workflow and item type match
            if workflow.itemtype_id != sword_mapping.item_type_id:
                current_app.logger.error(f"Item type and workflow do not match.")
                raise WekoSwordserverException(
                    "Item type and workflow do not match.",
                    errorType=ErrorType.ItemTypeNotMatched
                )

        check_result.update({"register_format": register_format})

        item_type = ItemTypes.get_by_id(sword_mapping.item_type_id)
        if item_type is None:
            current_app.logger.error(f"Item type not found for sword client.")
            raise WekoSwordserverException(
                "Item type not found for registration your item.",
                errorType=ErrorType.ItemTypeNotFound
            )
        check_result.update({"item_type_id": item_type.id})

        # TODO: validate mapping
        mapping = sword_mapping.mapping

        with open(f"{data_path}/{json_name}", "r") as f:
            json_ld = json.load(f)
        processed_json = process_json(json_ld)

        # TODO: make check_result
        list_record = generate_metadata_from_json(
            processed_json, mapping, item_type
        )
        list_record = handle_check_exist_record(list_record)
        handle_item_title(list_record)
        list_record = handle_check_date(list_record)
        handle_check_id(list_record)
        handle_check_file_metadata(list_record, data_path)

        check_result.update({"list_record": list_record})

    except WekoSwordserverException:
        raise

    except BadZipFile as ex:
        current_app.logger.error(
            "An error occurred while extraction the file."
        )
        traceback.print_exc()
        check_result.update({
            "error": f"The format of the specified file {filename} dose not "
            + "support import. Please specify a zip file."
        })

    except bagit.BagValidationError as ex:
        current_app.logger.error("Bag validation failed.")
        traceback.print_exc()
        check_result.update({
            "error": str(ex)
        })

    except (UnicodeDecodeError, UnicodeEncodeError) as ex:
        current_app.logger.error(
            "An error occurred while reading the file."
        )
        traceback.print_exc()
        check_result.update({
            "error": ex.reason
        })

    except Exception as ex:
        current_app.logger.error("An error occurred while checking the file.")
        traceback.print_exc()
        if (
            ex.args
            and len(ex.args)
            and isinstance(ex.args[0], dict)
            and ex.args[0].get("error_msg")
        ):
            check_result.update({"error": ex.args[0].get("error_msg")})
        else:
            check_result.update({"error": str(ex)})

    return check_result


# TODO: add generate_metadata function, and add read_json function
def generate_metadata_from_json(json, mapping, item_type, is_change_identifier=False):
    """Generate metadata from JSON-LD.

    Args:
        json (dict): Json data including metadata.
        mapping (dict): Mapping definition.
        item_type_id (int): ItemType ID used for registration.
        is_change_identifier (bool, optional):
            Change Identifier Mode. Defaults to False.

    Returns:
        list: list_record.
    """
    list_record = []

    mapper = WekoSwordMapper(json, item_type, mapping)
    metadata = mapper.map()

    list_record.append({
        "$schema": item_type.schema,
        "metadata": metadata,
        "item_type_name": item_type.item_type_name.name,
        "item_type_id": item_type.id,
    })
    print(f"list_record.error: {list_record[0].get('errors', 'not error occured')}")
    handle_set_change_identifier_flag(list_record, is_change_identifier)
    # FIXME: Change method below for GRDM link.
    handle_fill_system_item(list_record)
    print(f"list_record.error: {list_record[0].get('errors', 'not error occured')}")

    list_record = handle_validate_item_import(
        list_record, item_type.schema
    )

    return list_record
