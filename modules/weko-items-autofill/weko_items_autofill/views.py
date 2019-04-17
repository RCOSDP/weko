# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Items-Autofill is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-items-autofill."""

from __future__ import absolute_import, print_function

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_babelex import gettext as _
from flask_login import login_required

from .permissions import auto_fill_permission
from .utils import get_cinii_data, get_crossref_data, get_item_id, \
    parse_cinii_json_response, parse_crossref_json_response
from weko_admin.utils import get_current_api_certification

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


@blueprint_api.route('/get_items_autofill_data', methods=['POST'])
@login_required
@auto_fill_permission.require(http_exception=403)
def get_items_autofill_data():
    """Get auto fill metadata from API response.

    :return: result, response from API
    """
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
        if api_type == 'CrossRef':
            pid_response = get_current_api_certification('crf')
            pid = pid_response['cert_data']
            api_response = get_crossref_data(pid, search_data)
            result['result'] = parse_crossref_json_response(api_response,
                                                            result['items'])
        elif api_type == 'CiNii':
            api_response = get_cinii_data(search_data)
            result['result'] = parse_cinii_json_response(api_response,
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
    """Get metadata  select options.

    :return: json: Metadata select options
    """
    options = [{'value': 'Default', 'text': _('Select the ID')}]
    options.extend(current_app.config['WEKO_ITEMS_AUTOFILL_SELECT_OPTION'])
    result = {
        'options': options
    }
    return jsonify(result)
