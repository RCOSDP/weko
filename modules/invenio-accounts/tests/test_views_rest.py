# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2024 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE

"""Test authentication REST API views."""

import datetime
import json
from unittest import mock

from flask import url_for
from flask_security import current_user
from invenio_db import db

from invenio_accounts.models import Domain, DomainStatus
from invenio_accounts.testutils import create_test_user


def get_json(response):
    """Get JSON from response."""
    return json.loads(response.get_data(as_text=True))


def assert_error_resp(res, expected_errors, expected_status_code=400):
    """Assert errors in a client response."""
    assert res.status_code == expected_status_code
    payload = get_json(res)
    errors = payload.get("errors", [])
    for field, msg in expected_errors:
        if not field:  # top-level "message" error
            assert msg in payload["message"].lower()
            continue
        assert any(
            e["field"] == field and msg in e["message"].lower() for e in errors
        ), payload


def _mock_send_mail(subject, recipient, template, **context):
    from urllib.parse import urlsplit

    from invenio_accounts.config import SECURITY_RESET_URL

    assert context["reset_link"]
    assert SECURITY_RESET_URL in urlsplit(context["reset_link"])[2]


def _mock_send_confirmation_mail(subject, recipient, template, **context):
    from invenio_accounts.config import ACCOUNTS_REST_CONFIRM_EMAIL_ENDPOINT

    assert context["confirmation_link"]
    assert (
        ACCOUNTS_REST_CONFIRM_EMAIL_ENDPOINT.format(token="")
        in context["confirmation_link"]
    )


def _login_user(client, user, email="normal@TEST.com", password="123456"):
    url = url_for("invenio_accounts_rest_auth.login")
    res = client.post(url, data=dict(email=email, password=password))
    payload = get_json(res)
    assert res.status_code == 200
    assert payload["id"] == user.id
    assert payload["email"].lower() == user.email.lower()
    session_cookie = next(c for c in client.cookie_jar if c.name == "session")
    assert session_cookie is not None
    assert session_cookie.value
    assert current_user.is_authenticated


def test_login_view(api):
    app = api
    with app.app_context():
        normal_user = create_test_user(email="normal@test.com")
        create_test_user(email="disabled@test.com", active=False)
        create_test_user(email="nopass@test.com", password=None)

        db.session.commit()

        with app.test_client() as client:
            url = url_for("invenio_accounts_rest_auth.login")
            # Missing fields
            res = client.post(url)
            assert_error_resp(
                res,
                (
                    ("password", "required"),
                    ("email", "required"),
                ),
            )

            # Invalid fields
            res = client.post(url, data=dict(email="invalid-email", password=None))
            assert_error_resp(
                res,
                (
                    ("password", "required field"),
                    ("email", "not a valid email"),
                ),
            )

            # Invalid credentials
            res = client.post(url, data=dict(email="not@exists.com", password="123456"))
            assert_error_resp(res, (("email", "user does not exist"),))

            # No-password user
            res = client.post(
                url, data=dict(email="nopass@test.com", password="123456")
            )
            assert_error_resp(res, (("password", "no password is set"),))

            # Disabled account
            res = client.post(
                url, data=dict(email="disabled@test.com", password="123456")
            )
            assert_error_resp(res, ((None, "account is disabled"),))

            # Successful login
            _login_user(client, normal_user)

            # User info view
            res = client.get(url_for("invenio_accounts_rest_auth.user_info"))
            payload = get_json(res)
            assert res.status_code == 200
            assert payload["id"] == normal_user.id


def test_disabled_login_view(api):
    app = api
    app.config["ACCOUNTS_LOCAL_LOGIN_ENABLED"] = False

    with app.app_context():
        user = create_test_user(email="normal@test.com")
        db.session.commit()
        with app.test_client() as client:
            url = url_for("invenio_accounts_rest_auth.login")
            data = {"email": user.email, "password": "123456"}

            res = client.post(url, data=data)
            payload = get_json(res)

            assert res.status_code != 200
            expected_msg = app.config["SECURITY_MSG_LOCAL_LOGIN_DISABLED"][0]
            assert payload["message"] == expected_msg


