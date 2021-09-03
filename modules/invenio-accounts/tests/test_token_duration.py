# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test token duration."""

import time

import pytest
from flask_security import url_for_security
from flask_security.confirmable import confirm_email_token_status, \
    generate_confirmation_token
from flask_security.recoverable import generate_reset_password_token


@pytest.mark.parametrize("sleep,expired", [
    (0, False),
    (4, True),
])
def test_forgot_password_token(app, users, sleep, expired):
    """Test expiration of token for password reset."""
    token = generate_reset_password_token(users[0]['obj'])
    reset_link = url_for_security('reset_password', token=token)

    with app.test_client() as client:
        res = client.get(reset_link, follow_redirects=True)
        time.sleep(sleep)
        if expired:
            app.config['SECURITY_MSG_PASSWORD_RESET_EXPIRED'][0] % {
                'within': app.config['SECURITY_RESET_PASSWORD_WITHIN'],
                'email': users[0]['email']
            } in res.get_data(as_text=True)
        else:
            assert (
                '<button type="submit" class="btn btn-primary btn-lg '
                'btn-block">Reset Password</button>'
            ) in res.get_data(as_text=True)


def test_confirmation_token(app, users):
    """Test expiration of token for email confirmation.

    Test to ensures that the configuration option is respected.
    """
    user = users[0]['obj']
    token = generate_confirmation_token(user)
    # Valid
    expired, invalid, token_user = confirm_email_token_status(token)
    assert expired is False and invalid is False and token_user is user
    # Expired
    time.sleep(4)
    expired, invalid, token_user = confirm_email_token_status(token)
    assert expired is True and invalid is False and token_user is user
