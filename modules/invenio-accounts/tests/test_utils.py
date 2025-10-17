# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test test utilities."""

from __future__ import absolute_import, print_function

from datetime import datetime

import flask_login
import pytest
from flask_security import url_for_security
from flask_security.utils import hash_password
from invenio_db import db

from invenio_accounts import testutils
from invenio_accounts.errors import JWTDecodeError, JWTExpiredToken
from invenio_accounts.utils import jwt_create_token, jwt_decode_token, get_user_ids_by_role


def test_client_authenticated(app):
    """Test for testutils.py:client_authenticated(client).

    We want to verify that it doesn't return True when the client isn't
    authenticated/logged in.
    """
    ds = app.extensions['security'].datastore
    email = 'test@example.org'
    password = '123456'

    with app.app_context():
        change_password_url = url_for_security('change_password')
        login_url = url_for_security('login')

        with app.test_client() as client:
            # At this point we should not be authenticated/logged in as a user
            # assert flask_login.current_user.is_anonymous
            assert not testutils.client_authenticated(
                client, test_url=change_password_url)

            # Test HTTP status code of view when not logged in.
            response = client.get(change_password_url)
            assert response.status_code == 302
            assert change_password_url not in response.location
            assert login_url in response.location

            # Once more, following redirects.
            response = client.get(change_password_url, follow_redirects=True)
            assert response.status_code == 200
            assert response.location is None

            # Create a user manually directly in the datastore
            ds.create_user(email=email, password=hash_password(password))
            db.session.commit()

            # Manual login via view
            response = client.post(login_url,
                                   data={'email': email, 'password': password},
                                   environ_base={'REMOTE_ADDR': '127.0.0.1'})

            # Client gets redirected after logging in
            assert response.status_code == 302
            assert testutils.client_authenticated(client)
            assert flask_login.current_user.is_authenticated
            # `is_authenticated` returns True as long as the user object
            # isn't anonymous, i.e. it's an actual user.

            response = client.get(change_password_url)
            assert response.status_code == 200
            response = client.get(change_password_url, follow_redirects=True)
            assert response.status_code == 200


def test_create_test_user(app):
    """Test for testutils.py:create_test_user('test@example.org').

    Demonstrates basic usage and context requirements.
    """
    ds = app.extensions['security'].datastore
    email = 'test@example.org'
    password = '1234'

    with app.app_context():
        user = testutils.create_test_user(email, password)
        assert user.password_plaintext == password
        # Will fail if the app is configured to not "encrypt" the passwords.
        assert user.password != password

        # Verify that user exists in app's datastore
        user_ds = ds.find_user(email=email)
        assert user_ds
        assert user_ds.password == user.password

        with pytest.raises(Exception):
            # Catch-all "Exception" because it's raised by the datastore,
            # and the actual exception type will probably vary depending on
            # which datastore we're running the tests with.
            testutils.create_test_user(email, password)
        # No more tests here b/c the sqlalchemy session crashes when we try to
        # create a user with a duplicate email.


def test_create_test_user_defaults(app):
    """Test the default values for testutils.py:create_test_user."""
    with app.app_context():
        user = testutils.create_test_user('test@example.org')
        with app.test_client() as client:
            testutils.login_user_via_view(client, user.email,
                                          user.password_plaintext)
            assert testutils.client_authenticated(client)


def test_login_user_via_view(app):
    """Test the login-via-view function/hack."""
    email = 'test@example.org'
    password = '1234'

    with app.app_context():
        user = testutils.create_test_user(email, password)
        with app.test_client() as client:
            assert not testutils.client_authenticated(client)
            testutils.login_user_via_view(client, user.email,
                                          user.password_plaintext)
            assert testutils.client_authenticated(client)


def test_login_user_via_session(app):
    """Test the login-via-view function/hack."""
    email = 'test@example.org'
    password = '1234'

    with app.app_context():
        user = testutils.create_test_user(email, password)
        with app.test_client() as client:
            assert not testutils.client_authenticated(client)
            testutils.login_user_via_session(client, email=user.email)
            assert testutils.client_authenticated(client)


def test_jwt_token(app):
    """Test jwt creation."""
    with app.app_context():
        # Extra parameters
        extra = dict(
            defenders=['jessica', 'luke', 'danny', 'matt']
        )
        # Create token normally
        token = jwt_create_token(user_id=22, additional_data=extra)
        decode = jwt_decode_token(token)
        # Decode
        assert 'jessica' in decode.get('defenders')
        assert 22 == decode.get('sub')


def test_jwt_expired_token(app):
    """Test jwt creation."""
    with app.app_context():
        # Extra parameters
        extra = dict(
            exp=datetime(1970, 1, 1),
        )
        # Create token
        token = jwt_create_token(user_id=1, additional_data=extra)
        # Decode
        with pytest.raises(JWTExpiredToken):
            jwt_decode_token(token)
        # Random token
        with pytest.raises(JWTDecodeError):
            jwt_decode_token('Roadster SV')


def test_get_user_ids_by_role_returns_user_ids(app):
    """Test get_user_ids_by_role."""
    with app.app_context():
        ds = app.extensions['invenio-accounts'].datastore

        user1 = ds.create_user(email='test1@test.org', active=True)
        user2 = ds.create_user(email='test2@test.org', active=True)
        role = ds.create_role(name='superuser', description='1234')
        ds.add_role_to_user(user1, role)
        ds.add_role_to_user(user2, role)
        ds.commit()

        user_ids = get_user_ids_by_role(role.id)
        assert str(user1.id) in user_ids
        assert str(user2.id) in user_ids
        assert len(user_ids) == 2


@pytest.mark.parametrize("role_id, expected", [
    (999, []),
    (None, []),
    ('1', []),
])
def test_get_user_ids_by_role_returns_empty_list(app, role_id, expected):
    """Test get_user_ids_by_role."""
    with app.app_context():
        user_ids = get_user_ids_by_role(role_id)
        assert user_ids == expected
