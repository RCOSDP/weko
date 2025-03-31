# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 National Institute of Informatics.
#
# WEKO-Notifications is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask

from weko_notifications import WekoNotifications


def test_version():
    """Test version import."""
    from weko_notifications import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoNotifications(app)
    assert 'weko-notifications' in app.extensions

    app = Flask('testapp')
    ext = WekoNotifications()
    assert 'weko-notifications' not in app.extensions
    ext.init_app(app)
    assert 'weko-notifications' in app.extensions
