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

"""Module tests."""
import copy
import json
from unittest.mock import MagicMock
from weko_workflow.api import WorkActivity
import pytest
from mock import patch
from sqlalchemy.orm.attributes import flag_modified

from flask import json, jsonify, url_for, make_response, current_app
from flask_babelex import gettext as _
from invenio_db import db
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import uuid
from invenio_communities.models import Community
from invenio_pidstore.errors import PIDDoesNotExistError,PIDDeletedError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_cache import current_cache

from weko_admin.models import AdminSettings
from weko_deposit.api import WekoDeposit
from weko_workflow.config import WEKO_WORKFLOW_TODO_TAB, WEKO_WORKFLOW_WAIT_TAB,WEKO_WORKFLOW_ALL_TAB
from flask_login.utils import login_user,logout_user
from invenio_accounts.testutils import login_user_via_session as login
from weko_workflow.models import ActionStatusPolicy, ActivityItemApplication, ActivityRequestMail, ActionJournal, ActionIdentifier, Activity, ActivityHistory, WorkFlow, FlowActionRole, ActivityAction, GuestActivity, ActivityStatusPolicy
from weko_workflow.views import (render_guest_workflow,
                                 previous_action,
                                 check_authority_action,
                                 next_action,
                                 check_authority,
                                 display_guest_activity,
                                 display_guest_activity_item_application,
                                 render_guest_workflow)
from marshmallow.exceptions import ValidationError
from weko_records_ui.models import FileOnetimeDownload, FilePermission
from weko_records.models import ItemMetadata, ItemReference
from weko_workflow.schema.marshmallow import SaveActivitySchema
from weko_items_ui.utils import update_action_handler
from tests.helpers import create_record
from invenio_pidstore.resolver import Resolver
from weko_redis import RedisConnection


def response_data(response):
    return json.loads(response.data)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_index_acl_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_index_acl_nologin(client,db_register2):
    """_summary_

    Args:
        client (FlaskClient): flask test client
    """
    url = url_for('weko_workflow.index')
    res =  client.get(url)
    assert res.status_code == 302
    assert res.location == "http://test_server.localdomain/login/?next=%2Fworkflow%2F"


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code, enable_show_activity, approver_email_visible', [
    (0, 200, False, False),
    (1, 200, True, False),
    (2, 200, False, True),
    (3, 200, True, True),
    (4, 200, False, False),
    (5, 200, True, False),
    (6, 200, False, True),
])
# def test_index_acl(client, users, db_register2,users_index, status_code):
def test_index_acl(client, users, db_register2, mocker, app, users_index, status_code, enable_show_activity, approver_email_visible):
    app.config['WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY'] = enable_show_activity
    app.config['WEKO_WORKFLOW_COLUMNS'] = ['approver_email'] if approver_email_visible else []
    app.config['WEKO_WORKFLOW_APPROVER_EMAIL_COLUMN_VISIBLE'] = approver_email_visible
    mocker.patch("weko_workflow.views.render_template",return_value=make_response())

    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.index',_external=True)
    res = client.get(url)
    assert res.status_code == status_code

    url = url_for('weko_workflow.index',community="a",_external=True)
    res = client.get(url)
    assert res.status_code == status_code

    url = url_for('weko_workflow.index',tab=WEKO_WORKFLOW_TODO_TAB,_external=True)
    res = client.get(url)
    assert res.status_code == status_code

    url = url_for('weko_workflow.index',tab=WEKO_WORKFLOW_TODO_TAB,community="a",_external=True)
    res = client.get(url)
    assert res.status_code == status_code

    url = url_for('weko_workflow.index',tab=WEKO_WORKFLOW_WAIT_TAB,_external=True)
    res = client.get(url)
    assert res.status_code == status_code

    url = url_for('weko_workflow.index',tab=WEKO_WORKFLOW_WAIT_TAB,community="a",_external=True)
    res = client.get(url)
    assert res.status_code == status_code

    url = url_for('weko_workflow.index',tab=WEKO_WORKFLOW_ALL_TAB,_external=True)
    res = client.get(url)
    assert res.status_code == status_code

    url = url_for('weko_workflow.index',tab=WEKO_WORKFLOW_ALL_TAB,community="a",_external=True)
    res = client.get(url)
    assert res.status_code == status_code


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_iframe_success -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_iframe_success(client, db_register_full_action,users, db_records,mocker,without_remove_session):
    mock_render_template = MagicMock(return_value=jsonify({}))
    item = db_records[0][3]
    session = {
        "itemlogin_id":"1",
        "itemlogin_activity":db_register_full_action["activities"][1],
        "itemlogin_item":item,
        "itemlogin_steps":"test steps",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_record":"test approval_record",
        "itemlogin_histories":"test histories",
        "itemlogin_res_check":0,
        "itemlogin_pid":db_records[0][0],
        "itemlogin_community_id":"comm01"
    }
    mocker.patch("weko_workflow.views.session",session)
    with patch("weko_workflow.views.render_template", mock_render_template):
        url = url_for("weko_workflow.iframe_success")
        res = client.get(url)
        args, kwargs = mock_render_template.call_args
        assert args[0] == "weko_workflow/item_login_success.html"
        assert "form" in kwargs

    session = {
        "itemlogin_id":"1",
        "itemlogin_activity":db_register_full_action["activities"][1],
        "itemlogin_item":{},
        "itemlogin_steps":"test steps",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_record":"test approval_record",
        "itemlogin_histories":"test histories",
        "itemlogin_res_check":0,
        "itemlogin_pid":db_records[0][0],
    }
    mocker.patch("weko_workflow.views.session",session)
    with patch("weko_workflow.views.render_template", mock_render_template):
        url = url_for("weko_workflow.iframe_success")
        res = client.get(url)
        args, kwargs = mock_render_template.call_args
        assert args[0] == "weko_workflow/item_login_success.html"
        assert "form" in kwargs

    # not exist session key
    session = {}
    mocker.patch("weko_workflow.views.session",session)
    with patch("weko_workflow.views.render_template",mock_render_template):
        url = url_for("weko_workflow.iframe_success")
        res = client.get(url)
        mock_args, mock_kwargs = mock_render_template.call_args
        assert mock_args[0] == "weko_theme/error.html"
        assert mock_kwargs["error"] == "can not get data required for rendering"
    # can not get value from session
    session = {
        "itemlogin_id":"1",
        "itemlogin_activity":None,
        "itemlogin_item":{},
        "itemlogin_steps":"test steps",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_record":"test approval_record",
        "itemlogin_histories":"test histories",
        "itemlogin_res_check":0,
        "itemlogin_pid":db_records[0][0],
    }
    mocker.patch("weko_workflow.views.session",session)
    with patch("weko_workflow.views.render_template",mock_render_template):
        url = url_for("weko_workflow.iframe_success")
        res = client.get(url)
        mock_args, mock_kwargs = mock_render_template.call_args
        assert mock_args[0] == "weko_theme/error.html"
        assert mock_kwargs["error"] == "can not get data required for rendering"

    # wrong res_check
    session = {
        "itemlogin_id":"1",
        "itemlogin_activity":db_register_full_action["activities"][1],
        "itemlogin_item":{},
        "itemlogin_steps":"test steps",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_record":"test approval_record",
        "itemlogin_histories":"test histories",
        "itemlogin_res_check":"dummy",
        "itemlogin_pid":db_records[0][0],
    }
    mocker.patch("weko_workflow.views.session",session)
    with patch("weko_workflow.views.render_template",mock_render_template):
        url = url_for("weko_workflow.iframe_success")
        res = client.get(url)
        mock_args, mock_kwargs = mock_render_template.call_args
        assert mock_args[0] == "weko_theme/error.html"
        assert mock_kwargs["error"] == "can not get data required for rendering"

    # not exist itemlogin_record in session
    session = {
        "itemlogin_id":"1",
        "itemlogin_activity":db_register_full_action["activities"][1],
        "itemlogin_item":{},
        "itemlogin_steps":"test steps",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_histories":"test histories",
        "itemlogin_res_check":0,
        "itemlogin_pid":db_records[0][0],
    }
    mocker.patch("weko_workflow.views.session",session)
    with patch("weko_workflow.views.render_template",mock_render_template):
        url = url_for("weko_workflow.iframe_success")
        res = client.get(url)
        mock_args, mock_kwargs = mock_render_template.call_args
        assert mock_args[0] == "weko_theme/error.html"
        assert mock_kwargs["error"] == "can not get data required for rendering"

    # file is not list
    session = {
        "itemlogin_id":"1",
        "itemlogin_activity":db_register_full_action["activities"][1],
        "itemlogin_item":item,
        "itemlogin_steps":"test steps",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_record":"test approval_record",
        "itemlogin_histories":"test histories",
        "itemlogin_res_check":0,
        "itemlogin_pid":db_records[0][0],
        "itemlogin_community_id":"comm01"
    }
    mocker.patch("weko_workflow.views.session",session)
    with patch("weko_workflow.views.render_template",mock_render_template):
        with patch("weko_workflow.views.get_record_by_root_ver",return_value=("record","file")):
            url = url_for("weko_workflow.iframe_success")
            res = client.get(url)
            mock_args, mock_kwargs = mock_render_template.call_args
            assert mock_args[0] == "weko_theme/error.html"
            assert mock_kwargs["error"] == "can not get data required for rendering"

    # can not get action
    item = db_records[0][3]
    session = {
        "itemlogin_id":"1",
        "itemlogin_activity":db_register_full_action["activities"][1],
        "itemlogin_item":item,
        "itemlogin_steps":"test steps",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_record":"test approval_record",
        "itemlogin_histories":"test histories",
        "itemlogin_res_check":0,
        "itemlogin_pid":db_records[0][0],
        "itemlogin_community_id":"comm01"
    }
    with patch("weko_workflow.views.render_template",mock_render_template):
        with patch("weko_workflow.views.Action.get_action_detail",return_value=None):
            url = url_for("weko_workflow.iframe_success")
            res = client.get(url)
            mock_args, mock_kwargs = mock_render_template.call_args
            assert mock_args[0] == "weko_theme/error.html"
            assert mock_kwargs["error"] == "can not get data required for rendering"

    # can not get workflow_detail
    item = db_records[0][3]
    session = {
        "itemlogin_id":"1",
        "itemlogin_activity":db_register_full_action["activities"][1],
        "itemlogin_item":item,
        "itemlogin_steps":"test steps",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_record":"test approval_record",
        "itemlogin_histories":"test histories",
        "itemlogin_res_check":0,
        "itemlogin_pid":db_records[0][0],
        "itemlogin_community_id":"comm01"
    }
    with patch("weko_workflow.views.render_template",mock_render_template):
        with patch("weko_workflow.views.WorkFlow.get_workflow_by_id",return_value=None):
            url = url_for("weko_workflow.iframe_success")
            res = client.get(url)
            mock_args, mock_kwargs = mock_render_template.call_args
            assert mock_args[0] == "weko_theme/error.html"
            assert mock_kwargs["error"] == "can not get data required for rendering"


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_init_activity_acl_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_init_activity_acl_nologin(client,db_register2):
    """Test init_activity.

    Args:
        client (_type_): _description_
    """

    """"""
    url = url_for('weko_workflow.init_activity')
    input = {'workflow_id': 1, 'flow_id': 1}
    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == "http://test_server.localdomain/login/?next=%2Fworkflow%2Factivity%2Finit"


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_init_activity_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_init_activity_acl(app, client, users, users_index, status_code, item_type, workflow):
    """_summary_

    Args:
        client (_type_): _description_
        users (_type_): _description_
        users_index (_type_): _description_
        status_code (_type_): _description_
        db_register (_type_): _description_
    """
    workflow_id = workflow['workflow'].id
    flow_def_id = workflow['flow'].id
    item_type_id = item_type[0]['id']
    login(client=client, email=users[users_index]['email'])

    q = Activity.query.all()
    assert len(q) == 0
    q = ActivityHistory.query.all()
    assert len(q) == 0
    q = ActivityAction.query.all()
    assert len(q) == 0
    url = url_for('weko_workflow.init_activity')
    input = {'workflow_id': workflow_id, 'flow_id': flow_def_id, 'activity_confirm_term_of_use': True}
    res = client.post(url, json=input)
    assert res.status_code == status_code
    assert json.loads(res.data.decode('utf-8'))['data']['redirect'].endswith('00001')
    q = Activity.query.all()
    assert len(q) == 1
    q = Activity.query.first()
    assert q.extra_info == {}
    assert q.activity_login_user == users[users_index]['id']
    assert q.activity_update_user == users[users_index]['id']
    assert q.activity_confirm_term_of_use == True
    q = ActivityHistory.query.all()
    assert len(q) == 1
    q = ActivityAction.query.all()
    assert len(q) == 7

    url = url_for('weko_workflow.init_activity')
    input = {'workflow_id': -99, 'flow_id': flow_def_id}
    # with pytest.raises(Exception) as e:
    res = client.post(url, json=input)
    assert res.status_code == 500
    q = Activity.query.all()
    assert len(q) == 1
    q = ActivityHistory.query.all()
    assert len(q) == 1
    q = ActivityAction.query.all()
    assert len(q) == 7

    url = url_for('weko_workflow.init_activity')
    input = {'workflow_id': workflow_id, 'flow_id': -99}
    res = client.post(url, json=input)
    assert res.status_code == 500
    q = Activity.query.all()
    assert len(q) == 16
    q = ActivityHistory.query.all()
    assert len(q) == 2
    q = ActivityAction.query.all()
    assert len(q) == 7

    url = url_for('weko_workflow.init_activity')
    input = {'workflow_id': workflow_id}
    res = client.post(url, json=input)
    assert res.status_code == 400
    q = Activity.query.all()
    assert len(q) == 16
    q = ActivityHistory.query.all()
    assert len(q) == 2
    q = ActivityAction.query.all()
    assert len(q) == 10

    url = url_for('weko_workflow.init_activity')
    input = {'flow_id': flow_def_id}
    res = client.post(url, json=input)
    assert res.status_code == 400
    q = Activity.query.all()
    assert len(q) == 16
    q = ActivityHistory.query.all()
    assert len(q) == 2
    q = ActivityAction.query.all()
    assert len(q) == 10

    input = {}
    res = client.post(url, json=input)
    assert res.status_code == 400
    q = Activity.query.all()
    assert len(q) == 16
    q = ActivityHistory.query.all()
    assert len(q) == 2
    q = ActivityAction.query.all()
    assert len(q) == 10

    url = url_for('weko_workflow.init_activity', community='comm01')
    input = {'workflow_id': str(workflow_id), 'flow_id': str(flow_def_id)}
    res = client.post(url, json=input)
    assert res.status_code == status_code
    assert json.loads(res.data.decode('utf-8'))['data']['redirect'].endswith('comm01')
    q = Activity.query.all()
    assert len(q) == 17
    q = ActivityHistory.query.all()
    assert len(q) == 3
    q = ActivityAction.query.all()
    assert len(q) == 14

    url = url_for('weko_workflow.init_activity')
    input = {'workflow_id': 'd'+str(workflow_id), 'flow_id': str(flow_def_id)}
    res = client.post(url, json=input)
    assert res.status_code == 400
    q = Activity.query.all()
    assert len(q) == 17
    q = ActivityHistory.query.all()
    assert len(q) == 3
    q = ActivityAction.query.all()
    assert len(q) == 14

    url = url_for('weko_workflow.init_activity')
    input = {'workflow_id': str(workflow_id)+'d', 'flow_id': str(flow_def_id)}
    res = client.post(url, json=input)
    assert res.status_code == 400
    q = Activity.query.all()
    assert len(q) == 17
    q = ActivityHistory.query.all()
    assert len(q) == 3
    q = ActivityAction.query.all()
    assert len(q) == 14

    url = url_for('weko_workflow.init_activity')
    input = {'workflow_id': None, 'flow_id': flow_def_id}
    res = client.post(url, json=input)
    assert res.status_code == 400
    q = Activity.query.all()
    assert len(q) == 17
    q = ActivityHistory.query.all()
    assert len(q) == 3
    q = ActivityAction.query.all()
    assert len(q) == 14

    url = url_for('weko_workflow.init_activity')
    input = {'workflow_id': workflow_id, 'flow_id': None}
    res = client.post(url, json=input)
    assert res.status_code == 400
    q = Activity.query.all()
    assert len(q) == 17
    q = ActivityHistory.query.all()
    assert len(q) == 3
    q = ActivityAction.query.all()
    assert len(q) == 14

    url = url_for('weko_workflow.init_activity', community='comm02')
    input = {'workflow_id': workflow_id, 'flow_id': flow_def_id, 'itemtype_id': item_type_id}
    res = client.post(url, json=input)
    assert res.status_code == status_code
    assert json.loads(res.data.decode('utf-8'))['data']['redirect'].endswith('00003')
    q = Activity.query.all()
    assert len(q) == 18
    q = ActivityHistory.query.all()
    assert len(q) == 4
    q = ActivityAction.query.all()
    assert len(q) == 21

    app.config['WEKO_WORKFLOW_ENABLE_SHOWING_TERM_OF_USE'] = True
    app.config['WEKO_ITEMS_UI_SHOW_TERM_AND_CONDITION'] = ['テストアイテムタイプ']
    url = url_for('weko_workflow.init_activity')
    input = {
        'workflow_id': workflow_id,
        'flow_id': flow_def_id,
        'unknown':'unknown',
        'itemtype_id': item_type_id,
        'extra_info': {'test': 'test'},
        'related_title': 'aaa',
        'activity_login_user': 2,
        'activity_update_user': 3
    }
    res = client.post(url, json=input)
    assert res.status_code == status_code
    assert json.loads(res.data.decode('utf-8'))['data']['redirect'].endswith('00004')
    q = Activity.query.all()
    assert len(q) == 19
    q = Activity.query.filter(Activity.activity_id.like('%-00004')).first()
    assert q.extra_info == {'test': 'test', 'related_title': 'aaa'}
    assert q.activity_login_user == 2
    assert q.activity_update_user == 3
    assert q.activity_confirm_term_of_use == False
    q = ActivityHistory.query.all()
    assert len(q) == 5
    q = ActivityAction.query.all()
    assert len(q) == 22

    url = url_for('weko_workflow.init_activity')
    input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}
    with patch('weko_workflow.views.db.session.commit', side_effect=SQLAlchemyError("test_sql_error")):
        res = client.post(url, json=input)
        assert res.status_code == 500
    q = Activity.query.all()
    assert len(q) == 19
    q = ActivityHistory.query.all()
    assert len(q) == 5
    q = ActivityAction.query.all()
    assert len(q) == 28

    #for rtn is None
    input = {'workflow_id': workflow_id, 'flow_id': flow_def_id}
    with patch("weko_workflow.views.WorkActivity.init_activity", return_value=None):
        res = client.post(url, json=input)
        assert res.status_code == 500


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_init_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_init_activity(client, users, users_index, status_code, db_register, mocker):
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.init_activity')
    mocker.patch("weko_workflow.views.is_terms_of_use_only",return_value=False)
    workflow_id = db_register['workflow'].id
    flow_define_id = db_register['flow_define'].id

    #for community
    input = {'workflow_id': str(workflow_id), 'flow_id': str(flow_define_id)}
    url_comm=url_for('weko_workflow.init_activity', community = 1)
    res = client.post(url_comm, json=input)
    assert res.status_code == 200

    # #for request_mail
    # input = {'workflow_id':workflow_id, 'flow_id': flow_define_id
    #                 ,'extra_info':{'file_name' : 'test_file' , "record_id" : "1"}}
    # with patch("weko_workflow.views.RequestMailList.get_mail_list_by_item_id", return_value = [{"email":"contributor@test.org","author_id":""}]):
    #     res = client.post(url, json=input)
    #     assert res.status_code == 200

    with patch("weko_workflow.views.GetCommunity.get_community_by_id", return_value = Community(id=1)):
        res = client.post(url_comm, json=input)
        assert res.status_code == 200

    #for rtn is None
    input = {'workflow_id': str(workflow_id), 'flow_id': str(flow_define_id)}
    with patch("weko_workflow.views.WorkActivity.init_activity", return_value=None):
        res = client.post(url, json=input)
        assert res.status_code == 500

    #for Exception
    # input = {'workflow_id':workflow_id, 'flow_id': flow_define_id, 'extra_info':{'file_name' : 'test_file' , "record_id" : "1"}}
    # mocker.patch("weko_workflow.views.PersistentIdentifier.get", side_effect = PIDDoesNotExistError("depid", 1)) 
    # res = client.post(url, json=input)
    # assert res.status_code == 500

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_init_activity_is_terms_of_use_only -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_init_activity_is_terms_of_use_only(app, client,db_register,users):
    login(client=client, email=users[0]['email'])
    url = url_for('weko_workflow.init_activity')
    # 94
    with patch("weko_workflow.views.is_terms_of_use_only",return_value=True):
        # with patch("weko_workflow.views._generate_download_url",return_value='record/1/files/test_file'):
            input = {'workflow_id': db_register['workflow'].id, 'flow_id': db_register['flow_define'].id, 'unknown':'unknown'
                    ,'extra_info':{'file_name' : 'test_file' , "record_id" : "1"}}
            res = client.post(url, json=input)
            assert res.status_code == 200
            data = json.loads(res.data)
            assert data['code'] == 1
            assert data['msg'] == 'success'
            assert data['data']['is_download'] == True
            assert data['data']['redirect'] == '/record/1/files/test_file'

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_list_activity_acl_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_list_activity_acl_nologin(client, db, mocker):
    class MockActivity:
        def __init__(self):
            self.email = 'test@test.org'
            self.flows_name = 'test_flow'
            self.action_name = 'test_action'
            self.role_name = 'test_role'
            self.activity_status = 'M'
            self.StatusDesc = 'Doing'
    url = url_for('weko_workflow.list_activity')
    activity = MockActivity()
    mock_condition = mocker.patch('weko_workflow.views.filter_all_condition', return_value={'con1': 'val1'})
    mock_activity = mocker.patch('weko_workflow.views.WorkActivity.get_activity_list', return_value=([activity], 1, 1, 1, 'pagesall', 1))
    mock_layout = mocker.patch('weko_theme.utils.get_design_layout', return_value=(None, True))
    mock_render = mocker.patch('weko_workflow.views.render_template', return_value=jsonify({}))
    res = client.get(url)
    assert res.status_code == 302
    mock_condition.assert_not_called()
    mock_activity.assert_not_called()
    mock_layout.assert_not_called()
    mock_render.assert_not_called()

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_list_activity_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_list_activity_acl(client, users, mocker, users_index, status_code):
    class MockActivity:
        def __init__(self):
            self.email = 'test@test.org'
            self.flows_name = 'test_flow'
            self.action_name = 'test_action'
            self.role_name = 'test_role'
            self.activity_status = 'M'
            self.StatusDesc = 'Doing'
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.list_activity')
    activity = MockActivity()
    mock_condition = mocker.patch('weko_workflow.views.filter_all_condition', return_value={'con1': 'val1'})
    mock_activity = mocker.patch('weko_workflow.views.WorkActivity.get_activity_list', return_value=([activity], 1, 1, 1, 'pagesall', 1))
    mock_layout = mocker.patch('weko_theme.utils.get_design_layout', return_value=(None, True))
    mock_render = mocker.patch('weko_workflow.views.render_template', return_value=jsonify({}))
    res = client.get(url)
    assert res.status_code == status_code
    mock_condition.assert_called_with({})
    mock_activity.assert_called_with(conditions={'con1': 'val1'})
    mock_layout.assert_called_with('Root Index')
    mock_render.assert_called_with(
        'weko_workflow/activity_list.html',
        page=None,
        pages=1,
        name_param='pagesall',
        size=1,
        tab='todo',
        maxpage=1,
        render_widgets=True,
        activities=[activity],
    )

# def init_activity_guest():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_init_activity_guest_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_init_activity_guest_nologin(client,db_register2, mocker):
    """Test init activity for guest user."""
    url = url_for('weko_workflow.init_activity_guest')
    input = {'guest_mail': 'test@guest.com', 'workflow_id': 1, 'flow_id': 1,
            'item_type_id': 1, 'record_id': '1', 'guest_item_title': 'test',
            'file_name': 'test_file'}
    with patch("weko_workflow.views.is_terms_of_use_only",return_value=False):
        with patch('weko_workflow.views.init_activity_for_guest_user', return_value=(WorkActivity(), 'url')):
            with patch('weko_workflow.views.db.session.commit'):
                with patch('weko_workflow.views.send_usage_application_mail_for_guest_user', return_value=True):
                    res = client.post(url, json=input)
                    assert res.status_code == 200
                    data = json.loads(res.data)
                    assert data['msg'] == 'Email is sent successfully.'
            
            with patch('weko_workflow.views.db.session.commit', side_effect=SQLAlchemyError("test_sql_error")):
                mock_rollback = mocker.patch('weko_workflow.views.db.session.rollback')
                res = client.post(url, json=input)
                assert res.status_code == 200
                data = json.loads(res.data)
                assert data['msg'] == 'Cannot send mail'
                mock_rollback.assert_called()
            
            with patch('weko_workflow.views.db.session.commit', side_effect=Exception("test_sql_error")):
                mock_rollback = mocker.patch('weko_workflow.views.db.session.rollback')
                res = client.post(url, json=input)
                assert res.status_code == 200
                data = json.loads(res.data)
                assert data['msg'] == 'Cannot send mail'
                mock_rollback.assert_called()

    # 95
    with patch("weko_workflow.views.is_terms_of_use_only",return_value=True):
        with patch('weko_workflow.views.send_usage_application_mail_for_guest_user', return_value=True):
        # with patch("weko_workflow.views._generate_download_url",return_value='record/1/files/test_file'):
            res = client.post(url, json=input)
            assert res.status_code == 200
            data = json.loads(res.data)
            assert data['code'] == 1
            assert data['msg'] == 'success'
            assert data['data']['is_download'] == True
            assert data['data']['redirect'] == '/record/1/files/test_file'
    
    input = {'password_for_download': 'password', 'workflow_id': ''}
    with patch('weko_workflow.views.hash_password', return_value='hashed_password'):
        with patch("weko_workflow.views.is_terms_of_use_only",return_value=False):
            res = client.post(url, json=input)
            assert res.status_code == 200
            data = json.loads(res.data)
            assert data['msg'] == 'Cannot send mail'

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_init_activity_guest_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_init_activity_guest_users(client, users, db_register, db_guestactivity, users_index, status_code):
    current_app.config.setdefault('THEME_INSTITUTION_NAME', {'ja':"組織", 'en':"INSTITUTION"})
    """Test init activity for guest user."""
    current_app.config.setdefault('THEME_INSTITUTION_NAME', {'ja':"組織", 'en':"INSTITUTION"})
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.init_activity_guest')
    input = {'guest_mail': 'test@guest.com', 'workflow_id': 1, 'flow_id': 1,
             'item_type_id': 1, 'record_id': '1', 'guest_item_title': 'test',
             'file_name': 'test_file'}

    with patch('weko_workflow.views.send_usage_application_mail_for_guest_user', return_value=False):
        res = client.post(url, json=input)
        assert res.status_code == status_code

