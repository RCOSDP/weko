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
from re import M
import threading
from traceback import print_tb
from typing_extensions import Self
from unittest.mock import MagicMock
from weko_workflow.api import WorkActivity
import pytest
from mock import patch
from flask import Flask, json, jsonify, url_for, session, make_response
from flask_babelex import gettext as _
from invenio_db import db
from sqlalchemy import func
from datetime import datetime
import uuid
from invenio_communities.models import Community
from invenio_pidstore.errors import PIDDoesNotExistError,PIDDeletedError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus

import weko_workflow.utils
from weko_workflow import WekoWorkflow
from weko_workflow.config import WEKO_WORKFLOW_TODO_TAB, WEKO_WORKFLOW_WAIT_TAB,WEKO_WORKFLOW_ALL_TAB
from flask_security import login_user
from weko_workflow.models import ActionFeedbackMail, Activity, ActionStatus, Action, WorkFlow, FlowDefine, FlowAction,FlowActionRole, ActivityAction
from invenio_accounts.testutils import login_user_via_session as login
from weko_workflow.views import unlock_activity, check_approval, get_feedback_maillist, save_activity, previous_action
from marshmallow.exceptions import ValidationError
from weko_records_ui.models import FilePermission
from weko_records.models import ItemMetadata


def response_data(response):
    return json.loads(response.data)


def test_index_acl_nologin(client,db_register2):
    """_summary_

    Args:
        client (FlaskClient): flask test client
    """
    url = url_for('weko_workflow.index')
    res =  client.get(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login', next="/workflow/",_external=True)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_index_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_index_acl(client, users, db_register2,users_index, status_code):
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



def test_iframe_success(client, db_register,users, db_records,mocker):
    mock_render_template = MagicMock(return_value=jsonify({}))
    item = db_records[0][3]
    session = {
        "itemlogin_id":"1",
        "itemlogin_activity":db_register["activities"][1],
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
        mock_render_template.assert_called()

    session = {
        "itemlogin_id":"1",
        "itemlogin_activity":db_register["activities"][1],
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
        mock_render_template.assert_called()

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
        "itemlogin_activity":db_register["activities"][1],
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
        "itemlogin_activity":db_register["activities"][1],
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
        "itemlogin_activity":db_register["activities"][1],
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
        "itemlogin_activity":db_register["activities"][1],
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
        "itemlogin_activity":db_register["activities"][1],
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
    assert res.location == url_for('security.login', next="/workflow/activity/init",_external=True)


@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_init_activity_acl(client, users, users_index, status_code,db_register):
    """_summary_

    Args:
        client (_type_): _description_
        users (_type_): _description_
        users_index (_type_): _description_
        status_code (_type_): _description_
        db_register (_type_): _description_
    """
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.init_activity')
    input = {'workflow_id': db_register['workflow'].id, 'flow_id': db_register['flow_define'].id}
    res = client.post(url, json=input)
    assert res.status_code == status_code

@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_init_activity(client, users,users_index, status_code,db_register):
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.init_activity')
    input = {'workflow_id': db_register['workflow'].id, 'flow_id': db_register['flow_define'].id}
    res = client.post(url, json=input)
    assert res.status_code == status_code

    input = {'workflow_id': -99, 'flow_id': db_register['flow_define'].id}
    res = client.post(url, json=input)
    assert res.status_code == 500

    input = {'workflow_id': db_register['workflow'].id, 'flow_id': -99}
    res = client.post(url, json=input)
    assert res.status_code == 500


    input = {'workflow_id': db_register['workflow'].id}
    res = client.post(url, json=input)
    assert res.status_code == 400

    input = {'flow_id': db_register['flow_define'].id}
    res = client.post(url, json=input)
    assert res.status_code == 400

    input = {}
    res = client.post(url, json=input)
    assert res.status_code == 400

    input = {'workflow_id': str(db_register['workflow'].id), 'flow_id': str(db_register['flow_define'].id)}
    res = client.post(url, json=input)
    assert res.status_code == 200

    input = {'workflow_id': 'd'+str(db_register['workflow'].id), 'flow_id': str(db_register['flow_define'].id)}
    res = client.post(url, json=input)
    assert res.status_code == 400

    input = {'workflow_id': str(db_register['workflow'].id)+'d', 'flow_id': str(db_register['flow_define'].id)}
    res = client.post(url, json=input)
    assert res.status_code == 400

    input = {'workflow_id': None, 'flow_id': db_register['flow_define'].id}
    res = client.post(url, json=input)
    assert res.status_code == 400

    input = {'workflow_id': db_register['workflow'].id, 'flow_id': None}
    res = client.post(url, json=input)
    assert res.status_code == 400

    input = {'workflow_id': db_register['workflow'].id, 'flow_id': db_register['flow_define'].id, 'itemtype_id': db_register['item_type'].id}
    res = client.post(url, json=input)
    assert res.status_code == 200

    input = {'workflow_id': db_register['workflow'].id, 'flow_id': db_register['flow_define'].id, 'unknown':'unknown'}
    res = client.post(url, json=input)
    assert res.status_code == 200




def test_init_activity_guest_nologin(client,db_register2):
    """Test init activity for guest user."""
    url = url_for('weko_workflow.init_activity_guest')
    input = {'guest_mail': 'test@guest.com', 'workflow_id': 1, 'flow_id': 1,
             'item_type_id': 1, 'record_id': 1, 'guest_item_title': 'test',
             'file_name': 'test_file'}

    res = client.post(url, json=input)
    assert res.status_code == 200


@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_init_activity_guest_users(client, users, users_index, status_code):
    """Test init activity for guest user."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.init_activity_guest')
    input = {'guest_mail': 'test@guest.com', 'workflow_id': 1, 'flow_id': 1,
             'item_type_id': 1, 'record_id': 1, 'guest_item_title': 'test',
             'file_name': 'test_file'}

    res = client.post(url, json=input)
    assert res.status_code == status_code


def test_find_doi_nologin(client,db_register2):
    """Test of find doi."""
    url = url_for('weko_workflow.find_doi')
    input = {}

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
def test_find_doi_users(client, users, users_index, status_code):
    """Test of find doi."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.find_doi')
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == status_code


def test_save_activity_acl_nologin(client):
    """Test of save activity."""
    url = url_for('weko_workflow.save_activity')
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/save_activity_data",_external=True)


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
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}
    with patch('weko_workflow.views.save_activity_data'):
        res = client.post(url, json=input)
        assert res.status_code != 302 

def test_save_activity_acl_guestlogin(guest):
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}
    url = url_for('weko_workflow.save_activity')

    res = guest.post(url, json=input)
    assert res.status_code != 302
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_save_activity(client, users, db_register, users_index, status_code):
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.save_activity')
    
    input = {"activity_id":"A-20220921-00001","title":"test"}
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code== 400
    assert data["code"] == -1
    assert data["msg"] == "{'shared_user_id': ['Missing data for required field.']}"
    
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}
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
def test_save_activity_guestlogin(guest):
    url = url_for('weko_workflow.save_activity')
    
    input = {"activity_id":"A-20220921-00001","title":"test"}
    res = guest.post(url, json=input)
    data = response_data(res)
    assert res.status_code== 400
    assert data["code"] == -1
    assert data["msg"] == "{'shared_user_id': ['Missing data for required field.']}"

    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}
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
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_save_feedback_maillist_users(client, users, db_register, users_index, status_code):
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

    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        assert res.status_code == status_code


