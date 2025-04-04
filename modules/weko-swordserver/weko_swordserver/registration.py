# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-swordserver."""

import os
import uuid
import json
import shutil
import traceback
import bagit
from zipfile import BadZipFile
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app, request, url_for, abort

from invenio_accounts.models import User
from invenio_db import db
from invenio_deposit.scopes import actions_scope
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.utils import _location_has_quota
from invenio_indexer.api import RecordIndexer
from invenio_oauth2server.models import Token
from invenio_pidstore import current_pidstore

from weko_accounts.models import ShibbolethUser
from weko_admin.models import AdminSettings
from weko_deposit.api import WekoDeposit
from weko_deposit.serializer import file_uploaded_owner
from weko_search_ui.utils import (
    check_tsv_import_items,
    check_xml_import_items,
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
from weko_workflow.api import WorkActivity, WorkFlow as WorkFlows
from weko_workflow.models import ActionStatusPolicy, WorkFlow
from weko_workflow.headless import HeadlessActivity


from weko_records.api import ItemTypes
from .errors import ErrorType, WekoSwordserverException
from .mapper import WekoSwordMapper
from .utils import (
    get_record_by_client_id,
    unpack_zip,
    process_json
)


def check_import_items(file, is_change_identifier: bool = False):
    settings = AdminSettings.get("sword_api_setting", dict_to_object=False)
    default_format = settings.get("default_format")
    data_format = settings.get("data_format")
    if default_format == "TSV":
        check_tsv_result = check_tsv_import_items(file, is_change_identifier)
        if check_tsv_result.get("error"):
            # try xml
            workflow_id = int(data_format.get("XML", {}).get("workflow", "-1"))
            workflow = WorkFlow.query.get(workflow_id)
            if not workflow or workflow.is_deleted:
                raise WekoSwordserverException("Workflow is not configured for importing xml.", ErrorType.ServerError)
            item_type_id = workflow.itemtype_id
            check_xml_result = check_xml_import_items(
                file, item_type_id, is_gakuninrdm=False
            )
            if check_xml_result.get("error"):
                return check_tsv_result, None
            else:
                return check_xml_result, "XML"
        else:
            return check_tsv_result, "TSV/CSV"
    elif default_format == "XML":
        workflow_id = int(data_format.get("XML", {}).get("workflow", "-1"))
        workflow = WorkFlow.query.get(workflow_id)
        if not workflow or workflow.is_deleted:
            raise WekoSwordserverException("Workflow is not configured for importing xml.", ErrorType.ServerError)
        item_type_id = workflow.itemtype_id
        check_xml_result = check_xml_import_items(
            file, item_type_id, is_gakuninrdm=False
        )
        if check_xml_result.get("error"):
            # try tsv
            check_tsv_result = check_tsv_import_items(file, is_change_identifier)
            if check_tsv_result.get("error"):
                return check_xml_result, None
            else:
                return check_tsv_result, "TSV/CSV"
        else:
            return check_xml_result, "XML"

    return {}, None


def import_items_to_activity(item, data_path, request_info):
    workflow_id = request_info.get("workflow_id")
    # when metadata format was XML, get id from admin setting
    if workflow_id is None:
        settings = AdminSettings.get("sword_api_setting", dict_to_object=False)
        default_format = settings.get("default_format", "XML")
        data_format = settings.get("data_format")
        workflow_id = int(data_format.get(default_format, {}).get("workflow", "-1"))

    metadata = item.get("metadata")
    index = metadata.get("path")
    files_info = metadata.pop("files_info", [{}])
    files = [
        os.path.join(data_path, file_info.get("url", {}).get("label"))
            for file_info
            in files_info[0].get("items", {})
    ]
    comment = metadata.get("comment")
    link_data = item.get("link_data")
    grant_data = item.get("grant_data")

    try:
        headless = HeadlessActivity()
        url, current_action, recid = headless.auto(
            user_id= request_info.get("user_id"), workflow_id=workflow_id,
            index=index, metadata=metadata, files=files, comment=comment,
            link_data=link_data, grant_data=grant_data
        )
    except Exception as ex:
        traceback.print_exc()
        raise WekoSwordserverException(
            f"An error occurred while {headless.current_action}.",
            ErrorType.ServerError
        ) from ex

    return url, recid, current_action


def create_activity_from_jpcoar(check_result, data_path):
    deposit = {}
    settings = AdminSettings.get("sword_api_setting", dict_to_object=False)
    default_format = settings.get("default_format", "XML")
    data_format = settings.get("data_format")
    workflow_id = int(data_format.get(default_format, {}).get("workflow", "-1"))
    workflow = WorkFlow.query.filter_by(id=workflow_id).first()
    workflow_data = {
        "flow_id": workflow.flow_id,
        "workflow_id": workflow.id,
        "itemtype_id": workflow.itemtype_id,
    }

    work_activity = WorkActivity()
    activity =None
    try:
        activity = work_activity.init_activity(workflow_data)

        # update by data
        record_metadata = check_result.get("list_record")[0].get("metadata")
        if "$schema" in record_metadata:
            record_metadata.pop("$schema")

        files_info = None
        if "files_info" in record_metadata.keys():
            files_info = record_metadata.pop("files_info")

        # create activity temp data
        metadata = {"metainfo": record_metadata}

        if files_info:
            pid, files_metadata, deposit = upload_jpcoar_contents(data_path, files_info)
            # set item id
            activity.item_id = pid.object_uuid
            metadata["files"] = files_metadata

            # links_factory = obj_or_import_string('weko_search_ui.links:default_links_factory')
            # metadata['endpoints'] = links_factory(pid)

        work_activity.upt_activity_metadata(activity.activity_id, json.dumps(metadata))
        work_activity.update_title(activity.activity_id, record_metadata.get("title"))
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        current_app.logger.exception(ex)
        if activity:
            try:
                activity_data = dict(
                    activity_id=activity.activity_id,
                    action_id=activity.action_id,
                    action_version=activity.action.action_version,
                    action_status=ActionStatusPolicy.ACTION_CANCELED,
                    commond="",
                    action_order=activity.action_order
                )
                work_activity.quit_activity(activity_data)
            except:
                traceback.print_exc()
                current_app.logger.exception("activity quit canceled.")
        raise
    return activity, deposit.get("recid")


def upload_jpcoar_contents(data_path, contents_data):
    record_data = {}
    # Create uuid for record
    record_uuid = uuid.uuid4()
    # Create persistent identifier
    pid = current_pidstore.minters["weko_deposit_minter"](record_uuid, data=record_data)
    # Create record
    deposit = WekoDeposit.create(record_data, id_=record_uuid)

    # Index the record
    RecordIndexer().index(deposit)
    # get bucket
    bucket = Bucket.query.get(deposit["_buckets"]["deposit"])
    activity_files_data = []

    for files_info in contents_data:
        for file_info in files_info.get("items", []):
            # Check if file exists
            url = file_info.get("url", {}).get("url", "")
            file_path = os.path.join(data_path, url)
            if not url or not os.path.isfile(file_path):
                raise FileNotFoundError()

            # Check file size
            size_limit = bucket.size_limit
            location_limit = bucket.location.max_file_size
            content_length = os.path.getsize(file_path)
            if location_limit is not None:
                size_limit = min(size_limit, location_limit)
            if content_length and size_limit and content_length > size_limit:
                desc = (
                    "File size limit exceeded."
                    if isinstance(size_limit, int)
                    else size_limit.reason
                )
                current_app.logger.error(desc)
                raise FileSizeError(description=desc)
            if not _location_has_quota(bucket, content_length):
                desc = "Location has no quota"
                current_app.logger.error(desc)
                raise FileSizeError(description=desc)
            activity_file_data = create_file_info(
                bucket, file_path, size_limit, content_length
            )
            activity_files_data.append(activity_file_data)

            # update file url
            file_info["url"]["url"] = url_for(
                "invenio_records_ui.recid_files",
                pid_value=deposit["recid"],
                filename=os.path.basename(url),
                _external=True,
            )

    return pid, activity_files_data, deposit


def create_file_info(bucket, file_path, size_limit, content_length):
    stream = open(file_path, "rb")

    obj = ObjectVersion.create(bucket, os.path.basename(file_path), is_thumbnail=False)
    obj.set_contents(stream, size=content_length, size_limit=size_limit)

    return {
        "key": obj.basename,
        "uri": False,
        "multipart": False,
        "progress": 100,
        "completed": True,
        "version_id": str(obj.version_id),
        "is_head": True,
        "mimetype": obj.mimetype,
        "checksum": obj.file.checksum,
        "delete_marker": obj.deleted,
        "size": obj.file.size,
        "tags": {},
        "updated": obj.updated.isoformat(),
        "created_user_id": obj.created_user_id,
        "updated_user_id": obj.updated_user_id,
        "is_show": obj.is_show,
        "created": obj.created.isoformat(),
        "is_thumbnail": obj.is_thumbnail,
        **file_uploaded_owner(
            created_user_id=obj.created_user_id,
            updated_user_id=obj.updated_user_id
        ),
        "filename": obj.basename,
    }

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
        ) from ex

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
        workflow = None
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

        check_result.update({
            "register_format": register_format,
            "workflow_id": sword_client.workflow_id
        })

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
        index_tree_id = processed_json.get("record").get("header").get("indextree")
        if (
            register_format == "Workflow"
                and workflow.index_tree_id is not None
                and index_tree_id != workflow.index_tree_id
        ):
            processed_json.get("record").get("header").update(
                {"indextree": workflow.index_tree_id}
            )
            current_app.logger.info(
                f"Index is not matched with the workflow. "
                f"Replace the index tree id to {workflow.index_tree_id}."
            )

        list_record = generate_metadata_from_json(
            processed_json, json_ld, mapping, item_type
        )
        list_record = handle_check_exist_record(list_record)
        handle_item_title(list_record)
        list_record = handle_check_date(list_record)
        handle_check_id(list_record)
        handle_check_and_prepare_index_tree(list_record, True, [])
        handle_check_and_prepare_publish_status(list_record)

        # check if the user has scopes to publish
        required_scopes = set([actions_scope.id])
        token_scopes = set(request.oauth.access_token.scopes)
        if (
            list_record[0].get("publish_status") == "public"
            and not required_scopes.issubset(token_scopes)
        ):
            abort(403)

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
        msg = ""
        if (
            ex.args
            and len(ex.args)
            and isinstance(ex.args[0], dict)
            and ex.args[0].get("error_msg")
        ):
            msg = ex.args[0].get("error_msg")
            check_result.update({"error": msg})
        else:
            msg = str(ex)
            check_result.update({"error": str(ex)})
        current_app.logger.error(
            f"Check items error: {msg}")
        traceback.print_exc()

    return check_result


def generate_metadata_from_json(json, json_ld, mapping, item_type, is_change_identifier=False):
    """Generate metadata from JSON-LD.

    Args:
        json (dict): Json data including metadata.
        json_ld (dict): Original Json-LD data.
        mapping (dict): Mapping definition.
        item_type_id (int): ItemType ID used for registration.
        is_change_identifier (bool, optional):
            Change Identifier Mode. Defaults to False.

    Returns:
        list: list_record.
    """
    list_record = []

    mapper = WekoSwordMapper(json, json_ld, item_type, mapping)
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
