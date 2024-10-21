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
from flask import current_app
from zipfile import BadZipFile

from weko_records.api import ItemTypes
from weko_workflow.api import WorkFlow
from .errors import ErrorType, WekoSwordserverException
from .utils import (
    check_rocrate_required_files,
    check_swordbagit_required_files,
    get_record_by_token,
    unpack_zip)


def check_import_items(file, is_change_identifier = False):
    pass



def check_bagit_import_items(file, header_info, file_format):
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
                ]
                "register_format": "Direct",
                "item_type_id": 1,
            }


        example when register_format is "Workflow":
            check_result = {
                "data_path": "/tmp/xxxxx",
                "list_record": [
                ]
                "register_format": "Workflow",
                "workflow_id": 1,
                "item_type_id": 2,
            }



    """
    check_result = {}

    if isinstance(file, str):
        filename = file.split("/")[-1]
    else:
        filename = file.filename

    try:
        # TODO: extension zip in tmporary directory
        data_path, file_list = unpack_zip(file)
        check_result.update({"data_path": data_path})

        # Check if all required files are contained
        if file_format == 'ROCRATE':
            all_file_contained = all(check_rocrate_required_files(file_list))
        elif file_format == 'SWORD':
            all_file_contained = all(check_swordbagit_required_files(file_list))

        if not all_file_contained:
            raise WekoSwordserverException(
                'Metadata JSON File Or "manifest-sha256.txt" Is Lacking',
                errorType=ErrorType.BadRequest)

        # Check if the bag is valid
        bag = bagit.Bag(data_path)
        bag.validate()

        sword_client, sword_mapping = get_record_by_token(header_info["access_token"])
        if sword_mapping is None:
            current_app.logger.error(f"Mapping not defined for sword client.")
            raise WekoSwordserverException(
                "Metadata mapping not defined for registration your item.",
                errorType=ErrorType.MappingNotDefined
            )

        # Check workflow and item type
        register_format = sword_mapping.registration_type
        if register_format == "Workflow":
            # TODO: check workflow
            workflow = WorkFlow.get_workflow_by_id(sword_client.workflow_id)
            if workflow is None:
                current_app.logger.error(f"Workflow not found for sword client.")
                raise WekoSwordserverException(
                    "Workflow not found for registration your item.",
                    errorType=ErrorType.WorkflowNotFound
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
        item_type_name = item_type.item_type_name

        # TODO: validate mapping
        mapping = json.loads(sword_mapping.mapping)

        # TODO: make check_result

    except WekoSwordserverException:
        raise

    except BadZipFile as ex:
        current_app.logger.error(
            "An error occured while extraction the file."
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
            "error": "Bag validation failed. Please check your bag."
        })

    except (UnicodeDecodeError, UnicodeEncodeError) as ex:
        current_app.logger.error(
            "An error occured while reading the file."
        )
        traceback.print_exc()
        check_result.update({
            "error": ex.reason
        })

    except Exception as ex:
        current_app.logger.error("An error occured while checking the file.")
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
