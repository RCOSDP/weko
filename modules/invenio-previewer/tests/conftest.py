# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Pytest configuration."""

import os
import shutil
import tempfile
import uuid
from zipfile import ZipFile

import pytest
from flask import Flask
from flask_webpackext import current_webpack
from invenio_app import InvenioApp
from invenio_assets import InvenioAssets
from invenio_config import InvenioConfigDefault
from invenio_db import InvenioDB
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Location, ObjectVersion
from invenio_formatter import InvenioFormatter
from invenio_i18n import Babel
from invenio_pidstore.providers.recordid import RecordIdProvider
from invenio_records import InvenioRecords
from invenio_records_files.api import Record
from invenio_records_ui import InvenioRecordsUI
from invenio_records_ui.views import create_blueprint_from_app
from six import BytesIO

from invenio_previewer import InvenioPreviewer


@pytest.fixture(scope="module")
def app_config(app_config):
    """Flask application fixture with database initialization."""
    app_config.update(
        RECORDS_UI_DEFAULT_PERMISSION_FACTORY=None,
        RECORDS_UI_ENDPOINTS=dict(
            recid=dict(
                pid_type="recid",
                route="/records/<pid_value>",
                template="invenio_records_ui/detail.html",
            ),
            recid_previewer=dict(
                pid_type="recid",
                route="/records/<pid_value>/preview",
                view_imp="invenio_previewer.views:preview",
                record_class="invenio_records_files.api:Record",
            ),
            recid_files=dict(
                pid_type="recid",
                route="/record/<pid_value>/files/<filename>",
                view_imp="invenio_records_files.utils.file_download_ui",
                record_class="invenio_records_files.api:Record",
            ),
        ),
        SERVER_NAME="localhost",
    )
    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path):
    """Application factory fixture for use with pytest-invenio."""

    def _create_app(**config):
        app_ = Flask(
            __name__,
            instance_path=instance_path,
        )
        app_.config.update(config)
        Babel(app_)
        InvenioApp(app_)
        InvenioAssets(app_)
        InvenioDB(app_)
        InvenioRecords(app_)
        InvenioConfigDefault(app_)
        InvenioFormatter(app_)
        InvenioPreviewer(app_)._state
        InvenioRecordsUI(app_)
        app_.register_blueprint(create_blueprint_from_app(app_))
        InvenioFilesREST(app_)
        return app_

    return _create_app


@pytest.fixture(scope="module")
def testapp(base_app, database):
    """Application with just a database.

    Pytest-Invenio also initialise search with the app fixture.
    """
    yield base_app


@pytest.fixture(scope="module")
def webassets(testapp):
    """Flask application fixture with assets."""
    initial_dir = os.getcwd()
    os.chdir(testapp.instance_path)

    # The theme.config file has been moved from `invenio-theme` to cookiecutter
    # To solve this, a fake config file is created on the fly
    THEME_CONFIG_PATH = "less/theme.config"
    # force theme.config alias pointing to less/invenio_theme/theme.config.example
    theme_bundle = current_webpack.project.bundles[0]
    theme_bundle.aliases["../../theme.config"] = THEME_CONFIG_PATH

    current_webpack.project.create()
    current_webpack.project.install()

    # create a fake theme config file from the example one
    _assets = os.path.join(testapp.instance_path, "assets")
    example = os.path.join(_assets, "less", "invenio_theme", "theme.config.example")
    with open(example, "r") as fi:
        with open(os.path.join(_assets, THEME_CONFIG_PATH), "w") as fo:
            for line in fi:
                if line.startswith("@siteFolder"):
                    # use default theme as site theme instead of `my-site/site` as
                    # in `invenio-theme`
                    fo.write("@siteFolder: 'default';")
                else:
                    fo.write(line)

    current_webpack.project.build()

    yield testapp
    os.chdir(initial_dir)


@pytest.fixture()
def location(db):
    """File system location."""
    tmppath = tempfile.mkdtemp()
    loc = Location(name="testloc", uri=tmppath, default=True)
    db.session.add(loc)
    db.session.commit()
    yield loc
    shutil.rmtree(tmppath)


@pytest.fixture()
def record(db, location):
    """Record fixture."""
    rec_uuid = uuid.uuid4()
    provider = RecordIdProvider.create(object_type="rec", object_uuid=rec_uuid)
    record = Record.create(
        {
            "control_number": provider.pid.pid_value,
            "title": "TestDefault",
        },
        id_=rec_uuid,
    )
    db.session.commit()
    return record


@pytest.fixture()
def record_with_file(db, record, location):
    """Record with a test file."""
    testfile = ObjectVersion.create(record.bucket, "testfile", stream=BytesIO(b"atest"))
    record.update(
        dict(
            _files=[
                dict(
                    bucket=str(testfile.bucket_id),
                    key=testfile.key,
                    size=testfile.file.size,
                    checksum=str(testfile.file.checksum),
                    version_id=str(testfile.version_id),
                ),
            ]
        )
    )
    record.commit()
    db.session.commit()
    return record, testfile


@pytest.fixture()
def zip_fp(db):
    """ZIP file stream."""
    fp = BytesIO()

    zipf = ZipFile(fp, "w")
    zipf.writestr("Example.txt", "This is an example".encode("utf-8"))
    zipf.writestr("Lé UTF8 test.txt", "This is an example".encode("utf-8"))
    zipf.close()

    fp.seek(0)
    return fp