# def display_guest_activity():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_guest_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_display_guest_activity(client, users, db_register_full_action, db_guestactivity):
    """Test display_guest_activity func."""
    mock_render_template = MagicMock(return_value=jsonify({}))
    url = url_for('weko_workflow.display_guest_activity', file_name="Test_file", token='123')
    with patch("weko_workflow.views.render_template", mock_render_template):
        res = client.get(url)
        assert res.status_code == 200
        mock_args, mock_kwargs = mock_render_template.call_args
        assert mock_args[0] == "weko_theme/error.html"
        assert mock_kwargs["error"] == "Token is invalid"

    url = url_for('weko_workflow.display_guest_activity', file_name="Test_file", token=db_guestactivity[0])
    with patch("weko_workflow.views.render_template", mock_render_template):
        res = client.get(url)
        assert res.status_code == 200
        mock_args, mock_kwargs = mock_render_template.call_args
        assert mock_args[0] == "weko_theme/error.html"
        assert mock_kwargs["error"] == "The specified link has expired."

    url = url_for('weko_workflow.display_guest_activity', file_name="Test_file", token=db_guestactivity[1])
    with patch("flask.templating._render", return_value=""):
        res = client.get(url)
        assert res.status_code == 200

    url = url_for("weko_workflow.display_guest_activity",file_name="test.txt")
    mock_render = MagicMock(return_value=jsonify({}))
    with patch('weko_workflow.views.render_guest_workflow',mock_render):
        res = client.get(url)
        mock_render.assert_called()

# def render_guest_workflow():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_guest_activity_item_application -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_display_guest_activity_item_application(db_register, client):
    url = url_for("weko_workflow.display_guest_activity_item_application",record_id=1)
    mock_render = MagicMock(return_value=jsonify({}))
    with patch('weko_workflow.views.render_guest_workflow',mock_render):
        res = client.get(url)
        mock_render.assert_called()

# def display_guest_activity_item_application():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_render_guest_workflow -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_render_guest_workflow(client, users, db_register, db_guestactivity):
    url = "/activity/guest-user/file_name?token=token"
    mock_render_template = MagicMock(return_value=jsonify({}))
    client.get(url)
    return_validate_guest_activity_token = (False, None, None)
    with patch('weko_workflow.views.GuestActivity.get_expired_activities',return_value=""):
        with patch('weko_workflow.views.validate_guest_activity_token',return_value=return_validate_guest_activity_token):
            with patch('weko_workflow.views.render_template', mock_render_template):
                res = render_guest_workflow("file_name")
                mock_render_template.assert_called()

    return_validate_guest_activity_token = (True, None, None)
    with patch('weko_workflow.views.GuestActivity.get_expired_activities',return_value=""):
        with patch('weko_workflow.views.validate_guest_activity_token',return_value=return_validate_guest_activity_token):
            with patch('weko_workflow.views.validate_guest_activity_expired', return_value ="error"):
                with patch('weko_workflow.views.render_template', mock_render_template):
                    res = render_guest_workflow("file_name")
                    mock_render_template.assert_called()

    return_validate_guest_activity_token = (True, None, None)
    with patch('weko_workflow.views.GuestActivity.get_expired_activities',return_value=""):
        with patch('weko_workflow.views.validate_guest_activity_token',return_value=return_validate_guest_activity_token):
            with patch('weko_workflow.views.validate_guest_activity_expired', return_value =""):
                with patch('weko_workflow.views.prepare_data_for_guest_activity',return_value={}):
                    with patch('weko_workflow.views.get_usage_data',return_value={}):
                        with patch('weko_workflow.views.get_main_record_detail',return_value={"record":{"is_guest":True}}):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = render_guest_workflow("file_name")
                                mock_render_template.assert_called()

    return_validate_guest_activity_token = (True, None, None)
    with patch('weko_workflow.views.GuestActivity.get_expired_activities',return_value=""):
        with patch('weko_workflow.views.validate_guest_activity_token',return_value=return_validate_guest_activity_token):
            with patch('weko_workflow.views.validate_guest_activity_expired', return_value =""):
                with patch('weko_workflow.views.prepare_data_for_guest_activity',return_value={}):
                    with patch('weko_workflow.views.get_usage_data',return_value={}):
                        with patch('weko_workflow.views.get_main_record_detail',return_value={}):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = render_guest_workflow("file_name")
                                mock_render_template.assert_called()


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_find_doi_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_find_doi_nologin(client,db_register2):
    """Test of find doi."""
    url = url_for('weko_workflow.find_doi')
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_find_doi_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_find_doi_users(client, users, users_index, status_code):
    """Test of find doi."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.find_doi')
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == status_code


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_save_activity_acl_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_save_activity_acl_nologin(client):
    """Test of save activity."""
    url = url_for('weko_workflow.save_activity')
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_ids":[]}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/save_activity_data",_external=True)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_save_activity_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_save_activity_acl_users(client, users, users_index, status_code):
    """Test of save activity."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.save_activity')
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_ids":[]}
    with patch('weko_workflow.views.save_activity_data'):
        res = client.post(url, json=input)
        assert res.status_code != 302

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_save_activity_acl_guestlogin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_save_activity_acl_guestlogin(guest):
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_ids":[]}
    url = url_for('weko_workflow.save_activity')

    res = guest.post(url, json=input)
    assert res.status_code != 302


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_save_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_save_activity(client, users, db_register_full_action, users_index, status_code):
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.save_activity')

    input = {"activity_id":"A-20220921-00001","title":"test"}
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code== 400
    assert data["code"] == -1
    assert data["msg"] == "{'shared_user_ids': ['Missing data for required field.']}"

    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_ids":[]}
    with patch('weko_workflow.views.save_activity_data'):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code==status_code
        assert data["success"] == True
        assert data["msg"] == ""

    with patch('weko_workflow.views.save_activity_data', side_effect=Exception("test error")):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code==status_code
        assert data["success"] == False
        assert data["msg"] == "test error"

