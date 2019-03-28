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
import sys

import redis
from flask import (
    Blueprint, abort, current_app, flash, json, jsonify, redirect,
    render_template, request, session, url_for)
from flask_babelex import gettext as _
from flask_login import login_required
from invenio_i18n.ext import current_i18n
from invenio_records_ui.signals import record_viewed
from simplekv.memory.redisstore import RedisStore
from weko_groups.api import Group
from weko_records.api import ItemTypes
from weko_deposit.api import WekoRecord

from .permissions import item_permission
from .utils import (
    get_list_username,
    get_list_email,
    get_user_info_by_username,
    validate_user,
    get_user_info_by_email)

blueprint = Blueprint(
    'weko_items_ui',
    __name__,
    url_prefix='/items',
    template_folder='templates',
    static_folder='static',
)

blueprint_api = Blueprint(
    'weko_items_ui',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix="/items",
)


@blueprint.route('/', methods=['GET'])
@blueprint.route('/<int:item_type_id>', methods=['GET'])
@login_required
@item_permission.require(http_exception=403)
def index(item_type_id=0):
    """Renders an item register view.

    :param item_type_id: Item type ID. (Default: 0)
    :return: The rendered template.
    """
    try:
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
        # if 'filemeta' in json.dumps(item_type.schema):
        if 'filename' in json.dumps(item_type.schema):
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
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


@blueprint.route('/iframe', methods=['GET'])
@blueprint.route('/iframe/<int:item_type_id>', methods=['GET'])
@login_required
@item_permission.require(http_exception=403)
def iframe_index(item_type_id=0):
    """Renders an item register view.

    :param item_type_id: Item type ID. (Default: 0)
    :return: The rendered template.
    """
    try:
        item_type = ItemTypes.get_by_id(item_type_id)
        if item_type is None:
            return render_template('weko_items_ui/iframe/error.html',
                                   error_type='no_itemtype')
        json_schema = '/items/jsonschema/{}'.format(item_type_id)
        schema_form = '/items/schemaform/{}'.format(item_type_id)
        sessionstore = RedisStore(redis.StrictRedis.from_url(
            'redis://{host}:{port}/1'.format(
                host=os.getenv('INVENIO_REDIS_HOST', 'localhost'),
                port=os.getenv('INVENIO_REDIS_PORT', '6379'))))
        record = {}
        files = []
        endpoints = {}
        activity_session = session['activity_info']
        activity_id = activity_session.get('activity_id', None)
        if activity_id and sessionstore.redis.exists(
                'activity_item_'+activity_id):
            item_str = sessionstore.get('activity_item_'+activity_id)
            item_json = json.loads(item_str)
            if 'metainfo' in item_json:
                record = item_json.get('metainfo')
            if 'files' in item_json:
                files = item_json.get('files')
            if 'endpoints' in item_json:
                endpoints = item_json.get('endpoints')
        need_file = False
        if 'filename' in json.dumps(item_type.schema):
            need_file = True
        return render_template(
            'weko_items_ui/iframe/item_edit.html',
            need_file=need_file,
            record=record,
            jsonschema=json_schema,
            schemaform=schema_form,
            id=item_type_id,
            item_save_uri=url_for('.iframe_save_model'),
            files=files,
            endpoints=endpoints
        )
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


@blueprint.route('/iframe/model/save', methods=['POST'])
@login_required
@item_permission.require(http_exception=403)
def iframe_save_model():
    """Renders an item register view.

    :param item_type_id: Item type ID. (Default: 0)
    :return: The rendered template.
    """
    try:
        data = request.get_json()
        activity_session = session['activity_info']
        activity_id = activity_session.get('activity_id', None)
        if activity_id:
            sessionstore = RedisStore(redis.StrictRedis.from_url(
                'redis://{host}:{port}/1'.format(
                    host=os.getenv('INVENIO_REDIS_HOST', 'localhost'),
                    port=os.getenv('INVENIO_REDIS_PORT', '6379'))))
            sessionstore.put('activity_item_'+activity_id, json.dumps(data),
                             ttl_secs=60*60*24*7)
    except Exception as ex:
        current_app.logger.exception(str(ex))
        return jsonify(code=1, msg='Model save error')
    return jsonify(code=0, msg='Model save success')


