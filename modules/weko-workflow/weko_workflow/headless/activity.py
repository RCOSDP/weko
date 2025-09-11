# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Workflow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module for weko_workflow headless activity."""

import os
import json
import traceback
import uuid
from copy import deepcopy
from datetime import datetime
from flask import current_app, url_for, request
from sqlalchemy.exc import SQLAlchemyError

from invenio_accounts.models import User
from invenio_db import db
from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_files_rest.tasks import remove_file_data
from invenio_files_rest.utils import delete_file_instance
from invenio_pidstore import current_pidstore
from invenio_pidstore.models import PersistentIdentifier

from weko_deposit.api import WekoDeposit, WekoRecord
from weko_deposit.links import base_factory
from weko_deposit.serializer import file_uploaded_owner
from weko_items_ui.utils import (
    update_index_tree_for_record, validate_form_input_data, to_files_js
)
from weko_items_ui.views import (
    check_validation_error_msg, prepare_edit_item, prepare_delete_item
)
from weko_logging.activity_logger import UserActivityLogger
from weko_records.api import ItemTypes
from weko_records.serializers.utils import get_mapping

from ..api import Action, WorkActivity, WorkFlow
from ..errors import WekoWorkflowException
from ..utils import (
    check_authority_by_admin,
    delete_lock_activity_cache,
    get_identifier_setting,
)
from ..views import (
    next_action,
    verify_deletion,
    init_activity,
    lock_activity
)