def test_previous_action_acl_nologin(client,db_register2):
    """Test of previous action."""
    url = url_for('weko_workflow.previous_action', activity_id='1',
                  action_id=1, req=1)
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/activity/action/1/1/rejectOrReturn/1",_external=True)


@pytest.mark.parametrize('users_index, status_code, is_admin', [
    (0, 403, False),
    (1, 403, True),
    (2, 403, True),
    (3, 403, True),
    (4, 403, False),
    (5, 403, False),
    (6, 403, True),
])
def test_previous_action_acl_users(client, users, db_register, users_index, status_code, is_admin):
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
    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
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

    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
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

    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code != status_code
        assert data["code"] != 403

@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_previous_action(client, users, db_register, users_index, status_code):
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
    with patch("weko_workflow.views.WorkActivity.get_activity_by_id",side_effect=[db_register["activities"][0],None]):
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


def test_next_action_acl_nologin(client, db_register_fullaction):
    """Test of next action."""
    url = url_for('weko_workflow.next_action', activity_id='1',
                  action_id=1)
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/activity/action/1/1",_external=True)


@pytest.mark.parametrize('users_index, status_code, is_admin', [
    (0, 403, False),
    (1, 403, True),
    (2, 403, True),
    (3, 403, True),
    (4, 403, False),
    (5, 403, False),
    (6, 403, True),
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

    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        assert res.status_code != status_code

    action_users = {
        'allow': [],
        'deny': [users[users_index]["id"]]
    }
    url = url_for('weko_workflow.next_action',
                  activity_id='2',
                  action_id=1)
    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
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
    url = url_for('weko_workflow.next_action',
                  activity_id='3',
                  action_id=1)
    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code != status_code
        assert data["code"] != 403

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
    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = guest.post(url, json=input)
        assert res.status_code != 403

@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_next_action(client, db, users, db_register_fullaction, db_records, users_index, status_code, mocker):
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
    url = url_for("weko_workflow.next_action",
            activity_id="1", action_id=1)
    with patch("weko_workflow.views.WorkActivity.get_activity_by_id",side_effect=[db_register_fullaction["activities"][0],None]):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "can not get activity detail"

    # cannot get schema
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
    update_activity_order("2",7,5)
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
    update_activity_order("2",2,7)
    url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=2)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == 200
    assert data["code"] == 0
    assert data["msg"] == "success"


    # action: item register
    ## not exist pid_without_ver
    url = url_for("weko_workflow.next_action",
                  activity_id="1", action_id=3)
    update_activity_order("1",3,2)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == 500
    assert data["code"] == -1
    assert data["msg"] == "can not get pid_without_ver"
    ## not exist record
    with patch("weko_workflow.views.WekoRecord.get_record_by_pid",return_value=None):
        update_activity_order("2",3,2)
        input = {"temporary_save":1}
        url = url_for("weko_workflow.next_action",
                      activity_id="2", action_id=3)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "can not get record"

    with patch("weko_workflow.views.PersistentIdentifier.get_by_object",side_effect=PIDDoesNotExistError("recid","wrong value")):
        update_activity_order("2",3,2)
        input = {"temporary_save":1}
        url = url_for("weko_workflow.next_action",
                      activity_id="2", action_id=3)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "can not get PersistentIdentifier"
    with patch("weko_workflow.views.WekoDeposit.get_record", return_value=None):
        update_activity_order("2",3,2)
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
    update_activity_order("2",3,2)
    input = {"temporary_save":1}
    url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=3)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == 200
    assert data["code"] == 0
    assert data["msg"] == "success"

    ## temporary_save=0
    ###x activity action update faild
    with patch("weko_workflow.views.WorkActivity.upt_activity_action",return_value=False):
        update_activity_order("2",3,2)
        input = {"temporary_save":0}
        url = url_for("weko_workflow.next_action",
                      activity_id="2", action_id=3)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -2
        assert data["msg"] == ""

    # action: oa policy
    ## temporary_save = 1
    ### in journal
    update_activity_order("2",6,3)
    input = {"temporary_save":1,
             "journal":{"issn":"test issn"}}
    url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=6)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == 200
    assert data["code"] == 0
    assert data["msg"] == "success"

    ## temporary_save = 0
    update_activity_order("2",6,3)
    input = {"temporary_save":0,
             "journal":{"issn":"test issn"}}
    url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=6)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == 200
    assert data["code"] == 0
    assert data["msg"] == "success"

    # action: item link
    ## temporary_save = 0
    ### exist pid_without_ver, exist link_data
    update_activity_order("2",5,4)
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
    ####x raise except
    update_activity_order("2",5,4)
    err_msg = "test update error"
    with patch("weko_workflow.views.ItemLink.update",return_value=err_msg):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == err_msg
    ## temporary_save = 1
    update_activity_order("2",5,4)
    input = {
        "temporary_save":1,
        "link_data":[]
    }
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"

    # action: identifier grant
    ## exist identifier_select
    ###x temporary_save = 1
    update_activity_order("2",7,5)
    input = {
        "temporary_save":1,
        "identifier_grant":"1",
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
    input = {
        "temporary_save":0,
        "identifier_grant":"0",
        "identifier_grant_jalc_doi_suffix":"",
        "identifier_grant_jalc_cr_doi_suffix":"",
        "identifier_grant_jalc_dc_doi_suffix":"",
        "identifier_grant_ndl_jalc_doi_suffix":""
    }
    update_activity_order("2",7,5)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"

    ###### not _old_v
    input = {
        "temporary_save":0,
        "identifier_grant":"0",
        "identifier_grant_jalc_doi_suffix":"",
        "identifier_grant_jalc_cr_doi_suffix":"",
        "identifier_grant_jalc_dc_doi_suffix":"",
        "identifier_grant_ndl_jalc_doi_suffix":""
    }
    with patch("weko_workflow.views.IdentifierHandle.get_idt_registration_data",return_value=(None, None)):
        update_activity_order("2",7,5)
        url = url_for("weko_workflow.next_action",
                activity_id="2", action_id=7)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == status_code
        assert data["code"] == 0
        assert data["msg"] == "success"

    ###### _old_v & _old_v = _new_v
    update_activity_order("7",7,5)
    url = url_for("weko_workflow.next_action",
            activity_id="7", action_id=7)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    ##### item_id == pid_without_ver
    ###### _value
    update_activity_order("6",7,5)
    url = url_for("weko_workflow.next_action",
            activity_id="6", action_id=7)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"

    ###### not _value
    with patch("weko_workflow.views.IdentifierHandle.get_idt_registration_data",return_value=(None,None)):
        update_activity_order("6",7,5)
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
        "identifier_grant":"1",
        "identifier_grant_jalc_doi_suffix":"",
        "identifier_grant_jalc_cr_doi_suffix":"",
        "identifier_grant_jalc_dc_doi_suffix":"",
        "identifier_grant_ndl_jalc_doi_suffix":""
    }
    url = url_for("weko_workflow.next_action",
            activity_id="2", action_id=7)
    test_msg = _('Cannot register selected DOI for current Item Type of this '
                 'item.')
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=test_msg):
        update_activity_order("2",7,5)
        res = client.post(url,json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == test_msg

    #####x error_list
    mock_previous_action = mocker.patch("weko_workflow.views.previous_action",return_value=make_response())
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=True):
        update_activity_order("2",7,5)
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
        update_activity_order("5",7,5)
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
        update_activity_order("2",7,5)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == status_code
        assert data["code"] == 0
        assert data["msg"] == "success"
    ####### not (deposit and pid_without_ver and not recid)
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=False):
        url = url_for("weko_workflow.next_action",
            activity_id="5", action_id=7)
        update_activity_order("5",7,5)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == status_code
        assert data["code"] == 0
        assert data["msg"] == "success"


    url = url_for("weko_workflow.next_action",
            activity_id="2", action_id=7)
    ## not exist identifier_select & not temporary_save
    input = {
        "temporary_save":0,
        "identifier_grant_jalc_doi_suffix":"",
        "identifier_grant_jalc_cr_doi_suffix":"",
        "identifier_grant_jalc_dc_doi_suffix":"",
        "identifier_grant_ndl_jalc_doi_suffix":""
    }
    ### _value and _type
    ####x error_list is str
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=test_msg):
        update_activity_order("2",7,5)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] ==-1
        assert data["msg"] == test_msg
    ####x error_list is not str & error_list = True
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=True):
        update_activity_order("2",7,5)
        res = client.post(url, json=input)
        assert res.status_code == status_code
        mock_previous_action.assert_called_with(
            activity_id="2",
            action_id=7,
            req=-1
        )
    #### error_list is not str & error_list = False
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=False):
        update_activity_order("2",7,5)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == status_code
        assert data["code"] == 0
        assert data["msg"] == "success"
    ### not (_value and _type)
    url = url_for("weko_workflow.next_action",
                  activity_id="3", action_id=7)
    update_activity_order("3",7,5)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"]==0
    assert data["msg"] == "success"

    ## next_action_handler is None
    activity_action = ActivityAction.query.filter_by(
        activity_id="2",
        action_id=4,
        action_order=6
    ).first()
    activity_action.action_handler=None
    db.session.merge(activity_action)
    db.session.commit()
    url = url_for("weko_workflow.next_action",
                  activity_id="2",action_id=7)
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=False):
        update_activity_order("2",7,5)
        res = client.post(url, json=input)
        data=response_data(res)
        assert res.status_code == 500
        assert data["code"] == -2
        assert data["msg"] == "can not get next_action_handler"
    activity_action = ActivityAction.query.filter_by(
        activity_id="2",
        action_id=4,
        action_order=6
    ).first()
    activity_action.action_handler=-1
    db.session.merge(activity_action)
    db.session.commit()

    ## exist next_flow_action.action_roles
    flow_action_role = FlowActionRole(
        flow_action_id=db_register_fullaction["flow_actions"][5].id,
        action_role=None,
        action_user=1
    )
    with db.session.begin_nested():
        db.session.add(flow_action_role)
    db.session.commit()
    url = url_for("weko_workflow.next_action",
                  activity_id="2",action_id=7)
    with patch("weko_workflow.views.check_doi_validation_not_pass",return_value=False):
        update_activity_order("2",7,5)
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
        update_activity_order("2",4,6)
        res = client.post(url, json=input)
        data = response_data(res)
        result_status = 500 if check_role_approval() else 200
        result_code = -1 if check_role_approval() else 403
        result_msg = "can not get curretn_flow_action" if check_role_approval() else noauth_msg
        assert res.status_code == result_status
        assert data["code"] == result_code
        assert data["msg"] == result_msg

    with patch("weko_workflow.views.handle_finish_workflow",side_effect=mock_handle_finish_workflow):
        url = url_for("weko_workflow.next_action",
                      activity_id="2",action_id=4)
        ##x not exist next_action_detail
        with patch("weko_workflow.views.WorkActivity.get_activity_action_comment", return_value=None):
            update_activity_order("2",4,6)
            res = client.post(url, json=input)
            data = response_data(res)
            result_status = 500 if check_role_approval() else 200
            result_code = -2 if check_role_approval() else 403
            result_msg = "can not get next_action_detail" if check_role_approval() else noauth_msg
            assert res.status_code == result_status
            assert data["code"] == result_code
            assert data["msg"] == result_msg

        ## can create_onetime_download_url
        onetime_download = {"tile_url":"test_file"}
        with patch("weko_workflow.views.create_onetime_download_url_to_guest",return_value=onetime_download):
            update_activity_order("2",4,6)
            res = client.post(url, json=input)
            data = response_data(res)
            result_code = 0 if check_role_approval() else 403
            result_msg = _("success") if check_role_approval() else noauth_msg
            assert res.status_code == status_code
            assert data["code"] == result_code
            assert data["msg"] == result_msg

        ## exist feedbackmail
        ### exist feedbackmail, exist maillist
        update_activity_order("2",4,6)
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
        update_activity_order("3",4,6)
        res = client.post(url, json=input)
        data = response_data(res)
        result_code = 0 if check_role_approval() else 403
        result_msg = "success" if check_role_approval() else noauth_msg
        assert res.status_code == status_code
        assert data["code"] == result_code
        assert data["msg"] == result_msg

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
        update_activity_order("3",4,6)
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
        update_activity_order("4",4,6)
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
        with patch("weko_workflow.views.has_request_context",side_effect=BaseException):
            update_activity_order("5",4,6)
            res = client.post(url, json=input)
            result_status_code = 500 if check_role_approval() else 200
            assert res.status_code == result_status_code
            if not check_role_approval():
                data = response_data(res)
                assert data["code"] == 403
                assert data["msg"] == noauth_msg

        ## send signal
        url = url_for("weko_workflow.next_action",
                      activity_id="5",action_id=4)
        update_activity_order("5",4,6)
        res = client.post(url, json=input)
        data = response_data(res)
        result_code = 0 if check_role_approval() else 403
        result_msg = "success" if check_role_approval() else noauth_msg
        assert res.status_code == status_code
        assert data["code"] == result_code
        assert data["msg"] == result_msg


    ## can not publish
    with patch("weko_workflow.views.handle_finish_workflow",return_value=None):
        url = url_for("weko_workflow.next_action",
                      activity_id="2",action_id=4)
        update_activity_order("2",4,6)
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
        update_activity_order("2",3,2)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -2
        assert data["msg"] == "can not get next_flow_action"


    # not rtn
    with patch("weko_workflow.views.WorkActivityHistory.create_activity_history", return_value=None):
        url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=3)
        update_activity_order("2",3,2)
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "error"

    # action_status update faild
    with patch("weko_workflow.views.WorkActivity.upt_activity_action_status", return_value=False):
        url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=3)
        update_activity_order("2",3,2)
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
    update_activity_order("2",3,2)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == 200
    assert data["code"] == 0
    assert data["msg"] == _("success")


