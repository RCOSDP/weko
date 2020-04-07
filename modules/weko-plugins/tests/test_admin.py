# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""WEKO3 module docstring."""

from flask import url_for
from flask_admin import Admin, menu
from flask_plugins import get_plugin

from weko_plugins import wekoplugins
from weko_plugins.admin import plugin_adminview


def test_admin(app):
    """Test Weko-Plugin interace."""
    wekoplugins(app)
    admin = Admin(app, name='Test')

    assert 'view_class' in plugin_adminview
    assert 'kwargs' in plugin_adminview

    # Register both models in admin
    view_class = plugin_adminview.pop('view_class')
    kwargs = plugin_adminview.pop('kwargs')
    admin.add_view(view_class(**kwargs))

    # Check if generated admin menu contains the correct items
    menu_items = {str(item.name): item for item in admin.menu()}
    assert 'Plugins' in menu_items
    assert menu_items['Plugins'].is_category()

    submenu_items = {
        str(item.name): item for item in menu_items['Plugins'].get_children()
    }
    assert 'Plugin List' in submenu_items
    assert isinstance(submenu_items['Plugin List'], menu.MenuView)

    with app.test_request_context():
        index_view_url = url_for('pluginsetting.index')
        assert '/admin/pluginsetting/' == index_view_url
        detail_view_url = url_for('pluginsetting.detail',
                                  plugin='hello_world')
        assert '/admin/pluginsetting/hello_world' == detail_view_url
        setting_view_url = url_for('pluginsetting.setting',
                                   plugin='hello_world')
        assert '/admin/pluginsetting/setting/hello_world' == setting_view_url
        disable_view_url = url_for('pluginsetting.disable',
                                   plugin='hello_world')
        assert '/admin/pluginsetting/disable/hello_world' == disable_view_url
        enable_view_url = url_for('pluginsetting.enable',
                                  plugin='hello_world')
        assert '/admin/pluginsetting/enable/hello_world' == enable_view_url
        delete_view_url = url_for('pluginsetting.delete',
                                  plugin='hello_world')
        assert '/admin/pluginsetting/delete/hello_world' == delete_view_url

    with app.test_client() as client:
        # List plugin view.
        res = client.get(index_view_url)
        assert res.status_code == 200

        # List plugin view.
        res = client.get(detail_view_url)
        assert res.status_code == 200

        # List plugin view.
        res = client.get(setting_view_url)
        assert res.status_code == 200

        # List plugin view.
        res = client.get(disable_view_url)
        assert res.status_code == 302
        plugin = get_plugin('hello_world')
        assert plugin.enabled is False

        # List plugin view.
        res = client.get(enable_view_url)
        assert res.status_code == 302
        plugin = get_plugin('hello_world')
        assert plugin.enabled is True

        # List plugin view.
        res = client.get(delete_view_url)
        assert res.status_code == 302
        try:
            plugin = get_plugin('hello_world')
            assert 1 == 0
        except KeyError:
            # test success when except is happened
            assert 1 == 1
