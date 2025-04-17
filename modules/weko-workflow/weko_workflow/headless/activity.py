# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Workflow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module for weko_workflow headless activity."""

import os
import json
import uuid
from copy import deepcopy
from datetime import datetime
from flask import current_app, url_for, request

from invenio_accounts.models import User
from invenio_cache import current_cache
from invenio_db import db
from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_indexer.api import RecordIndexer
from invenio_pidstore import current_pidstore
from invenio_pidstore.models import PersistentIdentifier

from weko_deposit.api import WekoDeposit
from weko_deposit.links import base_factory
from weko_deposit.serializer import file_uploaded_owner
from weko_items_autofill.utils import get_workflow_journal
from weko_items_ui.utils import (
    update_index_tree_for_record, validate_form_input_data, to_files_js
)
from weko_items_ui.views import (
    check_validation_error_msg, prepare_edit_item, prepare_delete_item
)
from weko_records.api import ItemTypes, ItemsMetadata
from weko_records.serializers.utils import get_mapping
from weko_records_ui.utils import soft_delete
from weko_search_ui.utils import get_data_by_property

from ..api import Action, WorkActivity, WorkFlow, ActivityStatusPolicy
from ..errors import WekoWorkflowException
from ..utils import (
    check_authority_by_admin,
    delete_lock_activity_cache,
    delete_user_lock_activity_cache,
    get_identifier_setting,
    update_cache_data
)
from ..views import (
    next_action,
    verify_deletion,
    init_activity,
    get_feedback_maillist,
    lock_activity
)

