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

import os
import shutil
import tempfile

import pytest
from flask import Flask
from flask_babelex import Babel
from invenio_accounts import InvenioAccounts
from invenio_assets import InvenioAssets
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_deposit import InvenioDeposit
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Bucket, Location, ObjectVersion
from invenio_i18n import InvenioI18N
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_records_rest.utils import PIDConverter
from invenio_search import InvenioSearch
from invenio_search_ui import InvenioSearchUI
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix
from six import BytesIO
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database
from weko_admin import WekoAdmin
from weko_items_ui import WekoItemsUI
from weko_records import WekoRecords

from weko_deposit import WekoDeposit, WekoDepositREST
from weko_deposit.api import WekoRecord
from weko_deposit.config import WEKO_BUCKET_QUOTA_SIZE


@pytest.fixture()
def base_app(request):
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()

    def init_app(app_):
        app_.config.update(
            CELERY_ALWAYS_EAGER=True,
            CELERY_CACHE_BACKEND='memory',
            CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
            CELERY_RESULT_BACKEND='cache',
            CACHE_REDIS_URL='redis://redis:6379/0',
            JSONSCHEMAS_URL_SCHEME='http',
            SECRET_KEY='CHANGE_ME',
            SECURITY_PASSWORD_SALT='CHANGE_ME_ALSO',
            SQLALCHEMY_DATABASE_URI=os.environ.get(
                'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
            SEARCH_ELASTIC_HOSTS=os.environ.get(
                'SEARCH_ELASTIC_HOSTS', None),
            SQLALCHEMY_TRACK_MODIFICATIONS=True,
            SQLALCHEMY_ECHO=False,
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            DEPOSIT_SEARCH_API='/api/search',
            SECURITY_PASSWORD_HASH='plaintext',
            SECURITY_PASSWORD_SCHEMES=['plaintext'],
            SECURITY_DEPRECATED_PASSWORD_SCHEMES=[],
            OAUTHLIB_INSECURE_TRANSPORT=True,
            OAUTH2_CACHE_TYPE='simple',
            ACCOUNTS_JWT_ENABLE=False,
            INDEXER_DEFAULT_INDEX='{}-weko-item-v1.0.0'.format(
                index_prefix),
            INDEXER_DEFAULT_DOCTYPE='item-v1.0.0',
            INDEXER_DEFAULT_DOC_TYPE='item-v1.0.0',
            INDEXER_FILE_DOC_TYPE='content',
            WEKO_BUCKET_QUOTA_SIZE=WEKO_BUCKET_QUOTA_SIZE,
            WEKO_MAX_FILE_SIZE=WEKO_BUCKET_QUOTA_SIZE,
        )
        Babel(app_)
        InvenioAccounts(app_)
        InvenioAssets(app_)
        InvenioDB(app_)
        InvenioDeposit(app_)
        InvenioFilesREST(app_)
        InvenioJSONSchemas(app_)
        InvenioIndexer(app_)
        InvenioPIDStore(app_)
        InvenioRecords(app_)
        InvenioSearch(app_)
        InvenioSearchUI(app_)
        InvenioPIDRelations(app_)
        InvenioI18N(app_)
        WekoRecords(app_)
        WekoItemsUI(app_)
        WekoAdmin(app_)

    app = Flask('testapp', instance_path=instance_path)
    app.url_map.converters['pid'] = PIDConverter
    # initialize InvenioDeposit first in order to detect any invalid dependency
    WekoDeposit(app)
    # WekoDepositREST(app)
    init_app(app)

    with app.app_context():
        yield app

    shutil.rmtree(instance_path)


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    drop_database(str(db_.engine.url))


@pytest.fixture()
def location(app, db):
    """Create default location."""
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
def record(app, db):
    """Create a record."""
    metadata = {
        'title': 'fuu'
    }
    record = WekoRecord.create(metadata)
    record.commit()
    db.session.commit()
    return record


@pytest.fixture()
def generic_file(app, record):
    """Add a generic file to the record."""
    stream = BytesIO(b'test example')
    filename = 'generic_file.txt'
    record.files[filename] = stream
    record.files.dumps()
    record.commit()
    db_.session.commit()
    return filename
