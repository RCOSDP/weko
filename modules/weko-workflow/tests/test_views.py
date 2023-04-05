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
import os
import threading
from traceback import print_tb
from typing_extensions import Self
from unittest.mock import MagicMock
from weko_workflow.api import WorkActivity
from sqlalchemy.exc import SQLAlchemyError
import responses
import pytest
from mock import patch
from flask import Flask, json, jsonify, url_for, session, make_response, current_app
from flask_babelex import gettext as _
from invenio_db import db
from sqlalchemy import func
from datetime import datetime
import uuid
from invenio_communities.models import Community
from invenio_pidstore.errors import PIDDoesNotExistError,PIDDeletedError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus

import weko_workflow.utils
from weko_admin.models import Identifier
from weko_workflow import WekoWorkflow
from weko_workflow.config import WEKO_WORKFLOW_TODO_TAB, WEKO_WORKFLOW_WAIT_TAB,WEKO_WORKFLOW_ALL_TAB
from flask_security import login_user
from weko_workflow.models import ActionFeedbackMail, Activity, ActionStatus, Action, WorkFlow, FlowDefine, FlowAction,FlowActionRole, ActivityAction, GuestActivity,ActivityHistory,ActionIdentifier,ActionJournal
from invenio_accounts.testutils import login_user_via_session as login
from marshmallow.exceptions import ValidationError
from weko_records_ui.models import FilePermission
from weko_records.models import ItemMetadata
from weko_workflow.views import (
    unlock_activity, check_approval, 
    get_feedback_maillist, 
    save_activity, 
    previous_action, 
    check_authority,
    check_authority_action,
    get_journal,
    ActivityActionResource
    )
from weko_workflow.errors import ActivityBaseRESTError

