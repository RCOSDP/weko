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

import sys

from flask import Blueprint, Flask, abort, current_app, json, jsonify, \
    make_response, redirect, render_template, request, url_for, flash
from flask_babelex import gettext as _
from flask_login import login_required
from invenio_db import db
from weko_records.api import ItemTypeProps, ItemTypes, Mapping
from weko_schema_ui.api import WekoSchema
from invenio_i18n.ext import current_i18n

from .permissions import item_type_permission

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


@blueprint.route('/', methods=['GET'])
@blueprint.route('/<int:item_type_id>', methods=['GET'])
@blueprint.route('/register', methods=['GET'])
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


@blueprint.route('/<int:item_type_id>/render', methods=['GET'])
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
    else:
        result = result.render
    return jsonify(result)


@blueprint.route('/register', methods=['POST'])
@blueprint.route('/<int:item_type_id>/register', methods=['POST'])
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
    except BaseException:
        db.session.rollback()
        return jsonify(msg=_('Fail'))
    current_app.logger.debug('itemtype register: {}'.format(item_type_id))
    return jsonify(msg=_('Success'))


@blueprint.route('/property', methods=['GET'])
@login_required
@item_type_permission.require(http_exception=403)
def custom_property(property_id=0):
    """Renders an primitive property view."""
    lists = ItemTypeProps.get_records([])
    return render_template(
        current_app.config['WEKO_ITEMTYPES_UI_CREATE_PROPERTY'],
        lists=lists
    )

@blueprint.route('/property/list', methods=['GET'])
@login_required
@item_type_permission.require(http_exception=403)
def get_property_list(property_id=0):
    """Renders an primitive property view."""
    lang = request.values.get('lang')

    props = ItemTypeProps.get_records([])
    lists = {}
    for k in props:
        name = k.name
        if lang and 'title_i18n' in k.form and \
            lang in k.form['title_i18n'] and k.form['title_i18n'][lang]:
            name = k.form['title_i18n'][lang]

        tmp = {'name': name, 'schema': k.schema, 'form': k.form,
               'forms': k.forms, 'sort': k.sort}
        lists[k.id] = tmp

    lists['defaults'] = current_app.config['WEKO_ITEMTYPES_UI_DEFAULT_PROPERTIES']

    return jsonify(lists)

@blueprint.route('/property/<int:property_id>', methods=['GET'])
@login_required
@item_type_permission.require(http_exception=403)
def get_property(property_id=0):
    """Renders an primitive property view."""
    prop = ItemTypeProps.get_record(property_id)
    tmp = {'id': prop.id, 'name': prop.name, 'schema': prop.schema,
           'form': prop.form, 'forms': prop.forms}
    return jsonify(tmp)


@blueprint.route('/property', methods=['POST'])
@blueprint.route('/property/<int:property_id>', methods=['POST'])
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


@blueprint_api.route('/<int:ItemTypeID>/mapping', methods=['GET'])
def itemtype_mapping(ItemTypeID=0):
    item_type_mapping = Mapping.get_record(ItemTypeID)
    return jsonify(item_type_mapping)


