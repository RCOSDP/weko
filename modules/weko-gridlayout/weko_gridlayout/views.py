# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-gridlayout is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-gridlayout."""

# TODO: This is an example file. Remove it if you do not need it, including
# the templates and static folders as well as the test case.

from __future__ import absolute_import, print_function

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_babelex import gettext as _
from flask_login import current_user, login_required

from .api import WidgetItems
from .utils import get_repository_list, get_widget_design_setting, \
    get_widget_list, update_admin_widget_item_setting

blueprint = Blueprint(
    'weko_gridlayout',
    __name__,
    template_folder='templates',
    static_folder='static',
)

blueprint_api = Blueprint(
    'weko_gridlayout',
    __name__,
    url_prefix='/admin',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/")
def index():
    """Render a basic view."""
    return render_template(
        "weko_gridlayout/index.html",
        module_name=_('weko-gridlayout'))


@blueprint_api.route('/load_repository', methods=['GET'])
def load_repository():
    """Get Repository list, to display on the combobox on UI.

        :return: Example
        {
           'repositories': [
            {
                'id': 'repository id',
                'title': 'repository title'
            }
           ],
            'error': ''
        }
    """
    result = get_repository_list()
    return jsonify(result)


@blueprint_api.route('/load_widget_list/<string:repository_id>', methods=['GET'])
def load_widget_list(repository_id):
    """Get Widget list, to display on the Widget List panel on UI.

            :return: Example
            "widget-list": [
                {
                    "widgetId": "widget id",
                    "widgetLabel": "Widget label"
                }
            ],
            "error": ""
    """
    result = get_widget_list(repository_id)
    return jsonify(result)


@blueprint_api.route('/load_widget_design_setting/<string:repository_id>',
                     methods=['GET'])
def load_widget_design_setting(repository_id):
    result = get_widget_design_setting(repository_id)

    return jsonify(result)


@blueprint_api.route('/save_widget_layout_setting', methods=['POST'])
def save_widget_layout_setting():
    result = dict()

    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    result = update_widget_design_setting(data)

    return jsonify(result)


@blueprint_api.route('/load_widget_type', methods=['GET'])
@login_required
def load_widget_type():
    """Get Widget Type List."""
    from .utils import get_widget_type_list
    results = get_widget_type_list()
    return jsonify(results)

@blueprint_api.route('/save_widget_item', methods=['POST'])
@login_required
def save_widget_item():
    """Save Language List."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg='Header Error')
    data = request.get_json()
    status = WidgetItems().create(data)
    return jsonify(status)

@blueprint_api.route('/get_account_role', methods=['GET'])
@login_required
def get_account_role():
    role = WidgetItems().get_account_role()
    return jsonify(role)
