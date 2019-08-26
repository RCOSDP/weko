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

import operator
import os
import re
import sys
from datetime import date, timedelta

import redis
from flask import Blueprint, abort, current_app, flash, json, jsonify, \
    redirect, render_template, request, session, url_for
from flask_babelex import gettext as _
from flask_login import login_required
from flask_security import current_user
from invenio_accounts.models import Role, userrole
from invenio_i18n.ext import current_i18n
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_ui.signals import record_viewed
from invenio_stats.utils import QueryCommonReportsHelper, \
    QueryItemRegReportHelper, QueryRecordViewReportHelper, \
    QuerySearchReportHelper
from simplekv.memory.redisstore import RedisStore
from weko_admin.models import AdminSettings, RankingSettings
from weko_deposit.api import WekoDeposit, WekoRecord
from weko_groups.api import Group
from weko_index_tree.utils import get_user_roles
from weko_records.api import FeedbackMailList, ItemTypes, Mapping
from weko_records_ui.ipaddr import check_site_license_permission
from weko_records_ui.permissions import check_file_download_permission
from weko_workflow.api import GetCommunity, WorkActivity
from weko_workflow.config import ITEM_REGISTRATION_ACTION_ID
from weko_workflow.models import ActionStatusPolicy

from .config import IDENTIFIER_GRANT_CAN_WITHDRAW, IDENTIFIER_GRANT_DOI, \
    IDENTIFIER_GRANT_IS_WITHDRAWING, IDENTIFIER_GRANT_WITHDRAWN
from .permissions import item_permission
from .utils import get_actionid, get_current_user, get_list_email, \
    get_list_username, get_user_info_by_email, get_user_info_by_username, \
    get_user_information, get_user_permission, parse_ranking_results, \
    update_json_schema_by_activity_id, validate_form_input_data, \
    validate_user

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

        if 'filename' in json.dumps(item_type.schema):
            need_file = True

        return render_template(
            current_app.config['WEKO_ITEMS_UI_FORM_TEMPLATE'],
            render_widgets=True,
            need_file=need_file,
            record={},
            jsonschema=json_schema,
            schemaform=schema_form,
            lists=lists,
            id=item_type_id,
            files=[]
        )
    except BaseException:
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
                'activity_item_' + activity_id):
            item_str = sessionstore.get('activity_item_' + activity_id)
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
            records=record,
            jsonschema=json_schema,
            schemaform=schema_form,
            id=item_type_id,
            item_save_uri=url_for('.iframe_save_model'),
            files=files,
            endpoints=endpoints
        )
    except BaseException:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


