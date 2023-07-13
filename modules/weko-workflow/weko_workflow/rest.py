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

from flask import Blueprint, current_app, jsonify, request, make_response
from flask_babelex import get_locale as get_current_locale
from flask_login import current_user
from invenio_db import db
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_rest import ContentNegotiatedMethodView
from werkzeug.http import generate_etag

from .api import WorkActivity, Action, WorkActivityHistory
from .errors import InternalServerError, InvalidParameterValueError, PermissionError, VersionNotFoundRESTError, \
    StatusNotApproveError
from .scopes import activity_scope
from .utils import create_conditions_dict, check_role, check_etag, check_pretty, get_activity_display_info
from .views import check_authority_action, next_action, previous_action

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
        url_prefix = '',
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
    def get(self, **kwargs):
        """
        Get workflow activities.

        :returns: Workflow activities filtered by search criteria.
        """
        from .config import WEKO_GET_ACTIVITIES_API_VERSION

        version = kwargs.get('version')
        get_api_ver = WEKO_GET_ACTIVITIES_API_VERSION.get(version)
        
        if get_api_ver:
            return get_api_ver(self, **kwargs)
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
            # TODO: support for other languages
            language = request.headers.get('Accept-Language', 'en')
            if language == 'ja':
                get_current_locale().language = language
            
            # Get activity list
            work_activity = WorkActivity()
            rst_activities, _, rst_size, rst_page, _, rst_count = \
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
                        'action': activity.action.action_name,
                        'status': activity.StatusDesc,
                        'user': activity.email
                    }
                activity_list.append(_activity)

            # Response setting
            json_dict = dict()
            json_dict.update({'total': rst_count})
            json_dict.update({'condition': dict(status = param_status, limit = rst_size, page = rst_page)})
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
    def post(self, **kwargs):
        """
        Approve workflow activity.

        Returns:
            Approved result.
        """
        from .config import WEKO_APPROVE_API_VERSION
        version = kwargs.get('version')
        func = WEKO_APPROVE_API_VERSION.get(f'post-{version}')

        if func:
            return func(self, **kwargs)
        else:
            raise VersionNotFoundRESTError()

    def post_v1(self, **kwargs):
        activity_id = kwargs.get('activity_id')

        # Check if activity status is approval
        action_endpoint, action_id, activity_detail, _, _, _, _, _, _ = \
            get_activity_display_info(activity_id)
        if action_endpoint != 'approval':
            raise StatusNotApproveError

        # Check if you can approve
        res_check = check_authority_action(activity_id, action_id, True, activity_detail.action_order)
        if res_check != 0:
            raise PermissionError

        # Do approval action
        next_action(activity_id, action_id)

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
    def post(self, **kwargs):
        """
        Throw out workflow activity.

        Returns:
            Thrown out result.
        """
        from .config import WEKO_THROW_OUT_API_VERSION
        version = kwargs.get('version')
        func = WEKO_THROW_OUT_API_VERSION.get(f'post-{version}')

        if func:
            return func(self, **kwargs)
        else:
            raise VersionNotFoundRESTError()

    def post_v1(self, **kwargs):
        activity_id = kwargs.get('activity_id')

        # Check if activity status is approval
        action_endpoint, action_id, activity_detail, _, _, _, _, _, _ = \
            get_activity_display_info(activity_id)
        if action_endpoint != 'approval':
            raise StatusNotApproveError

        # Check if you can approve
        res_check = check_authority_action(activity_id, action_id, True, activity_detail.action_order)
        if res_check != 0:
            raise PermissionError

        # Do throw out action
        req = 0  # Return to previous action
        previous_action(activity_id, action_id, req)

        # Response setting
        res_json = ApproveActivity.create_approve_response(activity_id)
        response = make_response(jsonify(res_json), 200)

        return response