def response_data(response):
    return json.loads(response.data)


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_regex_replace -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_regex_replace(app):
    text = 'aaa@xxx.com bbb@yyy.com ccc@zzz.com'
    result = app.jinja_env.filters["regex_replace"](text, '[a-z]*@', 'ABC@')
    #result = app.jinja_env.filters["regex_replace"](text)
    assert result == "ABC@xxx.com ABC@yyy.com ABC@zzz.com"

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
@pytest.mark.parametrize('id, is_permission', [
    (0, True),
    (1, True),
    (2, True),
    (3, True),
    (4, True),
    (5, True),
    (6, True),
])
def test_index_acl(client, users, db_register2, id, is_permission):
    login(client=client, email=users[id]['email'])
    url = url_for('weko_workflow.index',_external=True)
    res = client.get(url)
    if is_permission:
        assert res.status_code != 403
    else:
        assert res.status_code == 403

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_index(app, users, db_register2,mocker):
    with app.test_client() as client:
        login(client=client, email=users[2]['email'])
        mocker.patch("weko_workflow.views.render_template",return_value=make_response())
        url = url_for('weko_workflow.index',_external=True)
        res = client.get(url)
        assert res.status_code == 200

        # with not exist community
        mocker.patch("weko_workflow.views.render_template",return_value=make_response())
        url = url_for('weko_workflow.index',community="a",_external=True)
        res = client.get(url)
        assert res.status_code == 200

        # with exist community
        mocker.patch("weko_workflow.views.render_template",return_value=make_response())
        url = url_for('weko_workflow.index',community="comm01",_external=True)
        res = client.get(url)
        assert res.status_code == 200

        app.config.update(
            WEKO_WORKFLOW_ENABLE_SHOW_ACTIVITY=True
        )
        mocker.patch("weko_workflow.views.render_template",return_value=make_response())
        url = url_for('weko_workflow.index',_external=True)
        res = client.get(url)
        assert res.status_code == 200
    
    with app.test_client() as client:
        # no role user
        mocker.patch("weko_workflow.views.render_template",return_value=make_response())
        login(client=client, email=users[7]['email'])
        url = url_for('weko_workflow.index',_external=True)
        res = client.get(url)
        assert res.status_code == 403

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_iframe_success -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_iframe_success(client, db, db_register,users, db_records,without_session_remove,mocker):
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

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_new_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_new_activity(client, users, db_register,without_session_remove):
    login(client=client, email=users[2]['email'])
    url = url_for("weko_workflow.new_activity")
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        res = client.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert args[0] == 'weko_workflow/workflow_list.html'
        assert kwargs["workflows"][0].id == 1

    # community in args, comm is None
    url = url_for("weko_workflow.new_activity",community="not_exist_comm")
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        res = client.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert args[0] == 'weko_workflow/workflow_list.html'
        assert kwargs["workflows"][0].id == 1
        assert kwargs["community"] == None
    
    # community in args, comm is not None
    url = url_for("weko_workflow.new_activity",community="comm01")
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        res = client.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert args[0] == 'weko_workflow/workflow_list.html'
        assert kwargs["workflows"][0].id == 1
        assert kwargs["community"].id == "comm01"
    
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

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_init_activity_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0, True),
    (1, True),
    (2, True),
    (3, True),
    (4, True),
    (5, True),
    (6, True),
])
def test_init_activity_acl(client, users, index, is_permission,db_register):
    """_summary_

    Args:
        client (_type_): _description_
        users (_type_): _description_
        index (_type_): _description_
        is_permission (_type_): _description_
        db_register (_type_): _description_
    """
    login(client=client, email=users[index]['email'])
    url = url_for('weko_workflow.init_activity')
    input = {}
    res = client.post(url, json=input)
    if is_permission:
        assert res.status_code != 403
    else:
        assert res.status_code == 403

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_init_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_init_activity(client, users,db_register,without_session_remove,mocker):
    
    login(client=client, email=users[2]['email'])
    url = url_for('weko_workflow.init_activity')
    with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_1"):
        input = {'workflow_id': db_register['workflow'].id, 'flow_id': db_register['flow_define'].id}
        res = client.post(url, json=input)
        assert json.loads(res.data) == {'code': 0, 'data': {'redirect': '/workflow/activity/detail/new_1'}, 'msg': 'success'}
        assert res.status_code == 200
        assert Activity.query.filter_by(activity_id="new_1").one() is not None
        
    # raise SQLAlchemyError
    print("tt2")
    with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_2"):
        input = {'workflow_id': -99, 'flow_id': db_register['flow_define'].id}
        res = client.post(url, json=input)
        assert res.status_code == 500
        
    # raise Exception
    with patch("weko_workflow.views.WorkActivity.init_activity",side_effect=Exception("test_error")):
        input = {'workflow_id': -99, 'flow_id': db_register['flow_define'].id}
        res = client.post(url, json=input)
        assert res.status_code == 500
        
    # bad request data
    with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_5"):
        input = {}
        res = client.post(url, json=input)
        assert res.status_code == 400
        
    # with exist community
    url = url_for("weko_workflow.init_activity",community="comm01")
    with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_13"):
        input = {'workflow_id': db_register['workflow'].id, 'flow_id': db_register['flow_define'].id}
        res = client.post(url, json=input)
        assert json.loads(res.data) == {'code': 0, 'data': {'redirect': '/workflow/activity/detail/new_13?community=comm01'}, 'msg': 'success'}
        assert res.status_code == 200
        assert Activity.query.filter_by(activity_id="new_1").one() is not None
        
    # with not exist community
    url = url_for("weko_workflow.init_activity",community="not_exist_comm")
    with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_14"):
        input = {'workflow_id': db_register['workflow'].id, 'flow_id': db_register['flow_define'].id}
        res = client.post(url, json=input)
        assert json.loads(res.data) == {'code': 0, 'data': {'redirect': '/workflow/activity/detail/new_14'}, 'msg': 'success'}
        assert res.status_code == 200
        assert Activity.query.filter_by(activity_id="new_1").one() is not None



    # 以下はinit_activityのif文の分岐が重複していたケース
    # ただ、例えばActivitySchema内での分岐は違う
    # そのテストを作るときに参考になる？
    # 存在しないflow_idでsqlalchemyerror
    #print("tt")
    #with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_3"):
    #    input = {'workflow_id': db_register['workflow'].id, 'flow_id': -99}
    #    res = client.post(url, json=input)
    #    assert res.status_code == 500
    
    # flow_idがリクエストデータに存在しない
    #print("tt")
    #with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_3"):
    #    input = {'workflow_id': db_register['workflow'].id}
    #    res = client.post(url, json=input)
    #    assert res.status_code == 400
    # workflow_idがリクエストデータに存在しない
    #print("tt")
    #with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_4"):
    #    input = {'flow_id': db_register['flow_define'].id}
    #    res = client.post(url, json=input)
    #    assert res.status_code == 400
    
    #print("tt4")
    #with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_6"):
    #    input = {'workflow_id': str(db_register['workflow'].id), 'flow_id': str(db_register['flow_define'].id)}
    #    res = client.post(url, json=input)
    #    assert res.status_code == 200
    # workflow_idをintにできない？
    #print("tt5")
    #with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_7"):
    #    input = {'workflow_id': 'd'+str(db_register['workflow'].id), 'flow_id': str(db_register['flow_define'].id)}
    #    res = client.post(url, json=input)
    #    print(json.loads(res.data))
    #    assert res.status_code == 400
    # ?
    #print("tt6")
    #with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_8"):
    #    input = {'workflow_id': str(db_register['workflow'].id)+'d', 'flow_id': str(db_register['flow_define'].id)}
    #    res = client.post(url, json=input)
    #    print(json.loads(res.data))
    #    assert res.status_code == 400
    #workflow_idがNone
    #print("tt7")
    #with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_9"):
    #    input = {'workflow_id': None, 'flow_id': db_register['flow_define'].id}
    #    res = client.post(url, json=input)
    #    print(json.loads(res.data))
    #    assert res.status_code == 400
    # flow_idがNone
    #print("tt8")
    #with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_10"):
    #    input = {'workflow_id': db_register['workflow'].id, 'flow_id': None}
    #    res = client.post(url, json=input)
    #    print(json.loads(res.data))
    #    assert res.status_code == 400
    #print("tt9")
    #with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_11"):
    #    input = {'workflow_id': db_register['workflow'].id, 'flow_id': db_register['flow_define'].id, 'itemtype_id': db_register['item_type'].id}
    #    res = client.post(url, json=input)
    #    assert res.status_code == 200
    #print("tt10")
    #with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_12"):
    #    input = {'workflow_id': db_register['workflow'].id, 'flow_id': db_register['flow_define'].id, 'unknown':'unknown'}
    #    res = client.post(url, json=input)
    #    assert res.status_code == 200

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_list_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_list_activity(client, users, db_register, without_session_remove):
    login(client=client, email=users[2]['email'])
    num_activitity = len(Activity.query.all())
    url = url_for("weko_workflow.list_activity")
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        res = client.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert args[0] == 'weko_workflow/activity_list.html'
        assert len(kwargs["activities"]) == num_activitity
        assert kwargs["tab"] == "todo"

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_init_activity_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_init_activity_guest(app,client,db_register2,db_register):
    """Test init activity for guest user."""
    url = url_for('weko_workflow.init_activity_guest')
    input = {'guest_mail': 'test@guest.com', 'workflow_id': 1, 'flow_id': 1,
             'item_type_id': 1, 'record_id': 1, 'guest_item_title': 'test',
             'file_name': 'test_file'}
    
    # success send mail
    with patch("weko_workflow.views.send_usage_application_mail_for_guest_user",return_value=True):
        with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_1"):
            res = client.post(url, json=input)
            print(json.loads(res.data))
            assert res.status_code == 200
            assert json.loads(res.data) == {'msg': 'Email is sent successfully.'}
    # failed send mail
    with patch("weko_workflow.views.send_usage_application_mail_for_guest_user",return_value=False):
        with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new_2"):
            res = client.post(url, json=input)
            assert res.status_code == 200
            assert json.loads(res.data) == {'msg': 'Cannot send mail'}
    
    # raise SQLAlchemyError
    with patch("weko_workflow.views.init_activity_for_guest_user",side_effect=SQLAlchemyError("test_sql_error")):
        res = client.post(url, json=input)
        assert res.status_code == 200
        assert json.loads(res.data) == {'msg': 'Cannot send mail'}

    # raise Exception
    with patch("weko_workflow.views.init_activity_for_guest_user",side_effect=Exception("test_error")):
        res = client.post(url, json=input)
        assert res.status_code == 200
        assert json.loads(res.data) == {'msg': 'Cannot send mail'}
    
    # guest_mail not in request.json 
    input = {'workflow_id': 1, 'flow_id': 1,
             'item_type_id': 1, 'record_id': 1, 'guest_item_title': 'test',
             'file_name': 'test_file'}
    res = client.post(url, json=input)
    assert res.status_code == 200
    assert json.loads(res.data) == {'msg': 'Cannot send mail'}

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_guest_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_display_guest_activity(client, db, users, db_register,without_session_remove,mocker):
    mocker.patch("weko_workflow.models.GuestActivity.get_expired_activities")
    activity = Activity(activity_id='guest_1',workflow_id=1, flow_id=1,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_id=-1, 
                    extra_info={"guest_mail":"","record_id":"","fiile_name":""},
                    action_order=1,
                    )
    db.session.add(activity)
    history = ActivityHistory(
        activity_id=activity.activity_id,
        action_id=activity.action_id,
        action_order=activity.action_order,
    )
    with db.session.begin_nested():
        db.session.add(history)
    activity_action = ActivityAction(activity_id=activity.activity_id,
                                    action_id=1,action_status="M",action_comment="",
                                    action_handler=1, action_order=1)
    db.session.add(activity_action)
    guest_act = GuestActivity(
        user_mail="test@guest.com",
        record_id="1",
        file_name="test_file.txt",
        activity_id="guest_1",
        token="test_token"
    )
    db.session.add(guest_act)
    db.session.commit()
    mocker.patch("weko_workflow.views.validate_guest_activity_token",return_value=(True,"guest_1","test@guest.com"))
    url = url_for("weko_workflow.display_guest_activity",file_name="test_file.txt",token="test_token")
    
    # failed validate token
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        with patch("weko_workflow.views.validate_guest_activity_token",return_value=(False,None,None)):
            res = client.get(url)
            assert res.status_code == 200
            mock_render.assert_called_with("weko_theme/error.html",error="Token is invalid")
    
    # failed validate guest activity
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        with patch("weko_workflow.views.validate_guest_activity_expired",return_value="error"):
            res = client.get(url)
            assert res.status_code == 200
            mock_render.assert_called_with("weko_theme/error.html",error="error")
    # nomal
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        res = client.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert args[0] == 'weko_workflow/activity_detail.html'
        assert kwargs["record_org"] == []
    

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_activity_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_display_activity_nologin(client,db_register2):
    """Test of display activity."""
    url = url_for('weko_workflow.display_activity', activity_id='1')
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for('security.login', next="/workflow/activity/detail/1",_external=True)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_activity_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0, True),
    (1, True),
    (2, True),
    (3, True),
    (4, True),
    (5, True),
    (6, True),
])
def test_display_activity_acl(client, users, db_register, index, is_permission):
    """
    Test of display activity.
    Expected: users[0]: AssertionError
    """
    login(client=client, email=users[index]['email'])
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
                    if is_permission:
                        assert res.status_code != 403
                    else:
                        assert res.status_code == 403
                    mock_render_template.assert_called()

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_display_activity(client, users, db_register, db_records, redis_connect,without_session_remove,mocker):
    mocker.patch('weko_workflow.views.RedisConnection.connection',return_value=redis_connect)
    login(client=client, email=users[2]['email'])
    # action_endpoint is None
    action = Action.query.filter_by(id=1).one()
    action.action_endpoint = None
    db.session.merge(action)
    db.session.commit()
    url = url_for('weko_workflow.display_activity', activity_id='1?2')
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        res = client.get(url)
        args, kwargs = mock_render.call_args
        assert args[0] == 'weko_theme/error.html'
        assert kwargs == {"error": 'can not get data required for rendering'}

    # action = 1
    action.action_endpoint="begin_action"
    db.session.merge(action)
    db.session.commit()
    url = url_for('weko_workflow.display_activity', activity_id='1')
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        res = client.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert kwargs["action_id"] == 1
        assert kwargs["_id"] == None
        assert kwargs["files"] == []
        #assert kwargs["item_link"]
        assert kwargs["community_id"] == ""
        assert kwargs["links"] == None
        assert kwargs["jsonschema"] == ""
    # with action_journal
    action_journal = ActionJournal(activity_id=1,action_id=1,action_journal={"key":"value"})
    db.session.add(action_journal)
    db.session.commit()
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        res = client.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert kwargs["action_id"] == 1
        assert kwargs["_id"] == None
        assert kwargs["files"] == []
        assert kwargs["temporary_journal"] == {"key":"value"}
        assert kwargs["community_id"] == ""
        assert kwargs["links"] == None
        assert kwargs["jsonschema"] == ""

    # with not exist community
    url = url_for('weko_workflow.display_activity', activity_id='1',community="not_exist_community")
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        res = client.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert kwargs["action_id"] == 1
        assert kwargs["_id"] == None
        assert kwargs["files"] == []
        #assert kwargs["item_link"]
        assert kwargs["community_id"] == ""
        assert kwargs["links"] == None
        assert kwargs["jsonschema"] == ""

    # with exist community
    url = url_for('weko_workflow.display_activity', activity_id='1',community="comm01")
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        res = client.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert kwargs["action_id"] == 1
        assert kwargs["_id"] == None
        assert kwargs["files"] == []
        #assert kwargs["item_link"]
        assert kwargs["community_id"] == "comm01"
        assert kwargs["links"] == None
        assert kwargs["jsonschema"] == ""

    url = url_for('weko_workflow.display_activity', activity_id='1')
    # action is item_login
    ## action_status = C
    activity1 = Activity.query.filter_by(activity_id="1").one()
    activity1.action_id = 3
    activity1.action_status = "C"
    db.session.merge(activity1)
    db.session.commit()
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        res = client.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert kwargs["action_id"] == 3
        assert kwargs["_id"] == None
        assert kwargs["files"] == []
        #assert kwargs["item_link"]
        assert kwargs["community_id"] == ""
        assert kwargs["links"] == None
        assert kwargs["jsonschema"] == '/items/jsonschema/1'
    
    ## activity with item ,redis
    activity1.action_status = None
    db.session.merge(activity1)
    activity2 = Activity.query.filter_by(activity_id="2").one()
    activity2.action_id=3
    db.session.merge(activity2)
    history2 = ActivityHistory(
        activity_id=activity2.activity_id,
        action_id=activity2.action_id,
        action_order=activity2.action_order,
    )
    db.session.add(history2)
    db.session.commit()
    redis_connect.put('updated_json_schema_2',bytes('test', 'utf-8'))
    mocker.patch('weko_workflow.views.RedisConnection.connection',return_value=redis_connect)

    ## raise PIDDoesNotExistError
    from invenio_pidstore.models import PersistentIdentifier
    pid = PersistentIdentifier.get_by_object("recid","rec",db_records[2][2].id)
    pid.object_type="xxx"
    db.session.merge(pid)
    db.session.commit()
    url = url_for('weko_workflow.display_activity', activity_id='2')
    res = client.get(url)
    assert res.status_code == 404

    ## raise PIDDeletedError
    pid.object_type="rec"
    pid.status="D"
    db.session.merge(pid)
    db.session.commit()
    res = client.get(url)
    assert res.status_code == 404

    ## raise Exception
    pid.status="R"
    db.session.merge(pid)
    db.session.commit()
    with patch("weko_workflow.views.get_pid_and_record",side_effect=Exception("test_error")):
        with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
            res = client.get(url)
            assert res.status_code == 200
            args, kwargs = mock_render.call_args
            assert kwargs["action_id"] == 3
            assert kwargs["_id"] == None
            assert kwargs["files"] == []
            #assert kwargs["item_link"]
            assert kwargs["community_id"] == ""
            assert kwargs["links"] == None
            assert kwargs["jsonschema"] == '/items/jsonschema/1/2'

    # action is item_link
    activity2.action_id=5
    db.session.merge(activity2)
    db.session.commit()
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        res = client.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert kwargs["action_id"] == 5
        assert kwargs["_id"] == "1"
        assert kwargs["files"] == []
        assert kwargs["item_link"] == []
        assert kwargs["community_id"] == ""
        assert kwargs["links"] == {'index': '/api/deposits/redirect/1.1', 'r': '/items/index/1.1', 'iframe_tree': '/items/iframe/index/1.1', 'iframe_tree_upgrade': '/items/iframe/index/1.2'}
        assert kwargs["jsonschema"] == ''

    # item with file
    activity2.temp_data = '{"files":[{"version_id":"29dd361d-dc7f-49bc-b471-bdb5752afef5","url": {"url": "https://localhost/record/1/files/test.txt"}}]}'
    db.session.merge(activity2)
    db.session.commit()
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        res = client.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert kwargs["action_id"] == 5
        assert kwargs["_id"] == "1"
        assert kwargs["files"] == [{'version_id': '29dd361d-dc7f-49bc-b471-bdb5752afef5', 'url': {'url': 'https://localhost/record/1/files/test.txt'}}]
        assert kwargs["item_link"] == []
        assert kwargs["community_id"] == ""
        assert kwargs["links"] == {'index': '/api/deposits/redirect/1.1', 'r': '/items/index/1.1', 'iframe_tree': '/items/iframe/index/1.1', 'iframe_tree_upgrade': '/items/iframe/index/1.2'}
        assert kwargs["jsonschema"] == ''

    # action is identifier_grant
    activity2.action_id = 7
    activity2.temp_data={}
    db.session.merge(activity2)
    db.session.commit()
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        res = client.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert kwargs["action_id"] == 7
        assert kwargs["_id"] == "1"
        assert kwargs["files"] == []
        assert kwargs["community_id"] == ""
        assert kwargs["links"] == {'index': '/api/deposits/redirect/1.1', 'r': '/items/index/1.1', 'iframe_tree': '/items/iframe/index/1.1', 'iframe_tree_upgrade': '/items/iframe/index/1.2'}
        assert kwargs["jsonschema"] == ''
        
    ## with community,with action_identifier_setting
    url = url_for('weko_workflow.display_activity', activity_id='2',community="comm01")
    identifier = Identifier(repository="comm01",created_userId='1',created_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S'),
        updated_userId='1',updated_date=datetime.strptime('2022-09-28 04:33:42','%Y-%m-%d %H:%M:%S'))
    db.session.add(identifier)
    action_identifier = ActionIdentifier(activity_id="2",action_id=7,action_identifier_select=0)
    db.session.add(action_identifier)
    db.session.commit()
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        res = client.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert kwargs["action_id"] == 7
        assert kwargs["_id"] == "1"
        assert kwargs["files"] == []
        assert kwargs["community_id"] == "comm01"
        assert kwargs["links"] == {'index': '/api/deposits/redirect/1.1', 'r': '/items/index/1.1', 'iframe_tree': '/items/iframe/index/1.1', 'iframe_tree_upgrade': '/items/iframe/index/1.2'}
        assert kwargs["jsonschema"] == ''
    
    ## without identifier_setting
    url = url_for('weko_workflow.display_activity', activity_id='2',community="not_exist_comm")
    with patch("weko_workflow.views.render_template",return_value=make_response()) as mock_render:
        res = client.get(url)
        assert res.status_code == 200
        args, kwargs = mock_render.call_args
        assert kwargs["action_id"] == 7
        assert kwargs["_id"] == "1"
        assert kwargs["files"] == []
        assert kwargs["community_id"] == ""
        assert kwargs["links"] == {'index': '/api/deposits/redirect/1.1', 'r': '/items/index/1.1', 'iframe_tree': '/items/iframe/index/1.1', 'iframe_tree_upgrade': '/items/iframe/index/1.2'}
        assert kwargs["jsonschema"] == ''
    
