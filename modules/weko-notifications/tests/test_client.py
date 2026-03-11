# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import pytest
from unittest.mock import patch

from weko_notifications.client import NotificationClient
from weko_notifications.notifications import Notification

# .tox/c1/bin/pytest --cov=weko_notifications tests/test_client.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace

# class NotificationClient:
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_client.py::TestNotificationClient -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-tr
class TestNotificationClient:
    # def __init__(self):
    # .tox/c1/bin/pytest --cov=weko_notifications tests/test_client.py::TestNotificationClient::test__init__ -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
    def test__init__(self):
        inbox = "http://localhost/inbox"
        client = NotificationClient(inbox)
        assert client.inbox == inbox

    # def send(self, notification):
    # .tox/c1/bin/pytest --cov=weko_notifications tests/test_client.py::TestNotificationClient::test_send -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
    def test_send(self, json_notifications):
        inbox = "http://localhost/inbox"
        client = NotificationClient(inbox)
        after_approval = json_notifications["after_approval"]

        with patch("weko_notifications.client.ldnlib.Sender") as mock_sender:
            notification = Notification().load(after_approval)
            mock_sender.return_value.send.return_value = None

            client.send(notification)
            mock_sender.assert_called_once()
            mock_sender.return_value.send.assert_called_once_with(inbox, notification.payload)

    # def send(self, notification):
    # .tox/c1/bin/pytest --cov=weko_notifications tests/test_client.py::TestNotificationClient::test_send_actually -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
    @pytest.mark.skip(reason="This test actually sends to the inbox.")
    def test_send_actually(self, json_notifications):
        inbox = "http://inbox:8080/inbox"
        client = NotificationClient(inbox)
        after_approval = json_notifications["after_approval"]
        after_approval.pop("id")
        notification = Notification().load(after_approval)

        client.send(notification)

    # def notifications(self):
    # .tox/c1/bin/pytest --cov=weko_notifications tests/test_client.py::TestNotificationClient::test_notifications -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
    def test_notifications(self):
        inbox = "http://localhost/inbox"
        client = NotificationClient(inbox)
        with patch("weko_notifications.client.ldnlib.Consumer") as mock_consumer:
            mock_consumer.return_value.notifications.return_value = ["1", "2", "3"]
            notifications = client.notifications()
            mock_consumer.assert_called_once()
            mock_consumer.return_value.notifications.assert_called_once_with(inbox, accept="application/ld+json")
            assert notifications == ["1", "2", "3"]