#guestuserでの機能テスト
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_save_activity_guestlogin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_save_activity_guestlogin(guest):
    url = url_for('weko_workflow.save_activity')

    input = {"activity_id":"A-20220921-00001","title":"test"}
    res = guest.post(url, json=input)
    data = response_data(res)
    assert res.status_code== 400
    assert data["code"] == -1
    assert data["msg"] == "{'shared_user_ids': ['Missing data for required field.']}"

    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_ids":[]}
    with patch('weko_workflow.views.save_activity_data'):
        res = guest.post(url, json=input)
        data = response_data(res)
        assert res.status_code==200
        assert data["success"] == True
        assert data["msg"] == ""

    with patch('weko_workflow.views.save_activity_data', side_effect=Exception("test error")):
        res = guest.post(url, json=input)
        data = response_data(res)
        assert res.status_code==200
        assert data["success"] == False
        assert data["msg"] == "test error"


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_save_feedback_maillist_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_save_feedback_maillist_users(client, users, db_register_full_action, users_index, status_code):
    """Test of save feedback maillist."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.save_feedback_maillist',
                  activity_id='1', action_id=1)
    input = {}

    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }

    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        assert res.status_code == status_code


@pytest.mark.parametrize('users_index, status_code', [
    (1, 200)
])
#.tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_save_request_maillist -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_save_request_maillist(client,users, db_register, users_index, status_code):
    login(client=client, email=users[users_index]['email'])
    input = {
        'request_maillst':[],
        'is_display_request_button':True
    }

    url = url_for('weko_workflow.save_request_maillist',activity_id='1', action_id=3)
    res = client.post(url, json=input)
    assert res.status_code == 200

    input = "text"
    url = url_for('weko_workflow.save_request_maillist',activity_id='1', action_id=3)
    res = client.post(url, json=input)
    data = response_data(res)
    assert data["code"] == -1

    input = {
        'request_maillst':[],
        'is_display_request_button':True
    }
    with patch('weko_workflow.api.WorkActivity.create_or_update_activity_request_mail',side_effect=Exception()):
        url = url_for('weko_workflow.save_request_maillist',activity_id='1', action_id=3)
        res = client.post(url, json=input)
        data = response_data(res)
    assert data["code"] == -1

    # Abnormal case: Content-Type is not 'application/json'.
    url = url_for('weko_workflow.save_request_maillist',activity_id='1', action_id=3)
    res = client.post(url, json=input, headers={"Content-Type":"text/plain"})
    data = response_data(res)
    assert data["code"] == -1
    assert data["msg"] == "Header Error"

@pytest.mark.parametrize('users_index, status_code', [
    (1, 200)
])
#.tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_save_item_application -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_save_item_application(client,users, db_register, users_index, status_code):
    login(client=client, email=users[users_index]['email'])
    input_with_description = {
        'workflow_for_item_application':"1",
        'terms_without_contents':"term_free",
        'is_display_item_application_button':True,
        'terms_description_without_contents':"利用規約自由入力"
    }
    input_without_description = {
        'workflow_for_item_application':"1",
        'terms_without_contents':"111111111",
        'is_display_item_application_button':True
    }

    # 正常系　terms_decriptionつき
    url = url_for('weko_workflow.save_item_application',activity_id='1', action_id=3)
    res = client.post(url, json=input_with_description)
    item_application = WorkActivity().get_activity_item_application('1')
    assert res.status_code == 200
    assert item_application.item_application.get("termsDescription")

    # 正常系　terms_descriptionなし
    res = client.post(url, json=input_without_description)
    item_application = WorkActivity().get_activity_item_application('1')
    assert res.status_code == 200
    assert not item_application.item_application.get("termsDescription")

    # 異常系　エラー
    with patch("weko_workflow.api.WorkActivity.create_or_update_activity_item_application", side_effect=Exception()):
        res = client.post(url, json=input_without_description)  
        data = response_data(res)
        assert data["code"]==-1
        assert data["msg"]=="Error"

    #異常系　'Content-Type'が'application/json'でない。
    # カバレッジが通せない。postメソッドの引数にheadersを設定しても無理だった。
    res = client.post(url, json = input_without_description, headers={"Content-Type":"text/plain"})
    data = response_data(res)
    assert data["code"]==-1
    assert data["msg"]=="Header Error"

#.tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_guest_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_display_guest_activity(client,mocker, db):
    render_mock = mocker.patch("weko_workflow.views.render_guest_workflow")
    display_guest_activity("test.txt")
    render_mock.assert_called()

#.tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_guest_activity_item_application -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_display_guest_activity_item_application(client,mocker, db):
    render_mock = mocker.patch("weko_workflow.views.render_guest_workflow")
    display_guest_activity_item_application("test.txt")
    render_mock.assert_called()

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_previous_action_acl_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_previous_action_acl_nologin(client,db_register2):
    """Test of previous action."""
    url = url_for('weko_workflow.previous_action', activity_id='1',
                  action_id=1, req=1)
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == "http://test_server.localdomain/login/?next=%2Fworkflow%2Factivity%2Faction%2F1%2F1%2FrejectOrReturn%2F1"


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_previous_action_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code, is_admin', [
    (0, 403, False),
    (1, 403, True),
    (2, 403, True),
    (3, 403, True),
    (4, 403, False),
    (5, 403, False),
    (6, 403, True),
])
def test_previous_action_acl_users(client, users, db_register_full_action, users_index, status_code, is_admin):
    current_app.config.setdefault('THEME_INSTITUTION_NAME', {'ja':"組織", 'en':"INSTITUTION"})
    """Test of previous action."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.previous_action',
                  activity_id='1',
                  action_id=1, req=1)
    input = {}

    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }
    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        assert res.status_code != status_code

    action_users = {
        'allow': [],
        'deny': [users[users_index]["id"]]
    }
    url = url_for('weko_workflow.previous_action',
                activity_id='2',
                action_id=1, req=1)

    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code != status_code
        if is_admin:
            assert data["code"] != 403
        else:
            assert data["code"] == 403

    action_users = {
        'allow': [users[users_index]["id"]],
        'deny': []
    }
    url = url_for('weko_workflow.previous_action',
                activity_id='3',
                action_id=1, req=1)

    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code != status_code
        assert data["code"] != 403


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_previous_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_previous_action(client, users, db_register_full_action, users_index, status_code):
    current_app.config.setdefault('THEME_INSTITUTION_NAME', {'ja':"組織", 'en':"INSTITUTION"})

    login(client=client, email=users[users_index]['email'])

    url = url_for("weko_workflow.previous_action",
                  activity_id="2",action_id=1,req=1)
    # argument error
    with patch("weko_workflow.views.type_null_check",return_value=False):
        res = client.post(url,json={})
        data = response_data(res)
        assert res.status_code==500
        assert data["code"] == -1
        assert data["msg"] == "argument error"

    # request_body error
    with patch("weko_workflow.views.ActionSchema",side_effect=ValidationError("test error")):
        res = client.post(url, json={})
        data = response_data(res)
        assert res.status_code==500
        assert data["code"] == -1
        assert data["msg"] == "test error"

    input = {"action_version":"1.0.0", "commond":"this is test comment."}

    # req=1
    url = url_for('weko_workflow.previous_action',
                  activity_id='2', action_id=1, req=1)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code==status_code
    assert data["code"] == 0
    assert data["msg"] == "success"

    # req=0
    url = url_for('weko_workflow.previous_action',
                  activity_id='2', action_id=3, req=0)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code==status_code
    assert data["code"] == 0
    assert data["msg"] == "success"

    # req=-1
    res = previous_action(activity_id="2", action_id=1, req=-1)
    data = response_data(res[0])
    assert data["code"] == 0
    assert data["msg"] == "success"


    # not pre_action
    url = url_for('weko_workflow.previous_action',
                  activity_id='2', action_id=3, req=0)
    with patch("weko_workflow.views.Flow.get_previous_flow_action", return_value=None):
        res = client.post(url, json=input)
        data = response_data(res)
        assert data["code"] == 0
        assert data["msg"] == "success"

    # not exist activity_detail
    url = url_for('weko_workflow.previous_action',
                  activity_id='1', action_id=1, req=1)
    with patch("weko_workflow.views.WorkActivity.get_activity_by_id",side_effect=[db_register_full_action["activities"][0],None]):
        if users_index in [1, 2, 6]:
            res = client.post(url, json=input)
            data = response_data(res)
            assert res.status_code==500
            assert data["code"] == -1
            assert data["msg"] == "can not get activity detail"
        else:
            with pytest.raises(Exception) as e:
                res = client.post(url, json=input)
                data = response_data(res)
                assert res.status_code==500
                assert data["code"] == -1
                assert data["msg"] == "can not get activity detail"

    # not create activity history
    url = url_for('weko_workflow.previous_action',
                  activity_id='2', action_id=3, req=0)
    with patch("weko_workflow.views.WorkActivityHistory.create_activity_history", return_value=None):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "error"

    # not create activity history
    url = url_for('weko_workflow.previous_action',
                  activity_id='2', action_id=3, req=0)
    with patch("weko_workflow.views.Flow.get_flow_action_detail", return_value=None):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "can not get flow action detail"

    # code=-2
    with patch("weko_workflow.views.WorkActivity.upt_activity_action_status", return_value=False):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -2
        assert data["msg"] == ""

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_next_action_acl_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_next_action_acl_nologin(client, db_register_fullaction):
    """Test of next action."""
    url = url_for('weko_workflow.next_action', activity_id='1',
                  action_id=1)
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == "http://test_server.localdomain/login/?next=%2Fworkflow%2Factivity%2Faction%2F1%2F1"

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_next_action_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code, is_admin', [
    (0, 200, False),
    (1, 200, True),
    (2, 200, True),
    (3, 200, True),
    (4, 200, False),
    (5, 200, False),
    (6, 200, True),
])
def test_next_action_acl_users(client, users, db_register_fullaction, users_index, status_code, is_admin):
    """Test of next action."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.next_action',
                  activity_id='1',
                  action_id=1)
    input = {}

    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }

    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        assert res.status_code == status_code

    url = url_for('weko_workflow.next_action',
                  activity_id='2',
                  action_id=1)
    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        with patch('weko_workflow.views.get_schema_action', return_value=None):
            res = client.post(url, json=input)
            data = response_data(res)
            assert res.status_code == 500
            assert data["msg"] == 'can not get schema by action_id'

    action_users = {
        'allow': [],
        'deny': [users[users_index]["id"]]
    }
    url = url_for('weko_workflow.next_action',
                  activity_id='2',
                  action_id=1)
    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        data = response_data(res)
        if is_admin:
            assert res.status_code == status_code
            assert data["msg"] == 'success'
        else:
            assert res.status_code == status_code
            assert data["msg"] == 'Authorization required'

    action_users = {
        'allow': [users[users_index]["id"]],
        'deny': []
    }
    url = url_for('weko_workflow.next_action',
                  activity_id='3',
                  action_id=1)
    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == status_code
        assert data["msg"] == 'success'

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_next_action_acl_guestlogin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_next_action_acl_guestlogin(guest, client, db_register_fullaction):
    input = {'action_version': 1, 'commond': 1}
    url = url_for('weko_workflow.next_action',
                  activity_id="1", action_id=1)
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }
    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = guest.post(url, json=input)
        assert res.status_code != 403

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_next_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_next_action(app, client, db, users, db_register_fullaction, db_records, users_index, status_code, mocker,logging_client):
    current_app.config.update(
        WEKO_NOTIFICATIONS=False
        )
    def update_activity_order(activity_id, action_id, action_order, item_id=None, extra_info={}, temp_data='{ }'):
        with db.session.begin_nested():
            activity=Activity.query.filter_by(activity_id=activity_id).one_or_none()
            activity.activity_status=ActionStatusPolicy.ACTION_BEGIN
            activity.action_id=action_id
            activity.action_order=action_order
            activity.action_status=None
            activity.extra_info=extra_info
            activity.temp_data = temp_data
            if item_id:
                activity.item_id=item_id
            db.session.merge(activity)
            pid = PersistentIdentifier.query.filter(
                PersistentIdentifier.object_uuid==activity.item_id,
                PersistentIdentifier.object_type=='rec',
                PersistentIdentifier.pid_type=='recid').one_or_none()
            if pid:
                pid.status=PIDStatus.NEW
                db.session.merge(pid)
        db.session.commit()

    login(client=client, email=users[users_index]["email"])
    with client.session_transaction() as session:
        session['itemlogin_id'] = "test id"
        session['itemlogin_activity'] = "test activity"
        session['itemlogin_item'] = "test item"
        session['itemlogin_steps'] = "test steps"
        session['itemlogin_action_id'] = "test action_id"
        session['itemlogin_cur_step'] = "test cur_step"
        session['itemlogin_record'] = "test approval_record"
        session['itemlogin_histories'] = "test histories"
        session['itemlogin_res_check'] = "test res_check"
        session['itemlogin_pid'] = "test recid"
        session['itemlogin_community_id'] = "test community_id"

    mocker.patch("weko_workflow.views.IdentifierHandle.remove_idt_registration_metadata",return_value=None)
    mocker.patch("weko_workflow.views.IdentifierHandle.update_idt_registration_metadata",return_value=None)
    mocker.patch("weko_workflow.views.FeedbackMailList.update_by_list_item_id")
    mocker.patch("weko_workflow.views.FeedbackMailList.delete_by_list_item_id")
    mock_signal = mocker.patch("weko_workflow.views.item_created.send")
    mocker.patch("weko_workflow.views.cris_researchmap_linkage_request.send")
    # new_item = uuid.uuid4()
    # mocker.patch("weko_workflow.views.handle_finish_workflow",return_value=new_item)
    mocker.patch("weko_deposit.api.WekoDeposit.publish",return_value=True)
    mocker.patch("weko_deposit.api.WekoDeposit.merge_data_to_record_without_version",return_value=db_records[0][6])
    mocker.patch("weko_deposit.api.WekoDeposit.commit",return_value=True)
    mocker.patch("weko_workflow.api.UpdateItem.publish",return_value=True)
    mocker.patch("invenio_oaiserver.tasks.update_records_sets.delay",return_value=True)

    flow_action_5 = db_register_fullaction["flow_actions"][5].id
    item_id1 = db_register_fullaction["activities"][0].item_id
    item_id2 = db_register_fullaction["activities"][1].item_id
    item_id3 = db_register_fullaction["activities"][2].item_id
    item_id4 = db_register_fullaction["activities"][3].item_id
    item_id5 = db_register_fullaction["activities"][4].item_id
    item_id6 = db_register_fullaction["activities"][5].item_id
    item_id7 = db_register_fullaction["activities"][6].item_id
    item_id8 = db_register_fullaction["activities"][7].item_id
    item_id9 = db_register_fullaction["activities"][8].item_id
    item_id10 = db_register_fullaction["activities"][9].item_id
    item_id11 = db_register_fullaction["activities"][10].item_id
    activity1 = db_register_fullaction["activities"][0]

    permissions = list()
    permissions.append(FilePermission(1,"1.1","test_file","3",None,-1))
    db.session.add_all(permissions)
    db.session.commit()

    # argument error
    with patch("weko_workflow.views.type_null_check",return_value=False):
        input = {}
        url = url_for("weko_workflow.next_action",
                      activity_id="1", action_id=1)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "argument error"
    # can not get activity_detail
    update_activity_order("1",1,1,item_id1)
    url = url_for("weko_workflow.next_action",
            activity_id="1", action_id=1)
    activity = copy.deepcopy(db_register_fullaction["activities"][0])
    with patch("weko_workflow.views.WorkActivity.get_activity_by_id",side_effect=[activity,None]):
        if users_index in [1, 2, 6]:
            res = client.post(url, json=input)
            data = response_data(res)
            assert res.status_code==500
            assert data["code"] == -1
            assert data["msg"] == "can not get activity detail"
        else:
            with pytest.raises(Exception) as e:
                res = client.post(url, json=input)
                data = response_data(res)
                assert res.status_code == 500
                assert data["code"] == -1
                assert data["msg"] == "can not get activity detail"

    # cannot get schema
    update_activity_order("1",1,1,item_id1)
    url = url_for("weko_workflow.next_action",
            activity_id="1", action_id=1)
    with patch("weko_workflow.views.get_schema_action",return_value=None):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -2
        assert data["msg"] == "can not get schema by action_id"

    # request_body error
    url = url_for("weko_workflow.next_action",
            activity_id="2", action_id=7)
    update_activity_order("2",7,5,item_id2)
    input = {
        "temporary_save":1,
        "identifier_grant":"1",
        "identifier_grant_jalc_doi_suffix":"",
        "identifier_grant_jalc_cr_doi_suffix":"",
        "identifier_grant_jalc_dc_doi_suffix":"",
    }
    res = client.post(url,json=input)
    data = response_data(res)
    assert res.status_code==500
    assert data["code"] == -1
    assert data["msg"] == "{'identifier_grant_ndl_jalc_doi_suffix': ['Missing data for required field.']}"

    # action: start
    input = {}
    url = url_for("weko_workflow.next_action",
                  activity_id="1", action_id=1)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"

    # action: end
    update_activity_order("2",2,7,item_id2)
    q = Activity.query.filter(Activity.activity_id=="2").first()
    assert q.activity_status == ActionStatusPolicy.ACTION_BEGIN
    assert q.action_id == 2
    assert q.action_status == None
    assert q.action_order == 7
    q = ActivityHistory.query.filter(ActivityHistory.activity_id=="2").all()
    assert len(q) == 0
    url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=2)
    with patch('weko_workflow.views.db.session.commit', side_effect=Exception("")):
        res = client.post(url, json=input)
        data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    q = Activity.query.filter(Activity.activity_id=="2").first()
    assert q.activity_status == ActionStatusPolicy.ACTION_BEGIN
    assert q.action_id == 2
    assert q.action_status == None
    assert q.action_order == 7
    q = ActivityHistory.query.filter(ActivityHistory.activity_id=="2").all()
    assert len(q) == 0
    url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=2)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    q = Activity.query.filter(Activity.activity_id=="2").first()
    assert q.activity_status == ActionStatusPolicy.ACTION_DONE
    assert q.action_id == 2
    assert q.action_status == 'F'
    assert q.action_order == 7
    q = ActivityHistory.query.filter(ActivityHistory.activity_id=="2").all()
    assert len(q) == 1

    # ActivityHistory create error
    url = url_for("weko_workflow.next_action",
                  activity_id="1", action_id=3)
    update_activity_order("1",3,2,item_id1)
    q = ActivityHistory.query.filter(ActivityHistory.activity_id=="1").all()
    assert len(q) == 0
    with patch('weko_workflow.views.db.session.commit', side_effect=Exception("")):
        res = client.post(url, json=input)
        data = response_data(res)
    assert res.status_code == 500
    assert data["code"] == -1
    assert data["msg"] == "can not get pid_without_ver"
    q = ActivityHistory.query.filter(ActivityHistory.activity_id=="1").all()
    assert len(q) == 0

    # action: item register
    ## not exist pid_without_ver
    url = url_for("weko_workflow.next_action",
                  activity_id="1", action_id=3)
    update_activity_order("1",3,2,item_id1)
    q = Activity.query.filter(Activity.activity_id=="1").first()
    assert q.activity_status == ActionStatusPolicy.ACTION_BEGIN
    assert q.action_id == 3
    assert q.action_status == None
    assert q.action_order == 2
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == 500
    assert data["code"] == -1
    assert data["msg"] == "can not get pid_without_ver"
    q = ActivityHistory.query.filter(ActivityHistory.activity_id=="1").all()
    assert len(q) == 0
    q = Activity.query.filter(Activity.activity_id=="1").first()
    assert q.activity_status == ActionStatusPolicy.ACTION_BEGIN
    assert q.action_id == 3
    assert q.action_status == None
    assert q.action_order == 2

    ## not exist record
    with patch("weko_workflow.views.WekoRecord.get_record_by_pid",return_value=None):
        update_activity_order("2",3,2,item_id2)
        q = ActivityHistory.query.filter(ActivityHistory.activity_id=="2").all()
        assert len(q) == 1
        input = {"temporary_save":1}
        url = url_for("weko_workflow.next_action",
                      activity_id="2", action_id=3)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "can not get record"
        q = ActivityHistory.query.filter(ActivityHistory.activity_id=="2").all()
        assert len(q) == 1

    with patch("weko_workflow.views.PersistentIdentifier.get_by_object",side_effect=PIDDoesNotExistError("recid","wrong value")):
        update_activity_order("2",3,2,item_id2)
        input = {"temporary_save":1}
        url = url_for("weko_workflow.next_action",
                      activity_id="2", action_id=3)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "can not get PersistentIdentifier"

    with patch("weko_workflow.views.WekoDeposit.get_record", return_value=None):
        update_activity_order("2",3,2,item_id2)
        input = {"temporary_save":1}
        url = url_for("weko_workflow.next_action",
                      activity_id="2", action_id=3)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "can not get pid_without_ver"

    ## template_save = 1
    ### not in journal
    # fail
    update_activity_order("2",3,2,item_id2)
    q = Activity.query.filter(Activity.activity_id=="2").first()
    assert q.activity_status == ActionStatusPolicy.ACTION_BEGIN
    assert q.action_id == 3
    assert q.action_status == None
    assert q.action_order == 2
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==3).first()
    assert q.action_comment == None
    input = {"temporary_save":1, "commond": "test_comment"}
    url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=3)
    with patch('weko_workflow.views.db.session.commit', side_effect=Exception("")):
        with pytest.raises(Exception) as e:
            res = client.post(url, json=input)
            data = response_data(res)
            assert res.status_code == 500
            assert data["code"] == -1
            assert data["msg"] == "error"
    q = Activity.query.filter(Activity.activity_id=="2").first()
    assert q.activity_status == ActionStatusPolicy.ACTION_BEGIN
    assert q.action_id == 3
    assert q.action_status == None
    assert q.action_order == 2
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==3).first()
    assert q.action_comment == "test_comment"

    # action: item register
    ## template_save = 1
    ### not in journal
    # success
    update_activity_order("2",3,2,item_id2)
    q = Activity.query.filter(Activity.activity_id=="2").first()
    assert q.activity_status == ActionStatusPolicy.ACTION_BEGIN
    assert q.action_id == 3
    assert q.action_status == None
    assert q.action_order == 2
    q = PersistentIdentifier.query.filter(
        PersistentIdentifier.object_uuid==item_id2,
        PersistentIdentifier.object_type=='rec',
        PersistentIdentifier.pid_type=='recid').first()
    assert q.status == PIDStatus.NEW
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==3).first()
    assert q.action_comment == "test_comment"
    input = {"temporary_save":1, "commond": "test_comment1"}
    url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=3)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    q = Activity.query.filter(Activity.activity_id=="2").first()
    assert q.activity_status == ActionStatusPolicy.ACTION_BEGIN
    assert q.action_id == 3
    assert q.action_status == None
    assert q.action_order == 2
    q = PersistentIdentifier.query.filter(
        PersistentIdentifier.object_uuid==item_id2,
        PersistentIdentifier.object_type=='rec',
        PersistentIdentifier.pid_type=='recid').first()
    assert q.status == PIDStatus.NEW
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==3).first()
    assert q.action_comment == "test_comment1"

    # action: oa policy
    ## temporary_save = 1
    ### in journal
    update_activity_order("2",6,3,item_id2)
    q = ActionJournal.query.filter(ActionJournal.activity_id=="2", ActionJournal.action_id==6).first()
    assert q == None
    input = {"temporary_save":1,
             "journal":{"issn":"test issn"}}
    url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=6)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    q = ActionJournal.query.filter(ActionJournal.activity_id=="2", ActionJournal.action_id==6).first()
    assert q.action_journal == {"issn":"test issn"}

    # action: item link
    ## temporary_save = 1
    # success
    update_activity_order("2",5,4,item_id2)
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==5).first()
    assert q.action_comment == None
    input = {
        "temporary_save":1,
        "link_data":[],
        "commond": "test_comment"
    }
    url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=5)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==5).first()
    assert q.action_comment == "test_comment"

    # action: identifier grant
    ## exist identifier_select
    ###x temporary_save = 1
    update_activity_order("2",7,5,item_id2)
    q = ActionIdentifier.query.filter(ActionIdentifier.activity_id=="2", ActionIdentifier.action_id==7).first()
    assert q.action_identifier_select == -2
    assert q.action_identifier_jalc_doi == ""
    assert q.action_identifier_jalc_cr_doi == ""
    assert q.action_identifier_jalc_dc_doi == ""
    assert q.action_identifier_ndl_jalc_doi == ""
    input = {
        "temporary_save":1,
        "identifier_grant":"1",
        "identifier_grant_jalc_doi_suffix":"123",
        "identifier_grant_jalc_cr_doi_suffix":"456",
        "identifier_grant_jalc_dc_doi_suffix":"789",
        "identifier_grant_ndl_jalc_doi_suffix":"000"
    }
    url = url_for("weko_workflow.next_action",
            activity_id="2", action_id=7)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    q = ActionIdentifier.query.filter(ActionIdentifier.activity_id=="2", ActionIdentifier.action_id==7).first()
    assert q.action_identifier_select == 1
    assert q.action_identifier_jalc_doi == "123"
    assert q.action_identifier_jalc_cr_doi == "456"
    assert q.action_identifier_jalc_dc_doi == "789"
    assert q.action_identifier_ndl_jalc_doi == "000"

    # action: item register
    ## temporary_save=0
    # success
    update_activity_order("2",3,2,item_id2)
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==3).first()
    assert q.action_status == ActionStatusPolicy.ACTION_BEGIN
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==6).first()
    assert q.action_status == ActionStatusPolicy.ACTION_BEGIN
    q = Activity.query.filter(Activity.activity_id=="2").first()
    assert q.action_id == 3
    assert q.action_status == None
    assert q.action_order == 2
    input = {"temporary_save":0}
    url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=3)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==3).first()
    assert q.action_status == ActionStatusPolicy.ACTION_DONE
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==6).first()
    assert q.action_status == ActionStatusPolicy.ACTION_DOING
    q = Activity.query.filter(Activity.activity_id=="2").first()
    assert q.action_id == 6
    assert q.action_status == ActionStatusPolicy.ACTION_DOING
    assert q.action_order == 3

    # action: oa policy
    # ## temporary_save = 0
    update_activity_order("2",6,3,item_id2)
    q = ActionJournal.query.filter(ActionJournal.activity_id=="2", ActionJournal.action_id==6).first()
    assert q.action_journal == {"issn":"test issn"}
    input = {"temporary_save":0,
             "journal":{"issn":"test issn 1"}}
    url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=6)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    q = ActionJournal.query.filter(ActionJournal.activity_id=="2", ActionJournal.action_id==6).first()
    assert q.action_journal == {"issn":"test issn 1"}

    # action: item link
    ## temporary_save = 0
    ### exist pid_without_ver, exist link_data
    update_activity_order("2",5,4,item_id2)
    q = ItemReference.query.all()
    assert q == []
    input = {
        "temporary_save":0,
        "link_data":[
            {"item_id":"1","item_title":"test item1","sele_id":"relateTo"}
        ]
    }
    url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=5)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    q = ItemReference.query.all()
    assert len(q) == 1

    # action: item link
    ####x raise except
    update_activity_order("2",5,4,item_id2)
    q = ActionJournal.query.filter(ActionJournal.activity_id=="2", ActionJournal.action_id==6).first()
    assert q.action_journal == {"issn":"test issn 1"}
    input = {
            "temporary_save":0,
            "journal":{"issn":"test issn 2"},
            "link_data":[{"item_id":"1","item_title":"test item1","sele_id":"relateTo"}]
        }
    url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=5)
    err_msg = "test update error"
    with patch("weko_workflow.views.ItemLink.update",return_value=err_msg):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == err_msg
        q = ActionJournal.query.filter(ActionJournal.activity_id=="2", ActionJournal.action_id==6).first()
        assert q.action_journal == {"issn":"test issn 1"}

    # action: identifier grant
    update_activity_order("2",7,5,item_id2)
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==7).first()
    assert q.action_status == ActionStatusPolicy.ACTION_DOING
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==5).first()
    assert q.action_status == ActionStatusPolicy.ACTION_DONE
    q = Activity.query.filter(Activity.activity_id=="2").first()
    assert q.action_id == 7
    assert q.action_status == None
    assert q.action_order == 5
    url = url_for("weko_workflow.next_action",
            activity_id="2", action_id=7)
    input = {
        "identifier_grant":"1",
        "identifier_grant_jalc_doi_suffix":"",
        "identifier_grant_jalc_cr_doi_suffix":"",
        "identifier_grant_jalc_dc_doi_suffix":"",
        "identifier_grant_ndl_jalc_doi_suffix":""
    }
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==7).first()
    assert q.action_status == ActionStatusPolicy.ACTION_RETRY
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==5).first()
    assert q.action_status == ActionStatusPolicy.ACTION_DONE
    q = Activity.query.filter(Activity.activity_id=="2").first()
    assert q.action_id == 3
    assert q.action_status == ActionStatusPolicy.ACTION_DOING
    assert q.action_order == 2.

    ### temporary_save = 0
    #### select NotGrant
    update_activity_order("2",7,5,item_id2)
    input = {
        "temporary_save":0,
        "identifier_grant":"0",
        "identifier_grant_jalc_doi_suffix":"",
        "identifier_grant_jalc_cr_doi_suffix":"",
        "identifier_grant_jalc_dc_doi_suffix":"",
        "identifier_grant_ndl_jalc_doi_suffix":""
    }
    url = url_for("weko_workflow.next_action",
            activity_id="2", action_id=7)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"

    ### temporary_save = 0
    #### select NotGrant
    update_activity_order("2",7,5,item_id2)
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==7).first()
    assert q.action_status == ActionStatusPolicy.ACTION_DONE
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==5).first()
    assert q.action_status == ActionStatusPolicy.ACTION_DONE
    q = Activity.query.filter(Activity.activity_id=="2").first()
    assert q.action_id == 7
    assert q.action_status == None
    assert q.action_order == 5
    input = {
        "temporary_save":0,
        "identifier_grant_jalc_doi_suffix":"",
        "identifier_grant_jalc_cr_doi_suffix":"",
        "identifier_grant_jalc_dc_doi_suffix":"",
        "identifier_grant_ndl_jalc_doi_suffix":""
    }
    url = url_for("weko_workflow.next_action",
            activity_id="2", action_id=7)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==7).first()
    assert q.action_status == ActionStatusPolicy.ACTION_RETRY
    q = ActivityAction.query.filter(ActivityAction.activity_id=="2", ActivityAction.action_id==5).first()
    assert q.action_status == ActionStatusPolicy.ACTION_DONE
    q = Activity.query.filter(Activity.activity_id=="2").first()
    assert q.action_id == 3
    assert q.action_status == ActionStatusPolicy.ACTION_DOING
    assert q.action_order == 2

    ###### _old_v & _old_v = _new_v
    mocker.patch("weko_workflow.views.process_send_approval_mails", return_value=None)
    mocker.patch("weko_workflow.views.process_send_notification_mail")
    update_activity_order("7",7,5,item_id7)
    url = url_for("weko_workflow.next_action",
            activity_id="7", action_id=7)

    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"

    ##### item_id == pid_without_ver
    ###### _value
    with patch("weko_workflow.views.IdentifierHandle.get_idt_registration_data",return_value=(["123"], ['JaLC'])):
        with patch("weko_workflow.views.check_doi_validation_not_pass",return_value="error_test"):
            update_activity_order("6",7,5,item_id6)
            url = url_for("weko_workflow.next_action",
                    activity_id="6", action_id=7)
            res = client.post(url, json=input)
            data = response_data(res)
            assert res.status_code == 500
            assert data["code"] == -1
            assert data["msg"] == "error_test"

    ###### not _value
    with patch("weko_workflow.views.IdentifierHandle.get_idt_registration_data",return_value=(None,None)):
        update_activity_order("6",7,5,item_id6)
        url = url_for("weko_workflow.next_action",
                activity_id="6", action_id=7)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == status_code
        assert data["code"] == 0
        assert data["msg"] == "success"

    #### select not Not_Grant
    #####x error_list is str
    input = {
        "temporary_save":0,
        "identifier_grant":"2",
        "identifier_grant_jalc_doi_suffix":"123",
        "identifier_grant_jalc_cr_doi_suffix":"456",
        "identifier_grant_jalc_dc_doi_suffix":"789",
        "identifier_grant_ndl_jalc_doi_suffix":"000"
    }
    url = url_for("weko_workflow.next_action",
            activity_id="2", action_id=7)
    test_msg = _('Cannot register selected DOI for current Item Type of this '
                 'item.')
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=test_msg):
        update_activity_order("2",7,5,item_id2)
        q = ActionIdentifier.query.filter(ActionIdentifier.activity_id=="2", ActionIdentifier.action_id==7).first()
        assert q.action_identifier_select == 0
        assert q.action_identifier_jalc_doi == ""
        assert q.action_identifier_jalc_cr_doi == ""
        assert q.action_identifier_jalc_dc_doi == ""
        assert q.action_identifier_ndl_jalc_doi == ""
        res = client.post(url,json=input)
        data = response_data(res)
        q = ActionIdentifier.query.filter(ActionIdentifier.activity_id=="2", ActionIdentifier.action_id==7).first()
        assert q.action_identifier_select == 2
        assert q.action_identifier_jalc_doi == "123"
        assert q.action_identifier_jalc_cr_doi == "456"
        assert q.action_identifier_jalc_dc_doi == "789"
        assert q.action_identifier_ndl_jalc_doi == "000"
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == test_msg

    #####x error_list
    input = {
        "temporary_save":0,
        "identifier_grant":"1",
        "identifier_grant_jalc_doi_suffix":"",
        "identifier_grant_jalc_cr_doi_suffix":"",
        "identifier_grant_jalc_dc_doi_suffix":"",
        "identifier_grant_ndl_jalc_doi_suffix":""
    }
    mock_previous_action = mocker.patch("weko_workflow.views.previous_action",return_value=make_response())
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=True):
        update_activity_order("2",7,5,item_id2)
        res = client.post(url,json=input)
        assert res.status_code == status_code
        mock_previous_action.assert_called_with(
            activity_id="2",
            action_id=7,
            req=-1
        )
    ##### error_list is not str and error_list=False
    url = url_for("weko_workflow.next_action",
            activity_id="5", action_id=7)
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=False):
        update_activity_order("5",7,5,item_id5)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == status_code
        assert data["code"] == 0
        assert data["msg"] == "success"
    ###### item_id
    ####### deposit and pid_without_ver and not recid
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=False):
        url = url_for("weko_workflow.next_action",
            activity_id="2", action_id=7)
        update_activity_order("2",7,5,item_id2)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == status_code
        assert data["code"] == 0
        assert data["msg"] == "success"
    ####### not (deposit and pid_without_ver and not recid)
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=False):
        url = url_for("weko_workflow.next_action",
            activity_id="5", action_id=7)
        update_activity_order("5",7,5,item_id5)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == status_code
        assert data["code"] == 0
        assert data["msg"] == "success"

    url = url_for("weko_workflow.next_action",
            activity_id="2", action_id=7)
    ## not exist identifier_select & not temporary_save
    ### _value and _type
    ####x error_list is str
    input = {
        "temporary_save":0,
        "identifier_grant_jalc_doi_suffix":"123",
        "identifier_grant_jalc_cr_doi_suffix":"456",
        "identifier_grant_jalc_dc_doi_suffix":"789",
        "identifier_grant_ndl_jalc_doi_suffix":"000"
    }
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=test_msg):
        update_activity_order("2",7,5,item_id2)
        q = ActionIdentifier.query.filter(ActionIdentifier.activity_id=="2", ActionIdentifier.action_id==7).first()
        assert q.action_identifier_select == 1
        assert q.action_identifier_jalc_doi == ""
        assert q.action_identifier_jalc_cr_doi == ""
        assert q.action_identifier_jalc_dc_doi == ""
        assert q.action_identifier_ndl_jalc_doi == ""
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] ==-1
        assert data["msg"] == test_msg
        q = ActionIdentifier.query.filter(ActionIdentifier.activity_id=="2", ActionIdentifier.action_id==7).first()
        assert q.action_identifier_select == 1
        assert q.action_identifier_jalc_doi == ""
        assert q.action_identifier_jalc_cr_doi == ""
        assert q.action_identifier_jalc_dc_doi == ""
        assert q.action_identifier_ndl_jalc_doi == ""
    ####x error_list is not str & error_list = True
    input = {
        "temporary_save":0,
        "identifier_grant_jalc_doi_suffix":"",
        "identifier_grant_jalc_cr_doi_suffix":"",
        "identifier_grant_jalc_dc_doi_suffix":"",
        "identifier_grant_ndl_jalc_doi_suffix":""
    }
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=True):
        update_activity_order("2",7,5,item_id2)
        res = client.post(url, json=input)
        assert res.status_code == status_code
        mock_previous_action.assert_called_with(
            activity_id="2",
            action_id=7,
            req=-1
        )
    #### error_list is not str & error_list = False
    input = {
        "temporary_save":0,
        "identifier_grant_jalc_doi_suffix":"",
        "identifier_grant_jalc_cr_doi_suffix":"",
        "identifier_grant_jalc_dc_doi_suffix":"",
        "identifier_grant_ndl_jalc_doi_suffix":""
    }
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=False):
        update_activity_order("2",7,5,item_id2)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == status_code
        assert data["code"] == 0
        assert data["msg"] == "success"
    ### not (_value and _type)
    url = url_for("weko_workflow.next_action",
                  activity_id="3", action_id=7)
    update_activity_order("3",7,5,item_id3)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"]==0
    assert data["msg"] == "success"

    # next_action_handler is None
    url = url_for("weko_workflow.next_action",
                  activity_id="2",action_id=7)
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=False):
        with patch("weko_workflow.views.WorkActivity.get_activity_action_comment", return_value=None):
            update_activity_order("2",7,5)
            res = client.post(url, json=input)
            data=response_data(res)
            assert res.status_code == 500
            assert data["code"] == -2
            assert data["msg"] == "can not get next_action_detail"
        q = GuestActivity.query.filter(GuestActivity.activity_id=="2").all()
        assert len(q) == 0
        q = FileOnetimeDownload.query.filter(FileOnetimeDownload.file_name=="test", FileOnetimeDownload.record_id=="1").all()
        assert len(q) == 0
        update_activity_order("2",7,5,item_id2,{"file_name":"test", "record_id": "1", "guest_mail": "guest@mail.com"})
        res = client.post(url, json=input)
        data=response_data(res)
        assert res.status_code == 200
        assert data["code"] == 0
        assert data["msg"] == "success"
        q = GuestActivity.query.filter(GuestActivity.activity_id=="2").all()
        assert len(q) == 0
        q = FileOnetimeDownload.query.filter(FileOnetimeDownload.file_name=="test", FileOnetimeDownload.record_id=="1").all()
        assert len(q) == 0
    activity_action = ActivityAction.query.filter_by(
        activity_id="2",
        action_id=4,
        action_order=6
    ).first()
    activity_action.action_handler=-1
    db.session.merge(activity_action)
    db.session.commit()

    # exist next_flow_action.action_roles
    url = url_for("weko_workflow.next_action",
                  activity_id="2",action_id=7)
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=False):
        update_activity_order("2",7,5,item_id2)
        res = client.post(url, json=input)
        data=response_data(res)
        assert res.status_code == status_code
        assert data["code"] == 0
        assert data["msg"] == "success"

    # action:approval
    def check_role_approval():
        if users[users_index]["id"] in [2,6,7]:
            return False
        else:
            return True

    noauth_msg = _('Authorization required')
    input = {
        "temporary_save":0
    }
    def mock_handle_finish_workflow(deposit,pid,recid):
        return pid.object_uuid
    ## can not get current_flow_action
    with patch("weko_workflow.views.Flow.get_flow_action_detail", return_value=None):
        url = url_for("weko_workflow.next_action",
                    activity_id="2",action_id=4)
        update_activity_order("2",4,6,item_id2)
        res = client.post(url, json=input)
        data = response_data(res)
        result_status = 500 if check_role_approval() else 200
        result_code = -1 if check_role_approval() else 403
        result_msg = "can not get curretn_flow_action" if check_role_approval() else noauth_msg
        assert res.status_code == result_status
        assert data["code"] == result_code
        assert data["msg"] == result_msg

    # with patch("weko_workflow.views.handle_finish_workflow",side_effect=mock_handle_finish_workflow):
    url = url_for("weko_workflow.next_action",
                    activity_id="2",action_id=4)
    ##x not exist next_action_detail
    with patch("weko_workflow.views.WorkActivity.get_activity_action_comment", return_value=None):
        update_activity_order("2",4,6,item_id2)
        res = client.post(url, json=input)
        data = response_data(res)
        result_status = 500 if check_role_approval() else 200
        result_code = -2 if check_role_approval() else 403
        result_msg = "can not get next_action_detail" if check_role_approval() else noauth_msg
        assert res.status_code == result_status
        assert data["code"] == result_code
        assert data["msg"] == result_msg

    ## can create_onetime_download_url
    new_id = uuid.uuid4()
    update_activity_order("2",4,6,item_id2,{"file_name":"test", "record_id": "1", "guest_mail": "guest@mail.com"})
    q = GuestActivity.query.filter(GuestActivity.activity_id=="2").all()
    assert len(q) == 1
    q = FileOnetimeDownload.query.filter(FileOnetimeDownload.file_name=="test", FileOnetimeDownload.record_id=="1").all()
    assert len(q) == 0
    res = client.post(url, json=input)
    data = response_data(res)
    result_code = 0 if check_role_approval() else 403
    result_msg = _("success") if check_role_approval() else noauth_msg
    assert res.status_code == status_code
    assert data["code"] == result_code
    assert data["msg"] == result_msg
    q = GuestActivity.query.filter(GuestActivity.activity_id=="2").all()
    if users_index in [0, 4, 5]:
        assert len(q) == 1
    else:
        assert len(q) == 0
    q = FileOnetimeDownload.query.filter(FileOnetimeDownload.file_name=="test", FileOnetimeDownload.record_id=="1").all()
    if users_index in [0, 4, 5]:
        assert len(q) == 0
    else:
        assert len(q) == 1

    ## exist requestmail
    ### exist feedbackmail, exist maillist
    update_activity_order("2",4,6,item_id2)
    adminsetting = {"display_request_form": True}
    with patch("weko_workflow.views.AdminSettings.get",return_value = adminsetting):
        request_mail = ActivityRequestMail(id = 1, activity_id =1, request_maillist=[{"mail":"test@test.org"}])
        with patch("weko_workflow.views.WorkActivity.get_activity_request_mail", return_value = request_mail):
            with patch("weko_workflow.views.WekoDeposit.update_request_mail"):
                with patch("weko_workflow.views.RequestMailList.update_by_list_item_id" )as update_request:
                    res = client.post(url, json=input)
                    data = response_data(res)
                    result_code = 0 if check_role_approval() else 403
                    result_msg = "success" if check_role_approval() else noauth_msg
                    assert res.status_code == status_code
                    assert data["code"] == result_code
                    assert data["msg"] == result_msg
                    if check_role_approval():
                        update_request.assert_called()

    # Permission is exist
    update_activity_order("2",4,6,item_id2,{"file_name":"test", "record_id": "1", "guest_mail": "guest@mail.com"})
    adminsetting = AdminSettings(id=1,name='items_display_settings',settings={"display_request_form": True})
    permission = FilePermission(users[users_index]['id'], '1', 'test_file', '1', '1', 1)
    with patch("weko_workflow.views.AdminSettings.get",return_value = adminsetting):
        request_mail = ActivityRequestMail(id = 1, activity_id =1, request_maillist=[{"mail":"test@test.org"}])
        with patch("weko_workflow.views.WorkActivity.get_activity_request_mail", return_value = request_mail):
            with patch("weko_workflow.views.WekoDeposit.update_request_mail"):
                with patch("weko_workflow.views.RequestMailList.update_by_list_item_id" )as update_request:
                    with patch('weko_workflow.views.FilePermission.find_by_activity', return_value=[permission]):
                        mock_files = mocker.patch('weko_workflow.views.grant_access_rights_to_all_open_restricted_files', return_value={})
                        res = client.post(url, json=input)
                        data = response_data(res)
                        result_code = 0 if check_role_approval() else 403
                        result_msg = "success" if check_role_approval() else noauth_msg
                        assert res.status_code == status_code
                        assert data["code"] == result_code
                        assert data["msg"] == result_msg
                        if check_role_approval():
                            update_request.assert_called()
                            mock_files.assert_called_once()

    # GuestActivity is exist
    update_activity_order("2",4,6,item_id2,{"file_name":"test", "record_id": "1", "guest_mail": "guest@mail.com"})
    adminsetting = AdminSettings(id=1,name='items_display_settings',settings={"display_request_form": True})
    guest_activity = GuestActivity(user_mail='user@mail.com', record_id='1', file_name='test', activity_id='2', token='token')
    with patch("weko_workflow.views.AdminSettings.get",return_value = adminsetting):
        request_mail = ActivityRequestMail(id = 1, activity_id =1, request_maillist=[{"mail":"test@test.org"}])
        with patch("weko_workflow.views.WorkActivity.get_activity_request_mail", return_value = request_mail):
            with patch("weko_workflow.views.WekoDeposit.update_request_mail"):
                with patch("weko_workflow.views.RequestMailList.update_by_list_item_id" )as update_request:
                    with patch('weko_workflow.views.GuestActivity.find_by_activity_id', return_value=[guest_activity]):
                        mock_files = mocker.patch('weko_workflow.views.grant_access_rights_to_all_open_restricted_files', return_value={})
                        res = client.post(url, json=input)
                        data = response_data(res)
                        result_code = 0 if check_role_approval() else 403
                        result_msg = "success" if check_role_approval() else noauth_msg
                        assert res.status_code == status_code
                        assert data["code"] == result_code
                        assert data["msg"] == result_msg
                        if check_role_approval():
                            update_request.assert_called()
                            mock_files.assert_called_once()

    ### exist requestmail, not maillist
    update_activity_order("2",4,6)
    adminsetting = {"display_request_form": True}
    with patch("weko_workflow.views.AdminSettings.get",return_value = adminsetting):
        with patch("weko_workflow.views.WorkActivity.get_activity_request_mail", return_value = None):
            with patch("weko_workflow.views.WekoDeposit.update_request_mail"):
                with patch("weko_workflow.views.RequestMailList.delete_by_list_item_id" )as delete_request:
                    res = client.post(url, json=input)
                    data = response_data(res)
                    result_code = 0 if check_role_approval() else 403
                    result_msg = "success" if check_role_approval() else noauth_msg
                    assert res.status_code == status_code
                    assert data["code"] == result_code
                    assert data["msg"] == result_msg
                    if check_role_approval():
                        delete_request.assert_called()

    ## exist item_application
    update_activity_order("2",4,6)
    item_application =  ActivityItemApplication(id=1, activity_id=1, item_application={"workflow":1, "terms":"term_free", "termsDescription":"test"})
    with patch("weko_workflow.views.WorkActivity.get_activity_item_application", return_value = item_application):
        with patch("weko_workflow.views.ItemApplication.update_by_list_item_id" )as update_application:
            with patch("weko_workflow.views.handle_finish_workflow",return_value=new_id):
                res= client.post(url, json=input)
                data = response_data(res)
                result_code = 0 if check_role_approval() else 403
                result_msg = "success" if check_role_approval() else noauth_msg
                assert res.status_code == status_code
                assert data["code"] == result_code
                assert data["msg"] == result_msg
                if check_role_approval():
                    update_application.assert_called()

    ## exist item_application, item_application 
    update_activity_order("2",4,6,item_id2)
    item_application =  ActivityItemApplication(id=1, activity_id=1, item_application={})
    with patch("weko_workflow.views.WorkActivity.get_activity_item_application", return_value = item_application):
        with patch("weko_workflow.views.ItemApplication.delete_by_list_item_id" )as delete_application:
            with patch("weko_workflow.views.handle_finish_workflow",return_value=new_id):
                res= client.post(url, json=input)
                data = response_data(res)
                result_code = 0 if check_role_approval() else 403
                result_msg = "success" if check_role_approval() else noauth_msg
                assert res.status_code == status_code
                assert data["code"] == result_code
                assert data["msg"] == result_msg
                if check_role_approval():
                    delete_application.assert_called() 

    ## exist feedbackmail
    ### exist feedbackmail, exist maillist
    update_activity_order("2",4,6,item_id2)
    with patch("weko_workflow.views.handle_finish_workflow",return_value=new_id):
        res = client.post(url, json=input)
        data = response_data(res)
        result_code = 0 if check_role_approval() else 403
        result_msg = "success" if check_role_approval() else noauth_msg
        assert res.status_code == status_code
        assert data["code"] == result_code
        assert data["msg"] == result_msg

    ### exist feedbackmail, not maillistxxx
    url = url_for("weko_workflow.next_action",
                    activity_id="3", action_id=4)
    update_activity_order("3",4,6,item_id3,{},'{ "cris_linkage": { "researchmap" : false } } ')
    with patch("weko_workflow.views.handle_finish_workflow",return_value=new_id):
        res = client.post(url, json=input)
        data = response_data(res)
        result_code = 0 if check_role_approval() else 403
        result_msg = "success" if check_role_approval() else noauth_msg
        assert res.status_code == status_code
        assert data["code"] == result_code
        assert data["msg"] == result_msg

    url = url_for("weko_workflow.next_action",
                    activity_id="3", action_id=4)
    update_activity_order("3",4,6,item_id3,{},'{ "cris_linkage": { "researchmap" : true } } ')
    res = client.post(url, json=input)
    data = response_data(res)

    url = url_for("weko_workflow.next_action",
                    activity_id="3", action_id=4)
    update_activity_order("3",4,6,item_id3,{},None)
    res = client.post(url, json=input)
    data = response_data(res)

    ### last_ver
    parent1 = PersistentIdentifier.get("recid","2")
    parent1.status = PIDStatus.NEW
    db.session.merge(parent1)
    parent2 = PersistentIdentifier.get("recid","2.1")
    parent2.status = PIDStatus.NEW
    db.session.merge(parent2)
    parent3 = PersistentIdentifier.get("recid","2.0")
    parent3.status = PIDStatus.NEW
    db.session.merge(parent3)
    db.session.commit()
    url = url_for("weko_workflow.next_action",
                    activity_id="3", action_id=4)
    update_activity_order("3",4,6,item_id3)
    res = client.post(url, json=input)
    data = response_data(res)
    result_status = 500 if check_role_approval() else 200
    result_code = -1 if check_role_approval() else 403
    result_msg = "can not get last_ver" if check_role_approval() else noauth_msg
    assert res.status_code == result_status
    assert data["code"] == result_code
    assert data["msg"] == result_msg
    parent1 = PersistentIdentifier.get("recid","2")
    parent1.status = PIDStatus.REGISTERED
    db.session.merge(parent1)
    parent2 = PersistentIdentifier.get("recid","2.1")
    parent2.status = PIDStatus.REGISTERED
    db.session.merge(parent2)
    parent3 = PersistentIdentifier.get("recid","2.0")
    parent3.status = PIDStatus.REGISTERED
    db.session.merge(parent3)
    db.session.commit()

    ## not exist feedbackmail
    url = url_for("weko_workflow.next_action",
                    activity_id="4", action_id=4)
    update_activity_order("4",4,6,item_id4)
    with patch("weko_workflow.views.handle_finish_workflow",return_value=new_id):
        res = client.post(url, json=input)
        data = response_data(res)
        result_code = 0 if check_role_approval() else 403
        result_msg = "success" if check_role_approval() else noauth_msg
        assert res.status_code == status_code
        assert data["code"] == result_code
        assert data["msg"] == result_msg

    ## raise BaseException
    url = url_for("weko_workflow.next_action",
                    activity_id="5",action_id=4)
    with patch("weko_workflow.views.handle_finish_workflow",return_value=new_id):
        with patch("weko_workflow.views.has_request_context",side_effect=BaseException):
            update_activity_order("5",4,6,item_id5)
            q = Activity.query.filter(Activity.activity_id=="5").first()
            assert q.activity_status == ActionStatusPolicy.ACTION_BEGIN
            assert q.action_id == 4
            assert q.action_status == None
            assert q.action_order == 6
            assert q.item_id == item_id5
            res = client.post(url, json=input)
            result_status_code = 500 if check_role_approval() else 200
            assert res.status_code == result_status_code
            if not check_role_approval():
                data = response_data(res)
                assert data["code"] == 403
                assert data["msg"] == noauth_msg
                q = Activity.query.filter(Activity.activity_id=="5").first()
                assert q.activity_status == ActionStatusPolicy.ACTION_BEGIN
                assert q.action_id == 4
                assert q.action_status == None
                assert q.action_order == 6
                assert q.item_id == item_id5

        ## send signal
        url = url_for("weko_workflow.next_action",
                        activity_id="5",action_id=4)
        update_activity_order("5",4,6,item_id5)
        res = client.post(url, json=input)
        data = response_data(res)
        result_code = 0 if check_role_approval() else 403
        result_msg = "success" if check_role_approval() else noauth_msg
        assert res.status_code == status_code
        assert data["code"] == result_code
        assert data["msg"] == result_msg
        q = Activity.query.filter(Activity.activity_id=="5").first()
        if users_index in [0, 4, 5]:
            assert q.activity_status == ActionStatusPolicy.ACTION_BEGIN
            assert q.action_id == 4
            assert q.action_status == None
            assert q.action_order == 6
        else:
            assert q.activity_status == ActionStatusPolicy.ACTION_DONE
            assert q.action_id == 2
            assert q.action_status == 'F'
            assert q.action_order == 7
            assert q.item_id == new_id

        input = {
        "temporary_save":1,
        "identifier_grant_jalc_doi_suffix":"",
        "identifier_grant_jalc_cr_doi_suffix":"",
        "identifier_grant_jalc_dc_doi_suffix":"",
        "identifier_grant_ndl_jalc_doi_suffix":""
        }
        identifier_info={"action_identifier_select":-2,
            "action_identifier_jalc_doi":"",
            "action_identifier_jalc_cr_doi":"",
            "action_identifier_jalc_dc_doi":"",
            "action_identifier_ndl_jalc_doi":""}
        with patch("weko_workflow.views.WorkActivity.get_action_identifier_grant", return_value=identifier_info):
            url = url_for("weko_workflow.next_action",
                      activity_id="3", action_id=4)
            update_activity_order("3",4,6)
            res = client.post(url, json=input)
            data = response_data(res)
            result_code = 0 if check_role_approval() else 403
            result_msg = "success" if check_role_approval() else noauth_msg
            assert res.status_code == status_code
            assert data["code"] == result_code
            assert data["msg"] == result_msg

        identifier_info={"action_identifier_select":-3,
            "action_identifier_jalc_doi":"",
            "action_identifier_jalc_cr_doi":"",
            "action_identifier_jalc_dc_doi":"",
            "action_identifier_ndl_jalc_doi":""}
        with patch("weko_workflow.views.WorkActivity.get_action_identifier_grant", return_value=identifier_info):
            url = url_for("weko_workflow.next_action",
                      activity_id="3", action_id=4)
            update_activity_order("3",4,6)
            res = client.post(url, json=input)
            data = response_data(res)
            result_code = 0 if check_role_approval() else 403
            result_msg = "success" if check_role_approval() else noauth_msg
            assert res.status_code == status_code
            assert data["code"] == result_code
            assert data["msg"] == result_msg

    input = {
        "temporary_save":0,
        "identifier_grant_jalc_doi_suffix":"",
        "identifier_grant_jalc_cr_doi_suffix":"",
        "identifier_grant_jalc_dc_doi_suffix":"",
        "identifier_grant_ndl_jalc_doi_suffix":""
    }
    ## can not publish
    with patch("weko_workflow.views.handle_finish_workflow",return_value=None):
        url = url_for("weko_workflow.next_action",
                      activity_id="2",action_id=4)
        update_activity_order("2",4,6,item_id2)
        res = client.post(url, json=input)
        data = response_data(res)
        result_status = 500 if check_role_approval() else 200
        result_code = -1 if check_role_approval() else 403
        result_msg = _("error") if check_role_approval() else noauth_msg
        assert res.status_code == result_status
        assert data["code"] == result_code
        assert data["msg"] == result_msg

    # no next_flow_action
    with patch("weko_workflow.views.Flow.get_next_flow_action",return_value=None):
        url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=3)
        update_activity_order("2",3,2,item_id2)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -2
        assert data["msg"] == "can not get next_flow_action"


    # not rtn
    with patch("weko_workflow.views.WorkActivityHistory.create_activity_history", return_value=None):
        url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=3)
        update_activity_order("2",3,2,item_id2)
        res = client.post(url, json=input)
        assert res.status_code == 500
        assert data["code"] == -2
        assert data["msg"] == "can not get next_flow_action"

    # action_status
    with patch("weko_workflow.views.WorkActivity.upt_activity_action", return_value=False):
        url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=3)
        update_activity_order("2",3,2,item_id2)
        res = client.post(url, json=input)
        assert res.status_code == 500
        assert data["code"] == -2
        assert data["msg"] == ""

    with patch("weko_workflow.views.WorkActivity.upt_activity_action_status", return_value=False):
        url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=3)
        update_activity_order("2",3,2,item_id2)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -2
        assert data["msg"] == ""


    with client.session_transaction() as session:
        # no session
        pass
    url = url_for("weko_workflow.next_action",
              activity_id="2", action_id=3)
    update_activity_order("2",3,2,item_id2)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == 200
    assert data["code"] == 0
    assert data["msg"] == _("success")

    ###### not delete flow
    # approval
    update_activity_order("2",4,6,item_id2)
    input = {}
    url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=4)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == 200

    ###### delete flow
    ## no approval
    update_activity_order("A-00000001-10020",1,1,item_id8)
    url = url_for("weko_workflow.next_action",
            activity_id="A-00000001-10020", action_id=1)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"

    # last_idt_setting and last_idt_setting.get('action_identifier_select'):
    ## last_idt_setting.get('action_identifier_select') == -1
    with patch("weko_workflow.api.WorkActivity.get_action_identifier_grant",return_value={"action_identifier_select":-1}):
        url = url_for("weko_workflow.next_action",
                    activity_id="2",action_id=4)
        update_activity_order("2",4,6,item_id2)
        res = client.post(url, json=input)
        assert res.status_code == status_code

    # last_idt_setting and last_idt_setting.get('action_identifier_select'):
    ## last_idt_setting.get('action_identifier_select') == -2
    with patch("weko_workflow.api.WorkActivity.get_action_identifier_grant",return_value={"action_identifier_select":-2}):
        url = url_for("weko_workflow.next_action",
                    activity_id="2",action_id=4)
        update_activity_order("2",4,6,item_id2)
        res = client.post(url, json=input)
        assert res.status_code == status_code

    # last_idt_setting and last_idt_setting.get('action_identifier_select'):
    ## last_idt_setting.get('action_identifier_select') == -3
    with patch("weko_workflow.api.WorkActivity.get_action_identifier_grant",return_value={"action_identifier_select":-3}):
        url = url_for("weko_workflow.next_action",
                    activity_id="2",action_id=4)
        update_activity_order("2",4,6,item_id2)
        res = client.post(url, json=input)
        assert res.status_code == status_code

    input = {
        "temporary_save":0,
        "identifier_grant":"0",
        "identifier_grant_jalc_doi_suffix":"",
        "identifier_grant_jalc_cr_doi_suffix":"",
        "identifier_grant_jalc_dc_doi_suffix":"",
        "identifier_grant_ndl_jalc_doi_suffix":""
    }
    # identifier_select == IDENTIFIER_GRANT_SELECT_DICT['NotGrant']:
    ## item_id == pid_without_ver.object_uuid
    update_activity_order("6",7,5,item_id6)
    url = url_for("weko_workflow.next_action",
            activity_id="6", action_id=7)
    res = client.post(url, json=input)
    assert res.status_code == status_code

    # identifier_select == IDENTIFIER_GRANT_SELECT_DICT['NotGrant']:
    ## item_id != pid_without_ver.object_uuid
    ### _old_v == _new_v
    update_activity_order("7",7,5,item_id7)
    url = url_for("weko_workflow.next_action",
            activity_id="7", action_id=7)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"

    ## approval
    # delete reject
    update_activity_order("A-00000001-10021",1,2,item_id9)
    assert next_action(activity_id="A-00000001-10021", action_id=4, json_data={"approval_reject":1})
    assert data["code"] == 0
    assert data["msg"] == "success"

    update_activity_order("A-00000001-10022",1,2,item_id10)
    assert next_action(activity_id="A-00000001-10022", action_id=4, json_data={"approval_reject":1})
    assert data["code"] == 0
    assert data["msg"] == "success"

    # delete approve
    update_activity_order("A-00000001-10021",1,2,item_id9)
    with patch("weko_records_ui.utils.soft_delete", return_value=True):
        url = url_for("weko_workflow.next_action",
                      activity_id="A-00000001-10021", action_id=4)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == status_code
        assert data["code"] == 0
        assert data["msg"] == "success"

    # delete two approve
    update_activity_order("A-00000001-10022",1,2,item_id10)
    with patch("weko_records_ui.utils.soft_delete", return_value=True):
        with patch("weko_items_ui.utils.send_mail_from_notification_info", return_value=True):
            url = url_for("weko_workflow.next_action",
                        activity_id="A-00000001-10022", action_id=4)
            res = client.post(url, json=input)
            data = response_data(res)
            assert res.status_code == status_code
            assert data["code"] == 0
            assert data["msg"] == "success"

    # delete approve
    update_activity_order("A-00000001-10023",1,3,item_id11)
    with patch("weko_records_ui.utils.delete_version", return_value=True):
        url = url_for("weko_workflow.next_action",
                      activity_id="A-00000001-10023", action_id=4)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == status_code
        assert data["code"] == 0
        assert data["msg"] == "success"

    # identifier_select == IDENTIFIER_GRANT_SELECT_DICT['NotGrant']:
    ## item_id == pid_without_ver.object_uuid
    ### not _value
    with patch("weko_workflow.utils.IdentifierHandle.get_idt_registration_data",return_value=(None,None)):
        update_activity_order("6",7,5,item_id6)
        url = url_for("weko_workflow.next_action",
                activity_id="6", action_id=7)
        res = client.post(url, json=input)
        assert res.status_code == status_code

    # identifier_select == IDENTIFIER_GRANT_SELECT_DICT['NotGrant']:
    ## item_id != pid_without_ver.object_uuid
    ### not _old_v    
    with patch("weko_workflow.utils.IdentifierHandle.get_idt_registration_data",return_value=(None,None)):
        update_activity_order("7",7,5,item_id7)
        url = url_for("weko_workflow.next_action",
                activity_id="7", action_id=7)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == status_code
        assert data["code"] == 0
        assert data["msg"] == "success"

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_next_action_usage_application -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200)
])
def test_next_action_usage_application(client, db, users, db_register_usage_application, db_records, users_index, status_code, mocker):
    def update_activity_order(activity_id, action_id, action_order):
        with db.session.begin_nested():
            activity=Activity.query.filter_by(activity_id=activity_id).one_or_none()
            activity.action_id=action_id
            activity.action_order=action_order
            db.session.merge(activity)
        db.session.commit()
    login(client=client, email=users[users_index]["email"])
    with client.session_transaction() as session:
        session['itemlogin_id'] = "test id"
        session['itemlogin_activity'] = "test activity"
        session['itemlogin_item'] = "test item"
        session['itemlogin_steps'] = "test steps"
        session['itemlogin_action_id'] = "test action_id"
        session['itemlogin_cur_step'] = "test cur_step"
        session['itemlogin_record'] = "test approval_record"
        session['itemlogin_histories'] = "test histories"
        session['itemlogin_res_check'] = "test res_check"
        session['itemlogin_pid'] = "test recid"
        session['itemlogin_community_id'] = "test community_id"

    mocker.patch("weko_workflow.views.IdentifierHandle.remove_idt_registration_metadata",return_value=None)
    mocker.patch("weko_workflow.views.IdentifierHandle.update_idt_registration_metadata",return_value=None)
    mocker.patch("weko_workflow.views.FeedbackMailList.update_by_list_item_id")
    mocker.patch("weko_workflow.views.FeedbackMailList.delete_by_list_item_id")
    mock_signal = mocker.patch("weko_workflow.views.item_created.send")
    new_item = uuid.uuid4()
    mocker.patch("weko_workflow.views.handle_finish_workflow",return_value=new_item)

    urls = []
    urls.append(url_for("weko_workflow.next_action",
                activity_id="A-00000001-20001", action_id=3))
    urls.append(url_for("weko_workflow.next_action",
                activity_id="A-00000001-20002", action_id=4))
    urls.append(url_for("weko_workflow.next_action",
                activity_id="A-00000001-20003", action_id=4))
    urls.append(url_for("weko_workflow.next_action",
                activity_id="A-00000001-20004", action_id=4))

    # file_namesが正規表現に合う場合
    with patch("weko_workflow.views.grant_access_rights_to_all_open_restricted_files") as grant_mock:
        urls.append(url_for("weko_workflow.next_action",
                activity_id="A-00000001-20005", action_id=4))
        grant_mock.assert_not_called()

    # update_activity_order("2",3,2)
    input = {

    }

    mocker.patch("weko_workflow.views.process_send_approval_mails", return_value=None)
    mocker.patch("weko_workflow.views.process_send_notification_mail")
    for url in urls:
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 200
        assert data["code"] == 0
        assert data["msg"] == _("success")


@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_next_action_for_request_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_next_action_for_request_mail(app, client, db, users, db_register_request_mail, db_records, users_index, status_code, mocker):
    def update_activity_order(activity_id, action_id, action_order):
        with db.session.begin_nested():
            activity=Activity.query.filter_by(activity_id=activity_id).one_or_none()
            activity.action_id=action_id
            activity.action_order=action_order
            db.session.merge(activity)
        db.session.commit()
    login(client=client, email=users[users_index]["email"])
    with client.session_transaction() as session:
        session['itemlogin_id'] = "test id"
        session['itemlogin_activity'] = "test activity"
        session['itemlogin_item'] = "test item"
        session['itemlogin_steps'] = "test steps"
        session['itemlogin_action_id'] = "test action_id"
        session['itemlogin_cur_step'] = "test cur_step"
        session['itemlogin_record'] = "test approval_record"
        session['itemlogin_histories'] = "test histories"
        session['itemlogin_res_check'] = "test res_check"
        session['itemlogin_pid'] = "test recid"
        session['itemlogin_community_id'] = "test community_id"

    mocker.patch("weko_workflow.views.IdentifierHandle.remove_idt_registration_metadata",return_value=None)
    mocker.patch("weko_workflow.views.IdentifierHandle.update_idt_registration_metadata",return_value=None)
    mocker.patch("weko_workflow.views.WekoDeposit.update_feedback_mail")
    mocker.patch("weko_workflow.views.FeedbackMailList.update_by_list_item_id")
    mocker.patch("weko_workflow.views.FeedbackMailList.delete_by_list_item_id")
    mock_signal = mocker.patch("weko_workflow.views.item_created.send")
    new_item = uuid.uuid4()
    mocker.patch("weko_workflow.views.handle_finish_workflow",return_value=new_item)
    mocker.patch("weko_workflow.views.process_send_notification_mail") 
    send_mail = mocker.patch("weko_workflow.views.process_send_approval_mails")
    get_ids = mocker.patch("weko_workflow.views.WorkActivity.get_user_ids_of_request_mails_by_activity_id",return_value =[1,2,3])
    update_activity_order("7",7,5)
    input = {
        "temporary_save":0,
        "identifier_grant":"0",
        "identifier_grant_jalc_doi_suffix":"",
        "identifier_grant_jalc_cr_doi_suffix":"",
        "identifier_grant_jalc_dc_doi_suffix":"",
        "identifier_grant_ndl_jalc_doi_suffix":""
    }
    adminsetting=AdminSettings(id=1,name='items_display_settings',settings={})
    # Adminsettings display_request_form is None
    with db.session.begin_nested():
        db.session.add(adminsetting)
    db.session.commit()

    url = url_for("weko_workflow.next_action",
            activity_id="7", action_id=7)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    send_mail.assert_not_called()
    get_ids.assert_not_called()

    # Adminsettings display_request_form is False
    with db.session.begin_nested():
        db.session.delete(adminsetting)
        adminsetting = AdminSettings(id=1,name='items_display_settings',settings={"display_request_form": False})
        db.session.add(adminsetting)
    db.session.commit()

    update_activity_order("7",7,5)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    send_mail.assert_not_called()
    get_ids.assert_not_called()

    # Adminsettings display_request_form is True
    with db.session.begin_nested():
        db.session.delete(adminsetting)
        adminsetting = AdminSettings(id=1,name='items_display_settings',settings={"display_request_form": True})
        db.session.add(adminsetting)
    db.session.commit()

    update_activity_order("7",7,5)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    send_mail.assert_called()


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_cancel_action_acl_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_cancel_action_acl_nologin(client,db_register2):
    """Test of cancel action."""
    url = url_for('weko_workflow.cancel_action',
                  activity_id='1', action_id=1)
    input = {'action_version': 1, 'commond': 1}

    # 51992 case.06(cancel_action)
    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == 'http://test_server.localdomain/login/?next=%2Fworkflow%2Factivity%2Faction%2F1%2F1%2Fcancel'

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_cancel_action_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code, is_admin', [
    (0, 403, False),
    (1, 403, True),
    (2, 403, True),
    (3, 403, True),
    (4, 403, False),
    (5, 403, False),
    (6, 403, True),
])
def test_cancel_action_acl_users(client, users, db_register_full_action, users_index, status_code, is_admin):
    """Test of cancel action."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.cancel_action',
                  activity_id='1', action_id=1)
    input = {'action_version': 1, 'commond': 1}
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }

    # 51992 case.07(cancel_action)
    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        assert res.status_code != status_code

    action_users = {
        'allow': [],
        'deny': [users[users_index]["id"]]
    }
    url = url_for('weko_workflow.cancel_action',
                  activity_id='2', action_id=1)
    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code != status_code
        if is_admin:
            assert data["code"] != 403
        else:
            assert data["code"] == 403

    action_users = {
        'allow': [users[users_index]["id"]],
        'deny': []
    }
    url = url_for('weko_workflow.cancel_action',
                  activity_id='3', action_id=1)
    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code != status_code
        assert data["code"] != 403

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_cancel_action_acl_guestlogin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_cancel_action_acl_guestlogin(guest, db_register_full_action):
    input = {'action_version': 1, 'commond': 1}
    url = url_for('weko_workflow.cancel_action',
                  activity_id="1", action_id=1)
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }

    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = guest.post(url, json=input)
        assert res.status_code != 403
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_cancel_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    # (0, 200),
    (1, 200),
    (2, 200),
    # (3, 200),
    # (4, 200),
    # (5, 200),
    (6, 200),
])
def test_cancel_action(client, users,db, db_register_full_action, db_records, add_file, users_index, status_code, mocker):
    login(client=client, email=users[users_index]['email'])
    #mocker.patch("weko_workflow.views.remove_file_cancel_action")
    # argument error
    with patch("weko_workflow.views.type_null_check",return_value=False):
        url = url_for('weko_workflow.cancel_action',
                  activity_id='1', action_id=1)
        # 51992 case.08,09(cancel_action)
        res = client.post(url, json={})
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "argument error"

    # request_body error
    url = url_for('weko_workflow.cancel_action',
              activity_id='1', action_id=1)
    with patch("weko_workflow.views.CancelSchema",side_effect=ValidationError("test error")):
        # 51992 case.10(cancel_action)
        res = client.post(url, json={})
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "test error"


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_cancel_action2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_cancel_action2(client, users,db, db_register_full_action, db_records, add_file, users_index, status_code, mocker):
    login(client=client, email=users[users_index]['email'])
    # can not get activity_detail
    input = {
        "action_version":"1.0.0",
        "commond":"this is test comment.",
        "pid_value":"1.1"
        }
    with patch("weko_workflow.views.WorkActivity.get_activity_by_id",side_effect=[db_register_full_action["activities"][0],None]):
        url = url_for('weko_workflow.cancel_action',
                      activity_id='1', action_id=1)
        # 51992 case.11(cancel_action)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "can not get activity detail"

    # not exist item, exist files, exist cancel_pv, exist file_permission
    input = {
        "action_version":"1.0.0",
        "commond":"this is test comment.",
        "pid_value":"1.1"
        }
    # FilePermission.init_file_permission(users[users_index]["id"],"1.1","test_file","1")
    add_file(db_records[2][2])
    url = url_for('weko_workflow.cancel_action',
                  activity_id='1', action_id=1)
    redirect_url = url_for("weko_workflow.display_activity",
                           activity_id="1").replace("http://test_server.localdomain","")
    q = Activity.query.filter(Activity.activity_id=="1").first()
    assert q.status == 'N'
    assert q.action_order == 1
    assert q.activity_status == ActionStatusPolicy.ACTION_BEGIN
    q = ActivityHistory.query.filter(ActivityHistory.activity_id=="1").all()
    assert len(q) == 1
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    assert data["data"]["redirect"] == redirect_url
    q = Activity.query.filter(Activity.activity_id=="1").first()
    assert q.status == 'N'
    assert q.action_order == 1
    assert q.activity_status == ActionStatusPolicy.ACTION_CANCELED
    q = ActivityHistory.query.filter(ActivityHistory.activity_id=="1").all()
    assert len(q) == 3

    permission = FilePermission(users[users_index]['id'], input['pid_value'], 'test_file', '1', '1', 1)
    with patch('weko_workflow.views.FilePermission.find_by_activity', return_value=[permission]):
        with patch('weko_workflow.views.FilePermission.delete_object'):
            res = client.post(url, json=input)
            data = response_data(res)
            assert res.status_code == status_code
            assert data["code"] == 0
            assert data["msg"] == "success"
            assert data["data"]["redirect"] == redirect_url
            q = Activity.query.filter(Activity.activity_id=="1").first()
            assert q.status == 'N'
            assert q.action_order == 1
            assert q.activity_status == ActionStatusPolicy.ACTION_CANCELED
            q = ActivityHistory.query.filter(ActivityHistory.activity_id=="1").all()
            assert len(q) == 5

    ## raise PIDDoesNotExistError
    # 51992 case.12(cancel_action)
    with patch("weko_workflow.views.PersistentIdentifier.get",side_effect=PIDDoesNotExistError("recid","test pid")):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "can not get PersistIdentifier"

    input = {
        "action_version":"1.0.0",
        "commond":"this is test comment.",
        }
    with patch("weko_workflow.views.get_pid_value_by_activity_detail",return_value=None):
        q = ActivityHistory.query.filter(ActivityHistory.activity_id=="1").all()
        assert len(q) == 5
        # 51992 case.01(cancel_action)
        res = client.post(url, json=input)
        data = response_data(res)
        redirect_url = url_for("weko_workflow.display_activity",
                       activity_id="1").replace("http://test_server.localdomain","")
        assert res.status_code == 200
        assert data["code"] == 0
        assert data["msg"] == "success"
        assert data["data"]["redirect"] == redirect_url
        q = ActivityHistory.query.filter(ActivityHistory.activity_id=="1").all()
        assert len(q) == 7

    # exist item, not exist files, not exist file_permission
    input = {
        "action_version": "1.0.0",
        "commond":"this is test comment."
    }
    url = url_for("weko_workflow.cancel_action",
                  activity_id="2", action_id=1)
    redirect_url = url_for("weko_workflow.display_activity",
                           activity_id="2").replace("http://test_server.localdomain","")
    # 51992 case.02(cancel_action)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    assert data["data"]["redirect"] == redirect_url

    # not cancel_record, not exist rtn
    # 51992 case.15(cancel_action)
    with patch("weko_workflow.views.WekoDeposit.get_record", return_value=None):
        with patch("weko_workflow.views.WorkActivity.quit_activity", return_value=None):
            res = client.post(url, json = input)
            data = response_data(res)
            assert res.status_code == 500
            assert data["code"] == -1
            assert data["msg"] == 'Error! Cannot process quit activity!'
            q = ActivityHistory.query.filter(ActivityHistory.activity_id=="1").all()
            assert len(q) == 7

    ## raise PIDDoesNotExistError
    # 51992 case.13(cancel_action)
    with patch("weko_workflow.views.PersistentIdentifier.get_by_object",side_effect=PIDDoesNotExistError("recid","test pid")):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "can not get PersistentIdentifier"

    # raise exception
    # 51992 case.14(cancel_action)
    with patch("weko_workflow.views.PersistentIdentifier.get_by_object", side_effect=Exception):
        res = client.post(url, json = input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "<class 'Exception'>"

    input = {
        "action_version":"1.0.0",
        "commond":"this is test comment.",
        }
    with patch("weko_workflow.views.get_pid_value_by_activity_detail",return_value=None):
        with patch("weko_records_ui.models.FilePermission.find_by_activity",side_effect=Exception):
            with pytest.raises(Exception) as e:
                res = client.post(url, json=input)
                data = response_data(res)
                assert res.status_code == 500
                assert data["code"] == -1
                assert data["msg"] == "Error! Cannot process quit activity!"
                q = ActivityHistory.query.filter(ActivityHistory.activity_id=="1").all()
                assert len(q) == 7

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_cancel_action3 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_cancel_action3(client, users,db, db_register_full_action, db_records, add_file, users_index, status_code, mocker):
    """
    Test cancel_action add case

    Args:
        client (fixture): cliant settings
        users (fixture): user settings
        db (fixture): db settings
        db_register_full_action (fixture): add FlowDefine, FlowAction, WorkFlow, Activity, ActivityAction, ActionFeedbackMail, ActivityHistory
        db_records (fixture): set pid data
        add_file (fixture): test file, bucket
        users_index (parametrize): test user
        status_code (parametrize): expect status
        mocker (fixture): mocker
    """
    login(client=client, email=users[users_index]['email'])
    activity_id = "9"
    action_id = 1

    input = {
        'action_version':'1.0.0',
        'commond':'this is test comment.'
    }

    # 51992 03(cancel_action)
    with patch('weko_workflow.views.WekoRecord.update_item_link') as mock_update_item_link:
        url = url_for('weko_workflow.cancel_action', activity_id=activity_id, action_id=action_id)
        client.post(url, json=input)

        mock_update_item_link.assert_called_once()

    activity_id = '2'
    action_id = 1

    # 51992 04(cancel_action)
    with patch('weko_workflow.views.ItemLink.update') as mock_update:
        url = url_for('weko_workflow.cancel_action', activity_id=activity_id, action_id=action_id)
        client.post(url, json=input)
        mock_update.assert_called_once()

    input = {
        "action_version":"1.0.0",
        "commond":"this is test comment.",
        "pid_value":"1.1"
        }
    activity_id = '1'
    action_id = 1

    # 51992 05(cancel_action)
    with patch('weko_workflow.views.remove_file_cancel_action') as mock_remove_file_cancel_action:
        add_file(db_records[2][2])
        url = url_for('weko_workflow.cancel_action', activity_id=activity_id, action_id=action_id)
        client.post(url, json=input)
        mock_remove_file_cancel_action.assert_called_once()


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_cancel_action_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_cancel_action_guest(guest, db, db_register_full_action, mocker):
    input = {
        "action_version": "1.0.0",
        "commond":"this is test comment."
    }
    activity_guest = Activity(activity_id="99",workflow_id=1,flow_id=db_register_full_action["flow_define"].id,
                              action_id=1,
                              activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                              title="test guest", extra_info={"guest_mail":"guest@test.org"},
                              action_order=1)
    with db.session.begin_nested():
        db.session.add(activity_guest)
    db.session.commit()
    mocker.patch("weko_workflow.views.validate_action_role_user", return_value=(False, False, False))
    url = url_for("weko_workflow.cancel_action",
                  activity_id="99", action_id=1)
    redirect_url = url_for("weko_workflow.display_guest_activity",file_name="test_file")
    res = guest.post(url, json=input)
    data = response_data(res)
    assert res.status_code == 200
    assert data["code"] == 0
    assert data["msg"] == "success"
    assert data["data"]["redirect"] == redirect_url


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_send_mail_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_send_mail_nologin(client,db_register2):
    """Test of send mail."""
    url = url_for('weko_workflow.send_mail', activity_id='1',
                  mail_id='1')
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_send_mail_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_send_mail_users(client, users, users_index, status_code):
    """Test of send mail."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.send_mail', activity_id='1',
                  mail_id='1')
    input = {}
    with patch('weko_workflow.views.process_send_reminder_mail'):
        res = client.post(url, json=input)
        assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_unlocks_activity_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_unlocks_activity_nologin(client, db_register2):
    url = url_for('weko_workflow.unlocks_activity',activity_id="A-22000111-00001")
    res = client.post(url)
    assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_unlocks_activity_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index', [ i for i in range(7)])
def test_unlocks_activity_acl(client, users, db_register2, users_index):
    url = url_for('weko_workflow.unlocks_activity',activity_id="A-22000111-00001")
    login(client=client, email=users[users_index]["email"])
    data = json.dumps({"locked_value":"", "is_opened":False})
    res = client.post(url,data=data)
    assert res.status_code != 302

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_unlocks_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_unlocks_activity(client, users, db_register2):

    activity_id="A-22000111-00001"
    url = url_for("weko_workflow.unlocks_activity", activity_id=activity_id)
    locked_value = "1-123456789"
    user = users[2]
    login(client=client, email=user["email"])

    lock_key = "workflow_locked_activity_{}".format(activity_id)
    user_lock_key = "workflow_userlock_activity_{}".format(user["id"])
    current_cache.delete(lock_key)
    current_cache.delete(user_lock_key)

    data = json.dumps({"locked_value":locked_value, "is_opened":False})

    # not locked
    res = client.post(url, data=data)
    assert res.status_code == 200
    assert json.loads(res.data) == {"code": 200, "msg_lock":None, "msg_userlock":"Not unlock"}

    # locked
    current_cache.set(lock_key,locked_value)
    current_cache.set(user_lock_key,activity_id)
    res = client.post(url, data=data)
    assert res.status_code == 200
    assert json.loads(res.data) == {"code": 200, "msg_lock":"Unlock success", "msg_userlock":"User Unlock Success"}
    assert current_cache.get(lock_key) == None
    assert current_cache.get(user_lock_key) == None

    current_cache.delete(lock_key)
    current_cache.delete(user_lock_key)



# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_unlocks_activity_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_unlocks_activity_nologin(client, db_register2):
    url = url_for('weko_workflow.unlocks_activity',activity_id="A-22000111-00001")
    res = client.post(url)
    assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_unlocks_activity_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index', [ i for i in range(7)])
def test_unlocks_activity_acl(client, users, db_register2, users_index):
    url = url_for('weko_workflow.unlocks_activity',activity_id="A-22000111-00001")
    login(client=client, email=users[users_index]["email"])
    data = json.dumps({"locked_value":"", "is_opened":False})
    res = client.post(url,data=data)
    assert res.status_code != 302

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_unlocks_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_unlocks_activity(client, users, db_register2):

    activity_id="A-22000111-00001"
    url = url_for("weko_workflow.unlocks_activity", activity_id=activity_id)
    locked_value = "1-123456789"
    user = users[2]
    login(client=client, email=user["email"])

    lock_key = "workflow_locked_activity_{}".format(activity_id)
    user_lock_key = "workflow_userlock_activity_{}".format(user["id"])
    current_cache.delete(lock_key)
    current_cache.delete(user_lock_key)

    data = json.dumps({"locked_value":locked_value, "is_opened":False})

    # not locked
    res = client.post(url, data=data)
    assert res.status_code == 200
    assert json.loads(res.data) == {"code": 200, "msg_lock":None, "msg_userlock":"Not unlock"}

    # locked
    current_cache.set(lock_key,locked_value)
    current_cache.set(user_lock_key,activity_id)
    res = client.post(url, data=data)
    assert res.status_code == 200
    assert json.loads(res.data) == {"code": 200, "msg_lock":"Unlock success", "msg_userlock":"User Unlock Success"}
    assert current_cache.get(lock_key) == None
    assert current_cache.get(user_lock_key) == None

    current_cache.delete(lock_key)
    current_cache.delete(user_lock_key)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_is_user_locked_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_is_user_locked_nologin(client, db_register2):
    url = url_for('weko_workflow.is_user_locked')
    res = client.post(url)
    assert res.status_code == 405


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_is_user_locked_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index', [ i for i in range(7)])
def test_is_user_locked_acl(client, users, db_register2, users_index):
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.is_user_locked')
    res = client.post(url)
    assert res.status_code != 302

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_is_user_locked -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_is_user_locked(client,db_register_full_action, users):
    login(client=client, email=users[2]['email'])
    current_cache.delete("workflow_userlock_activity_5")
    url = url_for('weko_workflow.is_user_locked')

    # not exist cache
    res = client.get(url)
    assert res.status_code == 200
    assert json.loads(res.data) == {"is_open": False, "activity_id": ""}

    current_cache.set("workflow_userlock_activity_5","1")
    res = client.get(url)
    assert res.status_code == 200
    assert json.loads(res.data) == {"is_open": True, "activity_id": "1"}

    current_cache.delete("workflow_userlock_activity_5")


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_user_lock_activity_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_user_lock_activity_nologin(client,db_register2):
    url = url_for('weko_workflow.user_lock_activity', activity_id='1',_external=False)
    res = client.post(url)
    assert res.status_code == 302
    #assert res.location == url_for("security.login",next=url,_external=True)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_user_lock_activity_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index', [ i for i in range(7)])
def test_user_lock_activity_acl(client, users, db_register2, users_index):
    login(client=client, email=users[users_index]['email'])
    # 51991 case.06(user_lock_activity)
    url = url_for('weko_workflow.user_lock_activity', activity_id='1')
    res = client.post(url)
    assert res.status_code != 302


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_user_lock_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_user_lock_activity(client,db_register2, users, mocker):
    login(client=client, email=users[2]['email'])
    current_cache.delete("workflow_userlock_activity_5")
    mocker.patch("weko_workflow.views.validate_csrf_header")
    url = url_for('weko_workflow.user_lock_activity', activity_id='1')
    # 51991 case.01(user_lock_activity)
    # not exist cache
    res = client.post(url)
    assert res.status_code == 200
    assert json.loads(res.data) == {"code":200,"msg":"Success","err":"","activity_id":""}
    assert current_cache.get("workflow_userlock_activity_5") == "1"

    # exist cache
    res = client.post(url)
    assert res.status_code == 200
    assert json.loads(res.data) == {"code":200,"msg":"","err":"Opened","activity_id":"1"}
    assert current_cache.get("workflow_userlock_activity_5") == "1"

    current_cache.delete("workflow_userlock_activity_5")

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_user_lock_activity_empty_cache_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('activity_status, status_code', [
    (None, 200),
    (ActivityStatusPolicy.ACTIVITY_BEGIN, 200),
    (ActivityStatusPolicy.ACTIVITY_MAKING, 200),
    (ActivityStatusPolicy.ACTIVITY_CANCEL, 200)
])
def test_user_lock_activity_empty_cache_data(client,db_register, users, activity_status, status_code, mocker):
    """
    Test user_lock_activity when cache data is empty

    Args:
        client (fixture): cliant settings
        db_register (fixture): add FlowDefine, FlowAction, WorkFlow, Activity, ActivityAction, ActionFeedbackMail, ActivityHistory
        users (fixture): user settings
        activity_status (parametrize): set status
        status_code (parametrize): expect status code
        mocker (fixture): mocker
    """
    login(client=client, email=users[2]['email'])
    current_cache.delete("workflow_userlock_activity_5")
    mocker.patch("weko_workflow.views.validate_csrf_header")
    url = url_for('weko_workflow.user_lock_activity', activity_id='1')

    mock_activity = None
    if activity_status:
        mock_activity = MagicMock()
        mock_activity.activity_status = activity_status

    # 51991 case.02～05(user_lock_activity)
    with patch("weko_workflow.views.get_cache_data", return_value=""):
        with patch("weko_workflow.views.update_cache_data") as mock_update_cache_data:
            with patch("weko_workflow.views.WorkActivity.get_activity_by_id", return_value=mock_activity):
                # exist cache
                res = client.post(url)
                assert res.status_code == status_code
                assert json.loads(res.data) == {"code":status_code,"msg":"Success","err":"","activity_id":""}
                if activity_status in [None, ActivityStatusPolicy.ACTIVITY_BEGIN, ActivityStatusPolicy.ACTIVITY_MAKING]:
                    mock_update_cache_data.assert_called_once()
                else:
                    mock_update_cache_data.assert_not_called()

            current_cache.delete("workflow_userlock_activity_5")

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_user_lock_activity_raise_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_user_lock_activity_raise_error(client, users, db_register, mocker):
    login(client=client, email=users[2]['email'])
    current_cache.delete("workflow_userlock_activity_5")
    mocker.patch("weko_workflow.views.validate_csrf_header")
    url = url_for('weko_workflow.user_lock_activity', activity_id='1')

    with patch('weko_workflow.views.WorkActivity.get_activity_by_id', side_effect=SQLAlchemyError("Simulated DB error")):
        with pytest.raises(SQLAlchemyError):
            res = client.post(url)
            assert res.status_code == 500

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_user_unlock_activity_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_user_unlock_activity_nologin(client,db_register2):
    url = url_for('weko_workflow.user_unlock_activity', activity_id='1',_external=False)
    res = client.post(url)
    assert res.status_code == 302


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_user_unlock_activity_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index', [ i for i in range(7)])
def test_user_unlock_activity_acl(client,users,db_register2,users_index):
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.user_unlock_activity', activity_id='1')
    data = json.dumps({"is_opened": True})
    res = client.post(url,data=data)
    assert res.status_code != 302


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_user_unlock_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_user_unlock_activity(client,users,db_register2,mocker):
    url = url_for('weko_workflow.user_unlock_activity', activity_id='1')
    login(client=client, email=users[2]['email'])
    current_cache.set("workflow_userlock_activity_5","2")
    # is_opened is True
    data = json.dumps({"is_opened": True})
    res = client.post(url,data=data)
    assert res.status_code == 200
    assert json.loads(res.data) == {"code": 200, "msg": "User Unlock Success"}
    assert current_cache.get("workflow_userlock_activity_5") == None

    # is_opened is False
    data = json.dumps({"is_opened": False})
    res = client.post(url,data=data)
    assert res.status_code == 200
    assert json.loads(res.data) == {"code": 200, "msg": "Not unlock"}
    assert current_cache.get("workflow_userlock_activity_5") == None

def test_lock_activity_nologin(client,db_register2):
    """Test of lock activity."""
    url = url_for('weko_workflow.lock_activity', activity_id='1')
    input = {}

    # 51991 case.08(lock_activity)
    res = client.post(url, json=input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_lock_activity_users(client, users, users_index, status_code):
    """Test of lock activity."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.lock_activity', activity_id='1')
    input = {}

    with patch('weko_workflow.views.get_cache_data', return_value=""):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, json=input)
            assert res.status_code != 302

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_lock_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_lock_activity(client, users,db_register_full_action, mocker):
    """Test of lock activity."""
    mocker.patch("weko_workflow.views.validate_csrf_header")
    status_code = 200
    login(client=client, email=users[2]['email'])

    #regular
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}

    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, data=input)
            assert res.status_code == status_code
            assert json.loads(res.data) == {"code": 200, "err": "", "locked_by_email": "user@test.org", "locked_by_username": "", "locked_value": "1-1661748792565", "msg": "Success"}

    #locked value  is validate error
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': 1661748792565}

    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, data=input)
            assert res.status_code == status_code
            assert json.loads(res.data) == {"code": 200, "err": "Locked", "locked_by_email": "user@test.org", "locked_by_username": "", "locked_value": "1-1661748792565", "msg": ""}

    #lock cache is different
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}

    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792568"):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, data=input)
            assert res.status_code == status_code
            assert json.loads(res.data) == {"code": 200, "err": "Locked", "locked_by_email": "user@test.org", "locked_by_username": "", "locked_value": "1-1661748792568", "msg": ""}

    #action_handler is None
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}

    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, data=input)
            assert res.status_code == status_code
            assert json.loads(res.data) == {"code": 200, "err": "", "locked_by_email": "user@test.org", "locked_by_username": "", "locked_value": "1-1661748792565", "msg": "Success"}

    #activity_id is type error
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}

    # 51991 case.09(lock_activity)
    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.type_null_check',return_value=False):
            with patch('weko_workflow.views.update_cache_data'):
                res = client.post(url, data=input)
                assert res.status_code == 500
                assert json.loads(res.data) == {"code": -1, "msg": "argument error"}

    #request vaidate error
    # 51991 case.10(lock_activity)
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {}

    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            with patch("weko_workflow.views.LockSchema",side_effect=ValidationError("test error")):
                res = client.post(url, data=input)
                assert res.status_code == 500
                assert json.loads(res.data) == {"code": -1, "msg": "test error"}

    # locked_by_email, locked_by_username is not exist
    # 51991 case.11(lock_activity)
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}
    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            with patch("weko_workflow.views.get_account_info",return_value=(None,None)):
                res = client.post(url, data=input)
                assert res.status_code == 500
                assert json.loads(res.data) == {"code": -1, "msg": "can not get user locked"}

    # not exist action status is doing
    activity_action = ActivityAction.query.filter_by(
        activity_id="A-00000003-00000",
        action_id=1,
        action_order=1
    ).first()
    activity_action.action_status="F"
    db.session.merge(activity_action)
    db.session.commit()
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}
    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, data=input)
            assert res.status_code == status_code
            assert json.loads(res.data)  == {"code": 200, "err": "", "locked_by_email": "user@test.org", "locked_by_username": "", "locked_value": "1-1661748792565", "msg": "Success"}
    activity_action = ActivityAction.query.filter_by(
        activity_id="A-00000003-00000",
        action_id=1,
        action_order=1
    ).first()
    activity_action.action_status="M"
    db.session.merge(activity_action)
    db.session.commit()

    # not exist action_handler
    activity_action = ActivityAction.query.filter_by(
        activity_id="A-00000003-00000",
        action_id=1,
        action_order=1
    ).first()
    activity_action.action_handler=None
    db.session.merge(activity_action)
    db.session.commit()
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}
    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, data=input)
            assert res.status_code == status_code
            assert json.loads(res.data)  == {"code": 200, "err": "", "locked_by_email": "user@test.org", "locked_by_username": "", "locked_value": "1-1661748792565", "msg": "Success"}
    activity_action = ActivityAction.query.filter_by(
        activity_id="A-00000003-00000",
        action_id=1,
        action_order=1
    ).first()
    activity_action.action_handler=0
    db.session.merge(activity_action)
    db.session.commit()

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_lock_activity_set_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('activity_status, status_code', [
    (None, 200),
    (ActivityStatusPolicy.ACTIVITY_BEGIN, 200),
    (ActivityStatusPolicy.ACTIVITY_MAKING, 200),
    (ActivityStatusPolicy.ACTIVITY_CANCEL, 200)
])
def test_lock_activity_set_status(client, users,db_register, mocker, activity_status, status_code):
    """
    Test of lock activity return get_cache_data None.

    """
    mocker.patch("weko_workflow.views.validate_csrf_header")
    login(client=client, email=users[2]['email'])

    # 51991 case.04～07(lock_activity)
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    locked_value =  '1-1661748792565'
    input = {'locked_value': locked_value}
    mock_account_info = ("user@test.org", "Test User")
    mock_activity = None
    if activity_status:
        mock_activity = MagicMock()
        mock_activity.activity_status = activity_status

    with patch("flask_login.utils._get_user",return_value=users[2]["obj"]):
        with patch('weko_workflow.views.get_cache_data', return_value=''):
            with patch('weko_workflow.views.get_account_info', return_value=mock_account_info):
                with patch('weko_workflow.views.update_cache_data') as mock_update_cache_data:
                    with patch('weko_workflow.views.WorkActivity.get_activity_by_id', return_value=mock_activity):
                        res = client.post(url, data=input)
                        assert res.status_code == status_code
                        response_data = json.loads(res.data)

                        assert response_data["msg"] == "Success"
                        if activity_status in [None, ActivityStatusPolicy.ACTIVITY_BEGIN, ActivityStatusPolicy.ACTIVITY_MAKING]:
                            mock_update_cache_data.assert_called_once()
                        else:
                            mock_update_cache_data.assert_not_called()

