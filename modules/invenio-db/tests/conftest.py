# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Pytest configuration."""

import os

import pytest
from flask import Flask

from invenio_db.utils import alembic_test_context


@pytest.fixture()
def db():
    """Database fixture with session sharing."""
    import invenio_db
    from invenio_db import shared

    db = invenio_db.db = shared.db = shared.SQLAlchemy(
        metadata=shared.MetaData(naming_convention=shared.NAMING_CONVENTION)
    )
    return db


@pytest.fixture()
def app():
    """Flask application fixture."""
    app = Flask(__name__)
    app.config.update(
        DB_VERSIONING=False,
        DB_VERSIONING_USER_MODEL=None,
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        ),
        ALEMBIC_CONTEXT=alembic_test_context(),
    )
    return app
