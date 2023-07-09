# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# INVENIO-ResourceSyncServer is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module tests."""

from __future__ import absolute_import, print_function

import os
from flask import Flask

from invenio_db import InvenioDB


def test_version():
    """Test version import."""
    from invenio_db import __version__
    assert __version__

# .tox/c1/bin/pytest --cov=invenio_db tests/test_invenio_db.py::test_init -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/modules/invenio-db/.tox/c1/tmp
def test_init(mock_entry_points):
    """Test extension initialization."""
    app = Flask('testapp')
    app.config.update(
        SECRET_KEY="SECRET_KEY",
        TESTING=True,
        SERVER_NAME="test_server",
        DB_VERSIONING=False,
        DB_VERSIONING_USER_MODEL=None,
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI','sqlite:///test.db')
    )
    ext = InvenioDB(app)
    assert 'invenio-db' in app.extensions

    app = Flask('testapp')
    app.config.update(
        SECRET_KEY="SECRET_KEY",
        TESTING=True,
        SERVER_NAME="test_server",
        DB_VERSIONING=False,
        DB_VERSIONING_USER_MODEL=None,
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI','sqlite:///test.db')
    )
    ext = InvenioDB()
    assert 'invenio-db' not in app.extensions
    ext.init_app(app)
    assert 'invenio-db' in app.extensions
    
# .tox/c1/bin/pytest --cov=invenio_db tests/test_invenio_db.py::test_init_db -vv -s --cov-branch --cov-report=term --cov-report=xml --basetemp=/code/modules/invenio-db/.tox/c1/tmp
def test_init_db(app, db, mock_entry_points):
    
    app.config.update(
        SECRET_KEY="SECRET_KEY",
        TESTING=True,
        SERVER_NAME="test_server",
        DB_VERSIONING=True,
        DB_VERSIONING_USER_MODEL=None,
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI','sqlite:///test.db')
    )
    from mock import patch
    ext = InvenioDB(app,db=db)
    # exist manager.pending_classes
    with patch("invenio_db.ext.versioning_models_registered",return_value=True):
        ext = InvenioDB(app,db=db)
    with patch("invenio_db.ext.versioning_models_registered",return_value=False):
        ext = InvenioDB(app,db=db)
