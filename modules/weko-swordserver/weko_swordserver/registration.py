# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-swordserver."""

import os
import shutil
import bagit
import json
import traceback
from flask import current_app, request
from zipfile import BadZipFile
from sqlalchemy.exc import SQLAlchemyError

from invenio_accounts.models import User
from invenio_oauth2server.models import Token

from weko_accounts.models import ShibbolethUser
from weko_search_ui.utils import (
    handle_check_and_prepare_index_tree,
    handle_check_and_prepare_publish_status,
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
    get_record_by_client_id,
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
        packaging (str): Packaging type. SWORDBagIt or SimpleZip.

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

    shared_id = None
    try:
        # parse On-Behalf-Of
        if "On-Behalf-Of" in request.headers:
            # get weko user id from email
            on_behalf_of = request.headers.get("On-Behalf-Of")
            user = User.query.filter_by(email=on_behalf_of).one_or_none()
            shared_id = user.id if user is not None else None
            if shared_id is None:
                # get weko user id from personal access token
                token = (
                    Token.query
                    .filter_by(access_token=on_behalf_of).one_or_none()
                )
                shared_id = token.user_id if token is not None else None
            if shared_id is None:
                # get weko user id from shibboleth user eppn
                shib_user = (
                    ShibbolethUser.query
                    .filter_by(shib_eppn=on_behalf_of).one_or_none()
                )
                shared_id = shib_user.weko_uid if shib_user is not None else None
    except SQLAlchemyError as ex:
        current_app.logger.error(
            "Somthing went wrong while searching user by On-Behalf-Of.")
        traceback.print_exc()
        raise WekoSwordserverException(
            "An error occurred while searching user by On-Behalf-Of.",
            errorType=ErrorType.ServerError
        )

    if isinstance(file, str):
        filename = os.path.basename(file)
    else:
        filename = file.filename

    try:
        data_path, files_list = unpack_zip(file)
        check_result.update({"data_path": data_path})

        # metadata json file name
        json_name = (
            current_app.config['WEKO_SWORDSERVER_METADATA_FILE_SWORD']
                if "SWORDBagIt" in packaging
                else current_app.config['WEKO_SWORDSERVER_METADATA_FILE_ROCRATE']
        )

        # Check if the bag is valid
        bag = bagit.Bag(data_path)
        bag.validate()

        client_id = request.oauth.client.client_id
        sword_client, sword_mapping = get_record_by_client_id(client_id)
        if sword_mapping is None:
            current_app.logger.error(f"Mapping not defined for sword client.")
            raise WekoSwordserverException(
                "Metadata mapping not defined for registration your item.",
                errorType=ErrorType.ServerError
            )

        # Check workflow and item type
        register_format = sword_client.registration_type
        if register_format == "Workflow":
            workflow = WorkFlow().get_workflow_by_id(sword_client.workflow_id)
            if workflow is None or workflow.is_deleted:
                current_app.logger.error(f"Workflow not found for sword client.")
                raise WekoSwordserverException(
                    "Workflow not found for registration your item.",
                    errorType=ErrorType.ServerError
                )
            # Check if workflow and item type match
            if workflow.itemtype_id != sword_mapping.item_type_id:
                current_app.logger.error(
                    "Item type and workflow do not match. "
                    f"ItemType ID must be {sword_mapping.item_type_id}, "
                    f"but the workflow's ItemType ID was {workflow.itemtype_id}.")
                raise WekoSwordserverException(
                    "Item type and workflow do not match.",
                    errorType=ErrorType.ServerError
                )

        check_result.update({"register_format": register_format})

        item_type = ItemTypes.get_by_id(sword_mapping.item_type_id)
        if item_type is None:
            current_app.logger.error(f"Item type not found for sword client.")
            raise WekoSwordserverException(
                "Item type not found for registration your item.",
                errorType=ErrorType.ServerError
            )
        check_result.update({"item_type_id": item_type.id})

        # TODO: validate mapping
        mapping = sword_mapping.mapping

        with open(f"{data_path}/{json_name}", "r") as f:
            json_ld = json.load(f)

        processed_json = process_json(json_ld)
        # FIXME: if workflow registration, check if the indextree is valid
        indextree = processed_json.get("record").get("header").get("indextree")

        list_record = generate_metadata_from_json(
            processed_json, mapping, item_type
        )
        list_record = handle_check_exist_record(list_record)
        handle_item_title(list_record)
        list_record = handle_check_date(list_record)
        handle_check_id(list_record)
        handle_check_and_prepare_index_tree(list_record, True, [])
        handle_check_and_prepare_publish_status(list_record)
        handle_check_file_metadata(list_record, data_path)

        # add zip file to temporary dictionary
        if current_app.config.get("WEKO_SWORDSERVER_DEPOSIT_DATASET"):
            if isinstance(file, str):
                shutil.copy(file, os.path.join(data_path, "data", filename))
            else:
                file.seek(0, 0)
                file.save(os.path.join(data_path, "data", filename))
            files_list.append(f"data/{filename}")

        handle_files_info(list_record, files_list, data_path, filename)

        # add on-behalf-of user id to metadata
        if shared_id is not None:
            list_record[0].get("metadata").update({"weko_shared_id": shared_id})

        check_result.update({"list_record": list_record})

    except WekoSwordserverException as ex:
        check_result.update({
            "error": ex.message
        })

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
        "$schema": f"/items/jsonschema/{item_type.id}",
        "metadata": metadata,
        "item_type_name": item_type.item_type_name.name,
        "item_type_id": item_type.id,
        "publish_status": metadata.pop("publish_status"),
    })
    handle_set_change_identifier_flag(list_record, is_change_identifier)
    handle_fill_system_item(list_record)

    list_record = handle_validate_item_import(
        list_record, item_type.schema
    )

    return list_record

def handle_files_info(list_record, files_list, data_path, filename):
    """ Handle files_info in metadata.

    Handle metadata for Direct registration and Workflow registration.
    pick up files infomation from metadata and add it to files_info.

    Args:
        list_record (list): List of metadata.
        files_list (list): List of files in the zip file.
        data_path (str): Path to the temporary directory.
        filename (str): Name of the zip file.

    Returns:
        list: list_record with files_info.
    """
    # for Direct registration handling
    target_files_list = []
    for file in files_list:
        if file.startswith("data/") and file != "data/":
            target_files_list.append(file.split("data/")[1])
    if target_files_list:
        list_record[0].update({"file_path":target_files_list})

    metadata = list_record[0].get("metadata")
    files_info = metadata.get("files_info")  # for Workflow registration
    key = files_info[0].get("key")
    file_metadata = metadata.get(key)  # for Direct registration

    # add dataset zip file's info to files_info if dataset will be deposited.
    if current_app.config.get("WEKO_SWORDSERVER_DEPOSIT_DATASET"):
        dataset_info = {
            "filesize": [
                {
                    "value": str(os.path.getsize(os.path.join(data_path, "data", filename))),
                }
            ],
            "filename":  filename,
            "format": "application/zip",
            "url": {
                "url": "",
                "objectType": "fulltext",
                "label": f"data/{filename}"
            },
        }
        files_info[0].get("items").append(dataset_info)
        file_metadata.append(dataset_info)

    return list_record