def test_cancel_action_acl_nologin(client,db_register2):
    """Test of cancel action."""
    url = url_for('weko_workflow.cancel_action',
                  activity_id='1', action_id=1)
    input = {'action_version': 1, 'commond': 1}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for('security.login', next="/workflow/activity/action/1/1/cancel",_external=True)


@pytest.mark.parametrize('users_index, status_code, is_admin', [
    (0, 403, False),
    (1, 403, True),
    (2, 403, True),
    (3, 403, True),
    (4, 403, False),
    (5, 403, False),
    (6, 403, True),
])
def test_cancel_action_acl_users(client, users, db_register, users_index, status_code, is_admin):
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

    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        assert res.status_code != status_code

    action_users = {
        'allow': [],
        'deny': [users[users_index]["id"]]
    }
    url = url_for('weko_workflow.cancel_action',
                  activity_id='2', action_id=1)
    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
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
    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code != status_code
        assert data["code"] != 403

def test_cancel_action_acl_guestlogin(guest, db_register):
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

    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = guest.post(url, json=input)
        assert res.status_code != 403

@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_cancel_action(client, users, db_register, db_records, add_file, users_index, status_code, mocker):
    login(client=client, email=users[users_index]['email'])
    #mocker.patch("weko_workflow.views.remove_file_cancel_action")
    # argument error
    with patch("weko_workflow.views.type_null_check",return_value=False):
        url = url_for('weko_workflow.cancel_action',
                  activity_id='1', action_id=1)
        res = client.post(url, json={})
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "argument error"

    # request_body error
    url = url_for('weko_workflow.cancel_action',
              activity_id='1', action_id=1)
    with patch("weko_workflow.views.CancelSchema",side_effect=ValidationError("test error")):
        res = client.post(url, json={})
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "test error"

    # can not get activity_detail
    input = {
        "action_version":"1.0.0",
        "commond":"this is test comment.",
        "pid_value":"1.1"
        }
    with patch("weko_workflow.views.WorkActivity.get_activity_by_id",side_effect=[db_register["activities"][0],None]):
        url = url_for('weko_workflow.cancel_action',
                      activity_id='1', action_id=1)
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
    FilePermission.init_file_permission(users[users_index]["id"],"1.1","test_file","1")
    add_file(db_records[2][2])
    url = url_for('weko_workflow.cancel_action',
                  activity_id='1', action_id=1)
    redirect_url = url_for("weko_workflow.display_activity",
                           activity_id="1").replace("http://test_server.localdomain","")
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    assert data["data"]["redirect"] == redirect_url

    ## raise PIDDoesNotExistError
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
        res = client.post(url, json=input)
        data = response_data(res)
        redirect_url = url_for("weko_workflow.display_activity",
                       activity_id="1").replace("http://test_server.localdomain","")
        assert res.status_code == 200
        assert data["code"] == 0
        assert data["msg"] == "success"
        assert data["data"]["redirect"] == redirect_url

    # exist item, not exist files, not exist file_permission
    input = {
        "action_version": "1.0.0",
        "commond":"this is test comment."
    }
    url = url_for("weko_workflow.cancel_action",
                  activity_id="2", action_id=1)
    redirect_url = url_for("weko_workflow.display_activity",
                           activity_id="2").replace("http://test_server.localdomain","")
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    assert data["data"]["redirect"] == redirect_url

    # not cancel_record, not exist rtn
    with patch("weko_workflow.views.WekoDeposit.get_record", return_value=None):
        with patch("weko_workflow.views.WorkActivity.quit_activity", return_value=None):
            res = client.post(url, json = input)
            data = response_data(res)
            assert res.status_code == 500
            assert data["code"] == -1
            assert data["msg"] == 'Error! Cannot process quit activity!'

    ## raise PIDDoesNotExistError
    with patch("weko_workflow.views.PersistentIdentifier.get_by_object",side_effect=PIDDoesNotExistError("recid","test pid")):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "can not get PersistentIdentifier"

    # raise exception
    with patch("weko_workflow.views.PersistentIdentifier.get_by_object", side_effect=Exception):
        res = client.post(url, json = input)
        data = response_data(res)
        assert res.status_code == 500
        assert data["code"] == -1
        assert data["msg"] == "<class 'Exception'>"