def test_lock_activity_raise_error(client, users,db_register):
    login(client=client, email=users[2]['email'])

    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input_data = {'locked_value': '1-1661748792565'}

    with patch('weko_workflow.views.WorkActivity.get_activity_by_id', side_effect=SQLAlchemyError("Simulated DB error")):
        with pytest.raises(SQLAlchemyError):
            res = client.post(url, json=input_data)
            assert res.status_code == 500
            data = json.loads(res.data)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_unlock_activity_acl_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_unlock_activity_acl_nologin(client,db_register2):
    """Test of unlock activity."""
    url = url_for('weko_workflow.unlock_activity', activity_id='1')
    input = {'locked_value':'1-1661748792565'}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == 'http://test_server.localdomain/login/?next=%2Fworkflow%2Factivity%2Funlock%2F1'


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_unlock_activity_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_unlock_activity_acl_users(client, users, users_index, status_code):
    """Test of unlock activity."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.unlock_activity', activity_id='1')
    input = {'locked_value':'1-1661748792565'}

    with patch('weko_workflow.views.get_cache_data', return_value=""):
        res = client.post(url, json=input)
        assert res.status_code != 302


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_unlock_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_unlock_activity(client, users, db_register_full_action, users_index, status_code):
    current_cache.delete("workflow_locked_activity_1")
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.unlock_activity', activity_id='1')
    input = {'locked_value':'1-1661748792565'}

    #check_flgの分岐テスト
    with patch('weko_workflow.views.type_null_check', return_value=False):
        res = client.post(url, json=input)
        data = json.loads(res.data.decode("utf-8"))
        assert res.status_code== 400
        assert data["code"] == -1
        assert data["msg"] == 'arguments error'

    #cur_locked_valが空文字の場合
    res = client.post(url, json=input)
    data = json.loads(res.data.decode("utf-8"))
    assert res.status_code==status_code
    assert data["code"] == 200
    assert data["msg"] == 'Not unlock'

    #locked_valueが空でなく、cur_locked_valと一致する場合
    current_cache.set("workflow_locked_activity_1",'1-1661748792565')
    res = client.post(url, json=input)
    data = json.loads(res.data.decode("utf-8"))
    assert res.status_code==status_code
    assert data["code"] == 200
    assert data["msg"] == 'Unlock success'

    #ValidationErrorの分岐テスト
    input = {}
    res = client.post(url, json=input)
    data = json.loads(res.data.decode("utf-8"))
    assert res.status_code== 400
    assert data["code"] == -1
    assert data["msg"] == "{'locked_value': ['Missing data for required field.']}"

    current_cache.delete("workflow_locked_activity_1")


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_check_approval_acl_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_approval_acl_nologin(client,db_register2):
    """Test of check approval."""
    url = url_for('weko_workflow.check_approval', activity_id='1')

    res = client.get(url)
    assert res.status_code == 302
    assert res.location == 'http://test_server.localdomain/login/?next=%2Fworkflow%2Fcheck_approval%2F1'


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_check_approval_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_check_approval_acl_users(client, users, users_index, status_code):
    """Test of check approval."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.check_approval', activity_id='1')
    response = {
        'check_handle': -1,
        'check_continue': -1,
        'error': 1
    }
    with patch('weko_workflow.views.check_continue', return_value=response):
        res = client.get(url)
        assert res.status_code != 302


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_check_approval -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_check_approval(client, users, db_register_full_action, users_index, status_code):
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.check_approval', activity_id='1')
    response = {
        'check_handle': -1,
        'check_continue': -1,
        'error': 1
    }

    #check_flgの分岐テスト
    with patch('weko_workflow.views.type_null_check', return_value=False):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code== 400
        assert data["code"] == -1
        assert data["msg"] == 'arguments error'

    with patch('weko_workflow.views.check_continue', side_effect=Exception):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code==status_code
        assert data['check_handle'] == -1
        assert data['check_continue'] == -1
        assert data['error'] == -1

    with patch('weko_workflow.views.check_continue', return_value=response):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code==status_code
        assert data['check_handle'] == -1
        assert data['check_continue'] == -1
        assert data['error'] == 1


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_get_feedback_maillist_acl_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_feedback_maillist_acl_nologin(client,db_register2):
    """Test of get feedback maillist."""
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='1')

    res = client.get(url)
    assert res.status_code == 302
    assert res.location == 'http://test_server.localdomain/login/?next=%2Fworkflow%2Fget_feedback_maillist%2F1'


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_get_feedback_maillist_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_get_feedback_maillist_acl_users(client, users, users_index, status_code):
    """Test of get feedback maillist."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='1')

    res = client.get(url)
    assert res.status_code != 302


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_get_feedback_maillist -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    #(1, 200),
    #(2, 200),
    #(3, 200),
    #(4, 200),
    #(5, 200),
    #(6, 200),
])
def test_get_feedback_maillist(client, users, db_register_full_action, users_index, status_code):
    login(client=client, email=users[users_index]['email'])

    action_feedback_mail = db_register_full_action['action_feedback_mail']
    action_feedback_mail_1 = db_register_full_action['action_feedback_mail1']
    action_feedback_mail_2 = db_register_full_action['action_feedback_mail2']

    print(action_feedback_mail)
    print(vars(action_feedback_mail))

    url = url_for('weko_workflow.get_feedback_maillist', activity_id='1')
    with patch('weko_workflow.views.type_null_check', return_value=False):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code== 400
        assert data["code"] == -1
        assert data["msg"] == 'arguments error'

    #戻り値jsonify(code=0, msg=_('Empty!'))の分岐テスト
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='1')
    res = client.get(url)
    data = response_data(res)
    assert res.status_code==status_code
    assert data['code'] == 0
    assert data['msg'] == 'Empty!'

    #戻り値jsonify(code=1,msg=_('Success'),data=mail_list)の分岐テスト
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='4')
    res = client.get(url)
    data = response_data(res)
    assert res.status_code==status_code
    assert data['code'] == 1
    assert data['msg'] == 'Success'
    assert data['data'] == [{"author_id": "", "email": "test@org"}]

    url = url_for('weko_workflow.get_feedback_maillist', activity_id='5')
    res = client.get(url)
    data = response_data(res)
    assert res.status_code==status_code
    assert data['code'] == 1
    assert data['msg'] == 'Success'
    assert data['data'] == [{"author_id": "1", "email": "test@org"}]

    url = url_for('weko_workflow.get_feedback_maillist', activity_id='6')
    res = client.get(url)
    data = response_data(res)
    assert res.status_code==status_code
    assert data['code'] == 1
    assert data['msg'] == 'Success'
    assert data['data'] == []

    #戻り値jsonify(code=-1, msg=_('Error'))の分岐テスト
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='3')
    with patch('weko_workflow.views.WorkActivity.get_action_feedbackmail', side_effect=Exception):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code == 400
        assert data['code'] == -1
        assert data['msg'] == 'Error'

    url = url_for('weko_workflow.get_feedback_maillist', activity_id='7')
    res = client.get(url)
    data = response_data(res)
    #mail_list = db_register['action_feedback_mail3'].feedback_maillist
    assert res.status_code == 400
    assert data['code'] == -1
    assert data['msg'] == 'mail_list is not list'


@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    #(1, 200),
    #(2, 200),
    #(3, 200),
    #(4, 200),
    #(5, 200),
    #(6, 200),
])
# def get_request_maillist(activity_id='0')
#.tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_get_request_maillist -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_request_maillist(client, users, users_index, status_code, mocker):
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.get_request_maillist', activity_id='1')
    with patch('weko_workflow.views.type_null_check', return_value=False):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code== 400
        assert data["code"] == -1
        assert data["msg"] == 'arguments error'

    #戻り値jsonify(code=0, msg=_('Empty!'))の分岐テスト
    with patch('weko_workflow.views.WorkActivity.get_activity_request_mail', return_value=None):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code==status_code
        assert data['code'] == 0
        assert data['msg'] == 'Empty!'

    #ActivityRequestMail内のmaillistがlist型でない
    with patch('weko_workflow.views.WorkActivity.get_activity_request_mail', return_value=ActivityRequestMail(request_maillist={})):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code == 400
        assert data['code'] == -1
        assert data['msg'] == 'mail_list is not list'

    #ActivityRequestMail内のmaillistにauthor_idがあって、emailがない。
    request_maillist =ActivityRequestMail(request_maillist=[{'author_id':"1", 'email':""}], display_request_button=True)
    with patch('weko_workflow.views.WorkActivity.get_activity_request_mail', return_value=request_maillist):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code == 200
        assert data['code'] == 1
        assert data['msg'] == 'Success'
        assert data['request_maillist'] == []

    #ActivityRequestMail内のmaillistにemailがあって、author_idがない。
    request_maillist =ActivityRequestMail(request_maillist=[{'author_id':"", 'email':"test@test.org"}], display_request_button=True)
    with patch('weko_workflow.views.WorkActivity.get_activity_request_mail', return_value=request_maillist):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code == 200
        assert data['code'] == 1
        assert data['msg'] == 'Success'
        assert data['request_maillist'] == [{'author_id':"", 'email':"test@test.org"}]

    #ActivityRequestMail内のmaillistにauthor_idとemailがあるが、author_idで登録されたAuthorsが見つからない。
    request_maillist =ActivityRequestMail(request_maillist=[{'author_id':1, 'email':"test@test.org"}], display_request_button=True)
    with patch('weko_workflow.views.WorkActivity.get_activity_request_mail', return_value=request_maillist):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code == 200
        assert data['code'] == 1
        assert data['msg'] == 'Success'
        assert data['request_maillist'] == []

    #ActivityRequestMail内のmaillistにauthor_idとemailがあり、author_idで登録されたAuthorsが見つかる。
    request_maillist =ActivityRequestMail(request_maillist=[{'author_id':1, 'email':"test@test.org"}], display_request_button=True)
    with patch('weko_workflow.views.WorkActivity.get_activity_request_mail', return_value = request_maillist):
        mocker.patch("weko_workflow.views.Authors.get_emails_by_id", return_value = ["test@test.org"])
        res = client.get(url)
        data = response_data(res)
        assert res.status_code == 200
        assert data['code'] == 1
        assert data['msg'] == 'Success'
        assert data['request_maillist'] == [{'author_id':1, 'email':"test@test.org"}]

    # 1つのauthor_idに対して2つのemailが存在する
    request_maillist =ActivityRequestMail(
        request_maillist=[{'author_id':1, 'email':"test@test.org"}, {'author_id':1, 'email':"test2@test.org"}], display_request_button=True)
    with patch('weko_workflow.views.WorkActivity.get_activity_request_mail', return_value = request_maillist):
        mocker.patch("weko_workflow.views.Authors.get_emails_by_id", return_value = ["test@test.org", "test2@test.org"])
        res = client.get(url)
        data = response_data(res)
        assert res.status_code == 200
        assert data['code'] == 1
        assert data['msg'] == 'Success'
        assert data['request_maillist'] == [{'author_id':1, 'email':"test@test.org"}, {'author_id':1, 'email':"test2@test.org"}]

    #Errorが起きた場合
    request_maillist =ActivityRequestMail(request_maillist=[{'author_id':1, 'email':"test@test.org"}])
    with patch('weko_workflow.views.WorkActivity.get_activity_request_mail', return_value = request_maillist):
        mocker.patch("weko_workflow.views.Authors.get_emails_by_id", return_value = ["test@test.org"])
        res = client.get(url)
        data = response_data(res)
        assert res.status_code == 400
        assert data['code'] == -1

    ActivityRequestMail(
            id = 3,
            activity_id = 3,
            display_request_button = True,
            request_maillist = [{"email":"not_user","author_id":""},
                                {"email":"user@test.org","author_id":""},
                                {"email":"contributor@test.org","author_id":""}]
    )
    
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    #(1, 200),
    #(2, 200),
    #(3, 200),
    #(4, 200),
    #(5, 200),
    #(6, 200),
])
# def get_item_application(activity_id='0')
#.tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_get_item_application -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_item_application(client, users, users_index, status_code, mocker):
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.get_item_application', activity_id='1')

    # activity_idがstrでないエラー
    with patch('weko_workflow.views.type_null_check', return_value=False):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code== 400
        assert data["code"] == -1
        assert data["msg"] == 'arguments error'

    #戻り値jsonify(code=0, msg=_('Empty!'))の分岐テスト
    with patch('weko_workflow.views.WorkActivity.get_activity_item_application', return_value=None):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code==status_code
        assert data['code'] == 0
        assert data['msg'] == 'Empty!'

    # 正常系
    item_application = ActivityItemApplication(activity_id=1, item_application={"workflow":1, "terms":"term_free", "termsDescription":"test"}, display_item_application_button=True)
    with patch('weko_workflow.views.WorkActivity.get_activity_item_application', return_value=item_application):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code==status_code
        assert data['code'] == 1
        assert data["item_application"] == {"workflow":1, "terms":"term_free", "termsDescription":"test"}

    # エラー
    with patch('weko_workflow.views.WorkActivity.get_activity_item_application', side_effect=Exception()):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code == 400
        assert data['code'] == -1
        assert data['msg'] == "Error"

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_save_activity_acl_nologin -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_save_activity_acl_nologin(client,db_register2):
    """Test of save activity."""
    url = url_for('weko_workflow.save_activity')
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_ids":[]}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == 'http://TEST_SERVER.localdomain/login/?next=%2Fworkflow%2Fsave_activity_data'


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_save_activity_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_save_activity_acl_users(client, users, users_index, status_code):
    """Test of save activity."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.save_activity')
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_ids":[]}
    with patch('weko_workflow.views.save_activity_data'):
        res = client.post(url, json=input)
        assert res.status_code != 302

