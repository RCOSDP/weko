# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-swordserver."""


import traceback
from hashlib import sha256
from zipfile import ZipFile

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from invenio_accounts.models import User
from invenio_oauth2server.models import Token
from weko_accounts.models import ShibbolethUser
from weko_admin.models import AdminSettings
from weko_search_ui.config import SWORD_METADATA_FILE, ROCRATE_METADATA_FILE
from weko_search_ui.utils import (
    check_tsv_import_items,
    check_xml_import_items,
    check_jsonld_import_items
)
from weko_workflow.api import WorkFlow as WorkFlows
from weko_workflow.models import  WorkFlow

from .api import SwordClient
from .errors import ErrorType, WekoSwordserverException


def check_import_file_format(file, packaging):
    """Check inport file format.

    Args:
        file (`FileStorage`): Import file
        packaging (str): Packaging in request header

    Raises:
        WekoSwordserverException: _description_

    Returns:
        str: Import file format
    """
    with ZipFile(file, "r") as zip_ref:
        file_list =  zip_ref.namelist()
    if "SWORDBagIt" in packaging:
        if SWORD_METADATA_FILE in file_list:
            file_format = "JSON"
        else:
            current_app.logger.error(
                "metadate/sword.json is not found in SWORDBagIt."
            )
            raise WekoSwordserverException(
                "SWORDBagIt requires metadate/sword.json.",
                ErrorType.MetadataFormatNotAcceptable
                )
    elif "SimpleZip" in packaging:
        if ROCRATE_METADATA_FILE in file_list:
            file_format = "JSON"
        elif any(ROCRATE_METADATA_FILE.split("/")[1] in filename
                for filename in file_list
            ):
            raise WekoSwordserverException(
                "ro-crate-metadata.json is required in data/ directory.",
                ErrorType.MetadataFormatNotAcceptable
                )
        elif any(filename.split("/")[1].endswith(".xml")
                for filename in file_list if "/" in filename
            ):
            file_format = "XML"
        elif any(filename.split("/")[1].endswith((".tsv", ".csv"))
                for filename in file_list if "/" in filename
            ):
            file_format = "TSV/CSV"
        else:
            current_app.logger.error(
                "ro-crate-metadata.json or other metadata file is not found."
            )
            raise WekoSwordserverException(
                "SimpleZip requires ro-crate-metadata.json or other metadata file.",
                ErrorType.MetadataFormatNotAcceptable
                )
    else:
        current_app.logger.error(
            f"Not accept packaging format: {packaging}"
        )
        raise WekoSwordserverException(
            f"Not accept packaging format: {packaging}",
            ErrorType.PackagingFormatNotAcceptable
            )
    return file_format


def get_shared_id_from_on_behalf_of(on_behalf_of):
    """Get shared ID from on-behalf-of.

    Get shared ID from on-behalf-of.
    If on-behalf-of is not shared ID, return None.

    Args:
        on_behalf_of (str): On-behalf-of in request
    Returns:
        int: Shared ID
    """
    shared_id = -1
    if on_behalf_of is None:
        return shared_id

    try:
        # get weko user id from email
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
        ) from ex
    return shared_id



def is_valid_file_hash(expected_hash, file):
    """Validate body hash.

    Validate body hash by comparing to digest in request headers.
    When body hash is valid : return True.
    Else : return False.

    Args:
        digest (): Digest in request headers.
        body (): Request body.

    Returns:
        bool: Check result.
    """
    file.seek(0)
    hasher = sha256()
    for chunk in iter(lambda: file.read(4096), b""):
        hasher.update(chunk)
    body_hash = hasher.hexdigest()

    return expected_hash == body_hash


