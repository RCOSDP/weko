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
from flask import current_app, url_for

from invenio_accounts.models import User
from invenio_db import db
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.utils import _location_has_quota
from invenio_indexer.api import RecordIndexer
from invenio_pidstore import current_pidstore

from weko_admin.models import AdminSettings
from weko_deposit.api import WekoDeposit
from weko_deposit.serializer import file_uploaded_owner
from weko_items_ui.utils import get_workflow_by_item_type_id
from weko_records.api import ItemTypes
from weko_search_ui.mapper import JsonLdMapper
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
    handle_validate_item_import,
    handle_check_authors_prefix,
    handle_check_authors_affiliation
)
from weko_workflow.api import WorkActivity, WorkFlow as WorkFlows
from weko_workflow.models import ActionStatusPolicy, WorkFlow
from weko_workflow.headless import HeadlessActivity

from .api import SwordItemTypeMapping
from .errors import ErrorType, WekoSwordserverException
from .utils import (
    get_record_by_client_id,
    unpack_zip,
    get_priority
)


def check_import_items(file, file_format, is_change_identifier=False):
    """Check metadata TSV/CSV or XML file for import.

    Check the contents of the file and return the result of the check.

    Args:
        file (FileStorage): File object.
        file_format (str): File format. "TSV/CSV" or "XML".
        is_change_identifier (bool, optional):
            Change Identifier Mode. Defaults to False.
    Returns:
        dict: Result of the check.
    """
    settings = AdminSettings.get(
        "sword_api_setting", dict_to_object=False
    ) or {}
    settings = settings.get("data_format", {})
    registar_type = (
        settings.get(file_format, {}).get("registration_type", "Direct")
    )
    check_result = {}
    check_result.update({"register_type": registar_type})
    is_active = settings.get(file_format, {}).get("active", True)
    if not is_active:
        current_app.logger.error(f"{file_format} metadata import is not enabled.")
        raise WekoSwordserverException(
            f"{file_format} metadata import is not enabled.", ErrorType.ServerError
        )

    if file_format == "TSV/CSV":
        check_result.update(check_tsv_import_items(file, is_change_identifier))

        if registar_type == "Workflow":
            # TODO: get workflow by item type id
            workflow = None
            check_result.update({"workflow_id": workflow.id})
    elif file_format == "XML":
        if registar_type == "Direct":
            raise WekoSwordserverException(
                "Direct registration is not allowed for XML metadata yet.",
                ErrorType.ServerError
            )

        workflow_id = int(settings.get(file_format, {}).get("workflow", "-1"))
        workflow = WorkFlow.query.get(workflow_id)
        item_type_id = workflow.itemtype_id
        check_result.update(check_xml_import_items(file, item_type_id))

    if not workflow or workflow.is_deleted:
        raise WekoSwordserverException("Workflow is not configured for importing xml.", ErrorType.ServerError)

    return check_result


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
        os.path.join(item.get("root_path"), file_info.get("url", {}).get("label"))
            for file_info
            in files_info[0].get("items", {})
    ]
    comment = metadata.get("comment")
    link_data = getattr(item['metadata'], 'link_data', None)
    grant_data = item.get("grant_data")

    error = None
    try:
        headless = HeadlessActivity()
        url, current_action, recid = headless.auto(
            user_id= request_info.get("user_id"), workflow_id=workflow_id,
            index=index, metadata=metadata, files=files, comment=comment,
            link_data=link_data, grant_data=grant_data
        )
    except Exception as ex:
        traceback.print_exc()
        url = headless.detail
        recid = headless.recid
        current_action = headless.current_action
        error = True

    return url, recid, current_action, error


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

