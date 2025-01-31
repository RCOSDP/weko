# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Workflow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module for weko_workflow headless activity."""

import os
import uuid
from datetime import datetime
from flask import current_app, url_for

from invenio_files_rest.errors import FileSizeError
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_indexer.api import RecordIndexer
from invenio_pidstore import current_pidstore

from weko_deposit.api import WekoDeposit
from weko_deposit.serializer import file_uploaded_owner
from weko_items_autofill.utils import get_workflow_journal
from weko_items_ui.utils import validate_form_input_data
from weko_items_ui.views import check_validation_error_msg
from weko_records.api import ItemTypes
from weko_records.serializers.utils import get_mapping
from weko_search_ui.utils import get_data_by_property

from ..api import Action, WorkActivity, WorkFlow
from ..errors import WekoWorkflowException
from ..utils import save_activity_data
from ..views import verify_deletion, init_activity, get_feedback_maillist

class HeadlessActivity(WorkActivity):
    """Handler of headless activity class.

    This class is used to handle the activity without UI.
    """
    def __init__(self):
        """Initialize."""
        super().__init__()
        self.params = {}
        self.detail = ""
        self.recid = None
        self.item_type = None
        self.user_id = None
        self.files_info = None
        self._model = None
        self._lock_skip = False

        actions = Action().get_action_list()
        self._actions = {
            f"{action.id}": action.action_endpoint for action in actions
        }

    @property
    def activity_id(self):
        """Get activity id."""
        return self._model.activity_id if self._model is not None else None

    @property
    def current_action_id(self):
        """Get current action id."""
        return self._model.action_id if self._model is not None else None

    @property
    def current_action(self):
        """Get current action endpoint."""
        if self.current_action_id is None:
            return None
        return self._actions.get(self.current_action_id)

    def init_activity(
            self, user_id, workflow_id=None, community_id=None,
            activity_id=None, item_id=None
        ):
        """Initialize activity.

        user_id and workflow_id are required to create a new activity.
        When activity_id is specified, it restarts the activity already exists.
        Additionally, item_id is required when creating an activity
        for an existing item edit.

        Args:
            user_id (int): User ID
            workflow_id (int, optional): Workflow ID
            community_id (str, optional): Community ID
            activity_id (str, optional): Activity ID
            item_id (str, optional): Item ID

        Returns:
            str: Activity detail URL.
        """
        # TODO: check user lock
        """weko_workflow.views.is_user_locked"""

        if self._model is not None:
            current_app.logger.error("activity is already initialized.")
            raise WekoWorkflowException("activity is already initialized.")

        if activity_id is not None:
            # restart activity
            # TODO: check user permission to restart activity
            # it should be equal to "weko_workflow.views.index" without pagenation.

            result = verify_deletion(activity_id).json
            if result.get("is_delete"):
                current_app.logger.error(f"activity({activity_id}) is already deleted.")
                raise WekoWorkflowException(f"activity({activity_id}) is already deleted.")
            else:
                self._model = super().get_activity_by_id(activity_id)
                if self._model is None:
                    current_app.logger.error(f"activity({activity_id}) is not found.")
                    raise WekoWorkflowException(f"activity({activity_id}) is not found.")

                self.detail = url_for(
                    "weko_workflow.display_activity", activity_id=activity_id
                )
                if self._model.activity_community_id is not None:
                    self.detail = url_for(
                        "weko_workflow.display_activity",
                        activity_id=activity_id,
                        community=self._model.activity_community_id,
                    )
                current_app.logger.info(f"activity({activity_id}) is restarted.")

                self.user_id = user_id
            return self.detail

        if "workflow_id" is None:
            current_app.logger.error("workflow_id is required to create activity.")
            raise WekoWorkflowException("workflow_id is required to create activity.")
        workflow = WorkFlow().get_workflow_by_id(workflow_id)
        self.item_type = ItemTypes.get_by_id(workflow.itemtype_id)
        activity = {
        "flow_id": workflow.flow_id,
        "workflow_id": workflow.id,
        "itemtype_id": workflow.itemtype_id,
        }

        if item_id is None:
            # create activity for new item
            activity.update("activity_login_user") = user_id
            result = init_activity(activity, community_id).json

            if result.get("code") == 0:
                self.detail = result.get("redirect")

                activity_id = self.detail.split("/activity/detail/")[1]
                if "?" in activity_id:
                    self.params.update({community_id: activity_id.split("?")[1]})
                    activity_id = activity_id.split("?")[0]
                self._model = super().get_activity_by_id(activity_id)
            else:
                current_app.logger.error(
                    f"failed to create headless activity: {result.get('msg')}")
                raise WekoWorkflowException(result.get("msg"))

        else:
            # create activity for existing item edit
            """ TODO: weko_items_ui.views.prepare_edit_item"""
            pass

        self.user_id = user_id
        current_app.logger.info(f"activity({activity_id}) is created.")
        return self.detail

    def auto(self, **params):
        """Auto process."""
        self.params.update(params)

        self.init_activity(
            self.params.get("user_id"), self.params.get("workflow_id"),
            self.params.get("community_id"), self.params.get("activity_id"),
            self.params.get("item_id")
        )

        self._lock_skip = False
        self._user_lock()
        locked_value = self._activity_lock()
        self._lock_skip = True

        # 動的に次のアクションを取得して実行できるようにする

        self._lock_skip = False
        self._activity_unlock(locked_value)
        self._user_unlock()

        returns = (self.detail, self.current_action, self.recid)

        self.end()

        return returns

    def item_registration(self, metadata, files, index, comment=""):
        """Action for item registration."""
        if self._model is None:
            current_app.logger.error("activity is not initialized.")
            raise WekoWorkflowException("activity is not initialized.")

        error = check_validation_error_msg(self.activity_id).json
        if error.pop("code") == 1:
            current_app.logger.error(f"failed to input metadata: {error}")
            # TODO: make message more easy to understand
            # it contains ""
            raise WekoWorkflowException(error)

        self.recid = self._input_metadata(metadata, files)
        self._designate_index(index)
        self._comment(comment)

        return self.detail


    def _input_metadata(self, metadata, files):
        """input metadata."""
        self._user_lock()
        locked_value = self._activity_lock()

        # TODO: metadata input assist (W-OA-06 2.2)

        metadata.setdefault("pubdate") = datetime.now().strftime("%Y-%m-%d")

        # grouplist = Group.get_group_list()
        # authors_prefix_settings = get_data_authors_prefix_settings()
        journal = get_workflow_journal(self.activity_id)

        # update feedback mail list
        feedback_maillist = get_feedback_maillist(self.activity_id).json
        feedback_maillist.append(metadata.pop("feedback_mail_list", []))
        self.create_or_update_action_feedbackmail(
            activity_id=self.activity_id,
            action_id=self.current_action_id,
            feedback_maillist=feedback_maillist
        )

        # get value of "Title" from metadata by jpcoar_mapping
        item_map = get_mapping(self.item_type.id, 'jpcoar_mapping', self.item_type)
        title_value_key = "title.@value"
        title, _ = get_data_by_property(metadata, item_map, title_value_key)
        save_activity_data({
            "activity_id": self.activity_id,
            "title": title,
            "shared_user_id": metadata.get("shared_user_id")
        })

        record_data = {}
        record_uuid = uuid.uuid4()
        pid = current_pidstore.minters["weko_deposit_minter"](record_uuid, data=record_data)
        self._deposit = WekoDeposit.create(record_data, id_=record_uuid)

        # TODO: update propaties of files metadata, but it is difficult to
        # decide whitch key should be updated.
        metadata["files"] = self.files_info = self._upload_files(files)

        result = {"is_valid": True}
        validate_form_input_data(result, self.item_type.id, metadata)
        if not result.get("is_valid"):
            current_app.logger.error(f"failed to input metadata: {result.get("error")}")
            raise WekoWorkflowException(result.get("error"))


        self._user_unlock()
        self._activity_unlock(locked_value)

        return pid

    def _upload_files(self, files):
        """upload files."""

        RecordIndexer().index(self._deposit)
        bucket = Bucket.query.get(self._deposit["_buckets"]["deposit"])

        files_info = []
        # [{"key": basename, "uri": False, "progress": 100, ...}]

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

            return {
                "tags": {},
                "created": obj.created.isoformat(),
                "updated": obj.updated.isoformat(),
                "filename": obj.basename,
                "key": obj.basename,
                "links": {
                    "sefl": url_for(),
                    "version": url_for(),
                    "uploads": url_for()
                },
                "size": obj.file.size,
                "checksum": obj.file.checksum,
                "mimetype": obj.mimetype,
                "delete_marker": obj.deleted,
                "is_head": True,
                "is_thumbnail": obj.is_thumbnail,
                **file_uploaded_owner(
                    created_user_id=obj.created_user_id,
                    updated_user_id=obj.updated_user_id
                ),
                "created_user_id": obj.created_user_id,
                "updated_user_id": obj.updated_user_id,
                "is_show": obj.is_show,
                "version_id": str(obj.version_id),
                "uri": False,
                "multiple": False,
                "progress": 100,
                "cmonplete": True,
            }

        for file in files:
            if isinstance(file, str):
                if not os.path.isfile(file):
                    current_app.logger.error(f"file({file}) is not found.")
                    raise WekoWorkflowException(f"file({file}) is not found.")
                size = os.path.getsize(file)
                with open(file, "rb") as f:
                    file_info = upload(os.path.basename(file), f, size)
            else:
                """werkzeug.datastructures.FileStorage"""
                file_info = upload(file.filename, file.stream, file.content_length)
            files_info.append(file_info)

        return files_info

    def _designate_index(self, index):
        """Designate index."""
        self._user_lock()
        locked_value = self._activity_lock()


        self._user_unlock()
        self._activity_unlock(locked_value)

    def _comment(self, comment):
        """Set comment."""
        self._user_lock()
        locked_value = self._activity_lock()


        self._user_unlock()
        self._activity_unlock(locked_value)

    def item_link(self, link_data):
        """Action for item link."""
        self._user_lock()
        locked_value = self._activity_lock()


        self._user_unlock()
        self._activity_unlock(locked_value)

    def identifier_grant(self, grant_data):
        """Action for identifier grant."""
        self._user_lock()
        locked_value = self._activity_lock()


        self._user_unlock()
        self._activity_unlock(locked_value)

    def approval(self, approve, reject):
        """Action for approval."""
        self._user_lock()
        locked_value = self._activity_lock()


        self._user_unlock()
        self._activity_unlock(locked_value)

    def end(self):
        """Action for end."""
        self.params = {}
        self._model = None
        self.detail = ""
        self.user_id = None
        pass

    def _save_activity(self):
        """Save activity."""
        pass

    def _user_lock(self):
        """User lock."""
        if not self._lock_skip:
            pass

    def _user_unlock(self):
        """User unlock."""
        if not self._lock_skip:
            pass

    def _activity_lock(self):
        """Activity lock."""
        locked_value = None
        if not self._lock_skip:
            pass

        return locked_value

    def _activity_unlock(self, locked_value):
        """Activity unlock."""
        if not self._lock_skip:
            pass