def test_cancel_action_guest(guest, db, db_register):
    input = {
        "action_version": "1.0.0",
        "commond":"this is test comment."
    }
    activity_guest = Activity(activity_id="99",workflow_id=1,flow_id=db_register["flow_define"].id,
                              action_id=1,
                              activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                              title="test guest", extra_info={"guest_mail":"guest@test.org"},
                              action_order=1)
    with db.session.begin_nested():
        db.session.add(activity_guest)
    db.session.commit()
    url = url_for("weko_workflow.cancel_action",
                  activity_id="99", action_id=1)
    redirect_url = url_for("weko_workflow.display_guest_activity",file_name="test_file")
    res = guest.post(url, json=input)
    data = response_data(res)
    assert res.status_code == 200
    assert data["code"] == 0
    assert data["msg"] == "success"
    assert data["data"]["redirect"] == redirect_url


def test_send_mail_nologin(client,db_register2):
    """Test of send mail."""
    url = url_for('weko_workflow.send_mail', activity_id='1',
                  mail_template='a')
    input = {}

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
def test_send_mail_users(client, users, users_index, status_code):
    """Test of send mail."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.send_mail', activity_id='1',
                  mail_template='a')
    input = {}
    with patch('weko_workflow.views.process_send_reminder_mail'):
        res = client.post(url, json=input)
        assert res.status_code == status_code


def test_lock_activity_nologin(client,db_register2):
    """Test of lock activity."""
    url = url_for('weko_workflow.lock_activity', activity_id='1')
    input = {}

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

@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_lock_activity(client, users,db_register, users_index, status_code):
    """Test of lock activity."""
    login(client=client, email=users[users_index]['email'])

    #regular
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}

    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, data=input)
            assert res.status_code == status_code

    #locked value  is validate error
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': 1661748792565}

    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, data=input)
            assert res.status_code == status_code

    #lock cache is different
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}

    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792568"):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, data=input)
            assert res.status_code == status_code

    #action_handler is None
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}

    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, data=input)
            assert res.status_code == status_code

    #activity_id is type error
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}

    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.type_null_check',return_value=False):
            with patch('weko_workflow.views.update_cache_data'):
                res = client.post(url, data=input)
                assert res.status_code == 500

    #request vaidate error
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {}

    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            with patch("weko_workflow.views.LockSchema",side_effect=ValidationError("test error")):
                res = client.post(url, data=input)
                assert res.status_code == 500

    # locked_by_email, locked_by_username is not exist
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}
    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            with patch("weko_workflow.views.get_account_info",return_value=(None,None)):
                res = client.post(url, data=input)
                assert res.status_code == 500
    
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
    activity_action = ActivityAction.query.filter_by(
        activity_id="A-00000003-00000",
        action_id=1,
        action_order=1
    ).first()
    activity_action.action_handler=0
    db.session.merge(activity_action)
    db.session.commit()


def test_unlock_activity_acl_nologin(client,db_register2):
    """Test of unlock activity."""
    url = url_for('weko_workflow.unlock_activity', activity_id='1')
    input = {'locked_value':'1-1661748792565'}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/activity/unlock/1",_external=True)

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

@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_unlock_activity(client, users, db_register, users_index, status_code):
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
    with patch('weko_workflow.views.get_cache_data', return_value=""):
        res = client.post(url, json=input)
        data = json.loads(res.data.decode("utf-8"))
        assert res.status_code==status_code
        assert data["code"] == 200
        assert data["msg"] == 'Not unlock'

    #locked_valueが空でなく、cur_locked_valと一致する場合
    with patch('weko_workflow.views.get_cache_data', return_value='1-1661748792565'):
        with patch('weko_workflow.views.delete_cache_data'):
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

def test_check_approval_acl_nologin(client,db_register2):
    """Test of check approval."""
    url = url_for('weko_workflow.check_approval', activity_id='1')

    res = client.get(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/check_approval/1",_external=True)

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


@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_check_approval(client, users, db_register, users_index, status_code):
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

def test_get_feedback_maillist_acl_nologin(client,db_register2):
    """Test of get feedback maillist."""
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='1')

    res = client.get(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/get_feedback_maillist/1",_external=True)

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

@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_get_feedback_maillist(client, users, db_register, users_index, status_code):
    login(client=client, email=users[users_index]['email'])

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
    mail_list = db_register['action_feedback_mail'].feedback_maillist
    assert res.status_code==status_code
    assert data['code'] == 1
    assert data['msg'] == 'Success'
    assert data['data'] == mail_list

    url = url_for('weko_workflow.get_feedback_maillist', activity_id='5')
    res = client.get(url)
    data = response_data(res)
    mail_list = db_register['action_feedback_mail1'].feedback_maillist
    assert res.status_code==status_code
    assert data['code'] == 1
    assert data['msg'] == 'Success'
    assert data['data'] == mail_list

    url = url_for('weko_workflow.get_feedback_maillist', activity_id='6')
    res = client.get(url)
    data = response_data(res)
    mail_list = db_register['action_feedback_mail2'].feedback_maillist
    assert res.status_code==status_code
    assert data['code'] == 1
    assert data['msg'] == 'Success'
    assert data['data'] == mail_list

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
    assert res.status_code==400
    assert data['code'] == -1
    assert data['msg'] == 'mail_list is not list'

def test_save_activity_acl_nologin(client,db_register2):
    """Test of save activity."""
    url = url_for('weko_workflow.save_activity')
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/save_activity_data",_external=True)

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
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}
    with patch('weko_workflow.views.save_activity_data'):
        res = client.post(url, json=input)
        assert res.status_code != 302


#save_activityは@login_required_customizeなのでguestuserloginのテストも必要
def test_save_activity_acl_guestlogin(guest,db_register2):
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}
    url = url_for('weko_workflow.save_activity')

    res = guest.post(url, json=input)
    assert res.status_code != 302


@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_save_activity(client, users, db_register, users_index, status_code):
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.save_activity')

    input = {"activity_id":"A-20220921-00001","title":"test"}
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code== 400
    assert data["code"] == -1
    assert data["msg"] == "{'shared_user_id': ['Missing data for required field.']}"

    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}
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


# guestuserでの機能テスト
def test_save_activity_guestlogin(guest,db_register2):
    url = url_for('weko_workflow.save_activity')

    input = {"activity_id":"A-20220921-00001","title":"test"}
    res = guest.post(url, json=input)
    data = response_data(res)
    assert res.status_code== 400
    assert data["code"] == -1
    assert data["msg"] == "{'shared_user_id': ['Missing data for required field.']}"

    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}
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


def test_display_activity_nologin(client,db_register2):
    """Test of display activity."""
    url = url_for('weko_workflow.display_activity', activity_id='1')
    input = {}

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
def test_display_activity_users(client, users, db_register, users_index, status_code):
    """
    Test of display activity.
    Expected: users[0]: AssertionError
    """
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
    mock_render_template = MagicMock(return_value=jsonify({}))
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.check_authority_action'):
            with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
                       return_value=(roles, action_users)):
                with patch('weko_workflow.views.render_template', mock_render_template):
                    res = client.post(url, json=input)
                    mock_render_template.assert_called()

@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_display_activity(client, users, db_register, users_index, status_code,mocker,redis_connect):
    login(client=client, email=users[users_index]['email'])

    workflow_detail = WorkFlow.query.filter_by(id=1).one_or_none()
    mock_render_template = MagicMock(return_value=jsonify({}))

    activity_detail = Activity.query.filter_by(activity_id='A-00000001-10001').one_or_none()
    #activity_detail = Activity.query.filter_by(activity_id='1').one_or_none()
    cur_action = activity_detail.action
    action_endpoint = 'item_login'
    #action_endpoint = cur_action.action_endpoint
    action_id = cur_action.id
    histories = 1
    item_metadata = ItemMetadata()
    item_metadata.id = '37075580-8442-4402-beee-05f62e6e1dc2'
    # item_metadata = {'created':datetime.strptime("2022-09-22 05:09:54.677307", "%Y-%m-%d %H:%M:%S.%f"),'updated':datetime.strptime("2022-09-22 05:09:54.677307", "%Y-%m-%d %H:%M:%S.%f"),
    #                 'id':'37075580-8442-4402-beee-05f62e6e1dc2','item_type_id':15,'json': {"id": "1", "pid": {"type": "depid", "value": "1", "revision_id": 0}, "lang": "ja", "owner": "1", "title": "title", "owners": [1], "status": "published", "$schema": "/items/jsonschema/15", "pubdate": "2022-08-20", "created_by": 1, "owners_ext": {"email": "wekosoftware@nii.ac.jp", "username": "", "displayname": ""}, "shared_user_id": -1, "item_1617186331708": [{"subitem_1551255647225": "ff", "subitem_1551255648112": "ja"}], "item_1617258105262": {"resourceuri": "http://purl.org/coar/resource_type/c_5794", "resourcetype": "conference paper"}}
    #                 ,'version_id':3}
    item = None
    steps = 1
    temporary_comment = 1


    test_pid = PersistentIdentifier()
    test_pid.pid_value = '1'
    # test_pid= dict(created=datetime.strptime("2022-09-22 05:09:48.085724", "%Y-%m-%d %H:%M:%S.%f"),updated=datetime.strptime("2022-09-22 05:09:48.085747", "%Y-%m-%d %H:%M:%S.%f"),
    #             id=3, pid_type='recid',pid_value='1',pid_provider='',status='R',object_type='rec',object_uuid='37075580-8442-4402-beee-05f62e6e1dc2')
    test_comm= Community()
    test_comm.id = 'test'
    # test_comm=  dict(created=datetime.strptime("2022-09-22 05:09:48.085724", "%Y-%m-%d %H:%M:%S.%f"),updated=datetime.strptime("2022-09-22 05:09:48.085747", "%Y-%m-%d %H:%M:%S.%f"),
    #             id='test',id_role=1,id_user=1,title='test',description='',page='',curation_policy='',community_header='',community_footer='',last_record_accepted=datetime.strptime("2000-01-01 00:00:00", "%Y-%m-%d %H:%M:%S"),
    #             logo_ext='',ranking=0,fixed_points=0,deleted_at=None,root_node_id=1557819733276)
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

    mocker.patch('weko_workflow.views.WorkActivity.get_activity_action_role',
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

    #template_url is None
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = None

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

    #Json_schema is None
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {}
    action_endpoint = 'item_login'
    template_url = "weko_items_ui/iframe/item_edit.html"
    json_schema = None

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

    #action_endpoint is identifier_grant and community is not root index
    url = url_for('weko_workflow.display_activity', activity_id='A-00000001-10001')
    input = {'community': 'test'}
    action_endpoint = 'identifier_grant'
    item = item_metadata

    with patch('weko_workflow.views.get_activity_display_info',
            return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
            steps, temporary_comment, workflow_detail)):
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
            steps, temporary_comment, workflow_detail)):
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
            steps, temporary_comment, workflow_detail)):
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

    #item is not None
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

def test_withdraw_confirm_nologin(client,db_register2):
    """Test of withdraw confirm."""
    url = url_for('weko_workflow.withdraw_confirm', activity_id='1',
                  action_id=1)
    input = {}

    res = client.post(url, json=input)
    assert res.location == url_for('security.login',next="/workflow/activity/detail/1/1/withdraw",
                                    _external=True)


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
    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
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
    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
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
    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code != status_code
        assert data["code"] != 403


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
    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
               return_value=(roles, action_users)):
        res = guest.post(url, json=input)
        assert res.status_code != 403


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
            with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
                return_value=(roles, action_users)):
                res = client.post(url, json=input)
                data = response_data(res)
                assert res.status_code == 500
                assert data["code"] == -1
                assert data["msg"] == "argument error"

    # Unexpected error check
    with patch('weko_workflow.views.type_null_check', side_effect=ValueError):
        with patch('weko_workflow.views.IdentifierHandle'):
            with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
                return_value=(roles, action_users)):
                res = client.post(url, json=input)
                data = response_data(res)
                assert res.status_code == 500
                assert data["code"] == -1
                assert data["msg"] == "Error!"


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
            with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
                return_value=(roles, action_users)):
                res = guest.post(url, json=input)
                data = response_data(res)
                assert res.status_code == 500
                assert data["code"] == -1
                assert data["msg"] == "argument error"

    # Unexpected error check
    with patch('weko_workflow.views.type_null_check', side_effect=ValueError):
        with patch('weko_workflow.views.IdentifierHandle'):
            with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
                return_value=(roles, action_users)):
                res = guest.post(url, json=input)
                data = response_data(res)
                assert res.status_code == 500
                assert data["code"] == -1
                assert data["msg"] == "Error!"


input_data_list = [
    ({}, 500, -1, "{'passwd': ['Missing data for required field.']}"),
    ({"passwd": None}, 500, -1, "{'passwd': ['Field may not be null.']}"),
    ({"passwd": "DELETE"}, 500, -1, "bad identifier data"),
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
        with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
        return_value=(roles, action_users)):
            res = client.post(url, json=input)
            data = response_data(res)
            assert res.status_code == status_code
            assert data["code"] == code
            assert data["msg"] == msg


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
        with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
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
                    with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
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
                        with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
                        return_value=(roles, action_users)):
                            res = guest.post(url, json=input)
                            data = response_data(res)
                            assert res.status_code == status_code
                            assert data["code"] == code
                            assert data["msg"] == msg
                            assert data["data"] == {"redirect": "guest_url"}