#.tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_save_activity_acl_guestlogin -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
#save_activityは@login_required_customizeなのでguestuserloginのテストも必要
def test_save_activity_acl_guestlogin(guest,db_register2):
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_ids":[]}
    url = url_for('weko_workflow.save_activity')

    res = guest.post(url, json=input)
    assert res.status_code != 302


#.tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_save_activity -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_save_activity(client, users, db_register_full_action, users_index, status_code):
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.save_activity')

    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_ids":'hogehoge'}
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code== 400
    assert data["code"] == -1
    assert data["msg"] == "{'shared_user_ids': ['Not a valid list.']}"

    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_ids":[]}
    with patch('weko_workflow.views.save_activity_data'):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code==status_code
        assert data["success"] == True
        assert data["msg"] == ""

    with patch('weko_workflow.views.save_activity_data', side_effect=Exception("test error")):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code==status_code
        assert data["success"] == False
        assert data["msg"] == "test error"


#.tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_save_activity_guestlogin -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
# guestuserでの機能テスト
def test_save_activity_guestlogin(guest,db_register2):
    url = url_for('weko_workflow.save_activity')

    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_ids":'hogehoge'}
    res = guest.post(url, json=input)
    data = response_data(res)
    assert res.status_code== 400
    assert data["code"] == -1
    assert data["msg"] == "{'shared_user_ids': ['Not a valid list.']}"

    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_ids":[]}
    with patch('weko_workflow.views.save_activity_data'):
        res = guest.post(url, json=input)
        data = response_data(res)
        assert res.status_code==200
        assert data["success"] == True
        assert data["msg"] == ""

    with patch('weko_workflow.views.save_activity_data', side_effect=Exception("test error")):
        res = guest.post(url, json=input)
        data = response_data(res)
        assert res.status_code==200
        assert data["success"] == False
        assert data["msg"] == "test error"

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_verify_deletion -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_workflow/.tox/c1/tmp
def test_verify_deletion(client, db, db_register2,db_register_full_action,users):
    flow_id = db_register_full_action["flow_define"].id
    def prepare_activity(act_id, recid, with_item=False, is_deleted=False):
        if with_item:
            record_metadata = {"path":["1"],"recid":recid,"title":["title"],"_deposit":{"id":recid}}
            item_metadata = {"id":recid,"title":"title"}
            record_id, depid, record, item, parent, doi, deposit = create_record(record_metadata, item_metadata)
            if is_deleted:
                parent.status=PIDStatus.DELETED
                record_id.status=PIDStatus.DELETED
                depid.status=PIDStatus.DELETED
                db.session.merge(parent)
                db.session.merge(record_id)
                db.session.merge(depid)
            db.session.commit()
            if with_item:
                recid_id = record_id.object_uuid
                pid=PersistentIdentifier.query.filter_by(pid_type="recid", object_uuid=recid_id).one()
        activity = Activity(
            activity_id=act_id,workflow_id=1, flow_id=flow_id,action_id=1, activity_login_user=1,
            activity_update_user=1,title="title" if with_item else None,action_order=1,
            item_id=record_id.object_uuid if with_item else None,
            activity_start=datetime.strptime('2200/01/11 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
        )
        db.session.add(activity)
        db.session.commit()

    login(client=client, email=users[2]['email'])

    # not exist item_id
    activity_id = "A-22000111-00001"
    prepare_activity(activity_id,"100")
    url = url_for("weko_workflow.verify_deletion",activity_id=activity_id)
    res = client.get(url)
    assert res.status_code == 200
    assert json.loads(res.data) == {"code": 200, "is_deleted": False}

    # exist item_id, not deleted
    activity_id = "A-22000111-00002"
    prepare_activity(activity_id,"101",with_item=True)
    url = url_for("weko_workflow.verify_deletion",activity_id=activity_id)
    res = client.get(url)
    assert res.status_code == 200
    assert json.loads(res.data) == {"code": 200, "is_deleted": False}

    # exist item_id, deleted
    activity_id = "A-22000111-00003"
    prepare_activity(activity_id,"102", with_item=True, is_deleted=True)
    url = url_for("weko_workflow.verify_deletion",activity_id=activity_id)
    res = client.get(url)
    assert res.status_code == 200
    assert json.loads(res.data) == {"code": 200, "is_deleted": True}

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_activity_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_workflow/.tox/c1/tmp
def test_display_activity_nologin(client,db_register2,mocker):
    """Test of display activity."""
    adminsetting = {"display_request_form": True}
    mocker.patch("weko_workflow.views.AdminSettings.get",return_value = adminsetting)
    url = url_for('weko_workflow.display_activity', activity_id='1')
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_activity_guestlogin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_workflow/.tox/c1/tmp
def test_display_activity_guestlogin(app, db_register, guest, mocker):
    """Test of display activity."""
    adminsetting = {"display_request_form": True}
    mocker.patch("weko_workflow.views.AdminSettings.get",return_value = adminsetting)
    url = url_for('weko_workflow.display_activity', activity_id='1')
    input = {}

    activity_detail = Activity.query.filter_by(activity_id='1').one_or_none()
    cur_action = activity_detail.action
    action_endpoint = cur_action.action_endpoint
    action_id = cur_action.id
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

    workflow_detail = WorkFlow.query.filter_by(id=1).one_or_none()
    owner_id = 1
    shared_user_ids = []
    mock_render_template = MagicMock(return_value=jsonify({}))
    with patch('weko_workflow.views.get_activity_display_info',
            return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.check_authority_action'):
            with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
                    return_value=(roles, action_users)):
                with patch('weko_workflow.views.render_template', mock_render_template):
                    res = guest.post(url, json=input)
                    assert res.status_code == 200
                    mock_render_template.assert_called()


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_activity_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_display_activity_users(client, users, db_register, users_index, status_code, mocker):
    """
    Test of display activity.
    Expected: users[0]: AssertionError
    """
    adminsetting = {"display_request_form": True}
    mocker.patch("weko_workflow.views.AdminSettings.get",return_value = adminsetting)
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.display_activity', activity_id='1')
    input = {}

    activity_detail = Activity.query.filter_by(activity_id='1').one_or_none()
    cur_action = activity_detail.action
    action_endpoint = cur_action.action_endpoint
    action_id = cur_action.id
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

    workflow_detail = WorkFlow.query.filter_by(id=1).one_or_none()
    owner_id = 1
    shared_user_ids = []
    mock_render_template = MagicMock(return_value=jsonify({}))
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.check_authority_action'):
            with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
                       return_value=(roles, action_users)):
                with patch('weko_workflow.views.render_template', mock_render_template):
                    res = client.post(url, json=input)
                    mock_render_template.assert_called()

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_display_activity(client, users, db_register,mocker,redis_connect,without_remove_session, app):
    def del_session():
        with client.session_transaction() as session:
            if session.get('activity_info'):
                del session['activity_info']
            if session.get('itemlogin_id'):
                del session['itemlogin_id']
            if session.get('itemlogin_activity'):
                del session['itemlogin_activity']
            if session.get('itemlogin_item'):
                del session['itemlogin_item']
            if session.get('itemlogin_steps'):
                del session['itemlogin_steps']
            if session.get('itemlogin_action_id'):
                del session['itemlogin_action_id']
            if session.get('itemlogin_cur_step'):
                del session['itemlogin_cur_step']
            if session.get('itemlogin_record'):
                del session['itemlogin_record']
            if session.get('itemlogin_res_check'):
                del session['itemlogin_res_check']
            if session.get('itemlogin_pid'):
                del session['itemlogin_pid']
            if session.get('itemlogin_community_id'):
                del session['itemlogin_community_id']
    login(client=client, email=users[2]['email'])
    adminsetting = {"display_request_form": True}
    mocker.patch("weko_workflow.views.AdminSettings.get",return_value = adminsetting)

    workflow_detail = WorkFlow.query.filter_by(id=1).one_or_none()
    mock_render_template = MagicMock(return_value=jsonify({}))

    activity_detail = Activity.query.filter_by(activity_id='A-00000001-10001').one_or_none()
    activity_detail.extra_info = {'related_title': 'related_title_1', 'guest_mail': 'user@example.com'}

    cur_action = activity_detail.action
    action_endpoint = 'item_login'
    action_id = cur_action.id
    histories = 1
    item_metadata = ItemMetadata()
    item_metadata.id = '37075580-8442-4402-beee-05f62e6e1dc2'
    # item_metadata = {'created':datetime.strptime("2022-09-22 05:09:54.677307", "%Y-%m-%d %H:%M:%S.%f"),'updated':datetime.strptime("2022-09-22 05:09:54.677307", "%Y-%m-%d %H:%M:%S.%f"),
    #                 'id':'37075580-8442-4402-beee-05f62e6e1dc2','item_type_id':15,'json': {"id": "1", "pid": {"type": "depid", "value": "1", "revision_id": 0}, "lang": "ja", "owner": "1", "title": "title", "owners": [1], "status": "published", "$schema": "/items/jsonschema/15", "pubdate": "2022-08-20", "created_by": 1, "owners_ext": {"email": "wekosoftware@nii.ac.jp", "username": "", "displayname": ""}, "shared_user_ids": [], "item_1617186331708": [{"subitem_1551255647225": "ff", "subitem_1551255648112": "ja"}], "item_1617258105262": {"resourceuri": "http://purl.org/coar/resource_type/c_5794", "resourcetype": "conference paper"}}
    #                 ,'version_id':3}
    item = None
    steps = 1
    temporary_comment = 1


    test_pid = PersistentIdentifier()
    test_pid.pid_value = '1'
    test_comm= Community()
    test_comm.id = 'test'
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }

    identifier = {'action_identifier_select': '',
                'action_identifier_jalc_doi': '',
                'action_identifier_jalc_cr_doi': '',
                'action_identifier_jalc_dc_doi': '',
                'action_identifier_ndl_jalc_doi': ''
                }


    template_url = "weko_items_ui/iframe/item_edit.html"
    need_file = False
    need_billing_file = False
    record = {}
    json_schema = "test"
    schema_form = "test"
    item_save_uri = ""
    files = []
    endpoints = {}
    need_thumbnail = False
    files_thumbnail = []
    allow_multi_thumbnail = False

    license_list = []
    record_detail_alt = dict(
        record=None,
        files=None,
        files_thumbnail=None,
        pid=None)
    
    owner_id = 1
    shared_user_ids = []


    mocker.patch('weko_workflow.api.WorkActivity.get_activity_action_role',
                return_value=(roles, action_users))
    mocker.patch('weko_workflow.views.WorkActivity.get_action_identifier_grant',return_value=identifier)
    mocker.patch('weko_workflow.views.check_authority_action',return_value=1)
    mocker.patch('weko_workflow.views.set_files_display_type',return_value=[])
    mocker.patch('weko_workflow.views.WorkActivity.get_action_journal')
    mocker.patch('weko_workflow.views.get_files_and_thumbnail',return_value=(["test1","test2"],files_thumbnail))
    mocker.patch('weko_workflow.views.get_usage_data')
    mocker.patch('weko_workflow.views.is_usage_application_item_type')
    mocker.patch('weko_theme.views.get_design_layout',return_value=(None,True))
    mocker.patch('weko_workflow.views.RedisConnection.connection',return_value=redis_connect)

    #regular
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    item = None
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #activity_id is not String
    url = url_for('weko_workflow.display_activity', activity_id=1001)
    input = {}
    item = None
    mock_render_template_error = MagicMock(return_value=jsonify({"error":"can not get data required for rendering"}))

    with patch('weko_workflow.views.get_activity_display_info',
            return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.type_null_check',return_value=False):
            with patch('weko_workflow.views.item_login',return_value=(template_url,
                    need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                    files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
                with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                    with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                        with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                            with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                                with patch('weko_workflow.views.render_template', mock_render_template_error):
                                    res = client.post(url, query_string=input)
                                    mock_render_template_error.assert_called()

    #activity_id is include "?"
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001?hoge')
    input = {}
    #action_endpoint = cur_action.action_endpoint
    activity_detail.extra_info = {}
    activity_detail.activity_id = 'A-00000001-10001'
    activity_detail.action_order = 6
    workflow_detail.itemtype_id = 1
    activity_detail.action_id = 1
    cur_action.action_version = '1.0.0'
    item = None
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #get_activity_display_info is include "None object"
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = None
    activity_detail.extra_info = {}
    activity_detail.activity_id = 'A-00000001-10001'
    activity_detail.action_order = 6
    workflow_detail.itemtype_id = 1
    activity_detail.action_id = 1
    cur_action.action_version = '1.0.0'
    with patch('weko_workflow.views.get_activity_display_info',
            return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #action_endpoint is identifier_grant and item is not None
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'identifier_grant'
    item = item_metadata
    with patch('weko_workflow.views.get_activity_display_info',
            return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #action_endpoint is item_login and activity is None
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10002')
    input = {}
    action_endpoint = 'item_login'
    with patch('weko_workflow.views.get_activity_display_info',
            return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #template_url is None
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = None
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #Json_schema is None
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = None
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #action_endpoint is identifier_grant and community is not root index
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {'community': 'test'}
    action_endpoint = 'identifier_grant'
    item = item_metadata
    with patch('weko_workflow.views.get_activity_display_info',
            return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,dict(test="test"))):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    # not identifier_setting
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {'community': 'test'}
    action_endpoint = 'identifier_grant'
    item = item_metadata
    with patch('weko_workflow.views.get_activity_display_info',
            return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,dict(test="test"))):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                with patch("weko_workflow.views.get_identifier_setting", return_value=None):
                                    res = client.post(url, query_string=input)
                                    mock_render_template.assert_called()

    #action_endpoint is identifier_grant and community is not root index
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {'community': 'test'}
    action_endpoint = 'item_login'
    item = item_metadata
    with patch('weko_workflow.views.get_activity_display_info',
            return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record'):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #json_schema is not None
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    with patch('weko_workflow.views.get_activity_display_info',
            return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #item is not None
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #action_endpoint is item_link
    #test No.3 (W2023-22 3(4))
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_link'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.ItemLink.get_item_link_info'):
            with patch('weko_workflow.views.item_login',return_value=(template_url,
                    need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                    files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
                with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                    with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                        with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                            with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                                with patch('weko_workflow.views.render_template', mock_render_template):
                                    res = client.post(url, query_string=input)
                                    mock_render_template.assert_called()

    #action_endpoint is item_login
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata
    del_session()
    with client.session_transaction() as session:
        assert "itemlogin_id" not in session
    # locked_value is not existed
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.ItemLink.get_item_link_info'):
            with patch('weko_workflow.views.item_login',return_value=(template_url,
                    need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                    files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
                with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                    with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                        with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                            with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                                with patch('weko_workflow.views.render_template', mock_render_template):
                                    res = client.post(url, query_string=input)
                                    mock_render_template.assert_called()
                                    with client.session_transaction() as session:
                                        assert "itemlogin_id" in session
                                        assert "activity_info" in session

    # locked_value is existed
    del_session()
    with client.session_transaction() as session:
        assert "itemlogin_id" not in session
    current_cache.set("workflow_userlock_activity_5","A-00000001-10001")
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.ItemLink.get_item_link_info'):
            with patch('weko_workflow.views.item_login',return_value=(template_url,
                    need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                    files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
                with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                    with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                        with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                            with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                                with patch('weko_workflow.views.render_template', mock_render_template):
                                    res = client.post(url, query_string=input)
                                    mock_render_template.assert_called()
                                    with client.session_transaction() as session:
                                        assert "itemlogin_id" not in session
                                        assert "activity_info" not in session
    current_cache.delete("workflow_userlock_activity_5")

    #raise PIDDeletedError
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',side_effect=PIDDeletedError('test','test')):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                #mock_render_template.assert_called()

    #raise PIDDoesNotExistError
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',side_effect=PIDDoesNotExistError('test','test')):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #raise Exception
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',side_effect=Exception()):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #approval record is not None
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,True)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #license_list is None
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=None):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #record_detail_alt is None
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=None):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {'community': 'test'}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata
    class MockUser:
        id = 0
    mock_user = MagicMock()
    mock_user.id = 0
    owner_id = 1
    shared_user_ids = []
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, None, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=None):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=None):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                with patch("flask_login.utils._get_user",return_value=mock_user):
                                    res = client.post(url, query_string=input)
                                    mock_render_template.assert_called()
    
    # action_endpoint is approval
    # test No.1 (W2023-22 3(4))
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'approval'
    json_schema = "test"
    item = item_metadata
    workflow_detail.open_restricted = True
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.ItemLink.get_item_link_info'):
            with patch('weko_workflow.views.item_login',return_value=(template_url,
                    need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                    files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
                with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                    with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                        with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                            with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                                with patch('weko_workflow.views.render_template', mock_render_template):
                                    res = client.post(url, query_string=input)
                                    mock_render_template.assert_called()

    #action_endpoint is approval
    #test No.2 (W2023-22 3(4))
    mocker.patch("weko_workflow.views.AdminSettings.get",return_value = True)
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'approval'
    json_schema = "test"
    item = item_metadata
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.ItemLink.get_item_link_info'):
            with patch('weko_workflow.views.item_login',return_value=(template_url,
                    need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                    files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
                with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                    with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                        with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                            with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                                with patch('weko_workflow.views.render_template', mock_render_template):
                                    res = client.post(url, query_string=input)
                                    mock_render_template.assert_called()

    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    mocker.patch("weko_workflow.views.AdminSettings.get",return_value = False)
    input = {}
    #action_endpoint = cur_action.action_endpoint
    activity_detail.extra_info = {"record_id":"100"}
    activity_detail.activity_id = 'A-00000001-10001'
    action_endpoint = 'end_action'
    cur_action.action_version = '1.0.0'
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                with patch('weko_workflow.views.WekoRecord.get_record_by_pid', return_value=None):
                                    res = client.post(url, query_string=input)
                                    mock_render_template.assert_called()

    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    mocker.patch("weko_workflow.views.AdminSettings.get",return_value = False)
    input = {}
    #action_endpoint = cur_action.action_endpoint
    activity_detail.extra_info = {"record_id":"100"}
    activity_detail.activity_id = 'A-00000001-10001'
    action_endpoint = 'end_action'
    cur_action.action_version = '1.0.0'
    mock_record = MagicMock()
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                with patch('weko_workflow.views.WekoRecord.get_record_by_pid', return_value=mock_record):
                                    with patch("weko_workflow.views.url_for", return_value = 'records/100'):
                                        res = client.post(url, query_string=input)
                                        mock_render_template.assert_called()


# def display_activity(activity_id="0")
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_activity_1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_display_activity_1(client, users_1, db_register_1, mocker, redis_connect):
    def del_session():
        with client.session_transaction() as session:
            if session.get('activity_info'):
                del session['activity_info']
            if session.get('itemlogin_id'):
                del session['itemlogin_id']
            if session.get('itemlogin_activity'):
                del session['itemlogin_activity']
            if session.get('itemlogin_item'):
                del session['itemlogin_item']
            if session.get('itemlogin_steps'):
                del session['itemlogin_steps']
            if session.get('itemlogin_action_id'):
                del session['itemlogin_action_id']
            if session.get('itemlogin_cur_step'):
                del session['itemlogin_cur_step']
            if session.get('itemlogin_record'):
                del session['itemlogin_record']
            if session.get('itemlogin_res_check'):
                del session['itemlogin_res_check']
            if session.get('itemlogin_pid'):
                del session['itemlogin_pid']
            if session.get('itemlogin_community_id'):
                del session['itemlogin_community_id']
    # ユーザー１でログイン
    login(client=client, email=users_1[0]['email'])

    workflow_detail = WorkFlow.query.filter_by(id=1).one_or_none()
    mock_render_template = MagicMock(return_value=jsonify({}))

    activity_detail = Activity.query.filter_by(activity_id='A-00000001-00005').one_or_none()
    #activity_detail = Activity.query.filter_by(activity_id='1').one_or_none()
    cur_action = activity_detail.action
    action_endpoint = 'item_login'
    #action_endpoint = cur_action.action_endpoint
    action_id = cur_action.id
    histories = 1
    item_metadata = ItemMetadata()
    item_metadata.id = '37075580-8442-4402-beee-05f62e6e1dc2'

    steps = 1
    temporary_comment = 1

    test_pid = PersistentIdentifier()
    test_pid.pid_value = '100.0'

    test_comm= Community()
    test_comm.id = 'test'
 
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }

    identifier = {'action_identifier_select': '',
                'action_identifier_jalc_doi': '',
                'action_identifier_jalc_cr_doi': '',
                'action_identifier_jalc_dc_doi': '',
                'action_identifier_ndl_jalc_doi': ''
                }


    template_url = "weko_items_ui/iframe/item_edit.html"
    need_file = False
    need_billing_file = False
    record = {}
    json_schema = "test"
    schema_form = "test"
    item_save_uri = ""
    files = []
    endpoints = {}
    need_thumbnail = False
    files_thumbnail = []
    allow_multi_thumbnail = False

    license_list = []
    record_detail_alt = dict(
        record=None,
        files=None,
        files_thumbnail=None,
        pid=None)

    mocker.patch('weko_workflow.api.WorkActivity.get_activity_action_role',
                return_value=(roles, action_users))
    mocker.patch('weko_workflow.views.WorkActivity.get_action_identifier_grant',return_value=identifier)
    mocker.patch('weko_workflow.views.check_authority_action',return_value=1)
    mocker.patch('weko_workflow.views.set_files_display_type',return_value=[])
    mocker.patch('weko_workflow.views.WorkActivity.get_action_journal')
    mocker.patch('weko_workflow.views.get_files_and_thumbnail',return_value=(["test1","test2"],files_thumbnail))
    mocker.patch('weko_workflow.views.get_usage_data')
    mocker.patch('weko_workflow.views.is_usage_application_item_type')
    mocker.patch('weko_theme.views.get_design_layout',return_value=(None,True))
    mocker.patch('weko_workflow.views.RedisConnection.connection',return_value=redis_connect)

    #regular
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-00005')
    input = {}
    action_endpoint = cur_action.action_endpoint
    item = item_metadata
    owner_id = 1
    shared_user_ids = [{'user':2}]
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #activity_id is not String
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = cur_action.action_endpoint
    item = None

    with patch('weko_workflow.views.get_activity_display_info',
            return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.type_null_check',return_value=False):
            with patch('weko_workflow.views.item_login',return_value=(template_url,
                    need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                    files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
                with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                    with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                        with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                            with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                                with patch('weko_workflow.views.render_template', mock_render_template):
                                    res = client.post(url, query_string=input)
                                    mock_render_template.assert_called()

    #activity_id is include "?"
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-?10001')
    input = {}
    action_endpoint = cur_action.action_endpoint
    item = None

    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #get_activity_display_info is include "None object"
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = None

    with patch('weko_workflow.views.get_activity_display_info',
            return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #action_endpoint is identifier_grant and item is not None
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'identifier_grant'
    item = item_metadata

    with patch('weko_workflow.views.get_activity_display_info',
            return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #action_endpoint is item_login and activity is None
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10002')
    input = {}
    action_endpoint = 'item_login'
    #action_endpoint = cur_action.action_endpoint
    action_id = cur_action.id
    histories = 1
    item_metadata = ItemMetadata()
    item_metadata.id = '37075580-8442-4402-beee-05f62e6e1dc2'

    steps = 1
    temporary_comment = 1

    test_pid = PersistentIdentifier()
    test_pid.pid_value = '100.0'

    identifier = {'action_identifier_select': '',
                'action_identifier_jalc_doi': '',
                'action_identifier_jalc_cr_doi': '',
                'action_identifier_jalc_dc_doi': '',
                'action_identifier_ndl_jalc_doi': ''
                }

    files_thumbnail = []

    # mocker.patch('weko_workflow.views.WorkActivity.get_activity_action_role',
    #             return_value=(roles, action_users))
    mocker.patch('weko_workflow.views.WorkActivity.get_action_identifier_grant',return_value=identifier)
    mocker.patch('weko_workflow.views.WorkActivity.get_action_journal')
    mocker.patch('weko_workflow.views.get_files_and_thumbnail',return_value=(["test1","test2"],files_thumbnail))

    # PIDDeletedError
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-00005')
    input = {}
    action_endpoint = cur_action.action_endpoint
    item = item_metadata
    owner_id = 1
    shared_user_ids = []
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #action_endpoint is item_link
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_link'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata

    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.ItemLink.get_item_link_info'):
            with patch('weko_workflow.views.item_login',return_value=(template_url,
                    need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                    files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
                with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                    with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                        with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                            with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                                with patch('weko_workflow.views.render_template', mock_render_template):
                                    res = client.post(url, query_string=input)
                                    mock_render_template.assert_called()

    #action_endpoint is item_login
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata
    del_session()
    with client.session_transaction() as session:
        assert "itemlogin_id" not in session
    # locked_value is not existed
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.ItemLink.get_item_link_info'):
            with patch('weko_workflow.views.item_login',return_value=(template_url,
                    need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                    files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
                with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                    with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                        with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                            with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                                with patch('weko_workflow.views.render_template', mock_render_template):
                                    res = client.post(url, query_string=input)
                                    mock_render_template.assert_called()
                                    with client.session_transaction() as session:
                                        assert "itemlogin_id" in session
                                        assert "activity_info" in session

    # locked_value is existed
    del_session()
    with client.session_transaction() as session:
        assert "itemlogin_id" not in session
    current_cache.set("workflow_userlock_activity_5","A-00000001-10001")
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.ItemLink.get_item_link_info'):
            with patch('weko_workflow.views.item_login',return_value=(template_url,
                    need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                    files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
                with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                    with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                        with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                            with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                                with patch('weko_workflow.views.render_template', mock_render_template):
                                    res = client.post(url, query_string=input)
                                    mock_render_template.assert_called()
                                    with client.session_transaction() as session:
                                        assert "itemlogin_id" not in session
                                        assert "activity_info" not in session
    current_cache.delete("workflow_userlock_activity_5")
    
    #raise PIDDeletedError
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',side_effect=PIDDeletedError('test','test')):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                #mock_render_template.assert_called()

    #raise PIDDoesNotExistError
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata

    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',side_effect=PIDDoesNotExistError('test','test')):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #raise Exception
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata

    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',side_effect=Exception()):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #approval record is not None
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata

    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,True)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #license_list is None
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata

    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=None):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=record_detail_alt):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()

    #record_detail_alt is None
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata

    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=test_comm):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=None):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                res = client.post(url, query_string=input)
                                mock_render_template.assert_called()
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {'community': 'test'}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = "test"
    item = item_metadata
    class MockUser:
        id = 0
    mock_user = MagicMock()
    mock_user.id = 0
    
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, None, \
               steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.item_login',return_value=(template_url,
                need_file,need_billing_file,record,json_schema,schema_form,item_save_uri,
                files,endpoints,need_thumbnail,files_thumbnail,allow_multi_thumbnail)):
            with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
                with patch('weko_workflow.views.GetCommunity.get_community_by_id',return_value=None):
                    with patch('weko_records_ui.utils.get_list_licence',return_value=license_list):
                        with patch('weko_workflow.views.get_main_record_detail',return_value=None):
                            with patch('weko_workflow.views.render_template', mock_render_template):
                                with patch("flask_login.utils._get_user",return_value=mock_user):
                                    res = client.post(url, query_string=input)
                                    mock_render_template.assert_called()

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_activity_2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_display_activity_2(client, users_1, db_register_1, mocker):
    # ユーザー１でログイン
    login(client=client, email=users_1[0]['email'])

    workflow_detail = WorkFlow.query.filter_by(id=1).one_or_none()

    activity_detail = Activity.query.filter_by(activity_id='A-00000001-00005').one_or_none()
    activity_detail.shared_user_ids = []
    #activity_detail = Activity.query.filter_by(activity_id='1').one_or_none()
    cur_action = activity_detail.action
    action_endpoint = 'item_login'
    #action_endpoint = cur_action.action_endpoint
    action_id = cur_action.id
    histories = 1
    item_metadata = ItemMetadata()
    item_metadata.id = '37075580-8442-4402-beee-05f62e6e1dc2'

    steps = 1
    temporary_comment = 1

    test_pid = PersistentIdentifier()
    test_pid.pid_value = '100.0'

    identifier = {'action_identifier_select': '',
                'action_identifier_jalc_doi': '',
                'action_identifier_jalc_cr_doi': '',
                'action_identifier_jalc_dc_doi': '',
                'action_identifier_ndl_jalc_doi': ''
                }

    files_thumbnail = []

    # mocker.patch('weko_workflow.views.WorkActivity.get_activity_action_role',
    #             return_value=(roles, action_users))
    mocker.patch('weko_workflow.views.WorkActivity.get_action_identifier_grant',return_value=identifier)
    mocker.patch('weko_workflow.views.WorkActivity.get_action_journal')
    mocker.patch('weko_workflow.views.get_files_and_thumbnail',return_value=(["test1","test2"],files_thumbnail))

    # PIDDeletedError
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-00005')
    input = {}
    action_endpoint = cur_action.action_endpoint
    item = item_metadata
    owner_id = 1
    shared_user_ids = []
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail, owner_id, shared_user_ids)):
        with patch('weko_workflow.views.get_pid_and_record',return_value=(test_pid,None)):
            with patch('weko_workflow.views.get_contributors', side_effect=PIDDeletedError('test','test')):
                res = client.post(url, query_string=input)
                assert res.status_code == 404

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_check_authority -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_authority(client, activity_acl, activity_acl_users):
    users = activity_acl_users["users"]
    activities = activity_acl

    # user is admin user
    login_user(users[0])
    activity=activities[0]
    result = check_authority(lambda activity_id,action_id:"{}:{}".format(activity_id,action_id))(activity_id=activity.activity_id,action_id=activity.action_id)
    assert result == "A-00000001-00001:5"


    login_user(users[2])
    # action user(role) is not set
    activity=activities[21]
    result = check_authority(lambda activity_id,action_id:"{}:{}".format(activity_id,action_id))(activity_id=activity.activity_id,action_id=activity.action_id)
    assert result == "A-00000001-00022:5"

    # action role(user) is set, is_deny is False
    activity=activities[33]
    result = check_authority(lambda activity_id,action_id:"{}:{}".format(activity_id,action_id))(activity_id=activity.activity_id,action_id=activity.action_id)
    assert result == "A-00000001-00034:5"

    # action role(user) is set, is_deny is True
    activity=activities[34]
    result = check_authority(lambda activity_id,action_id:"{}:{}".format(activity_id,action_id))(activity_id=activity.activity_id,action_id=activity.action_id)
    assert json.loads(result.data.decode('utf-8')) == {"code":403,"msg":"Authorization required"}

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_check_authority_action -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_authority_action(client, activity_acl, activity_acl_users, db_register):
    users = activity_acl_users["users"]
    activities = activity_acl
    # no authenticated
    result = check_authority_action()
    assert result == 1

    # sysadmin user
    login_user(users[0])
    activity = activities[0]
    result = check_authority_action(activity_id=activity.activity_id,
                                    action_id=activity.action_id,
                                    action_order=activity.action_order)
    assert result == 0

    # repoadmin user
    login_user(users[1])
    activity = activities[0]
    result = check_authority_action(activity_id=activity.activity_id,
                                    action_id=activity.action_id,
                                    action_order=activity.action_order)
    assert result == 0

    # comadmin user, activity index is within community permissions
    login_user(users[3])
    activity = activities[21]
    result = check_authority_action(activity_id=activity.activity_id,
                                    action_id=activity.action_id,
                                    action_order=activity.action_order)
    assert result == 0

    # comadmin user, activity index is not within community permissions
    ## action role(user) is set, is_deny is True
    activity = activities[14]
    result = check_authority_action(activity_id=activity.activity_id,
                                    action_id=activity.action_id,
                                    action_order=activity.action_order)
    assert result == 1

    ## action role(user) is set, is_deny is False, is_allow is True
    activity = activities[13]
    result = check_authority_action(activity_id=activity.activity_id,
                                    action_id=activity.action_id,
                                    action_order=activity.action_order)
    assert result == 0

    ## action role(user) is set, is_deny is False, is_allow is False
    activity = activities[36]
    result = check_authority_action(activity_id=activity.activity_id,
                                    action_id=activity.action_id,
                                    action_order=activity.action_order)
    assert result == 1

    # check shared_user
    ## action is approval
    activity = activities[38]
    result = check_authority_action(activity_id=activity.activity_id,
                                    action_id=activity.action_id,
                                    action_order=activity.action_order)

    assert result == 1

    # action is not approval, shared_user is self in item_metadata
    activity = activities[37]
    result = check_authority_action(activity_id=activity.activity_id,
                                    action_id=activity.action_id,
                                    action_order=activity.action_order)
    assert result == 0

    # action is not approval, shared_user is self in activity
    activity = activities[31]
    result = check_authority_action(activity_id=activity.activity_id,
                                    action_id=activity.action_id,
                                    action_order=activity.action_order)
    assert result == 0

    # action is not approval, shared_user is not self
    activity = activities[26]
    result = check_authority_action(activity_id=activity.activity_id,
                                    action_id=activity.action_id,
                                    action_order=activity.action_order)
    assert result == 1

    current_app.config['WEKO_WORKFLOW_ENABLE_CONTRIBUTOR']=False
    # activity creator check
    # contain_login_item_application is True
    ## activity creator is self
    activity = activities[11]
    result = check_authority_action(activity_id=activity.activity_id,
                                    action_id=activity.action_id,
                                    contain_login_item_application=True,
                                    action_order=activity.action_order)
    assert result == 0

    ## activity creator is not self
    activity = activities[26]
    result = check_authority_action(activity_id=activity.activity_id,
                                    action_id=activity.action_id,
                                    contain_login_item_application=True,
                                    action_order=activity.action_order)
    assert result == 1

    # contain_login_item_application is False
    ## activity creator is self
    activity = activities[11]
    result = check_authority_action(activity_id=activity.activity_id,
                                    action_id=activity.action_id,
                                    contain_login_item_application=False,
                                    action_order=activity.action_order)
    assert result == 0

    ## activity creator is not self
    activity = activities[26]
    result = check_authority_action(activity_id=activity.activity_id,
                                    action_id=activity.action_id,
                                    contain_login_item_application=False,
                                    action_order=activity.action_order)
    assert result == 1

    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        current_app.config["WEKO_WORKFLOW_ENABLE_CONTRIBUTOR"]=True

        # cur_user != activity_login_user and cur_user != activity.shared_user_id
        result = check_authority_action(activity_id=activity.activity_id, action_id=3, contain_login_item_application=False, action_order=2)
        assert result == 1

        # cur_user != action_handler
        result = check_authority_action(activity_id=activity.activity_id, action_id=3, contain_login_item_application=True, action_order=2)
        assert result == 1

        # action_handler == -1 and cur_user == activity.shared_user_id
        activity_action = db_register["activity_actions"][2]
        activity_action.action_handler = -1
        activity.shared_user_ids = [users[0]["id"]]
        db.session.merge(activity_action)
        db.session.merge(activity)
        db.session.commit()
        result = check_authority_action(activity_id=activity.activity_id, action_id=3, contain_login_item_application=True, action_order=2)
        assert result == 1

        # action_handler != -1 and cur_user == activity.shared_user_id
        activity_action.action_handler = 100
        db.session.merge(activity_action)
        db.session.commit()
        result = check_authority_action(activity_id=activity.activity_id, action_id=3, contain_login_item_application=True, action_order=2)
        assert result == 0

# def check_authority_action(activity_id='0', action_id=0, contain_login_item_application=False, action_order=0):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_check_authority_action2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_authority_action2(app, client, users, db_register, mocker):
    current_app.config['WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'] = False
    # ログアウトしている場合、1
    with app.test_request_context():
        logout_user()
        assert 1 == check_authority_action(activity_id='11', 
                            action_id=0, 
                            contain_login_item_application=False, 
                            action_order=0)

    # ログインユーザーが、登録ユーザーでない場合 admin
    with patch("flask_login.utils._get_user",return_value=users[2]["obj"]):
        assert 0 == check_authority_action(activity_id='11', 
                            action_id=0, 
                            contain_login_item_application=False, 
                            action_order=0)

    # ログインユーザーが、登録ユーザーでない場合 user
    with patch("flask_login.utils._get_user",return_value=users[7]["obj"]):
        assert 1 == check_authority_action(activity_id='1', 
                            action_id=1, 
                            contain_login_item_application=False, 
                            action_order=1)

    # ログインユーザーが、登録ユーザーでない場合 generaluser allow only
    with patch("flask_login.utils._get_user",return_value=users[4]["obj"]):
        assert 1 == check_authority_action(activity_id='10', 
                            action_id=3, 
                            contain_login_item_application=False, 
                            action_order=2)

    # ログインユーザーが、登録ユーザーでない場合 deny only
    with patch("flask_login.utils._get_user",return_value=users[4]["obj"]):
        assert 1 == check_authority_action(activity_id='10', 
                            action_id=3, 
                            contain_login_item_application=False, 
                            action_order=1)

    # ログインユーザーが、登録ユーザー場合 generaluser
    with patch("flask_login.utils._get_user",return_value=users[0]["obj"]):
        assert 1 == check_authority_action(activity_id='guest', 
                            action_id=3, 
                            contain_login_item_application=False, 
                            action_order=1)

    # ログインユーザーが、登録ユーザーの場合 contributor
    with patch("flask_login.utils._get_user",return_value=users[0]["obj"]):
        assert 1 == check_authority_action(activity_id='11', 
                            action_id=3, 
                            contain_login_item_application=False, 
                            action_order=1)

    # ログインユーザーが、登録ユーザーでない場合 current user_id=6 shared_user_ids=[2,4]
    with patch("flask_login.utils._get_user",return_value=users[4]["obj"]):
        mocker.patch("weko_workflow.api.WorkActivity.get_activity_action_role",return_value=({'allow':[],'deny':[]}, {'allow':[],'deny':[]}))
        assert 1 == check_authority_action(activity_id='11', 
                            action_id=3, 
                            contain_login_item_application=False, 
                            action_order=1)

        assert 1 == check_authority_action(activity_id='11', 
                            action_id=3, 
                            contain_login_item_application=False, 
                            action_order=2)

        mocker.patch("weko_workflow.api.WorkActivity.get_activity_action_role",return_value=({'allow':[],'deny':[5]}, {'allow':[],'deny':[]}))
        assert 1 == check_authority_action(activity_id='11', 
                            action_id=3, 
                            contain_login_item_application=False, 
                            action_order=1)

    # ログインユーザーが、登録ユーザーでない場合 repoadmin shared_user_ids=[2,4]
    with patch("flask_login.utils._get_user",return_value=users[1]["obj"]): # cur_user=6
        mocker.patch("weko_workflow.api.WorkActivity.get_activity_action_role",return_value=({'allow':[],'deny':[]}, {'allow':[],'deny':[]}))
        assert 0 == check_authority_action(activity_id='11', 
                            action_id=3, 
                            contain_login_item_application=False, 
                            action_order=1)

    with patch("flask_login.utils._get_user",return_value=users[0]["obj"]): # cur_user=2  activity.activity_login_user=2
        mocker.patch("weko_workflow.api.WorkActivity.get_activity_action_role",return_value=({'allow':[],'deny':[]}, {'allow':[],'deny':[]}))
        assert 0 == check_authority_action(activity_id='11', 
                            action_id=3, 
                            contain_login_item_application=False, 
                            action_order=1)

    with patch("flask_login.utils._get_user",return_value=users[4]["obj"]): # cur_user=2  activity.activity_login_user=2
        mocker.patch("weko_workflow.api.WorkActivity.get_activity_action_role",return_value=({'allow':[],'deny':[]}, {'allow':[],'deny':[]}))
        current_app.config['WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'] = True
        assert 1 == check_authority_action(activity_id='11', 
                            action_id=3, 
                            contain_login_item_application=False, 
                            action_order=1)
        # ItemMetadataあり
        activity = Activity.query.filter_by(activity_id='11').first()
        im = ItemMetadata.query.filter_by(id=activity.item_id).one_or_none()
        im.json['shared_user_ids'] = [1,2,3,4,5,6]
        assert 0 == check_authority_action(activity_id='11', 
                            action_id=3, 
                            contain_login_item_application=False, 
                            action_order=1)
        im.json['shared_user_ids'] = []
        im.json['owner'] = users[4]['id']
        assert 0 == check_authority_action(activity_id='11', 
                            action_id=3, 
                            contain_login_item_application=False, 
                            action_order=1)
        im.json['shared_user_ids'] = []
        im.json['owner'] = -1
        update_action_handler('2', 1, users[4]["id"])
        assert 0 == check_authority_action(activity_id='2', 
                            action_id=1, 
                            contain_login_item_application=True, 
                            action_order=1)

        # ItemMetadataなし
        activity = Activity.query.filter_by(activity_id='11').first()
        activity.temp_data = json.dumps({'metainfo':{'shared_user_ids':[{'user': 1},{'user': users[4]['id']}], 'owner': 1}})
        activity.item_id=str(uuid.uuid4())
        assert 0 == check_authority_action(activity_id='11', 
                            action_id=3, 
                            contain_login_item_application=False, 
                            action_order=1)
        activity.temp_data = json.dumps({'metainfo':{'shared_user_ids':[{'user': 1}], 'owner': users[4]['id']}})
        activity.item_id=str(uuid.uuid4())
        assert 0 == check_authority_action(activity_id='11', 
                            action_id=3, 
                            contain_login_item_application=False, 
                            action_order=1)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_withdraw_confirm_nologin -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_withdraw_confirm_nologin -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_withdraw_confirm_nologin(client,db_register2):
    """Test of withdraw confirm."""
    url = url_for('weko_workflow.withdraw_confirm', activity_id='1',
                  action_id=1)
    input = {}

    res = client.post(url, json=input)
    assert res.location == 'http://test_server.localdomain/login/?next=%2Fworkflow%2Factivity%2Fdetail%2F1%2F1%2Fwithdraw'


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_withdraw_confirm_users -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code, is_admin', [
    (0, 403, False),
    (1, 403, True),
    (2, 403, True),
    (3, 403, True),
    (4, 403, False),
    (5, 403, False),
    (6, 403, True),
])
def test_withdraw_confirm_users(client, users, db_register_fullaction, users_index, status_code, is_admin):
    """Test of withdraw confirm."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.withdraw_confirm',
                  activity_id='1',
                  action_id=1)
    input = {}

    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }
    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        assert res.status_code != status_code

    action_users = {
        'allow': [],
        'deny': [users[users_index]["id"]]
    }
    url = url_for('weko_workflow.withdraw_confirm',
                  activity_id='2',
                  action_id=1)
    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code != status_code
        if is_admin:
            assert data["code"] != 403
        else:
            assert data["code"] == 403

    action_users = {
        'allow': [users[users_index]["id"]],
        'deny': []
    }
    url = url_for('weko_workflow.withdraw_confirm',
                  activity_id='3',
                  action_id=1)
    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code != status_code
        assert data["code"] != 403


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_withdraw_confirm_guestlogin -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_withdraw_confirm_guestlogin(guest, client, db_register_fullaction):
    input = {}
    url = url_for('weko_workflow.withdraw_confirm',
                  activity_id="1", action_id=1)
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }
    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = guest.post(url, json=input)
        assert res.status_code != 403


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_withdraw_confirm_exception1 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index', [0, 1, 2, 3, 4, 5, 6])
def test_withdraw_confirm_exception1(client, users, db_register_fullaction, users_index):
    """Test of withdraw confirm."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.withdraw_confirm', activity_id='1',
            action_id=2)
    input = {"passwd": "DELETE"}
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }

    # activity_id, action_id check
    with patch('weko_workflow.views.type_null_check', return_value=False):
        with patch('weko_workflow.views.IdentifierHandle'):
            with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
                return_value=(roles, action_users)):
                res = client.post(url, json=input)
                data = response_data(res)
                assert res.status_code == 500
                assert data["code"] == -1
                assert data["msg"] == "argument error"

    # Unexpected error check
    with patch('weko_workflow.views.type_null_check', side_effect=ValueError):
        with patch('weko_workflow.views.IdentifierHandle'):
            with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
                return_value=(roles, action_users)):
                res = client.post(url, json=input)
                data = response_data(res)
                assert res.status_code == 500
                assert data["code"] == -1
                assert data["msg"] == "Error!"


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_withdraw_confirm_exception1_guestlogin -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_withdraw_confirm_exception1_guestlogin(guest, client, users, db_register_fullaction):
    """Test of withdraw confirm."""
    url = url_for('weko_workflow.withdraw_confirm', activity_id='1',
            action_id=2)
    input = {"passwd": "DELETE"}
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }

    # activity_id, action_id check
    with patch('weko_workflow.views.type_null_check', return_value=False):
        with patch('weko_workflow.views.IdentifierHandle'):
            with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
                return_value=(roles, action_users)):
                res = guest.post(url, json=input)
                data = response_data(res)
                assert res.status_code == 500
                assert data["code"] == -1
                assert data["msg"] == "argument error"

    # Unexpected error check
    with patch('weko_workflow.views.type_null_check', side_effect=ValueError):
        with patch('weko_workflow.views.IdentifierHandle'):
            with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
                return_value=(roles, action_users)):
                res = guest.post(url, json=input)
                data = response_data(res)
                assert res.status_code == 500
                assert data["code"] == -1
                assert data["msg"] == "Error!"


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_withdraw_confirm_exception2 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
input_data_list = [
    ({}, 500, -1, "{'passwd': ['Missing data for required field.']}"),
    ({"passwd": None}, 500, -1, "{'passwd': ['Field may not be null.']}"),
    ({"passwd": "something"}, 500, -1, "Invalid password")
]
@pytest.mark.parametrize('input_data, status_code, code, msg', input_data_list)
@pytest.mark.parametrize('users_index', [0, 1, 2, 3, 4, 5, 6])
def test_withdraw_confirm_exception2(client, users, db_register_fullaction, users_index, status_code, input_data, code, msg):
    """Test of withdraw confirm."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.withdraw_confirm', activity_id='1',
            action_id=2)
    input = input_data
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }

    with patch('weko_workflow.views.IdentifierHandle'):
        with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
        return_value=(roles, action_users)):
            res = client.post(url, json=input)
            data = response_data(res)
            assert res.status_code == status_code
            assert data["code"] == code
            assert data["msg"] == msg


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_withdraw_confirm_exception2_guestlogin -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('input_data, status_code, code, msg', input_data_list)
def test_withdraw_confirm_exception2_guestlogin(guest, client, users, db_register_fullaction, input_data, status_code, code, msg):
    """Test of withdraw confirm."""
    url = url_for('weko_workflow.withdraw_confirm', activity_id='1',
            action_id=2)
    input = input_data
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }

    with patch('weko_workflow.views.IdentifierHandle'):
        with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
            return_value=(roles, action_users)):
            res = guest.post(url, json=input)
            data = response_data(res)
            assert res.status_code == status_code
            assert data["code"] == code
            assert data["msg"] == msg


case_list = [
    ("success", 200, 0, "success")
]

@pytest.mark.parametrize('case, status_code, code, msg', case_list)
@pytest.mark.parametrize('users_index', [0, 1, 2, 3, 4, 5, 6])
def test_withdraw_confirm_passwd_delete(client, users, db_register_fullaction, users_index, status_code, case, code, msg):
    """Test of withdraw confirm."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.withdraw_confirm', activity_id='1',
            action_id=2)
    input = {"passwd": "DELETE"}
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }

    if case == "success":
        with patch('invenio_pidstore.models.PersistentIdentifier.get_by_object'):
            with patch('weko_workflow.views.WorkActivity.get_action_identifier_grant', return_value={}):
                with patch('weko_workflow.views.IdentifierHandle'):
                    with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
                    return_value=(roles, action_users)):
                        res = client.post(url, json=input)
                        data = response_data(res)
                        assert res.status_code == status_code
                        assert data["code"] == code
                        assert data["msg"] == msg
                        assert data["data"] == {"redirect": url_for('weko_workflow.display_activity', activity_id='1')}

