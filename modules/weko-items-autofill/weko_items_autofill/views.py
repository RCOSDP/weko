# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Items-Autofill is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-items-autofill."""

# TODO: This is an example file. Remove it if you do not need it, including
# the templates and static folders as well as the test case.

from __future__ import absolute_import, print_function

from flask import Blueprint, jsonify, render_template, request
from flask_babelex import gettext as _

from flask_login import login_required

from .permissions import auto_fill_permission
from .api import AmazonApi
from . import config

blueprint = Blueprint(
    'weko_items_autofill',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/items/autofill',
)
blueprint_api = Blueprint(
    'weko_items_autofill',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/items/autofill',
)


@blueprint.route("/")
def index():
    """Render a basic view."""
    return render_template(
        "weko_items_autofill/index.html",
        module_name=_('WEKO-Items-Autofill'))


@blueprint_api.route("/search/<id_type>/<item_id>",
                     methods=['GET'])
# @login_required
# @auto_fill_permission.require(http_exception=403)
def search_amazon_data(id_type, item_id):
    """Get data from Amazon Advertising API.
    :type id_type: str id type
    :type item_id: str item id
    :return
    """
    # data = request.get_json()
    # id_type = data.get('idType')
    # item_id = data.get('itemId')
    result_test = {
        'title': 'Title',
        'sourceTitle': 'Source Title',
        'language': 'English',
        'creator': 'Amazon Creator',
        'pageStart': '1',
        'pageEnd': '10',
        'date': '2019-02-19',
        'publisher': 'Amazon JP',
        'relatedIdentifier': '076243631X'
    }
    if id_type and item_id:
        api = AmazonApi(config.WEKO_ITEMS_AUTOFILL_AWS_ACCESS_KEY_ID,
                        config.WEKO_ITEMS_AUTOFILL_AWS_SECRET_ACCESS_KEY,
                        config.WEKO_ITEMS_AUTOFILL_ASSOCIATE_TAG)
        response_data = api.search(id_type, item_id)
    else:
        response_data = {'error': 'Please input item id!'}

    return jsonify(result_test)
