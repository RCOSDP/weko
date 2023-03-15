# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Bulkupdate is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask

from weko_bulkupdate import WekoBulkupdate


def test_version():
    """Test version import."""
    from weko_bulkupdate import __version__
    assert __version__

# .tox/c1/bin/pytest --cov=weko_bulkupdate tests/test_weko_bulkupdate.py::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-bulkupdate/.tox/c1/tmp
def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoBulkupdate(app)
    assert 'weko-bulkupdate' in app.extensions

    app = Flask('testapp')
    ext = WekoBulkupdate()
    assert 'weko-bulkupdate' not in app.extensions
    ext.init_app(app)
    assert 'weko-bulkupdate' in app.extensions
    
    app = Flask("testapp")
    app.config.update(BASE_TEMPLATE="test_base_template.html")
    ext = WekoBulkupdate(app)
    assert 'weko-bulkupdate' in app.extensions

#def test_view(base_client):
#    """Test view."""
#    res = base_client.get("/")
#    assert res.status_code == 404
#    assert 'Welcome to WEKO-Bulkupdate' in str(res.data)
