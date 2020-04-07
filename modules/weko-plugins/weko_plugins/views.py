# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

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
    Set plugin base info.

    :param plugin:
    :return:

    """
    plugin = get_plugin(plugin)
    return render_template(
        'weko_plugins/plugin_setting.html',
        plugin=plugin
    )