def test_registration_view(api):
    app = api
    with app.app_context():
        create_test_user(email="old@test.com")
        db.session.commit()
        with app.test_client() as client:
            url = url_for("invenio_accounts_rest_auth.register")

            # Missing fields
            res = client.post(url)
            assert_error_resp(
                res,
                (
                    ("password", "required"),
                    ("email", "required"),
                ),
            )

            # Invalid fields
            res = client.post(url, data=dict(email="invalid-email", password="short"))
            assert_error_resp(
                res,
                (
                    ("password", "length"),
                    ("email", "not a valid email"),
                ),
            )

            # Existing user
            res = client.post(url, data=dict(email="old@test.com", password="123456"))
            assert_error_resp(res, (("email", "old@test.com is already associated"),))

            # Successful registration
            res = client.post(url, data=dict(email="new@test.com", password="123456"))
            payload = get_json(res)
            assert res.status_code == 200
            assert payload["id"] == 2
            assert payload["email"] == "new@test.com"
            session_cookie = next(c for c in client.cookie_jar if c.name == "session")
            assert session_cookie is not None
            assert session_cookie.value

            res = client.get(url_for("invenio_accounts_rest_auth.user_info"))
            assert res.status_code == 200


def test_custom_registration_view(app_with_flexible_registration):
    app = app_with_flexible_registration
    with app.app_context():
        create_test_user(email="old@test.com")
        db.session.commit()
        with app.test_client() as client:
            url = url_for("invenio_accounts_rest_auth.register")

            # Missing custom field
            res = client.post(url, data=dict(email="new@test.com", password="123456"))
            assert_error_resp(res, (("active", "required"),))

            # Successful registration
            res = client.post(
                url, data=dict(email="new@test.com", password="123456", active=True)
            )
            assert res.status_code == 200


def test_registration_view_blocked_by_domain(api):
    app = api
    with app.app_context():
        # Block the domain
        Domain.create("test.com", status=DomainStatus.blocked)
        db.session.commit()
        with app.test_client() as client:
            url = url_for("invenio_accounts_rest_auth.register")

            res = client.post(
                url, data=dict(email="new@test.com", password="123456", active=True)
            )
            assert_error_resp(res, [("email", "blocked")])


def test_logout_view(api):
    app = api
    with app.app_context():
        normal_user = create_test_user(email="normal@test.com")
        db.session.commit()
        with app.test_client() as client:
            # Login user
            _login_user(client, normal_user)
            old_session_cookie = next(
                c for c in client.cookie_jar if c.name == "session"
            )

            # Log out user
            url = url_for("invenio_accounts_rest_auth.logout")
            res = client.post(url)
            payload = get_json(res)
            assert payload["message"] == "User logged out."
            new_session_cookie = next(
                c for c in client.cookie_jar if c.name == "session"
            )
            assert old_session_cookie.value != new_session_cookie.value
            assert current_user.is_anonymous


@mock.patch("invenio_accounts.views.rest.send_mail", _mock_send_mail)
def test_forgot_password_view(api):
    app = api
    with app.app_context():
        create_test_user(email="normal@test.com")
        db.session.commit()
        with app.test_client() as client:
            url = url_for("invenio_accounts_rest_auth.forgot_password")

            # Invalid email
            res = client.post(url, data=dict(email="invalid"))
            assert_error_resp(res, (("email", "user does not exist"),))

            # Valid email
            res = client.post(url, data=dict(email="normal@test.com"))
            payload = get_json(res)
            assert "Instructions to reset your password" in payload["message"]


