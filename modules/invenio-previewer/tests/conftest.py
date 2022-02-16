# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import subprocess
import tempfile
import uuid
from zipfile import ZipFile

import pytest
from click.testing import CliRunner
from flask import Flask
from flask.cli import ScriptInfo
from flask_assets import assets
from flask_babelex import Babel
from invenio_accounts import InvenioAccounts
from invenio_assets import InvenioAssets
from invenio_assets.cli import collect, npm
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_pidstore.providers.recordid import RecordIdProvider
from invenio_records import InvenioRecords
from invenio_records_files.api import Record, RecordsBuckets
from invenio_records_ui import InvenioRecordsUI
from six import BytesIO
from sqlalchemy_utils.functions import create_database, database_exists

from invenio_previewer import InvenioPreviewer
from invenio_previewer.bundles import previewer_base_css, previewer_base_js


@pytest.yield_fixture(scope='session', autouse=True)
def app():
    """Flask application fixture with database initialization."""
    instance_path = tempfile.mkdtemp()

    app_ = Flask(
        'testapp', static_folder=instance_path, instance_path=instance_path)
    app_.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI',
            'sqlite:///:memory:'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        RECORDS_UI_DEFAULT_PERMISSION_FACTORY=None,
        RECORDS_UI_ENDPOINTS=dict(
            recid=dict(
                pid_type='recid',
                route='/records/<pid_value>',
                template='invenio_records_ui/detail.html',
            ),
            recid_previewer=dict(
                pid_type='recid',
                route='/records/<pid_value>/preview/<filename>',
                view_imp='invenio_previewer.views:preview',
                record_class='invenio_records_files.api:Record',
            ),
            recid_files=dict(
                pid_type='recid',
                route='/record/<pid_value>/files/<filename>',
                view_imp='invenio_records_files.utils.file_download_ui',
                record_class='invenio_records_files.api:Record',
            ),
        ),
        SERVER_NAME='localhost'
    )
    Babel(app_)
    assets_ext = InvenioAssets(app_)
    InvenioDB(app_)
    InvenioRecords(app_)
    previewer = InvenioPreviewer(app_)._state
    InvenioRecordsUI(app_)
    InvenioFilesREST(app_)
    InvenioAccounts(app_)

    # Add base assets bundles for jQuery and Bootstrap
    # Note: These bundles aren't included by default since package consumers
    # should handle assets and their dependencies manually.
    # assets_ext.env.register(previewer.js_bundles[0], previewer_base_js)
    # assets_ext.env.register(previewer.css_bundles[0], previewer_base_css)

    with app_.app_context():
        yield app_

    shutil.rmtree(instance_path)


@pytest.yield_fixture()
def db(app):
    """Setup database."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()


@pytest.yield_fixture(scope='session')
def webassets(app):
    """Flask application fixture with assets."""
    initial_dir = os.getcwd()
    os.chdir(app.instance_path)

    script_info = ScriptInfo(create_app=lambda info: app)
    script_info._loaded_app = app

    runner = CliRunner()
    runner.invoke(npm, obj=script_info)

    subprocess.call(['npm', 'install'])
    runner.invoke(collect, ['-v'], obj=script_info)
    runner.invoke(assets, ['build'], obj=script_info)

    yield app

    os.chdir(initial_dir)


@pytest.yield_fixture()
def location(db):
    """File system location."""
    tmppath = tempfile.mkdtemp()

    loc = Location(
        name='testloc',
        uri=tmppath,
        default=True
    )
    db.session.add(loc)
    db.session.commit()

    yield loc

    shutil.rmtree(tmppath)


@pytest.fixture()
def bucket(db, location):
    """File system location."""
    bucket = Bucket.create(location)
    db.session.commit()
    return bucket


@pytest.fixture()
def testfile(db, bucket):
    """File system location."""
    obj = ObjectVersion.create(bucket, 'testfile', stream=BytesIO(b'atest'))
    db.session.commit()
    return obj


@pytest.fixture()
def record(db):
    """Record fixture."""
    rec_uuid = uuid.uuid4()
    provider = RecordIdProvider.create(
        object_type='rec', object_uuid=rec_uuid)
    record = Record.create({
        'control_number': provider.pid.pid_value,
        'title': 'TestDefault',
    }, id_=rec_uuid)
    db.session.commit()
    return record


@pytest.fixture()
def record_with_file(db, record, testfile):
    """Record with a test file."""
    rb = RecordsBuckets(record_id=record.id, bucket_id=testfile.bucket_id)
    db.session.add(rb)
    record.update(dict(
        _files=[dict(
            bucket=str(testfile.bucket_id),
            key=testfile.key,
            size=testfile.file.size,
            checksum=str(testfile.file.checksum),
            version_id=str(testfile.version_id),
        ), ]
    ))
    record.commit()
    db.session.commit()
    return record


@pytest.fixture()
def zip_fp(db):
    """ZIP file stream."""
    fp = BytesIO()

    zipf = ZipFile(fp, 'w')
    zipf.writestr('Example.txt', 'This is an example'.encode('utf-8'))
    zipf.writestr(u'Lé UTF8 test.txt', 'This is an example'.encode('utf-8'))
    zipf.close()

    fp.seek(0)
    return fp
