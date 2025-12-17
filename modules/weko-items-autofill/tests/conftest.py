# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Items-Autofill is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile

import pytest
from flask import Flask
from flask_babelex import Babel
from sqlalchemy_utils.functions import create_database, database_exists


from invenio_access import InvenioAccess
from invenio_access.models import ActionUsers, ActionRoles
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User, Role
from invenio_accounts.testutils import create_test_user
from invenio_cache import InvenioCache
from invenio_communities.models import Community
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_files_rest.models import Location
from invenio_oauth2server import InvenioOAuth2Server

from weko_search_ui.config import INDEXER_DEFAULT_DOCTYPE,INDEXER_FILE_DOC_TYPE
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeName
from weko_records_ui import WekoRecordsUI
from weko_index_tree.models import Index
from weko_workflow.models import ActionStatus, Action

from weko_admin.models import ApiCertificate

from weko_items_autofill import WekoItemsAutofill
from weko_items_ui.config import WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_MAPPINGS,WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_TYPE_MAPPINGS

from tests.helpers import json_data, create_record

@pytest.fixture()
def celery_config():
    """Override pytest-invenio fixture.

    TODO: Remove this fixture if you add Celery support.
    """
    return {}


@pytest.yield_fixture()
def instance_path():
    """Temporary instance path."""
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def create_app(instance_path):
    """Application factory fixture."""
    def factory(**config):
        from weko_items_autofill import WekoItemsAutofill
        from weko_items_autofill.views import blueprint
        app = Flask('testapp', instance_path=instance_path)
        app.config.update(**config)
        Babel(app)
        WekoItemsAutofill(app)
        app.register_blueprint(blueprint)
        return app
    return factory