@pytest.mark.skip(reason="")
def test_display_activity1(client, users, db_register,mocker,redis_connect):
    login(client=client, email=users[2]['email'])

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

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_check_authority -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_authority(users,db_register):
    # check_authority_by_admin is True
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        result = check_authority(lambda activity_id,action_id: True)(activity_id="1",action_id=1)
        assert result == True
    
    # pass check
    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        result = check_authority(lambda activity_id,action_id: True)(activity_id="1",action_id=1)
        assert result == True
    
    # user in deny
    flow_action = FlowAction.query.filter_by(id=1).one()
    action_role = FlowActionRole(flow_action_id=flow_action.id,action_user=users[4]["id"],action_user_exclude=True)
    db.session.add(action_role)
    db.session.commit()
    with patch("flask_login.utils._get_user", return_value=users[4]["obj"]):
        result = check_authority(lambda activity_id,action_id: True)(activity_id="1",action_id=1)
        assert json.loads(result.data) == {"code":403,"msg":"Authorization required"}
    
    # user not in allow
    action_role.action_user=users[0]["id"]
    action_role.action_user_exclude=False
    db.session.merge(action_role)
    db.session.commit()
    with patch("flask_login.utils._get_user", return_value=users[4]["obj"]):
        result = check_authority(lambda activity_id,action_id: True)(activity_id="1",action_id=1)
        assert json.loads(result.data) == {"code":403,"msg":"Authorization required"}
    
    # role in deny
    action_role.action_user=None
    action_role.action_role=6
    action_role.action_role_exclude=True
    db.session.merge(action_role)
    db.session.commit()
    with patch("flask_login.utils._get_user", return_value=users[4]["obj"]):
        result = check_authority(lambda activity_id,action_id: True)(activity_id="1",action_id=1)
        assert json.loads(result.data) == {"code":403,"msg":"Authorization required"}
    
    # role not in allow
    action_role.action_role=1
    action_role.action_role_exclude=False
    db.session.merge(action_role)
    db.session.commit()
    with patch("flask_login.utils._get_user", return_value=users[4]["obj"]):
        result = check_authority(lambda activity_id,action_id: True)(activity_id="1",action_id=1)
        assert json.loads(result.data) == {"code":403,"msg":"Authorization required"}

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_check_authority_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_authority_action(app, users,db_register):
    with app.test_request_context():
        # not login
        result = check_authority_action()
        assert result == 1

    # login user with admin role
    with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
        result = check_authority_action(activity_id="1")
        assert result == 0

    # user in deny
    flow_action = FlowAction.query.filter_by(id=1).one()
    action_role = FlowActionRole(flow_action_id=flow_action.id,action_user=users[4]["id"],action_user_exclude=True)
    db.session.add(action_role)
    db.session.commit()
    with patch("flask_login.utils._get_user", return_value=users[4]["obj"]):
        result = check_authority_action(activity_id="1",action_id=1,action_order=1)
        assert result == 1

    # user in allow
    action_role.action_user_exclude=False
    db.session.merge(action_role)
    db.session.commit()
    with patch("flask_login.utils._get_user", return_value=users[4]["obj"]):
        result = check_authority_action(activity_id="1",action_id=1,action_order=1)
        assert result == 0

    # role in deny
    action_role.action_user=None
    action_role.action_role=6
    action_role.action_role_exclude=True
    db.session.merge(action_role)
    db.session.commit()
    with patch("flask_login.utils._get_user", return_value=users[4]["obj"]):
        result = check_authority_action(activity_id="1",action_id=1,action_order=1)
        assert result == 1

    # role not in allow
    action_role.action_role=1
    action_role.action_role_exclude=False
    db.session.merge(action_role)
    db.session.commit()
    with patch("flask_login.utils._get_user", return_value=users[4]["obj"]):
        result = check_authority_action(activity_id="1",action_id=1,action_order=1)
        assert result == 1
    
    app.config.update(
        WEKO_WORKFLOW_ENABLE_CONTRIBUTOR=False
    )
    action_role.action_role=6
    db.session.merge(action_role)
    db.session.commit()
    with patch("flask_login.utils._get_user", return_value=users[4]["obj"]):
        result = check_authority_action(activity_id="1",action_id=1,action_order=1,contain_login_item_application=False)
        assert result == 1
        
    app.config.update(
        WEKO_WORKFLOW_ENABLE_CONTRIBUTOR=True
    )
    # user = activity_login_user
    db.session.delete(action_role)
    db.session.commit()
    with patch("flask_login.utils._get_user", return_value=users[7]["obj"]):
        result = check_authority_action(activity_id="1",action_id=1,action_order=1,contain_login_item_application=False)
        assert result == 0
        
    # TODO: cast(ItemMetadata.json["shared_user_id"],types.INT)が多分postgres限定でエラー
    #print("tt8")
    ## WEKO_WORKFLOW_ENABLE_CONTRIBUTOR is True, itemmetadata is exist
    #activity = Activity.query.filter_by(activity_id="2").one()
    #metadata = ItemMetadata.query.filter_by(id=activity.item_id).one()
    #with patch("flask_sqlalchemy._QueryProperty.__get__") as mock_query:
    #    mock_query.return_value.filter_by.return_value.one_or_none.return_value=metadata
    #    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
    #        result = check_authority_action(activity_id="2",action_id=1,action_order=1)
    #        assert result == 0
    #print("tt9")
    ##with patch("flask_sqlalchemy._QueryProperty.__get__") as mock_query:
    #    #mock_query.return_value.filter_by.side_effect = ItemMetadata.query.filter_by(id=100)
    #with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
    #    result = check_authority_action(activity_id="8",action_id=1,action_order=1)
    #    assert result == 0
    
    # WEKO_WORKFLOW_ENABLE_CONTRIBUTOR is False
    app.config.update(
        WEKO_WORKFLOW_ENABLE_CONTRIBUTOR=False
    )
    # ActivityAction.action_handler = user, contain_login_item_application is True
    with patch("flask_login.utils._get_user", return_value=users[7]["obj"]):
        result = check_authority_action(activity_id="2",action_id=1,action_order=1,contain_login_item_application=True)
        assert result == 0
    
    with patch("flask_login.utils._get_user", return_value=users[0]["obj"]):
        result = check_authority_action(activity_id="2",action_id=1,action_order=1,contain_login_item_application=True)
        assert result == 1


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

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_previous_action -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_previous_action(client, users, db_register):
    login(client=client, email=users[2]['email'])

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
    assert res.status_code==200
    assert data["code"] == 0
    assert data["msg"] == "success"
    act = Activity.query.filter_by(activity_id="2").one()
    actact = ActivityAction.query.filter_by(activity_id="2",action_id=3).one()
    # req=0
    # without identifier_select
    url = url_for('weko_workflow.previous_action',
                  activity_id='2', action_id=3, req=0)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code==200
    assert data["code"] == 0
    assert data["msg"] == "success"
    
    act = Activity.query.filter_by(activity_id="2").one()
    act.action_order = 2
    db.session.merge(act)
    actact = ActivityAction.query.filter_by(activity_id="2",action_id=3).one()
    actact.action_status = "M"
    db.session.merge(actact)
    db.session.commit()
    
    ## with identifier_select
    action_identifier = ActionIdentifier(activity_id="2",action_id=7,action_identifier_select=-2)
    db.session.add(action_identifier)
    db.session.commit()
    url = url_for('weko_workflow.previous_action',
                  activity_id='2', action_id=3, req=0)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code==200
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

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_get_journals -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@responses.activate
def test_get_journals(client,redis_connect,db_register2,mocker):
    mocker.patch('weko_workflow.views.RedisConnection.connection',return_value=redis_connect)
    
    # key not values
    url = url_for("weko_workflow.get_journals")
    res = client.get(url)
    assert res.status_code == 200
    assert json.loads(res.data) == {}
    
    redis_connect.put("oa_policy_test_key",bytes('{"key":"value"}',"utf-8"))
    # key in redis
    url = url_for("weko_workflow.get_journals",key="test_key")
    res = client.get(url)
    assert res.status_code == 200
    assert json.loads(res.data) == {"key": "value"}
    
    # key not in redis
    responses.add(
        responses.GET,
        'http://www.sherpa.ac.uk/romeo/api29.php?jtitle=not_exist_key1&qtype=starts',
        body='<?xml version="1.0" encoding="UTF-8"?><test><title>test data</title></test>'
    )
    url = url_for("weko_workflow.get_journals",key="not_exist_key1")
    res = client.get(url)
    assert res.status_code == 200
    assert json.loads(res.data) == {"test": {"title": "test data"}}
    assert redis_connect.redis.exists("oa_policy_not_exist_key1") == True
    
    # raise Exception
    responses.add(
        responses.GET,
        'http://www.sherpa.ac.uk/romeo/api29.php?jtitle=not_exist_key2&qtype=starts',
        body='<?xml version="1.0" encoding="UTF-8"?><test><title>test data</title></test>'
    )
    current_app.config.update(
        WEKO_WORKFLOW_OAPOLICY_CACHE_TTL = "not_int"
    )
    url = url_for("weko_workflow.get_journals",key="not_exist_key2")
    res = client.get(url)
    assert res.status_code == 200
    assert json.loads(res.data) == {"test": {"title": "test data"}}
    assert redis_connect.redis.exists("oa_policy_not_exist_key2") == False

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_get_journal -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@responses.activate
def test_get_journal(client,redis_connect,db_register2,mocker):
    mocker.patch('weko_workflow.views.RedisConnection.connection',return_value=redis_connect)
    # not method and value
    res = get_journal(None,None)
    assert json.loads(res.data) == {}
    
    responses.add(
        responses.GET,
        'http://www.sherpa.ac.uk/romeo/api29.php?issn=not_hits',
        body='<?xml version="1.0" encoding="UTF-8"?><romeoapi><header><numhits>0</numhits></header></romeoapi>'
    )
    url = url_for("weko_workflow.get_journal",method="issn",value="not_hits")
    res = client.get(url)
    assert res.status_code == 200
    assert json.loads(res.data) == {"romeoapi": {"header": {"numhits": "0"}}}
    
    responses.add(
        responses.GET,
        'http://www.sherpa.ac.uk/romeo/api29.php?issn=list_hits',
        body='<?xml version="1.0" encoding="UTF-8"?><romeoapi><header><numhits>2</numhits></header><journals><journal>test_journal1</journal><journal>test_journal2</journal></journals><publishers><publisher>test_publisher1</publisher><publisher>test_publisher2</publisher></publishers></romeoapi>'
    )
    url = url_for("weko_workflow.get_journal",method="issn",value="list_hits")
    res = client.get(url)
    assert res.status_code == 200
    assert json.loads(res.data) == {'romeoapi': {'header': {'numhits': '2'}, 'journals': {'journal': 'test_journal1'}, 'publishers': {'publisher': 'test_publisher1'}}}
    
    responses.add(
        responses.GET,
        'http://www.sherpa.ac.uk/romeo/api29.php?issn=not_list_hits',
        body='<?xml version="1.0" encoding="UTF-8"?><romeoapi><header><numhits>2</numhits></header><journals><journal>test_journal1</journal></journals><publishers><publisher>test_publisher1</publisher></publishers></romeoapi>'
    )
    url = url_for("weko_workflow.get_journal",method="issn",value="not_list_hits")
    res = client.get(url)
    assert res.status_code == 200
    assert json.loads(res.data) == {'romeoapi': {'header': {'numhits': '2'}, 'journals': {'journal': 'test_journal1'}, 'publishers': {'publisher': 'test_publisher1'}}}
    
    responses.add(
        responses.GET,
        'http://www.sherpa.ac.uk/romeo/api29.php?jtitle=test_value&qtype=exact',
        body='<?xml version="1.0" encoding="UTF-8"?><romeoapi><header><numhits>2</numhits></header><journals><journal>test_journal1</journal></journals><publishers><publisher>test_publisher1</publisher></publishers></romeoapi>'
    )
    url = url_for("weko_workflow.get_journal",method="test",value="test_value")
    res = client.get(url)
    assert res.status_code == 200
    assert json.loads(res.data) == {'romeoapi': {'header': {'numhits': '2'}, 'journals': {'journal': 'test_journal1'}, 'publishers': {'publisher': 'test_publisher1'}}}
    


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

