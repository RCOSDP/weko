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

"""Blueprint for Weko index tree rest."""

import inspect

import json
from datetime import datetime as dt
from flask import Blueprint, current_app, jsonify, request, make_response, session
from flask_babelex import get_locale
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_rest import ContentNegotiatedMethodView
from werkzeug.http import generate_etag
from weko_deposit.api import WekoDeposit
from weko_index_tree.api import Indexes
from weko_index_tree.utils import get_index_id
from weko_items_ui.api import item_login
from weko_records.api import ItemTypes, Mapping
from weko_records.serializers.utils import get_item_type_name, get_mapping
from weko_redis.redis import RedisConnection
from weko_search_ui.utils import get_thumbnail_key, handle_check_item_is_locked
from weko_workflow.models import ActionStatusPolicy

from .api import WorkActivity, Action, WorkActivityHistory, WorkFlow
from .errors import ExpiredActivityError, IndexNotFoundError, InternalServerError, InvalidParameterValueError, InvalidTokenError, ItemUneditableError, MetadataFormatError, PermissionError, StatusNotItemRegistrationError, VersionNotFoundRESTError, \
    StatusNotApproveError
from .scopes import activity_scope
from .utils import auto_fill_title, create_conditions_dict, check_role, check_etag, check_pretty, get_activity_display_info, create_limmiter, \
    get_files_and_thumbnail, get_main_record_detail, get_pid_and_record, get_usage_data, is_hidden_pubdate, is_usage_application_item_type, \
    prepare_data_for_guest_activity, save_activity_data, validate_guest_activity_expired, validate_guest_activity_token
from .views import check_authority_action, next_action, previous_action

limiter = create_limmiter()


def create_blueprint(app, endpoints):
    """
    Create Weko-Workflow-REST blueprint.
    See: :data:`weko_workflow.config.WEKO_WORKFLOW_REST_ENDPOINTS`.

    :param endpoints: List of endpoints configuration.
    :returns: The configured blueprint.
    """
    blueprint = Blueprint(
        'weko_workflow_rest',
        __name__,
        url_prefix='',
    )

    @blueprint.teardown_request
    def dbsession_clean(exception):
        current_app.logger.debug('weko_workflow dbsession_clean: {}'.format(exception))
        if exception is None:
            try:
                db.session.commit()
            except:
                db.session.rollback()
        db.session.remove()

    for endpoint, options in (endpoints or {}).items():
        if endpoint == 'activities':
            activities = GetActivities.as_view(
                GetActivities.view_name.format(endpoint),
                default_media_type=options.get('default_media_type')
            )
            blueprint.add_url_rule(
                options.get('activities_route'),
                view_func=activities,
                methods=['GET']
            )
        elif endpoint == 'approve':
            view_func = ApproveActivity.as_view(
                ApproveActivity.view_name.format(endpoint),
                default_media_type=options.get('default_media_type')
            )
            blueprint.add_url_rule(
                options.get('route'),
                view_func=view_func,
                methods=['POST']
            )
        elif endpoint == 'throw_out':
            view_func = ThrowOutActivity.as_view(
                ThrowOutActivity.view_name.format(endpoint),
                default_media_type=options.get('default_media_type')
            )
            blueprint.add_url_rule(
                options.get('route'),
                view_func=view_func,
                methods=['POST']
            )
        elif endpoint == 'file_application':
            view_func = FileApplicationActivity.as_view(
                FileApplicationActivity.view_name.format(endpoint),
                default_media_type=options.get('default_media_type')
            )
            blueprint.add_url_rule(
                options.get('route'),
                view_func=view_func,
                methods=['POST']
            )

    return blueprint


