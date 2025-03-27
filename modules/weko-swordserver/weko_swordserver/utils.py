# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-swordserver."""

import os
import tempfile
import traceback
from copy import deepcopy
from datetime import datetime, timezone
from dateutil import parser
from hashlib import sha256
from zipfile import ZipFile

from flask import current_app, request
from sqlalchemy.exc import SQLAlchemyError

from weko_admin.models import AdminSettings
from invenio_accounts.models import User
from invenio_oauth2server.models import Token
from weko_accounts.models import ShibbolethUser
from weko_search_ui.utils import (
    check_tsv_import_items,
    check_xml_import_items,
    #check_jsonld_import_items
)
from weko_workflow.api import WorkActivity, WorkFlow as WorkFlows
from weko_workflow.headless import HeadlessActivity
from weko_workflow.models import ActionStatusPolicy, WorkFlow
from weko_records.api import ItemTypes, ItemsMetadata
from invenio_pidstore.models import PersistentIdentifier

from .api import SwordClient, SwordItemTypeMapping
from .errors import WekoSwordserverException, ErrorType


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
        if "metadata/sword.json" in file_list:
            file_format = "JSON"
        else:
            current_app.logger.error(
                "SWORDBagIt requires metadate/sword.json."
            )
            raise WekoSwordserverException(
                "SWORDBagIt requires metadate/sword.json.",
                ErrorType.MetadataFormatNotAcceptable
                )
    elif "SimpleZip" in packaging:
        if "ro-crate-metadata.json" in file_list:
            file_format = "JSON"
        else:
            file_format = "OTHERS"
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


def unpack_zip(file):
    """Unpack zip file.

    Unpack zip file and return extracted files information.

    Args:
        file (FileStorage | str): Zip file object or file path.

    Returns:
        tuple (str, list[str]):
        data_path: Path of extracted files, file_list: List of extracted files.

    """
    data_path = os.path.join(
        tempfile.gettempdir(),
        current_app.config.get("WEKO_SEARCH_UI_IMPORT_TMP_PREFIX")
            + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")[:-3]
    )

    # Create temp dir for import data
    os.mkdir(data_path)

    # Extract zip file, Extracted files remain.
    with ZipFile(file) as zip_ref:
        file_list = []
        for info in zip_ref.infolist():
            try:
                info.filename = (
                    info.orig_filename.encode("cp437").decode("cp932"))
                # replace backslash to slash
                if os.sep != "/" and os.sep in info.filename:
                    info.filename = info.filename.replace(os.sep, "/")
                file_list.append(info.filename)
            except Exception:
                traceback.print_exc()
                raise
        zip_ref.extractall(path=data_path)

    return data_path, file_list


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


def get_record_by_client_id(client_id):
    """
    Get the SwordClient and SwordItemTypeMapping records associated with client ID.

    Args:
        client_id (str): The ID of the client to get the settings records for.

    Returns:
        tuple (SwordClientModel, SwordItemTypeMappingModel):
            A tuple containing the SwordClient object and the SwordItemTypeMapping
            object. If the client or mapping is not found, the corresponding
            value in the tuple will be None.
    """
    sword_client = SwordClient.get_client_by_id(client_id)

    mapping_id = sword_client.mapping_id if sword_client is not None else None
    sword_mapping = SwordItemTypeMapping.get_mapping_by_id(mapping_id)

    return sword_client, sword_mapping


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


