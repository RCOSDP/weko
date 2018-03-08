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

from flask import abort, Blueprint, current_app, json, jsonify, redirect, \
    render_template, request, url_for, Flask, make_response
from flask_babelex import gettext as _
from flask_login import login_required, current_user
from invenio_db import db
from weko_records.api import ItemTypes, ItemTypeProps, Mapping

from .permissions import item_type_permission

blueprint = Blueprint(
    'weko_itemtypes_ui',
    __name__,
    url_prefix='/itemtypes',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/", methods=['GET'])
@blueprint.route("/<int:item_type_id>", methods=['GET'])
@blueprint.route("/register", methods=['GET'])
@login_required
@item_type_permission.require(http_exception=403)
def index(item_type_id=0):
    """Renders an item type register view.

    :param item_type_id: Item type i. Default 0.
    """
    lists = ItemTypes.get_latest()
    return render_template(
        current_app.config['WEKO_ITEMTYPES_UI_REGISTER_TEMPLATE'],
        lists=lists,
        id=item_type_id
    )


@blueprint.route("/<int:item_type_id>/render", methods=['GET'])
@login_required
@item_type_permission.require(http_exception=403)
def render(item_type_id=0):
    result = None
    if item_type_id > 0:
        result = ItemTypes.get_by_id(id_=item_type_id)
    if result is None:
        result = {
            'table_row': [],
            'table_row_map': {},
            'meta_list': {},
            'schemaeditor': {
                'schema': {}
            }
        }
    return jsonify(result.render)


@blueprint.route("/register", methods=['POST'])
@blueprint.route("/<int:item_type_id>/register", methods=['POST'])
@login_required
@item_type_permission.require(http_exception=403)
def register(item_type_id=0):
    """Register an item type."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg=_('Header Error'))

    data = request.get_json()
    try:
        record = ItemTypes.update(id_=item_type_id,
                                  name=data.get('table_row_map').get('name'),
                                  schema=data.get('table_row_map').get(
                                      'schema'),
                                  form=data.get('table_row_map').get('form'),
                                  render=data)
        Mapping.create(item_type_id=record.model.id,
                       mapping=data.get('table_row_map').get('mapping'))
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify(msg=_('Fail'))
    current_app.logger.debug('itemtype register: {}'.format(item_type_id))
    return jsonify(msg=_('Success'))


@blueprint.route("/property", methods=['GET'])
@login_required
@item_type_permission.require(http_exception=403)
def custom_property(property_id=0):
    """Renders an primitive property view."""
    lists = ItemTypeProps.get_records([])
    return render_template(
        current_app.config['WEKO_ITEMTYPES_UI_CREATE_PROPERTY'],
        lists=lists
    )


@blueprint.route("/property/list", methods=['GET'])
@login_required
@item_type_permission.require(http_exception=403)
def get_property_list(property_id=0):
    """Renders an primitive property view."""
    props = ItemTypeProps.get_records([])
    lists = {}
    for k in props:
        tmp = {}
        tmp['name'] = k.name
        tmp['schema'] = k.schema
        tmp['form'] = k.form
        tmp['forms'] = k.forms
        lists[k.id] = tmp

    return jsonify(lists)


@blueprint.route("/property/<int:property_id>", methods=['GET'])
@login_required
@item_type_permission.require(http_exception=403)
def get_property(property_id=0):
    """Renders an primitive property view."""
    prop = ItemTypeProps.get_record(property_id)
    tmp = {}
    tmp['id'] = prop.id
    tmp['name'] = prop.name
    tmp['schema'] = prop.schema
    tmp['form'] = prop.form
    tmp['forms'] = prop.forms
    return jsonify(tmp)


@blueprint.route("/property", methods=['POST'])
@blueprint.route("/property/<int:property_id>", methods=['POST'])
@login_required
@item_type_permission.require(http_exception=403)
def custom_property_new(property_id=0):
    """Register an item type."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg=_('Header Error'))

    data = request.get_json()
    try:
        ItemTypeProps.create(property_id=property_id,
                             name=data.get('name'),
                             schema=data.get('schema'),
                             form_single=data.get('form1'),
                             form_array=data.get('form2'))
        db.session.commit()
    except Exception as ex:
        current_app.logger.debug(ex)
        db.session.rollback()
        return jsonify(msg=_('Fail'))
    return jsonify(msg=_('Success'))


@blueprint.route("/mapping", methods=['GET'])
@blueprint.route("/mapping/<int:ItemTypeID>", methods=['GET'])
@login_required
@item_type_permission.require(http_exception=403)
def mapping_index(ItemTypeID=0):
    """Renders an item type mapping view.

    :param ItemTypeID: Item type ID. (Default: 0)
    :return: The rendered template.
    """
    lists = ItemTypes.get_all()
    if lists is None or len(lists) == 0:
        return render_template(
            current_app.config['WEKO_ITEMTYPES_UI_ERROR_TEMPLATE']
        )
    item_type = ItemTypes.get_by_id(ItemTypeID)
    if item_type is None:
        return redirect(url_for('.mapping_index', ItemTypeID=lists[0].id))
    item_type_mapping = Mapping.get_record(ItemTypeID)
    mapping = json.dumps(item_type_mapping, indent=4, ensure_ascii=False)
    current_app.logger.debug(mapping)
    return render_template(
        current_app.config['WEKO_ITEMTYPES_UI_MAPPING_TEMPLATE'],
        lists=lists,
        mapping=mapping,
        id=ItemTypeID
    )


@blueprint.route("/mapping", methods=['POST'])
@login_required
@item_type_permission.require(http_exception=403)
def mapping_register():
    """Register an item type mapping."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg=_('Header Error'))

    data = request.get_json()
    current_app.logger.debug(data)
    try:
        Mapping.create(item_type_id=data.get('item_type_id'),
                       mapping=json.loads(data.get('mapping')))
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify(msg=_('Fail'))
    return jsonify(msg=_('Success'))
