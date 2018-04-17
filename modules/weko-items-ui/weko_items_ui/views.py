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

"""Blueprint for weko-items-ui."""

import os

import redis
from flask import Blueprint, current_app, flash, json, jsonify, redirect, \
    render_template, request, session, url_for
from flask_babelex import gettext as _
from flask_login import login_required
from invenio_records_ui.signals import record_viewed
from simplekv.memory.redisstore import RedisStore
from weko_groups.api import Group
from weko_records.api import ItemTypes

from .permissions import item_permission

blueprint = Blueprint(
    'weko_items_ui',
    __name__,
    url_prefix='/items',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/", methods=['GET'])
@blueprint.route("/<int:item_type_id>", methods=['GET'])
@login_required
@item_permission.require(http_exception=403)
def index(item_type_id=0):
    """Renders an item register view.

    :param item_type_id: Item type ID. (Default: 0)
    :return: The rendered template.
    """
    current_app.logger.debug(item_type_id)
    lists = ItemTypes.get_latest()
    if lists is None or len(lists) == 0:
        return render_template(
            current_app.config['WEKO_ITEMS_UI_ERROR_TEMPLATE']
        )
    item_type = ItemTypes.get_by_id(item_type_id)
    if item_type is None:
        return redirect(
            url_for('.index', item_type_id=lists[0].item_type[0].id))
    json_schema = '/items/jsonschema/{}'.format(item_type_id)
    schema_form = '/items/schemaform/{}'.format(item_type_id)
    need_file = False
    if 'filemeta' in json.dumps(item_type.schema):
        need_file = True
    return render_template(
        current_app.config['WEKO_ITEMS_UI_FORM_TEMPLATE'],
        need_file=need_file,
        record={},
        jsonschema=json_schema,
        schemaform=schema_form,
        lists=lists,
        id=item_type_id,
        files=[]
    )


# @blueprint.route("/edit/<int:pid>", methods=['GET'])
# @login_required
# @item_permission.require(http_exception=403)
# def edit(pid=0):
#     """Renders an item edit view.
#
#     :param pid: PID value. (Default: 0)
#     :return: The rendered template.
#     """
#     current_app.logger.debug(pid)
#     return "OK"


@blueprint.route('/jsonschema/<int:item_type_id>', methods=['GET'])
@login_required
@item_permission.require(http_exception=403)
def get_json_schema(item_type_id=0):
    """Get json schema.

    :param item_type_id: Item type ID. (Default: 0)
    :return: The json object.
    """
    current_app.logger.debug(item_type_id)
    result = None
    if item_type_id > 0:
        result = ItemTypes.get_record(item_type_id)
        if 'filemeta' in json.dumps(result):
            group_list = Group.get_group_list()
            group_enum = list(group_list.keys())
            filemeta_group = result.get('properties').get('filemeta').get(
                'items').get('properties').get('groups')
            filemeta_group['enum'] = group_enum
    current_app.logger.debug(result)
    if result is None:
        return '{}'
    return jsonify(result)


@blueprint.route('/schemaform/<int:item_type_id>', methods=['GET'])
@login_required
@item_permission.require(http_exception=403)
def get_schema_form(item_type_id=0):
    """Get schema form.

    :param item_type_id: Item type ID. (Default: 0)
    :return: The json object.
    """
    current_app.logger.debug(item_type_id)
    cur_lang = 'default'
    if current_app.config['I18N_SESSION_KEY'] in session:
        cur_lang = session[current_app.config['I18N_SESSION_KEY']]
    current_app.logger.debug('cur_lang: ' + cur_lang)
    result = None
    if item_type_id > 0:
        result = ItemTypes.get_by_id(item_type_id)
    if result is None:
        return '["*"]'
    current_app.logger.debug(result.form)
    schema_form = result.form
    filemeta_form = schema_form[0]
    if 'filemeta' == filemeta_form.get('key'):
        group_list = Group.get_group_list()
        filemeta_form_group = filemeta_form.get('items')[-1]
        filemeta_form_group['type'] = 'select'
        filemeta_form_group['titleMap'] = group_list
    if 'default' != cur_lang:
        for elem in schema_form:
            if 'title_i18n' in elem:
                if cur_lang in elem['title_i18n']:
                    if len(elem['title_i18n'][cur_lang]) > 0:
                        elem['title'] = elem['title_i18n'][cur_lang]
            if 'type' in elem and 'fieldset' == elem['type']:
                for sub_elem in elem['items']:
                    if 'title_i18n' in sub_elem:
                        if cur_lang in sub_elem['title_i18n']:
                            if len(sub_elem['title_i18n'][cur_lang]) > 0:
                                sub_elem['title'] = sub_elem['title_i18n'][
                                    cur_lang]
    return jsonify(schema_form)


@blueprint.route("/index/<int:pid_value>", methods=['GET', 'PUT', 'POST'])
@login_required
@item_permission.require(http_exception=403)
def items_index(pid_value=0):
    if pid_value == 0:
        return redirect(url_for('.index'))
    if request.method == 'GET':
        return render_template(
            current_app.config['WEKO_ITEMS_UI_INDEX_TEMPLATE'],
            pid_value=pid_value)
    if request.headers['Content-Type'] != 'application/json':
        flash(_('invalide request'), 'error')
        return render_template(
            current_app.config['WEKO_ITEMS_UI_INDEX_TEMPLATE'])

    data = request.get_json()
    sessionstore = RedisStore(redis.StrictRedis.from_url(
        'redis://{host}:{port}/1'.format(
            host=os.getenv('INVENIO_REDIS_HOST', 'localhost'),
            port=os.getenv('INVENIO_REDIS_PORT', '6379'))))
    if request.method == 'PUT':
        """ update index of item info """
        item_str = sessionstore.get('item_index_{}'.format(pid_value))
        sessionstore.delete('item_index_{}'.format(pid_value))
        current_app.logger.debug(item_str)
        item = json.loads(item_str)
        item['index'] = data
        current_app.logger.debug(item)
    elif request.method == 'POST':
        """ update item data info """
        current_app.logger.debug(data)
        sessionstore.put('item_index_{}'.format(pid_value), json.dumps(data),
                         ttl_secs=300)
    return jsonify(data)


def default_view_method(pid, record, template=None):
    """Default view method.

    Sends ``record_viewed`` signal and renders template.
    """
    record_viewed.send(
        current_app._get_current_object(),
        pid=pid,
        record=record,
    )

    item_type_id = record.get('item_type_id')
    lists = ItemTypes.get_latest()
    if lists is None or len(lists) == 0:
        return render_template(
            current_app.config['WEKO_ITEMS_UI_ERROR_TEMPLATE']
        )
    item_type = ItemTypes.get_by_id(item_type_id)
    if item_type is None:
        return redirect(
            url_for('.index', item_type_id=lists[0].item_type[0].id))
    json_schema = '/items/jsonschema/{}'.format(item_type_id)
    schema_form = '/items/schemaform/{}'.format(item_type_id)
    need_file = False
    if 'filemeta' in json.dumps(item_type.schema):
        need_file = True
    return render_template(
        template,
        need_file=need_file,
        record=record.item_metadata,
        jsonschema=json_schema,
        schemaform=schema_form,
        lists=lists,
        id=item_type_id,
        files=to_files_js(record),
        pid=pid
    )


def to_files_js(record):
    """List files in a deposit."""
    res = []

    for f in record.files:
        res.append({
            'key': f.key,
            'version_id': f.version_id,
            'checksum': f.file.checksum,
            'size': f.file.size,
            'completed': True,
            'progress': 100,
            'links': {
                'self': (
                    current_app.config['DEPOSIT_FILES_API'] +
                    u'/{bucket}/{key}?versionId={version_id}'.format(
                        bucket=f.bucket_id,
                        key=f.key,
                        version_id=f.version_id,
                    )),
            }
        })

    return res


@blueprint.route("/demo", methods=['GET'])
@login_required
def index_demo():
    """Renders an item test data upload view.

    :return: The rendered template.
    """
    return render_template(
        current_app.config['WEKO_ITEMS_UI_DEMO_TEMPLATE']
    )
