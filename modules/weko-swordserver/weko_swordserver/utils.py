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
from sqlalchemy.orm.exc import NoResultFound

from invenio_accounts.models import User
from invenio_oauth2server.models import Token
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidstore.resolver import Resolver

from weko_accounts.models import ShibbolethUser
from weko_admin.models import AdminSettings
from weko_deposit.api import WekoDeposit

from weko_items_ui.utils import check_item_is_being_edit
from weko_records_ui.utils import soft_delete
from weko_search_ui.config import SWORD_METADATA_FILE, ROCRATE_METADATA_FILE
from weko_search_ui.utils import (
    check_tsv_import_items,
    check_xml_import_items,
    check_jsonld_import_items
)
from weko_workflow.api import WorkFlow as WorkFlows, WorkActivity
from weko_workflow.utils import check_an_item_is_locked

from .api import SwordClient
from .errors import ErrorType, WekoSwordserverException


def check_import_file_format(file, packaging):
    """Check inport file format.

    Args:
        file (`FileStorage`): Import file
        packaging (str): Packaging in request header

    Raises:
        WekoSwordserverException:
            - If packaging format is not SWORDBagIt or SimpleZip
            - If metadata file is not found in SWORDBagIt
            - If metadata file is not found in SimpleZip
            - If packaging format is SimpleZip but sword.json is found
            - If packaging format is SimpleZip but ro-crate-metadata.json is not found
            - If packaging format is SimpleZip but other metadata file is not found
            - If packaging format is not accept

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
        elif SWORD_METADATA_FILE in file_list:
            current_app.logger.error(
                "packaging format is SimpleZip, but sword.json is found."
            )
            raise WekoSwordserverException(
                "packaging format is SimpleZip, but sword.json is found.",
                ErrorType.MetadataFormatNotAcceptable
                )
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
                "Metadata file is not found in SimpleZip."
            )
            raise WekoSwordserverException(
                "SimpleZip requires ro-crate-metadata.json or other metadata file.",
                ErrorType.ContentMalformed
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
        int: Shared user ID

    Raises:
        WekoSwordserverException:
            - If no user found by On-Behalf-Of.
            - If an error occurs while searching user by On-Behalf-Of.
    """
    shared_id = -1
    if on_behalf_of is None:
        return shared_id

    try:
        # get weko user id from email
        user = User.query.filter_by(email=on_behalf_of).one_or_none()
        shared_id = int(user.id) if user is not None else None
        if shared_id is None:
            # get weko user id from personal access token
            token = (
                Token.query
                .filter_by(access_token=on_behalf_of).one_or_none()
            )
            shared_id = int(token.user_id) if token is not None else None
        if shared_id is None:
            # get weko user id from shibboleth user eppn
            shib_user = (
                ShibbolethUser.query
                .filter_by(shib_eppn=on_behalf_of).one()
            )
            shared_id = int(shib_user.weko_uid)
    except NoResultFound as ex:
        msg = "No user found by On-Behalf-Of."
        current_app.logger.error(msg)
        traceback.print_exc()
        raise WekoSwordserverException(
            msg, errorType=ErrorType.BadRequest
        ) from ex
    except SQLAlchemyError as ex:
        current_app.logger.error(
            "DB error occurred while searching user by On-Behalf-Of."
        )
        traceback.print_exc()
        raise WekoSwordserverException(
            "Failed to get shared ID from On-Behalf-Of.",
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
    if not isinstance(expected_hash, str):
        return False

    file.seek(0)
    hasher = sha256()
    for chunk in iter(lambda: file.read(4096), b""):
        hasher.update(chunk)
    body_hash = hasher.hexdigest()

    return expected_hash == body_hash


def check_import_items(
    file, file_format, is_change_identifier=False, shared_id=-1, **kwargs
):
    """Check metadata file for import.

    Check the contents of the file and return the result of the check.

    Args:
        file (FileStorage): File object.
        file_format (str): File format. "TSV/CSV", "XML" or "JSON-LD".
        is_change_identifier (bool, optional):
            Change Identifier Mode. Defaults to False.
        shared_id (int, optional): Contributor ID. Defaults to -1.
        **kwargs: Additional arguments.
            - client_id (str): Client ID.
            - packaging (str): Packaging type.
    Returns:
        dict: Result of the check.
    """
    sword_settings = AdminSettings.get("sword_api_setting", False) or {}
    current_setting = sword_settings.get(file_format) or {}

    is_active = current_setting.get("active", file_format != "XML")
    if not is_active:
        current_app.logger.error(f"{file_format} metadata import is not enabled.")
        raise WekoSwordserverException(
            f"{file_format} metadata import is not enabled.",
            ErrorType.MetadataFormatNotAcceptable
        )

    registration_type = current_setting.get("registration_type") or "Direct"
    duplicate_check = current_setting.get("duplicate_check") or False

    check_result = {
        "list_record": [],
        "register_type": registration_type,
        "duplicate_check": duplicate_check,
    }

    if file_format == "TSV/CSV":
        check_result.update(
            check_tsv_import_items(file, is_change_identifier, shared_id=shared_id)
        )

        if registration_type == "Workflow":
            item_type_id = check_result["list_record"][0].get("item_type_id")
            item_type_name = check_result["list_record"][0].get("item_type_name")

            list_workflow = WorkFlows().get_workflow_by_itemtype_id(item_type_id)
            if not list_workflow:
                current_app.logger.error(
                    f"Workflow not found for item type ID: {item_type_name}"
                )
                error = check_result.get("error", "")
                error_ = "Workflow not found for item type ID."
                error += f"; {error_}" if error else error_
                check_result.update({"error": error})
            else:
                list_workflow = WorkFlows().reduce_workflows_for_registration(list_workflow)
                if not list_workflow:
                    current_app.logger.error(
                        f"No workflow found for item registration."
                    )
                    error = check_result.get("error", "")
                    error_ = "No workflow found for item type ID."
                    error += f"; {error_}" if error else error_
                    check_result.update({"error": error})
                else:
                    workflow = list_workflow[0]
                    workflow_id = workflow.id
                    check_result.update({"workflow_id": workflow_id})

    elif file_format == "XML":
        if registration_type == "Direct":
            raise WekoSwordserverException(
                "Direct registration is not allowed for XML metadata yet.",
                ErrorType.MetadataFormatNotAcceptable
            )

        workflow_id = int(current_setting.get("workflow", "-1"))
        workflow = WorkFlows().get_workflow_by_id(workflow_id)

        if workflow is None or workflow.is_deleted:
            current_app.logger.error(
                f"Workflow not found. Workflow ID: {workflow_id}"
            )
            raise WekoSwordserverException(
                "Workflow not found for registration your item.",
                errorType=ErrorType.BadRequest
            )

        if not WorkFlows().reduce_workflows_for_registration([workflow]):
            current_app.logger.error(
                f"Workflow is not for item registration: {workflow_id}"
            )
            raise WekoSwordserverException(
                "Workflow is not for item registration.",
                errorType=ErrorType.BadRequest
            )

        item_type_id = workflow.itemtype_id
        check_result.update(
            check_xml_import_items(file, item_type_id, shared_id=shared_id)
        )
        check_result.update({"workflow_id": workflow_id})

    elif file_format == "JSON":
        packaging = kwargs.get("packaging")
        client_id = kwargs.get("client_id")

        sword_client = SwordClient.get_client_by_id(client_id)
        if sword_client is None or not sword_client.active:
            current_app.logger.error(
                f"No SWORD API setting foound for client ID: {client_id}"
            )
            raise WekoSwordserverException(
                "No SWORD API setting found for client ID that you are using.",
                errorType=ErrorType.BadRequest
            )
        mapping_id = sword_client.mapping_id
        workflow_id = sword_client.workflow_id
        meta_data_api = sword_client.meta_data_api
        # Check workflow and item type
        registration_type = sword_client.registration_type
        check_result.update({"register_type": registration_type})

        check_result.update({
            "register_type": registration_type,
            "workflow_id": workflow_id,
            "duplicate_check": sword_client.duplicate_check,
        })

        workflow = None
        if registration_type == "Workflow":
            workflow = WorkFlows().get_workflow_by_id(workflow_id)
            if workflow is None or workflow.is_deleted:
                current_app.logger.error(
                    f"Workflow not found for client ID: {client_id}"
                )
                raise WekoSwordserverException(
                    "Workflow not found for registration your item.",
                    errorType=ErrorType.BadRequest
                )

            if not WorkFlows().reduce_workflows_for_registration([workflow]):
                current_app.logger.error(
                    f"Workflow is not for item registration: {workflow_id}"
                )
                raise WekoSwordserverException(
                    "Workflow is not for item registration.",
                    errorType=ErrorType.BadRequest
                )

        validate_bagit = current_app.config["WEKO_SWORDSERVER_BAGIT_VERIFICATION"]
        check_result.update(
            check_jsonld_import_items(
                file, packaging, mapping_id, meta_data_api, shared_id,
                validate_bagit=validate_bagit,
                is_change_identifier=is_change_identifier
            )
        )

        item_type_id = check_result.get("item_type_id")
        # Check if workflow and item type match
        if (
            registration_type == "Workflow"
            and workflow.itemtype_id != item_type_id
        ):
            current_app.logger.error(
                "Item type and workflow do not match. "
                f"ItemType ID must be {item_type_id}, "
                f"but the workflow's ItemType ID was {workflow.itemtype_id}.")
            error = check_result.get("error", "")
            error += "; Item type and workflow do not match."
            check_result.update({"error": error})
    else:
        raise WekoSwordserverException(
            f"Unsupported file format: {file_format}",
            ErrorType.MetadataFormatNotAcceptable
        )

    return check_result


def update_item_ids(list_record, new_id, old_id):
    """Iterate through list_record, check and update item_id.

    Args:
        list_record (list): A list containing multiple ITEMs.
        new_id (str): The new ID used to overwrite item_id.
        old_id (str): old (not number) ID of new_id.

    Returns:
        list: The updated list_record.

    Raises:
        ValueError: If list_record is not a list.
    """
    # Iterate through each ITEM in list_record
    for item in list_record:
        metadata = item.get("metadata")
        if not metadata or not item.get("link_data"):
            continue  # Skip if metadata is missing or doesn't have "link_data"
        link_data = item.get("link_data")

        for link_item in link_data:
            if not isinstance(link_item, dict):
                continue

            if link_item.get("item_id") == old_id:
                # If a match is found, overwrite item_id with new_id
                link_item["item_id"] = new_id
                current_app.logger.info(
                    f"Updated item_id {old_id} to {new_id} "
                    f"in ITEM {item.get('_id')}"
                )

    return list_record


def check_deletion_type(client_id):
    """Check deletion type.

    Check deletion type for item deletion from client_id.

    Args:
        client_id (str): Client ID.

    Returns:
        dict: check result.
            - deletion_type (str): Deletion type. "Direct" or "Workflow".
            - workflow_id (int): Workflow ID if deletion_type is "Workflow".
            - delete_flow_id (int): Delete flow ID if deletion_type is "Workflow".

    Raises:
        WekoSwordserverException:
            - If no SWORD API setting found for client ID.
            - If workflow not found for registration item.
            - If invalid registration type.
    """
    sword_client = SwordClient.get_client_by_id(client_id)
    if sword_client is None:
        current_app.logger.error(
            f"No SWORD API setting foound for client ID: {client_id}"
        )
        raise WekoSwordserverException(
            "No SWORD API setting found for client ID that you are using.",
            errorType=ErrorType.BadRequest
        )

    result = {}
    register_type = sword_client.registration_type
    if register_type == "Workflow":
        workflow = WorkFlows().get_workflow_by_id(sword_client.workflow_id)
        if workflow is None or workflow.is_deleted:
            current_app.logger.error(
                f"Workflow not found. Workflow ID: {sword_client.workflow_id}"
            )
            raise WekoSwordserverException(
                "Workflow not found for registration your item.",
                errorType=ErrorType.BadRequest
            )

        # Check if workflow has delete_flow_id
        delete_flow_id = workflow.delete_flow_id
        deletion_type = "Workflow" if delete_flow_id else "Direct"
        result["deletion_type"] = deletion_type
        if deletion_type == "Workflow":
            result["workflow_id"] = sword_client.workflow_id
            result["delete_flow_id"] = delete_flow_id

    elif register_type == "Direct":
        result["deletion_type"] = "Direct"

    else:
        current_app.logger.error(
            f"Invalid registration type: {register_type}"
        )
        raise WekoSwordserverException(
            f"Invalid registration type: {register_type}",
            errorType=ErrorType.ServerError
        )
    return result


def delete_item_directly(recid, request_info=None):
    """Delete item directly.

    Delete item directly by recid.

    Args:
        recid (str): Record ID.
        request_info (dict, optional): Request information. Defaults to None.

    Raises:
        WekoSwordserverException:
            - If item is in import progress.
            - If item is being edited.
    """
    resolver = Resolver(
        pid_type="recid", object_type="rec",
        getter=WekoDeposit.get_record
    )
    pid, record = resolver.resolve(recid)

    if not record:
        current_app.logger.error(f"Record not found: {recid}.")
        raise WekoSwordserverException(
            "Record not found.",
            errorType=ErrorType.NotFound
        )

    work_activity = WorkActivity()
    latest_pid = PIDVersioning(child=pid).last_child

    # Check Record is in import progress
    if check_an_item_is_locked(recid):
        current_app.logger.error(f"Item is in import progress: {recid}.")
        raise WekoSwordserverException(
            "Item cannot be deleted because it is in import progress.",
            errorType=ErrorType.BadRequest
        )

    item_uuid = latest_pid.object_uuid
    latest_activity = work_activity.get_workflow_activity_by_item_id(item_uuid)
    if check_item_is_being_edit(pid, latest_activity, work_activity):
        current_app.logger.error(f"Item is being edited: {recid}.")
        raise WekoSwordserverException(
            "Item cannot be deleted because it is being edited.",
            errorType=ErrorType.BadRequest
        )

    soft_delete(recid)
