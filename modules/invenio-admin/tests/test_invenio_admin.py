# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Module tests."""

from __future__ import absolute_import, print_function

import importlib

import flask_admin
import pkg_resources
import pytest
from flask import Flask
from flask_admin.contrib.sqla import ModelView
from invenio_access.permissions import Permission
from invenio_db import db
from invenio_theme import InvenioTheme
from mock import patch
from pkg_resources import EntryPoint

from invenio_admin import InvenioAdmin
from invenio_admin.permissions import admin_permission_factory
from invenio_admin.views import protected_adminview_factory


def test_version():
    """Test version import."""
    from invenio_admin import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = InvenioAdmin(app)
    assert 'invenio-admin' in app.extensions

    app = Flask('testapp')
    ext = InvenioAdmin()
    assert 'invenio-admin' not in app.extensions
    ext.init_app(app)
    assert 'invenio-admin' in app.extensions


def test_invenio_theme_loading_order():
    """Test base template set correctly by invenio_theme."""
    app = Flask('testapp')
    InvenioAdmin(app)
    assert app.config.get('ADMIN_BASE_TEMPLATE') is None

    app = Flask('testapp')
    InvenioTheme(app)
    InvenioAdmin(app)
    assert app.config.get('ADMIN_BASE_TEMPLATE') is not None

    app = Flask('testapp')
    InvenioAdmin(app)
    InvenioTheme(app)
    assert app.config.get('ADMIN_BASE_TEMPLATE') is not None


def test_base_template_override():
    """Test base template is set up correctly."""
    app = Flask('testapp')
    base_template = 'test_base_template.html'
    app.config['ADMIN_BASE_TEMPLATE'] = base_template
    InvenioTheme(app)
    state = InvenioAdmin(app)
    assert app.config.get('ADMIN_BASE_TEMPLATE') == base_template

    # Force call of before_first_request registered triggers.
    app.try_trigger_before_first_request_functions()
    assert state.admin.base_template == base_template


def test_default_permission(app):
    """Test loading of default permission class."""
    with app.app_context():
        with patch('pkg_resources.get_distribution') as get_distribution:
            get_distribution.side_effect = pkg_resources.DistributionNotFound
            assert not isinstance(admin_permission_factory(None), Permission)

    assert isinstance(admin_permission_factory(None), Permission)


def test_admin_view_authenticated(app):
    """Test the authentication for the admin."""
    with app.test_client() as client:
        res = client.get("/admin/", follow_redirects=False)
        # Assert redirect to login
        assert res.status_code == 302

    # Unauthenticated users are redirect to login page.
    with app.test_client() as client:
        # Model view
        res = client.get("/admin/testmodel/", follow_redirects=False)
        assert res.status_code == 302
        assert res.location.startswith('http://localhost/login')

        # Base view
        res = client.get('/admin/testbase/')
        assert res.status_code == 302
        assert res.location.startswith('http://localhost/login')
        res = client.get('/admin/testbase/foo/')
        assert res.status_code == 302
        assert res.location.startswith('http://localhost/login')

    # User 1 can access admin because it has ActioNeed(admin-access)
    with app.test_client() as client:
        res = client.get('/login/?user=1')
        assert res.status_code == 200
        # Admin panel
        res = client.get('/admin/')
        assert res.status_code == 200

        # Model view
        res = client.get('/admin/testmodel/')
        assert res.status_code == 200

        # Base view
        res = client.get('/admin/testbase/')
        assert res.status_code == 200
        res = client.get('/admin/testbase/foo/')
        assert res.status_code == 200

    # User 2 is missing ActioNeed(admin-access) and thus can't access admin.
    # 403 error returned.
    with app.test_client() as client:
        res = client.get('/login/?user=2')
        # Admin panel
        res = client.get("/admin/")
        assert res.status_code == 403

        # Model view
        res = client.get("/admin/testmodel/")
        assert res.status_code == 403

        # Base view
        res = client.get('/admin/testbase/')
        assert res.status_code == 403
        res = client.get('/admin/testbase/foo/')
        assert res.status_code == 403


def test_menu_visiblity(app):
    """Test menu visiblity."""
    @app.route('/menu/')
    def render_menu():
        settings_menu = app.extensions['menu'].submenu('settings')
        return ';'.join([i.url for i in settings_menu.children if i.visible])

    with app.test_client() as client:
        res = client.get('/menu/')
        assert '/admin/' not in res.get_data(as_text=True)
        res = client.get('/login/?user=1')
        assert res.status_code == 200
        res = client.get('/menu/')
        assert '/admin/' in res.get_data(as_text=True)


