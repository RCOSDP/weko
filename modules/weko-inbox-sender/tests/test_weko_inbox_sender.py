# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-Inbox-Sender is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask

from weko_inbox_sender import WekoInboxSender


def test_version():
    """Test version import."""
    from weko_inbox_sender import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoInboxSender(app)
    assert 'weko-inbox-sender' in app.extensions

    app = Flask('testapp')
    ext = WekoInboxSender()
    assert 'weko-inbox-sender' not in app.extensions
    ext.init_app(app)
    assert 'weko-inbox-sender' in app.extensions


def test_view(base_client):
    """Test view."""
    res = base_client.get("/")
    assert res.status_code == 200
    assert 'Welcome to WEKO-Inbox-Sender' in str(res.data)