class GetActivities(ContentNegotiatedMethodView):
    """Resource to get workflow activities."""
    view_name = '{0}_activities'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(GetActivities, self).__init__(
            *args,
            **kwargs
        )

    @require_api_auth()
    @require_oauth_scopes(activity_scope.id)
    @limiter.limit('')
    def get(self, **kwargs):
        """
        Get workflow activities.

        :returns: Workflow activities filtered by search criteria.
        """

        version = kwargs.get('version')
        func_name = f'get_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    def get_v1(self, **kwargs):
        from .config import WEKO_WORKFLOW_TODO_TAB, WEKO_WORKFLOW_WAIT_TAB, WEKO_WORKFLOW_ALL_TAB

        try:
            # Check user and permission
            if not current_user or not check_role():
                raise PermissionError()

            # Get parameter
            param_pretty = str(request.values.get('pretty', 'false'))
            param_status = str(request.values.get('status', 'todo'))
            param_limit = str(request.values.get('limit', '20'))
            param_page = str(request.values.get('page', '1'))

            # Check parameter
            if not param_status in [WEKO_WORKFLOW_TODO_TAB, WEKO_WORKFLOW_WAIT_TAB, WEKO_WORKFLOW_ALL_TAB]:
                raise InvalidParameterValueError()
            if not param_limit.isnumeric() or not param_page.isnumeric():
                raise InvalidParameterValueError()

            # Check ETag
            etag = generate_etag(str(param_status + param_limit + param_page + param_pretty).encode('utf-8'))
            if check_etag(etag):
                return make_response('304 Not Modified', 304)

            # Check pretty
            check_pretty(param_pretty)

            # Setting language
            language = request.headers.get('Accept-Language', 'en')
            if language in current_app.config.get('WEKO_WORKFLOW_API_ACCEPT_LANGUAGES'):
                get_locale().language = language

            # Get activity list
            work_activity = WorkActivity()
            rst_activities, _rst_max, rst_size, rst_page, _rst_name, rst_count = \
                work_activity.get_activity_list(None, create_conditions_dict(param_status, param_limit, param_page), False)

            activity_list = []
            for activity in rst_activities:
                _activity = \
                    {
                        'created': activity.created.strftime('%Y-%m-%d %H:%M:%S'),
                        'updated': activity.updated.strftime('%Y-%m-%d %H:%M:%S'),
                        'activity_id': activity.activity_id,
                        'item_name': activity.title,
                        'workflow_type': activity.workflow.flows_name,
                        'action': _(activity.action.action_name),
                        'status': _(activity.StatusDesc),
                        'user': activity.email
                    }
                activity_list.append(_activity)

            # Response setting
            json_dict = dict()
            json_dict.update({'total': rst_count})
            json_dict.update({'condition': dict(status=param_status, limit=rst_size, page=rst_page)})
            json_dict.update({'activities': activity_list})
            response = make_response(jsonify(json_dict), 200)
            response.headers['ETag'] = etag

            return response

        except InvalidParameterValueError:
            raise InvalidParameterValueError()
        except PermissionError:
            raise PermissionError()
        except Exception:
            raise InternalServerError()


class ApproveActivity(ContentNegotiatedMethodView):
    """Resource to approve workflow activities."""
    view_name = '{0}_activity'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(ApproveActivity, self).__init__(*args, **kwargs)

    @require_api_auth()
    @require_oauth_scopes(activity_scope.id)
    @limiter.limit('')
    def post(self, **kwargs):
        """
        Approve workflow activity.

        Returns:
            Approved result.
        """
        version = kwargs.get('version')
        func_name = f'post_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    def post_v1(self, **kwargs):
        activity_id = kwargs.get('activity_id')

        # Check if activity status is approval
        action_endpoint, action_id, activity_detail, _cur_action, _histories, _item, _steps, _temporary_comment, _workflow_detail, _owner_id, _shared_user_ids = \
            get_activity_display_info(activity_id)
        if action_endpoint != 'approval':
            raise StatusNotApproveError

        # Check if you can approve
        res_check = check_authority_action(activity_id, action_id, True, activity_detail.action_order)
        if res_check != 0:
            raise PermissionError

        # Do approval action
        next_action(activity_id=activity_id, action_id=action_id)

        # Response setting
        res_json = ApproveActivity.create_approve_response(activity_id)
        response = make_response(jsonify(res_json), 200)

        return response

    @staticmethod
    def create_approve_response(activity_id):
        """
        Create approve API response

        Args:
            activity_id: Activity ID.

        Returns:
            API response.
        """

        activity = WorkActivity().get_activity_by_id(activity_id)
        action = Action().get_action_detail(activity.action_id)

        # get latest approve history
        histories = WorkActivityHistory().get_activity_history_list(activity_id)
        histories = [history for history in histories if history.action_id == 4]
        histories = sorted(histories, key=lambda x: x.action_date, reverse=True)
        history = histories[0]

        res_json = {
            'next_action': {
                'id': activity.action_id,
                'endpoint': action.action_endpoint,
            },
            'action_info': {
                'action_id': history.action_id,
                'action_date': history.action_date.strftime('%Y/%m/%d %H:%M:%S.%f'),
                'action_user': history.action_user,
                'action_status': history.action_status,
                'action_comment': history.action_comment,
            },
        }
        return res_json


