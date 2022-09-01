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
import sys
import shutil
import uuid
import tempfile

import pytest
from elasticsearch_dsl import response, Search
from flask import Flask
from flask_babelex import Babel
from invenio_i18n import InvenioI18N
from invenio_accounts import InvenioAccounts
from invenio_accounts.testutils import create_test_user
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_files_rest.models import Location
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_search import InvenioSearch
from sqlalchemy_utils.functions import create_database, database_exists
from weko_deposit import WekoDeposit
from weko_itemtypes_ui import WekoItemtypesUI
from weko_search_ui import WekoSearchUI
from weko_records_ui import WekoRecordsUI
from weko_records_ui.config import WEKO_PERMISSION_SUPER_ROLE_USER, WEKO_PERMISSION_ROLE_COMMUNITY, EMAIL_DISPLAY_FLG
from weko_admin.models import AdminSettings

from weko_records import WekoRecords
from weko_records.api import ItemTypes
from weko_records.config import WEKO_ITEMTYPE_EXCLUDED_KEYS
from weko_records.models import ItemTypeName, SiteLicenseInfo, FeedbackMailList

from tests.helpers import json_data, create_record

sys.path.append(os.path.dirname(__file__))

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
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND="cache",
        SECRET_KEY="CHANGE_ME",
        SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SEARCH_ELASTIC_HOSTS=os.environ.get(
            'SEARCH_ELASTIC_HOSTS', 'elasticsearch'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        TESTING=True,
        JSONSCHEMAS_HOST='inveniosoftware.org',
        THEME_SITEURL="https://localhost",
        WEKO_ITEMTYPE_EXCLUDED_KEYS=WEKO_ITEMTYPE_EXCLUDED_KEYS,
        INDEX_IMG='indextree/36466818-image.jpg',
        SEARCH_UI_SEARCH_INDEX='tenant1',
        INDEXER_DEFAULT_DOCTYPE='item-v1.0.0',
        INDEXER_FILE_DOC_TYPE='content',
        I18N_LANGUAGES=[("ja", "Japanese"), ("en", "English")],
        WEKO_PERMISSION_SUPER_ROLE_USER=WEKO_PERMISSION_SUPER_ROLE_USER,
        WEKO_PERMISSION_ROLE_COMMUNITY=WEKO_PERMISSION_ROLE_COMMUNITY,
        EMAIL_DISPLAY_FLG=EMAIL_DISPLAY_FLG
    )

    WekoRecords(app_)
    Babel(app_)
    InvenioI18N(app_)
    InvenioAccounts(app_)
    InvenioDB(app_)
    InvenioJSONSchemas(app_)
    InvenioSearch(app_)
    InvenioIndexer(app_)
    InvenioPIDStore(app_)
    InvenioPIDRelations(app_)
    InvenioRecords(app_)
    WekoDeposit(app_)
    WekoItemtypesUI(app_)
    WekoSearchUI(app_)
    WekoRecordsUI(app_)

    return app_


@pytest.yield_fixture()
def app(base_app):
    """Flask application fixture."""
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def i18n_app(app):
    with app.test_request_context(headers=[('Accept-Language','en')]):
        yield app


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
def location(app):
    """Create default location."""
    tmppath = tempfile.mkdtemp()
    with db_.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=tmppath, default=True)
        db_.session.add(loc)
    db_.session.commit()
    return location


@pytest.fixture()
def user():
    """Create a example user."""
    return create_test_user(email='test@test.org')


@pytest.fixture()
def item_type(app, db):
    _item_type_name = ItemTypeName(name='test')

    _render = {
        'meta_list': {},
        'table_row_map': {
            'schema': {
                'properties': {
                    'item_1': {}
                }
            }
        },
        'table_row': ['1']
    }

    return ItemTypes.create(
        name='test',
        item_type_name=_item_type_name,
        schema={},
        render=_render,
        tag=1
    )

@pytest.fixture()
def item_type2(app, db):
    _item_type_name = ItemTypeName(name='test2')

    _render = {
        'meta_list': {},
        'table_row_map': {
            'schema': {
                'properties': {
                    'item_1': {}
                }
            }
        },
        'table_row': ['1']
    }

    return ItemTypes.create(
        name='test2',
        item_type_name=_item_type_name,
        schema={},
        render=_render,
        tag=1
    )


@pytest.fixture()
def mock_execute():
    def factory(data):
        if isinstance(data, str):
            data = json_data(data)
        dummy = response.Response(Search(), data)
        return dummy
    return factory


@pytest.fixture()
def records(db):
    record_data = json_data("data/test_records.json")
    item_data = json_data("data/test_items.json")
    record_num = len(record_data)
    result = []
    for d in range(record_num):
        result.append(create_record(record_data[d], item_data[d]))
    db.session.commit()
    yield result


@pytest.fixture()
def admin_settings(app, db):
    setting = AdminSettings(
        name="items_display_settings",
        settings={"items_display_email": True, "items_search_author": "name"}
    )
    
    with db.session.begin_nested():
        db.session.add(setting)


@pytest.fixture()
def site_license_info(app, db):
    record = SiteLicenseInfo(
        organization_id=1,
        organization_name='test',
        domain_name='domain',
        mail_address='nii@nii.co.jp',
        receive_mail_flag=False)
    with db.session.begin_nested():
        db.session.add(record)
    return record
