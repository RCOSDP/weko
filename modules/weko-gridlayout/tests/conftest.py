# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-gridlayout is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile

import pytest
from mock import patch
from flask import Flask
from flask_admin import Admin
from flask_babelex import Babel
from sqlalchemy_utils.functions import create_database, database_exists

from invenio_accounts import InvenioAccounts
from invenio_accounts.testutils import create_test_user, login_user_via_session
from invenio_access.models import ActionUsers
from invenio_access import InvenioAccess
from invenio_db import InvenioDB, db as db_

from invenio_accounts.models import User, Role
from weko_gridlayout import WekoGridLayout
#from weko_admin import WekoAdmin
from weko_gridlayout.views import blueprint, blueprint_api
from weko_gridlayout.services import WidgetItemServices
from weko_gridlayout.admin import widget_adminview, WidgetSettingView
from weko_gridlayout.models import WidgetItem
from weko_admin.models import AdminLangSettings

@pytest.fixture(scope='module')
def celery_config():
    """Override pytest-invenio fixture.

    TODO: Remove this fixture if you add Celery support.
    """
    return {}


@pytest.fixture(scope='module')
def create_app(instance_path):
    """Application factory fixture."""
    def factory(**config):
        app = Flask('testapp', instance_path=instance_path)
        app.config.update(**config)
        Babel(app)
        InvenioAccounts(app)
        WekoGridLayout(app)

        return app
    return factory

@pytest.yield_fixture()
def instance_path():
    path = tempfile.mkdtemp()
    yield path
    shutil.rmtree(path)


@pytest.fixture()
def base_app(instance_path):
    app_ = Flask("testapp", instance_path=instance_path)
    app_.config.update(
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        TESTING=True,
        SECRET_KEY='SECRET_KEY',
    )
    Babel(app_)
    InvenioDB(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    #WekoAdmin(app_)
    app_.register_blueprint(blueprint)
    app_.register_blueprint(blueprint_api)

    return app_


@pytest.yield_fixture()
def app(base_app):
    with base_app.app_context():
        yield base_app

@pytest.yield_fixture()
def client(app):
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
def widget_item(db):
    insert_obj = \
        {"1": {
            "repository_id": "Root Index",
            "widget_type": "Free description",
            "is_enabled": True,
            "is_deleted": False,
            "locked": False,
            "locked_by_user": None,
            "multiLangSetting": {
                "en": {
                    "label": "for test"
                }
            }
        }}
    for i in insert_obj:
        with patch("weko_gridlayout.models.WidgetItem.get_sequence", return_value=i):
            WidgetItemServices.create(insert_obj[str(i)])
    widget_data = WidgetItem.query.all()
    return widget_data


@pytest.fixture()
def widget_items(db):
    insert_obj = \
        {"1": {
            "repository_id": "Root Index",
            "widget_type": "Free description",
            "is_enabled": True,
            "is_deleted": False,
            "locked": False,
            "locked_by_user": None,
            "multiLangSetting": {
                "en": {
                    "label": "for test"
                }
            }
        },
        "2": {
            "repository_id": "Root Index",
            "widget_type": "Free description",
            "is_enabled": True,
            "is_deleted": False,
            "locked": False,
            "locked_by_user": None,
            "multiLangSetting": {
                "fil": {
                    "label": "for test2"
                }
            }
        },
        "3": {
            "repository_id": "Root Index",
            "widget_type": "Free description",
            "is_enabled": True,
            "is_deleted": False,
            "locked": False,
            "locked_by_user": None,
            "multiLangSetting": {
                "hi": {
                    "label": "for test3"
                }
            }
        }}
    for i in insert_obj:
        with patch("weko_gridlayout.models.WidgetItem.get_sequence", return_value=i):
            WidgetItemServices.create(insert_obj[str(i)])
    widget_data = WidgetItem.query.all()
    return widget_data


@pytest.fixture()
def admin_view(app, db, view_instance):
    """Admin view fixture"""
    assert isinstance(widget_adminview, dict)

    assert 'model' in widget_adminview
    assert 'modelview' in widget_adminview
    admin = Admin(app, name="Test")

    widget_adminview_copy = dict(widget_adminview)
    widget_model = widget_adminview_copy.pop('model')
    widget_view = widget_adminview_copy.pop('modelview')
    #admin.add_view(widget_view(widget_model, db.session, **widget_adminview_copy))

    #admin.add_view(widget_adminview['modelview'](
    #    widget_adminview['model'], db.session,
    #    category=widget_adminview['category']))
    admin.add_view(view_instance)


@pytest.fixture()
def view_instance(app, db):
    view = WidgetSettingView(WidgetItem, db.session)
    return view


@pytest.fixture()
def admin_lang_settings(db):
    AdminLangSettings.create(lang_code="en", lang_name="English",
                             is_registered=True, sequence=1, is_active=True)
    AdminLangSettings.create(lang_code="fil", lang_name="Filipino (Pilipinas)",
                             is_registered=False, sequence=0, is_active=True)

# fixtureをparametrizeする場合に使用
@pytest.fixture()
def get_fixture_values(request):
    def _get_fixture(fixture):
        return request.getfixturevalue(fixture)
    return _get_fixture
