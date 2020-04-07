# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Blueprint for weko-itemtypes-ui."""


from flask import Blueprint, current_app, jsonify
from flask_babelex import gettext as _
from flask_login import login_required
from weko_records.api import Mapping

blueprint = Blueprint(
    'weko_itemtypes_ui',
    __name__,
    url_prefix='/itemtypes',
    template_folder='templates',
    static_folder='static',
)

blueprint_api = Blueprint(
    'weko_itemtypes_rest',
    __name__,
    url_prefix='/itemtypes',
    template_folder='templates',
    static_folder='static',
)


@blueprint_api.route('/<int:ItemTypeID>/mapping', methods=['GET'])
def itemtype_mapping(ItemTypeID=0):
    """Itemtype mapping."""
    item_type_mapping = Mapping.get_record(ItemTypeID)
    return jsonify(item_type_mapping)
