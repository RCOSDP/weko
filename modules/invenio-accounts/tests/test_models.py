# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test invenio-accounts models."""

from __future__ import absolute_import

from invenio_db import db
from sqlalchemy import inspect

from invenio_accounts import testutils
from invenio_accounts.models import SessionActivity, User


def test_session_activity_model(app):
    """Test SessionActivity model."""
    with app.app_context():
        # SessionActivity table is in the database
        inspector = inspect(db.engine)
        assert 'accounts_user_session_activity' in inspector.get_table_names()

        user = testutils.create_test_user('test@example.org')

        # Create a new SessionActivity object, put it in the db
        session_activity = SessionActivity(user_id=user.get_id(),
                                           sid_s="teststring")
        database = db

        # the `created` field is magicked in via the Timestamp mixin class
        assert not session_activity.created
        database.session.add(session_activity)
        # Commit it to the books.
        database.session.commit()
        assert session_activity.created
        assert len(user.active_sessions) == 1

        # Now how does this look on the user object?
        assert session_activity == user.active_sessions[0]

        session_two = SessionActivity(user_id=user.get_id(),
                                      sid_s="testring_2")
        database.session.add(session_two)
        # Commit it to the books.
        database.session.commit()

        assert len(user.active_sessions) == 2
        # Check #columns in table
        queried = database.session.query(SessionActivity)
        assert queried.count() == 2
        active_sessions = queried.all()
        assert session_activity.sid_s in [x.sid_s for x in active_sessions]
        assert session_two in queried.filter(
            SessionActivity.sid_s == session_two.sid_s)
        assert queried.count() == 2  # `.filter` doesn't change the query

        # Test session deletion
        session_to_delete = user.active_sessions[0]
        database.session.delete(session_to_delete)
        assert len(user.active_sessions) == 2  # Not yet updated.
        assert queried.count() == 1
        # Deletion is visible on `user` once database session is commited.
        database.session.commit()
        assert len(user.active_sessions) == 1
        assert user.active_sessions[0].sid_s != session_to_delete.sid_s

def test_get_email_by_id(app, users):
    with app.app_context():
        with app.test_client() as client:
            lst = User.get_email_by_id(1)
            assert len(lst) > 0
