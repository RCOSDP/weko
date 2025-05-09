# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

import pytest
from unittest.mock import patch

from sqlalchemy.exc import SQLAlchemyError

# .tox/c1/bin/pytest --cov=weko_notifications tests/test_models.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace

from weko_notifications.models import NotificationsUserSettings

# class  NotificationsUserSettings(db.Model, Timestamp):
# .tox/c1/bin/pytest --cov=weko_notifications tests/test_models.py::TestNotificationsUserSettings -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
class TestNotificationsUserSettings():
    # def get_by_user_id(cls, user_id):
    # .tox/c1/bin/pytest --cov=weko_notifications tests/test_models.py::TestNotificationsUserSettings::test_get_by_user_id -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
    def test_get_by_user_id(self, app, db, users, user_profiles):

        assert NotificationsUserSettings.get_by_user_id(users[0]["id"]) == None

        obj = NotificationsUserSettings(user_id=users[0]["id"],subscribe_email=False)
        db.session.add(obj)
        db.session.commit()

        assert NotificationsUserSettings.get_by_user_id(users[0]["id"]) == obj

        obj = NotificationsUserSettings(user_id=users[3]["id"],subscribe_email=False)
        db.session.add(obj)
        db.session.commit()

        assert NotificationsUserSettings.get_by_user_id(users[3]["id"]) == obj

    # def create_or_update(cls, user_id, subscribe_email=None):
    # .tox/c1/bin/pytest --cov=weko_notifications tests/test_models.py::TestNotificationsUserSettings::test_create_or_update -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-notifications/.tox/c1/tmp --full-trace
    def test_create_or_update(self, app, db, users, user_profiles, mocker):
        obj = NotificationsUserSettings.create_or_update(users[0]["id"],subscribe_email=False)
        assert obj.user_id == users[0]["id"]
        assert obj.subscribe_email == False
        assert NotificationsUserSettings.query.count() == 1
        assert NotificationsUserSettings.query.first() == obj

        obj = NotificationsUserSettings.create_or_update(users[0]["id"],subscribe_email=False)
        assert obj.user_id == users[0]["id"]
        assert obj.subscribe_email == False
        assert NotificationsUserSettings.query.count() == 1
        assert NotificationsUserSettings.query.first() == obj

        obj = NotificationsUserSettings.create_or_update(users[0]["id"],subscribe_email=True)
        assert obj.user_id == users[0]["id"]
        assert obj.subscribe_email == True
        assert NotificationsUserSettings.query.count() == 1
        assert NotificationsUserSettings.query.first() == obj

        obj = NotificationsUserSettings.create_or_update(users[0]["id"],subscribe_email=True)
        assert obj.user_id == users[0]["id"]
        assert obj.subscribe_email == True
        assert NotificationsUserSettings.query.count() == 1
        assert NotificationsUserSettings.query.first() == obj

        obj = NotificationsUserSettings.create_or_update(users[0]["id"],subscribe_email=None)
        assert obj.subscribe_email == True
        assert NotificationsUserSettings.query.count() == 1
        assert NotificationsUserSettings.query.first() == obj

        mock_session_add = mocker.patch("weko_notifications.models.db.session.add")
        mock_session_add.side_effect = SQLAlchemyError("Test exception")

        with pytest.raises(SQLAlchemyError):
            NotificationsUserSettings.create_or_update(users[0]["id"],subscribe_email=False)
        assert NotificationsUserSettings.query.count() == 1
        assert NotificationsUserSettings.query.first() == obj
