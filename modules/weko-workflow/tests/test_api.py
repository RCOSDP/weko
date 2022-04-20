import threading
import pytest
from mock import patch, MagicMock
from flask import Flask, json, url_for, jsonify
from invenio_db import db
from sqlalchemy import func

import weko_workflow.utils
from weko_workflow import WekoWorkflow
from weko_workflow.models import Activity,WorkFlow
from invenio_accounts.testutils import login_user_via_session
def _post(client, url, json_data):
    return client.post(url, json=json_data)
@pytest.mark.parametrize('users_index, status_code', [
    #(0, 403),
    #(1, 200),
    #(2, 200),
    #(3, 200),
    (4, 200),
])
def test_display_activity_users(create_activity,client, users, users_index, status_code, db):
    """Test of display activity."""
    login_user_via_session(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.display_activity', activity_id='1')
    input = {}

    #activity_detail = Activity.query.filter_by(activity_id='1').one_or_none()
    activity_detail = create_activity["activity"]
    #cur_action = activity_detail.action
    cur_action=create_activity["action"]
    workflow_detail=create_activity["workflow"]
    #action_endpoint = cur_action.action_endpoint
    #action_id = cur_action.id
    action_endpoint="approval"
    action_id = 4
    histories = 1
    item = None
    steps = 1
    temporary_comment = 1

    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }
    ctx = {'community': None}

    # workflow_detail = WorkFlow(flows_id='{39ba43f0-c876-4086-97f4-d9aed1be8083}', itemtype_id=15, flow_id=1, is_deleted=False, open_restricted=True, is_gakuninrdm=False)
    mock_render_template = MagicMock(return_value=jsonify({}))
    with patch('weko_workflow.views.get_activity_display_info', return_value = (action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.check_authority_action'):
            with patch('weko_workflow.views.WorkActivity.get_activity_action_role', return_value=(roles, action_users)):
                with patch("weko_workflow.views.render_template", mock_render_template):
                    res = _post(client, url, input)
                    mock_render_template.assert_called()