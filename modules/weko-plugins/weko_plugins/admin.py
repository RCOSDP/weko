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

"""WEKO3 module docstring."""

from flask import redirect, request, url_for
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from flask_plugins import get_enabled_plugins, get_plugin

from .proxies import current_plugins


class PluginSettingView(BaseView):
    @expose('/', methods=['GET'])
    def index(self):
        """
        Get plugins list info
        :return:
        """
        # current_plugins.plugin_manager.load_plugins()
        return self.render(
            'weko_plugins/admin/plugin_list.html',
            plugins=get_enabled_plugins()
        )

    @expose('/<plugin>', methods=['GET'])
    def detail(self, plugin):
        """
        Get plugin base info
        :param plugin:
        :return:
        """
        plugin = get_plugin(plugin)
        return self.render(
            'weko_plugins/admin/plugin_detail.html',
            plugin=plugin
        )

    @expose('/setting/<plugin>', methods=['GET'])
    def setting(self, plugin):
        """
        Set plugin base info
        :param plugin:
        :return:
        """
        plugin = get_plugin(plugin)
        return self.render(
            'weko_plugins/admin/plugin_setting.html',
            plugin=plugin
        )

    @expose('/disable/<plugin>', methods=['GET'])
    def disable(self, plugin):
        """
        Disable the plugin
        :param plugin:
        :return:
        """
        plugin = get_plugin(plugin)
        current_plugins.plugin_manager.disable_plugins([plugin])
        redirect_url = url_for('pluginsetting.index')
        href = request.args.get('href', 'index')
        if 'detail' == href:
            redirect_url = url_for('pluginsetting.detail',
                                   plugin=plugin.identifier)
        return redirect(redirect_url)

    @expose('/enable/<plugin>', methods=['GET'])
    def enable(self, plugin):
        """
        Enable the plugin
        :param plugin:
        :return:
        """
        plugin = get_plugin(plugin)
        current_plugins.plugin_manager.enable_plugins([plugin])
        redirect_url = url_for('pluginsetting.index')
        href = request.args.get('href', 'index')
        if 'detail' == href:
            redirect_url = url_for('pluginsetting.detail',
                                   plugin=plugin.identifier)
        return redirect(redirect_url)

    @expose('/delete/<plugin>', methods=['GET'])
    def delete(self, plugin):
        """
        Delete the plugin
        :param plugin:
        :return:
        """
        plugin = get_plugin(plugin)
        if plugin is not None:
            plugin.delete()
            del current_plugins.plugin_manager.plugins[plugin.identifier]
            # del current_plugins.plugin_manager.all_plugins[plugin.identifier]
        return redirect(url_for('pluginsetting.index'))


plugin_adminview = {
    'view_class': PluginSettingView,
    'kwargs': {
        'category': _('Plugins'),
        'name': _('Plugin List'),
        'endpoint': 'pluginsetting'
    }
}

__all__ = (
    'plugin_adminview',
)