#@pytest.mark.parametrize('users_index, status_code', [
#    (0, 200),
#    (1, 200),
#    (2, 200),
#    (3, 200),
#    (4, 200),
#    (5, 200),
#    (6, 200),
#])
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_cancel_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_cancel_action(client, users, db_register, db_records, add_file, mocker):
    login(client=client, email=users[2]['email'])
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
    print("xxxxxx")
    # not exist item, exist files, exist cancel_pv, exist file_permission
    input = {
        "action_version":"1.0.0",
        "commond":"this is test comment.",
        "pid_value":"1.1"
        }
    FilePermission.init_file_permission(users[2]["id"],"1.1","test_file","1")
    add_file(db_records[2][2])
    url = url_for('weko_workflow.cancel_action',
                  activity_id='1', action_id=1)
    redirect_url = url_for("weko_workflow.display_activity",
                           activity_id="1").replace("http://test_server.localdomain","")
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == 200
    assert data["code"] == 0
    assert data["msg"] == "success"
    assert data["data"]["redirect"] == redirect_url
    print("xxxxxx")
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
    assert res.status_code == 200
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


def test_withdraw_confirm(client, users, db_register_fullaction):
    url = url_for('weko_workflow.withdraw_confirm',
                  activity_id='1',
                  action_id=1)
    login(client=client, email=users[2]['email'])
    
    
