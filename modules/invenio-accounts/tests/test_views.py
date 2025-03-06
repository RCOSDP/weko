# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test account views."""

import base64

import mock
from flask import url_for
from flask_babelex import gettext as _
from flask_login import COOKIE_NAME, LoginManager
from flask_security import url_for_security
from flask_security.forms import LoginForm
from flask_security.views import _security

from invenio_accounts.models import SessionActivity
from invenio_accounts.testutils import create_test_user


def test_no_log_in_message_for_logged_in_users(app):
    """Test the password reset form for logged in users.

    Password reset form should not show log in or sign up messages for logged
    in users.
    """
    with app.app_context():
        forgot_password_url = url_for_security('forgot_password')

    with app.test_client() as client:
        log_in_message = _('Log In').encode('utf-8')
        sign_up_message = _('Sign Up').encode('utf-8')

        resp = client.get(forgot_password_url)
        assert resp.status_code == 200
        assert log_in_message in resp.data
        assert sign_up_message in resp.data

        test_email = 'info@inveniosoftware.org'
        test_password = 'test1234'
        resp = client.post(url_for_security('register'), data=dict(
            email=test_email,
            password=test_password,
        ), environ_base={'REMOTE_ADDR': '127.0.0.1'})

        resp = client.post(url_for_security('login'), data=dict(
            email=test_email,
            password=test_password,
        ))

        resp = client.get(forgot_password_url, follow_redirects=True)
        if resp.status_code == 200:
            # This behavior will be phased out in future Flask-Security
            # release as per mattupstate/flask-security#291
            assert log_in_message not in resp.data
            assert sign_up_message not in resp.data
        else:
            # Future Flask-Security will redirect to post login view when
            # authenticated user requests password reset page.
            assert resp.data == client.get(
                app.config['SECURITY_POST_LOGIN_VIEW']).data

# .tox/c1/bin/pytest --cov=invenio_accounts tests/test_views.py::test_view_list_sessions -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-accounts/.tox/c1/tmp
def test_view_list_sessions(app, app_i18n):
    """Test view list sessions."""
    with app.test_request_context():
        user1 = create_test_user(email='user1@invenio-software.org')
        user1_id = user1.id
        user2 = create_test_user(email='user2@invenio-software.org')
        user2_id = user2.id

        with app.test_client() as client:
            client.post(url_for_security('login'), data=dict(
                email=user1.email,
                password=user1.password_plaintext,
            ))

        with app.test_client() as client:
            client.post(url_for_security('login'), data=dict(
                email=user2.email,
                password=user2.password_plaintext,
            ))

            # get the list of user 2 sessions
            url = url_for('invenio_accounts.security')
            res = client.get(url)
            assert res.status_code == 200

            # check session for user 1 is not in the list
            sessions_1 = SessionActivity.query.filter_by(
                user_id=user1_id).all()
            user1_sid = sessions_1[0].sid_s
            assert len(sessions_1) == 1
            assert sessions_1[0].sid_s not in res.data.decode('utf-8')

            # check session for user 2 is in the list
            sessions_2 = SessionActivity.query.filter_by(
                user_id=user2_id).all()
            user2_sid = sessions_2[0].sid_s
            assert len(sessions_2) == 1
            assert sessions_2[0].sid_s in res.data.decode('utf-8')

            # test user 2 to delete user 1 session
            url = url_for('invenio_accounts.revoke_session')
            res = client.post(url, data={'sid_s': user1_sid})
            assert res.status_code == 302
            assert len(SessionActivity.query.filter_by(
                user_id=user2_id).all()) == 1
            
            # test user 2 to delete user 2 session
            with mock.patch('invenio_accounts.tasks.db.session.commit', side_effect=Exception('')):
                url = url_for('invenio_accounts.revoke_session')
                res = client.post(url, data={'sid_s': user2_sid})
                assert res.status_code == 302
                assert len(SessionActivity.query.filter_by(
                    user_id=user2_id).all()) == 1

            url = url_for('invenio_accounts.revoke_session')
            res = client.post(url, data={'sid_s': user2_sid})
            assert res.status_code == 302
            assert len(SessionActivity.query.filter_by(
                user_id=user2_id).all()) == 0