class ThrowOutActivity(ContentNegotiatedMethodView):
    """Resource to throw out workflow activities."""
    view_name = '{0}_activity'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(ThrowOutActivity, self).__init__(*args, **kwargs)

    @require_api_auth()
    @require_oauth_scopes(activity_scope.id)
    @limiter.limit('')
    def post(self, **kwargs):
        """
        Throw out workflow activity.

        Returns:
            Thrown out result.
        """
        version = kwargs.get('version')
        func_name = f'post_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    def post_v1(self, **kwargs):
        activity_id = kwargs.get('activity_id')

        # Check if activity status is approval
        action_endpoint, action_id, activity_detail, _cur_action, _histories, _item, _steps, _temporary_comment, _workflow_detail, _owner_id, _shared_user_ids = \
            get_activity_display_info(activity_id)
        if action_endpoint != 'approval':
            raise StatusNotApproveError

        # Check if you can approve
        res_check = check_authority_action(activity_id, action_id, True, activity_detail.action_order)
        if res_check != 0:
            raise PermissionError

        # Do throw out action
        req = 0  # Return to previous action
        previous_action(activity_id=activity_id, action_id=action_id, req=req)

        # Response setting
        res_json = ApproveActivity.create_approve_response(activity_id)
        response = make_response(jsonify(res_json), 200)

        return response