@pytest.mark.parametrize('case, status_code, code, msg', case_list)
def test_withdraw_confirm_passwd_delete_guestlogin(guest, client, users, db_register_fullaction, case, status_code, code, msg):
    """Test of withdraw confirm."""
    url = url_for('weko_workflow.withdraw_confirm', activity_id='1',
            action_id=2)
    input = {"passwd": "DELETE"}
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }
    session = {
        "guest_url": "guest_url"
    }
    with patch("weko_workflow.views.session",session):
        if case == "success":
            with patch('invenio_pidstore.models.PersistentIdentifier.get_by_object'):
                with patch('weko_workflow.views.WorkActivity.get_action_identifier_grant', return_value={}):
                    with patch('weko_workflow.views.IdentifierHandle'):
                        with patch('weko_workflow.api.WorkActivity.get_activity_action_role',
                        return_value=(roles, action_users)):
                            res = guest.post(url, json=input)
                            data = response_data(res)
                            assert res.status_code == status_code
                            assert data["code"] == code
                            assert data["msg"] == msg
                            assert data["data"] == {"redirect": "guest_url"}

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_usage_report_nologin -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_usage_report_nologin(client, db):
    """Test of usage report with no login."""
    url = url_for('weko_workflow.usage_report')
    res = client.get(url)
    assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_usage_report -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_usage_report(client, users):
    """Test of usage report."""
    class MockActivity:
        def __init__(self):
            self.activity_id = 1
            self.title = 'test_title'
            self.flows_name = 'test_flow'
            self.email = 'test@test.org'
            self.StatusDesc = 'desc'
            self.role_name = 'test_role'

    login(client=client, email=users[0]['email'])
    url = url_for('weko_workflow.usage_report')
    with patch('weko_workflow.views.filter_all_condition', return_value={}):
        with patch('weko_workflow.views.WorkActivity.get_activity_list', return_value=([MockActivity()], None, None, None, None, None)):
            with patch('weko_workflow.views.get_workflow_item_type_names'):
                res = client.get(url)
                assert res.status_code == 200
                response = json.loads(res.data)
                assert response['activities'] == [
                    {
                        'activity_id': 1,
                        'item': 'test_title',
                        'work_flow': 'test_flow', 
                        'email': 'test@test.org',
                        'status': 'desc',
                        'user_role': 'test_role'
                    }
                ]

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_get_data_init_nologin -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_data_init_nologin(client, db):
    """Test of get_data_init with no login."""
    url = url_for('weko_workflow.get_data_init')
    res = client.get(url)
    assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_get_data_init -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_data_init(client, users):
    """Test of get_data_init."""
    login(client=client, email=users[0]['email'])
    workflows = [{'id': 1, 'flows_name': 'test_flow'}]
    roles = [{'id': 'none_login', 'name': 'Guest'}]
    terms = [{'id': 1, 'name': 'test_term', 'content': 'test_content'}]
    url = url_for('weko_workflow.get_data_init')
    with patch('weko_records_ui.utils.get_workflows', return_value=workflows):
        with patch('weko_records_ui.utils.get_roles', return_value=roles):
            with patch('weko_records_ui.utils.get_terms', return_value=terms):
                res = client.get(url)
                assert res.status_code == 200
                response = json.loads(res.data)
                assert response['init_workflows'] == workflows
                assert response['init_roles'] == roles
                assert response['logged_roles'] == [
                    {'id': 3, 'name': 'Contributor'},
                    {'id': 4, 'name': 'Community Administrator'},
                    {'id': 5, 'name': 'General'},
                    {'id': 6, 'name': 'Original Role'},
                    {'id': 7, 'name': 'Student'}
                ]
                assert response['init_terms'] == terms

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_download_activitylog_nologin -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_download_activitylog_nologin(client,db_register2):
    """_summary_

    Args:
        client (FlaskClient): flask test client
    """
    #2
    url = url_for('weko_workflow.download_activitylog')
    res =  client.get(url)
    assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_download_activitylog_1 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 403),
    (4, 403),
    (5, 403),
    (6, 200),
])
def test_download_activitylog_1(client, db, db_register_full_action , users, users_index, status_code):
    """Test of download_activitylog."""
    login(client=client, email=users[users_index]['email'])

    if status_code == 200:
        with pytest.raises(Exception) as e:
            #1
            url = url_for('weko_workflow.download_activitylog',
                        activity_id='2')
            res = client.get(url)
            assert res.status_code == status_code
    else:
        #1
        url = url_for('weko_workflow.download_activitylog',
                    activity_id='2')
        res = client.get(url)
        assert res.status_code == status_code

    #3
    current_app.config.update(
        DELETE_ACTIVITY_LOG_ENABLE = False
    )
    current_app.config.update(
        WEKO_WORKFLOW_FILTER_PARAMS = [
            'createdfrom', 'createdto', 'workflow', 'user', 'item', 'status', 'tab',
            'sizewait', 'sizetodo', 'sizeall', 'pagesall', 'pagestodo', 'pageswait'
        ]
    )

    url = url_for('weko_workflow.download_activitylog',
                tab='all')
    res = client.get(url)
    assert res.status_code == 403

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_download_activitylog_2 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (1, 200),
    (2, 200),
    (6, 200),
])
def test_download_activitylog_2(client, db_register_full_action, users, users_index, status_code):
    """Test of download_activitylog."""
    login(client=client, email=users[users_index]['email'])

    with pytest.raises(Exception) as e:
        #4
        url = url_for('weko_workflow.download_activitylog',
                    activity_id='2')
        res = client.get(url)
        assert res.status_code == status_code


    #5
    url = url_for('weko_workflow.download_activitylog',
                activity_id='100')
    res = client.get(url)
    assert res.status_code == 400

    #6
    url = url_for('weko_workflow.download_activitylog',
                tab='all')
    res = client.get(url)
    assert res.status_code == status_code

    #7
    url = url_for('weko_workflow.download_activitylog',
                createdto='1900-01-17')
    res = client.get(url)
    assert res.status_code == 400

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_clear_activitylog_nologin -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_clear_activitylog_nologin(client,db_register2):
    """_summary_

    Args:
        client (FlaskClient): flask test client
    """
    #10
    url = url_for('weko_workflow.clear_activitylog')
    res =  client.get(url)
    assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_clear_activitylog_1 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 403),
    (4, 403),
    (5, 403),
    (6, 200),
])
def test_clear_activitylog_1(client, db_register_full_action, users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])

    #9,11
    url = url_for('weko_workflow.clear_activitylog',
                activity_id='A-00000001-10001')
    res = client.get(url)
    assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_clear_activitylog_2 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (1, 200),
    (2, 200),
    (6, 200),
])
def test_clear_activitylog_2(client, db_register_full_action, users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])
    #12
    url = url_for('weko_workflow.clear_activitylog',
                activity_id='100')
    res = client.get(url)
    assert res.status_code == 400

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_clear_activitylog_3 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (1, 200),
    (2, 200),
    (6, 200),
])
def test_clear_activitylog_3(client, db_register_full_action, users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])
    #13
    with patch('weko_workflow.views.WorkActivity.quit_activity', return_value=None):
        url = url_for('weko_workflow.clear_activitylog',
                    activity_id='A-00000001-10001')
        res = client.get(url)
        assert res.status_code == 400

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_clear_activitylog_4 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (1, 200),
    (2, 200),
    (6, 200),
])
def test_clear_activitylog_4(client, db_register_full_action, users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])
    #14
    with patch('invenio_db.db.session.delete', side_effect=Exception("test error")):
        url = url_for('weko_workflow.clear_activitylog',
                    activity_id='A-00000001-10001')
        res = client.get(url)
        assert res.status_code == 400

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_clear_activitylog_5 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 403),
    (4, 403),
    (5, 403),
    (6, 200),
])
def test_clear_activitylog_5(client, db_register_full_action, users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])
    #15
    url = url_for('weko_workflow.clear_activitylog',
                tab='all')
    res = client.get(url)
    assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_clear_activitylog_6 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (1, 200),
    (2, 200),
    (6, 200),
])
def test_clear_activitylog_6(client, db_register_full_action, users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])
    #16
    url = url_for('weko_workflow.clear_activitylog',
                createdto='1900-01-17')
    res = client.get(url)
    assert res.status_code == 400

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_clear_activitylog_7 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (1, 200),
    (2, 200),
    (6, 200),
])
def test_clear_activitylog_7(client, db_register_full_action, users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])
    #17
    with patch('weko_workflow.views.WorkActivity.quit_activity', return_value=None):
        url = url_for('weko_workflow.clear_activitylog',
                    tab='all')
        res = client.get(url)
        assert res.status_code == 400

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_clear_activitylog_8 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (1, 200),
    (2, 200),
    (6, 200),
])
def test_clear_activitylog_8(client, db_register_full_action, users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])
    #18
    with patch('invenio_db.db.session.delete', side_effect=Exception("test error")):
        url = url_for('weko_workflow.clear_activitylog',
                    tab='all')
        res = client.get(url)
        assert res.status_code == 400

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_clear_activitylog_9 -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 403),
    (4, 403),
    (5, 403),
    (6, 200),
])
def test_clear_activitylog_9(client, db_register_full_action, users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])
    #19
    current_app.config.update(
        DELETE_ACTIVITY_LOG_ENABLE = False
    )

    url = url_for('weko_workflow.clear_activitylog',
                tab='all')
    res = client.get(url)
    assert res.status_code == 403