@blueprint.route('/iframe/model/save', methods=['POST'])
@login_required
@item_permission.require(http_exception=403)
def iframe_save_model():
    """Renders an item register view.

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
            sessionstore.put(
                'activity_item_' + activity_id,
                json.dumps(data).encode('utf-8'),
                ttl_secs=60 * 60 * 24 * 7)
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


@blueprint.route('/jsonschema/<int:item_type_id>', methods=['GET'])
@blueprint.route('/jsonschema/<int:item_type_id>/<string:activity_id>',
                 methods=['GET'])
@login_required
@item_permission.require(http_exception=403)
def get_json_schema(item_type_id=0, activity_id=""):
    """Get json schema.

    :param item_type_id: Item type ID. (Default: 0)
    :param activity_id: Activity ID.  (Default: Null)
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
                for _, value in properties.items():
                    if 'validationMessage_i18n' in value:
                        value['validationMessage'] =\
                            value['validationMessage_i18n'][cur_lang]
            else:
                result = ItemTypes.get_record(item_type_id)
                if 'filemeta' in json.dumps(result):
                    group_list = Group.get_group_list()
                    group_enum = list(group_list.keys())
                    filemeta_group = result.get('properties').get(
                        'filemeta').get('items').get('properties').get('groups')
                    filemeta_group['enum'] = group_enum
            # hidden option
            hidden_subitem = 'subitem_thumbnail'
            properties = result.get('properties')
            hidden_items = [key for key, dic in properties.items()
                            for val in dic.values() if isinstance(val, dict)
                            and hidden_subitem in val]
            if hidden_items and hidden_subitem in json.dumps(result):
                result = update_schema_remove_hidden_item(result, hidden_items)

        if result is None:
            return '{}'

        if activity_id:
            updated_json_schema = update_json_schema_by_activity_id(result,
                                                                    activity_id)
            if updated_json_schema:
                result = updated_json_schema

        json_schema = result
        return jsonify(json_schema)
    except BaseException:
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
                if 'title_i18n' in elem and cur_lang in elem['title_i18n']\
                        and len(elem['title_i18n'][cur_lang]) > 0:
                    elem['title'] = elem['title_i18n'][cur_lang]
                if 'items' in elem:
                    for sub_elem in elem['items']:
                        if 'title_i18n' in sub_elem and cur_lang in \
                            sub_elem['title_i18n'] and len(
                                sub_elem['title_i18n'][cur_lang]) > 0:
                            sub_elem['title'] = sub_elem['title_i18n'][cur_lang]
                        if sub_elem.get('title') == 'Group/Price':
                            for sub_item in sub_elem['items']:
                                if sub_item['title'] == "価格" and \
                                    'validationMessage_i18n' in sub_item and \
                                    cur_lang in sub_item[
                                    'validationMessage_i18n'] and\
                                    len(sub_item['validationMessage_i18n']
                                        [cur_lang]) > 0:
                                    sub_item['validationMessage'] = sub_item[
                                        'validationMessage_i18n'][cur_lang]
                        if 'items' in sub_elem:
                            for sub_item in sub_elem['items']:
                                if 'title_i18n' in sub_item and cur_lang in \
                                        sub_item['title_i18n'] and len(
                                        sub_item['title_i18n'][cur_lang]) > 0:
                                    sub_item['title'] = sub_item['title_i18n'][
                                        cur_lang]

        return jsonify(schema_form)
    except BaseException:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


@blueprint.route('/index/<int:pid_value>', methods=['GET', 'PUT', 'POST'])
@login_required
@item_permission.require(http_exception=403)
def items_index(pid_value=0):
    """Items index."""
    try:
        if pid_value == 0:
            return redirect(url_for('.index'))

        record = WekoRecord.get_record_by_pid(pid_value)
        action = 'private' if record.get('publish_status', '1') == '1' \
            else 'publish'

        if request.method == 'GET':
            return render_template(
                current_app.config['WEKO_ITEMS_UI_INDEX_TEMPLATE'],
                render_widgets=True,
                pid_value=pid_value,
                action=action)

        if request.headers['Content-Type'] != 'application/json':
            flash(_('invalide request'), 'error')
            return render_template(
                current_app.config['WEKO_ITEMS_UI_INDEX_TEMPLATE'],
                render_widgets=True)

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
            sessionstore.put(
                'item_index_{}'.format(pid_value),
                json.dumps(data),
                ttl_secs=300)
        return jsonify(data)
    except BaseException:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


@blueprint.route('/iframe/index/<int:pid_value>',
                 methods=['GET', 'PUT', 'POST'])
@login_required
@item_permission.require(http_exception=403)
def iframe_items_index(pid_value=0):
    """Iframe items index."""
    try:
        if pid_value == 0:
            return redirect(url_for('.iframe_index'))

        record = WekoRecord.get_record_by_pid(pid_value)
        action = 'private' if record.get('publish_status', '1') == '1' \
            else 'publish'

        if request.method == 'GET':
            return render_template(
                'weko_items_ui/iframe/item_index.html',
                render_widgets=True,
                pid_value=pid_value,
                action=action,
                activity=session['itemlogin_activity'],
                item=session['itemlogin_item'],
                steps=session['itemlogin_steps'],
                action_id=session['itemlogin_action_id'],
                cur_step=session['itemlogin_cur_step'],
                record=session['itemlogin_record'],
                histories=session['itemlogin_histories'],
                res_check=session['itemlogin_res_check'],
                pid=session['itemlogin_pid'],
                community_id=session['itemlogin_community_id'])

        if request.headers['Content-Type'] != 'application/json':
            flash(_('Invalid Request'), 'error')
            return render_template(
                'weko_items_ui/iframe/item_index.html',
                render_widgets=True)

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
            sessionstore.put(
                'item_index_{}'.format(pid_value),
                json.dumps(data),
                ttl_secs=300)
        return jsonify(data)
    except BaseException:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


