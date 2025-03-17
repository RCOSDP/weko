# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask

from weko_swordserver import WekoSWORDServer


def test_version():
    """Test version import."""
    from weko_swordserver import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoSWORDServer(app)
    assert 'weko-swordserver' in app.extensions

    app = Flask('testapp')
    ext = WekoSWORDServer()
    assert 'weko-swordserver' not in app.extensions
    ext.init_app(app)
    assert 'weko-swordserver' in app.extensions


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_weko_swordserver.py::test_view -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp
def test_view(client,sessionlifetime,install_node_module):
    """Test view."""
    import os
    os.environ["INVENIO_WEB_HOST_NAME"] = "weko3.example.org"
    res = client.get("/")
    assert res.status_code == 200
    # assert 'Welcome to WEKO-SWORDServer' in str(res.data)
