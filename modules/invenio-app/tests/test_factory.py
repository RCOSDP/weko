# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import request, url_for

from invenio_app.factory import create_ui


def test_version():
    """Test version import."""
    from invenio_app import __version__
    assert __version__


def test_config_loader():
    """Test config loader."""
    app = create_ui()
    assert 'cache_size' in app.jinja_options


def test_trusted_hosts():
    """Test trusted hosts configuration."""
    app = create_ui(
        APP_ALLOWED_HOSTS=['example.org', 'www.example.org'],
        APP_ENABLE_SECURE_HEADERS=False,
        RATELIMIT_ENABLED=False
    )

    @app.route('/host')
    def index_host():
        return request.host

    @app.route('/url-for')
    def index_url():
        return url_for('index_url', _external=True)

    with app.test_client() as client:
        for u in ['/host', '/url-for']:
            res = client.get(u, headers={'Host': 'attacker.org'})
            assert res.status_code == 400

            res = client.get(u, headers={'Host': 'example.org'})
            assert res.status_code == 200

            res = client.get(u, headers={'Host': 'www.example.org'})
            assert res.status_code == 200

# There used to be a test here checking if the X-Forwarded-Host
#  is checked as well. It was deleted because from werkzeug 0.15.0 onwards
#  this check is not supported and therefore it caused the test to fail.
#  New way of dealing with proxies in werkzeug is `ProxyFix
#  <https://werkzeug.palletsprojects.com/en/0.15.x/middleware/proxy_fix`_.
#  The change in werkzeug mentioned above is visible in this
# `PR <https://github.com/pallets/werkzeug/pull/1303/files>`_.
