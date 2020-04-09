# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Helper functions for tests."""

from flask import url_for


def sign_up(app, client, email=None, password=None):
    """Register a user."""
    with app.test_request_context():
        register_url = url_for('security.register')

    client.post(register_url, data=dict(
        email=email or app.config['TEST_USER_EMAIL'],
        password=password or app.config['TEST_USER_PASSWORD'],
    ), environ_base={'REMOTE_ADDR': '127.0.0.1'})


def login(app, client, email=None, password=None):
    """Log the user in with the test client."""
    with app.test_request_context():
        login_url = url_for('security.login')

    client.post(login_url, data=dict(
        email=email or app.config['TEST_USER_EMAIL'],
        password=password or app.config['TEST_USER_PASSWORD'],
    ))