@pytest.mark.parametrize('users_index, is_admin', [
    (0, False),
    (1, True),
    (2, True),
    (3, True),
    (4, False),
    (5, False),
    (6, True),
])
def test_withdraw_confirm_acl_users(client, users, db_register_fullaction, users_index, is_admin):
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
        assert res.status_code != 403

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
        assert res.status_code != 403
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
        assert res.status_code != 403
        assert data["code"] != 403


def test_withdraw_confirm_acl_guestlogin(guest, client, db_register_fullaction):
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


@pytest.mark.parametrize('index, is_permission', [
    (0, True),
    (1, True),
    (2, True),
    (3, True),
    (4, True),
    (5, True),
    (6, True),
])
def test_save_feedback_maillist_users(client, users, db_register, index, is_permission):
    """Test of save feedback maillist."""
    login(client=client, email=users[index]['email'])
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
        if is_permission:
            assert res.status_code != 403
        else:
            assert res.status_code == 403

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_save_feedback_maillist -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_save_feedback_maillist(client,users,db_register):
    login(client=client, email=users[2]['email'])
    url = url_for("weko_workflow.save_feedback_maillist",activity_id="1",action_id="1")
    
    # header error
    res = client.post(url,data={},headers={"Content-Type":"text/html"})
    assert res.status_code == 200
    assert json.loads(res.data) == {"code":-1, "msg":"Header Error"}
    
    # raise Exception
    with patch("weko_workflow.views.WorkActivity.create_or_update_action_feedbackmail",side_effect=Exception("test_error")):
        res = client.post(url,json={},headers={"Content-Type":"application/json"})
        assert res.status_code == 200
        assert json.loads(res.data) == {"code":-1, "msg":"Error"}
    
    data = {"email":"test@test.org"}
    res = client.post(url,json=data,headers={"Content-Type":"application/json"})
    assert res.status_code == 200
    assert json.loads(res.data) == {"code":0, "msg":"Success"}
    assert ActionFeedbackMail.query.filter_by(id=6).one().feedback_maillist == {"email":"test@test.org"}
    

def test_get_feedback_maillist_acl_nologin(client,db_register2):
    """Test of get feedback maillist."""
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='1')

    res = client.get(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/get_feedback_maillist/1",_external=True)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_get_feedback_maillist_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0, True),
    (1, True),
    (2, True),
    (3, True),
    (4, True),
    (5, True),
    (6, True),
])
def test_get_feedback_maillist_acl_users(client, users, index, is_permission):
    """Test of get feedback maillist."""
    login(client=client, email=users[index]['email'])
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='1')

    res = client.get(url)
    if is_permission:
        assert res.status_code != 403
    else:
        assert res.status_code == 403

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_get_feedback_maillist -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_feedback_maillist(client, users, db_register,without_session_remove):
    login(client=client, email=users[2]['email'])

    # argument error
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='1')
    with patch('weko_workflow.views.type_null_check', return_value=False):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code== 400
        assert data["code"] == -1
        assert data["msg"] == 'arguments error'

    # action_feedback is false
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='1')
    res = client.get(url)
    data = response_data(res)
    assert res.status_code==200
    assert data['code'] == 0
    assert data['msg'] == 'Empty!'

    # action_feedback is true
    ## author_id not in mail
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='4')
    res = client.get(url)
    data = response_data(res)
    mail_list = db_register['action_feedback_mail'].feedback_maillist
    assert res.status_code==200
    assert data['code'] == 1
    assert data['msg'] == 'Success'
    assert data['data'] == mail_list

    ## exist mail from author
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='5')
    res = client.get(url)
    data = response_data(res)
    mail_list = db_register['action_feedback_mail1'].feedback_maillist
    assert res.status_code==200
    assert data['code'] == 1
    assert data['msg'] == 'Success'
    assert data['data'] == mail_list
    
    ## not exist mail from author
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='6')
    res = client.get(url)
    data = response_data(res)
    mail_list = db_register['action_feedback_mail2'].feedback_maillist
    assert res.status_code==200
    assert data['code'] == 1
    assert data['msg'] == 'Success'
    assert data['data'] == mail_list
    
    # raise Exception
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='3')
    with patch('weko_workflow.views.WorkActivity.get_action_feedbackmail', side_effect=Exception):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code == 400
        assert data['code'] == -1
        assert data['msg'] == 'Error'

    ## mail_list is not list
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='7')
    res = client.get(url)
    data = response_data(res)
    #mail_list = db_register['action_feedback_mail3'].feedback_maillist
    assert res.status_code==400
    assert data['code'] == -1
    assert data['msg'] == 'mail_list is not list'

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_lock_activity_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_lock_activity_nologin(client,db_register2):
    """Test of lock activity."""
    url = url_for('weko_workflow.lock_activity', activity_id='1')
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/activity/lock/1",_external=True)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_lock_activity_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0, True),
    (1, True),
    (2, True),
    (3, True),
    (4, True),
    (5, True),
    (6, True),
])
def test_lock_activity_acl_users(client, users, index, is_permission):
    """Test of lock activity."""
    login(client=client, email=users[index]['email'])
    url = url_for('weko_workflow.lock_activity', activity_id='1')
    input = {}

    res = client.post(url,json=input)
    if is_permission:
        assert res.status_code != 403
    else:
        assert res.status_code == 403

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_lock_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_lock_activity(client,users,db_register,csrftoken):
    """Test of lock activity."""
    login(client=client, email=users[2]['email'])
    token, set_session = csrftoken
    headers = {"X-CSRFToken":token}
    set_session(client)
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}
    print("tt1")
    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, data=input,headers=headers)
            assert res.status_code == 200
    print("tt2")
    #locked value  is validate error
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': 1661748792565}

    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, data=input,headers=headers)
            assert res.status_code == 200

    #lock cache is different
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}
    print("tt3")
    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792568"):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, data=input,headers=headers)
            assert res.status_code == 200

    #action_handler is None
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}
    print("tt4")
    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, data=input,headers=headers)
            assert res.status_code == 200

    #activity_id is type error
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}
    print("tt5")
    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.type_null_check',return_value=False):
            with patch('weko_workflow.views.update_cache_data'):
                res = client.post(url, data=input,headers=headers)
                assert res.status_code == 500

    #request vaidate error
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {}
    print("tt6")
    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            with patch("weko_workflow.views.LockSchema",side_effect=ValidationError("test error")):
                res = client.post(url, data=input,headers=headers)
                assert res.status_code == 500
    print("tt7")
    # locked_by_email, locked_by_username is not exist
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}
    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            with patch("weko_workflow.views.get_account_info",return_value=(None,None)):
                res = client.post(url, data=input,headers=headers)
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
    print("tt8")
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}
    with patch('weko_workflow.views.get_cache_data', return_value="1-1661748792565"):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, data=input,headers=headers)
            assert res.status_code == 200
    activity_action = ActivityAction.query.filter_by(
        activity_id="A-00000003-00000",
        action_id=1,
        action_order=1
    ).first()
    activity_action.action_status="M"
    db.session.merge(activity_action)
    db.session.commit()
    print("tt9")
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
            res = client.post(url, data=input,headers=headers)
            assert res.status_code == 200
    activity_action = ActivityAction.query.filter_by(
        activity_id="A-00000003-00000",
        action_id=1,
        action_order=1
    ).first()
    activity_action.action_handler=0
    db.session.merge(activity_action)
    db.session.commit()
    print("tt10")
    url = url_for('weko_workflow.lock_activity', activity_id='A-00000003-00000')
    input = {'locked_value': '1-1661748792565'}
    with patch('weko_workflow.views.get_cache_data', return_value=""):
        with patch('weko_workflow.views.update_cache_data'):
            res = client.post(url, data=input,headers=headers)
            assert res.status_code == 200