class HeadlessActivity(WorkActivity):
    """Handler of headless activity class.

    This class is used to handle the activity without UI. <br>
    Recommended to use `auto` method to automatically progress the action. <br>
    If you want to progress the action manually, use each method, such as
    `item_registration`, `item_link`, `identifier_grant`, `approval`. <br>
    But, this is not recommended because the order of actions is different for each flow.

    Attributes:
        user (User): Activity operator user model
        workflow (WorkFlow): Workflow model
        item_type (ItemType): Item type model
        files_info (list): List of file information uploaded in the activity
        activity_id (str): Activity ID
        current_action_id (int): Current action ID
        current_action (str): Current action endpoint
        community (str): Community ID
        detail (str): Activity detail URL
        recid (str): Record ID

    Examples:

    >>> headless = HeadlessActivity()
    >>> url, current_action, recid = headless.auto(
    ...     user_id=1, workflow_id=1,
    ...     metadata={"pubdate": "2025-01-01", "item_30001_title0": {...}, ...},
    ...     files=["/var/tmp/..."], index=[1623632832836],
    ...     comment="comment", link_data=[{"item_id": 1, "sele_id": "isVersionOf"}],
    ... )
    >>> print(url, current_action, recid)
    'http://weko3.example.org/workflow/activity/detail/A-EXAMPLE-0001', 'end_action', 1
    """
    def __init__(
            self, _lock_skip=False,
            _metadata_inheritance=False, _files_inheritance=False
        ):
        """Initialize.

        Args:
            _lock_skip (bool, optional): Defaults to False.
                If True, skips the activity lock/unlock process.
            _metadata_inheritance (bool, optional): Defaults to True.
                If True, inherits metadata from the previous version.
                If False, replaces all metadata.
            _files_inheritance (bool, optional): Defaults to True.
                If True, inherits files from the previous version.
                If False, replaces all files.
        """
        super().__init__()
        self.user = None
        """ User: User model """
        self.workflow = None
        """ WorkFlow: Workflow model """
        self.item_type = None
        """ ItemType: Item type model """
        self.files_info = None
        """ list: List of file information """
        self._recid = None
        self._model = None
        self._deposit = None
        self._lock_skip = _lock_skip
        self._metadata_inheritance = _metadata_inheritance
        self._files_inheritance= _files_inheritance

        actions = Action().get_action_list()
        self._actions = {
            int(action.id): str(action.action_endpoint) for action in actions
        }

    @property
    def activity_id(self):
        """str: activity id."""
        return str(self._model.activity_id) if self._model else None

    @property
    def current_action_id(self):
        """int: current action id."""
        return int(self._model.action_id) if self._model else None

    @property
    def current_action(self):
        """str: current action endpoint.

        It can be `begin_action`, `login_item`, `link_item`, `identifier_grant`,
        `approval` or `end_action`.
        """
        return self._actions.get(self.current_action_id) if self._model else None

    @property
    def community(self):
        """str: community id."""
        return (
            str(self._model.activity_community_id)
            if self._model and self._model.activity_community_id
            else None
        )

    @property
    def detail(self):
        """str: activity detail URL."""
        return str(url_for(
            "weko_workflow.display_activity",
            activity_id=self.activity_id, community=self.community,
            _external=True
        )) if self._model else ""

    @property
    def recid(self):
        """str: Record ID."""
        return self._recid if isinstance(self._recid, str) else None

    def init_activity(self, user_id, **kwargs):
        """Manual initialization of activity.

        Note:
            Please use `auto` method to automatically progress the action.

        user_id and workflow_id are required to create a new activity. <br>
        If activity_id is specified, an existing activity will be resumed. <br>
        If creating an activity to edit an existing item, item_id is required.

        Args:
            user_id (int): User ID
            **kwargs:
                - workflow_id (int): Workflow ID
                - community (str): Community ID
                - activity_id (str): Activity ID
                - item_id (str): Item ID
                - for_delete (bool): <br>
                    Flag to create activity for delete item. Defaults to False.

        Returns:
            str: Activity detail URL.
        """
        if self._model is not None:
            current_app.logger.error("activity is already initialized.")
            raise WekoWorkflowException("activity is already initialized.")

        activity_id = kwargs.get("activity_id")
        shared_ids = kwargs.get("shared_ids", [])
        if activity_id is not None:
            # restart activity
            result, _ = verify_deletion(activity_id)
            if result.json.get("is_delete"):
                current_app.logger.error(f"activity({activity_id}) is already deleted.")
                raise WekoWorkflowException(f"activity({activity_id}) is already deleted.")

            self._model = self.get_activity_by_id(activity_id)
            if self._model is None:
                current_app.logger.error(f"activity({activity_id}) is not found.")
                raise WekoWorkflowException(f"activity({activity_id}) is not found.")
            self.workflow = self._model.workflow
            self.item_type = ItemTypes.get_by_id(self.workflow.itemtype_id)
            # check user permission
            user = User.query.get(user_id)
            if (
                self._model.activity_login_user != user_id
                    and {'user': user_id} not in self._model.shared_user_ids
                    and not check_authority_by_admin(self.activity_id, user)
            ):
                current_app.logger.error(
                    f"user({user_id}) cannot access activity({activity_id}).")
                raise WekoWorkflowException(
                    f"user({user_id}) cannot access activity({activity_id}).")

            locked_value = self._activity_lock()
            current_app.logger.info(
                f"activity({self.activity_id}) is restarted by user({user_id}).")
            self.user = user
            pid = PersistentIdentifier.get_by_object(
                "recid", object_type="rec", object_uuid=self._model.item_id
            )
            self._recid = pid.pid_value
            self._activity_unlock(locked_value)
            return self.detail

        item_id = kwargs.get("item_id")
        community = kwargs.get("community")
        for_delete = kwargs.get("for_delete") or False
        if item_id is not None:
            item_id = str(item_id)
            # edit or delete item
            if not for_delete:
                response = prepare_edit_item(item_id, community)
            else:
                response = prepare_delete_item(item_id, community, shared_ids)

            if response.json.get("code") != 0:
                current_app.logger.error(
                    f"failed to create activity: {response.json.get('msg')}")
                raise WekoWorkflowException(response.json.get("msg"))

            url = str(response.json.get("data").get("redirect"))
            if "/records/" in url and for_delete:
                # item delete directly
                self.user = User.query.get(user_id)
                self._recid = item_id
                return url
            activity_id = url.split("/activity/detail/")[1]
            if "?" in activity_id:
                activity_id = activity_id.split("?")[0]

            self._model = self.get_activity_by_id(activity_id)
            self.workflow = self._model.workflow
            self.item_type = ItemTypes.get_by_id(self.workflow.itemtype_id)
            pid = PersistentIdentifier.get_by_object(
                "recid", object_type="rec", object_uuid=self._model.item_id
            )
            self._recid = pid.pid_value

        else:
            workflow_id = kwargs.get("workflow_id")
            if workflow_id is None:
                current_app.logger.error("workflow_id is required to create activity.")
                raise WekoWorkflowException("workflow_id is required to create activity.")

            # create activity for new item
            self.workflow = workflow = WorkFlow().get_workflow_by_id(workflow_id)
            if workflow is None or workflow.is_deleted:
                current_app.logger.error(f"workflow(id={workflow_id}) is not found.")
                raise WekoWorkflowException(f"workflow(id={workflow_id}) is not found.")

            self.item_type = ItemTypes.get_by_id(workflow.itemtype_id)
            activity = {
                "flow_id": workflow.flow_id,
                "workflow_id": workflow.id,
                "itemtype_id": workflow.itemtype_id,
                "activity_login_user": user_id
            }

            result, _ = init_activity(activity, community)

            if result.json.get("code") != 0:
                current_app.logger.error(
                    f"failed to create activity: {result.json.get('msg')}")
                raise WekoWorkflowException(result.json.get("msg"))

            url = result.json.get("data").get("redirect")
            activity_id = url.split("/activity/detail/")[1]
            if "?" in activity_id:
                activity_id = activity_id.split("?")[0]
            self._model = self.get_activity_by_id(activity_id)

        self.user = User.query.get(user_id)
        current_app.logger.info(
            f"activity({activity_id}) is created by user({user_id}).")
        return self.detail

    def auto(self, **params):
        """Automatically progressing the action.

        Automatically progress the actions of an activity. <br>
        If there is an approval action, it stops there. <br>
        When registering a new item, specify workflow ID; <br>
        when editing an existing item, specify item ID; <br>
        when resuming an existing activity, specify activity ID; <br>

        Args:
            user_id (int): User ID <br>
            metadata (dict): Metadata with item type format <br>
            workflow_id (int, optional): Workflow ID <br>
            community (str, optional): Community ID <br>
            activity_id (str, optional): Activity ID <br>
            item_id (str, optional): Item ID <br>
            files (list, optional): List of temporary file avsolute path <br>
            index (list, optional): List of index ID <br>
            comment (str, optional): Comment <br>
            link_data (list, optional):
                List of item link information <br>
                e.g. [{"item_id": 1, "sele_id": "isVersionOf"}] <br>
            grant_data (dict, optional): data for identifier grant.

        Examples:

        >>> headless = HeadlessActivity()
        >>> url, current_action, recid = headless.auto(
        ...     user_id=1, workflow_id=1,
        ...     metadata={"pubdate": "2025-01-01", "item_30001_title0": {...}, ...},
        ...     files=["/var/tmp/..."], index=[1623632832836],
        ...     comment="comment", link_data=[{"item_id": 1, "sele_id": "isVersionOf"}],
        ... )
        >>> print(url, current_action, recid)
        'http://weko3.example.org/workflow/activity/detail/A-EXAMPLE-0001', 'end_action', 1
        """

        self.init_activity(**params)

        # skip locks temporarily even if skip flag is not True
        _lf = self._lock_skip
        locked_value = self._activity_lock()
        self._lock_skip = True

        # automatically progressing the action
        while self.current_action not in {"end_action", "approval"}:
            if self.current_action == "item_login":
                self.item_registration(
                    params.get("metadata"), params.get("files"),
                    params.get("index"), params.get("comment"),
                    params.get("non_extract")
                )
            elif self.current_action == "item_link":
                self.item_link(params.get("link_data"))
            elif self.current_action == "identifier_grant":
                self.identifier_grant(params.get("grant_data"))
            else:
                raise NotImplementedError(
                    f"Action {self.current_action} is not implemented."
                )

        self._lock_skip = _lf
        self._activity_unlock(locked_value)

        returns = self.detail, self.current_action, self.recid

        self.end()

        return returns


    def item_registration(
            self, metadata, files=None, index=None, comment=None, non_extract=None
        ):
        """Manual action for item registration.

        Note:
            Please use `auto` method to automatically progress the action.

        Args:
            metadata (dict): Metadata with item type format
            files (list, optional): List of temporary file avsolute path
            index (list, optional): List of index ID.
                if use workflow setting, do not specify this parameter.
            comment (str, optional): Comment
            non_extract (list, optional):
                List of file names to exclude from text extraction.
                If specified, these files will not be processed for text extraction.

        Returns:
            str: Activity detail URL.

        Raises:
            WekoWorkflowException:
                Something went wrong in the activity processing.
        """
        if self._model is None:
            current_app.logger.error("activity is not initialized.")
            raise WekoWorkflowException("activity is not initialized.")

        # some error had occurred in idnentifier_grant if not enough metadata.
        error = check_validation_error_msg(self.activity_id).json
        if error.pop("code") == 1:
            current_app.logger.error(f"failed to input metadata: {error}")
            raise WekoWorkflowException(error)

        self._input_metadata(metadata, files, non_extract)
        self._designate_index(index)
        self._comment(comment)

        return self.detail


    def _input_metadata(self, metadata, files=None, non_extract=None):
        """input metadata.

        Inputs metadata to the deposit and uploads files. <br>
        Item type of the metadata must match the workflow item type. <br>

        Args:
            metadata (dict): Metadata with item type format.
            files (list, optional):
                List of file paths or file objects to upload.
            non_extract (list, optional):
                List of file names to exclude from text extraction.
                If specified, these files will not be processed for text extraction.

        Returns:
            str: Record ID (recid) of the item.

        Raises:
            WekoWorkflowException:
                If the item type of the metadata does not match the workflow item type,
                or if there is an error in processing the metadata input.
        """
        locked_value = self._activity_lock()
        non_extract = non_extract if isinstance(non_extract, list) else []

        try:
            itemtype_id = metadata.get("$schema", "").split("/")[-1]
            if itemtype_id != "" and int(itemtype_id) != self.item_type.id:
                msg = (
                    "Itemtype of importing item;(id={}) is not matched with "
                    "workflow itemtype;(id={})."
                    .format(itemtype_id, self.item_type.id)
                )
                current_app.logger.error(msg)
                raise WekoWorkflowException(msg)
            metadata.update({"$schema": f"/items/jsonschema/{self.item_type.id}"})

            metadata.setdefault("pubdate", datetime.now().strftime("%Y-%m-%d"))
            feedback_maillist = metadata.pop("feedback_mail_list", [])
            self.create_or_update_action_feedbackmail(
                activity_id=self.activity_id,
                action_id=self.current_action_id,
                feedback_maillist=feedback_maillist
            )
            request_maillist = metadata.pop("request_mail_list", [])
            self.create_or_update_activity_request_mail(
                activity_id=self.activity_id,
                request_maillist=request_maillist,
                is_display_request_button=False
            )

            from weko_search_ui.utils import get_data_by_property
            # get value of "Title" from metadata by jpcoar_mapping
            item_map = get_mapping(self.item_type.id, "jpcoar_mapping", self.item_type)
            title_value_key = "title.@value"
            title, _ = get_data_by_property(metadata, item_map, title_value_key)
            weko_shared_ids = [
                {"user": int(id)} if not isinstance(id, dict) else id
                for id in metadata.get("weko_shared_ids", [])
            ]
            shared_user_ids = metadata.get("shared_user_ids", [])
            identifierRegistration_key = item_map.get(
                "identifierRegistration.@attributes.identifierType", ""
            ).split(".")[0]

            # merge shared_user_ids
            shared_ids = shared_user_ids if shared_user_ids else weko_shared_ids

            self.update_activity(self.activity_id, {
                "title": title[0] if title else "",
                "shared_user_ids": shared_ids
            })

            _old_metadata, _old_files = {}, []
            if self.recid is None:
                # create new item
                location_name = None
                if self.workflow and self.workflow.location:
                    location_name = self.workflow.location.name
                record_data = {}
                record_uuid = uuid.uuid4()
                pid = (
                    current_pidstore
                    .minters["weko_deposit_minter"](record_uuid, data=record_data)
                )
                self._deposit = WekoDeposit.create(
                    record_data, id_=record_uuid,
                    workflow_location_name=location_name
                )
                self._model.item_id = record_uuid

            else:
                # update existing item
                record_uuid = self._model.item_id
                self._deposit = WekoDeposit.get_record(record_uuid)

                if metadata.get("edit_mode", "Keep").lower() == "upgrade":
                    cur_pid = PersistentIdentifier.get_by_object(
                        "recid", object_type="rec", object_uuid=record_uuid
                    )

                    if cur_pid.pid_value.endswith(".0"):
                        parent_pid = PersistentIdentifier.get(
                            "recid", cur_pid.pid_value.split(".")[0]
                        )
                        _deposit = WekoDeposit.get_record(parent_pid.object_uuid)
                        _deposit.non_extract = non_extract
                        self._deposit = _deposit.newversion(parent_pid)
                        self._deposit.merge_data_to_record_without_version(cur_pid)
                        record_uuid = self._model.item_id = self._deposit.model.id
                        db.session.merge(self._model)

                        weko_record = WekoRecord.get_record_by_pid(
                            self._deposit.pid.pid_value
                        )
                        weko_record.update_item_link(parent_pid.pid_value)
                        current_app.logger.info(
                            "Item {} is upgraded to {}."
                            .format(
                                parent_pid.pid_value,
                                self._deposit.pid.pid_value.split(".")[1]
                            )
                        )

                self._deposit.non_extract = non_extract
                pid = PersistentIdentifier.get_by_object(
                    "recid", object_type="rec", object_uuid=record_uuid
                )

                # get old metadata by record_uuid
                _old_metadata = self._deposit.item_metadata
                _old_files = to_files_js(self._deposit)

            db.session.commit()
            self._recid = pid.pid_value

            if self._metadata_inheritance:
                # update old metadata partially
                metadata = {**_old_metadata, **metadata}
            # if metadata_replace is True, replace all metadata

            deleted_items = metadata.get("deleted_items") or []
            item_type_render = self.item_type.render
            for metadata_id in item_type_render["table_row"]:
                # ignore Identifier Regstration (Import hasn't withdraw DOI)
                if metadata_id == identifierRegistration_key:
                    continue
                if metadata_id not in metadata and metadata_id not in deleted_items:
                    deleted_items.append(metadata_id)
            metadata["deleted_items"] = deleted_items

            # from metadata before update
            old_files_obj = {
                f.key: f.obj for f in self._deposit.files
                if f.key in [_.get("key") for _ in _old_files]
            }

            if not self._files_inheritance:
                self.files_info = self._upload_files(files, old_files_obj)
            else:
                _new_files = self._upload_files(files, old_files_obj)
                files_dict = {file["key"]: file for file in _old_files}
                # replace old files with new files if they have the same key
                for new_file in _new_files:
                    files_dict[new_file["key"]] = new_file
                self.files_info = list(files_dict.values())

            # to exclude from file text extraction
            for file in self.files_info:
                file["non_extract"] = file["filename"] in non_extract

            file_key_list = []
            for key, value in metadata.items():
                if not isinstance(value, list) or not len(value):
                    continue
                if isinstance(value[0], dict) and "filename" in value[0]:
                    file_key_list.append(key)

            # Update file metadata with uploaded file information
            for file_metadata, uploaded_file in (
                (file_metadata, uploaded_file)
                for file_key in file_key_list
                for file_metadata in metadata[file_key]
                for uploaded_file in self.files_info
                if file_metadata["filename"] == uploaded_file["filename"]
            ):
                url_dict = file_metadata.get("url", {})
                url_dict["url"] = "{}/record/{}/files/{}".format(
                    current_app.config["THEME_SITEURL"],
                    pid.pid_value,
                    uploaded_file.get("filename")
                )
                file_metadata["url"]= url_dict
                file_metadata["format"] = uploaded_file.get("mimetype")
                file_metadata["version_id"] = uploaded_file.get("version_id")

            # Delete files not in metadata
            delete_files = set()
            current_filenames = [
                file.get("filename")
                for file_key in file_key_list
                for file in metadata[file_key]
            ]
            # from updated metadata
            for uploaded_file in self.files_info:
                if uploaded_file.get("key") not in current_filenames:
                    delete_files.add(uploaded_file.get("version_id"))

            for file_metadata in _old_files:
                filename = file_metadata.get("key")
                if filename not in current_filenames and filename in old_files_obj:
                    delete_files.add(file_metadata.get("version_id"))
            self._delete_file(delete_files)

            # remove files_info with deleted files
            self.files_info = [
                file for file in self.files_info
                if file.get("version_id") not in delete_files
            ]

            # save metadata into workflow_activity.tmp_data
            data = {
                "metainfo": metadata,
                "files": self.files_info,
                "endpoint": {
                    "initialization": f"/api/deposits/redirect/{pid.pid_value}",
                }
            }
            data["endpoint"].update(base_factory(pid))
            self.upt_activity_metadata(self.activity_id, json.dumps(data))

            # designate_index
            workflow_index = self.workflow.index_tree_id
            list_index =  (
                [workflow_index]
                if workflow_index is not None else metadata.get("path", [])
            )
            if not isinstance(list_index, list) or not list_index:
                raise WekoWorkflowException(
                    "Index is not specified in workflow or item metadata."
                )

            result = {"is_valid": True}
            validate_form_input_data(result, self.item_type.id, deepcopy(metadata))
            if not result.get("is_valid"):
                current_app.logger.error(
                    "Failed to input metadata: {}".format(result.get("error"))
                )
                raise WekoWorkflowException(result.get("error"))

            index = {
                "index": list_index,
                "actions": metadata.get("publish_status")
            }
            self._deposit.update(index, metadata)
            self._deposit.commit()
        except WekoWorkflowException as ex:
            traceback.print_exc()
            raise
        except SQLAlchemyError as ex:
            db.session.rollback()
            msg = f"Failed to input metadata to deposit: {ex}"
            current_app.logger.error(msg)
            traceback.print_exc()
            raise WekoWorkflowException(msg) from ex
        except Exception as ex:
            msg = f"Failed to input metadata to deposit: {ex}"
            current_app.logger.error(msg)
            traceback.print_exc()
            raise WekoWorkflowException(msg) from ex
        finally:
            self._activity_unlock(locked_value)


    def _upload_files(self, files, old_files):
        """upload files."""
        files = files or []
        bucket = Bucket.query.get(self._deposit["_buckets"]["deposit"])
        files_info = []

        def upload(file_name, stream, size, is_thumbnail=False):
            size_limit = bucket.size_limit
            location_limit = bucket.location.max_file_size
            if location_limit is not None:
                size_limit = min(size_limit, location_limit)
            if size and size_limit and size > size_limit:
                desc = (
                    "File size limit exceeded."
                    if isinstance(size_limit, int)
                    else size_limit.reason
                )
                current_app.logger.error(desc)
                raise FileSizeError(description=desc)

            root_file_id = None
            if file_name in old_files:
                obj = old_files[file_name]
                root_file_id = obj.root_file_id
                obj.remove()

            obj = ObjectVersion.create(bucket, file_name, is_thumbnail=False)
            obj.is_thumbnail = is_thumbnail
            obj.set_contents(
                stream, size=size, size_limit=size_limit, root_file_id=root_file_id
            )
            url = f"{request.url_root}api/files/{obj.bucket_id}/{obj.basename}"
            return {
                "created": obj.created.isoformat(),
                "updated": obj.updated.isoformat(),
                "key": obj.basename,
                "filename": obj.basename,
                "size": obj.file.size,
                "checksum": obj.file.checksum,
                "mimetype": obj.mimetype,
                "is_head": True,
                "is_show": obj.is_show,
                "is_thumbnail": obj.is_thumbnail,
                "created_user_id": obj.created_user_id,
                "updated_user_id": obj.updated_user_id,
                "uploaded_owners": file_uploaded_owner(
                    created_user_id=obj.created_user_id,
                    updated_user_id=obj.updated_user_id
                ),
                "links": {
                    "sefl": url,
                    "version": f"{url}?versionId={obj.version_id}",
                    "uploads": f"{url}?uploads",
                },
                "tags": {},
                "licensetype": None,
                "displaytype": None,
                "delete_marker": obj.deleted,
                "uri": False,
                "multiple": False,
                "progress": 100,
                "complete": True,
                "version_id": str(obj.version_id),
            }

        for file in files:
            if isinstance(file, str):
                if not os.path.isfile(file):
                    current_app.logger.warning(f"file({file}) is not found.")
                    continue
                size = os.path.getsize(file)
                with open(file, "rb") as f:
                    file_info = upload(os.path.basename(file), f, size)
            elif isinstance(file, dict):
                file_info = file
            else:
                "werkzeug.datastructures.FileStorage"
                file.seek(0, 2)
                file_size = file.tell()
                file.seek(0)
                file_info = upload(file.filename, file.stream, file_size)

            UserActivityLogger.info(
                operation="FILE_CREATE",
                target_key=file_info.get("filename"),
                required_commit=False
            )
            files_info.append(file_info)

        return files_info

    def _delete_file(self, version_ids):
        """Delete ObjectVersions

        Delete the target ObjectVersion and rewrite is_head. Optionally,
        delete the FileInstance and file (asynchronous).

        Args:
            version_ids (list[str]): A list of version_ids to be deleted
        """
        for version_id in version_ids:
            obj = ObjectVersion.get(version_id=version_id)
            file_key = obj.key
            obj.remove()
            if obj.is_head:
                obj_to_restore = ObjectVersion.get_versions(
                    obj.bucket, obj.key, desc=True
                ).first()
                if obj_to_restore:
                    obj_to_restore.is_head = True
            if obj.file_id and not delete_file_instance(obj.file_id):
                remove_file_data.delay(str(obj.file_id))

            UserActivityLogger.info(
                operation="FILE_DELETE",
                target_key=file_key,
                required_commit=False
            )

    def _designate_index(self, index=None):
        """Designate Index.

        Args:
            index (list): list of index identifier.
        """
        locked_value = self._activity_lock()

        index = self.workflow.index_tree_id or index

        if not isinstance(index, list):
            index = [index]
        try:
            for idx in index:
                update_index_tree_for_record(self.recid, idx)
        except Exception as ex:
            current_app.logger.error(f"failed to designate index: {ex}")
            raise WekoWorkflowException("failed to designate index.") from ex
        finally:
            self._activity_unlock(locked_value)

    def _comment(self, comment):
        """Set Comment."""
        locked_value = self._activity_lock()

        try:
            result, _ = next_action(
                activity_id=self.activity_id, action_id=self.current_action_id,
                json_data={"commond": comment}
            )
        except Exception as ex:
            current_app.logger.error(f"failed to set comment: {ex}")
            raise WekoWorkflowException("failed to set comment.") from ex
        finally:
            self._activity_unlock(locked_value)

        if result.json.get("code") != 0:
            current_app.logger.error(
                "failed to set comment: {}".format(result.json.get("msg"))
            )
            raise WekoWorkflowException(result.json.get("msg"))

    def item_link(self, link_data=None):
        """Action for Item Link.

        Args:
            link_data (list, optional): List of item link information. <br>
                e.g. [{"item_id": 1, "sele_id": "isVersionOf"}]

        Raises:
            WekoWorkflowException:
                If the item link action fails or if the link data is invalid.

        """
        link_data = link_data or []
        locked_value = self._activity_lock()

        try:
            result, _ = next_action(
                activity_id=self.activity_id, action_id=self.current_action_id,
                json_data={"link_data": link_data}
            )
        except Exception as ex:
            current_app.logger.error(f"failed in Item Link: {ex}")
            raise WekoWorkflowException("failed in Item Link.") from ex
        finally:
            self._activity_unlock(locked_value)

        if result.json.get("code") != 0:
            current_app.logger.error(f"failed in Item Link: {result.json.get('msg')}")
            raise WekoWorkflowException(result.json.get("msg"))

    def identifier_grant(self, grant_data=None):
        """Action for Identifier Grant.

        Args:
            grant_data (dict, optional): Data for identifier grant. <br>
                If not specified, default values will be used.

        Raises:
            WekoWorkflowException:
                If the identifier grant action fails or if the grant data is invalid.
        """
        locked_value = self._activity_lock()

        grant_data = grant_data if isinstance(grant_data, dict) else {}
        identifier_setting = get_identifier_setting(self.community or "Root Index")
        text_empty = "<Empty>"

        grant_data.setdefault("identifier_grant", "0")
        grant_data.setdefault("identifier_grant_jalc_doi_suffix",
            f"https://doi.org/{identifier_setting.jalc_doi or text_empty}/{self.recid}")
        grant_data.setdefault("identifier_grant_jalc_cr_doi_suffix",
            f"https://doi.org/{identifier_setting.jalc_crossref_doi or text_empty}/{self.recid}")
        grant_data.setdefault("identifier_grant_jalc_dc_doi_suffix",
            f"https://doi.org/{identifier_setting.jalc_datacite_doi or text_empty}/{self.recid}")
        grant_data.setdefault("identifier_grant_ndl_jalc_doi_suffix",
            f"https://doi.org/{identifier_setting.ndl_jalc_doi or text_empty}/{self.recid}")

        try:
            # If not enough metadata, return to item registration and
            # leave error message in cache.
            result, _ = next_action(
                activity_id=self.activity_id, action_id=self.current_action_id,
                json_data=grant_data
            )
        except Exception as ex:
            current_app.logger.error(f"failed in Identifier Grant: {ex}")
            raise WekoWorkflowException("failed in Identifier Grant.") from ex
        finally:
            self._activity_unlock(locked_value)

        if result.json.get("code") != 0:
            current_app.logger.error(f"failed in Identifier Grant: {result.json.get('msg')}")
            raise WekoWorkflowException(result.json.get("msg"))

    def end(self):
        """Reset."""
        self.__init__(
            _lock_skip=self._lock_skip,
            _metadata_inheritance=self._metadata_inheritance,
            _files_inheritance=self._files_inheritance
        )

    def _activity_lock(self):
        """Activity lock.

        Lock the activity to prevent concurrent modifications.

        Returns:
            str: Locked value if successful, None if lock is skipped.

        Raises:
            WekoWorkflowException: If the activity is already locked.
        """
        locked_value = None
        if self._lock_skip:
            return None

        """weko_workflow.views.lock_activity"""
        locked_value, code = lock_activity(self.activity_id)
        if code == 500:
            current_app.logger.error("Activity is already locked.")
            raise WekoWorkflowException("Activity is already locked.")

        return str(locked_value.get_json().get("locked_value"))

    def _activity_unlock(self, locked_value):
        """Activity unlock.

        Unlock the activity after processing is complete.

        Args:
            locked_value (str): The value used to lock the activity.

        Returns:
            str: Message of the unlock response, or None if lock was skipped.
        """
        if self._lock_skip:
            return None

        return delete_lock_activity_cache(
            self.activity_id, {"locked_value":locked_value}
        )
