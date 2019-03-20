# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Items-Autofill is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-items-autofill."""

from __future__ import absolute_import, print_function

from flask import Blueprint, jsonify, render_template, request
from flask_babelex import gettext as _
from flask_login import login_required

from .permissions import auto_fill_permission
from .utils import parse_crossref_json_response, get_item_id, get_crossref_data, get_item_path
from . import config

blueprint = Blueprint(
    "weko_items_autofill",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/autofill",
)

blueprint_api = Blueprint(
    "weko_items_autofill",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/autofill",
)


@blueprint.route("/")
def index():
    """Render a basic view."""
    return render_template(
        "weko_items_autofill/index.html", module_name=_("WEKO-Items-Autofill")
    )


@blueprint_api.route('/crossref_api', methods=['POST'])
@login_required
@auto_fill_permission.require(http_exception=403)
def get_items_autofill_data():
    result = {
        'result': '',
        'items': '',
        'error': ''
    }
    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    api_type = data.get('api_type', '')
    search_data = data.get('search_data', '')
    item_type_id = data.get('item_type_id', '')

    try:
        result['items'] = get_item_id(item_type_id)
		result['path'] = get_item_path(item_type_id)
        if api_type == 'CrossRef':
            pid = config.WEKO_ITEMS_AUTOFILL_CROSSREF_API_PID
            api_response = get_crossref_data(pid, search_data)
            result['result'] = parse_crossref_json_response(api_response,
                                                            result['items'])
        else:
            result['error'] = api_type + ' is NOT support autofill feature.'
    except Exception as e:
        result['error'] = str(e)

    return jsonify(result)


@blueprint_api.route('/select_options', methods=['GET'])
@login_required
@auto_fill_permission.require(http_exception=403)
def get_selection_option():
    options = [{'value': 'Default', 'text': _('Select the ID')}]
    options.extend(config.WEKO_ITEMS_AUTOFILL_SELECT_OPTION)
    result = {
        'options': options
    }
    return jsonify(result)


@blueprint_api.route('/get_item_map/<int:item_type_id>', methods=['GET'])
def get_item_map(item_type_id=0):
    """
    host to ~/api/autofill/get_item_map/{id}
    function return the dictionary of sub item id
    """
    results = get_item_id(item_type_id)
    return jsonify(results)


@blueprint_api.route('/get_item_type/<int:item_type_id>', methods=['GET'])
def get_item_type(item_type_id=0):
    """
    host to ~/api/autofill/get_item_map/{id}
    function return the dictionary of sub item id
    """
    results = get_item_path(item_type_id)
    return jsonify(results)