def test_unlock_activity_acl_nologin(client,db_register2):
    """Test of unlock activity."""
    url = url_for('weko_workflow.unlock_activity', activity_id='1')
    input = {'locked_value':'1-1661748792565'}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/activity/unlock/1",_external=True)

@pytest.mark.parametrize('index, is_permission', [
    (0, True),
    (1, True),
    (2, True),
    (3, True),
    (4, True),
    (5, True),
    (6, True),
])
def test_unlock_activity_acl_users(client, users, index, is_permission):
    """Test of unlock activity."""
    login(client=client, email=users[index]['email'])
    url = url_for('weko_workflow.unlock_activity', activity_id='1')
    input = {'locked_value':'1-1661748792565'}

    with patch('weko_workflow.views.get_cache_data', return_value=""):
        res = client.post(url, json=input)
        if is_permission:
            assert res.status_code != 403
            assert res.status_code != 302
        else:
            assert res.status_code == 403

def test_unlock_activity(client, users, db_register):
    login(client=client, email=users[2]['email'])
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
        assert res.status_code==200
        assert data["code"] == 200
        assert data["msg"] == 'Not unlock'

    #locked_valueが空でなく、cur_locked_valと一致する場合
    with patch('weko_workflow.views.get_cache_data', return_value='1-1661748792565'):
        with patch('weko_workflow.views.delete_cache_data'):
            res = client.post(url, json=input)
            data = json.loads(res.data.decode("utf-8"))
            assert res.status_code==200
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
@pytest.mark.parametrize('index, is_permission', [
    (0, True),
    (1, True),
    (2, True),
    (3, True),
    (4, True),
    (5, True),
    (6, True),
])
def test_check_approval_acl_users(client, users, index, is_permission):
    """Test of check approval."""
    login(client=client, email=users[index]['email'])
    url = url_for('weko_workflow.check_approval', activity_id='1')
    response = {
        'check_handle': -1,
        'check_continue': -1,
        'error': 1
    }
    with patch('weko_workflow.views.check_continue', return_value=response):
        res = client.get(url)
        if is_permission:
            assert res.status_code != 302
            assert res.status_code != 403
        else:
            assert res.status_code == 403

def test_check_approval(client, users, db_register):
    login(client=client, email=users[2]['email'])
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
        assert res.status_code==200
        assert data['check_handle'] == -1
        assert data['check_continue'] == -1
        assert data['error'] == -1

    with patch('weko_workflow.views.check_continue', return_value=response):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code==200
        assert data['check_handle'] == -1
        assert data['check_continue'] == -1
        assert data['error'] == 1

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_send_mail_acl_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_send_mail_acl_nologin(client,db_register2):
    """Test of send mail."""
    url = url_for('weko_workflow.send_mail', activity_id='1',
                  mail_template='a')
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/send_mail/1/a",_external=True)

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_send_mail_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', [
    (0, True),
    (1, True),
    (2, True),
    (3, True),
    (4, True),
    (5, True),
    (6, True),
])
def test_send_mail_acl_users(app,client, users, index, is_permission):
    """Test of send mail."""
    login(client=client, email=users[index]['email'])
    url = url_for('weko_workflow.send_mail', activity_id='1',
                  mail_template='a')
    input = {}
    app.config.update(WEKO_WORKFLOW_ENABLE_AUTO_SEND_EMAIL=False)
    res = client.post(url, json=input)
    if is_permission:
        assert res.status_code != 403
    else:
        assert res.status_code == 403

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_send_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_send_mail(app,client,users,db_register,mocker):
    def mock_setting(cfg):
        current_app.extensions['mail'].default_sender = "test_sender"
    mocker.patch("invenio_mail.admin._set_flask_mail_cfg",side_effect=mock_setting)
    login(client=client, email=users[2]['email'])
    with app.extensions["mail"].record_messages() as outbox:
        app.config.update(
            WEKO_WORKFLOW_MAIL_TEMPLATE_FOLDER_PATH=os.path.join(os.path.dirname(__file__),"data")
        )
        url = url_for('weko_workflow.send_mail', activity_id='2',
                      mail_template='email_template.tpl')
        res = client.post(url)
        assert res.status_code == 200
        assert json.loads(res.data) == {"code":1, "msg":"Success"}
        assert len(outbox) == 1
        assert outbox[0].subject == "Subject: test_subject"
        
    # raise Exception
    with patch("weko_workflow.views.process_send_reminder_mail",side_effect=ValueError("test_error")):
        url = url_for('weko_workflow.send_mail', activity_id='2',
                      mail_template='email_template.tpl')
        res = client.post(url)
        assert res.status_code == 200
        assert json.loads(res.data) == {"code":-1, "msg":"Error"}
    
    # not send mail
    app.config.update(WEKO_WORKFLOW_ENABLE_AUTO_SEND_EMAIL=False)
    url = url_for('weko_workflow.send_mail', activity_id='2',
                      mail_template='email_template.tpl')
    res = client.post(url)
    assert res.status_code == 200
    assert json.loads(res.data) == {"code":1, "msg":"Success"}


def test_save_activity_acl_nologin(client):
    """Test of save activity."""
    url = url_for('weko_workflow.save_activity')
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/save_activity_data",_external=True)


@pytest.mark.parametrize('index, is_permission', [
    (0, True),
    (1, True),
    (2, True),
    (3, True),
    (4, True),
    (5, True),
    (6, True),
])
def test_save_activity_acl_users(client, users, index, is_permission):
    """Test of save activity."""
    login(client=client, email=users[index]['email'])
    url = url_for('weko_workflow.save_activity')
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}
    with patch('weko_workflow.views.save_activity_data'):
        res = client.post(url, json=input)
        if is_permission:
            assert res.status_code != 302 
            assert res.status_code != 403
        else:
            assert res.status_code == 403

def test_save_activity_acl_guestlogin(guest):
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}
    url = url_for('weko_workflow.save_activity')

    res = guest.post(url, json=input)
    assert res.status_code != 302

def test_save_activity_acl_nologin(client,db_register2):
    """Test of save activity."""
    url = url_for('weko_workflow.save_activity')
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/save_activity_data",_external=True)