# class ActivityActionResource(ContentNegotiatedMethodView):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_ActivityActionResource_post -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_ActivityActionResource_post(client, db_register_full_action, users):
    url = '/depositactivity/{}'.format(db_register_full_action['activities'][0].activity_id)
    login(client=client, email=users[2]['email'])
    res = client.get(url)
    assert res.status_code == 400

# def weko_workflow.schema.marshmallow.SaveActivitySchema(json):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_SaveActivitySchema -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_SaveActivitySchema():
    json = {'activity_id': '11', 'title': 'sample', 'shared_user_ids': [{'user': 1},{'user':2}], 'approval1':'', 'approval2':''}
    data = SaveActivitySchema().load(json)
    assert data.data['activity_id'] == '11'
    assert data.data['title'] == 'sample'
    assert data.data['shared_user_ids'] == [{'user': 1},{'user':2}]
    assert data.data['approval1'] == ''
    assert data.data['approval2'] == ''

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_edit_item_direct_1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 302),
    (1, 302),
    (2, 302),
    (3, 302),
    (4, 302),
    (5, 302),
    (6, 302),
])
def test_edit_item_direct_1(client, users, users_index, status_code):
    login(client=client, email=users[users_index]['email'])
    url = url_for("weko_workflow.edit_item_direct", pid_value="1")
    res = client.get(url)
    assert res.status_code == 302
    assert res.location == 'http://test_server.localdomain/workflow/edit_item_direct_after_login/1'

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_edit_item_direct_2 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_edit_item_direct_2(client, db_register2):
    url = url_for("weko_workflow.edit_item_direct", pid_value="1")
    res = client.get(url)
    assert res.status_code == 302
    assert res.location == 'http://test_server.localdomain/login/?next=%2Fworkflow%2Fedit_item_direct_after_login%2F1'

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_edit_item_direct_after_login_01 -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize(
    "users_index, status_code",
    [
        (1, 302),
        (2, 302),
        (3, 302),
        (6, 302),
    ],
)
def test_edit_item_direct_after_login_01(client, users, db_register, users_index, status_code, mocker):
    mocker.patch('celery.task.control.inspect.ping', return_value="")
    return_data = MagicMock(activity_id=1)
    mocker.patch("weko_workflow.views.prepare_edit_workflow", return_value=return_data)
    login(client=client, email=users[users_index]["email"])
    url = url_for("weko_workflow.edit_item_direct_after_login", pid_value="1")
    res = client.get(url)
    assert res.status_code == status_code
    assert res.location == 'http://test_server.localdomain/workflow/activity/detail/1'

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_edit_item_direct_after_login_02 -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize(
    "users_index, status_code",
    [
        (0, 400),
        (1, 400),
        (2, 400),
        (3, 400),
        (4, 400),
        (5, 400),
        (6, 400),
    ],
)
def test_edit_item_direct_after_login_02(client, users, db_register, users_index, status_code, mocker):
    mock_render_template = mocker.patch('weko_workflow.views.render_template', return_value ='')
    mock_redis = MagicMock(exists=MagicMock(return_value=True))
    mock_sessionstorage = MagicMock(redis=mock_redis)
    mocker.patch.object(RedisConnection, 'connection', return_value = mock_sessionstorage)
    login(client=client, email=users[users_index]["email"])
    url = url_for("weko_workflow.edit_item_direct_after_login", pid_value="1")
    res = client.get(url)
    mock_render_template.assert_called_with("weko_theme/error.html", error="This Item is being edited.")
    mock_redis.exists.assert_called_once()
    assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_edit_item_direct_after_login_03 -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize(
    "users_index, status_code",
    [
        (0, 404),
        (1, 404),
        (2, 404),
        (3, 404),
        (4, 404),
        (5, 404),
        (6, 404),
    ],
)
def test_edit_item_direct_after_login_03(client, users, db_register, users_index, status_code, mocker):
    mock_render_template = mocker.patch('weko_workflow.views.render_template', return_value ='')
    mock_resolve = mocker.patch.object(Resolver, 'resolve', return_value = (None, None))
    login(client=client, email=users[users_index]["email"])
    url = url_for("weko_workflow.edit_item_direct_after_login", pid_value="1")
    res = client.get(url)
    mock_render_template.assert_called_with("weko_theme/error.html", error="Record does not exist.")
    mock_resolve.assert_called_once()
    assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_edit_item_direct_after_login_03_2 -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize(
    "users_index, status_code",
    [
        (0, 404),
        (1, 404),
        (2, 404),
        (3, 404),
        (4, 404),
        (5, 404),
        (6, 404),
    ],
)
def test_edit_item_direct_after_login_03_2(client, users, db_register, users_index, status_code, mocker):
    mock_render_template = mocker.patch('weko_workflow.views.render_template', return_value ='')
    mock_resolve = mocker.patch.object(Resolver, 'resolve', side_effect=PIDDoesNotExistError(None, None))
    login(client=client, email=users[users_index]["email"])
    url = url_for("weko_workflow.edit_item_direct_after_login", pid_value="1")
    res = client.get(url)
    mock_render_template.assert_called_with("weko_theme/error.html", error="Record does not exist.")
    mock_resolve.assert_called_once()
    assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_edit_item_direct_after_login_04 -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize(
    "users_index, status_code",
    [
        (0, 400),
        (4, 400),
        (5, 400),
    ],
)
def test_edit_item_direct_after_login_04(client, users, db_register, users_index, status_code, mocker):
    mock_render_template = mocker.patch('weko_workflow.views.render_template', return_value ='')
    login(client=client, email=users[users_index]["email"])
    url = url_for("weko_workflow.edit_item_direct_after_login", pid_value="1")
    res = client.get(url)
    mock_render_template.assert_called_with("weko_theme/error.html", error="You are not allowed to edit this item.")
    assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_edit_item_direct_after_login_05 -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize(
    "users_index, status_code",
    [
        (1, 400),
        (2, 400),
        (3, 400),
        (6, 400),
    ],
)
def test_edit_item_direct_after_login_05(client, users, db_register, users_index, status_code, mocker):
    mock_render_template = mocker.patch('weko_workflow.views.render_template', return_value ='')
    mocker.patch('weko_records.api.ItemTypes.get_latest', return_value=None)
    login(client=client, email=users[users_index]["email"])
    url = url_for("weko_workflow.edit_item_direct_after_login", pid_value="1")
    res = client.get(url)
    mock_render_template.assert_called_with("weko_theme/error.html", error="You do not even have an ItemType.")
    assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_edit_item_direct_after_login_06 -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize(
    "users_index, status_code",
    [
        (1, 400),
        (2, 400),
        (3, 400),
        (6, 400),
    ],
)
def test_edit_item_direct_after_login_06(client, users, db_register, users_index, status_code, mocker):
    mock_render_template = mocker.patch('weko_workflow.views.render_template', return_value ='')
    mocker.patch('weko_records.api.ItemTypes.get_by_id', return_value=None)
    login(client=client, email=users[users_index]["email"])
    url = url_for("weko_workflow.edit_item_direct_after_login", pid_value="1")
    res = client.get(url)
    mock_render_template.assert_called_with("weko_theme/error.html", error="Dependency ItemType not found.")
    assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_edit_item_direct_after_login_07 -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize(
    "users_index, status_code",
    [
        (1, 400),
        (2, 400),
        (3, 400),
        (6, 400),
    ],
)
def test_edit_item_direct_after_login_07(client, users, db_register, users_index, status_code, mocker):
    mock_render_template = mocker.patch('weko_workflow.views.render_template', return_value ='')
    mocker.patch('weko_workflow.views.check_an_item_is_locked', return_value = True)
    login(client=client, email=users[users_index]["email"])
    url = url_for("weko_workflow.edit_item_direct_after_login", pid_value="1")
    res = client.get(url)
    mock_render_template.assert_called_with("weko_theme/error.html", error="Item cannot be edited because the import is in progress.")
    assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_edit_item_direct_after_login_08 -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize(
    "users_index, status_code",
    [
        (1, 400),
        (2, 400),
        (3, 400),
        (6, 400),
    ],
)
def test_edit_item_direct_after_login_08(client, users, db_register, users_index, status_code, mocker):
    mock_render_template = mocker.patch('weko_workflow.views.render_template', return_value ='')
    mocker.patch('celery.task.control.inspect.ping', return_value="")
    mocker.patch('weko_workflow.views.check_item_is_being_edit', return_value = "1")
    login(client=client, email=users[users_index]["email"])
    url = url_for("weko_workflow.edit_item_direct_after_login", pid_value="1")
    res = client.get(url)
    mock_render_template.assert_called_with("weko_theme/error.html", error="This Item is being edited.")
    assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_edit_item_direct_after_login_09 -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize(
    "users_index, status_code",
    [
        (1, 400),
        (2, 400),
        (3, 400),
        (6, 400),
    ],
)
def test_edit_item_direct_after_login_09(client, users, db_register, users_index, status_code, mocker):
    mock_render_template = mocker.patch('weko_workflow.views.render_template', return_value ='')
    mocker.patch('celery.task.control.inspect.ping', return_value='')
    mock_get_workflow_activity_by_item_id = mocker.patch.object(WorkActivity, 'get_workflow_activity_by_item_id', return_value = None)
    mocker.patch('weko_workflow.views.get_workflow_by_item_type_id', return_value=None)
    login(client=client, email=users[users_index]["email"])
    url = url_for("weko_workflow.edit_item_direct_after_login", pid_value="1")
    res = client.get(url)
    assert mock_get_workflow_activity_by_item_id.call_count == 2
    mock_render_template.assert_called_with("weko_theme/error.html", error="Workflow setting does not exist.")
    assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_edit_item_direct_after_login_10 -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize(
    "users_index, status_code",
    [
        (1, 302),
        (2, 302),
        (3, 302),
        (6, 302),
    ],
)
def test_edit_item_direct_after_login_10(client, users, db_register, users_index, status_code, mocker):
    mocker.patch('celery.task.control.inspect.ping', return_value="")
    mock_get_workflow_activity_by_item_id = mocker.patch.object(WorkActivity, 'get_workflow_activity_by_item_id', return_value = None)
    return_data_1 = MagicMock(id="1", flow_id="1")
    mocker.patch('weko_workflow.views.get_workflow_by_item_type_id', return_value=return_data_1)
    return_data_2 = MagicMock(activity_id=1)
    mocker.patch("weko_workflow.views.prepare_edit_workflow", return_value=return_data_2)
    login(client=client, email=users[users_index]["email"])
    url = url_for("weko_workflow.edit_item_direct_after_login", pid_value="1")
    res = client.get(url)
    assert mock_get_workflow_activity_by_item_id.call_count == 2
    assert res.status_code == status_code
    assert res.location == 'http://test_server.localdomain/workflow/activity/detail/1'

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_edit_item_direct_after_login_11 -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize(
    "users_index, status_code",
    [
        (1, 500),
        (2, 500),
        (3, 500),
        (6, 500),
    ],
)
def test_edit_item_direct_after_login_11(client, users, db_register, users_index, status_code, mocker):
    mock_render_template = mocker.patch('weko_workflow.views.render_template', return_value ='')
    mocker.patch('celery.task.control.inspect.ping', return_value="")
    mocker.patch("weko_workflow.views.prepare_edit_workflow", side_effect=SQLAlchemyError)
    login(client=client, email=users[users_index]["email"])
    url = url_for("weko_workflow.edit_item_direct_after_login", pid_value="1")
    res = client.get(url)
    mock_render_template.assert_called_with("weko_theme/error.html", error="An error has occurred.")
    assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_edit_item_direct_after_login_12 -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize(
    "users_index, status_code",
    [
        (1, 500),
        (2, 500),
        (3, 500),
        (6, 500),
    ],
)
def test_edit_item_direct_after_login_12(client, users, db_register, users_index, status_code, mocker):
    mock_render_template = mocker.patch('weko_workflow.views.render_template', return_value ='')
    mocker.patch('celery.task.control.inspect.ping', return_value="")
    mocker.patch("weko_workflow.views.prepare_edit_workflow", side_effect=BaseException)
    login(client=client, email=users[users_index]["email"])
    url = url_for("weko_workflow.edit_item_direct_after_login", pid_value="1")
    res = client.get(url)
    mock_render_template.assert_called_with("weko_theme/error.html", error="An error has occurred.")
    assert res.status_code == status_code
