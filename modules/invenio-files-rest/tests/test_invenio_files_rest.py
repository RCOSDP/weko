# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

import pytest
from flask import Flask, current_app

from invenio_files_rest import InvenioFilesREST


def test_version():
    """Test version import."""
    from invenio_files_rest import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    ext = InvenioFilesREST(app)
    assert "invenio-files-rest" in app.extensions

    app = Flask("testapp")
    ext = InvenioFilesREST()
    assert "invenio-files-rest" not in app.extensions
    ext.init_app(app)
    assert "invenio-files-rest" in app.extensions


def test_alembic(app, db):
    """Test alembic recipes."""
    ext = app.extensions["invenio-db"]

    if db.engine.name == "sqlite":
        raise pytest.skip("Upgrades are not supported on SQLite.")

    # skip index from alembic migrations until sqlalchemy 2.0
    # https://github.com/sqlalchemy/sqlalchemy/discussions/7597
    def include_object(object, name, type_, reflected, compare_to):
        if name == "ix_uq_partial_files_object_is_head":
            return False

        return True

    current_app.config["ALEMBIC_CONTEXT"] = {"include_object": include_object}

    assert not ext.alembic.compare_metadata()
    db.drop_all()
    ext.alembic.upgrade()

    assert not ext.alembic.compare_metadata()
    ext.alembic.stamp()
    ext.alembic.downgrade(target="96e796392533")
    ext.alembic.upgrade()

    assert not ext.alembic.compare_metadata()
