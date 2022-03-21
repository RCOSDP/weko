# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Pytest configuration."""

import shutil
import os
import tempfile

import pytest
from flask import Flask
from flask_babelex import Babel

from weko_search_ui import WekoSearchUI
from invenio_db import InvenioDB


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""
    app_ = Flask("testapp", instance_path=instance_path)
    app_.config.update(
        SECRET_KEY="SECRET_KEY",
        TESTING=True,
        INDEX_IMG="indextree/36466818-image.jpg",
    )
    Babel(app_)
    WekoSearchUI(app_)

    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


#


# @pytest.fixture()
# def db():
#     """Database fixture with session sharing."""
#     import invenio_db
#     from invenio_db import shared
#     db = invenio_db.db = shared.db = shared.SQLAlchemy(
#         metadata=shared.MetaData(naming_convention=shared.NAMING_CONVENTION)
#     )
#     return db


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
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SECRET_KEY="SECRET_KEY",
        TESTING=True,
        INDEX_IMG="indextree/36466818-image.jpg",
    )
    Babel(app)
    InvenioDB(app)
    WekoSearchUI(app)
    return app
