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

"""Blueprint for weko-itemtypes-ui."""


from flask import Blueprint, jsonify, request,current_app
from weko_records.api import ItemTypes, Mapping
from invenio_db import db


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


@blueprint_api.route('/lastest', methods=['GET'])
def get_itemtypes():
    """Get List Itemtype."""
    def convert(item):
        item_type = item.item_type.first()
        return {
            'id': item_type.id,
            'name': item.name,
            'tag': item_type.tag,
            'harvesting_type': item_type.harvesting_type,
            'is_deleted': item_type.is_deleted
        }

    item_types = list(map(convert, ItemTypes.get_latest(True)))
    filter_type = request.args.get('type') or None
    if filter_type == 'harvesting_type':
        item_types = [
            item for item in item_types
            if item['harvesting_type']
        ]
    elif filter_type == 'deleted_type':
        item_types = [
            item for item in item_types
            if item['is_deleted']
        ]
    elif filter_type == 'normal_type':
        item_types = [
            item for item in item_types
            if not (item['is_deleted'] or item['harvesting_type'])
        ]
    elif filter_type == 'all_type':
        item_types = [
            item for item in item_types
            if not (item['is_deleted'])
        ]

    return jsonify(item_types)


@blueprint.app_template_filter('replace_mapping_version')
def replace_mapping_version(jp_key):
    """Replace mapping version key.

    :param jp_key:
    :return:
    """
    if jp_key == "versiontype":
        return "version(oaire)"
    elif jp_key == "version":
        return "version(datacite)"
    return jp_key

@blueprint.teardown_request
@blueprint_api.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("weko_itemtypes_ui dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()