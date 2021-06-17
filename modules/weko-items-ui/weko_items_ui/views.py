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

import json
import os
import sys
from datetime import date, timedelta

import redis
from flask import Blueprint, abort, current_app, flash, json, jsonify, \
    redirect, render_template, request, session, url_for
from flask_babelex import gettext as _
from flask_login import login_required
from flask_security import current_user
from invenio_i18n.ext import current_i18n
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidstore.resolver import Resolver
from invenio_records_ui.signals import record_viewed
from simplekv.memory.redisstore import RedisStore
from weko_accounts.utils import login_required_customize
from weko_admin.models import AdminSettings, RankingSettings
from weko_deposit.api import WekoRecord
from weko_groups.api import Group
from weko_index_tree.utils import check_index_permissions, get_index_id, \
    get_user_roles
from weko_records.api import ItemTypes
from weko_records_ui.ipaddr import check_site_license_permission
from weko_records_ui.permissions import check_file_download_permission
from weko_workflow.api import GetCommunity, WorkActivity, WorkFlow
from weko_workflow.utils import check_an_item_is_locked, \
    get_record_by_root_ver, get_thumbnails, prepare_edit_workflow, \
    set_files_display_type
from werkzeug.utils import import_string

from .permissions import item_permission
from .utils import _get_max_export_items, check_item_is_being_edit, \
    export_items, get_current_user, get_data_authors_prefix_settings, \
    get_list_email, get_list_username, get_ranking, get_user_info_by_email, \
    get_user_info_by_username, get_user_information, get_user_permission, \
    get_workflow_by_item_type_id, hide_form_items, is_schema_include_key, \
    remove_excluded_items_in_json_schema, sanitize_input_data, save_title, \
    set_multi_language_name, to_files_js, translate_schema_form, \
    translate_validation_message, update_index_tree_for_record, \
    update_json_schema_by_activity_id, update_schema_form_by_activity_id, \
    update_sub_items_by_user_role, validate_form_input_data, validate_user, \
    validate_user_mail_and_index

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
        from weko_theme.utils import get_design_layout

        # Get the design for widget rendering
        page, render_widgets = get_design_layout(
            current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])

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
        need_file, need_billing_file = is_schema_include_key(item_type.schema)

        return render_template(
            current_app.config['WEKO_ITEMS_UI_FORM_TEMPLATE'],
            page=page,
            render_widgets=render_widgets,
            need_file=need_file,
            need_billing_file=need_billing_file,
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
        record = {}
        files = []
        endpoints = {}
        activity_session = session['activity_info']
        activity_id = activity_session.get('activity_id', None)
        if activity_id:
            activity = WorkActivity()
            metadata = activity.get_activity_metadata(activity_id)
            if metadata:
                item_json = json.loads(metadata)
                if 'metainfo' in item_json:
                    record = item_json.get('metainfo')
                if 'files' in item_json:
                    files = item_json.get('files')
                if 'endpoints' in item_json:
                    endpoints = item_json.get('endpoints')
        need_file, need_billing_file = is_schema_include_key(item_type.schema)

        return render_template(
            'weko_items_ui/iframe/item_edit.html',
            need_file=need_file,
            need_billing_file=need_billing_file,
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
@login_required_customize
def iframe_save_model():
    """Renders an item register view.

    :return: The rendered template.
    """
    try:
        data = request.get_json()
        activity_session = session['activity_info']
        activity_id = activity_session.get('activity_id', None)
        if activity_id:
            sanitize_input_data(data)
            save_title(activity_id, data)
            activity = WorkActivity()
            activity.upt_activity_metadata(activity_id, json.dumps(data))
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
@login_required_customize
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
            result = ItemTypes.get_record(item_type_id)
            properties = result.get('properties')
            if 'filemeta' in json.dumps(result):
                group_list = Group.get_group_list()
                group_enum = list(group_list.keys())
                filemeta_group = properties.get(
                    'filemeta').get(
                    'items').get('properties').get('groups')
                filemeta_group['enum'] = group_enum
            for _key, value in properties.items():
                translate_validation_message(value, cur_lang)
        if result is None:
            return '{}'
        if activity_id:
            updated_json_schema = update_json_schema_by_activity_id(
                result,
                activity_id)
            if updated_json_schema:
                result = updated_json_schema
        json_schema = result
        # Remove excluded item in json_schema
        remove_excluded_items_in_json_schema(item_type_id, json_schema)
        return jsonify(json_schema)
    except BaseException:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


@blueprint.route('/schemaform/<int:item_type_id>', methods=['GET'])
@blueprint.route('/schemaform/<int:item_type_id>/<string:activity_id>',
                 methods=['GET'])
@login_required_customize
def get_schema_form(item_type_id=0, activity_id=''):
    """Get schema form.

    :param item_type_id: Item type ID. (Default: 0)
    :param activity_id: Activity ID.  (Default: Null)
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

        from .utils import recursive_form
        recursive_form(schema_form)
        # Check role for input(5 item type)
        update_sub_items_by_user_role(item_type_id, schema_form)

        # Hide form items
        schema_form = hide_form_items(result, schema_form)

        for elem in schema_form:
            set_multi_language_name(elem, cur_lang)
            if 'items' in elem:
                items = elem['items']
                for item in items:
                    set_multi_language_name(item, cur_lang)

        if 'default' != cur_lang:
            for elem in schema_form:
                translate_schema_form(elem, cur_lang)

        if activity_id:
            updated_schema_form = update_schema_form_by_activity_id(
                schema_form,
                activity_id)
            if updated_schema_form:
                schema_form = updated_schema_form

        return jsonify(schema_form)
    except BaseException:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


@blueprint.route('/index/<string:pid_value>', methods=['GET', 'PUT', 'POST'])
@login_required
@item_permission.require(http_exception=403)
def items_index(pid_value='0'):
    """Items index."""
    try:
        if pid_value == '0' or pid_value == 0:
            return redirect(url_for('.index'))

        record = WekoRecord.get_record_by_pid(pid_value)
        action = 'private' if record.get('publish_status', '1') == '1' \
            else 'publish'

        from weko_theme.utils import get_design_layout

        # Get the design for widget rendering
        page, render_widgets = get_design_layout(
            current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])
        if request.method == 'GET':
            return render_template(
                current_app.config['WEKO_ITEMS_UI_INDEX_TEMPLATE'],
                page=page,
                render_widgets=render_widgets,
                pid_value=pid_value,
                action=action)

        if request.headers['Content-Type'] != 'application/json':
            flash(_('Invalid request'), 'error')
            return render_template(
                current_app.config['WEKO_ITEMS_UI_INDEX_TEMPLATE'],
                page=page,
                render_widgets=render_widgets)

        data = request.get_json()
        sessionstore = RedisStore(redis.StrictRedis.from_url(
            'redis://{host}:{port}/1'.format(
                host=os.getenv('INVENIO_REDIS_HOST', 'localhost'),
                port=os.getenv('INVENIO_REDIS_PORT', '6379'))))
        if request.method == 'PUT':
            """update index of item info."""
            item_str = sessionstore.get('item_index_{}'.format(pid_value))
            sessionstore.delete('item_index_{}'.format(pid_value))
            item = json.loads(item_str)
            item['index'] = data
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


@blueprint.route('/iframe/index/<string:pid_value>',
                 methods=['GET', 'PUT', 'POST'])
@login_required_customize
def iframe_items_index(pid_value='0'):
    """Iframe items index."""
    try:
        files_thumbnail = None
        if pid_value == '0' or pid_value == 0:
            return redirect(url_for('.iframe_index'))

        record = WekoRecord.get_record_by_pid(pid_value)
        action = 'private' if record.get('publish_status', '1') == '1' \
            else 'publish'

        community_id = session.get('itemlogin_community_id')
        ctx = {'community': None}
        if community_id:
            comm = GetCommunity.get_community_by_id(community_id)
            ctx = {'community': comm}

        if request.method == 'GET':
            cur_activity = session['itemlogin_activity']

            workflow = WorkFlow()
            workflow_detail = workflow.get_workflow_by_id(
                cur_activity.workflow_id)
            if workflow_detail and workflow_detail.index_tree_id:
                index_id = get_index_id(cur_activity.activity_id)
                update_index_tree_for_record(pid_value, index_id)
                return redirect(url_for('weko_workflow.iframe_success'))

            # Get the design for widget rendering
            from weko_theme.utils import get_design_layout

            page, render_widgets = get_design_layout(
                community_id
                or current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])
            root_record = None
            files = []
            if pid_value and '.' in pid_value:
                root_record, files = get_record_by_root_ver(pid_value)
                if root_record and root_record.get('title'):
                    session['itemlogin_item']['title'] = root_record['title'][0]
                    files_thumbnail = get_thumbnails(files, None)
            else:
                root_record = session['itemlogin_record']
            if root_record and files and len(root_record) > 0 and \
                    len(files) > 0 and isinstance(root_record, (list, dict)):
                files = set_files_display_type(root_record, files)
            return render_template(
                'weko_items_ui/iframe/item_index.html',
                page=page,
                render_widgets=render_widgets,
                pid_value=pid_value,
                action=action,
                activity=session['itemlogin_activity'],
                item=session['itemlogin_item'],
                steps=session['itemlogin_steps'],
                action_id=session['itemlogin_action_id'],
                cur_step=session['itemlogin_cur_step'],
                record=root_record,
                histories=session['itemlogin_histories'],
                res_check=session['itemlogin_res_check'],
                pid=session['itemlogin_pid'],
                community_id=community_id,
                files=files,
                files_thumbnail=files_thumbnail,
                **ctx
            )

        if request.headers['Content-Type'] != 'application/json':
            flash(_('Invalid Request'), 'error')
            from weko_theme.utils import get_design_layout
            page, render_widgets = get_design_layout(
                current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])
            return render_template(
                'weko_items_ui/iframe/item_index.html',
                page=page,
                render_widgets=render_widgets,
                community_id=community_id,
                **ctx
            )

        data = request.get_json()
        sessionstore = RedisStore(redis.StrictRedis.from_url(
            'redis://{host}:{port}/1'.format(
                host=os.getenv('INVENIO_REDIS_HOST', 'localhost'),
                port=os.getenv('INVENIO_REDIS_PORT', '6379'))))
        if request.method == 'PUT':
            """update index of item info."""
            item_str = sessionstore.get('item_index_{}'.format(pid_value))
            sessionstore.delete('item_index_{}'.format(pid_value))
            item = json.loads(item_str)
            item['index'] = data
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
    send_info = dict()
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
    files = to_files_js(record)
    record = record.item_metadata
    endpoints = {}
    activity_session = session['activity_info']
    activity_id = activity_session.get('activity_id', None)
    if activity_id:
        activity = WorkActivity()
        metadata = activity.get_activity_metadata(activity_id)
        if metadata:
            item_json = json.loads(metadata)
            if 'metainfo' in item_json:
                record = item_json.get('metainfo')
            if 'files' in item_json:
                files = item_json.get('files')
            if 'endpoints' in item_json:
                endpoints = item_json.get('endpoints')
    need_file, need_billing_file = is_schema_include_key(item_type.schema)

    return render_template(
        template,
        need_file=need_file,
        need_billing_file=need_billing_file,
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


@blueprint_api.route('/validate_email_and_index', methods=['POST'])
def validate_user_email_and_index():
    """Validate user mail and index.

    :return:
    """
    result = {}
    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)
    data = request.get_json()
    result = validate_user_mail_and_index(data)
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
        Check permission: check if user is owner/admin/shared user
        Create new activity for editing flow
    request:
        header: Content type must be json
        data:
            pid_value: pid_value
    return: The result json:
        code: status code,
        msg: meassage result,
        data: url redirect
    """
    err_code = current_app.config.get('WEKO_ITEMS_UI_API_RETURN_CODE_ERROR',
                                      -1)
    if request.headers['Content-Type'] != 'application/json':
        """Check header of request"""
        return jsonify(
            code=err_code,
            msg=_('Header Error')
        )

    post_activity = request.get_json()
    getargs = request.args
    pid_value = post_activity.get('pid_value')
    community = getargs.get('community', None)

    if pid_value:
        record_class = import_string('weko_deposit.api:WekoDeposit')
        resolver = Resolver(pid_type='recid',
                            object_type='rec',
                            getter=record_class.get_record)
        recid, deposit = resolver.resolve(pid_value)
        authenticators = [str(deposit.get('owner')),
                          str(deposit.get('weko_shared_id'))]
        user_id = str(get_current_user())
        activity = WorkActivity()
        latest_pid = PIDVersioning(child=recid).last_child

        # ! Check User's Permissions
        if user_id not in authenticators and not get_user_roles()[0]:
            return jsonify(
                code=err_code,
                msg=_("You are not allowed to edit this item.")
            )

        # ! Check dependency ItemType
        if not ItemTypes.get_latest():
            return jsonify(
                code=err_code,
                msg=_("You do not even have an ItemType.")
            )

        item_type_id = deposit.get('item_type_id')
        item_type = ItemTypes.get_by_id(item_type_id)
        if not item_type:
            return jsonify(
                code=err_code,
                msg=_("Dependency ItemType not found.")
            )

        if not deposit:
            return jsonify(
                code=err_code,
                msg=_('Record does not exist.')
            )

        # Check Record is in import progress
        if check_an_item_is_locked(pid_value):
            return jsonify(
                code=err_code,
                msg=_('Item cannot be edited because '
                      'the import is in progress.')
            )

        # ! Check Record is being edit
        item_uuid = latest_pid.object_uuid
        post_workflow = activity.get_workflow_activity_by_item_id(item_uuid)

        if post_workflow:
            if check_item_is_being_edit(recid, post_workflow, activity):
                return jsonify(
                    code=err_code,
                    msg=_('This Item is being edited.')
                )

            post_activity['workflow_id'] = post_workflow.workflow_id
            post_activity['flow_id'] = post_workflow.flow_id
        else:
            post_workflow = activity.get_workflow_activity_by_item_id(
                recid.object_uuid
            )
            workflow = get_workflow_by_item_type_id(item_type.name_id,
                                                    item_type_id)
            if not workflow:
                return jsonify(
                    code=err_code,
                    msg=_('Workflow setting does not exist.')
                )
            post_activity['workflow_id'] = workflow.id
            post_activity['flow_id'] = workflow.flow_id
        post_activity['itemtype_id'] = item_type_id
        post_activity['community'] = community
        post_activity['post_workflow'] = post_workflow

        rtn = prepare_edit_workflow(post_activity, recid, deposit)

        if community:
            comm = GetCommunity.get_community_by_id(community)
            url_redirect = url_for('weko_workflow.display_activity',
                                   activity_id=rtn.activity_id,
                                   community=comm.id)
        else:
            url_redirect = url_for('weko_workflow.display_activity',
                                   activity_id=rtn.activity_id)

        return jsonify(
            code=0,
            msg='success',
            data=dict(redirect=url_redirect)
        )

    return jsonify(
        code=err_code,
        msg=_('An error has occurred.')
    )


@blueprint.route('/ranking', methods=['GET'])
def ranking():
    """Ranking page view."""
    # get ranking settings
    settings = RankingSettings.get()
    # get statistical period
    end_date = date.today()  # - timedelta(days=1)
    start_date = end_date - timedelta(days=int(settings.statistical_period))

    from weko_theme.utils import get_design_layout

    # Get the design for widget rendering -- Always default
    page, render_widgets = get_design_layout(
        current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])

    rankings = get_ranking(settings)

    x = rankings.get('most_searched_keywords')
    if x:
        import urllib.parse
        for y in x:
            if y["title"].split():
                y["url"] = '/search?search_type=0&q={}'.format(
                    urllib.parse.quote(y["title"]))
            else:
                y["url"] = '/search?search_type=0&q={z}'.format(z=y["title"])
    return render_template(
        current_app.config['WEKO_ITEMS_UI_RANKING_TEMPLATE'],
        page=page,
        render_widgets=render_widgets,
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


@blueprint.route('/validate_bibtext_export', methods=['POST'])
def validate_bibtex_export():
    """Validate export Bibtex.

    @return:
    """
    from .utils import validate_bibtex
    post_data = request.get_json()
    record_ids = post_data['record_ids']
    invalid_record_ids = validate_bibtex(record_ids)
    return jsonify(invalid_record_ids=invalid_record_ids)


@blueprint.route('/export', methods=['GET', 'POST'])
def export():
    """Item export view."""
    export_settings = AdminSettings.get('item_export_settings') or \
        AdminSettings.Dict2Obj(
        current_app.config[
            'WEKO_ADMIN_DEFAULT_ITEM_EXPORT_SETTINGS'])
    if not export_settings.allow_item_exporting:
        return abort(403)

    if request.method == 'POST':
        return export_items(request.form.to_dict())

    from weko_search_ui.api import SearchSetting
    search_type = request.args.get('search_type', '0')  # TODO: Refactor
    community_id = ""
    ctx = {'community': None}
    cur_index_id = search_type if search_type not in ('0', '1',) else None
    if 'community' in request.args:
        from weko_workflow.api import GetCommunity
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        community_id = comm.id

    from weko_theme.utils import get_design_layout

    # Get the design for widget rendering
    page, render_widgets = get_design_layout(
        community_id or current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])

    sort_options, display_number = SearchSetting.get_results_setting()
    disply_setting = dict(size=display_number)

    return render_template(
        current_app.config['WEKO_ITEMS_UI_EXPORT_TEMPLATE'],
        page=page,
        render_widgets=render_widgets,
        index_id=cur_index_id,
        community_id=community_id,
        sort_option=sort_options,
        disply_setting=disply_setting,
        enable_contents_exporting=export_settings.enable_contents_exporting,
        max_export_num=_get_max_export_items(),
        **ctx
    )


@blueprint_api.route('/validate', methods=['POST'])
@login_required_customize
def validate():
    """Validate input data.

    :return:
    """
    result = {
        "is_valid": True,
        "error": ""
    }
    request_data = request.get_json()
    validate_form_input_data(
        result,
        request_data.get('item_id'),
        request_data.get('data')
    )
    return jsonify(result)


@blueprint_api.route('/check_validation_error_msg/<string:activity_id>',
                     methods=['GET'])
@login_required_customize
def check_validation_error_msg(activity_id):
    """Check whether sessionstore('updated_json_schema_') is exist.

    :param activity_id: The identify of Activity.
    :return: Show error message
    """
    sessionstore = RedisStore(redis.StrictRedis.from_url(
        'redis://{host}:{port}/1'.format(
            host=os.getenv('INVENIO_REDIS_HOST', 'localhost'),
            port=os.getenv('INVENIO_REDIS_PORT', '6379'))))
    if sessionstore.redis.exists(
            'updated_json_schema_{}'.format(activity_id)) \
            and sessionstore.get('updated_json_schema_{}'.format(activity_id)):
        session_data = sessionstore.get(
            'updated_json_schema_{}'.format(activity_id))
        error_list = json.loads(session_data.decode('utf-8'))
        msg = []
        if error_list.get('error_type'):
            if error_list.get('error_type') == 'no_resource_type':
                msg.append(_(error_list.get('msg', '')))

        else:
            msg.append(_('PID does not meet the conditions.'))
        if error_list.get('pmid'):
            msg.append(_(
                'Since PMID is not subject to DOI registration, please '
                'select another type.'
            ))
        if error_list.get('doi'):
            msg.append(_(
                'Prefix/Suffix of Identifier is not consistency with'
                ' content of Identifier Registration.'))
        if error_list.get('url'):
            msg.append(_(
                'Please input location information (URL) for Identifier.'))
        return jsonify(code=1,
                       msg=msg,
                       error_list=error_list)
    else:
        return jsonify(code=0)


@blueprint.route('/', methods=['GET'])
@blueprint.route('/corresponding-activity', methods=['GET'])
@login_required
@item_permission.require(http_exception=403)
def corresponding_activity_list():
    """Get corresponding usage & output activity list.

    :return: activity list
    """
    result = {}
    work_activity = WorkActivity()
    if "get_corresponding_usage_activities" in dir(work_activity):
        usage_application_list, output_report_list = work_activity. \
            get_corresponding_usage_activities(current_user.get_id())
        result = {'usage_application': usage_application_list,
                  'output_report': output_report_list}
    return jsonify(result)


@blueprint_api.route('/author_prefix_settings', methods=['GET'])
def get_authors_prefix_settings():
    """Get all author prefix settings."""
    author_prefix_settings = get_data_authors_prefix_settings()
    if author_prefix_settings is not None:
        results = []
        for prefix in author_prefix_settings:
            scheme = prefix.scheme
            url = prefix.url
            result = dict(
                scheme=scheme,
                url=url
            )
            results.append(result)
        return jsonify(results)
    else:
        return abort(403)


@blueprint.route('/sessionvalidate', methods=['POST'])
def session_validate():
    """Validate the session."""
    authorized = True if current_user and current_user.get_id() else False
    result = {
        "unauthorized": authorized,
        "msg": _('Your session has timed out. Please login again.')
    }
    return jsonify(result)


@blueprint_api.route('/check_record_doi/<string:pid_value>', methods=['GET'])
@login_required
def check_record_doi(pid_value='0'):
    """Check public status.

    :param pid_value: pid_value.
    :return:
    """
    record = WekoRecord.get_record_by_pid(pid_value)
    if record.pid_doi:
        return jsonify({'code': 0})
    return jsonify({'code': -1})


@blueprint_api.route('/check_record_doi_indexes/<string:pid_value>',
                     methods=['GET'])
@login_required
def check_record_doi_indexes(pid_value='0'):
    """Check restrict DOI and Indexes.

    :param pid_value: pid_value.
    :return:
    """
    doi = int(request.args.get('doi', '0'))
    record = WekoRecord.get_record_by_pid(pid_value)
    if (record.pid_doi or doi > 0) and \
            not check_index_permissions(record=record, is_check_doi=True):
        return jsonify({
            'code': -1
        })

    return jsonify({'code': 0})
