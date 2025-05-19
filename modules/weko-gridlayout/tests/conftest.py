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
import json
import shutil
import tempfile
import pytest
import io
from PIL import Image
from uuid import UUID
from mock import patch, MagicMock
from flask import Flask
from flask_admin import Admin
from flask_babelex import Babel
from sqlalchemy_utils.functions import create_database, database_exists
from datetime import datetime, timedelta
from tests.helpers import create_record, json_data

from invenio_cache import InvenioCache
from invenio_accounts import InvenioAccounts
from invenio_accounts.testutils import create_test_user, login_user_via_session
from invenio_access.models import ActionUsers
from invenio_files_rest import InvenioFilesREST
from invenio_files_rest.models import ObjectVersion,Bucket, Location
from invenio_access import InvenioAccess
from invenio_db import InvenioDB, db as db_
from invenio_accounts.models import User, Role
from invenio_communities.models import Community
from invenio_search import InvenioSearch, current_search, current_search_client
from invenio_stats import InvenioStats

from weko_redis.redis import RedisConnection
from weko_records.models import ItemTypeProperty
from weko_records.models import ItemType, ItemTypeMapping, ItemTypeName
from weko_records.api import Mapping
from weko_index_tree.models import Index
from weko_gridlayout import WekoGridLayout
#from weko_admin import WekoAdmin
from weko_gridlayout.views import blueprint, blueprint_api
from weko_gridlayout.services import WidgetItemServices
from weko_gridlayout.admin import widget_adminview, WidgetSettingView
from weko_gridlayout.models import WidgetType, WidgetItem,WidgetMultiLangData,WidgetDesignSetting,WidgetDesignPage
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
        # SQLALCHEMY_DATABASE_URI=os.environ.get(
        #     'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'),
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                           'postgresql+psycopg2://invenio:dbpass123@postgresql:5432/wekotest'),
        TESTING=True,
        BASE_TEMPLATE = 'weko_gridlayout/base.html',
        WEKO_GRIDLAYOUT_BASE_TEMPLATE = 'weko_gridlayout/base.html',
        WEKO_GRIDLAYOUT_ADMIN_WIDGET_DESIGN = 'weko_gridlayout/admin/widget_design.html',
        SERVER_NAME="TEST_SERVER",
        SEARCH_INDEX_PREFIX='test-',
        SEARCH_ELASTIC_HOSTS=os.environ.get(
            'SEARCH_ELASTIC_HOSTS', 'elasticsearch'),
        INDEXER_DEFAULT_DOC_TYPE='testrecord',
        SEARCH_UI_SEARCH_INDEX='test-weko',
        SECRET_KEY='SECRET_KEY',
        CACHE_REDIS_URL='redis://redis:6379/0',
        CACHE_REDIS_DB='0',
        CACHE_REDIS_HOST='redis',
        REDIS_PORT='6379',
        WEKO_GRIDLAYOUT_BUCKET_UUID='61531203-4104-4425-a51b-d32881eeab22',
        FILES_REST_DEFAULT_STORAGE_CLASS="S",
        FILES_REST_STORAGE_CLASS_LIST={
            "S": "Standard",
            "A": "Archive",
        },
        FILES_REST_DEFAULT_QUOTA_SIZE=None,
        FILES_REST_DEFAULT_MAX_FILE_SIZE=None,
        FILES_REST_OBJECT_KEY_MAX_LEN=255,
        BABEL_DEFAULT_TIMEZONE='Asia/Tokyo'
    )
    Babel(app_)
    InvenioDB(app_)
    InvenioAccounts(app_)
    InvenioAccess(app_)
    InvenioFilesREST(app_)
    WekoGridLayout(app_)
    # InvenioCache(app_)
    # WekoAdmin(app_)
    InvenioStats(app_)
    InvenioCache(app_)
    InvenioSearch(app_)
    app_.register_blueprint(blueprint)
    app_.register_blueprint(blueprint_api)

    return app_


@pytest.yield_fixture()
def app(base_app):
    with base_app.app_context():
        yield base_app


