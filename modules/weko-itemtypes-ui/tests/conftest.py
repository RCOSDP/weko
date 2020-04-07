# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pytest configuration."""

import shutil
import tempfile

import pytest
from flask import Flask
from flask_babelex import Babel
from invenio_assets import InvenioAssets
from invenio_i18n import InvenioI18N
from invenio_theme import InvenioTheme
from weko_records import WekoRecords


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path):
    """Flask application fixture."""
    app_ = Flask('testapp', instance_path=instance_path)
    app_.config.update(
        SECRET_KEY='SECRET_KEY',
        TESTING=True,
    )
    Babel(app_)
    InvenioI18N(app_)
    InvenioTheme(app_)
    InvenioAssets(app_)
    WekoRecords(app_)
    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app