# .tox/c1/bin/pytest --cov=invenio_accounts tests/test_views.py::test_login_remember_me_disabled -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-accounts/.tox/c1/tmp
def test_login_remember_me_disabled(app, users):
    """Test login remember me is disabled."""
    email = users[0]['email']
    password = users[0]['password']
    with app.test_request_context():
        _security.login_form = LoginForm
        with app.test_client() as client:
            res = client.post(
                url_for_security('login'),
                data={'email': email, 'password': password, 'remember': True},
                environ_base={'REMOTE_ADDR': '127.0.0.1'})
            # check the remember_me cookie is not there
            name = '{0}='.format(COOKIE_NAME)
            assert all([
                name not in val for val in res.headers.values()])
            # check the session cookie is still there
            assert any([
                'session=' in val for val in res.headers.values()])


# .tox/c1/bin/pytest --cov=invenio_accounts tests/test_views.py::test_login_from_headers_disabled -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-accounts/.tox/c1/tmp
def test_login_from_headers_disabled(app, users):
    """Test login from headers is disabled."""
    app.login_manager.request_callback = None
    email = users[0]['email']
    basic_fmt = 'Basic {0}'
    decoded = bytes.decode(base64.b64encode(str.encode(str(email))))
    headers = [('Authorization', basic_fmt.format(decoded))]
    with app.test_request_context():
        with app.test_client() as client:
            res = client.get(
                url_for('invenio_accounts.security'),
                headers=headers,
                environ_base={'REMOTE_ADDR': '127.0.0.1'})
            # check redirect to login
            assert res.status_code == 302
            assert '<a href="/login/' in res.data.decode('utf-8')


def test_flask_login_disabled_function_exist():
    """Test flask login still has disabled functions."""
    # in case one of them fails, it means that flask-login has changed
    # and we should check if the unwanted login methods are still disabled.
    assert hasattr(LoginManager, '_set_cookie')
    assert hasattr(LoginManager, '_load_from_header')
    assert hasattr(LoginManager, '_load_from_request')


# .tox/c1/bin/pytest --cov=invenio_accounts tests/test_views.py::test_flask_login_load_from_header_works_as_expected -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-accounts/.tox/c1/tmp
def test_flask_login_load_from_header_works_as_expected(app, users):
    """Test flask login load from header exists."""
    def load_user(*args, **kwargs):
        app.login_manager.reload_user()
    app.login_manager.request_callback = None
    headers = [('Authorization', 'Basic 123')]
    with app.test_request_context():
        with app.test_client() as client, \
                mock.patch.object(LoginManager, '_load_from_header',
                                  side_effect=load_user) as mock_h:
            client.get(
                url_for('invenio_accounts.security'),
                headers=headers,
                environ_base={'REMOTE_ADDR': '127.0.0.1'})
            # check the patch is called
            assert mock_h.called is True


# .tox/c1/bin/pytest --cov=invenio_accounts tests/test_views.py::test_flask_login_load_from_request_works_as_expected -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-accounts/.tox/c1/tmp
def test_flask_login_load_from_request_works_as_expected(app, users):
    """Test flask login load from request exists."""
    def load_user(*args, **kwargs):
        app.login_manager.reload_user()
    with app.test_request_context():
        with app.test_client() as client, \
                mock.patch.object(LoginManager, '_load_from_request',
                                  side_effect=load_user) as mock_h:
            client.get(
                url_for('invenio_accounts.security'),
                environ_base={'REMOTE_ADDR': '127.0.0.1'})
            # check the patch is called
            assert mock_h.called is True