def default_view_method(pid, record, template=None):
    """Default view method.

    Sends ``record_viewed`` signal and renders template.
    """
    check_site_license_permission()
    send_info = {}
    send_info['site_license_flag'] = True \
        if hasattr(current_user, 'site_license_flag') else False
    send_info['site_license_name'] = current_user.site_license_name \
        if hasattr(current_user, 'site_license_name') else ''
    record_viewed.send(
        current_app._get_current_object(),
        pid=pid,
        record=record,
        info=send_info
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
    sessionstore = RedisStore(redis.StrictRedis.from_url(
        'redis://{host}:{port}/1'.format(
            host=os.getenv('INVENIO_REDIS_HOST', 'localhost'),
            port=os.getenv('INVENIO_REDIS_PORT', '6379'))))
    files = to_files_js(record)
    record = record.item_metadata
    endpoints = {}
    activity_session = session['activity_info']
    activity_id = activity_session.get('activity_id', None)
    if activity_id and sessionstore.redis.exists(
            'activity_item_' + activity_id):
        item_str = sessionstore.get('activity_item_' + activity_id)
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
        template,
        need_file=need_file,
        record=record,
        jsonschema=json_schema,
        schemaform=schema_form,
        lists=lists,
        links=to_links_js(pid),
        id=item_type_id,
        files=files,
        pid=pid,
        item_save_uri=url_for('weko_items_ui.iframe_save_model'),
        endpoints=endpoints
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
    files = record.files
    if files is not None:
        for f in files:
            res.append({
                'displaytype': f.get('displaytype', ''),
                'filename': f.get('filename', ''),
                'mimetype': f.mimetype,
                'key': f.key,
                'version_id': f.version_id,
                'checksum': f.file.checksum,
                'size': f.file.size,
                'completed': True,
                'progress': 100,
                'links': {
                    'self': (
                        current_app.config['DEPOSIT_FILES_API']
                        + u'/{bucket}/{key}?versionId={version_id}'.format(
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
    """get_search_data.

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
    """validate_user_info.

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


@blueprint_api.route('/get_user_info/<int:owner>/<int:shared_user_id>',
                     methods=['GET'])
def get_user_info(owner, shared_user_id):
    """get_user_info.

    Get username and password by querying user id

    param:
        user_id: The user ID
    return: The result json:
        username: The username,
        email: The email,
        error: null if no error occurs
    """
    result = {
        'username': '',
        'email': '',
        'owner': False,
        'error': ''
    }
    try:
        user_info = get_user_information(shared_user_id)
        result['username'] = user_info['username']
        result['email'] = user_info['email']
        if owner != 0:
            result['owner'] = get_user_permission(owner)
    except Exception as e:
        result['error'] = str(e)

    return jsonify(result)


@blueprint_api.route('/get_current_login_user_id', methods=['GET'])
def get_current_login_user_id():
    """get_current_login_user_id.

    Get user id of user is currently login
    """
    result = {
        'user_id': '',
        'error': ''
    }

    try:
        user_id = get_current_user()
        result['user_id'] = user_id
    except Exception as e:
        result['error'] = str(e)

    return jsonify(result)


@blueprint_api.route('/prepare_edit_item', methods=['POST'])
@login_required
def prepare_edit_item():
    """Prepare_edit_item.

    Host the api which provide 2 service:
        Create new activity for editing flow
        Check permission: check if user is owner/admin/shared user
    request:
        header: Content type must be json
        data:
            pid_value: pid_value
    return: The result json:
        code: status code,
        msg: meassage result,
        data: url redirect
    """
    if request.headers['Content-Type'] != 'application/json':
        """Check header of request"""
        return jsonify(code=-1, msg=_('Header Error'))
    post_activity = request.get_json()
    pid_value = post_activity.get('pid_value')
    if pid_value:
        try:
            record = WekoRecord.get_record_by_pid(pid_value)
            owner = str(record.get('owner'))
            shared_id = str(record.get('weko_shared_id'))
            user_id = str(get_current_user())
            is_admin = get_user_roles()
            activity = WorkActivity()
            pid_object = PersistentIdentifier.get('recid', pid_value)

            # check item is being editied
            item_id = pid_object.object_uuid
            workflow_action_stt = \
                activity.get_workflow_activity_status_by_item_id(
                    item_id=item_id)
            # show error when has stt is Begin or Doing
            if workflow_action_stt is not None and \
                (workflow_action_stt == ActionStatusPolicy.ACTION_BEGIN
                 or workflow_action_stt == ActionStatusPolicy.ACTION_DOING):
                return jsonify(code=-13,
                               msg=_('The workflow is being edited. '))

            if user_id != owner and not is_admin[0] and user_id != shared_id:
                return jsonify(code=-1,
                               msg=_('You are not allowed to edit this item.'))
            lists = ItemTypes.get_latest()
            if not lists:
                return jsonify(code=-1,
                               msg=_('You do not even have an itemtype.'))
            item_type_id = record.get('item_type_id')
            item_type = ItemTypes.get_by_id(item_type_id)
            if item_type is None:
                return jsonify(code=-1, msg=_('This itemtype not found.'))

            upt_current_activity = activity.upt_activity_detail(
                item_id=pid_object.object_uuid)

            if upt_current_activity is not None:
                post_activity['workflow_id'] = upt_current_activity.workflow_id
                post_activity['flow_id'] = upt_current_activity.flow_id
                post_activity['itemtype_id'] = item_type_id
                getargs = request.args
                community = getargs.get('community', None)

                # Create a new version of a record.
                record = WekoDeposit.get_record(item_id)
                if record is None:
                    return jsonify(code=-1, msg=_('Record does not exist.'))
                deposit = WekoDeposit(record, record.model)
                new_record = deposit.newversion(pid_object)
                if new_record is None:
                    return jsonify(code=-1, msg=_('An error has occurred.'))
                rtn = activity.init_activity(
                    post_activity, community, new_record.model.id)
                if rtn:
                    # GOTO: TEMPORARY EDIT MODE FOR IDENTIFIER
                    identifier_actionid = get_actionid('identifier_grant')
                    identifier = activity.get_action_identifier_grant(
                        upt_current_activity.activity_id, identifier_actionid)
                    if identifier:
                        if identifier.get('action_identifier_select') > \
                                IDENTIFIER_GRANT_DOI:
                            identifier['action_identifier_select'] = \
                                IDENTIFIER_GRANT_CAN_WITHDRAW
                        elif identifier.get('action_identifier_select') == \
                                IDENTIFIER_GRANT_IS_WITHDRAWING:
                            identifier['action_identifier_select'] = \
                                IDENTIFIER_GRANT_WITHDRAWN
                        activity.create_or_update_action_identifier(
                            rtn.activity_id,
                            identifier_actionid,
                            identifier)

                    mail_list = FeedbackMailList.get_mail_list_by_item_id(
                        item_id=pid_object.object_uuid)
                    if mail_list:
                        activity.create_or_update_action_feedbackmail(
                            activity_id=rtn.activity_id,
                            action_id=ITEM_REGISTRATION_ACTION_ID,
                            feedback_maillist=mail_list
                        )

                    if community:
                        comm = GetCommunity.get_community_by_id(community)
                        url_redirect = url_for('weko_workflow.display_activity',
                                               activity_id=rtn.activity_id,
                                               community=comm.id)
                    else:
                        url_redirect = url_for('weko_workflow.display_activity',
                                               activity_id=rtn.activity_id)
                    return jsonify(code=0, msg='success',
                                   data={'redirect': url_redirect})
        except Exception as e:
            current_app.logger.error('Unexpected error: ', str(e))
    return jsonify(code=-1, msg=_('An error has occurred.'))


@blueprint.route('/ranking', methods=['GET'])
def ranking():
    """Ranking page view."""
    # get ranking settings
    settings = RankingSettings.get()
    # get statistical period
    end_date = date.today()  # - timedelta(days=1)
    start_date = end_date - \
        timedelta(days=int(settings.statistical_period) - 1)

    rankings = {}
    # most_reviewed_items
    if settings.rankings['most_reviewed_items']:
        result = QueryRecordViewReportHelper.get(start_date=start_date.strftime('%Y-%m-%d'),
                                                 end_date=end_date.strftime(
                                                     '%Y-%m-%d'),
                                                 agg_size=settings.display_rank,
                                                 agg_sort={'value': 'desc'})
        rankings['most_reviewed_items'] = \
            parse_ranking_results(result, settings.display_rank,
                                  list_name='all', title_key='record_name',
                                  count_key='total_all', pid_key='pid_value')

    # most_downloaded_items
    if settings.rankings['most_downloaded_items']:
        result = QueryItemRegReportHelper.get(start_date=start_date.strftime('%Y-%m-%d'),
                                              end_date=end_date.strftime(
                                                  '%Y-%m-%d'),
                                              target_report='3',
                                              unit='Item',
                                              agg_size=settings.display_rank,
                                              agg_sort={'_count': 'desc'})
        rankings['most_downloaded_items'] = \
            parse_ranking_results(result, settings.display_rank,
                                  list_name='data', title_key='col2',
                                  count_key='col3', pid_key='col1')

    # created_most_items_user
    if settings.rankings['created_most_items_user']:
        result \
            = QueryItemRegReportHelper.get(start_date=start_date.strftime('%Y-%m-%d'),
                                           end_date=end_date.strftime(
                                               '%Y-%m-%d'),
                                           target_report='0',
                                           unit='User',
                                           agg_size=settings.display_rank,
                                           agg_sort={'_count': 'desc'})
        rankings['created_most_items_user'] = \
            parse_ranking_results(result, settings.display_rank,
                                  list_name='data',
                                  title_key='user_id', count_key='count')

    # most_searched_keywords
    if settings.rankings['most_searched_keywords']:
        result = QuerySearchReportHelper.get(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            agg_size=settings.display_rank,
            agg_sort={'value': 'desc'},
            agg_filter={'search_type': [0, 1]}
        )
        rankings['most_searched_keywords'] = \
            parse_ranking_results(result, settings.display_rank,
                                  list_name='all', title_key='search_key',
                                  count_key='count', search_key='search_key')

    # new_items
    if settings.rankings['new_items']:
        new_item_start_date = end_date - \
            timedelta(days=int(settings.new_item_period) - 1)
        if new_item_start_date < start_date:
            new_item_start_date = start_date
        new_items_list = []
        result = QueryCommonReportsHelper.get(
            start_date=new_item_start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            event='item_create',
            agg_size=settings.display_rank,
            agg_sort={'_term': 'desc'}
        )
        rankings['new_items'] = \
            parse_ranking_results(result, settings.display_rank,
                                  list_name='all', title_key='record_name',
                                  pid_key='pid_value', date_key='create_date')

    return render_template(current_app.config['WEKO_ITEMS_UI_RANKING_TEMPLATE'],
                           render_widgets=True,
                           is_show=settings.is_show,
                           start_date=start_date,
                           end_date=end_date,
                           rankings=rankings)


def check_ranking_show():
    """Check ranking show/hide."""
    result = 'hide'
    settings = RankingSettings.get()
    if settings and settings.is_show:
        result = ''
    return result


@blueprint_api.route('/check_restricted_content', methods=['POST'])
def check_restricted_content():
    """Check if record has restricted content for current user.

    :return: boolean
    """
    if request.headers['Content-Type'] != 'application/json':
        return abort(400)

    post_data = request.get_json()
    restricted_records = set()
    for record_id in post_data['record_ids']:
        try:
            record = WekoRecord.get_record_by_pid(record_id)
            for file in record.files:
                if not check_file_download_permission(record, file.info()):
                    restricted_records.add(record_id)
        except Exception:
            pass
    return jsonify({'restricted_records': list(restricted_records)})


def _get_max_export_items():
    """Get max amount of items to export."""
    max_table = current_app.config['WEKO_ITEMS_UI_MAX_EXPORT_NUM_PER_ROLE']
    non_user_max = max_table[current_app.config['WEKO_PERMISSION_ROLE_GENERAL']]
    current_user_id = current_user.get_id()

    if not current_user_id:  # Non-logged in users
        return non_user_max

    try:
        roles = db.session.query(Role).join(userrole).filter_by(
            user_id=current_user_id).all()
    except Exception as e:
        return current_app.config['WEKO_ITEMS_UI_DEFAULT_MAX_EXPORT_NUM']

    current_max = non_user_max
    for role in roles:
        if role in max_table and max_table[role] > current_max:
            current_max = max_table[role]
    return current_max


def _export_item(record_id, format, include_contents):
    """Exports files for record according to view permissions."""
    exported_item = {}
    record = WekoRecord.get_record_by_pid(record_id)

    if record:
        exported_item['record_id'] = record.id
        exported_item['files'] = []

        # First get all of the files, checking for permissions while doing so
        if include_contents:
            for file in record.files:  # TODO: Temporary processing
                if check_file_download_permission(record, file.info()):
                    exported_item['files'].append(file.info())
                    # TODO: Then convert the item into the desired format

    return exported_item


def export_items(post_data):
    """Gather all the item data and export and return as a JSON or BIBTEX.

    :return: JSON, BIBTEX
    """
    include_contents = True if \
        post_data['export_file_contents_radio'] == 'True' else False
    format = post_data['export_format_radio']
    record_ids = json.loads(post_data['record_ids'])
    if len(record_ids) > _get_max_export_items():
        return abort(400)

    result = {'items': []}
    try:
        # Double check for limits
        for id in record_ids:
            result['items'].append(_export_item(id, format, include_contents))

    except Exception as e:
        current_app.logger.error(e)
        flash(_('Error occurred during item export.'), 'error')
        return redirect(url_for('weko_items_ui.export'))
    return jsonify(result)  # TODO: Change this to file download code


@blueprint.route('/export', methods=['GET', 'POST'])
def export():
    """Item export view."""
    export_settings = AdminSettings.get('item_export_settings') or \
        AdminSettings.Dict2Obj(
            current_app.config['WEKO_ADMIN_DEFAULT_ITEM_EXPORT_SETTINGS'])
    if not export_settings.allow_item_exporting:
        return abort(403)

    if request.method == 'POST':
        return export_items(request.form.to_dict())

    from weko_search_ui.api import SearchSetting
    search_type = request.args.get('search_type', '0')  # TODO: Refactor
    community_id = ""
    ctx = {'community': None}
    cur_index_id = search_type if search_type not in ('0', '1', ) else None
    if 'community' in request.args:
        from weko_workflow.api import GetCommunity
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        community_id = comm.id

    sort_options, display_number = SearchSetting.get_results_setting()
    disply_setting = dict(size=display_number)

    return render_template(
        current_app.config['WEKO_ITEMS_UI_EXPORT_TEMPLATE'],
        render_widgets=True,
        index_id=cur_index_id,
        community_id=community_id,
        sort_option=sort_options,
        disply_setting=disply_setting,
        enable_contents_exporting=export_settings.enable_contents_exporting,
        max_export_num=_get_max_export_items(),
        **ctx
    )


@blueprint_api.route('/validate', methods=['POST'])
@login_required
def validate():
    """Validate input data.

    :return:
    """
    result = {
        "is_valid": True,
        "error": ""
    }
    request_data = request.get_json()
    validate_form_input_data(result, request_data.get('item_id'),
                             request_data.get('data'))
    return jsonify(result)


@blueprint_api.route('/check_validation_error_msg/<string:activity_id>',
                     methods=['GET'])
@login_required
@item_permission.require(http_exception=403)
def check_validation_error_msg(activity_id):
    """Check whether session('update_json_schema') is exist.

    :param activity_id: The identify of Activity.
    :return: Show error message
    """
    if session.get('update_json_schema') and session[
            'update_json_schema'].get(activity_id):
        error_list = session[
            'update_json_schema'].get(activity_id)
        return jsonify(code=1,
                       msg=_('PID does not meet the conditions.'),
                       error_list=error_list)
    else:
        return jsonify(code=0)


def update_schema_remove_hidden_item(schema, items_name):
    """Update schema: remove hidden items.

    :param schema: json schema
    :param items_name: list items which has hidden flg
    :return: The json object.
    """
    if not schema or not items_name:
        return '{}'
    render = schema.model.render
    for item in items_name:
        hidden_flg = render['meta_list'][item]['option']['hidden']
        if hidden_flg:
            schema['properties'].pop(item)

    return schema
