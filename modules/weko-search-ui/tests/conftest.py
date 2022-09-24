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

from multiprocessing import dummy
import shutil
import os
import tempfile
import os
import json
import uuid

import pytest
from flask import Flask, current_app
from flask import session, url_for
from flask_babelex import Babel
from flask_admin import Admin
from elasticsearch_dsl import response, Search

from invenio_accounts import InvenioAccounts
from invenio_accounts.testutils import create_test_user, login_user_via_session
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers
from invenio_cache import InvenioCache
from sqlalchemy_utils.functions import create_database, database_exists
from invenio_db import InvenioDB, db as db_
from invenio_search import RecordsSearch
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix
from invenio_records_rest import InvenioRecordsREST
from invenio_pidstore import InvenioPIDStore, current_pidstore
from invenio_i18n.ext import InvenioI18N, current_i18n
from invenio_records_rest import InvenioRecordsREST
from invenio_records_rest.views import create_blueprint_from_app
from invenio_records_rest.utils import PIDConverter
from invenio_records.models import RecordMetadata
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix
from invenio_search import InvenioSearch
from weko_records.models import ItemTypeName, ItemType
from weko_index_tree import WekoIndexTree
from weko_index_tree.models import Index
from weko_admin.models import FacetSearchSetting

from weko_search_ui import WekoSearchUI, WekoSearchREST
from weko_search_ui.config import SEARCH_UI_SEARCH_INDEX
from weko_search_ui.admin import item_management_import_adminview

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
        DB_VERSIONING=False,
        DB_VERSIONING_USER_MODEL=None,
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_RESULT_BACKEND='cache',
        SECRET_KEY="SECRET_KEY",
        TESTING=True,
        SERVER_NAME="localhost:8443",
        INDEX_IMG='indextree/36466818-image.jpg',
        WEKO_SEARCH_REST_ENDPOINTS = dict(
            recid=dict(
                pid_type='recid',
                pid_minter='recid',
                pid_fetcher='recid',
                search_class=RecordsSearch,
                # search_index=SEARCH_UI_SEARCH_INDEX,
                search_index="tenant1-weko",
                search_type='item-v1.0.0',
                search_factory_imp='weko_search_ui.query.weko_search_factory',
                # record_class='',
                record_serializers={
                    'application/json': ('invenio_records_rest.serializers'
                                        ':json_v1_response'),
                },
                search_serializers={
                    'application/json': ('weko_records.serializers'
                                        ':json_v1_search'),
                },
                index_route='/index/',
                links_factory_imp='weko_search_ui.links:default_links_factory',
                default_media_type='application/json',
                max_result_window=10000,
            ),
        ),
        JSON_AS_ASCII=False,
        BABEL_DEFAULT_LOCALE="en",
        BABEL_DEFAULT_LANGUAGE="en",
        BABEL_DEFAULT_TIMEZONE="Asia/Tokyo",
        I18N_LANGUAGES=[("ja", "Japanese"), ("en", "English")],
        I18N_SESSION_KEY="my_session_key",
        # SEARCH_INDEX_PREFIX=index_prefix,
        SEARCH_INDEX_PREFIX="tenant1",
        # SEARCH_UI_SEARCH_INDEX = "{}-weko".format(index_prefix),
        SEARCH_UI_SEARCH_INDEX = "tenant1-weko",
        WEKO_SEARCH_TYPE_INDEX="index",
        WEKO_SEARCH_TYPE_KEYWORD = "keyword"
    )
    app_.url_map.converters['pid'] = PIDConverter
    
    Babel(app_)
    InvenioDB(app_)
    InvenioI18N(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioRecordsREST(app_)
    InvenioPIDStore(app_)
    InvenioCache(app_)
    InvenioSearch(app_)
    WekoIndexTree(app_)
    WekoSearchUI(app_)
    app_.register_blueprint(create_blueprint_from_app(app_))

    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app

@pytest.yield_fixture()
def admin_view(app):
    admin = Admin(app, name="Test")
    view_class_ItemImportView = item_management_import_adminview["view_class"]
    admin.add_view(view_class_ItemImportView(**item_management_import_adminview["kwargs"]))
    
@pytest.yield_fixture()
def client(app):
    with app.test_client() as client:
        yield client


@pytest.yield_fixture()
def client_rest(app):
    WekoSearchREST(app)
    with app.test_client() as client:
        yield client

@pytest.fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)):
        create_database(str(db_.engine.url))
    db_.create_all()
    yield db_
    db_.session.remove()
    db_.drop_all()

