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

import sys
import json
import traceback
import requests
from copy import deepcopy
from datetime import date, datetime, timedelta

from flask import (
    Blueprint, abort, current_app, flash, jsonify, redirect,
    render_template, request, session, url_for
)
from flask_babelex import gettext as _
from flask_login import login_required
from flask_security import current_user
from flask_wtf import FlaskForm
from sqlalchemy.exc import SQLAlchemyError, StatementError
from werkzeug.utils import import_string
from webassets.exceptions import BuildError
from werkzeug.exceptions import BadRequest

from invenio_db import db
from invenio_i18n.ext import current_i18n
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidstore.resolver import Resolver
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records_ui.signals import record_viewed

from weko_accounts.utils import login_required_customize
from weko_admin.models import AdminSettings, RankingSettings
from weko_deposit.api import WekoRecord
from weko_groups.api import Group
from weko_index_tree.utils import (
    check_index_permissions, get_index_id, get_user_roles
)
from weko_records.api import ItemTypes
from weko_records_ui.ipaddr import check_site_license_permission
from weko_records_ui.permissions import check_file_download_permission
from weko_redis.redis import RedisConnection
from weko_schema_ui.models import PublishStatus
from weko_workflow.api import GetCommunity, WorkActivity, WorkFlow as WorkFlows
from weko_workflow.utils import (
    check_an_item_is_locked, get_record_by_root_ver, get_thumbnails,
    prepare_edit_workflow, set_files_display_type, prepare_delete_workflow
)

from .permissions import item_permission
from .utils import (
    _get_max_export_items, check_item_is_being_edit,
    export_items, export_rocrate, get_current_user, get_data_authors_prefix_settings,
    get_data_authors_affiliation_settings, get_list_email, get_list_username,
    get_ranking, get_user_info_by_email, get_user_info_by_username,
    get_user_information, get_user_permission, get_workflow_by_item_type_id,
    hide_form_items, is_schema_include_key, remove_excluded_items_in_json_schema,
    sanitize_input_data, save_title, set_multi_language_name, to_files_js,
    translate_schema_form, translate_validation_message, update_index_tree_for_record,
    update_json_schema_by_activity_id, update_schema_form_by_activity_id,
    update_sub_items_by_user_role, validate_form_input_data, validate_user,
    validate_user_mail_and_index, get_weko_link, get_access_token,
    is_duplicate_record, lock_item_will_be_edit
)
from .config import WEKO_ITEMS_UI_FORM_TEMPLATE,WEKO_ITEMS_UI_ERROR_TEMPLATE
from weko_theme.config import WEKO_THEME_DEFAULT_COMMUNITY


blueprint = Blueprint(
    'weko_items_ui',
    __name__,
    url_prefix='/items',
    template_folder='templates',
    static_folder='static',
)

blueprint_api = Blueprint(
        'weko_items_ui_api',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix="/items",
)