def test_save_activity(client, users, db_register):
    login(client=client, email=users[2]['email'])
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
        assert res.status_code==200
        assert data["success"] == True
        assert data["msg"] == ""

    with patch('weko_workflow.views.save_activity_data', side_effect=Exception("test error")):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code==200
        assert data["success"] == False
        assert data["msg"] == "test error"

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_usage_report -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_usage_report(app,client,users,db_register,db_register2,mocker):
    mocker.patch("weko_workflow.views.get_workflow_item_type_names")
    login(client=client, email=users[2]['email'])
    app.config.update(
            WEKO_ITEMS_UI_OUTPUT_REPORT="",
            WEKO_ITEMS_UI_USAGE_REPORT = "テストアイテムタイプ"
        )
    url = url_for("weko_workflow.usage_report",tab='all')
    
    class mock_activity:
        def __init__(self,data):
            for key, value in data.items():
                setattr(self, key, value)
    data = [
        {"activity_id":"1","title":"test_activity1","flows_name":"test_flow","email":"test@test.org","StatusDesc":"Doing","role_name":"administrator"},
        {"activity_id":"2","title":"test_activity2","flows_name":"test_flow","email":"test@test.org","StatusDesc":"Doing","role_name":"administrator"}
    ]
    activities = list()
    for d in data:
        activities.append(mock_activity(d))
    with patch("weko_workflow.views.WorkActivity.get_activity_list",return_value=(activities,None,None,None,None)):
        res = client.get(url)
        assert res.status_code == 200
        assert json.loads(res.data) == {'activities': [{'activity_id': '1', 'email': 'test@test.org', 'item': 'test_activity1', 'status': 'Doing', 'user_role': 'administrator', 'work_flow': 'test_flow'}, {'activity_id': '2', 'email': 'test@test.org', 'item': 'test_activity2', 'status': 'Doing', 'user_role': 'administrator', 'work_flow': 'test_flow'}]}
    

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_send_mail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_get_data_init(client, users,db_register, db_register2):
    login(client=client, email=users[2]['email'])
    url = url_for("weko_workflow.get_data_init")
    res = client.get(url)
    assert res.status_code == 200
    print(json.loads(res.data))


def test_download_activitylog_nologin(client,db_register2):
    """_summary_

    Args:
        client (FlaskClient): flask test client
    """
    #2
    url = url_for('weko_workflow.download_activitylog')
    res =  client.get(url)
    assert res.status_code == 302

@pytest.mark.parametrize('index, is_permission', [
    (0, False),
    (1, True),
    (2, True),
    (3, False),
    (4, False),
    (5, False),
    (6, True),
])
def test_download_activitylog_acl(client, db_register , users, index, is_permission):
    """Test of download_activitylog."""
    login(client=client, email=users[index]['email'])
    url = url_for('weko_workflow.download_activitylog',
                activity_id='2')
    res = client.get(url)
    if is_permission:
        assert res.status_code != 403
    else:
        assert res.status_code == 403

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_download_activitylog -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_download_activitylog(app,client, db_register, users,without_session_remove,mocker):
    login(client=client, email=users[2]['email'])
    app.config.update(
        WEKO_WORKFLOW_ACTIVITYLOG_XLS_COLUMNS=["activity_id","title","flows_name","email","StatusDesc","role_name"]
    )
    class mock_activity:
        def __init__(self,data):
            for key, value in data.items():
                setattr(self, key, value)
    data = [
        {"activity_id":"1","title":"test_activity1","flows_name":"test_flow","email":"test@test.org","StatusDesc":"Doing","role_name":"administrator"},
        {"activity_id":"2","title":"test_activity2","flows_name":"test_flow","email":"test@test.org","StatusDesc":"Doing","role_name":"administrator"}
    ]
    activities = list()
    for d in data:
        activities.append(mock_activity(d))
    mocker.patch("weko_workflow.views.WorkActivity.get_activity_list",return_value=(activities,None,None,None,None))
    activity = mock_activity(data[0])
    
    login(client=client, email=users[0]['email'])
    url = url_for('weko_workflow.download_activitylog',
                activity_id='2')
    with patch("weko_workflow.views.WorkActivity.get_activity_by_id",return_value=activity):
        res = client.get(url)
        assert res.status_code == 403
        
    login(client=client, email=users[2]['email'])
    # exist activity_id in args
    url = url_for('weko_workflow.download_activitylog',
                activity_id='2')
    with patch("weko_workflow.views.WorkActivity.get_activity_by_id",return_value=activity):
        res = client.get(url)
        assert res.status_code == 200
    
    # not exist activity_id in args
    url = url_for('weko_workflow.download_activitylog',
                activity_id='10')
    with patch("weko_workflow.views.WorkActivity.get_activity_by_id",return_value=None):
        res = client.get(url)
        assert res.status_code == 400
        assert json.loads(res.data) == {"code": -1, "msg": "no activity error"}
    
    # activity_id not in args
    url = url_for('weko_workflow.download_activitylog',
                tab='all')
    with patch("weko_workflow.views.WorkActivity.get_activity_list",return_value=(activities,None,None,None,None)):
        res = client.get(url)
        assert res.status_code == 200
    
    # activity_id not in args, not find activity
    url = url_for('weko_workflow.download_activitylog',
                createdto='1900-01-17')
    with patch("weko_workflow.views.WorkActivity.get_activity_list",return_value=(None,None,None,None,None)):
        res = client.get(url)
        assert res.status_code == 400
    
    # DELETE_ACTIVITY_LOG_ENABLE is False
    current_app.config.update(
        DELETE_ACTIVITY_LOG_ENABLE = False
    )
    url = url_for('weko_workflow.download_activitylog',
                tab='all')
    res = client.get(url)
    assert res.status_code == 403


#@pytest.mark.parametrize('users_index, status_code', [
#    (1, 200),
#    (2, 200),
#    (6, 200),
#])
#def test_download_activitylog_2(client, db_register , users, users_index, status_code):
#    """Test of download_activitylog."""
#    login(client=client, email=users[users_index]['email'])
#
#    #4
#    url = url_for('weko_workflow.download_activitylog',
#                activity_id='2')
#    res = client.get(url)
#    assert res.status_code == status_code
#
#
#    #5
#    url = url_for('weko_workflow.download_activitylog',
#                activity_id='10')
#    res = client.get(url)
#    assert res.status_code == 400
#
#    #6
#    url = url_for('weko_workflow.download_activitylog',
#                tab='all')
#    res = client.get(url)
#    assert res.status_code == status_code
#
#    #7
#    url = url_for('weko_workflow.download_activitylog',
#                createdto='1900-01-17')
#    res = client.get(url)
#    assert res.status_code == 400

def test_withdraw_confirm_nologin(client,db_register2):
    """Test of withdraw confirm."""
    url = url_for('weko_workflow.withdraw_confirm', activity_id='1',
                  action_id=1)
    input = {}

    res = client.post(url, json=input)
    assert res.location == url_for('security.login',next="/workflow/activity/detail/1/1/withdraw",
                                    _external=True)


def test_clear_activitylog_nologin(client,db_register2):
    """_summary_

    Args:
        client (FlaskClient): flask test client
    """
    #10
    url = url_for('weko_workflow.clear_activitylog')
    res =  client.get(url)
    assert res.status_code == 302


@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 403),
    (4, 403),
    (5, 403),
    (6, 200),
])
def test_clear_activitylog_1(client, db_register , users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])

    #9,11
    url = url_for('weko_workflow.clear_activitylog',
                activity_id='A-00000001-10001')
    res = client.get(url)
    assert res.status_code == status_code

@pytest.mark.parametrize('users_index, status_code', [
    (1, 200),
    (2, 200),
    (6, 200),
])
def test_clear_activitylog_2(client, db_register , users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])
    #12
    url = url_for('weko_workflow.clear_activitylog',
                activity_id='10')
    res = client.get(url)
    assert res.status_code == 400

@pytest.mark.parametrize('users_index, status_code', [
    (1, 200),
    (2, 200),
    (6, 200),
])
def test_clear_activitylog_3(client, db_register , users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])
    #13
    with patch('weko_workflow.views.WorkActivity.quit_activity', return_value=None):
        url = url_for('weko_workflow.clear_activitylog',
                    activity_id='A-00000001-10001')
        res = client.get(url)
        assert res.status_code == 400

@pytest.mark.parametrize('users_index, status_code', [
    (1, 200),
    (2, 200),
    (6, 200),
])
def test_clear_activitylog_4(client, db_register , users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])
    #14
    with patch('invenio_db.db.session.delete', side_effect=Exception("test error")):
        url = url_for('weko_workflow.clear_activitylog',
                    activity_id='A-00000001-10001')
        res = client.get(url)
        assert res.status_code == 400

