# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Indextree-Journal is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

from __future__ import absolute_import, print_function

import os
from os.path import dirname, exists, join
import json
import shutil
import tempfile
from datetime import date, datetime, timedelta

import pytest
from flask import Flask
from flask_babelex import Babel
from sqlalchemy_utils.functions import create_database, database_exists

from invenio_accounts import InvenioAccounts
from invenio_accounts.testutils import create_test_user, login_user_via_session
from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers
from invenio_admin import InvenioAdmin
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_i18n import InvenioI18N
from weko_records import WekoRecords
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeName
from weko_index_tree.models import Index
from weko_workflow import WekoWorkflow

from weko_indextree_journal import WekoIndextreeJournal, WekoIndextreeJournalREST
from weko_indextree_journal.models import Journal
from weko_indextree_journal.views import blueprint
from weko_indextree_journal.rest import create_blueprint


@pytest.yield_fixture()
def instance_path():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path):    
    app_ = Flask(
        "testapp",
        instance_path=instance_path,
        static_folder=join(instance_path, "static"),
    )
    app_.config.update(
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND="cache",
        CACHE_REDIS_URL="redis://redis:6379/0",
        CACHE_REDIS_DB=0,
        CACHE_REDIS_HOST="redis",
        REDIS_PORT="6379",
        JSONSCHEMAS_URL_SCHEME="http",
        SECRET_KEY="CHANGE_ME",
        SECURITY_PASSWORD_SALT="CHANGE_ME_ALSO",
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "SQLALCHEMY_DATABASE_URI", "sqlite:///test.db"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SQLALCHEMY_ECHO=False,
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        DEPOSIT_SEARCH_API="/api/search",
        SECURITY_PASSWORD_HASH="plaintext",
        SECURITY_PASSWORD_SCHEMES=["plaintext"],
        SECURITY_DEPRECATED_PASSWORD_SCHEMES=[],
        OAUTHLIB_INSECURE_TRANSPORT=True,
        OAUTH2_CACHE_TYPE="simple",
        ACCOUNTS_JWT_ENABLE=False,
        INDEXER_DEFAULT_INDEX="{}-weko-item-v1.0.0".format("test"),
        INDEXER_DEFAULT_DOCTYPE="item-v1.0.0",
        INDEXER_DEFAULT_DOC_TYPE="item-v1.0.0",
        INDEXER_FILE_DOC_TYPE="content",
        WEKO_INDEX_TREE_STYLE_OPTIONS={
            "id": "weko",
            "widths": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"],
        },
        WEKO_INDEX_TREE_UPATED=True,
        I18N_LANGUAGE=[("ja", "Japanese"), ("en", "English")],
        SERVER_NAME="TEST_SERVER",
        SEARCH_ELASTIC_HOSTS="elasticsearch",
        SEARCH_INDEX_PREFIX="test-",
        WEKO_PERMISSION_ROLE_USER=[
            "System Administrator",
            "Repository Administrator",
            "Contributor",
            "General",
            "Community Administrator",
        ],
        WEKO_PERMISSION_SUPER_ROLE_USER=[
            "System Administrator",
            "Repository Administrator",
        ],
        WEKO_INDEXTREE_JOURNAL_REST_ENDPOINTS = dict(
            tid=dict(
                record_class='weko_indextree_journal.api:Journals',
                admin_indexjournal_route='/admin/indexjournal/<int:journal_id>',
                journal_route='/admin/indexjournal',
                # item_tree_journal_route='/tree/journal/<int:pid_value>',
                # journal_move_route='/tree/journal/move/<int:index_id>',
                default_media_type='application/json',
                create_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
                read_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
                update_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
                delete_permission_factory_imp='weko_indextree_journal.permissions:indextree_journal_permission',
            )
        ),
    )
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioDB(app_)
    InvenioAdmin(app_)
    InvenioI18N(app_)
    WekoRecords(app_)
    WekoWorkflow(app_)
    WekoIndextreeJournal(app_)
    WekoIndextreeJournalREST(app_)
    Babel(app_)

    return app_


@pytest.yield_fixture()
def app(base_app):
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def client_rest(app):
    with app.test_client() as client:
        yield client


@pytest.yield_fixture()
def i18n_app(app):
    with app.test_request_context(
        headers=[('Accept-Language','ja')]):
        app.extensions['invenio-oauth2server'] = 1
        yield app


@pytest.fixture()
def db(app):
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