class FileApplicationActivity(ContentNegotiatedMethodView):
    view_name = '{0}_activity'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(FileApplicationActivity, self).__init__(*args, **kwargs)

    @require_api_auth(True)
    @require_oauth_scopes(activity_scope.id)
    @limiter.limit('')
    def post(self, **kwargs):
        """
        Post file application.

        Returns:
            Result json.
        """
        version = kwargs.get('version')
        func_name = f'post_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError() # 404 Error

    def post_v1(self, **kwargs):
        def _fit_item_data_to_schema(schema, item_data, activity,
                                     current_key="", errors:list=[], _title_fill_data:dict={}):
            ret = None
            if schema.get('type') == 'object':
                ret = {}
                properties = schema.get('properties')
                
                for schema_key, schema_val in properties.items():
                    full_key = schema_key if not current_key else f"{current_key}.{schema_key}"
                    res_item = _fit_item_data_to_schema(schema_val, item_data.get(schema_key, {}), activity,
                                                        current_key=full_key, errors=errors, _title_fill_data=_title_fill_data)
                    ret[schema_key] = res_item

            elif schema.get('type') == 'array' and schema.get('items'):
                ret = []
                if not isinstance(item_data, list):
                    item_data = [{}]
                for idx, sub_item_data in enumerate(item_data):
                    full_key = idx if not current_key else f"{current_key}.{idx}"
                    res_item = _fit_item_data_to_schema(schema.get('items'), sub_item_data, activity,
                                                        current_key=full_key, errors=errors, _title_fill_data=_title_fill_data)
                    if res_item:
                        ret.append(res_item)

            elif "string" in schema.get('type'):
                sub_item_key = current_key.split('.')[-1]
                ret = item_data if item_data else ""
                ret = _auto_fill(sub_item_key, ret, activity)
                if not ret and schema.get('default'):
                    ret = schema.get('default')
                if schema.get('enum'):
                    if ret and not ret in schema.get('enum'):
                        errors.append(f"{ret} is not one of enum in {current_key}")
                if sub_item_key == 'subitem_fullname':
                    _title_fill_data['subitem_fullname_value'] = ret
                if sub_item_key == 'subitem_restricted_access_item_title':
                    _title_fill_data['subitem_restricted_access_item_title_key'] = current_key

            return ret
        
        def _auto_fill(key, value, activity):
            target_keys = []
            if activity['usage_type'] == "Application":
                target_keys = [
                    'subitem_restricted_access_dataset_usage',
                    'subitem_restricted_access_usage_report_id',
                    'subitem_restricted_access_wf_issued_date',
                    'subitem_restricted_access_application_date',
                    'subitem_restricted_access_approval_date',
                    'subitem_restricted_access_item_title'
                ]
            elif activity['usage_type'] == "Report":
                target_keys = [
                    'subitem_restricted_access_dataset_usage',
                    'subitem_fullname',
                    'subitem_mail_address',
                    'subitem_university/institution',
                    'subitem_affiliated_division/department',
                    'subitem_position',
                    'subitem_position(others)',
                    'subitem_phone_number',
                    'subitem_restricted_access_usage_report_id',
                    'subitem_restricted_access_wf_issued_date',
                    'subitem_restricted_access_application_date',
                    'subitem_restricted_access_approval_date',
                    'subitem_restricted_access_item_title'
                ]
            if key in target_keys:
                if key == 'subitem_restricted_access_dataset_usage':
                    # dataset_usage
                    value = activity['dataset_usage']
                elif key == 'subitem_restricted_access_usage_report_id':
                    # usage_report_id
                    value = activity['usage_report_id']
                elif key == 'subitem_restricted_access_wf_issued_date':
                    # wf_issued_date
                    value = activity['wf_issued_date']
                elif key == 'subitem_restricted_access_application_date':
                    # (today: YYYY-MM-DD)
                    value = dt.today().strftime('%Y-%m-%d')
                elif key == 'subitem_restricted_access_approval_date':
                    # '' (承認時に入る値のため空にする)
                    value = ''
                elif key == 'subitem_restricted_access_item_title':
                    # item_title + 入力データに含まれる subitem_fullname の内容
                    # 後で書き換えるのでここでは何もしない
                    pass
                elif key == 'subitem_fullname':
                    # usage_data_name
                    value = activity['usage_data_name']
                elif key == 'subitem_mail_address':
                    # mail_address
                    value = activity['mail_address']
                elif key == 'subitem_university/institution':
                    # university_institution
                    value = activity['university_institution']
                elif key == 'subitem_affiliated_division/department':
                    # affiliated_division_department
                    value = activity['affiliated_division_department']
                elif key == 'subitem_position':
                    # position
                    value = activity['position']
                elif key == 'subitem_position(others)':
                    # position_other
                    value = activity['position_other']
                elif key == 'subitem_phone_number':
                    # phone_number
                    value = activity['phone_number']
            return value
        
        def _title_auto_fill(item_data, activity, title_fill_data):
            usage_type = activity.get('usage_type')
            if usage_type and usage_type in ["Application", "Report"]:
                item_title = activity.get('item_title')
                restricted_access_item_title_key = title_fill_data.get('subitem_restricted_access_item_title_key')
                fullname_value = title_fill_data.get('subitem_fullname_value')
                if restricted_access_item_title_key:
                    title_val = f"{item_title}{fullname_value}"
                    item_data, is_finished = _recursive_search_and_set_item_data(item_data, restricted_access_item_title_key, title_val)
            return item_data

        def _recursive_search_and_set_item_data(data, target_key, val):
            is_finished=False
            keys = target_key.split('.')
            target = keys.pop(0)
            for k, v in data.items():
                if k != target:
                    continue
                if keys:
                    data[k], is_finished = _recursive_search_and_set_item_data(v, ".".join(keys), val)
                    if is_finished:
                        break
                else:
                    data[k] = val
                    is_finished = True
                    break
            return data, is_finished
        
        def _remove_empty_data(data):
            if isinstance(data, str) and not data:
                return True
            elif isinstance(data, dict):
                remove_list = []
                for item in data:
                    if _remove_empty_data(data[item]):
                        remove_list.append(item)
                for item in remove_list:
                    data.pop(item)
                if not data:
                    return True
            elif isinstance(data, list):
                for item in data:
                    if _remove_empty_data(item):
                        data.remove(item)
                if not data:
                    return True
            return False
        
        def _get_required_keys(schema, current_key=""):
            required_keys = []

            for rkey in schema.get('required', []):
                required_keys.append(f"{current_key}.{rkey}" if current_key else rkey)

            if schema.get('type') == 'object':
                properties = schema.get('properties', {})
                for sub_key, sub_schema in properties.items():
                    full_key = f"{current_key}.{sub_key}" if current_key else sub_key
                    required_keys += _get_required_keys(sub_schema, full_key)

            elif schema.get('type') == 'array' and schema.get('items'):
                full_key = f"{current_key}.[]" if current_key else "[]"
                required_keys += _get_required_keys(schema.get('items'), full_key)

            if required_keys:
                required_keys = list(set(required_keys))
                required_keys.sort()

            return required_keys

        def _check_required(data, schema, excepted_keys, err_keys:list=[]):
            def __exists_data(d, paths):
                if isinstance(d, str) and d:
                    return True
                elif isinstance(d, dict):
                    if len(paths) == 0:
                        return len(d) > 0
                    target = paths.pop(0)
                    if target in d:
                        return __exists_data(d[target], paths)
                elif isinstance(d, list):
                    if len(paths) == 0:
                        return len(d) > 0
                    target = paths.pop(0)
                    if target == "[]":
                        for v in d:
                            if __exists_data(v, list(paths)):
                                return True
                return False

            req_keys = _get_required_keys(schema)
            req_keys = [i for i in req_keys if i not in excepted_keys]

            for rkey in req_keys:
                need_to_check = True

                # if parents exists at err_keys, do not need to check this key.
                paths = rkey.split(".")
                for i in range(len(paths)):
                    if ".".join(paths[:i+1]) in err_keys:
                        need_to_check = False
                        break
                
                if need_to_check and not __exists_data(data, paths):
                    err_keys.append(rkey)


        # Get parameter
        activity_id = kwargs.get('activity_id')
        language = str(request.headers.get('Accept-Language', 'en'))
        param_pretty = str(request.values.get('pretty', 'false'))
        token = request.values.get('token', None)
        index_ids = request.values.get('index_ids', "")
        index_ids = index_ids.split(',') if index_ids else []
        input_item_data = ""
        if request.data:
            input_item_data = json.loads(request.data.decode("utf-8"))
        if not len(input_item_data):
            current_app.logger.error(f"[{activity_id}] request body is empty.")
            raise InvalidParameterValueError() # 400 Error
        
        # Check pretty
        check_pretty(param_pretty)

        # Setting language
        if language in current_app.config.get('WEKO_WORKFLOW_API_ACCEPT_LANGUAGES'):
            get_locale().language = language
        
        # Get activity data
        activity = {}
        if not current_user.is_authenticated:
            # In case guest user
            activity = FileApplicationActivity.get_guest_activity(activity_id, token)
        else:
            activity = FileApplicationActivity.get_activity(activity_id)

        # Check if you can execute action
        if activity.get("res_check", 1) != 0:
            raise PermissionError

        # Fit input_item_data to item_type_schema
        item_type_schema = ItemTypes.get_by_id(activity['id']).schema
        errors = []
        title_fill_data = {}
        reg_data = _fit_item_data_to_schema(item_type_schema, input_item_data, activity,
                                            errors=errors, _title_fill_data=title_fill_data)
        if errors:
            current_app.logger.error(f"[{activity_id}] metadata format error: {errors}")
            raise MetadataFormatError(errors) # 400エラー
        
        # auto fill title
        reg_data = _title_auto_fill(reg_data, activity, title_fill_data)
        _remove_empty_data(reg_data)

        # check required metadata
        required_errors = []
        excepted_keys = []
        if activity.get('is_hidden_pubdate', False):
            excepted_keys.append("pubdate")
        _check_required(reg_data, item_type_schema, excepted_keys, err_keys=required_errors)
        if required_errors:
            required_errors = f"missing requied metadata: {', '.join(required_errors)}"
            current_app.logger.error(f"[{activity_id}] missing requied metadata: {required_errors}")
            raise MetadataFormatError(required_errors) # 400エラー

        # Set path
        workflow = WorkFlow()
        workflow_detail = workflow.get_workflow_by_id(activity['activity'].workflow_id)
        try:
            if workflow_detail and workflow_detail.index_tree_id:
                index_id = get_index_id(activity_id)
                reg_data["path"] = [f"{index_id}"]
            else:
                reg_data["path"] = index_ids

            if not reg_data["path"]:
                current_app.logger.error(f"[{activity_id}] index not specified.")
                raise
            for p in reg_data["path"]:
                if not Indexes.get_index(p):
                    current_app.logger.error(f"[{activity_id}] index not found. (index_id: {p})")
                    raise
        except Exception:
            raise IndexNotFoundError()

        # item registration
        item = {
            "item_title": activity.get('item_title'),
            "$schema": activity.get('jsonschema'),
            "metadata": reg_data,
            "item_type_id": activity.get('id')
        }
        item_id = activity['activity'].item_id
        if not item_id:
            # Deposit new item
            item["id"] = FileApplicationActivity.create_deposit()
        else:
            # Edit item
            pid = PersistentIdentifier.get_by_object(pid_type='recid',
                                                     object_type='rec',
                                                     object_uuid=item_id)
            item["id"] = pid.pid_value
            try:
                handle_check_item_is_locked(item)
            except:
                current_app.logger.error(f"[{activity_id}] this item uneditable. (item_id: {item_id})")
                raise ItemUneditableError()
        
        try:
            FileApplicationActivity.register_item_metadata(item)

            # Update activity
            save_activity_data(dict(
                activity_id = activity_id,
                title = activity.get('item_title'),
                shared_user_ids = []
            ))
            
            # Do ItemRegistration action
            next_action(activity_id=activity_id, action_id=activity['activity'].action_id)
        except Exception as ex:
            current_app.logger.error(f"[{activity_id}] error in item save. (item_id: {item['id']}): {ex}")
            raise InternalServerError()

        # get latest approve history
        from .config import WEKO_WORKFLOW_ITEM_REGISTRATION_ACTION_ID
        histories = WorkActivityHistory().get_activity_history_list(activity_id)
        histories = [history for history in histories if history.action_id == WEKO_WORKFLOW_ITEM_REGISTRATION_ACTION_ID]
        histories = sorted(histories, key=lambda x: x.action_date, reverse=True)
        action_info = {}
        if len(histories) > 0:
            action_info = {
                'action_id': histories[0].action_id,
                'action_date': histories[0].action_date.strftime('%Y/%m/%d %H:%M:%S.%f'),
                'action_user': histories[0].action_user,
                'action_status': histories[0].action_status,
                'action_comment': histories[0].action_comment,
            }

        # Create response
        res_json = {
            "action_info": action_info,
            "registerd_data": reg_data
        }
        response = make_response(jsonify(res_json), 200)
        return response

    def get_activity(activity_id):
        activity = WorkActivity()
        action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail, owner_id, shared_user_ids = get_activity_display_info(activity_id)
        if action_endpoint != 'item_login':
            current_app.logger.error(f"[{activity_id}] action_endpoint is not 'item_login':{action_endpoint}")
            raise StatusNotItemRegistrationError() # 400 Error

        allow_multi_thumbnail = False
        application_item_type = False
        approval_record = []
        data_type = activity_detail.extra_info.get('related_title') if activity_detail.extra_info else None
        files = []
        files_thumbnail = []
        is_hidden_pubdate_value = False
        item_save_uri = ''
        item_type_name = get_item_type_name(workflow_detail.itemtype_id)
        json_schema = ''
        need_billing_file = False
        need_file = False
        need_thumbnail = False
        recid = None
        record = {}
        schema_form = ''
        step_item_login_url = None
        title = ""

        _activity = activity.get_activity_by_id(activity_id)
        if _activity and _activity.action_status != ActionStatusPolicy.ACTION_CANCELED:
            activity_session = dict(
                activity_id=activity_id,
                action_id=activity_detail.action_id,
                action_version=cur_action.action_version,
                action_status=ActionStatusPolicy.ACTION_DOING,
                commond=''
            )
            session['activity_info'] = activity_session
        
        # get item edit page info.
        step_item_login_url, need_file, need_billing_file, \
            record, json_schema, schema_form,\
            item_save_uri, files, endpoints, need_thumbnail, files_thumbnail, \
            allow_multi_thumbnail \
            = item_login(item_type_id=workflow_detail.itemtype_id)

        application_item_type = is_usage_application_item_type(activity_detail)

        if not record and item:
            record = item

        redis_connection = RedisConnection()
        sessionstore = redis_connection.connection(db=current_app.config['ACCOUNTS_SESSION_REDIS_DB_NO'], kv = True)
        if sessionstore.redis.exists(
            'updated_json_schema_{}'.format(activity_id)) \
            and sessionstore.get(
                'updated_json_schema_{}'.format(activity_id)):
            json_schema = (json_schema + "/{}").format(activity_id)
            schema_form = (schema_form + "/{}").format(activity_id)

        title = auto_fill_title(item_type_name)
        is_hidden_pubdate_value = is_hidden_pubdate(item_type_name)

        if item:
            try:
                # get record data for the first time access to editing item screen
                recid, approval_record = get_pid_and_record(item.id)
                files, files_thumbnail = get_files_and_thumbnail(activity_id, item)
            except Exception:
                raise Exception() # 404
        
        res_check = check_authority_action(str(activity_id), int(action_id), True, activity_detail.action_order)
        ctx = {'community': None}
        session['itemlogin_id'] = activity_id
        session['itemlogin_activity'] = activity_detail
        session['itemlogin_item'] = item
        session['itemlogin_steps'] = steps
        session['itemlogin_action_id'] = action_id
        session['itemlogin_cur_step'] = action_endpoint
        session['itemlogin_record'] = approval_record
        session['itemlogin_histories'] = histories
        session['itemlogin_res_check'] = res_check
        session['itemlogin_pid'] = recid
        session['itemlogin_community_id'] = ""

        user_id = current_user.id if hasattr(current_user , 'id') else None
        user_profile = None
        if user_id:
            from weko_user_profiles.views import get_user_profile_info
            user_profile={}
            user_profile['results'] = get_user_profile_info(int(user_id))

        # Get item link info.
        record_detail_alt = get_main_record_detail(
            activity_id, activity_detail, action_endpoint, item,
            approval_record, files, files_thumbnail)
        ctx.update(
            dict(
                record_org=record_detail_alt.get('record'),
                files_org=record_detail_alt.get('files'),
                thumbnails_org=record_detail_alt.get('files_thumbnail')
            )
        )

        # Get Auto fill data for Restricted Access Item Type.
        usage_data = get_usage_data(
            workflow_detail.itemtype_id, activity_detail, user_profile)
        ctx.update(usage_data)
        ctx.update(
            dict(
                files_thumbnail=files_thumbnail,
                files=files,
                record=approval_record
            )
        )

        return dict(
            action_endpoint_key=current_app.config.get(
                'WEKO_ITEMS_UI_ACTION_ENDPOINT_KEY'),
            action_id=action_id,
            activity_id=activity_detail.activity_id,
            activity=activity_detail,
            allow_multi_thumbnail=allow_multi_thumbnail,
            application_item_type=application_item_type,
            auto_fill_data_type=data_type,
            auto_fill_title=title,
            enable_contributor=current_app.config[
                'WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'],
            enable_feedback_maillist=current_app.config[
                'WEKO_WORKFLOW_ENABLE_FEEDBACK_MAIL'],
            error_type='item_login_error',
            histories=histories,
            id=workflow_detail.itemtype_id,
            is_hidden_pubdate=is_hidden_pubdate_value,
            item_save_uri=item_save_uri,
            item=item,
            jsonschema=json_schema,
            # list_license=list_license,
            need_billing_file=need_billing_file,
            need_file=need_file,
            need_thumbnail=need_thumbnail,
            out_put_report_title=current_app.config[
                'WEKO_ITEMS_UI_OUTPUT_REGISTRATION_TITLE'],
            pid=recid,
            records=record,
            res_check=res_check,
            schemaform=schema_form,
            step_item_login_url=step_item_login_url,
            steps=steps,
            user_profile=user_profile,
            **ctx
        )
    
    def get_guest_activity(activity_id, token):
        action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail, owner_id, shared_user_ids = get_activity_display_info(activity_id)
        if action_endpoint != 'item_login':
            current_app.logger.error(f"[{activity_id}] action_endpoint is not 'item_login':{action_endpoint}")
            raise StatusNotItemRegistrationError() # 400 Error
        
        # Get file_name
        extra_info = activity_detail.extra_info
        file_name = extra_info.get('file_name', '')

        # Validate token
        current_app.logger.debug(f"[{activity_id}] token: {token}, file_name: {file_name}")
        is_valid, token_activity_id, guest_email = validate_guest_activity_token(token, file_name)
        if not is_valid or activity_id != token_activity_id:
            current_app.logger.error(f"[{activity_id}] guest activity token is invalid.")
            raise InvalidTokenError() # 400 Error

        error_msg = validate_guest_activity_expired(activity_id)
        if error_msg:
            current_app.logger.error(f"[{activity_id}] guest activity expired:{error_msg}")
            raise ExpiredActivityError() # 400 Error

        session['guest_token'] = token
        session['guest_email'] = guest_email
        session['guest_url'] = request.full_path

        guest_activity = prepare_data_for_guest_activity(activity_id)

        # Get Auto fill data for Restricted Access Item Type.
        usage_data = get_usage_data(
            guest_activity.get('id'), guest_activity.get('activity'))
        guest_activity.update(usage_data)

        # Get item link info.
        record_detail_alt = get_main_record_detail(activity_id,
                                                guest_activity.get('activity'))
        if record_detail_alt.get('record'):
            record_detail_alt['record']['is_guest'] = True

        guest_activity.update(
            dict(
                record_org=record_detail_alt.get('record'),
                files_org=record_detail_alt.get('files'),
                thumbnails_org=record_detail_alt.get('files_thumbnail'),
                record=record_detail_alt.get('record'),
                files=record_detail_alt.get('files'),
                files_thumbnail=record_detail_alt.get('files_thumbnail'),
                pid=record_detail_alt.get('pid', None),
            )
        )

        return guest_activity
    

    def create_deposit():
        # Create deposit
        dep = WekoDeposit.create({})
        return dep["recid"]

    def register_item_metadata(item):
        # Get recid
        pid = PersistentIdentifier.query.filter_by(
            pid_type="recid", pid_value=item["id"]
        ).first()
        record = WekoDeposit.get_record(pid.object_uuid)

        # Set publish_status to private
        record['publish_status'] = '1'
        record.commit()
        
        _deposit_data = record.dumps().get("_deposit")
        deposit = WekoDeposit(record, record.model)
        new_data = dict(
            **item.get("metadata"),
            **_deposit_data,
            **{
                "$schema": item.get("$schema"),
                "title": item.get("item_title"),
                "publish_status": 1 # private
            }
        )
        item_status = {
            "index": new_data["path"],
            "actions": "private"
        }
        if not new_data.get("pid"):
            new_data = dict(
                **new_data, **{"pid": {"revision_id": 0, "type": "recid", "value": item["id"]}}
            )

        # set delete flag for file metadata if is empty.
        new_data, is_cleaned = FileApplicationActivity._clean_file_metadata(item["item_type_id"], new_data)
        new_data = FileApplicationActivity._autofill_thumbnail_metadata(item["item_type_id"], new_data, deposit.files)

        deposit.update(item_status, new_data)
        deposit.commit()

    def _clean_file_metadata(item_type_id, data):
        # clear metadata of file information
        is_cleaned = True
        item_map = get_mapping(Mapping.get_record(item_type_id), "jpcoar_mapping")
        key = item_map.get("file.URI.@value")
        if key:
            key = key.split(".")[0]
            if not data.get(key):
                deleted_items = data.get("deleted_items") or []
                deleted_items.append(key)
                data["deleted_items"] = deleted_items
            else:
                is_cleaned = False
        return data, is_cleaned
    
    def _autofill_thumbnail_metadata(item_type_id, data, files):
        key = get_thumbnail_key(item_type_id)
        if key:
            thumbnail_item = {}
            subitem_thumbnail = []
            for file in files:
                if file.is_thumbnail is True:
                    subitem_thumbnail.append(
                        {
                            "thumbnail_label": file.key,
                            "thumbnail_url": current_app.config["DEPOSIT_FILES_API"]
                            + "/{bucket}/{key}?versionId={version_id}".format(
                                bucket=file.bucket_id,
                                key=file.key,
                                version_id=file.version_id,
                            ),
                        }
                    )
            if subitem_thumbnail:
                thumbnail_item["subitem_thumbnail"] = subitem_thumbnail
            if thumbnail_item:
                data[key] = thumbnail_item
            else:
                deleted_items = data.get("deleted_items") or []
                deleted_items.append(key)
                data["deleted_items"] = deleted_items
        return data
