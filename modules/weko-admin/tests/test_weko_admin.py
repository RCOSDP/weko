# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests for weko admin."""

import random
from datetime import timedelta

from flask import Flask, current_app, url_for

from weko_admin import WekoAdmin


def test_version():
    """Test version import."""
    from weko_admin import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testwekoadmin_app')
    ext = WekoAdmin(app)
    assert 'weko-admin' in app.extensions

    app = Flask('testapp')
    ext = WekoAdmin()
    assert 'weko-admin' not in app.extensions
    ext.init_app(app)
    assert 'weko-admin' in app.extensions


def test_view(app):
    """
    Test view.

    :param app: The flask application.
    """
    with app.test_request_context():
        hello_url = url_for('weko_admin.lifetime')

    with app.test_client() as client:
        res = client.get(hello_url)
        code = res.status_code
        assert code == 200 or code == 301 or code == 302
        if res.status_code == 200:
            assert 'lifetimeRadios' in str(res.data)


def test_set_lifetime(app):
    """Test set lifetime."""
    valid_time = (15, 30, 45, 60, 180, 360, 720, 1440)
    set_time = random.choice(valid_time)
    with app.test_request_context():
        hello_url = url_for('weko_admin.set_lifetime', minutes=set_time)

    with app.test_client() as client:
        res = client.get(hello_url)
        assert res.status_code == 200
        assert 'Session lifetime was updated' in str(res.data)
        assert app.permanent_session_lifetime.seconds == timedelta(
            minutes=int(set_time)).seconds