def check_jsonld_import_items(
        file,
        packaging,
        shared_id=-1,
        client_id=None,
        mapping_id=None,
        is_change_identifier=False):
    """Check bagit import items.

    Check that the actual file contents match the recorded hashes stored
    in the manifest files and mapping metadata to the item type.
    client_id or mapping_id is required to get the mapping data.

    Args:
        file (FileStorage | str): File object or file path.
        packaging (str): Packaging type. SWORDBagIt or SimpleZip.
        shared_id (int): Shared ID. Defaults to -1.
        client_id (int): Client ID. Defaults to None.
        mapping_id (int): Mapping ID. Defaults to None.
        is_change_identifier (bool, optional):
            Change Identifier Mode. Defaults to False.

    Returns:
        dict: Result of mapping to item type

    Example:

    >>> check_bagit_import_items(file, "SimpleZip")
    {
        "data_path": "/tmp/xxxxx",
        "list_record": [
            # list of metadata
        ]
        "register_type": "Direct",
        "item_type_id": 1,
    } # Setiing is `Direct`

    >>> check_bagit_import_items(file, "SimpleZip")
    {
        "data_path": "/tmp/xxxxx",
        "list_record": [
            # list of metadata
        ]
        "register_type": "Workflow",
        "workflow_id": 1,
        "item_type_id": 2,
    } # Setting is `Workflow`
    """
    check_result = {}

    if isinstance(file, str):
        filename = os.path.basename(file)
    else:
        filename = file.filename

    try:
        data_path, files_list = unpack_zip(file)
        check_result.update({
            "data_path": data_path,
            "weko_shared_id": shared_id
        })

        # metadata json file name
        json_name = (
            current_app.config['WEKO_SWORDSERVER_METADATA_FILE_SWORD']
                if "SWORDBagIt" in packaging
                else current_app.config['WEKO_SWORDSERVER_METADATA_FILE_ROCRATE']
        )

        # Check if the bag is valid
        bag = bagit.Bag(data_path)
        bag.validate()

        if client_id is not None:
            sword_client, sword_mapping = get_record_by_client_id(client_id)
        elif mapping_id is not None:
            sword_mapping = SwordItemTypeMapping.get_mapping_by_id(mapping_id)
        else:
            current_app.logger.error(f"Client ID or Mapping ID not defined.")
            raise WekoSwordserverException(
                "Client ID or Mapping ID not defined.",
                errorType=ErrorType.ServerError
            )

        if sword_mapping is None:
            current_app.logger.error(f"Mapping not defined for sword client.")
            raise WekoSwordserverException(
                "Metadata mapping not defined for registration your item.",
                errorType=ErrorType.ServerError
            )

        # Check workflow and item type
        register_type = sword_client.registration_type
        workflow = None
        if register_type == "Workflow":
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
            "register_type": register_type,
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
        mapper = JsonLdMapper(item_type.id, mapping)
        item_metadatas, _ = mapper.to_item_metadata(json_ld)
        list_record = [
            {
                "$schema": f"/items/jsonschema/{item_type.id}",
                "metadata": item_metadata,
                "item_type_name": item_type.item_type_name.name,
                "item_type_id": item_type.id,
                "publish_status": item_metadata.get("publish_status")
                # item_metadata has attributes
                # >  id, link_data, non_existent, save_as_is, metadata_only,
                # >  cnri, doi_ra, doi
            } for item_metadata in item_metadatas
        ]

        list_record.sort(key=lambda x: get_priority(x['metadata'].link_data))
        handle_index_tree_much_with_workflow(list_record, workflow)
        handle_save_bagit(list_record, file, data_path, filename)

        handle_set_change_identifier_flag(list_record, is_change_identifier)
        handle_fill_system_item(list_record)

        list_record = handle_validate_item_import(list_record, item_type.schema)

        list_record = handle_check_exist_record(list_record)
        handle_item_title(list_record)
        list_record = handle_check_date(list_record)
        handle_check_id(list_record)
        handle_check_and_prepare_index_tree(list_record, True, [])
        handle_check_and_prepare_publish_status(list_record)

        handle_check_file_metadata(list_record, data_path)

        handle_check_authors_prefix(list_record)
        handle_check_authors_affiliation(list_record)

        # add zip file to temporary dictionary
        # if current_app.config.get("WEKO_SWORDSERVER_DEPOSIT_DATASET"):
        #     if isinstance(file, str):
        #         shutil.copy(file, os.path.join(data_path, "data", filename))
        #     else:
        #         file.seek(0, 0)
        #         file.save(os.path.join(data_path, "data", filename))

            # files_list.append(f"data/{filename}")
        # handle_files_info(list_record, files_list, data_path, filename)

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


def handle_index_tree_much_with_workflow(list_record, workflow):
    """Handle index tree id much with workflow."""
    if workflow is None or workflow.index_tree_id is None:
        return

    for record in list_record:
        record.get("metadata").update({"path": [workflow.index_tree_id]})
        current_app.logger.info(
            f"Index is not matched with the workflow. "
            f"Replace the index tree id to {workflow.index_tree_id}."
        )

def handle_save_bagit(list_record, file, data_path, filename):
    """Handle save bagit file as is.

    Save the bagit file as is if the metadata has the save_as_is flag.
    """
    if len(list_record) > 1:
        # item split flag takes precedence over save Bag flag
        return

    metadata = list_record[0].get("metadata")
    if metadata is None or not metadata.save_as_is:
        return

    if isinstance(file, str):
        shutil.copy(file, os.path.join(data_path, "data", filename))
    else:
        file.seek(0, 0)
        file.save(os.path.join(data_path, "data", filename))

    current_app.logger.info("Save the bagit file as is.")
    list_record[0]["file_path"] = [filename] # for Direct registration

    files_info = metadata.get("files_info")  # for Workflow registration
    key = files_info[0].get("key")

    dataset_info = {                         # replace metadata
        "filesize": [
            {
                "value": str(os.path.getsize(
                    os.path.join(data_path, "data", filename))
                ),
            }
        ],
        "filename":  filename,
        "format": "application/zip",
        "url": {
            "objectType": "dataset",
            "label": filename
        },
    }
    metadata[key] = [dataset_info]


# def handle_files_info(list_record, files_list, data_path, filename):
#     """ Handle files_info in metadata.

#     Handle metadata for Direct registration and Workflow registration.
#     pick up files infomation from metadata and add it to files_info.

#     Args:
#         list_record (list): List of metadata.
#         files_list (list): List of files in the zip file.
#         data_path (str): Path to the temporary directory.
#         filename (str): Name of the zip file.

#     Returns:
#         list: list_record with files_info.
#     """
#     # for Direct registration handling
#     target_files_list = []
#     for file in files_list:
#         if file.startswith("data/") and file != "data/":
#             target_files_list.append(file.split("data/")[1])
#     if target_files_list:
#         list_record[0].update({"file_path":target_files_list})

#     metadata = list_record[0].get("metadata")
#     files_info = metadata.get("files_info")  # for Workflow registration
#     key = files_info[0].get("key")
#     file_metadata = metadata.get(key)  # for Direct registration

#     # add dataset zip file's info to files_info if dataset will be deposited.
#     if current_app.config.get("WEKO_SWORDSERVER_DEPOSIT_DATASET"):
#         dataset_info = {
#             "filesize": [
#                 {
#                     "value": str(os.path.getsize(os.path.join(data_path, "data", filename))),
#                 }
#             ],
#             "filename":  filename,
#             "format": "application/zip",
#             "url": {
#                 "url": "",
#                 "objectType": "fulltext",
#                 "label": f"data/{filename}"
#             },
#         }
#         files_info[0].get("items").append(dataset_info)
#         file_metadata.append(dataset_info)

#     return list_record
