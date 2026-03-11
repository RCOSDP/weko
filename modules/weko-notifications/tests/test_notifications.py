# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

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

    # def __eq__(self, other):
    # .tox/c1/bin/pytest --cov=weko_notifications tests/test_notifications.py::TestNotifications::test__eq__ -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
    def test__eq__(self, json_notifications):
        after_approval = json_notifications["after_approval"]
        offer_approval = json_notifications["offer_approval"]
        notification = Notification().load(after_approval)
        notification2 = Notification().load(after_approval)
        notification3 = Notification().load(offer_approval)

        assert notification == notification2
        assert notification != notification3

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
        after_registration = json_notifications["after_registration"]
        after_registration.pop("id")

        notification = Notification.create_item_registered(
            target_id=3,
            actor_id=3,
            object_id=2000001,
            object_name="A new record",
            actor_name="Alex",
            ietf_cite_as="https://doi.org/10.34477/0002000001"
        )

        assert notification.payload.pop("id") is not None
        assert notification.payload.pop("updated") is not None
        assert notification.payload["@context"] == COAR_NOTIFY_CONTEXT
        assert notification.activity_type == ActivityType.ANNOUNCE_INGEST.value
        assert notification.payload == after_registration
        assert notification._is_validated == True

    # def create_request_approval(cls, target_id, object_id, actor_id, context_id, **kwargs):
    # .tox/c1/bin/pytest --cov=weko_notifications tests/test_notifications.py::TestNotifications::test_create_request_approval -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
    def test_create_request_approval(self, app, json_notifications):
        offer_approval = json_notifications["offer_approval"]
        offer_approval.pop("id")

        notification = Notification.create_request_approval(
            target_id=1,
            actor_id=3,
            object_id=2000001,
            object_name="A new record",
            context_id="A-20250306-00001",
            actor_name="Alex"
        )

        assert notification.payload.pop("id") is not None
        assert notification.payload.pop("updated") is not None
        assert notification.payload["@context"] == COAR_NOTIFY_CONTEXT
        assert notification.activity_type == ActivityType.OFFER_ENDORSE.value
        assert notification.payload == offer_approval
        assert notification._is_validated == True

    # def create_item_approved(cls, target_id, object_id, actor_id, context_id, **kwargs):
    # .tox/c1/bin/pytest --cov=weko_notifications tests/test_notifications.py::TestNotifications::test_create_item_approved -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
    def test_create_item_approved(self, app, json_notifications):
        after_approval = json_notifications["after_approval"]
        after_approval.pop("id")
        after_approval.pop("inReplyTo")

        notification = Notification.create_item_approved(
            target_id=3,
            actor_id=1,
            object_id=2000001,
            object_name="A new record",
            context_id="A-20250306-00001",
            actor_name="Admin",
            ietf_cite_as="https://doi.org/10.34477/0002000001"
        )

        assert notification.payload.pop("id") is not None
        assert notification.payload.pop("updated") is not None
        assert notification.payload["@context"] == COAR_NOTIFY_CONTEXT
        assert notification.activity_type == ActivityType.ANNOUNCE_ENDORSE.value
        assert notification.payload == after_approval
        assert notification._is_validated == True

    # def create_item_rejected(cls, target_id, object_id, actor_id, context_id, **kwargs):
    # .tox/c1/bin/pytest --cov=weko_notifications tests/test_notifications.py::TestNotifications::test_create_item_rejected -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
    def test_create_item_rejected(self, app, json_notifications):
        after_rejection = json_notifications["after_rejection"]
        after_rejection.pop("id")
        after_rejection.pop("inReplyTo")

        notification = Notification.create_item_rejected(
            target_id=3,
            actor_id=1,
            object_id=2000001,
            object_name="A new record",
            context_id="A-20250306-00001",
            actor_name="Admin"
        )

        assert notification.payload.pop("id") is not None
        assert notification.payload.pop("updated") is not None
        assert notification.payload["@context"] == COAR_NOTIFY_CONTEXT
        assert notification.activity_type == ActivityType.ACKNOWLEDGE_AND_REJECT.value
        assert notification.payload == after_rejection
        assert notification._is_validated == True