@pytest.yield_fixture()
def i18n_app(app):
    with app.test_request_context(
        headers=[('Accept-Language','ja')]):
        app.extensions['invenio-oauth2server'] = 1
        app.extensions['invenio-queues'] = 1
        #app.extensions['invenio-search'] = MagicMock()
        app.extensions['invenio-i18n'] = MagicMock()
        app.extensions['invenio-i18n'].language = "ja"
        yield app


@pytest.yield_fixture()
def client(app):
    with app.test_client() as client:
        yield client


@pytest.yield_fixture()
def client_request_args(app, file_instance_mock):
    with app.test_client() as client:
        with patch("flask.templating._render", return_value=""):
            r = client.get('/', query_string={
                'remote_addr': '0.0.0.0',
                'referrer': 'test',
                'host': '127.0.0.1',
                'url_root': 'https://localhost/api/'
                # 'search_type': WEKO_SEARCH_TYPE_DICT["FULL_TEXT"],
                })
        yield r


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
    else:
        user = User.query.filter_by(email='user@test.org').first()
        contributor = User.query.filter_by(email='contributor@test.org').first()
        comadmin = User.query.filter_by(email='comadmin@test.org').first()
        repoadmin = User.query.filter_by(email='repoadmin@test.org').first()
        sysadmin = User.query.filter_by(email='sysadmin@test.org').first()
        generaluser = User.query.filter_by(email='generaluser@test.org')
        originalroleuser = create_test_user(email='originalroleuser@test.org')
        originalroleuser2 = create_test_user(email='originalroleuser2@test.org')

    role_count = Role.query.filter_by(name='System Administrator').count()
    if role_count != 1:
        sysadmin_role = ds.create_role(name='System Administrator')
        repoadmin_role = ds.create_role(name='Repository Administrator')
        contributor_role = ds.create_role(name='Contributor')
        comadmin_role = ds.create_role(name='Community Administrator')
        general_role = ds.create_role(name='General')
        originalrole = ds.create_role(name='Original Role')
    else:
        sysadmin_role = Role.query.filter_by(name='System Administrator').first()
        repoadmin_role = Role.query.filter_by(name='Repository Administrator').first()
        contributor_role = Role.query.filter_by(name='Contributor').first()
        comadmin_role = Role.query.filter_by(name='Community Administrator').first()
        general_role = Role.query.filter_by(name='General').first()
        originalrole = Role.query.filter_by(name='Original Role').first()

    ds.add_role_to_user(sysadmin, sysadmin_role)
    ds.add_role_to_user(repoadmin, repoadmin_role)
    ds.add_role_to_user(contributor, contributor_role)
    ds.add_role_to_user(comadmin, comadmin_role)
    ds.add_role_to_user(generaluser, general_role)
    ds.add_role_to_user(originalroleuser, originalrole)
    ds.add_role_to_user(originalroleuser2, originalrole)
    ds.add_role_to_user(originalroleuser2, repoadmin_role)

    # Assign access authorization
    with db.session.begin_nested():
        action_users = [
            ActionUsers(action='superuser-access', user=sysadmin)
        ]
        db.session.add_all(action_users)

    return [
        {'email': contributor.email, 'id': contributor.id, 'obj': contributor},
        {'email': repoadmin.email, 'id': repoadmin.id, 'obj': repoadmin},
        {'email': sysadmin.email, 'id': sysadmin.id, 'obj': sysadmin},
        {'email': comadmin.email, 'id': comadmin.id, 'obj': comadmin},
        {'email': generaluser.email, 'id': generaluser.id, 'obj': sysadmin},
        {'email': originalroleuser.email, 'id': originalroleuser.id, 'obj': originalroleuser},
        {'email': originalroleuser2.email, 'id': originalroleuser2.id, 'obj': originalroleuser2},
        {'email': user.email, 'id': user.id, 'obj': user},
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
            # "is_main_layout": True,
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
                },
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


