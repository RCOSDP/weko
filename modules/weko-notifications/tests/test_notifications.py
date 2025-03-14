# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import pytest
from unittest.mock import patch
from marshmallow import ValidationError

from weko_notifications.config import COAR_NOTIFY_CONTEXT
from weko_notifications.notifications import Notification, ActivityType

# .tox/c1/bin/pytest --cov=weko_notifications tests/test_notifications.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace

# class TestNotifications:
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_notifications.py::TestNotifications -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
class TestNotifications:
    # def __init__(self):
    # .tox/c1/bin/pytest --cov=weko_notifications tests/test_notifications.py::TestNotifications::test__init__ -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
    def test__init__(self):
        notification = Notification()
        assert notification.activity_type == None
        assert notification.origin == {}
        assert notification.target == {}
        assert notification.object == {}
        assert notification.actor == {}
        assert notification.context == {}
        assert notification.in_reply_to == None
        assert notification.payload == {}
        assert notification._is_validated == False

    # def body(self):
    # .tox/c1/bin/pytest --cov=weko_notifications tests/test_notifications.py::TestNotifications::test_current_body -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
    def test_current_body(self, json_notifications):
        after_approval = json_notifications["after_approval"]
        notification = Notification()
        notification.payload["id"] = after_approval["id"]
        notification.activity_type = after_approval["type"]
        notification.origin = after_approval["origin"]
        notification.target = after_approval["target"]
        notification.object = after_approval["object"]
        notification.actor = after_approval["actor"]
        notification.context = after_approval["context"]
        notification.in_reply_to = after_approval["inReplyTo"]

        assert notification.current_body == after_approval

    # def __str__(self):
    # .tox/c1/bin/pytest --cov=weko_notifications tests/test_notifications.py::TestNotifications::test__str__ -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
    def test__str__(self, json_notifications):
        after_approval = json_notifications["after_approval"]
        notification = Notification()
        notification.payload["id"] = after_approval["id"]
        notification.activity_type = after_approval["type"]
        notification.origin = after_approval["origin"]
        notification.target = after_approval["target"]
        notification.object = after_approval["object"]
        notification.actor = after_approval["actor"]
        notification.context = after_approval["context"]
        notification.in_reply_to = after_approval["inReplyTo"]

        result = str(notification)
        assert result == str(notification.current_body)
        assert len(result) == len(str(after_approval))

        assert str(after_approval["id"]) in result

    # def create(self):
    # .tox/c1/bin/pytest --cov=weko_notifications tests/test_notifications.py::TestNotifications::test_create -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
    def test_create(self, json_notifications):
        after_approval = json_notifications["after_approval"]
        notification = Notification()
        notification.payload["id"] = after_approval["id"]
        notification.activity_type = after_approval["type"]
        notification.origin = after_approval["origin"]
        notification.target = after_approval["target"]
        notification.object = after_approval["object"]
        notification.actor = after_approval["actor"]
        notification.context = after_approval["context"]
        notification.in_reply_to = after_approval["inReplyTo"]

        notification.create()

        assert notification.payload.pop("updated") is not None
        assert notification.payload == after_approval
        assert notification._is_validated == True

    # def load(self, payload):
    # .tox/c1/bin/pytest --cov=weko_notifications tests/test_notifications.py::TestNotifications::test_load -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
    def test_load(self, json_notifications):
        after_approval = json_notifications["after_approval"]
        notification = Notification().load(after_approval)

        assert notification.payload.pop("updated") is not None
        assert notification.payload == after_approval
        assert notification._is_validated == True

    # def create_item_registared(cls, target_id, actor_id, object_id, **kwargs):
    # .tox/c1/bin/pytest --cov=weko_notifications tests/test_notifications.py::TestNotifications::test_create_item_registared -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
    def test_create_item_registared(self, app, json_notifications):
        notification = Notification.create_item_registared(
            target_id=3,
            actor_id=3,
            object_id=2000001,
            object_name="Test item",
            actor_name="Alex",
        )
        assert notification.id is not None
        assert notification.updated is not None
        assert notification.payload["@context"] == COAR_NOTIFY_CONTEXT
        assert notification.activity_type == ActivityType.ANNOUNCE_INGEST.value
        assert notification.origin == {
            "id": app.config["THEME_SITEURL"],
            "inbox": app.config["THEME_SITEURL"] + "/inbox",
            "type": "Service",
            }
        assert notification.target == {
            "id": app.config["THEME_SITEURL"] + "/user/3",
            "inbox": app.config["THEME_SITEURL"] + "/inbox",
            "type": "Person",
            }
        assert notification.object == {
            "id": app.config["THEME_SITEURL"] + "/records/2000001",
            "object": None,
            "type": ["Page", "sorg:WebPage"],
            "name": "Test item",
            "url": None,
            "ietf:cite-as": None
            }
        assert notification.actor == {
            "id": app.config["THEME_SITEURL"] + "/user/3",
            "type": "Person",
            "name": "Alex",
            }
        assert notification.context == {}
        assert notification.in_reply_to is None
        assert notification._is_validated == True
