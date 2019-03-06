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
from .crossref_api import Works
from .utils import get_items_autofill, parse_crossref_response
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
        if api_type == 'CrossRef':
            api = Works()
            api_response = api.doi(search_data)
            result['result'] = parse_crossref_response(api_response)
            result['items'] = get_items_autofill(item_type_id)
        elif api_type == 'Amazon':
            pass

    except Exception as e:
        result['error'] = str(e)

    return jsonify(result)


@blueprint_api.route('/select_options', methods=['GET'])
@login_required
@auto_fill_permission.require(http_exception=403)
def get_selection_option():
    result = config.WEKO_ITEMS_AUTOFILL_SELECT_OPTION
    return jsonify(result)
