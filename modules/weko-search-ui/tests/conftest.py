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
from flask import session, url_for
from flask_babelex import Babel

from weko_search_ui import WekoSearchUI
from invenio_db import InvenioDB
from invenio_i18n.ext import InvenioI18N, current_i18n
from invenio_records_rest import InvenioRecordsREST


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


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
        JSON_AS_ASCII=False,
        BABEL_DEFAULT_LOCALE="en",
        BABEL_DEFAULT_LANGUAGE="en",
        BABEL_DEFAULT_TIMEZONE="Asia/Tokyo",
        I18N_LANGUAGES=[("ja", "Japanese"), ("en", "English")],
        I18N_SESSION_KEY="my_session_key",
    )
    Babel(app)
    InvenioDB(app)
    InvenioI18N(app)
    InvenioRecordsREST(app)
    WekoSearchUI(app)
    return app
