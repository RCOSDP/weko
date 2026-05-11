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

import datetime
import os
import shutil
import tempfile
from time import sleep

import pytest
from elasticsearch.exceptions import RequestError
from flask import Flask
from flask.cli import ScriptInfo
from flask_babelex import Babel
from flask_breadcrumbs import Breadcrumbs
from flask_celeryext import FlaskCeleryExt
from flask_oauthlib.provider import OAuth2Provider
from flask_security import login_user
from .helpers import fill_oauth2_headers, make_pdf_fixture
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint as accounts_blueprint
from invenio_assets import InvenioAssets
from invenio_db import InvenioDB, db
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import Location
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_oauth2server import InvenioOAuth2Server, InvenioOAuth2ServerREST
from invenio_oauth2server.models import Client, Token
from invenio_oauth2server.views import \
    settings_blueprint as oauth2server_settings_blueprint
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
import invenio_records_files.models  # noqa: F401
from invenio_records_rest import InvenioRecordsREST
from invenio_records_rest.utils import PIDConverter
from invenio_records_ui import InvenioRecordsUI
from invenio_rest import InvenioREST
from invenio_search import InvenioSearch, current_search, current_search_client
from invenio_search_ui import InvenioSearchUI
from six import BytesIO, get_method_self
from sqlalchemy import inspect
from werkzeug.wsgi import DispatcherMiddleware
from unittest.mock import patch

from invenio_deposit import InvenioDeposit, InvenioDepositREST
from invenio_deposit.api import Deposit
from invenio_deposit.scopes import write_scope
from kombu import Exchange, Queue
import weko_records_ui.models  # noqa: F401

def object_as_dict(obj):
    """Make a dict from SQLAlchemy object."""
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


# Store the original function
_original_check_created_id = None

def _safe_check_created_id(record):
    """Wrapper that handles None shared_ids."""
    from flask import current_app
    from flask_security import current_user
    
    is_himself = False
    supers = current_app.config.get('WEKO_PERMISSION_SUPER_ROLE_USER', [])
    comadmin = current_app.config.get('WEKO_PERMISSION_ROLE_COMMUNITY', [])
    proxy_posting = current_app.config.get('WEKO_ITEMS_UI_PROXY_POSTING', False)
    user_id = current_user.get_id() \
            if current_user and current_user.is_authenticated else None
    if user_id is not None:
        created_id = record.get('_deposit', {}).get('created_by')
        owner = record.get('owner')
        shared_ids = record.get('weko_shared_ids') or []  # Handle None
        if user_id and created_id and user_id == str(created_id):
            is_himself = True
        elif user_id and owner and user_id == str(owner):
            is_himself = True
        elif user_id and len(shared_ids) > 0:
            if int(user_id) in shared_ids:
                is_himself = True
        if not is_himself:
            # check role
            from weko_groups.api import Group
            check_role = []
            check_role.extend(supers)
            check_role.extend(comadmin)
            for role in list(current_user.roles or []):
                if role.name in check_role:
                    is_himself = True
                    break
        if not is_himself and proxy_posting:
            from weko_items_ui.utils import is_proxy_posting_user
            is_himself = is_proxy_posting_user()
    return is_himself


@pytest.fixture(autouse=True)
def mock_permissions():
    """Mock check_created_id to handle None shared_ids."""
    with patch('weko_records_ui.permissions.check_created_id', _safe_check_created_id):
        yield


@pytest.yield_fixture()
def base_app(request):
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()
    database_uri = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'
    )

    def init_app(app_):
        app_.config.update(
            BROKER_URL='amqp://guest:guest@rabbitmq:5672/',
            CELERY_BROKER_URL = 'amqp://guest:guest@rabbitmq:5672/',
            CELERY_ALWAYS_EAGER=True,
            CELERY_CACHE_BACKEND='memory',
            CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
            CELERY_RESULT_BACKEND='cache',
            JSONSCHEMAS_URL_SCHEME='http',
            SECRET_KEY='CHANGE_ME',
            SECURITY_PASSWORD_SALT='CHANGE_ME_ALSO',
            SQLALCHEMY_DATABASE_URI=database_uri,
            SEARCH_ELASTIC_HOSTS=os.environ.get(
                'SEARCH_ELASTIC_HOSTS', 'elasticsearch'),
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
            INDEXER_DEFAULT_INDEX='records-default-v1.0.0',
            INDEXER_DEFAULT_DOC_TYPE='default-v1.0.0',
            INDEXER_MQ_QUEUE = Queue("indexer", 
                exchange=Exchange("indexer", type="direct"), routing_key="indexer",auto_delete=False,queue_arguments={"x-queue-type":"quorum"}),
            WEKO_PERMISSION_SUPER_ROLE_USER=[
                "System Administrator",
                "Repository Administrator",
            ],
            WEKO_RECORDS_UI_EMAIL_ITEM_KEYS = ['creatorMails', 'contributorMails', 'mails'],
            WEKO_PERMISSION_ROLE_COMMUNITY = ['Community Administrator'],
        )
        Babel(app_)
        FlaskCeleryExt(app_)
        Breadcrumbs(app_)
        OAuth2Provider(app_)
        InvenioDB(app_)
        InvenioAccounts(app_)
        InvenioAccess(app_)
        InvenioIndexer(app_)
        InvenioJSONSchemas(app_)
        InvenioOAuth2Server(app_)
        InvenioFilesREST(app_)
        InvenioPIDStore(app_)
        InvenioRecords(app_)
        InvenioSearch(app_)

    api_app = Flask('testapiapp', instance_path=instance_path)
    api_app.url_map.converters['pid'] = PIDConverter
    InvenioDepositREST(api_app)

    init_app(api_app)
    InvenioREST(api_app)
    InvenioOAuth2ServerREST(api_app)
    InvenioRecordsREST(api_app)

    app = Flask('testapp', instance_path=instance_path)
    app.url_map.converters['pid'] = PIDConverter
    InvenioDeposit(app)
    init_app(app)
    app.register_blueprint(accounts_blueprint)
    app.register_blueprint(oauth2server_settings_blueprint)
    InvenioAssets(app)
    InvenioSearchUI(app)
    InvenioRecordsUI(app)
    app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        '/api': api_app.wsgi_app
    })

    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        shutil.rmtree(instance_path)


