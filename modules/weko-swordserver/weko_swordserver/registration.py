import os
import time
import uuid
import json
import traceback
from flask import current_app, url_for

from invenio_db import db
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.utils import _location_has_quota
from invenio_indexer.api import RecordIndexer
from invenio_pidstore import current_pidstore

from weko_admin.models import AdminSettings
from weko_deposit.api import WekoDeposit
from weko_deposit.serializer import file_uploaded_owner
from weko_search_ui.utils import check_tsv_import_items, check_xml_import_items
from weko_workflow.api import WorkActivity
from weko_workflow.models import ActionStatusPolicy, WorkFlow


def check_import_items(file, is_change_identifier: bool = False):
    settings = AdminSettings.get("sword_api_setting", dict_to_object=False)
    default_format = settings.get("default_format")
    data_format = settings.get("data_format")
    if default_format == "TSV":
        check_tsv_result = check_tsv_import_items(file, is_change_identifier)
        if check_tsv_result.get("error"):
            # try xml
            time.sleep(1)
            workflow_id = int(data_format.get("XML", {}).get("workflow", "-1"))
            workflow = WorkFlow.query.filter_by(id=workflow_id).first()
            item_type_id = workflow.itemtype_id
            check_xml_result = check_xml_import_items(
                file, item_type_id, is_gakuninrdm=False
            )
            if check_xml_result.get("error"):
                return check_tsv_result, None
            else:
                return check_xml_result, "Workflow" # data_format['XML']['register_format']
        else:
            return check_tsv_result, "Direct" # data_format['TSV']['register_format']
    elif default_format == "XML":
        workflow_id = int(data_format.get("XML", {}).get("workflow", "-1"))
        workflow = WorkFlow.query.filter_by(id=workflow_id).first()
        item_type_id = workflow.itemtype_id
        check_xml_result = check_xml_import_items(
            file, item_type_id, is_gakuninrdm=False
        )
        if check_xml_result.get("error"):
            # try tsv
            time.sleep(1)
            check_tsv_result = check_tsv_import_items(file, is_change_identifier)
            if check_tsv_result.get("error"):
                return check_xml_result, None
            else:
                return check_tsv_result, "Direct" # data_format['TSV']['register_format']
        else:
            return check_xml_result, "Workflow" # data_format['XML']['register_format']

    return {}, None


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
        raise ex
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