@pytest.fixture()
def db_register(users,db):
    widgettype_0 = WidgetType(type_id='Free description',type_name='Free description')
    widgettype_1 = WidgetType(type_id='Access counter',type_name='Access counter')
    widgettype_2 = WidgetType(type_id='Notice',type_name='Notice')
    widgettype_3 = WidgetType(type_id='New arrivals',type_name='New arrivals')
    widgettype_4 = WidgetType(type_id='Main contents',type_name='Main contents')
    widgettype_5 = WidgetType(type_id='Menu',type_name='Menu')
    widgettype_6 = WidgetType(type_id='Header',type_name='Header')
    widgettype_7 = WidgetType(type_id='Footer',type_name='Footer')

    widgetitem_1 = WidgetItem(widget_id=1,repository_id='Root Index',widget_type='Main contents',settings={"background_color": "#FFFFFF", "label_enable": True, "theme": "default", "frame_border_color": "#DDDDDD", "border_style": "solid", "label_text_color": "#333333", "label_color": "#F5F5F5"},is_enabled=True,is_deleted=False,locked=True,locked_by_user=1)
    widgetitem_2 = WidgetItem(widget_id=2,repository_id='Root Index',widget_type='Free description',settings={"background_color": "#FFFFFF", "label_enable": True, "theme": "default", "frame_border_color": "#DDDDDD", "border_style": "solid", "label_text_color": "#333333", "label_color": "#F5F5F5"},is_enabled=True,is_deleted=False,locked=True,locked_by_user=1)
    widgetitem_3 = WidgetItem(widget_id=3,repository_id='Root Index',widget_type='Access counter',settings={"background_color":"#FFFFFF", "label_enable": True, "theme": "default", "frame_border_color": "#DDDDDD", "border_style": "solid", "label_text_color": "#333333", "label_color": "#F5F5F5", "access_counter": "0", "following_message": "None", "other_message": "None", "preceding_message": "None"},is_enabled=True,is_deleted=False,locked=True,locked_by_user=1)
    widgetitem_4 = WidgetItem(widget_id=4,repository_id='Root Index',widget_type='Notice',settings={"background_color": "#FFFFFF", "label_enable": True, "theme": "default", "frame_border_color": "#DDDDDD", "border_style": "solid", "label_text_color": "#333333", "label_color": "#F5F5F5", "hide_the_rest": "None", "read_more": "None"},is_enabled=True,is_deleted=False,locked=True,locked_by_user=1)
    widgetitem_5 = WidgetItem(widget_id=5,repository_id='Root Index',widget_type='New arrivals',settings={"background_color": "#FFFFFF", "label_enable": True, "theme": "default", "frame_border_color": "#DDDDDD", "border_style": "solid", "label_text_color": "#333333", "label_color": "#F5F5F5", "new_dates": "5", "display_result": "5", "rss_feed": True},is_enabled=True,is_deleted=False,locked=True,locked_by_user=1)
    widgetitem_6 = WidgetItem(widget_id=6,repository_id='Root Index',widget_type='Menu',settings={"background_color": "#FFFFFF", "label_enable": True, "theme": "default", "frame_border_color": "#DDDDDD", "border_style": "solid", "label_text_color": "#333333", "label_color": "#F5F5F5", "menu_orientation": "horizontal", "menu_bg_color": "#ffffff", "menu_active_bg_color": "#ffffff", "menu_default_color": "#000000", "menu_active_color": "#000000", "menu_show_pages": [2]},is_enabled=True,is_deleted=False,locked=True,locked_by_user=1)
    widgetitem_7 = WidgetItem(widget_id=7,repository_id='Root Index',widget_type='Header',settings={"background_color": "#3D7FA1", "label_enable": False, "theme": "simple", "fixedHeaderBackgroundColor": "#FFFFFF", "fixedHeaderTextColor": "#808080"},is_enabled=True,is_deleted=False,locked=True,locked_by_user=1)
    widgetitem_8 = WidgetItem(widget_id=8,repository_id='Root Index',widget_type='Footer',settings={"background_color": "#3D7FA1", "label_enable": False, "theme": "simple"},is_enabled=True,is_deleted=False,locked=True,locked_by_user=1)


    widgetmultilangdata_1=WidgetMultiLangData(widget_id=1,lang_code='en',label='',description_data='null',is_deleted=False)
    widgetmultilangdata_2=WidgetMultiLangData(widget_id=2,lang_code='en',label='',description_data='{"description": "<p>free description</p>"}',is_deleted=False)
    widgetmultilangdata_3=WidgetMultiLangData(widget_id=3,lang_code='en',label='',description_data='"{"access_counter": "0"}',is_deleted=False)
    widgetmultilangdata_4=WidgetMultiLangData(widget_id=4,lang_code='en',label='',description_data='{"description": "<p>notice</p>"}',is_deleted=False)
    widgetmultilangdata_5=WidgetMultiLangData(widget_id=5,lang_code='en',label='',description_data='null',is_deleted=False)
    widgetmultilangdata_6=WidgetMultiLangData(widget_id=5,lang_code='en',label='',description_data='null',is_deleted=False)
    widgetmultilangdata_7=WidgetMultiLangData(widget_id=6,lang_code='en',label='',description_data='null',is_deleted=False)
    widgetmultilangdata_8=WidgetMultiLangData(widget_id=7,lang_code='en',label='',description_data='{"description": "<p>header</p>"}',is_deleted=False)
    widgetmultilangdata_9=WidgetMultiLangData(widget_id=8,lang_code='en',label='',description_data='{"description": "<p>footer</p>"}',is_deleted=False)

    widget_design_setting_1 = WidgetDesignSetting(repository_id='Root Index',settings=[{"x": 0, "y": 0, "width": 12, "height": 4, "name": "header", "id": "Root Index", "type": "Header", "widget_id": 7, "background_color": "#3D7FA1", "label_enable": False, "theme": "simple", "fixedHeaderBackgroundColor": "#FFFFFF", "fixedHeaderTextColor": "#808080", "multiLangSetting": {"en": {"label": "header", "description": {"description": "<p>header</p>"}}}}, {"x": 0, "y": 4, "width": 12, "height": 4, "name": "menu", "id": "Root Index", "type": "Menu", "widget_id": 6, "background_color": "#FFFFFF", "label_enable": True, "theme": "default", "frame_border_color": "#DDDDDD", "border_style": "solid", "label_text_color": "#333333", "label_color": "#F5F5F5", "menu_orientation": "horizontal", "menu_bg_color": "#ffffff", "menu_active_bg_color": "#ffffff", "menu_default_color": "#000000", "menu_active_color": "#000000", "menu_show_pages": [2], "multiLangSetting": {"en": {"label": "menu", "description": None }}}, {"x": 0, "y": 8, "width": 12, "height": 21, "name": "main contents", "id": "Root Index", "type": "Main contents", "widget_id": 1, "background_color": "#FFFFFF", "label_enable": True, "theme": "default", "frame_border_color": "#DDDDDD", "border_style": "solid", "label_text_color": "#333333", "label_color": "#F5F5F5", "multiLangSetting": {"en": {"label": "main contents", "description": None}}}, {"x": 0, "y": 29, "width": 2, "height": 6, "name": "new arrivals", "id": "Root Index", "type": "New arrivals", "widget_id": 5, "background_color": "#FFFFFF", "label_enable": True, "theme": "default", "frame_border_color": "#DDDDDD", "border_style": "solid", "label_text_color": "#333333", "label_color": "#F5F5F5", "new_dates": "5", "display_result": "5", "rss_feed": True, "multiLangSetting": {"en": {"label": "new arrivals", "description": None}}}, {"x": 2, "y": 29, "width": 2, "height": 6, "name": "Free description", "id": "Root Index", "type": "Free description", "widget_id": 2, "background_color": "#FFFFFF", "label_enable": True, "theme": "default", "frame_border_color": "#DDDDDD", "border_style": "solid", "label_text_color": "#333333", "label_color": "#F5F5F5", "multiLangSetting": {"en": {"label": "Free description", "description": {"description": "<p>free description</p>"}}}}, {"x": 4, "y": 29, "width": 2, "height": 6, "name": "access counter", "id": "Root Index", "type": "Access counter", "widget_id": 3, "created_date": "2022-07-19", "background_color": "#FFFFFF", "label_enable": True, "theme": "default", "frame_border_color": "#DDDDDD", "border_style": "solid", "label_text_color": "#333333", "label_color": "#F5F5F5", "access_counter": "0", "following_message": "None", "other_message": "None", "preceding_message": "None", "multiLangSetting": {"en": {"label": "access counter", "description": {"access_counter": "0"}}}}, {"x": 6, "y": 29, "width": 2, "height": 6, "name": "notice", "id": "Root Index", "type": "Notice", "widget_id": 4, "background_color": "#FFFFFF", "label_enable": True, "theme": "default", "frame_border_color": "#DDDDDD", "border_style": "solid", "label_text_color": "#333333", "label_color": "#F5F5F5", "hide_the_rest": "None", "read_more": "None", "multiLangSetting": {"en": {"label": "notice", "description": {"description": "<p>notice</p>"}}}}, {"x": 0, "y": 35, "width": 12, "height": 5, "name": "footer", "id": "Root Index", "type": "Footer", "widget_id": 8, "background_color": "#3D7FA1", "label_enable": False, "theme": "simple", "multiLangSetting": {"en": {"label": "footer", "description": {"description": "<p>footer</p>"}}}}])
    widget_design_setting_2 = WidgetDesignSetting(repository_id='test',settings={})

    widget_design_page_1=WidgetDesignPage(id=1,title='Main Layout',repository_id='Root Index',url='/',template_name='',settings=(),is_main_layout=True)
    widget_design_page_2=WidgetDesignPage(id=2,title='about',repository_id='Root Index',url='/about',template_name='',settings=[{"x": 0, "y": 0, "width": 2, "height": 6, "name": "access counter", "id": "Root Index", "type": "Access counter", "widget_id": 3, "background_color": "#FFFFFF", "label_enable": True, "theme": "default", "frame_border_color": "#DDDDDD", "border_style": "solid", "label_text_color": "#333333", "label_color": "#F5F5F5", "access_counter": "0", "following_message": "None", "other_message": "None", "preceding_message": "None", "multiLangSetting": {"en": {"label": "access counter", "description": {"access_counter": "0"}}}, "created_date": "2022-07-30"}],is_main_layout=False)

    with db.session.begin_nested():
        db.session.add(widgettype_0)
        db.session.add(widgettype_1)
        db.session.add(widgettype_2)
        db.session.add(widgettype_3)
        db.session.add(widgettype_4)
        db.session.add(widgettype_5)
        db.session.add(widgettype_6)
        db.session.add(widgettype_7)
        db.session.add(widgetitem_1)
        db.session.add(widgetitem_2)
        db.session.add(widgetitem_3)
        db.session.add(widgetitem_4)
        db.session.add(widgetitem_5)
        db.session.add(widgetitem_6)
        db.session.add(widgetitem_7)
        db.session.add(widgetitem_8)
        db.session.add(widgetmultilangdata_1)
        db.session.add(widgetmultilangdata_2)
        db.session.add(widgetmultilangdata_3)
        db.session.add(widgetmultilangdata_4)
        db.session.add(widgetmultilangdata_5)
        db.session.add(widgetmultilangdata_6)
        db.session.add(widgetmultilangdata_7)
        db.session.add(widgetmultilangdata_8)
        db.session.add(widgetmultilangdata_9)
        db.session.add(widget_design_setting_1)
        db.session.add(widget_design_setting_2)
        db.session.add(widget_design_page_1)
        db.session.add(widget_design_page_2)