@pytest.fixture()
def users(app, db):
    """Create users."""
    ds = app.extensions['invenio-accounts'].datastore
    user = create_test_user(email='test@test.org')
    contributor = create_test_user(email='test2@test.org')
    comadmin = create_test_user(email='test3@test.org')
    repoadmin = create_test_user(email='test4@test.org')
    sysadmin = create_test_user(email='test5@test.org')

    r1 = ds.create_role(name='System Administrator')
    ds.add_role_to_user(sysadmin, r1)
    r2 = ds.create_role(name='Repository Administrator')
    ds.add_role_to_user(repoadmin, r2)
    r3 = ds.create_role(name='Contributor')
    ds.add_role_to_user(contributor, r3)
    r4 = ds.create_role(name='Community Administrator')
    ds.add_role_to_user(comadmin, r4)

    # Assign access authorization
    with db.session.begin_nested():
        action_users = [
            ActionUsers(action='superuser-access', user=sysadmin)
        ]
        db.session.add_all(action_users)

    return [
        {'email': user.email, 'id': user.id,
         'password': user.password_plaintext, 'obj': user},
        {'email': contributor.email, 'id': contributor.id,
         'password': contributor.password_plaintext, 'obj': contributor},
        {'email': comadmin.email, 'id': comadmin.id,
         'password': comadmin.password_plaintext, 'obj': comadmin},
        {'email': repoadmin.email, 'id': repoadmin.id,
         'password': repoadmin.password_plaintext, 'obj': repoadmin},
        {'email': sysadmin.email, 'id': sysadmin.id,
         'password': sysadmin.password_plaintext, 'obj': sysadmin},
    ]

def json_data(filename):
    with open(filename, "r") as f:
        return json.load(f)

@pytest.fixture()
def item_type(db):
    item_type_name1 = ItemTypeName(name="デフォルトアイテムタイプ（フル）2",
                                  has_site_license=True,
                                  is_active=True)
    item_type_name2 = ItemTypeName(name="デフォルトアイテムタイプ（フル）3",
                                  has_site_license=True,
                                  is_active=True)
    
    item_type17 = ItemType(id=17,name_id=1,harvesting_type=False,
                         schema=json_data("tests/item_type/17_schema.json"),
                         form=json_data("tests/item_type/17_form.json"),
                         render=json_data("tests/item_type/17_render.json"),
                         tag=1,version_id=58,is_deleted=False)
    
    item_type18 = ItemType(id=18,name_id=2,harvesting_type=False,
                         schema=json_data("tests/item_type/18_schema.json"),
                         form=json_data("tests/item_type/18_form.json"),
                         render=json_data("tests/item_type/18_render.json"),
                         tag=1,version_id=58,is_deleted=False)
    with db.session.begin_nested():
        db.session.add(item_type_name1)
        db.session.add(item_type_name2)
        db.session.add(item_type17)
        db.session.add(item_type18)
    
    return {"item_type_name1":item_type_name1,
            "item_type_name2":item_type_name2,
            "item_type17":item_type17,
            "item_type18":item_type18}

@pytest.fixture()
def record(db):
    with db.session.begin_nested():
        id1 = uuid.UUID('b7bdc3ad-4e7d-4299-bd87-6d79a250553f')
        # data = json_data("tests/data/record01.json")
        # pid = current_pidstore.minters['recid'](id, data)
        # rec = Record.create(data, id_=id)
        rec1 = RecordMetadata(id=id1,
                             json=json_data("tests/data/record01.json"),
                             version_id=1
                             )
        id2 = uuid.UUID('362e800c-08a2-425d-a2b6-bcae7d5c3701')
        rec2 = RecordMetadata(id=id2,
                              json=json_data("tests/data/record02.json"),
                              version_id=2)
        id3 = uuid.UUID('3ead53d0-8e4a-489e-bb6c-d88433a029c2')
        rec3 = RecordMetadata(id=id3,
                              json=json_data("tests/data/record03.json"),
                              version_id=3)
        db.session.add(rec1)
        db.session.add(rec2)
        db.session.add(rec3)
    # with db.session.begin_nested():
    #     db.session.add(rec)
    
    return [{"id":id1, "record": rec1},{"id":id2,"record":rec2},{"id":id3,"record":rec3}]

@pytest.fixture()
def facet_search_setting(db):
    datas = json_data("tests/data/facet_search_setting.json")
    settings = list()

    for setting in datas:
        settings.append(FacetSearchSetting(**datas[setting]))
    with db.session.begin_nested():
        db.session.add_all(settings)

@pytest.fixture()
def index(db):
    datas = json_data("tests/data/index.json")
    indexes = list()
    for index in datas:
        indexes.append(Index(**datas[index]))
    with db.session.begin_nested():
        db.session.add_all(indexes)
        
@pytest.fixture()
def mock_es_execute():
    def _dummy_response(data):
        if isinstance(data, str):
            data = json_data(data)
        dummy=response.Response(Search(), data)
        return dummy
    return _dummy_response