@pytest.yield_fixture()
def app(base_app):
    """Yield the REST API application in its context."""
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def api(base_app):
    """Yield the REST API application in its context."""
    api = get_method_self(base_app.wsgi_app.mounts['/api'])
    with api.app_context():
        yield api


@pytest.yield_fixture()
def test_client(base_app):
    """Test client."""
    with base_app.test_client() as client_:
        yield client_


@pytest.fixture()
def users(app):
    """Create users."""
    with db.session.begin_nested():
        datastore = app.extensions['security'].datastore
        user1 = datastore.create_user(email='info@inveniosoftware.org',
                                      password='tester', active=True)
        user2 = datastore.create_user(email='test@inveniosoftware.org',
                                      password='tester2', active=True)
        admin = datastore.create_user(email='admin@inveniosoftware.org',
                                      password='tester3', active=True)
        db.session.add(ActionUsers(
            action='deposit-admin-access', user=admin
        ))
    db.session.commit()
    return [object_as_dict(user1), object_as_dict(user2)]


@pytest.fixture()
def client(app, users):
    """Create client."""
    with db.session.begin_nested():
        client_ = Client(
            client_id='client_test_u1c1',
            client_secret='client_test_u1c1',
            name='client_test_u1c1',
            description='',
            is_confidential=False,
            user_id=users[0]['id'],
            _redirect_uris='',
            _default_scopes='',
        )
        db.session.add(client_)
    db.session.commit()
    return client_


@pytest.fixture()
def write_token_user_1(app, client, users):
    """Create token."""
    with db.session.begin_nested():
        token_ = Token(
            client=client,
            user_id=users[0]['id'],
            access_token='dev_access_1',
            refresh_token='dev_refresh_1',
            expires=datetime.datetime.now() + datetime.timedelta(hours=10),
            is_personal=False,
            is_internal=True,
            _scopes=write_scope.id,
        )
        db.session.add(token_)
    db.session.commit()
    return token_


@pytest.fixture()
def write_token_user_2(app, client, users):
    """Create token."""
    with db.session.begin_nested():
        token_ = Token(
            client=client,
            user_id=users[1]['id'],
            access_token='dev_access_2',
            refresh_token='dev_refresh_2',
            expires=datetime.datetime.now() + datetime.timedelta(hours=10),
            is_personal=False,
            is_internal=True,
            _scopes=write_scope.id,
        )
        db.session.add(token_)
    db.session.commit()
    return token_


@pytest.fixture()
def fake_schemas(app, api, es, tmpdir):
    """Fake schema."""
    schemas = tmpdir.mkdir('schemas')
    empty_schema = '{"title": "Empty"}'
    for path in (('deposit-v1.0.0.json', ),
                 ('deposits', 'test-v1.0.0.json'),
                 ('test-v1.0.0.json', ), ):
        schema = schemas
        for section in path[:-1]:
            schema = schema.mkdir(section)
        schema = schema.join(path[-1])
        schema.write(empty_schema)

    app.extensions['invenio-jsonschemas'].register_schemas_dir(schemas.strpath)
    api.extensions['invenio-jsonschemas'].register_schemas_dir(schemas.strpath)


@pytest.yield_fixture()
def es(app):
    """Elasticsearch fixture."""
    try:
        list(current_search.create())
    except RequestError:
        list(current_search.delete(ignore=[404]))
        list(current_search.create(ignore=[400]))
    current_search_client.indices.refresh()
    yield current_search_client
    list(current_search.delete(ignore=[404]))


@pytest.fixture()
def location(app):
    """Create default location."""
    tmppath = tempfile.mkdtemp()
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=tmppath, default=True)
        db.session.add(loc)
    db.session.commit()
    return location


@pytest.fixture()
def deposit(app, es, users, location):
    """New deposit with files."""
    record = {
        'title': 'fuu',
        'weko_shared_ids': []
    }
    with app.test_request_context():
        datastore = app.extensions['security'].datastore
        login_user(datastore.find_user(email=users[0]['email']))
        deposit = Deposit.create(record)
        deposit.commit()
        db.session.commit()
    sleep(2)
    return deposit


@pytest.fixture()
def files(app, deposit):
    """Add a file to the deposit."""
    return []


@pytest.fixture()
def pdf_file(app):
    """Create a test pdf file."""
    return None


@pytest.fixture()
def pdf_file2(app):
    """Create a test pdf file."""
    return None


@pytest.fixture()
def pdf_file2_samename(app):
    """Create a test pdf file."""
    return None


@pytest.fixture()
def json_headers():
    """JSON headers."""
    return [('Content-Type', 'application/json'),
            ('Accept', 'application/json')]


@pytest.fixture()
def oauth2_headers_user_1(app, json_headers, write_token_user_1):
    """Authentication headers (with a valid oauth2 token)."""
    return fill_oauth2_headers(json_headers, write_token_user_1)


@pytest.fixture()
def oauth2_headers_user_2(app, json_headers, write_token_user_2):
    """Authentication headers (with a valid oauth2 token)."""
    return fill_oauth2_headers(json_headers, write_token_user_2)

@pytest.fixture()
def script_info(app):
    """Get ScriptInfo object for testing CLI."""
    return ScriptInfo(create_app=lambda info: app)