@pytest.fixture
def indices(app, db):
    with db.session.begin_nested():
        # Create a test Indices
        testIndexOne = Index(index_name="testIndexOne",browsing_role="Contributor",public_state=True,id=11)
        testIndexTwo = Index(index_name="testIndexTwo",browsing_group="group_test1",public_state=True,id=22)
        testIndexThree = Index(
            index_name="testIndexThree",
            browsing_role="Contributor",
            public_state=True,
            harvest_public_state=True,
            id=33,
            item_custom_sort={'1': 1},
            public_date=datetime.today() - timedelta(days=1)
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
            public_date=datetime.today() - timedelta(days=1)
        )
        testIndexMore = Index(index_name="testIndexMore",parent=33,public_state=True,id='more')
        testIndexPrivate = Index(index_name="testIndexPrivate",public_state=False,id=55)

        db.session.add(testIndexThree)
        db.session.add(testIndexThreeChild)
        
    return {
        'index_dict': dict(testIndexThree),
        'index_non_dict': testIndexThree,
        'index_non_dict_child': testIndexThreeChild,
    }


@pytest.fixture()
def item_type(db):
    item_type_name = ItemTypeName(name='テストアイテムタイプ',
                                  has_site_license=True,
                                  is_active=True)
    with db.session.begin_nested():
        db.session.add(item_type_name)
    item_type = ItemType(name_id=1,harvesting_type=True,
                         schema=json_data("data/item_type/15_schema.json"),
                         form=json_data("data/item_type/15_form.json"),
                         render=json_data("data/item_type/15_render.json"),
                         tag=1,version_id=1,is_deleted=False)
    itemtype_property_data = json_data("data/itemtype_properties.json")[0]
    item_type_property = ItemTypeProperty(
        name=itemtype_property_data["name"],
        schema=itemtype_property_data["schema"],
        form=itemtype_property_data["form"],
        forms=itemtype_property_data["forms"],
        delflg=False
    )
    with db.session.begin_nested():
        db.session.add(item_type)
        db.session.add(item_type_property)
    mappin = Mapping.create(
        item_type.id,
        mapping = json_data("data/item_type/item_type_mapping.json")
    )
    db.session.commit()
    return item_type


