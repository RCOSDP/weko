# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-gridlayout is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-gridlayout."""
from __future__ import absolute_import, print_function

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_babelex import gettext as _
from flask_login import login_required

from .api import WidgetItems
from .utils import delete_admin_widget_item_setting, get_repository_list, \
    get_system_language, get_widget_design_setting, get_widget_list, \
    get_widget_preview, get_widget_type_list, \
    update_admin_widget_item_setting, update_widget_design_setting

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
@login_required
def index():
    """Render a basic view."""
    return render_template(
        "weko_gridlayout/index.html",
        module_name=_('weko-gridlayout'))


@blueprint_api.route('/load_repository', methods=['GET'])
@login_required
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


@blueprint_api.route('/load_widget_list_design_setting/<string:repository_id>',
                     methods=['GET'])
@login_required
def load_widget_list_design_setting(repository_id):
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
    result = dict()
    result["widget-list"] = get_widget_list(repository_id)
    result["widget-preview"] = get_widget_preview(repository_id)
    result["error"] = result["widget-list"].get("error") or result[
        "widget-preview"].get("error")
    return jsonify(result)


@blueprint_api.route('/load_widget_design_setting/<string:repository_id>',
                     methods=['GET'])
def load_widget_design_setting(repository_id):
    """Load  Widget design setting from DB by repository id.

    :param repository_id:
    :return:
    """
    result = get_widget_design_setting(repository_id)
    return jsonify(result)


@blueprint_api.route('/save_widget_layout_setting', methods=['POST'])
@login_required
def save_widget_layout_setting():
    """Save Widget design setting into DB.

    :return:
    """
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
    return update_admin_widget_item_setting(data)


@blueprint_api.route('/delete_widget_item', methods=['POST'])
@login_required
def delete_widget_item():
    """Delete Language List."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg='Header Error')
    data = request.get_json()
    return delete_admin_widget_item_setting(data.get('data_id'))


@blueprint_api.route('/get_account_role', methods=['GET'])
@login_required
def get_account_role():
    """Get Account role.

    :return:
    """
    role = WidgetItems().get_account_role()
    return jsonify(role)


@blueprint_api.route('/get_system_lang', methods=['GET'])
def get_system_lang():
    """Get system language.

    Returns:
        language -- list

    """
    result = get_system_language()
    return jsonify(result)