@pytest.fixture()
def base_app(instance_path):
    app_ = Flask('testapp', instance_path=instance_path)
    app_.config.update(
        SECRET_KEY='SECRET_KEY',
        LOGIN_DISABLED=False,
        WTF_CSRF_ENABLED=False,
        TESTING=True,
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        CACHE_REDIS_URL=os.environ.get(
            "CACHE_REDIS_URL", "redis://redis:6379/0"
        ),
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST="redis",
        SEARCH_UI_SEARCH_INDEX="test-weko",
        INDEXER_DEFAULT_DOCTYPE=INDEXER_DEFAULT_DOCTYPE,
        INDEXER_FILE_DOC_TYPE=INDEXER_FILE_DOC_TYPE,
        WEKO_PERMISSION_SUPER_ROLE_USER=[
            "System Administrator",
            "Repository Administrator",
        ],
        WEKO_PERMISSION_ROLE_COMMUNITY="Community Administrator",
        WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_MAPPINGS=WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_MAPPINGS,
        WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_TYPE_MAPPINGS = WEKO_ITEMS_UI_CRIS_LINKAGE_RESEARCHMAP_TYPE_MAPPINGS
    )
    Babel(app_)
    InvenioDB(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    #search = InvenioSearch(app_)
    InvenioCache(app_)
    InvenioOAuth2Server(app_)
    #WekoSearchUI(app_)
    WekoRecordsUI(app_)
    WekoItemsAutofill(app_)
    return app_


@pytest.yield_fixture()
def app(base_app):
    with base_app.app_context():
        yield base_app

@pytest.yield_fixture()
def client(app):
    from weko_items_autofill.views import blueprint
    app.register_blueprint(blueprint)
    with app.test_client() as client:
        yield client

@pytest.yield_fixture()
def client_api(app):
    from weko_items_autofill.views import blueprint_api
    app.register_blueprint(blueprint_api)

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
    user_count = User.query.filter_by(email='user@test.org').count()
    if user_count != 1:
        user = create_test_user(email='user@test.org')
        contributor = create_test_user(email='contributor@test.org')
        comadmin = create_test_user(email='comadmin@test.org')
        repoadmin = create_test_user(email='repoadmin@test.org')
        sysadmin = create_test_user(email='sysadmin@test.org')
        generaluser = create_test_user(email='generaluser@test.org')
        originalroleuser = create_test_user(email='originalroleuser@test.org')
        originalroleuser2 = create_test_user(email='originalroleuser2@test.org')
        student = create_test_user(email='student@test.org')
    else:
        user = User.query.filter_by(email='user@test.org').first()
        contributor = User.query.filter_by(email='contributor@test.org').first()
        comadmin = User.query.filter_by(email='comadmin@test.org').first()
        repoadmin = User.query.filter_by(email='repoadmin@test.org').first()
        sysadmin = User.query.filter_by(email='sysadmin@test.org').first()
        generaluser = User.query.filter_by(email='generaluser@test.org')
        originalroleuser = create_test_user(email='originalroleuser@test.org')
        originalroleuser2 = create_test_user(email='originalroleuser2@test.org')
        student = User.query.filter_by(email='student@test.org').first()
        
    role_count = Role.query.filter_by(name='System Administrator').count()
    if role_count != 1:
        sysadmin_role = ds.create_role(name='System Administrator')
        repoadmin_role = ds.create_role(name='Repository Administrator')
        contributor_role = ds.create_role(name='Contributor')
        comadmin_role = ds.create_role(name='Community Administrator')
        general_role = ds.create_role(name='General')
        originalrole = ds.create_role(name='Original Role')
        studentrole = ds.create_role(name='Student')
    else:
        sysadmin_role = Role.query.filter_by(name='System Administrator').first()
        repoadmin_role = Role.query.filter_by(name='Repository Administrator').first()
        contributor_role = Role.query.filter_by(name='Contributor').first()
        comadmin_role = Role.query.filter_by(name='Community Administrator').first()
        general_role = Role.query.filter_by(name='General').first()
        originalrole = Role.query.filter_by(name='Original Role').first()
        studentrole = Role.query.filter_by(name='Student').first()

    ds.add_role_to_user(sysadmin, sysadmin_role)
    ds.add_role_to_user(repoadmin, repoadmin_role)
    ds.add_role_to_user(contributor, contributor_role)
    ds.add_role_to_user(comadmin, comadmin_role)
    ds.add_role_to_user(generaluser, general_role)
    ds.add_role_to_user(originalroleuser, originalrole)
    ds.add_role_to_user(originalroleuser2, originalrole)
    ds.add_role_to_user(originalroleuser2, repoadmin_role)
    ds.add_role_to_user(student,studentrole)

    # Assign access authorization
    with db.session.begin_nested():
        action_users = [
            ActionUsers(action='superuser-access', user=sysadmin),
        ]
        db.session.add_all(action_users)
        action_roles = [
            ActionRoles(action='superuser-access', role=sysadmin_role),
            ActionRoles(action='admin-access', role=repoadmin_role),
            ActionRoles(action='schema-access', role=repoadmin_role),
            ActionRoles(action='index-tree-access', role=repoadmin_role),
            ActionRoles(action='indextree-journal-access', role=repoadmin_role),
            ActionRoles(action='item-type-access', role=repoadmin_role),
            ActionRoles(action='item-access', role=repoadmin_role),
            ActionRoles(action='files-rest-bucket-update', role=repoadmin_role),
            ActionRoles(action='files-rest-object-delete', role=repoadmin_role),
            ActionRoles(action='files-rest-object-delete-version', role=repoadmin_role),
            ActionRoles(action='files-rest-object-read', role=repoadmin_role),
            ActionRoles(action='search-access', role=repoadmin_role),
            ActionRoles(action='detail-page-acces', role=repoadmin_role),
            ActionRoles(action='download-original-pdf-access', role=repoadmin_role),
            ActionRoles(action='author-access', role=repoadmin_role),
            ActionRoles(action='items-autofill', role=repoadmin_role),
            ActionRoles(action='stats-api-access', role=repoadmin_role),
            ActionRoles(action='read-style-action', role=repoadmin_role),
            ActionRoles(action='update-style-action', role=repoadmin_role),
            ActionRoles(action='detail-page-acces', role=repoadmin_role),

            ActionRoles(action='admin-access', role=comadmin_role),
            ActionRoles(action='index-tree-access', role=comadmin_role),
            ActionRoles(action='indextree-journal-access', role=comadmin_role),
            ActionRoles(action='item-access', role=comadmin_role),
            ActionRoles(action='files-rest-bucket-update', role=comadmin_role),
            ActionRoles(action='files-rest-object-delete', role=comadmin_role),
            ActionRoles(action='files-rest-object-delete-version', role=comadmin_role),
            ActionRoles(action='files-rest-object-read', role=comadmin_role),
            ActionRoles(action='search-access', role=comadmin_role),
            ActionRoles(action='detail-page-acces', role=comadmin_role),
            ActionRoles(action='download-original-pdf-access', role=comadmin_role),
            ActionRoles(action='author-access', role=comadmin_role),
            ActionRoles(action='items-autofill', role=comadmin_role),
            ActionRoles(action='detail-page-acces', role=comadmin_role),
            ActionRoles(action='detail-page-acces', role=comadmin_role),

            ActionRoles(action='item-access', role=contributor_role),
            ActionRoles(action='files-rest-bucket-update', role=contributor_role),
            ActionRoles(action='files-rest-object-delete', role=contributor_role),
            ActionRoles(action='files-rest-object-delete-version', role=contributor_role),
            ActionRoles(action='files-rest-object-read', role=contributor_role),
            ActionRoles(action='search-access', role=contributor_role),
            ActionRoles(action='detail-page-acces', role=contributor_role),
            ActionRoles(action='download-original-pdf-access', role=contributor_role),
            ActionRoles(action='author-access', role=contributor_role),
            ActionRoles(action='items-autofill', role=contributor_role),
            ActionRoles(action='detail-page-acces', role=contributor_role),
            ActionRoles(action='detail-page-acces', role=contributor_role),
        ]
        db.session.add_all(action_roles)
    db.session.commit()
    index = Index()
    db.session.add(index)
    db.session.commit()
    comm = Community.create(community_id="comm01", role_id=sysadmin_role.id,
                            id_user=sysadmin.id, title="test community",
                            description=("this is test community"),
                            root_node_id=index.id)
    db.session.commit()
    return [
        {'email': sysadmin.email, 'id': sysadmin.id, 'obj': sysadmin},
        {'email': repoadmin.email, 'id': repoadmin.id, 'obj': repoadmin},
        {'email': comadmin.email, 'id': comadmin.id, 'obj': comadmin},
        {'email': contributor.email, 'id': contributor.id, 'obj': contributor},
        {'email': generaluser.email, 'id': generaluser.id, 'obj': generaluser},
        {'email': originalroleuser.email, 'id': originalroleuser.id, 'obj': originalroleuser},
        {'email': originalroleuser2.email, 'id': originalroleuser2.id, 'obj': originalroleuser2},
        {'email': user.email, 'id': user.id, 'obj': user},
        {'email': student.email,'id': student.id, 'obj': student}
    ]

@pytest.fixture()
def itemtypes(db):
    schema = json_data("data/itemtypes/schema.json")
    form = json_data("data/itemtypes/forms.json")
    render = json_data("data/itemtypes/render.json")
    mapping = json_data("data/itemtypes/mapping.json")
    
    item_type_name = ItemTypeName(
        id=1, name="テストアイテムタイプ1", has_site_license=True, is_active=True
    )
    item_type = ItemType(
        id=1,
        name_id=item_type_name.id,
        harvesting_type=True,
        schema=schema,
        form=form,
        render=render,
        tag=1,
        version_id=1,
        is_deleted=False,
    )
    item_type_mapping = ItemTypeMapping(id=1, item_type_id=item_type.id, mapping=mapping)
    with db.session.begin_nested():
        db.session.add(item_type_name)
        db.session.add(item_type)
        db.session.add(item_type_mapping)
    
    item_type_name2 = ItemTypeName(
        id=2, name="all_none_itemtype", has_site_license=True, is_active=True
    )
    item_type2 = ItemType(
        id=2,
        name_id=item_type_name2.id,
        harvesting_type=True,
        schema=None,
        form=None,
        render=None,
        tag=1,
        version_id=1,
        is_deleted=False,
    )
    item_type_mapping2 = ItemTypeMapping(id=2, item_type_id=item_type2.id, mapping={})   
    with db.session.begin_nested():
        db.session.add(item_type_name2)
        db.session.add(item_type2)
        db.session.add(item_type_mapping2)
    itemtype_name15 = ItemTypeName(id=3,name='テストアイテムタイプ3',
                                  has_site_license=True,
                                  is_active=True)
    with db.session.begin_nested():
        db.session.add(itemtype_name15)
    item_type15 = ItemType(id=3,name_id=itemtype_name15.id,harvesting_type=True,
                     schema=json_data("data/itemtypes/15_schema.json"),
                     form=json_data("data/itemtypes/15_form.json"),
                     render=json_data("data/itemtypes/15_render.json"),
                     tag=1,version_id=1,is_deleted=False)
    item_type_mapping3 = ItemTypeMapping(id=3, item_type_id=item_type15.id, mapping=json_data("data/itemtypes/15_item_type_mapping.json"))
    itemtype_name_for_error = ItemTypeName(id=4,name='テストアイテムタイプ4',
                                  has_site_license=True,
                                  is_active=True)
    item_type_for_error = ItemType(id=4,name_id=itemtype_name_for_error.id,harvesting_type=True,
                     schema={},
                     render={},
                     tag=1,version_id=1,is_deleted=False)
    item_type_mapping_for_error = ItemTypeMapping(id=4, item_type_id=item_type_for_error.id, mapping={})

    with db.session.begin_nested():
        db.session.add(item_type15)
        db.session.add(item_type_mapping3)
        db.session.add(itemtype_name_for_error)
        db.session.add(item_type_for_error)
        db.session.add(item_type_mapping_for_error)
        
    db.session.commit()

    return [(item_type,item_type_name,item_type_mapping),(item_type2,item_type_name2),(item_type15,itemtype_name15),(item_type_for_error,itemtype_name_for_error)]

@pytest.fixture()
def actions(db):
    action_datas = json_data("data/actions.json")
    action = list()
    
    with db.session.begin_nested():
        for data in action_datas:
            action.append(Action(**data))
        db.session.add_all(action)
    status_datas = json_data("data/action_status.json")
    status = list()
    
    with db.session.begin_nested():
        for data in status_datas:
            status.append(ActionStatus(**data))
        db.session.add_all(status)
    db.session.commit()
    return action, status

@pytest.fixture()
def location(app, db, instance_path):
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name='local', uri=instance_path, default=True)
        db.session.add(loc)
    db.session.commit()
    return loc

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
def api_certificate(db):
    api = ApiCertificate(
        api_code="crf",
        api_name="CrossRef",
        cert_data="test.test@test.org"
    )
    db.session.add(api)
    db.session.commit()
    return api