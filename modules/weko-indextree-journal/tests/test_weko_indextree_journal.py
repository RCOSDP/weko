# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Indextree-Journal is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask

from weko_indextree_journal import WekoIndextreeJournal


def test_version():
    """Test version import."""
    from weko_indextree_journal import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoIndextreeJournal(app)
    assert 'weko-indextree-journal' in app.extensions

    app = Flask('testapp')
    ext = WekoIndextreeJournal()
    assert 'weko-indextree-journal' not in app.extensions
    ext.init_app(app)
    assert 'weko-indextree-journal' in app.extensions


def test_view(base_client):
    """Test view."""
    res = base_client.get("/")
    assert res.status_code == 200
    assert 'Welcome to WEKO-Indextree-Journal' in str(res.data)