@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 403),
    (4, 403),
    (5, 403),
    (6, 200),
])
def test_clear_activitylog_5(client, db_register , users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])
    #15
    url = url_for('weko_workflow.clear_activitylog',
                tab='all')
    res = client.get(url)
    assert res.status_code == status_code

@pytest.mark.parametrize('users_index, status_code', [
    (1, 200),
    (2, 200),
    (6, 200),
])
def test_clear_activitylog_6(client, db_register , users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])
    #16
    url = url_for('weko_workflow.clear_activitylog',
                createdto='1900-01-17')
    res = client.get(url)
    assert res.status_code == 400

@pytest.mark.parametrize('users_index, status_code', [
    (1, 200),
    (2, 200),
    (6, 200),
])
def test_clear_activitylog_7(client, db_register , users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])
    #17
    with patch('weko_workflow.views.WorkActivity.quit_activity', return_value=None):
        url = url_for('weko_workflow.clear_activitylog',
                    tab='all')
        res = client.get(url)
        assert res.status_code == 400

@pytest.mark.parametrize('users_index, status_code', [
    (1, 200),
    (2, 200),
    (6, 200),
])
def test_clear_activitylog_8(client, db_register , users, users_index, status_code):
    """Test of clear_activitylog."""
    login(client=client, email=users[users_index]['email'])
    #18
    with patch('invenio_db.db.session.delete', side_effect=Exception("test error")):
        url = url_for('weko_workflow.clear_activitylog',
                    tab='all')
        res = client.get(url)
        assert res.status_code == 400

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_clear_activitylog_9 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 403),
    (4, 403),
    (5, 403),
    (6, 200),
])
def test_clear_activitylog_9(client, db_register , users,mocker, users_index, status_code):
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

class TestActivityActionResource:
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::TestActivityActionResource::test_activity_information -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_activity_information(self,app,db,client,users,db_register):
        obj =  ActivityActionResource()
        with app.test_request_context():
            with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
                act = Activity.query.filter_by(activity_id="1").one()
                # activity_status is finaly
                act.activity_status="F"
                db.session.merge(act)
                db.session.commit()
                result = obj.activity_information(act)
                assert result == {'activityId':"1","email":"user@test.org","status":"Done"}
                
                # activity_status is cancel
                act.activity_status="C"
                db.session.merge(act)
                db.session.commit()
                result = obj.activity_information(act)
                assert result == {'activityId':"1","email":"user@test.org","status":"Canceled"}
                
                # other
                act.activity_status="M"
                db.session.merge(act)
                db.session.commit()
                result = obj.activity_information(act)
                assert result == {'activityId':"1","email":"user@test.org","status":"Doing"}
        
    
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::TestActivityActionResource::test_post -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_post(self,app,client,users,db_register,without_session_remove,mocker):
        app.config.update(
            WEKO_WORKFLOW_GAKUNINRDM_DATA=[
                {"flow_id":1,"workflow_id":"1"}
            ]
        )
        url = url_for("weko_activity_rest.workflow_activity_new",activity_id="1")
        login(client=client, email=users[2]['email'])
        app.config.update(ACCOUNTS_JWT_ENABLE=False)
        
        # item_type_id not in args
        res = client.post(url,data={})
        assert res.status_code == 405
        
        filepath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'data',
            'sample_file.zip'
        )
        file_data = open(filepath,"rb")
        data = {"item_type_id":"1","file": (file_data,"test_file.csv")}

        # error in check_result
        with patch("weko_workflow.views.check_import_items",return_value={"error":"test_error"}):
            file_data = open(filepath,"rb")
            data = {"item_type_id":"1","file": (file_data,"test_file.csv")}
            res = client.post(url,data=data,buffered=True,content_type="multipart/form-data")
            assert res.status_code == 405

        # errors in check_result
        with patch("weko_workflow.views.check_import_items",return_value={"list_record":[{"errors":["test_error"]}]}):
            file_data = open(filepath,"rb")
            data = {"item_type_id":"1","file": (file_data,"test_file.csv")}
            res = client.post(url,data=data,buffered=True,content_type="multipart/form-data")
            assert res.status_code == 405

        # item not in check_result
        with patch("weko_workflow.views.check_import_items",return_value={"list_record":[{}]}):
            file_data = open(filepath,"rb")
            data = {"item_type_id":"1","file": (file_data,"test_file.csv")}
            res = client.post(url,data=data,buffered=True,content_type="multipart/form-data")
            assert res.status_code == 405

        check_result = {
            "data_path":"/tmp/deposit_activity_20230330194654",
            "list_record":[{"item_title":"test_item"}]
        }
        mocker.patch("weko_workflow.views.check_import_items",return_value=check_result)
        # import_items_to_system is failed
        with patch("weko_workflow.views.import_items_to_system",return_value={"success": False, "error_id": 1}):
            os.makedirs("/tmp/deposit_activity_20230330194654")
            file_data = open(filepath,"rb")
            data = {"item_type_id":"1","file": (file_data,"test_file.csv")}
            res = client.post(url,data=data,buffered=True,content_type="multipart/form-data")
            assert res.status_code == 405

        mocker.patch("weko_workflow.views.import_items_to_system",return_value={"success": True, "recid": "10"})
        PersistentIdentifier.create('recid', "10",object_type='rec', object_uuid=uuid.uuid4(),status=PIDStatus.REGISTERED)
        os.makedirs("/tmp/deposit_activity_20230330194654")
        file_data = open(filepath,"rb")
        data = {"item_type_id":"1","file": (file_data,"test_file.csv")}
        with patch("weko_workflow.api.WorkActivity.get_new_activity_id",return_value="new10"):
            res = client.post(url,data=data,buffered=True,content_type="multipart/form-data")
            assert res.status_code == 200
            assert json.loads(res.data) == {"activityId":"new10","email":"sysadmin@test.org","status":"Doing"}
        
        os.makedirs("/tmp/deposit_activity_20230330194654")
        file_data = open(filepath,"rb")
        data = {"item_type_id":"1","file": (file_data,"test_file.csv")}
        with patch("weko_workflow.api.WorkActivity.get_new_activity_id",side_effect=Exception("test_error")):
            res = client.post(url,data=data,buffered=True,content_type="multipart/form-data")
            assert res.status_code == 405
        
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::TestActivityActionResource::test_get -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp    
    def test_get(self, app, client,users,db_register):
        
        login(client=client, email=users[2]['email'])
        app.config.update(ACCOUNTS_JWT_ENABLE=False)
        
        # activity_id is None
        with app.test_request_context():
            with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
                obj =  ActivityActionResource()
                with pytest.raises(ActivityBaseRESTError):
                    res = obj.get(None)
                # activity_id is None
        
        # not exist activity
        url = url_for("weko_activity_rest.workflow_activity_action",activity_id="100")
        res = client.get(url)
        assert res.status_code == 404
        
        # success
        url = url_for("weko_activity_rest.workflow_activity_action",activity_id="1")
        res = client.get(url)
        assert json.loads(res.data) == {"activityId":"1","email":"user@test.org","status":"Doing"}

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::TestActivityActionResource::test_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
    def test_delete(self, app, client, users, db_register):
        login(client=client, email=users[2]['email'])
        app.config.update(ACCOUNTS_JWT_ENABLE=False)
        
        # activity_id is None
        with app.test_request_context():
            with patch("flask_login.utils._get_user", return_value=users[2]["obj"]):
                obj =  ActivityActionResource()
                with pytest.raises(ActivityBaseRESTError):
                    res = obj.delete(None)
        
        # not exist activity
        url = url_for("weko_activity_rest.workflow_activity_action",activity_id="100")
        res = client.delete(url)
        assert res.status_code == 404
        
        act = Activity.query.filter_by(activity_id="2").one()
        act.activity_status="B"
        db.session.merge(act)
        db.session.commit()
        url = url_for("weko_activity_rest.workflow_activity_action",activity_id="2")
        res = client.delete(url)
        assert res.status_code == 404
        
        act = Activity.query.filter_by(activity_id="1").one()
        act.activity_status="M"
        db.session.merge(act)
        db.session.commit()
        url = url_for("weko_activity_rest.workflow_activity_action",activity_id="1")
        res = client.delete(url)
        assert res.status_code == 200
        assert str(res.data,"utf-8") == "登録アクティビティを削除"
        
        act = Activity.query.filter_by(activity_id="1").one()
        act.activity_status="M"
        db.session.merge(act)
        db.session.commit()
        with patch("weko_workflow.views.WorkActivity.quit_activity",return_value=False):
            res = client.delete(url)
            assert res.status_code == 404