def process_json(json_ld):
    """Process json-ld.

    Process RO-Crate metadata json-ld data.
    Pick up necessary data from @graph and resolve links
    in order to map to WEKO item type.

    Args:
        json_ld (dict): Json-ld data.

    Returns:
        dict: Processed json data.
    """
    json = deepcopy(json_ld)

    # transform list which contains @id to dict in @graph
    if "@graph" in json and isinstance(json["@graph"], list):
        new_value = {}
        for v in json["@graph"]:
            if isinstance(v, dict) and "@id" in v:
                new_value[v["@id"]] = v
            else:
                current_app.logger.error("Invalid json-ld format.")
                raise WekoSwordserverException(
                    "Invalid json-ld format.",
                    ErrorType.MetadataFormatNotAcceptable
                )
        json["@graph"] = new_value
    # TODO: support SWORD json-ld format
    else:
        current_app.logger.error("Invalid json-ld format.")
        raise WekoSwordserverException(
            "Invalid json-ld format.",
            ErrorType.MetadataFormatNotAcceptable
        )
    # Remove unnecessary keys
    json = json.get("@graph")

    def _resolve_link(parent, key, value):
        if isinstance(value, dict):
            if len(value) == 1 and "@id" in value and value["@id"] in json:
                parent[key] = json[value["@id"]]
            else:
                for k, v in value.items():
                    _resolve_link(value, k, v)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                _resolve_link(value, i, v)

    for key, value in json.items():
        _resolve_link(json, key, value)

    # replace Dataset identifier
    id = current_app.config["WEKO_SWORDSERVER_DATASET_ROOT"].get("")
    enc = current_app.config["WEKO_SWORDSERVER_DATASET_ROOT"].get("enc")
    json.update({enc: json.pop(id)})

    # prepare json for mapper format
    json = {
        "record": {
            "header": {
                "identifier": json.get(enc).get("name"),
                "datestamp": (
                    parser.parse(json.get(enc).pop("datePublished"))
                    .strftime('%Y-%m-%d')
                ),
                "publish_status": json.get(enc).pop("accessMode"),
                "indextree": (
                    int(json.get(enc).get("isPartOf").pop("sameAs", "/").split("/")[-1])
                        if "sameAs" in json.get(enc).get("isPartOf")
                        else None
                )
            },
            "metadata": json
        }
    }

    return json


def delete_items_with_activity(item_id, request_info):
    activity = WorkActivity()

    workflow = activity.get_workflow_activity_by_item_id(item_id)
    if workflow is None:
        workflows = WorkFlows()
        """get_workflow_activity_by_item_idで取得できなかったときにすること

        from invenio_pidstore.models import PersistentIdentifier から itemidからobjectuuidを取得

        ItemsMetadataでobjectuuidからitemtypeを取得

        itemtypeでworkflow_idを取得"""
        pid = PersistentIdentifier.query.filter_by(pid_value=item_id).one_or_none()
        if pid is None:
            raise WekoSwordserverException(
                f"Item ID {item_id} not found.",
                ErrorType.NotFound
            )
        object_uuid = pid.object_uuid

        item_metadata = ItemsMetadata.get_by_object_id(object_uuid)
        if item_metadata is None:
            raise WekoSwordserverException(
                f"Item metadata not found for item ID {item_id}.",
                ErrorType.NotFound
            )
        item_type_id = item_metadata.item_type_id

        workflow = workflows.get_workflow_by_itemtype_id(item_type_id)
        if workflow is None:
            raise WekoSwordserverException(
                f"Workflow not found for item ID {item_id}.",
                ErrorType.NotFound
            )

    workflow_id = workflow.id
    user_id=request_info.get("user_id")
    community_id=request_info.get("community_id")

    try:
        headless = HeadlessActivity()
        url = headless.init_activity(
            user_id=user_id, workflow_id=workflow_id, community_id=community_id,
            item_id=item_id, for_delete=True
        )
        # headless.delete(item_id)

    except Exception as ex:
        traceback.print_exc()
        raise WekoSwordserverException(
            f"An error occurred while {headless.current_action}.",
            ErrorType.ServerError
        ) from ex

    return url


def get_register_format():
    """Get register format and validate SWORD client.

    Returns:
        dict: A dictionary containing register_format, workflow_id, and item_type_id.

    Raises:
        WekoSwordserverException: If any validation fails.
    """
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
    workflow = None
    delete_flow_id = None
    if register_format == "Workflow":
        workflow = WorkFlows().get_workflow_by_id(sword_client.workflow_id)
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
        
        # Check if workflow has delete_flow_id
        delete_flow_id = WorkFlow.query.filter_by(id=sword_client.workflow_id).one_or_none().delete_flow_id

    item_type = ItemTypes.get_by_id(sword_mapping.item_type_id)
    if item_type is None:
        current_app.logger.error(f"Item type not found for sword client.")
        raise WekoSwordserverException(
            "Item type not found for registration your item.",
            errorType=ErrorType.ServerError
        )

    return {
        "register_format": register_format,
        "workflow_id": sword_client.workflow_id,
        "delete_flow_id": delete_flow_id,
        "item_type_id": item_type.id
    }
