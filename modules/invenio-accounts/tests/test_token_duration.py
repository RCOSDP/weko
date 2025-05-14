# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test token duration."""

import time

from flask import url_for
from mock import patch
import pytest
from flask_security import url_for_security
from flask_security.confirmable import confirm_email_token_status, \
    generate_confirmation_token
from flask_security.recoverable import generate_reset_password_token

from invenio_accounts import testutils


# .tox/c1/bin/pytest --cov=invenio_accounts tests/test_token_duration.py::test_forgot_password_token -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-accounts/.tox/c1/tmp
@pytest.mark.parametrize("sleep,expired", [
    (0, False),
    (4, True),
])
def test_forgot_password_token(app, sleep, expired):
    """Test expiration of token for password reset."""
    with app.app_context():
        with app.test_client() as client:
            user = testutils.create_test_user('test@example.org')
            testutils.login_user_via_view(client, user=user)
            token = generate_reset_password_token(user)

            client.get(url_for_security('logout'))
            reset_link = url_for_security('reset_password', token=token)
            time.sleep(sleep)

            res = client.get(reset_link, follow_redirects=True)
            if expired:
                assert app.config['SECURITY_MSG_PASSWORD_RESET_EXPIRED'][0] % {
                    'within': app.config['SECURITY_RESET_PASSWORD_WITHIN'],
                    'email': user.email
                } in res.get_data(as_text=True)
            else:
                assert (
                    '<button type="submit" class="btn btn-primary btn-lg '
                    'btn-block">Reset Password</button>'
                ) in res.get_data(as_text=True)


# .tox/c1/bin/pytest --cov=invenio_accounts tests/test_token_duration.py::test_confirmation_token -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-accounts/.tox/c1/tmp
def test_confirmation_token(app):
    """Test expiration of token for email confirmation.

    Test to ensures that the configuration option is respected.
    """
    with app.app_context():
        with app.test_client() as client:
            user = testutils.create_test_user('test@example.org')
            testutils.login_user_via_view(client, user.email, user.password_plaintext)
            token = generate_confirmation_token(user)
            # Valid
            expired, invalid, token_user = confirm_email_token_status(token)
            assert expired is False and invalid is False and token_user is user
            # Expired
            time.sleep(4)
            expired, invalid, token_user = confirm_email_token_status(token)
            assert expired is True and invalid is False and token_user is user