def test_disabled_forgot_password_view(api):
    from flask_security.recoverable import generate_reset_password_token

    app = api
    app.config["SECURITY_RECOVERABLE"] = False
    app.extensions["security"].recoverable = False

    with app.app_context():
        user = create_test_user(email="normal@test.com")
        generate_reset_password_token(user)
        db.session.commit()
        with app.test_client() as client:
            url = url_for("invenio_accounts_rest_auth.forgot_password")
            res = client.post(url, data={"email": user.email})
            payload = get_json(res)

            assert res.status_code != 200
            expected = app.config["SECURITY_MSG_PASSWORD_RECOVERY_DISABLED"][0]
            assert payload["message"] == expected


def test_reset_password_view(api):
    from flask_security.recoverable import generate_reset_password_token

    app = api
    with app.app_context():
        normal_user = create_test_user(email="normal@test.com")
        # Generate token
        token = generate_reset_password_token(normal_user)
        db.session.commit()
        with app.test_client() as client:
            url = url_for("invenio_accounts_rest_auth.reset_password")
            res = client.post(url, data=dict(password="new-password", token=token))
            payload = get_json(res)
            assert res.status_code == 200
            assert "You successfully reset your password" in payload["message"]

            # Login using new password
            res = client.post(
                url, data=dict(email="normal@test.com", password="new-password")
            )
            payload = get_json(res)
            assert res.status_code == 200
            assert payload["id"] == normal_user.id
            assert payload["email"] == normal_user.email
            session_cookie = next(c for c in client.cookie_jar if c.name == "session")
            assert session_cookie is not None
            assert session_cookie.value


def test_disabled_reset_password_view(api):
    from flask_security.recoverable import generate_reset_password_token

    app = api
    app.config["SECURITY_RECOVERABLE"] = False
    app.extensions["security"].recoverable = False

    with app.app_context():
        user = create_test_user(email="normal@test.com")
        token = generate_reset_password_token(user)
        db.session.commit()
        with app.test_client() as client:
            url = url_for("invenio_accounts_rest_auth.reset_password")
            data = {
                "token": token,
                "password": "123456",
            }

            res = client.post(url, data=data)
            payload = get_json(res)

            assert res.status_code != 200
            expected = app.config["SECURITY_MSG_PASSWORD_RESET_DISABLED"][0]
            assert payload["message"] == expected


def test_change_password_view(api):
    app = api
    with app.app_context():
        normal_user = create_test_user(email="normal@test.com")
        db.session.commit()
        with app.test_client() as client:
            url = url_for("invenio_accounts_rest_auth.change_password")

            # Not authorized user
            res = client.post(
                url, data=dict(password="123456", new_password="new-password")
            )
            assert_error_resp(
                res,
                ((None, "server could not verify that you are authorized"),),
                expected_status_code=401,
            )

            # Logged in user
            _login_user(client, normal_user)

            # Same password
            res = client.post(url, data=dict(password="123456", new_password="123456"))
            assert_error_resp(res, (("password", "new password must be different"),))

            # Valid password
            res = client.post(
                url, data=dict(password="123456", new_password="new-password")
            )
            payload = get_json(res)
            assert "successfully changed your password" in payload["message"]
            # Log in using new password
            _login_user(client, normal_user, password="new-password")


def test_disabled_change_password_view(api):
    app = api
    app.config["SECURITY_CHANGEABLE"] = False
    app.extensions["security"].changeable = False

    with app.app_context():
        user = create_test_user(email="normal@test.com")
        db.session.commit()
        with app.test_client() as client:
            _login_user(client, user)
            url = url_for("invenio_accounts_rest_auth.change_password")
            data = {
                "password": user.password_plaintext,
                "new_password": "1234567",
            }

            res = client.post(url, data=data)
            payload = get_json(res)

            assert res.status_code != 200
            expected = app.config["SECURITY_MSG_PASSWORD_CHANGE_DISABLED"][0]
            assert payload["message"] == expected