@blueprint.route('/iframe/success', methods=['GET'])
def iframe_success():
    """Renders an item register view.

    :return: The rendered template.
    """
    return render_template('weko_items_ui/iframe/error.html',
                           error_type='item_login_success')


@blueprint.route('/iframe/error', methods=['GET'])
def iframe_error():
    """Renders an item register view.

    :return: The rendered template.
    """
    return render_template('weko_items_ui/iframe/error.html',
                           error_type='item_login_error')


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
    try:
        result = None
        cur_lang = current_i18n.language

        if item_type_id > 0:
            if item_type_id == 20:
                result = ItemTypes.get_by_id(item_type_id)
                if result is None:
                    return '{}'
                json_schema = result.schema
                properties = json_schema.get('properties')
                for key, value in properties.items():
                    if 'validationMessage_i18n' in value:
                        value['validationMessage'] = value['validationMessage_i18n'][cur_lang]
            else:
                result = ItemTypes.get_record(item_type_id)
                if 'filemeta' in json.dumps(result):
                    group_list = Group.get_group_list()
                    group_enum = list(group_list.keys())
                    filemeta_group = result.get('properties').get('filemeta').get(
                        'items').get('properties').get('groups')
                    filemeta_group['enum'] = group_enum

                json_schema = result

        if result is None:
            return '{}'
        return jsonify(json_schema)
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


@blueprint.route('/schemaform/<int:item_type_id>', methods=['GET'])
@login_required
@item_permission.require(http_exception=403)
def get_schema_form(item_type_id=0):
    """Get schema form.

    :param item_type_id: Item type ID. (Default: 0)
    :return: The json object.
    """
    try:
        # cur_lang = 'default'
        # if current_app.config['I18N_SESSION_KEY'] in session:
        #     cur_lang = session[current_app.config['I18N_SESSION_KEY']]
        cur_lang = current_i18n.language
        result = None
        if item_type_id > 0:
            result = ItemTypes.get_by_id(item_type_id)
        if result is None:
            return '["*"]'
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
                if 'items' in elem:
                    for sub_elem in elem['items']:
                        if 'title_i18n' in sub_elem:
                            if cur_lang in sub_elem['title_i18n']:
                                if len(sub_elem['title_i18n'][cur_lang]) > 0:
                                    sub_elem['title'] = sub_elem['title_i18n'][
                                        cur_lang]
        return jsonify(schema_form)
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


@blueprint.route('/index/<int:pid_value>', methods=['GET', 'PUT', 'POST'])
@login_required
@item_permission.require(http_exception=403)
def items_index(pid_value=0):
    try:
        if pid_value == 0:
            return redirect(url_for('.index'))

        record = WekoRecord.get_record_by_pid(pid_value)
        action = 'private' if record.get('publish_status', '1') == '1' \
            else 'publish'

        if request.method == 'GET':
            return render_template(
                current_app.config['WEKO_ITEMS_UI_INDEX_TEMPLATE'],
                pid_value=pid_value,
                action=action)

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
            """update index of item info."""
            item_str = sessionstore.get('item_index_{}'.format(pid_value))
            sessionstore.delete('item_index_{}'.format(pid_value))
            current_app.logger.debug(item_str)
            item = json.loads(item_str)
            item['index'] = data
            current_app.logger.debug(item)
        elif request.method == 'POST':
            """update item data info."""
            sessionstore.put('item_index_{}'.format(pid_value), json.dumps(data),
                             ttl_secs=300)
        return jsonify(data)
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


@blueprint.route('/iframe/index/<int:pid_value>',
                 methods=['GET', 'PUT', 'POST'])