@pytest.fixture()
def user(app, db):
    """Create a example user."""
    return create_test_user(email='test@test.org')


@pytest.fixture()
def communities(app, db, user, indices):
    """Create some example communities."""
    user1 = db_.session.merge(user)
    ds = app.extensions['invenio-accounts'].datastore
    r = ds.create_role(name='superuser', description='1234')
    ds.add_role_to_user(user1, r)
    ds.commit()
    db.session.commit()

    comm0 = Community.create(community_id='comm1', role_id=r.id,
                             id_user=user1.id, title='Title1',
                             description='Description1',
                             root_node_id=33)
    db.session.add(comm0)

    return comm0

@pytest.yield_fixture()
def es(app):
    current_search_client.indices.delete(index='test-*')
    # top_view aggr
    aggr_top_view_mapping = json_data("data/mapping/top_view/v6/aggr-top-view-v1.json")
    aggr_top_view_mapping.update({'aliases':
        {'{}stats-top-view'.format(app.config['SEARCH_INDEX_PREFIX']): {'is_write_index': True}}})
    current_search_client.indices.create(
        index='{}stats-top-view-0001'.format(app.config['SEARCH_INDEX_PREFIX']),
        body=aggr_top_view_mapping, ignore=[400, 404]
    )
    
    try:
        yield current_search_client
    finally:
        current_search_client.indices.delete(index="test-*")
    