@mock.patch("invenio_accounts.views.rest.send_mail", _mock_send_confirmation_mail)
def test_send_confirmation_email_view(api):
    app = api
    with app.app_context():
        normal_user = create_test_user(email="normal@test.com")
        confirmed_user = create_test_user(
            email="confirmed@test.com", confirmed_at=datetime.datetime.now()
        )

        db.session.commit()
        with app.test_client() as client:
            url = url_for("invenio_accounts_rest_auth.send_confirmation")
            _login_user(client, normal_user)
            res = client.post(url, data=dict(email=normal_user.email))

            assert_error_resp(
                res,
                ((None, "confirmation instructions have been sent"),),
                expected_status_code=200,
            )

            # Already confirmed
            res = client.post(url, data=dict(email=confirmed_user.email))
            assert_error_resp(res, ((None, "email has already been confirmed"),))


def test_confirm_email_view(api):
    from flask_security.confirmable import generate_confirmation_token

    app = api
    with app.app_context():
        normal_user = create_test_user(email="normal@test.com")
        confirmed_user = create_test_user(
            email="confirmed@test.com", confirmed_at=datetime.datetime.now()
        )
        Domain.create("test.com", status=DomainStatus.verified)
        db.session.commit()
        # Generate token
        token = generate_confirmation_token(normal_user)
        confirmed_token = generate_confirmation_token(confirmed_user)
        with app.test_client() as client:
            url = url_for("invenio_accounts_rest_auth.confirm_email")

            # Invalid token
            res = client.post(url, data=dict(token="foo"))
            payload = get_json(res)
            assert "invalid confirmation token" in payload["message"][0].lower()

            # Already confirmed user
            res = client.post(url, data=dict(token=confirmed_token))
            payload = get_json(res)
            assert "email has already been confirmed" in payload["message"].lower()

            # Valid confirm user
            assert normal_user.confirmed_at is None
            res = client.post(url, data=dict(token=token))
            payload = get_json(res)
            assert "your email has been confirmed" in payload["message"].lower()
            assert normal_user.confirmed_at
            # User is verified because domain is verified.
            assert normal_user.verified_at


def test_sessions_list_view(api):
    app = api
    session_total = 3
    with app.app_context():
        normal_user = create_test_user(email="normal@test.com")
        db.session.commit()

        url = url_for("invenio_accounts_rest_auth.sessions_list")

        for _ in range(session_total):
            with app.test_client() as client:
                _login_user(client, normal_user)

        res = client.get(url)
        payload = get_json(res)
        assert payload["total"] == session_total
        assert isinstance(payload["results"], list)


def test_sessions_item_view(api):
    app = api
    with app.app_context():
        normal_user = create_test_user(email="normal@test.com")
        db.session.commit()

        old_sid_s = None
        with app.test_client() as client:
            # Invalid session
            _login_user(client, normal_user)
            url = url_for("invenio_accounts_rest_auth.sessions_item", sid_s="foo")
            res = client.delete(url)
            assert_error_resp(res, ((None, "unable to remove session"),))

            # Valid session
            sid_s = current_user.active_sessions[0].sid_s
            assert current_user
            url = url_for("invenio_accounts_rest_auth.sessions_item", sid_s=sid_s)
            res = client.delete(url)
            assert_error_resp(
                res,
                (
                    (None, "successfully removed"),
                    (None, "logged out"),
                ),
                expected_status_code=200,
            )
            assert not current_user.active_sessions

            # Login again and save session
            _login_user(client, normal_user)
            old_sid_s = current_user.active_sessions[0].sid_s

        with app.test_client() as client:
            _login_user(client, normal_user)
            url = url_for("invenio_accounts_rest_auth.sessions_item", sid_s=old_sid_s)
            res = client.delete(url)
            assert_error_resp(
                res,
                (
                    (None, "successfully removed"),
                    (None, "revoked"),
                ),
                expected_status_code=200,
            )