@pytest.fixture
def test_indices(app, db):
    def base_index(id, parent, position, public_date=None, coverpage_state=False, recursive_browsing_role=False,
                   recursive_contribute_role=False, recursive_browsing_group=False,
                   recursive_contribute_group=False, online_issn=''):
        _browsing_role = "3,-98,-99"
        _contribute_role = "1,2,3,4,-98,-99"
        _group = "g1,g2"
        return Index(
            id=id,
            parent=parent,
            position=position,
            index_name="Test index {}".format(id),
            index_name_english="Test index {}".format(id),
            index_link_name="Test index link {}".format(id),
            index_link_name_english="Test index link {}".format(id),
            index_link_enabled=False,
            more_check=False,
            display_no=position,
            harvest_public_state=True,
            public_state=True,
            public_date=public_date,
            recursive_public_state=True if not public_date else False,
            coverpage_state=coverpage_state,
            recursive_coverpage_check=True if coverpage_state else False,
            browsing_role=_browsing_role,
            recursive_browsing_role=recursive_browsing_role,
            contribute_role=_contribute_role,
            recursive_contribute_role=recursive_contribute_role,
            browsing_group=_group,
            recursive_browsing_group=recursive_browsing_group,
            contribute_group=_group,
            recursive_contribute_group=recursive_contribute_group,
            biblio_flag=True if not online_issn else False,
            online_issn=online_issn
        )
    
    with db.session.begin_nested():
        db.session.add(base_index(1, 0, 0, datetime(2022, 1, 1), True, True, True, True, True, '1234-5678'))
        db.session.add(base_index(2, 0, 1))
        db.session.add(base_index(3, 0, 2))
        db.session.add(base_index(11, 1, 0))
        db.session.add(base_index(21, 2, 0))
        db.session.add(base_index(22, 2, 1))
    db.session.commit()


@pytest.fixture
def test_journals(app, db, test_indices):
    def base_data(id):
        return Journal(
            id=id,
            index_id=id,
            publication_title="test journal {}".format(id),
            date_first_issue_online="2022-01-01",
            date_last_issue_online="2022-01-01",
            title_url="search?search_type=2&q={}".format(id),
            title_id=str(id),
            coverage_depth="abstract",
            publication_type="serial",
            access_type="F",
            language="en",
            is_output=True
        )

    with db.session.begin_nested():
        db.session.add(base_data(1))
    db.session.commit()

@pytest.fixture()
def db_itemtype(app, db):
    item_type_name = ItemTypeName(
        id=1, name="テストアイテムタイプ", has_site_license=True, is_active=True
    )
    item_type_schema = dict()
    with open("tests/data/itemtype_schema.json", "r") as f:
        item_type_schema = json.load(f)

    item_type_form = dict()
    with open("tests/data/itemtype_form.json", "r") as f:
        item_type_form = json.load(f)

    item_type_render = dict()
    with open("tests/data/itemtype_render.json", "r") as f:
        item_type_render = json.load(f)

    item_type_mapping = dict()
    with open("tests/data/itemtype_mapping.json", "r") as f:
        item_type_mapping = json.load(f)

    item_type = ItemType(
        id=1,
        name_id=1,
        harvesting_type=True,
        schema=item_type_schema,
        form=item_type_form,
        render=item_type_render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )

    item_type_mapping = ItemTypeMapping(id=1, item_type_id=1, mapping=item_type_mapping)

    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)

    return {
        "item_type_name": item_type_name,
        "item_type": item_type,
        "item_type_mapping": item_type_mapping,
    }


@pytest.fixture
def indices(app, db):
    with db.session.begin_nested():
        # Create a test Indices
        testIndexOne = Index(
            index_name="testIndexOne",
            browsing_role="Contributor",
            public_state=True,
            id=11,
        )
        testIndexTwo = Index(
            index_name="testIndexTwo",
            browsing_group="group_test1",
            public_state=True,
            id=22,
        )
        testIndexThree = Index(
            index_name="testIndexThree",
            browsing_role="Contributor",
            public_state=True,
            harvest_public_state=True,
            id=33,
            item_custom_sort={"1": 1},
            public_date=datetime.today() - timedelta(days=1),
        )
        testIndexThreeChild = Index(
            index_name="testIndexThreeChild",
            browsing_role="Contributor",
            parent=33,
            index_link_enabled=True,
            index_link_name="test_link",
            public_state=True,
            harvest_public_state=False,
            id=44,
            public_date=datetime.today() - timedelta(days=1),
        )
        testIndexMore = Index(
            index_name="testIndexMore", parent=33, public_state=True, id="more"
        )
        testIndexPrivate = Index(
            index_name="testIndexPrivate", public_state=False, id=55
        )

        db.session.add(testIndexThree)
        db.session.add(testIndexThreeChild)

    return {
        "index_dict": dict(testIndexThree),
        "index_non_dict": testIndexThree,
        "index_non_dict_child": testIndexThreeChild,
    }