#  OAポリシー取得エンドポイント
@blueprint.route("/api/oa_policies", methods=["GET"])
@login_required
def get_oa_policy():
    """
    OAポリシー情報を取得するAPIエンドポイント。

    リクエストパラメータ:
        - issn (str): ISSN番号
        - eissn (str): eISSN番号
        - title (str): 雑誌名

    レスポンス:
        - 成功時: {"policy_url": "取得したポリシーURL"}
        - 失敗時: {"error": "エラーメッセージ"}, HTTPステータスコード
    """
    try:
        issn = request.args.get("issn", "").strip()
        eissn = request.args.get("eissn", "").strip()
        title = request.args.get("title", "").strip()

        if not issn and not eissn and not title:
            return jsonify({"error": "Please enter ISSN, eISSN, or journal title"}), 400

        api_url = current_app.config.get("WEKO_ITEMS_UI_OA_POLICY_API_URL")
        api_code = current_app.config.get("WEKO_ITEMS_UI_OA_POLICY_API_CODE")

        # アクセストークンを取得
        token_info = get_access_token(api_code)

        if not token_info or "access_token" not in token_info:
            return jsonify({"error": "Authentication error occurred"}), 401

        token = token_info["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        params = {"issn": issn, "eissn": eissn, "title": title}

        # APIリクエスト送信
        response = requests.get(api_url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            return jsonify({"policy_url": data.get("url", "No Policy Information found")})
        elif response.status_code == 404:
            return jsonify({"error": "No matching policy"}), 404
        elif response.status_code == 429:
            return jsonify({"error": "Request limit exceeded"}), 429
        elif response.status_code == 500:
            return jsonify({"error": "Internal server error"}), 500
        else:
            return jsonify({"error": "An unknown error occurred"}), 500

    except requests.exceptions.RequestException:
        return jsonify({"error": "API Request Failed"}), 500
    except Exception as e:
        return jsonify({"error": f"An unknown error occurred: {str(e)}"}), 500

@blueprint.route('/', methods=['GET'])
@blueprint.route('/<int:item_type_id>', methods=['GET'])
@login_required
@item_permission.require(http_exception=403)
def index(item_type_id=0):
    """Renders an item register view.
    :param item_type_id: Item type ID. (Default: 0)
    :return: The rendered template.
    ---
      get:
        description: Renders an item register view.
        security:
        - login_required: []
        parameters:
          - name: item_type_id
            in: query
            description: item_type_id
            schema:
              type: string
        responses:
          200:
            description: render result of weko_items_ui/edit.html
            content:
                text/html
          302:
            description:
          403:
            description: no item_permission

    """
    try:
        from weko_theme.utils import get_design_layout

        # Get the design for widget rendering
        page, render_widgets = get_design_layout(
            current_app.config.get('WEKO_THEME_DEFAULT_COMMUNITY',WEKO_THEME_DEFAULT_COMMUNITY))

        lists = ItemTypes.get_latest()
        if lists is None or len(lists) == 0:
            return render_template(
                current_app.config.get('WEKO_ITEMS_UI_ERROR_TEMPLATE',WEKO_ITEMS_UI_ERROR_TEMPLATE)
            ),400
        item_type = ItemTypes.get_by_id(item_type_id)
        if item_type is None:
            return redirect(
                url_for('.index', item_type_id=lists[0].item_type[0].id))
        json_schema = '/items/jsonschema/{}'.format(item_type_id)
        schema_form = '/items/schemaform/{}'.format(item_type_id)
        need_file, need_billing_file = is_schema_include_key(item_type.schema)

        return render_template(
            current_app.config.get('WEKO_ITEMS_UI_FORM_TEMPLATE',WEKO_ITEMS_UI_FORM_TEMPLATE),
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
        ),200
    except BaseException:
        current_app.logger.error(
            'Unexpected error: {}'.format(sys.exc_info()[0]))
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
                                   error_type='no_itemtype'),404
        json_schema = '/items/jsonschema/{}'.format(item_type_id)
        schema_form = '/items/schemaform/{}'.format(item_type_id)
        record = {}
        files = []
        endpoints = {}
        activity_session = session.get('activity_info',{})
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
        current_app.logger.error(
            'Unexpected error: {}'.format(sys.exc_info()[0]))
    return abort(400)


@blueprint.route('/iframe/model/save', methods=['POST'])
@login_required_customize
def iframe_save_model():
    """Renders an item register view.

    :return: The rendered template.
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify(code=1, msg="リクエストデータがありません"), 400

        is_duplicate, recid_list, recid_links = is_duplicate_record(data)
        if is_duplicate:
            return jsonify({
                "code": 1,
                "msg": _('The same item may have been registered.'),
                "recid_list": recid_list,
                "duplicate_links": recid_links,
                "is_duplicate": is_duplicate,
            })

        if data and data.get('metainfo'):
            metainfo = deepcopy(data.get('metainfo'))
            for key in list(metainfo.keys()):
                if key.startswith('either_valid_'):
                    del data['metainfo'][key]

        # セッション取得
        activity_session = session.get('activity_info', {})
        activity_id = activity_session.get('activity_id', None)
        if activity_id:
            sanitize_input_data(data)
            save_title(activity_id, data)
            # メタデータからweko_linkを作成します。
            weko_link = get_weko_link(data)
            data["weko_link"] = weko_link
            activity = WorkActivity()
            activity.upt_activity_metadata(activity_id, json.dumps(data))
            db.session.commit()
    except Exception as ex:
        db.session.rollback()
        current_app.logger.exception("{}".format(ex))
        return jsonify(code=1, msg='Model save error'), 500  # HTTP 500 エラーを返す

    return jsonify(code=0, msg='Model save success at {} (UTC)'.format(
        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))), 200


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
        current_app.logger.error(
            'Unexpected error: {}'.format(sys.exc_info()[0]))
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
        current_app.logger.error(
            'Unexpected error: {}'.format(sys.exc_info()[0]))
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
        action = 'private' \
            if record.get('publish_status', PublishStatus.PRIVATE.value) \
                in [PublishStatus.DELETE.value, PublishStatus.PRIVATE.value, PublishStatus.NEW.value] \
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

        redis_connection = RedisConnection()
        sessionstore = redis_connection.connection(db=current_app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True)
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
    except PIDDoesNotExistError as ex:
        current_app.logger.error(
            'PIDDoesNotExistError: {}'.format(ex))
    except KeyError as ex:
        current_app.logger.error('KeyError: {}'.format(ex))
    except FileNotFoundError as ex:
        current_app.logger.error("FileNotFoundError: {}".format(ex))
    except BuildError as ex:
        current_app.logger.error("BuildError: {}".format(ex))
    except BadRequest as ex:
        current_app.logger.error("BadRequest: {}".format(ex))
    except BaseException:
        current_app.logger.error(
            'Unexpected error: {}'.format(sys.exc_info()[0]))
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
        action = 'private' \
            if record.get('publish_status', PublishStatus.PRIVATE.value) \
                in [PublishStatus.DELETE.value, PublishStatus.PRIVATE.value, PublishStatus.NEW.value] \
            else 'publish'

        community_id = session.get('itemlogin_community_id')
        ctx = {'community': None}
        if community_id:
            comm = GetCommunity.get_community_by_id(community_id)
            ctx = {'community': comm}

        if request.method == 'GET':
            cur_activity = session.get('itemlogin_activity')
            if cur_activity is None:
                abort(400)

            workflow = WorkFlows()
            workflow_detail = workflow.get_workflow_by_id(
                cur_activity.workflow_id)

            if workflow_detail and workflow_detail.index_tree_id:
                index_id = get_index_id(cur_activity.activity_id)
                update_index_tree_for_record(pid_value, index_id)
                db.session.commit()
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
                    # current_app.logger.debug("session['itemlogin_item']:{}".format(session['itemlogin_item']))
                    session['itemlogin_item']['title'] = \
                        root_record['title'][0]
                    files_thumbnail = get_thumbnails(files, None)
            else:
                # current_app.logger.debug("session['itemlogin_record']: {}".format(session['itemlogin_record']))
                root_record = session['itemlogin_record']
            if root_record and files and len(root_record) > 0 and \
                    len(files) > 0 and isinstance(root_record, (list, dict)):
                files = set_files_display_type(root_record, files)

            from weko_workflow.utils import get_main_record_detail
            record_detail_alt = get_main_record_detail(
                cur_activity.activity_id, cur_activity)
            ctx.update(
                dict(
                    record_org=record_detail_alt.get('record'),
                    files_org=record_detail_alt.get('files'),
                    thumbnails_org=record_detail_alt.get('files_thumbnail')
                )
            )
            # current_app.logger.debug("session['itemlogin_activity']: {}".format(session['itemlogin_activity']))
            # current_app.logger.debug("session['itemlogin_item']: {}".format(session['itemlogin_item']))
            # current_app.logger.debug("session['itemlogin_steps']: {}".format(session['itemlogin_steps']))
            # current_app.logger.debug("session['itemlogin_action_id']: {}".format(session['itemlogin_action_id']))
            # current_app.logger.debug("session['itemlogin_cur_step']: {}".format(session['itemlogin_cur_step']))
            # current_app.logger.debug("session['itemlogin_histories']: {}".format(session['itemlogin_histories']))
            # current_app.logger.debug("session['itemlogin_res_check']: {}".format(session['itemlogin_res_check']))
            # current_app.logger.debug("session['itemlogin_pid']: {}".format(session['itemlogin_pid']))

            form = FlaskForm(request.form)

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
                form=form,
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

        redis_connection = RedisConnection()
        sessionstore = redis_connection.connection(db=current_app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True)
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
                bytes(json.dumps(data),"utf-8"),
                ttl_secs=300)
        return jsonify(data)
    except KeyError as ex:
        db.session.rollback()
        current_app.logger.error('KeyError: {}'.format(ex))
    except AttributeError as ex:
        db.session.rollback()
        current_app.logger.error('AttributeError: {}'.format(ex))
        import traceback
        current_app.logger.error(traceback.format_exc())
    except BadRequest as ex:
        db.session.rollback()
        current_app.logger.error('BadRequest: {}'.format(ex))
    except StatementError as ex:
        db.session.rollback()
        current_app.logger.error('BadRequest: {}'.format(ex))
    except BaseException:
        db.session.rollback()
        current_app.logger.error(
            'Unexpected error: {}'.format(sys.exc_info()[0]))
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
    # activity_session = session['activity_info']
    activity_session = session.get('activity_info',{})
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
@item_permission.require(http_exception=403)
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
@item_permission.require(http_exception=403)
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


@blueprint.route('/prepare_edit_item', methods=['POST'])
@login_required
def prepare_edit_item(id=None, community=None):
    """Prepare_edit_item.

    Host the api which provide 2 service:
        Check permission: check if user is owner/admin/shared user
        Create new activity for editing flow
    request:
        header: Content type must be json
        data:
            pid_value: pid_value
    Args:
        id: pid_value
    return: The result json:
        code: status code,
        msg: meassage result,
        data: url redirect
    """
    err_code = current_app.config.get(
        'WEKO_ITEMS_UI_API_RETURN_CODE_ERROR', -1
    )

    if not id and request:
        if request.headers['Content-Type'] != 'application/json':
            """Check header of request"""
            return jsonify(code=err_code, msg=_('Header Error'))

    post_activity = request.get_json() or {}
    getargs = request.args if request else {}
    pid_value = id or post_activity.get('pid_value')
    community = community or getargs.get('community', None)

    # Check redis cache
    if not lock_item_will_be_edit(pid_value):
        current_app.logger.error(f"Item {pid_value} is being edited.")
        return jsonify(
            code=err_code,
            msg=_('This Item is being edited.')
        )

    if pid_value:
        pid_value = str(pid_value)
        record_class = import_string('weko_deposit.api:WekoDeposit')
        resolver = Resolver(pid_type='recid',
                            object_type='rec',
                            getter=record_class.get_record)
        recid, deposit = resolver.resolve(pid_value)
        authenticators = [
            str(deposit.get('owner')),
            str(deposit.get('weko_shared_id'))
        ]
        user_id = str(get_current_user())
        work_activity = WorkActivity()
        latest_pid = PIDVersioning(child=recid).last_child

        # ! Check User's Permissions
        if user_id not in authenticators and not get_user_roles(is_super_role=True)[0]:
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
                msg=_('Item cannot be edited because the import is in progress.')
            )

        # ! Check Record is being edit
        item_uuid = latest_pid.object_uuid
        latest_activity = work_activity.get_workflow_activity_by_item_id(item_uuid)
        current_app.logger.info(f"pid_value: {pid_value}, item_uuid: {item_uuid}, latest_activity: {latest_activity}")

        is_begin_edit = check_item_is_being_edit(recid, latest_activity, work_activity)
        if is_begin_edit:
            current_app.logger.info(f"Item {pid_value} is being edited.")
            return jsonify(
                code=err_code,
                msg=_('This Item is being edited.'),
                activity_id=is_begin_edit
            )

        if latest_activity:
            post_activity['workflow_id'] = latest_activity.workflow_id
            post_activity['flow_id'] = latest_activity.flow_id
        else:
            latest_activity = work_activity.get_workflow_activity_by_item_id(
                recid.object_uuid
            )
            workflow = get_workflow_by_item_type_id(
                item_type.name_id, item_type_id
            )
            if not workflow:
                return jsonify(
                    code=err_code,
                    msg=_('Workflow setting does not exist.')
                )
            post_activity['workflow_id'] = workflow.id
            post_activity['flow_id'] = workflow.flow_id

        post_activity['itemtype_id'] = item_type_id
        post_activity['community'] = community
        post_activity['post_workflow'] = latest_activity

        try:
            rtn = prepare_edit_workflow(post_activity, recid, deposit)
            db.session.commit()
        except SQLAlchemyError as ex:
            current_app.logger.error('sqlalchemy error: {}'.format(ex))
            traceback.format_exc()
            db.session.rollback()
            return jsonify(
                code=err_code,
                msg=_('An error has occurred.')
            )
        except BaseException as ex:
            current_app.logger.error('Unexpected error: {}'.format(ex))
            traceback.format_exc()
            db.session.rollback()
            return jsonify(
                code=err_code,
                msg=_('An error has occurred.')
            )

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


@blueprint.route('/prepare_delete_item', methods=['POST'])
@login_required
def prepare_delete_item(id=None, community=None, shared_user_id=-1):
    """Prepare delete item.

    Delete item directly or create delete activity.

    Request:
        header: Content type must be json
        data:
            pid_value: pid_value
        query:
            community: community id

    Args:
        id (str): pid_value
        community (str): community id
        shared_user_id (int): shared user id

    Returns:
        Response: JSON response with code and message.
    """
    err_code = current_app.config.get(
        'WEKO_ITEMS_UI_API_RETURN_CODE_ERROR', -1
    )

    if not id and request:
        if request.headers['Content-Type'] != 'application/json':
            """Check header of request"""
            return jsonify(code=err_code, msg=_('Header Error'))

    post_activity = request.get_json() or {}
    getargs = request.args if request else {}
    del_value = str(id or post_activity.get('pid_value'))
    pid_value = del_value.replace("del_ver_", "")
    community = community or getargs.get('community', None)

    # Check redis cache
    if not lock_item_will_be_edit(pid_value.split(".")[0]):
        current_app.logger.error(f"Item {pid_value} is being edited.")
        return jsonify(
            code=err_code,
            msg=_('This Item is being edited.')
        )

    if pid_value:
        record_class = import_string('weko_deposit.api:WekoDeposit')
        resolver = Resolver(
            pid_type='recid', object_type='rec',
            getter=record_class.get_record
        )
        recid, deposit = resolver.resolve(pid_value)
        authenticators = [
            str(deposit.get('owner')), str(deposit.get('weko_shared_id'))
        ]
        user_id = str(current_user.get_id())
        work_activity = WorkActivity()
        latest_pid = PIDVersioning(child=recid).last_child

        # ! Check User's Permissions
        if user_id not in authenticators and not get_user_roles(is_super_role=True)[0]:
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
                msg=_('Item cannot be edited because the import is in progress.')
            )

        workflow, workflow_id = None, None
        # ! Check Record is being edit
        item_uuid = latest_pid.object_uuid
        latest_activity = work_activity.get_workflow_activity_by_item_id(item_uuid)

        is_begin_edit = check_item_is_being_edit(recid, latest_activity, work_activity)
        if is_begin_edit:
            current_app.logger.info(f"Item {pid_value} is being edited.")
            return jsonify(
                code=err_code,
                msg=_('This Item is being edited.'),
                activity_id=is_begin_edit
            )

        if latest_activity:
            workflow = WorkFlows().get_workflow_by_id(latest_activity.workflow_id)
            if not workflow.is_deleted:
                workflow_id = latest_activity.workflow_id

        if not workflow_id:
            workflow = get_workflow_by_item_type_id(
                item_type.name_id, item_type_id, with_deleted=False
            )
            if workflow:
                workflow_id = workflow.id

        post_activity['itemtype_id'] = item_type_id
        post_activity['community'] = community
        post_activity['workflow_id'] = workflow_id
        post_activity["title"] = deposit.get("item_title") or None

        from .utils import send_mail_item_deleted, send_mail_delete_request

        if not workflow or workflow.delete_flow_id is None:
            from weko_records_ui.views import soft_delete
            soft_delete(del_value)
            send_mail_item_deleted(pid_value, deposit, user_id)
            return jsonify(
                code=0,
                msg="success",
                data=dict(redirect=request.referrer)
            )

        post_activity['flow_id'] = workflow.delete_flow_id
        post_activity['shared_user_id'] = shared_user_id

        try:
            rtn = prepare_delete_workflow(post_activity, recid, deposit)
            db.session.commit()
        except SQLAlchemyError as ex:
            current_app.logger.error('sqlalchemy error: {}'.format(ex))
            traceback.format_exc()
            db.session.rollback()
            return jsonify(
                code=err_code,
                msg=_('An error has occurred.')
            )
        except Exception as ex:
            current_app.logger.error('Unexpected error: {}'.format(ex))
            traceback.format_exc()
            db.session.rollback()
            return jsonify(
                code=err_code,
                msg=_('An error has occurred.')
            )

        if community:
            comm = GetCommunity.get_community_by_id(community)
            url_redirect = url_for(
                'weko_workflow.display_activity',
                activity_id=rtn.activity_id, community=comm.id
            )
        else:
            url_redirect = url_for(
                'weko_workflow.display_activity',
                activity_id=rtn.activity_id
            )

        if rtn.action_id == 2:   # end_action
            send_mail_item_deleted(pid_value, deposit, user_id)

        if rtn.action_id == 4:   # approval
            send_mail_delete_request(rtn)

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

    if not settings:
        upd_data = RankingSettings()
        dafault_data = current_app.config['WEKO_ITEMS_UI_RANKING_DEFAULT_SETTINGS']
        upd_data.is_show = dafault_data['is_show']
        upd_data.new_item_period = dafault_data['new_item_period']
        upd_data.statistical_period = dafault_data['statistical_period']
        upd_data.display_rank = dafault_data['display_rank']
        upd_data.rankings = dafault_data['rankings']
        RankingSettings.update(data=upd_data)
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
        post_data = request.form.to_dict()
        if (post_data["export_format_radio"] == "ROCRATE"):
            return export_rocrate(post_data)
        return export_items(post_data)

    from weko_search_ui.api import SearchSetting
    search_type = request.args.get('search_type', '0')  # TODO: Refactor
    community_id = ""
    ctx = {'community': None}
    cur_index_id = search_type if search_type not in ('0', '1',) else None
    if 'community' in request.args:
        from weko_workflow.api import GetCommunity
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        if comm is not None:
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
    {
    "code": 1,
    "error_list": {
        "either": [],
        "either_key": [],
        "mapping": [],
        "pattern": [],
        "required": [],
        "required_key": []
    },
    "msg": []
    }
    """

    redis_connection = RedisConnection()
    sessionstore = redis_connection.connection(db=current_app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True)
    if sessionstore.redis.exists(
            'updated_json_schema_{}'.format(activity_id)) \
            and sessionstore.get('updated_json_schema_{}'.format(activity_id)):
        session_data = sessionstore.get(
            'updated_json_schema_{}'.format(activity_id))
        error_list = json.loads(session_data.decode('utf-8'))
        msg = [_('PID does not meet the conditions.')]
        if error_list.get('mapping'):
            mapping_err_msg = _('The mapping of required items for DOI '
                                'validation is not set. Please recheck the '
                                'following mapping settings.<br/>{}')
            keys = [k for k in error_list.get('mapping')]
            msg.append(mapping_err_msg.format('<br/>'.join(keys)))
        if error_list.get('other'):
            msg.append(_(error_list.get('other')))
        return jsonify(code=1, msg=msg, error_list=error_list)
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
            name = prefix.name
            scheme = prefix.scheme
            url = prefix.url
            result = dict(
                name=name,
                scheme=scheme,
                url=url
            )
            results.append(result)
        return jsonify(results)
    else:
        return abort(403)

@blueprint_api.route('/author_affiliation_settings', methods=['GET'])
def get_authors_affiliation_settings():
    """Get all author affiliation settings."""
    author_affiliation_settings = get_data_authors_affiliation_settings()
    if author_affiliation_settings is not None:
        results = []
        for affiliation in author_affiliation_settings:
            name = affiliation.name
            scheme = affiliation.scheme
            url = affiliation.url
            result = dict(
                name=name,
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
def check_record_doi_indexes(pid_value='0', doi='0'):
    """Check restrict DOI and Indexes.

    Args:
        pid_value (str, optional): _description_. Defaults to '0'.

    Returns:
        _type_: _description_
    Rises:
        invenio_pidstore.errors.PIDDoesNotExistError
    """
    doi = int(request.args.get('doi') or doi)
    record = WekoRecord.get_record_by_pid(pid_value)
    if (record.pid_doi or doi > 0) and \
            not check_index_permissions(record=record, is_check_doi=True):
        return jsonify({
            'code': -1
        })

    return jsonify({'code': 0})

@blueprint.teardown_request
@blueprint_api.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("weko_items_ui dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()