@pytest.fixture
def redis_connect(app):
    redis_connection = RedisConnection().connection(db=app.config['CACHE_REDIS_DB'], kv = True)
    return redis_connection

@pytest.fixture()
def location(app, db):
    """Create default location."""
    tmppath = tempfile.mkdtemp()
    with db.session.begin_nested():
        Location.query.delete()
        loc = Location(name="local", uri=tmppath, default=True)
        db.session.add(loc)
    db.session.commit()
    return location

@pytest.fixture
def widget_upload(app,db,location):
    bucket_id = app.config['WEKO_GRIDLAYOUT_BUCKET_UUID']
    bucket_id = UUID(bucket_id)
    storage_class = app.config[
                'FILES_REST_DEFAULT_STORAGE_CLASS']
    location = Location.get_default()
    bucket = Bucket(id=bucket_id,
                            location=location,
                            default_storage_class=storage_class)
    db.session.add(bucket)
    
            
    img = Image.new("L", (128, 128))
    img_bytes = io.BytesIO()
    
    key = "{0}_{1}".format(0,"test.png")
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    obj = ObjectVersion.create(
            bucket, key, stream=img_bytes,
            mimetype="image/png"
                    )
    db.session.add(obj)
    db.session.commit()
    return {"obj":obj,"key":key}
                