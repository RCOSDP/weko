# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import pytest
from flask import current_app, session, url_for
from flask_admin import menu
from flask_security.utils import hash_password
from invenio_db import db
from werkzeug.local import LocalProxy

from invenio_accounts import InvenioAccounts
from invenio_accounts.cli import users_create
from invenio_accounts.models import SessionActivity
from invenio_accounts.testutils import login_user_via_view

_datastore = LocalProxy(
    lambda: current_app.extensions['security'].datastore
)


def test_admin(app, admin_view):
    """Test flask-admin interace."""

    # Test activation and deactivation

    with app.app_context():
        # create user and save url for testing
        request_url = url_for("user.action_view")
        kwargs = dict(email="test@test.cern", active=False,
                      password=hash_password('aafaf4as5fa'))
        _datastore.create_user(**kwargs)
        _datastore.commit()
        inserted_id = _datastore.get_user('test@test.cern').id

    with app.test_client() as client:

        res = client.post(
            request_url,
            data={'rowid': inserted_id, 'action': 'activate'},
            follow_redirects=True
        )
        assert res.status_code == 200

        res = client.post(
            request_url,
            data={'rowid': inserted_id, 'action': 'inactivate'},
            follow_redirects=True
        )
        assert res.status_code == 200

        pytest.raises(
            ValueError, client.post, request_url,
            data={'rowid': -42, 'action': 'inactivate'},
            follow_redirects=True
        )
        pytest.raises(
            ValueError, client.post, request_url,
            data={'rowid': -42, 'action': 'activate'},
            follow_redirects=True
        )


def test_admin_createuser(app, admin_view):
    """Test flask-admin user creation"""

    with app.test_client() as client:
        # Test empty mail form

        res = client.post(
            url_for('user.create_view'),
            data={'email': ''},
            follow_redirects=True
        )
        assert b'This field is required.' in res.data

        # Reproduces the workflow described in #154

        res = client.post(
            url_for('user.create_view'),
            data={'email': 'test1@test.cern'},
            follow_redirects=True
        )
        assert _datastore.get_user('test1@test.cern') is not None

        res = client.post(
            url_for('user.create_view'),
            data={'email': 'test2@test.cern', 'active': 'true'},
            follow_redirects=True
        )
        user = _datastore.get_user('test2@test.cern')
        assert user is not None
        assert user.active is True

        res = client.post(
            url_for('user.create_view'),
            data={'email': 'test3@test.cern', 'active': 'false'},
            follow_redirects=True
        )
        user = _datastore.get_user('test3@test.cern')
        assert user is not None
        assert user.active is False

    user_data = dict(email='test4@test.cern', active=False,
                     password=hash_password('123456'))
    _datastore.create_user(**user_data)

    user_data = dict(email='test5@test.cern', active=True,
                     password=hash_password('123456'))
    _datastore.create_user(**user_data)

    user_data = dict(email='test6@test.cern', active=False,
                     password=hash_password('123456'))
    _datastore.create_user(**user_data)
    _datastore.commit()
    assert _datastore.get_user('test4@test.cern') is not None
    user = _datastore.get_user('test5@test.cern')
    assert user is not None
    assert user.active is True
    user = _datastore.get_user('test6@test.cern')
    assert user is not None
    assert user.active is False


def test_admin_sessions(app, admin_view, users):
    """Test flask-admin session."""
    with app.test_request_context():
        index_view_url = url_for('sessionactivity.index_view')
        delete_view_url = url_for('sessionactivity.delete_view')
    with app.test_client() as client:
        res = client.get(index_view_url)
        assert res.status_code == 200

        # simulate login as user 1
        datastore = app.extensions['security'].datastore
        login_user_via_view(client=client, email=users[0]['email'],
                            password=users[0]['password'])
        from flask import session
        sid_s = session.sid_s
        # and try to delete own session sid_s: FAILS
        res = client.post(
            delete_view_url, data={'id': sid_s}, follow_redirects=True)
        assert res.status_code == 200
        sessions = SessionActivity.query.all()
        assert len(sessions) == 1
        assert sessions[0].sid_s == sid_s

    with app.test_client() as client:
        # simulate login as user 2
        login_user_via_view(client=client, email=users[1]['email'],
                            password=users[1]['password'])
        new_sid_s = session.sid_s
        sessions = SessionActivity.query.all()
        assert len(sessions) == 2
        all_sid_s = [session.sid_s for session in sessions]
        assert sorted([sid_s, new_sid_s]) == sorted(all_sid_s)
        # and try to delete a session of another user: WORKS
        res = client.post(
            delete_view_url, data={'id': sid_s},
            follow_redirects=True)
        sessions = SessionActivity.query.all()
        assert len(sessions) == 1
        assert sessions[0].sid_s == new_sid_s
