# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests foe weko-accounts."""

from flask import Flask
from weko_accounts import WekoAccounts


def test_version():
    """Test version import."""
    from weko_accounts import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoAccounts(app)
    assert 'weko-accounts' in app.extensions

    app = Flask('testapp')
    ext = WekoAccounts()
    assert 'weko-accounts' not in app.extensions
    ext.init_app(app)
    assert 'weko-accounts' in app.extensions


def test_view(app):
    """
    Test view.

    :param app: The flask application.
    """
    WekoAccounts(app)
    with app.test_client() as client:
        res = client.get("/weko/")
        assert res.status_code == 200
        assert 'Welcome to WEKO-Accounts' in str(res.data)