def check_import_items(file, file_format, is_change_identifier=False, **kwargs):
    """Check metadata file for import.

    Check the contents of the file and return the result of the check.

    Args:
        file (FileStorage): File object.
        file_format (str): File format. "TSV/CSV", "XML" or "JSON-LD".
        is_change_identifier (bool, optional):
            Change Identifier Mode. Defaults to False.
    Returns:
        dict: Result of the check.
    """
    settings = AdminSettings.get(
        "sword_api_setting", dict_to_object=False
    ) or {}
    settings = settings.get("data_format", {})
    register_type = (
        settings.get(file_format, {}).get("registration_type", "Direct")
    )
    check_result = {}
    check_result.update({"register_type": register_type})
    is_active = settings.get(file_format, {}).get(
        "active", file_format != "XML"
    )
    if not is_active:
        current_app.logger.error(f"{file_format} metadata import is not enabled.")
        raise WekoSwordserverException(
            f"{file_format} metadata import is not enabled.",
            ErrorType.MetadataFormatNotAcceptable
        )

    if file_format == "TSV/CSV":
        check_result.update(check_tsv_import_items(file, is_change_identifier))

        if register_type == "Workflow":
            item_type_id = check_result["list_record"][0].get("item_type_id")
            workflow = WorkFlows().get_workflow_by_item_type_id(item_type_id)
            check_result.update({"workflow_id": workflow.id})
    elif file_format == "XML":
        if register_type == "Direct":
            raise WekoSwordserverException(
                "Direct registration is not allowed for XML metadata yet.",
                ErrorType.MetadataFormatNotAcceptable
            )

        workflow_id = int(settings.get(file_format, {}).get("workflow", "-1"))
        workflow = WorkFlow.query.get(workflow_id)
        item_type_id = workflow.itemtype_id
        check_result.update(check_xml_import_items(file, item_type_id))

    elif file_format == "JSON":
        packaging = kwargs.get("packaging")
        client_id = kwargs.get("client_id")
        shared_id = kwargs.get("shared_id", -1)

        sword_client = SwordClient.get_client_by_id(client_id)
        mapping_id = sword_client.mapping_id
        # Check workflow and item type
        register_type = sword_client.registration_type
        check_result.update({"register_type": register_type})

        check_result.update({
            "register_type": register_type,
            "workflow_id": sword_client.workflow_id
        })

        check_result.update(
            check_jsonld_import_items(
                file, packaging, mapping_id, shared_id,
                is_change_identifier
            )
        )

        if register_type == "Workflow":
            workflow = WorkFlows().get_workflow_by_id(sword_client.workflow_id)
            item_type_id = check_result.get("item_type_id")
            # Check if workflow and item type match
            if workflow.itemtype_id != item_type_id:
                current_app.logger.error(
                    "Item type and workflow do not match. "
                    f"ItemType ID must be {item_type_id}, "
                    f"but the workflow's ItemType ID was {workflow.itemtype_id}.")
                raise WekoSwordserverException(
                    "Item type and workflow do not match.",
                    errorType=ErrorType.ServerError
                )
    else:
        raise WekoSwordserverException(
            f"Unsupported file format: {file_format}",
            ErrorType.MetadataFormatNotAcceptable
        )

    if register_type == "Workflow" and (workflow is None or workflow.is_deleted):
        raise WekoSwordserverException(
            "Workflow is not configured for importing xml.",
            ErrorType.ServerError
    )

    return check_result


def update_item_ids(list_record, new_id):
    """Iterate through list_record, check and update item_id.

    Args:
        list_record (list): A list containing multiple ITEMs.
        new_id (str): The new ID used to overwrite item_id.

    Returns:
        list: The updated list_record.

    Raises:
        ValueError: If list_record is not a list.
    """
    if not isinstance(list_record, list):
        raise ValueError("list_record must be a list.")

    # Create a dictionary to map identifiers to their respective items
    identifier_to_item = {}
    for item in list_record:
        if not isinstance(item, dict):
            continue

        metadata = item.get('metadata')
        if not metadata or not hasattr(metadata, 'id'):
            continue  # Skip if metadata is missing or doesn't have 'id'

        current_identifier = getattr(metadata, 'id')
        if current_identifier is not None:  # Skip if identifier is empty
            identifier_to_item[current_identifier] = item

    # Iterate through each ITEM in list_record
    for item in list_record:
        if not isinstance(item, dict):
            continue

        metadata = item.get('metadata')
        if not metadata or not hasattr(metadata, 'link_data'):
            continue  # Skip if metadata is missing or doesn't have 'link_data'

        link_data = getattr(metadata, 'link_data', [])
        if not isinstance(link_data, list):
            continue

        for link_item in link_data:
            if not isinstance(link_item, dict):
                continue

            item_id = link_item.get("item_id")
            sele_id = link_item.get("sele_id")
            if item_id in identifier_to_item and sele_id == "isSupplementedBy":
                # If a match is found, overwrite item_id with new_id
                link_item["item_id"] = new_id
                current_app.logger.info(
                    f"Updated item_id {item_id} to {new_id} "
                    f"in ITEM {item.get('identifier')}"
                )

    return list_record