def test_custom_permissions(app, testmodelcls):
    """Test custom permissions."""
    class CustomModel(testmodelcls):
        """Some custom model."""
        pass

    class CustomView(ModelView):
        """Some custom model."""
        @staticmethod
        def is_accessible():
            """Check if accessible."""
            return False

    protected_view = protected_adminview_factory(CustomView)
    app.extensions['admin'][0].add_view(
        protected_view(CustomModel, db.session))

    with app.test_client() as client:
        res = client.get('/login/?user=1')
        assert res.status_code == 200
        res = client.get('/admin/')
        assert res.status_code == 200
        res = client.get('/admin/testmodel/')
        assert res.status_code == 200
        res = client.get('/admin/testbase/')
        assert res.status_code == 200
        res = client.get('/admin/custommodel/')
        assert res.status_code == 403


class MockEntryPoint(EntryPoint):
    """Mock of EntryPoint."""

    def load(self):
        """Mock the load of entry point."""
        mod = importlib.import_module(self.module_name)
        obj = getattr(mod, self.name)
        return obj


def _mock_iter_entry_points(group=None):
    """Mock the entry point iterator."""
    data = {
        'invenio_admin.views_invalid': [
            MockEntryPoint('zero', 'demo.onetwo'),
        ],
        'invenio_admin.views': [
            MockEntryPoint('one', 'demo.onetwo'),
            MockEntryPoint('two', 'demo.onetwo'),
            MockEntryPoint('three', 'demo.three'),
            MockEntryPoint('four', 'demo.four'),
        ]
    }
    names = data.keys() if group is None else [group]
    for key in names:
        for entry_point in data[key]:
            yield entry_point


@patch('pkg_resources.iter_entry_points', _mock_iter_entry_points)
def test_invalid_entry_points():
    """Test invalid admin views discovery through entry points."""
    app = Flask('testapp')
    admin_app = InvenioAdmin()
    with pytest.raises(Exception) as e:
        admin_app.init_app(
            app, entry_point_group='invenio_admin.views_invalid'
        )
    assert '"view_class"' in str(e)


@patch('pkg_resources.iter_entry_points', _mock_iter_entry_points)
def test_entry_points():
    """Test admin views discovery through entry points."""
    from flask_principal import Permission
    app = Flask('testapp')
    admin_app = InvenioAdmin(
        app,
        permission_factory=lambda x: Permission(),
        view_class_factory=lambda x: x)
    # Check if model views were added by checking the labels of menu items
    menu_items = {str(item.name): item for item in admin_app.admin.menu()}
    assert 'OneAndTwo' in menu_items  # Category for ModelOne and ModelTwo
    assert 'Four' in menu_items  # Category for ModelOne and ModelTwo
    assert 'Model One' not in menu_items  # ModelOne should go to a category
    assert 'Model Two' not in menu_items  # ModelTwo should go to a category
    assert 'Model Three' in menu_items  # ModelThree goes straight to menu
    assert isinstance(menu_items['Model Three'], flask_admin.menu.MenuView)
    assert isinstance(menu_items['OneAndTwo'], flask_admin.menu.MenuCategory)
    assert menu_items['OneAndTwo'].is_category()
    assert not menu_items['Model Three'].is_category()
    submenu_items = {str(item.name): item for item in
                     menu_items['OneAndTwo'].get_children()}
    assert 'Model One' in submenu_items
    assert 'Model Two' in submenu_items
    assert not submenu_items['Model One'].is_category()
    assert not submenu_items['Model Two'].is_category()
    assert isinstance(submenu_items['Model One'], flask_admin.menu.MenuView)
    assert isinstance(submenu_items['Model Two'], flask_admin.menu.MenuView)
    four_item = menu_items['Four'].get_children()[0]
    assert four_item.name == 'View number Four'
    assert isinstance(four_item, flask_admin.menu.MenuView)


def test_talisman_csp_config_overridden(app):
    """Test that the CSP config of Talisman is set to None."""
    class Talisman:
        """Fake Talisman class."""
        def __init__(self):
            from werkzeug.local import Local
            self.local_options = Local()
            setattr(self.local_options, 'content_security_policy',
                    "'default-src': '\'self\'")

    class InvenioApp:
        """Fake Invenio App class."""
        def __init__(self, talisman):
            print('ciao')
            self.talisman = talisman

    app.extensions['invenio-app'] = InvenioApp(Talisman())
    invenio_app = app.extensions['invenio-app']
    assert invenio_app.talisman.local_options.content_security_policy

    with app.test_client() as client:
        res = client.get('/login/?user=1')
        assert res.status_code == 200
        res = client.get('/admin/')
        assert res.status_code == 200
        assert not invenio_app.talisman.local_options.content_security_policy