@blueprint.route('/mapping', methods=['GET'])
@blueprint.route('/mapping/<int:ItemTypeID>', methods=['GET'])
@login_required
@item_type_permission.require(http_exception=403)
def mapping_index(ItemTypeID=0):
    """Renders an item type mapping view.

    :param ItemTypeID: Item type ID. (Default: 0)
    :return: The rendered template.
    """
    try:
        lists = ItemTypes.get_latest()    # ItemTypes.get_all()
        if lists is None or len(lists) == 0:
            return render_template(
                current_app.config['WEKO_ITEMTYPES_UI_ERROR_TEMPLATE']
            )
        item_type = ItemTypes.get_by_id(ItemTypeID)
        if item_type is None:
            return redirect(url_for('.mapping_index', ItemTypeID=lists[0].id))
        itemtype_list = []
        itemtype_prop = item_type.schema.get('properties')
        for key, prop in itemtype_prop.items():
            cur_lang = current_i18n.language
            schema_form = item_type.form
            elemStr = ''
            if 'default' != cur_lang:
                for elem in schema_form:
                    if 'items' in elem:
                        for sub_elem in elem['items']:
                            if 'key' in sub_elem and sub_elem['key'] == key:
                                if 'title_i18n' in sub_elem:
                                    if cur_lang in sub_elem['title_i18n']:
                                        if len(sub_elem['title_i18n'][cur_lang]) > 0:
                                            elemStr = sub_elem['title_i18n'][
                                                cur_lang]
                                else:
                                    elemStr = sub_elem['title']
                                break
                    else:
                        if elem['key'] == key:
                            if 'title_i18n' in elem:
                                if cur_lang in elem['title_i18n']:
                                    if len(elem['title_i18n'][cur_lang]) > 0:
                                        elemStr = elem['title_i18n'][
                                            cur_lang]
                            else:
                                elemStr = elem['title']

                    if elemStr != '':
                        break

            if elemStr == '':
                elemStr = prop.get('title')

            itemtype_list.append((key, elemStr))
            # itemtype_list.append((key, prop.get('title')))
        # jpcoar_list = []
        mapping_name = request.args.get('mapping_type', 'jpcoar_mapping')
        jpcoar_xsd = WekoSchema.get_all()
        jpcoar_lists = {}
        for item in jpcoar_xsd:
            jpcoar_lists[item.schema_name] = json.loads(item.xsd)
        # jpcoar_prop = json.loads(jpcoar_xsd.model.xsd)
        # for key in jpcoar_prop.keys():
        #     jpcoar_list.append((key, key))
        item_type_mapping = Mapping.get_record(ItemTypeID)
        # mapping = json.dumps(item_type_mapping, indent=4, ensure_ascii=False)
        return render_template(
            current_app.config['WEKO_ITEMTYPES_UI_MAPPING_TEMPLATE'],
            lists=lists,
            hide_mapping_prop=item_type_mapping,
            mapping_name=mapping_name,
            hide_itemtype_prop=itemtype_prop,
            jpcoar_prop_lists=remove_xsd_prefix(jpcoar_lists),
            itemtype_list=itemtype_list,
            id=ItemTypeID
        )
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


@blueprint.route('/mapping/schema', methods=['GET'])
@blueprint.route('/mapping/schema/', methods=['GET'])
@blueprint.route('/mapping/schema/<string:SchemaName>', methods=['GET'])
@login_required
@item_type_permission.require(http_exception=403)
def schema_list(SchemaName=None):
    jpcoar_lists = {}
    if SchemaName is None:
        jpcoar_xsd = WekoSchema.get_all()
        for item in jpcoar_xsd:
            jpcoar_lists[item.schema_name] = json.loads(item.xsd)
    else:
        jpcoar_xsd = WekoSchema.get_record_by_name(SchemaName)
        if jpcoar_xsd is not None:
            jpcoar_lists[SchemaName] = json.loads(jpcoar_xsd.model.xsd)
    return jsonify(remove_xsd_prefix(jpcoar_lists))


def remove_xsd_prefix(jpcoar_lists):
    jpcoar_copy = {}

    def remove_prefix(jpcoar_src, jpcoar_dst):
        for key, value in jpcoar_src.items():
            if 'type' == key:
                jpcoar_dst[key] = value
                continue
            jpcoar_dst[key.split(':').pop()] = {}
            if isinstance(value, object):
                remove_prefix(value, jpcoar_dst[key.split(':').pop()])

    remove_prefix(jpcoar_lists, jpcoar_copy)
    return jpcoar_copy


@blueprint.route('/mapping', methods=['POST'])
@login_required
@item_type_permission.require(http_exception=403)
def mapping_register():
    """Register an item type mapping."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg=_('Header Error'))

    data = request.get_json()
    try:
        Mapping.create(item_type_id=data.get('item_type_id'),
                       mapping=data.get('mapping'))
        db.session.commit()
    except BaseException:
        db.session.rollback()
        return jsonify(msg=_('Fail'))
    return jsonify(msg=_('Success'))