class HeadlessActivity(WorkActivity):
    """Handler of headless activity class.

    This class is used to handle the activity without UI. <br>
    Recommended to use `auto` method to automatically progress the action. <br>
    If you want to progress the action manually, use each method, such as
    `item_registration`, `item_link`, `identifier_grant`, `approval`. <br>
    But, this is not recommended because the order of actions is different for each flow.


    Examples:

    >>> headless = HeadlessActivity()
    >>> url, current_action, recid = headless.auto(
    ...     user_id=1, workflow_id=1,
    ...     metadata={"pubdate": "2025-01-01", "item_30001_title0": {...}, ...},
    ...     files=["/var/tmp/..."], index=[1623632832836],
    ...     comment="comment", link_data=[{"item_id": 1, "sele_id": "isVersionOf"}],
    ... )
    >>> print(url, current_action, recid)
    http://weko3.example.org/workflow/activity/detail/A-EXAMPLE-0001 end_action 1
    """
    def __init__(
            self, _lock_skip=True, _metadata_replace=True, _files_replace=True
        ):
        """Initialize.

        Args:
            _lock_skip (bool, optional): Defaults to True.
                if True, skip user and activity lock and unlock process.
        """
        super().__init__()
        self.user = None
        """ User: User model """
        self.item_type = None
        """ ItemType: Item type model """
        self.recid = None
        """ int: Record ID """
        self.files_info = None
        """ list: List of file information """
        self._model = None
        self._deposit = None
        self._lock_skip = _lock_skip
        self._metadata_replace = _metadata_replace
        self._files_replace= _files_replace

        actions = Action().get_action_list()
        self._actions = {
            action.id: action.action_endpoint for action in actions
        }

    @property
    def activity_id(self):
        """str: activity id."""
        return self._model.activity_id if self._model is not None else None

    @property
    def current_action_id(self):
        """int: current action id."""
        return self._model.action_id if self._model is not None else None

    @property
    def current_action(self):
        """str: current action endpoint.

        It can be `begin_action`, `login_item`, `link_item`, `identifier_grant`,
        `approval` or `end_action`.
        """
        return self._actions.get(self.current_action_id) if self._model is not None else None

    @property
    def community(self):
        """str: community id."""
        return self._model.activity_community_id if self._model is not None else None

    @property
    def detail(self):
        """str: activity detail URL."""
        return url_for(
            "weko_workflow.display_activity",
            activity_id=self.activity_id, community=self.community,
            _external=True
        ) if self._model is not None else ""

    def init_activity(self, user_id, **kwargs):
        """Manual initialization of activity.

        Note:
            Please use `auto` method to automatically progress the action.

        user_id and workflow_id are required to create a new activity. <br>
        When activity_id is specified, it restarts the activity already exists. <br>
        Additionally, item_id is required when creating an activity
        for an existing item edit.

        Args:
            user_id (int): User ID
            workflow_id (int, optional): Workflow ID
            community (str, optional): Community ID
            activity_id (str, optional): Activity ID
            item_id (str, optional): Item ID
            for_delete (bool, optional):
                Flag to create activity for delete item. Defaults to False.

        Returns:
            str: Activity detail URL.
        """
        if self._model is not None:
            current_app.logger.error("activity is already initialized.")
            raise WekoWorkflowException("activity is already initialized.")

        activity_id = kwargs.get("activity_id")
        if activity_id is not None:
            result = verify_deletion(activity_id).json
            if result.get("is_delete"):
                current_app.logger.error(f"activity({activity_id}) is already deleted.")
                raise WekoWorkflowException(f"activity({activity_id}) is already deleted.")

            self._model = super().get_activity_by_id(activity_id)
            if self._model is None:
                current_app.logger.error(f"activity({activity_id}) is not found.")
                raise WekoWorkflowException(f"activity({activity_id}) is not found.")

            # check user permission
            user = User.query.get(user_id)
            if (
                self._model.activity_login_user != user_id
                    and self._model.shared_user_id != user_id
                    and not check_authority_by_admin(self.activity_id, user)
            ):
                current_app.logger.error(
                    f"user({user_id}) cannot restart activity({activity_id}).")
                raise WekoWorkflowException(
                    f"user({user_id}) cannot restart activity({activity_id}).")

            locked_value = self._activity_lock()
            current_app.logger.info(
                f"activity({self.activity_id}) is restarted by user({user_id}).")
            self.user = user
            self._activity_unlock(locked_value)
            return self.detail

        item_id = kwargs.get("item_id")
        community = kwargs.get("community")
        if item_id is not None:
            # edit or delete item
            if not kwargs.get("for_delete", False):
                response = prepare_edit_item(item_id, community)
            else:
                response = prepare_delete_item(item_id, community)

            if response.json.get("code") != 0:
                current_app.logger.error(
                    f"failed to create activity: {response.json.get('msg')}")
                raise WekoWorkflowException(response.json.get("msg"))

            url = response.json.get("data").get("redirect")
            activity_id = url.split("/activity/detail/")[1]
            if "?" in activity_id:
                activity_id = activity_id.split("?")[0]

            self.recid = item_id
            self._model = super().get_activity_by_id(activity_id)
            self.workflow = self._model.workflow
            self.item_type = ItemTypes.get_by_id(self.workflow.itemtype_id)

        else:
            workflow_id = kwargs.get("workflow_id")
            if workflow_id is None:
                current_app.logger.error("workflow_id is required to create activity.")
                raise WekoWorkflowException("workflow_id is required to create activity.")

            # create activity for new item
            self.workflow = workflow = WorkFlow().get_workflow_by_id(workflow_id)
            if workflow is None:
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
            self._model = super().get_activity_by_id(activity_id)

        self.user = User.query.get(user_id)
        current_app.logger.info(
            f"activity({activity_id}) is created by user({user_id}).")
        return self.detail

    def auto(self, **params):
        """Automatically progressing the action.

        Args:
            user_id (int): User ID <br>
            workflow_id (int): Workflow ID <br>
            community (str, optional): Community ID <br>
            activity_id (str, optional): Activity ID <br>
            item_id (str, optional): Item ID <br>
            metadata (dict): Metadata with item type format <br>
            files (list, optional): List of temporary file avsolute path <br>
            index (list, optional): List of index ID <br>
            comment (str, optional): Comment <br>
            link_data (list, optional): List of item link information <br>
                e.g. [{"item_id": 1, "sele_id": "isVersionOf"}] <br>
            grant_data (dict): data for identifier grant <br>
        """

        self.init_activity(**params)

        # skip locks temporarily even if skip flag is not True
        _lf = self._lock_skip
        self._user_lock()
        locked_value = self._activity_lock()
        self._lock_skip = True

        # automatically progressing the action
        while self.current_action not in {"end_action", "approval"}:
            if self.current_action == "item_login":
                self.item_registration(
                    params.get("metadata"), params.get("files"),
                    params.get("index"), params.get("comment"),
                    params.get("non_extract"),
                    params.get("workspace_register")
                )
            elif self.current_action == "item_link":
                self.item_link(params.get("link_data"))
            elif self.current_action == "identifier_grant":
                self.identifier_grant(params.get("grant_data"))
            elif self.current_action == "oa_policy":
                self.oa_policy(params.get("policy"))

        self._lock_skip = _lf
        self._activity_unlock(locked_value)
        self._user_unlock()

        returns = (self.detail, self.current_action, self.recid)

        self.end()

        return returns


    def item_registration(
            self, metadata, files=None, index=None, comment=None, non_extract=None, workspace_register=None):
        """Manual action for item registration.

        Note:
            Please use `auto` method to automatically progress the action.

        Args:
            metadata (dict): Metadata with item type format
            files (list, optional): List of temporary file avsolute path
            index (list, optional): List of index ID.
                if use workflow setting, do not specify this parameter.
            comment (str, optional): Comment
        """
        if self._model is None:
            current_app.logger.error("activity is not initialized.")
            raise WekoWorkflowException("activity is not initialized.")

        # some error had occurred in idnentifier_grant if not enough metadata.
        error = check_validation_error_msg(self.activity_id).json
        if error.pop("code") == 1:
            current_app.logger.error(f"failed to input metadata: {error}")
            # TODO: make message more easy to understand
            # it contains ""
            raise WekoWorkflowException(error)

        self.recid = self._input_metadata(metadata, files, non_extract, workspace_register)
        self._designate_index(index)
        self._comment(comment)

        return self.detail


    def _input_metadata(self, metadata, files=None, non_extract=None, workspace_register=None):
        """input metadata."""
        locked_value = self._activity_lock()

        try:
            metadata.setdefault("pubdate", datetime.now().strftime("%Y-%m-%d"))
            feedback_maillist = metadata.pop("feedback_mail_list", [])
            self.create_or_update_action_feedbackmail(
                activity_id=self.activity_id,
                action_id=self.current_action_id,
                feedback_maillist=feedback_maillist
            )

            from weko_search_ui.utils import get_data_by_property
            # get value of "Title" from metadata by jpcoar_mapping
            item_map = get_mapping(self.item_type.id, "jpcoar_mapping", self.item_type)
            title_value_key = "title.@value"
            title, _ = get_data_by_property(metadata, item_map, title_value_key)
            weko_shared_id = metadata.get("weko_shared_id", -1)
            shared_user_id = metadata.get("shared_user_id", -1)

            self.update_activity(self.activity_id, {
                "title": title[0] if len(title) > 0 else "",
                "shared_user_id": weko_shared_id
                    if shared_user_id == -1 else shared_user_id
            })

            result = {"is_valid": True}
            validate_form_input_data(result, self.item_type.id, deepcopy(metadata))
            if not result.get("is_valid"):
                current_app.logger.error(f"failed to input metadata: {result.get('error')}")
                raise WekoWorkflowException(result.get("error"))

            _old_metadata, _old_files = {}, []
            if self.recid is None:
                record_data = {}
                record_uuid = uuid.uuid4()
                pid = current_pidstore.minters["weko_deposit_minter"](record_uuid, data=record_data)
                self._deposit = WekoDeposit.create(record_data, id_=record_uuid)
                self._model.item_id = record_uuid
                db.session.commit()

            else:
                record_uuid = self._model.item_id
                pid = PersistentIdentifier.query.filter_by(
                        pid_type="recid", object_uuid=record_uuid
                    ).first()
                self._deposit = WekoDeposit.get_record(record_uuid)
                # if status == "upgrade":
                #     self._deposit = self._deposit.newversion(pid)

                # get old metadata by record_uuid
                _old_metadata = ItemsMetadata.get_by_object_id(record_uuid).json
                _old_files = to_files_js(self._deposit)
                db.session.commit()

            if not self._metadata_replace:
                # update old metadata partially
                metadata = {**_old_metadata, **metadata}
            # if metadata_replace is True, replace all metadata
            metadata.update({"$schema": f"/items/jsonschema/{self.item_type.id}"})

            data = {
                "metainfo": metadata,
                "files": [],
                "endpoint": {
                    "initialization": f"/api/deposits/redirect/{pid}",
                }
            }

            # TODO: update submited files and reuse other files
            if self._files_replace:
                data["files"] = self.files_info = self._upload_files(files)
            else:
                _new_files = self._upload_files(files)
                old_files_dict = {file["key"]: file for file in _old_files}
                for new_file in _new_files:
                    old_files_dict[new_file["key"]] = new_file
                data["files"] = self.files_info = list(old_files_dict.values())

            # to exclude from file text extraction
            for file in data["files"]:
                if isinstance(non_extract, list) and file["filename"] in non_extract:
                    file["non_extract"] = True
      
            if workspace_register and data["files"]:
                data_without_outer_list = data["files"][0]
                data["files"] = data_without_outer_list

            data["endpoint"].update(base_factory(pid))
            self.upt_activity_metadata(self.activity_id, json.dumps(data))

            # designate_index
            workflow_index = self.workflow.index_tree_id
            list_index =  (
                [workflow_index]
                if workflow_index is not None else metadata.get("path", [])
            )
            if not isinstance(list_index, list) or not list_index:
                raise Exception(
                    "Index is not specified in workflow or item metadata."
                )

            index = {
                "index": list_index,
                "actions": metadata.get("publish_status")
            }
            self._deposit.update(index, metadata)
            self._deposit.commit()
        except Exception as ex:
            msg = f"Failed to input metadata to deposit: {ex}"
            current_app.logger.error(msg)
            raise WekoWorkflowException(msg) from ex
        finally:
            self._activity_unlock(locked_value)

        return pid.pid_value

    def _upload_files(self, files=None):
        """upload files."""
        files = files or []
        bucket = Bucket.query.get(self._deposit["_buckets"]["deposit"])
        files_info = []

        def upload(file_name, stream, size):
            size_limit = bucket.size_limit
            location_limit = bucket.location.max_file_size
            if location_limit is not None:
                size_limit = min(size_limit, location_limit)
            if location_limit and size_limit and size > size_limit:
                desc = (
                    "File size limit exceeded."
                    if isinstance(size_limit, int)
                    else size_limit.reason
                )
                current_app.logger.error(desc)
                raise FileSizeError(description=desc)

            # TODO: support thumbnail
            obj = ObjectVersion.create(bucket, file_name, is_thumbnail=False)
            obj.set_contents(stream, size=size, size_limit=size_limit)
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
                "cmonplete": True,
                "version_id": str(obj.version_id),
            }

        for file in files:
            if isinstance(file, str):
                if not os.path.isfile(file):
                    current_app.logger.error(f"file({file}) is not found.")
                    raise WekoWorkflowException(f"file({file}) is not found.")
                size = os.path.getsize(file)
                with open(file, "rb") as f:
                    file_info = upload(os.path.basename(file), f, size)
            elif isinstance(file, dict):
                file_info = files
            else:
                """werkzeug.datastructures.FileStorage"""

                file.seek(0, 2)
                file_size = file.tell()
                file.seek(0)
                file_info = upload(file.filename, file.stream, file_size)
            files_info.append(file_info)

        return files_info

    def _designate_index(self, index=None):
        """Designate Index.

        Args:
            index (list): list of index identifier.
        """
        locked_value = self._activity_lock()

        index = index or self.workflow.index_tree_id

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
                self.activity_id, self.current_action_id, {"commond": comment}
            )
        except Exception as ex:
            current_app.logger.error(f"failed to set comment: {ex}")
            raise WekoWorkflowException("failed to set comment.") from ex
        finally:
            self._activity_unlock(locked_value)

        if result.json.get("code") != 0:
            current_app.logger.error(f"failed to set comment: {result.json.get('msg')}")
            raise WekoWorkflowException(result.json.get("msg"))

    def item_link(self, link_data=None):
        """Action for Item Link."""
        link_data = link_data or []
        locked_value = self._activity_lock()

        try:
            result, _ = next_action(
                self.activity_id, self.current_action_id, {"link_data": link_data}
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
        """Action for Identifier Grant."""
        locked_value = self._activity_lock()

        grant_data = grant_data or {}
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
                self.activity_id, self.current_action_id, grant_data
            )
        except Exception as ex:
            current_app.logger.error(f"failed in Identifier Grant: {ex}")
            raise WekoWorkflowException("failed in Identifier Grant.") from ex
        finally:
            self._activity_unlock(locked_value)

        if result.json.get("code") != 0:
            current_app.logger.error(f"failed in Identifier Grant: {result.json.get('msg')}")
            raise WekoWorkflowException(result.json.get("msg"))

    def approval(self, approve, reject):
        """Action for Approval."""
        locked_value = self._activity_lock()

        try:
            # TODO:
            pass
        except Exception as ex:
            current_app.logger.error(f"failed in Approval: {ex}")
            raise WekoWorkflowException("failed in Approval.") from ex
        finally:
            self._activity_unlock(locked_value)

    def oa_policy(self, policy):
        """Action for OA Policy Confirmation."""
        locked_value = self._activity_lock()

        try:
            # TODO:
            pass
        except Exception as ex:
            current_app.logger.error(f"failed in OA Policy Confirmation: {ex}")
            raise WekoWorkflowException("failed in OA Policy Confirmation.") from ex
        finally:
            self._activity_unlock(locked_value)

    def end(self):
        """Action for End."""
        self.user = None
        self.item_type = None
        self.recid = None
        self.files_info = None
        self._model = None
        self._deposit = None
        self._lock_skip = None

    def _user_lock(self):
        """User lock."""
        if self._lock_skip:
            return

        """weko_workflow.views.user_lock_activity"""
        cache_key = f"workflow_userlock_activity_{self.user.id}"
        timeout = current_app.permanent_session_lifetime.seconds
        cur_locked_val = str(current_cache.get(cache_key) or str()) or str()
        message = ""
        if cur_locked_val:
            message = "Opened"
        else:
            work_activity = WorkActivity()
            act = work_activity.get_activity_by_id(self.activity_id)
            if (act is None
                or act.activity_status in [
                    ActivityStatusPolicy.ACTIVITY_BEGIN,
                    ActivityStatusPolicy.ACTIVITY_MAKING
            ]):
                update_cache_data(
                    cache_key,
                    self.activity_id,
                    timeout
                )
            message = "Locked"

        return message

    def _user_unlock(self, data=None):
        """User unlock."""
        if self._lock_skip:
            return
        data = data or {"is_opened": False , "is_force" : False}
        return delete_user_lock_activity_cache(self.activity_id, data)

    def _activity_lock(self):
        """Activity lock."""
        locked_value = None
        if self._lock_skip:
            return None

        """weko_workflow.views.lock_activity"""
        locked_value, code = lock_activity(self.activity_id)
        if code == 500:
            current_app.logger.error("Activity is already locked.")
            raise WekoWorkflowException("Activity is already locked.")

        return locked_value.get_json().get("locked_value")

    def _activity_unlock(self, locked_value):
        """Activity unlock."""
        if self._lock_skip:
            return None

        return delete_lock_activity_cache(
            self.activity_id, {"locked_value":locked_value})
