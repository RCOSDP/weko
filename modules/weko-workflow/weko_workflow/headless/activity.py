# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Workflow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module for weko_workflow headless activity."""

from flask import current_app, url_for

from ..api import Action, WorkActivity
from ..errors import WekoWorkflowException
from ..views import verify_deletion, init_activity

class HeadlessActivity(WorkActivity):
    """Handler of headless activity class."""
    def __init__(self):
        """Initialize."""
        super().__init__()
        self.parms = {}
        self.model = None
        self.detail = ""
        self.lock_skip = False
        pass

    @property
    def activity_id(self):
        """Get activity id."""
        return self.model.activity_id if self.model is not None else None

    @property
    def current_action_id(self):
        """Get current action id."""
        return self.model.action_id if self.model is not None else None

    @property
    def current_action(self):
        """Get current action endpoint."""
        if self.current_action_id is None:
            return None
        return Action().get_action_detail(self.current_action_id).action_endpoint

    def init_activity(
            self, user_id, activity=None, community_id=None,
            activity_id=None, item_id=None
        ):
        """Initialize activity.

        Args:
            activity (dict): Activity info
            user_id (str): User ID
            community_id (str, optional): Community ID
            activity_id (str, optional): Activity ID
            item_id (str, optional): Item ID
        """
        if self.model is not None:
            current_app.logger.error("activity is already initialized.")
            raise WekoWorkflowException("activity is already initialized.")

        if activity_id is not None:
            # restart activity
            result = verify_deletion(activity_id).json
            if result.get("is_delete"):
                current_app.logger.error(f"activity({activity_id}) is already deleted.")
                raise WekoWorkflowException(f"activity({activity_id}) is already deleted.")
            else:
                self.model = super().get_activity_by_id(activity_id)
                if self.model is None:
                    current_app.logger.error(f"activity({activity_id}) is not found.")
                    raise WekoWorkflowException(f"activity({activity_id}) is not found.")

                self.detail = url_for(
                    "weko_workflow.display_activity", activity_id=activity_id
                )
                if self.model.activity_community_id is not None:
                    self.detail = url_for(
                        "weko_workflow.display_activity",
                        activity_id=activity_id,
                        community=self.model.activity_community_id,
                    )
                current_app.logger.info(f"activity({activity_id}) is restarted.")

                self._activity_lock(activity_id)
                self._user_lock(user_id)
            return self.detail

        if (
            activity is None
            or "workflow_id" not in activity
            or "flow_id" not in activity
        ):
            current_app.logger.error("invalid activity info.")
            raise WekoWorkflowException("invalid activity info.")

        if item_id is None:
            # create activity for new item
            result = init_activity(activity, community_id).json

            if result.get("code") == 0:
                self.detail = result.get("redirect")

                activity_id = self.detail.split("/activity/detail/")[1]
                if "?" in activity_id:
                    self.parms.update({community_id: activity_id.split("?")[1]})
                    activity_id = activity_id.split("?")[0]
                self.model = super().get_activity_by_id(activity_id)
            else:
                current_app.logger.error(
                    f"failed to create headless activity: {result.get('msg')}")
                raise WekoWorkflowException(result.get("msg"))

        else:
            # create activity for existing item edit
            """weko_items_ui.views.prepare_edit_item"""
            pass

        self._activity_lock(activity_id)
        self._user_lock(user_id)
        current_app.logger.info(f"activity({activity_id}) is created.")
        return self.detail

    def auto(self, parms):
        """Auto process."""
        self.parms.update(parms)
        self.init_activity(
            self.parms.get("user_id"), self.parms.get("activity"),
            self.parms.get("community_id"), self.parms.get("activity_id"),
            self.parms.get("item_id")
        )
        self.lock_skip = True

        self.item_registration(
            self.parms.get("metadata"), self.parms.get("skip_fulltext"))

        pass

    def item_registration(self, metadata, skip_fulltext=[]):
        """Action for item registration."""
        self.parms.update("skip_fulltext") = skip_fulltext
        pass

    def input_metadata(self, metadata):
        """input metadata."""
        pass

    def upload_files(self, files):
        """upload files."""
        pass

    def designate_index(self, index):
        """Designate index."""
        pass

    def comment(self, comment_data):
        """Set comment."""
        pass

    def item_link(self, link_data):
        """Action for item link."""
        pass

    def identifier_grant(self, grant_data):
        """Action for identifier grant."""
        pass

    def approval(self, approve, reject):
        """Action for approval."""
        pass

    def end(self):
        """Action for end."""
        pass

    def _save(self):
        """Save activity."""
        pass

    def _user_lock(self, user_id):
        """User lock."""
        pass

    def _user_unlock(self, user_id):
        """User unlock."""
        pass

    def _activity_lock(self, activity_id):
        """Activity lock."""
        if not self.lock_skip:
            pass

    def _activity_unlock(self, activity_id):
        """Activity unlock."""
        if not self.lock_skip:
            pass
