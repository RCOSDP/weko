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
from unittest.mock import patch

import pytest
from flask import Flask
from flask_menu import Menu
from flask_babelex import Babel
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_accounts.testutils import create_test_user
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers
from invenio_admin import InvenioAdmin
from invenio_assets import InvenioAssets
from invenio_db import InvenioDB, db as db_
from invenio_cache import InvenioCache
from invenio_deposit import InvenioDeposit
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.views import blueprint as invenio_files_rest_blueprint
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
from simplekv.memory.redisstore import RedisStore
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database
from weko_admin import WekoAdmin
# from weko_items_ui import WekoItemsUI
from weko_records import WekoRecords
# from weko_records_ui import WekoRecordsUI
from weko_search_ui import WekoSearchUI
from weko_search_ui.config import WEKO_SEARCH_MAX_RESULT
from weko_theme import WekoTheme

from weko_deposit import WekoDeposit, WekoDepositREST
from weko_deposit.api import WekoRecord
from weko_deposit.views import blueprint
from weko_deposit.api import WekoDeposit as aWekoDeposit
from weko_deposit.config import WEKO_BUCKET_QUOTA_SIZE, \
    WEKO_DEPOSIT_REST_ENDPOINTS, _PID


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
                'SQLALCHEMY_DATABASE_URI',
                'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/invenio'),
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
            INDEX_IMG='indextree/36466818-image.jpg',
            WEKO_SEARCH_MAX_RESULT=WEKO_SEARCH_MAX_RESULT,
            WEKO_DEPOSIT_REST_ENDPOINTS=WEKO_DEPOSIT_REST_ENDPOINTS,
            WEKO_INDEX_TREE_STYLE_OPTIONS={
                'id': 'weko',
                'widths': ['1', '2', '3', '4', '5', '6', '7', '8',
                           '9', '10', '11']
            }
        )
        Babel(app_)
        InvenioAccounts(app_)
        InvenioAccess(app_)
        InvenioAdmin(app_)
        InvenioAssets(app_)
        InvenioCache(app_)
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
        # WekoItemsUI(app_)
        # WekoRecordsUI(app_)
        WekoAdmin(app_)
        WekoSearchUI(app_)
        WekoTheme(app_)
        Menu(app_)
        app_.register_blueprint(blueprint)
        app_.register_blueprint(invenio_files_rest_blueprint)
        # app_.register_blueprint(create_blueprint)

    app = Flask('testapp', instance_path=instance_path)
    app.url_map.converters['pid'] = PIDConverter
    # initialize InvenioDeposit first in order to detect any invalid dependency
    WekoDeposit(app)
    WekoDepositREST(app)
    WEKO_DEPOSIT_REST_ENDPOINTS['depid']['rdc_route'] = '/deposits/redirect/<{0}:pid_value>'.format(_PID)
    WEKO_DEPOSIT_REST_ENDPOINTS['depid']['pub_route'] = '/deposits/publish/<{0}:pid_value>'.format(_PID)
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
    # drop_database(str(db_.engine.url))


@pytest.fixture()
def location(app, db):
    """Create default location."""
    tmppath = tempfile.mkdtemp()

    location = Location.query.filter_by(name="testloc").count()
    if location != 1:
        loc = Location(
            name='testloc',
            uri=tmppath,
            default=True
        )
        db.session.add(loc)
        db.session.commit()
    else:
        loc = Location.query.filter_by(name='testloc').first()

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


@pytest.yield_fixture()
def client(app):
    """Get test client."""
    with app.test_client() as client:
        yield client


@pytest.fixture()
def users(app, db):
    """Create users."""
    ds = app.extensions['invenio-accounts'].datastore
    user_count = User.query.filter_by(email='test@test.org').count()
    if user_count != 1:
        user = create_test_user(email='test@test.org')
        contributor = create_test_user(email='test2@test.org')
        comadmin = create_test_user(email='test3@test.org')
        repoadmin = create_test_user(email='test4@test.org')
        sysadmin = create_test_user(email='test5@test.org')

    else:
        user = User.query.filter_by(email='test@test.org').first()
        contributor = User.query.filter_by(email='test2@test.org').first()
        comadmin = User.query.filter_by(email='test3@test.org').first()
        repoadmin = User.query.filter_by(email='test4@test.org').first()
        sysadmin = User.query.filter_by(email='test5@test.org').first()

    role_count = Role.query.filter_by(name='System Administrator').count()
    if role_count != 1:
        r1 = ds.create_role(name='System Administrator')
        r2 = ds.create_role(name='Repository Administrator')
        r3 = ds.create_role(name='Contributor')
        r4 = ds.create_role(name='Community Administrator')

    else:
        r1 = Role.query.filter_by(name='System Administrator').first()
        r2 = Role.query.filter_by(name='Repository Administrator').first()
        r3 = Role.query.filter_by(name='Contributor').first()
        r4 = Role.query.filter_by(name='Community Administrator').first()

    ds.add_role_to_user(sysadmin, r1)
    ds.add_role_to_user(repoadmin, r2)
    ds.add_role_to_user(contributor, r3)
    ds.add_role_to_user(comadmin, r4)

    # Assign access authorization
    with db.session.begin_nested():
        action_users = [
            ActionUsers(action='superuser-access', user=sysadmin)
        ]
        db.session.add_all(action_users)

    return [
        {'email': user.email, 'id': user.id, 'obj': user},
        {'email': contributor.email, 'id': contributor.id, 'obj': contributor},
        {'email': comadmin.email, 'id': comadmin.id, 'obj': comadmin},
        {'email': repoadmin.email, 'id': repoadmin.id, 'obj': repoadmin},
        {'email': sysadmin.email, 'id': sysadmin.id, 'obj': sysadmin},
    ]


@pytest.fixture()
def deposit(app, location):
    bucket = Bucket(default_location=1,
                    default_storage_class='S', size=0,
                    quota_size=app.config['WEKO_BUCKET_QUOTA_SIZE'],
                    max_file_size=app.config['WEKO_MAX_FILE_SIZE'],
                    locked=False, deleted=False, location=location)
    with patch('weko_deposit.api.Bucket.create', return_value=bucket):
        deposit = aWekoDeposit.create({})
        return deposit.pid.pid_value