@login_required
@item_permission.require(http_exception=403)
def iframe_items_index(pid_value=0):
    try:
        if pid_value == 0:
            return redirect(url_for('.iframe_index'))

        record = WekoRecord.get_record_by_pid(pid_value)
        action = 'private' if record.get('publish_status', '1') == '1' \
            else 'publish'

        if request.method == 'GET':
            return render_template(
                'weko_items_ui/iframe/item_index.html',
                pid_value=pid_value,
                action=action)

        if request.headers['Content-Type'] != 'application/json':
            flash(_('invalide request'), 'error')
            return render_template(
                'weko_items_ui/iframe/item_index.html')

        data = request.get_json()
        sessionstore = RedisStore(redis.StrictRedis.from_url(
            'redis://{host}:{port}/1'.format(
                host=os.getenv('INVENIO_REDIS_HOST', 'localhost'),
                port=os.getenv('INVENIO_REDIS_PORT', '6379'))))
        if request.method == 'PUT':
            """update index of item info."""
            item_str = sessionstore.get('item_index_{}'.format(pid_value))
            sessionstore.delete('item_index_{}'.format(pid_value))
            current_app.logger.debug(item_str)
            item = json.loads(item_str)
            item['index'] = data
            current_app.logger.debug(item)
        elif request.method == 'POST':
            """update item data info."""
            sessionstore.put('item_index_{}'.format(pid_value), json.dumps(data),
                             ttl_secs=300)
        return jsonify(data)
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


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
    # if 'filemeta' in json.dumps(item_type.schema):
    if 'filename' in json.dumps(item_type.schema):
        need_file = True
    return render_template(
        template,
        need_file=need_file,
        record=record.item_metadata,
        jsonschema=json_schema,
        schemaform=schema_form,
        lists=lists,
        links=to_links_js(pid),
        id=item_type_id,
        files=to_files_js(record),
        pid=pid
    )


def to_links_js(pid):
    """Get API links."""
    self_url = current_app.config['DEPOSIT_RECORDS_API'].format(
        pid_value=pid.pid_value)
    links = {
        'self': self_url,
        'ret': url_for('weko_items_ui.index')
    }
    from weko_deposit.links import base_factory
    links.update(base_factory(pid))
    return links


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


@blueprint.route('/upload', methods=['GET'])
@login_required
def index_upload():
    """Renders an item data upload view.

    :return: The rendered template.
    """
    return render_template(
        current_app.config['WEKO_ITEMS_UI_UPLOAD_TEMPLATE']
    )


@blueprint_api.route('/get_search_data/<data_type>', methods=['GET'])
def get_search_data(data_type=''):
    """
    Host the api provide search data:
    Provide 2 search data: username and email

    param: 
        data_type: type of response data (username, email)
    return:
        list of search data
    """
    result = {
        'results': '',
        'error': '',
    }
    try:
        if data_type == 'username':
            result['results'] = get_list_username()
        elif data_type == 'email':
            result['results'] = get_list_email()
        else:
            result['error'] = 'Invaid method'
    except Exception as e:
        result['error'] = str(e)

    return jsonify(result)


@blueprint_api.route('/validate_user_info', methods=['POST'])
def validate_user_info():
    """
    Host the api which provide 2 service:
        Get autofill data: return user information based on request data
        Validate user information: check if user is exist

    request:
        header: Content type must be json
        data:
            username: The username
            email: The email
    return: response pack:
        results: user information if user is valid
        validation: 'true' if user is valid, other case return 'false'
        error: return error message, empty if no error occurs

    How to use:
        1. Get autofill data: fill username or email
        2. Validation: fill both username and email
    """
    result = {
        'results': '',
        'validation': '',
        'error': ''
    }

    if request.headers['Content-Type'] != 'application/json':
        """Check header of request"""
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    username = data.get('username', '')
    email = data.get('email', '')

    try:
        if username != "":
            if email == "":
                result['results'] = get_user_info_by_username(username)
                result['validation'] = True
            else:
                validate_data = validate_user(username, email)
                result['results'] = validate_data['results']
                result['validation'] = validate_data['validation']
            return jsonify(result)

        if email != "":
            result['results'] = get_user_info_by_email(email)
            result['validation'] = True

            return jsonify(result)
    except Exception as e:
        result['error'] = str(e)

    return jsonify(result)
