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

"""Blueprint for weko-plugins."""

from flask import Blueprint, render_template
from flask_babelex import gettext as _
from flask_plugins import get_plugin

blueprint = Blueprint(
    'weko_plugins',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/plugins'
)


@blueprint.route('/')
def index():
    """Render a basic view."""

    return render_template(
        'weko_plugins/index.html',
        module_name=_('weko-plugins')
    )


@blueprint.route('/setting/<plugin>', methods=['GET'])
def setting(plugin):
    """
    Set plugin base info
    :param plugin:
    :return:
    """
    plugin = get_plugin(plugin)
    return render_template(
        'weko_plugins/plugin_setting.html',
        plugin=plugin
    )
