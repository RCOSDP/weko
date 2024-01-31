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
import time
from re import M
import threading
import copy
from traceback import print_tb
from typing_extensions import Self
from unittest.mock import MagicMock
from weko_workflow.api import WorkActivity
import pytest
from mock import patch
from flask import Flask, json, jsonify, url_for, session, make_response, current_app
from flask_babelex import gettext as _
from flask_security import current_user
from flask_login import logout_user
from invenio_db import db
from sqlalchemy import func
from datetime import datetime
import uuid
from invenio_communities.models import Community
from invenio_pidstore.errors import PIDDoesNotExistError,PIDDeletedError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from weko_admin.models import AdminSettings
import weko_workflow.utils
from weko_workflow import WekoWorkflow
from weko_workflow.config import WEKO_WORKFLOW_TODO_TAB, WEKO_WORKFLOW_WAIT_TAB,WEKO_WORKFLOW_ALL_TAB
from flask_security import login_user
from weko_workflow.models import ActionFeedbackMail, ActivityRequestMail, ActivityItemApplication, Activity, ActionStatus, Action, WorkFlow, FlowDefine, FlowAction,FlowActionRole, ActivityAction
from invenio_accounts.testutils import login_user_via_session as login
from invenio_communities.models import Community
from weko_workflow.api import WorkActivity
from weko_workflow.views import (unlock_activity, 
                                 check_approval, 
                                 get_feedback_maillist, 
                                 save_activity, 
                                 render_guest_workflow,
                                 previous_action,
                                 _generate_download_url,
                                 check_authority_action,
                                 display_guest_activity,
                                 display_guest_activity_item_application,
                                 render_guest_workflow)
from marshmallow.exceptions import ValidationError
from weko_records_ui.models import FilePermission
from weko_records.models import ItemMetadata
from weko_workflow.schema.marshmallow import SaveActivitySchema
from weko_items_ui.utils import update_action_handler


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
    item_type_id = db_register['item_type'].id

    input = {'workflow_id': workflow_id, 'flow_id': flow_define_id}
    res = client.post(url, json=input)
    assert res.status_code == status_code

    input = {'workflow_id': -99, 'flow_id': flow_define_id}
    res = client.post(url, json=input)
    assert res.status_code == 500

    input = {'workflow_id': workflow_id, 'flow_id': -99}
    res = client.post(url, json=input)
    assert res.status_code == 500


    input = {'workflow_id': workflow_id}
    res = client.post(url, json=input)
    assert res.status_code == 400

    input = {'flow_id': flow_define_id}
    res = client.post(url, json=input)
    assert res.status_code == 400

    input = {}
    res = client.post(url, json=input)
    assert res.status_code == 400

    input = {'workflow_id': str(workflow_id), 'flow_id': str(flow_define_id)}
    res = client.post(url, json=input)
    assert res.status_code == 200

    input = {'workflow_id': 'd'+str(workflow_id), 'flow_id': str(flow_define_id)}
    res = client.post(url, json=input)
    assert res.status_code == 400

    input = {'workflow_id': str(workflow_id)+'d', 'flow_id': str(flow_define_id)}
    res = client.post(url, json=input)
    assert res.status_code == 400

    input = {'workflow_id': None, 'flow_id': flow_define_id}
    res = client.post(url, json=input)
    assert res.status_code == 400

    input = {'workflow_id': workflow_id, 'flow_id': None}
    res = client.post(url, json=input)
    assert res.status_code == 400

    input = {'workflow_id': workflow_id, 'flow_id': flow_define_id, 'itemtype_id': item_type_id}
    res = client.post(url, json=input)
    assert res.status_code == 200

    input = {'workflow_id': workflow_id, 'flow_id': flow_define_id, 'unknown':'unknown'}
    res = client.post(url, json=input)
    assert res.status_code == 200

    #for community
    input = {'workflow_id': str(workflow_id), 'flow_id': str(flow_define_id)}
    url_comm=url_for('weko_workflow.init_activity', community = 1)
    res = client.post(url_comm, json=input)
    assert res.status_code == 200
    
    with patch("weko_workflow.views.GetCommunity.get_community_by_id", return_value = Community(id=1)):
        res = client.post(url_comm, json=input)
        assert res.status_code == 200

    # #for request_mail
    # input = {'workflow_id':workflow_id, 'flow_id': flow_define_id
    #                 ,'extra_info':{'file_name' : 'test_file' , "record_id" : "1"}}
    # with patch("weko_workflow.views.RequestMailList.get_mail_list_by_item_id", return_value = [{"email":"contributor@test.org","author_id":""}]):
    #     res = client.post(url, json=input)
    #     assert res.status_code == 200

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

# def init_activity_guest():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_init_activity_guest_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_init_activity_guest_nologin(app, client,db_register2):
    """Test init activity for guest user."""
    url = url_for('weko_workflow.init_activity_guest')
    input = {'guest_mail': 'test@guest.com', 'workflow_id': 1, 'flow_id': 1,
            'item_type_id': 1, 'record_id': 1, 'guest_item_title': 'test',
            'file_name': 'test_file'}
    with patch("weko_workflow.views.is_terms_of_use_only",return_value=False):
        res = client.post(url, json=input)
        assert res.status_code == 200

    # 95
    with patch("weko_workflow.views.is_terms_of_use_only",return_value=True):
        # with patch("weko_workflow.views._generate_download_url",return_value='record/1/files/test_file'):
            res = client.post(url, json=input)
            assert res.status_code == 200
            data = json.loads(res.data)
            assert data['code'] == 1
            assert data['msg'] == 'success'
            assert data['data']['is_download'] == True
            assert data['data']['redirect'] == '/record/1/files/test_file'

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
def test_init_activity_guest_users(client, users, db_register, users_index, status_code):
    current_app.config.setdefault('THEME_INSTITUTION_NAME', {'ja':"組織", 'en':"INSTITUTION"})
    """Test init activity for guest user."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.init_activity_guest')
    input = {'guest_mail': 'test@guest.com', 'workflow_id': 1, 'flow_id': 1,
             'item_type_id': 1, 'record_id': 1, 'guest_item_title': 'test',
             'file_name': 'test_file'}

    res = client.post(url, json=input)
    assert res.status_code == status_code

# def display_guest_activity():
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_guest_activity -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_display_guest_activity(db_register, client):
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
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_ids":[]}

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
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_ids":[]}
    with patch('weko_workflow.views.save_activity_data'):
        res = client.post(url, json=input)
        assert res.status_code != 302 

def test_save_activity_acl_guestlogin(guest):
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_ids":[]}
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
    item_application = WorkActivity().get_activity_item_application(1)
    assert res.status_code == 200
    assert item_application.item_application.get("termsDescription")

    # 正常系　terms_descriptionなし
    res = client.post(url, json=input_without_description)
    item_application = WorkActivity().get_activity_item_application(1)
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
    # res = client.post(url, json = input_without_description, headers={"Content-Type":"text"})

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

def test_previous_action_acl_nologin(client,db_register2):
    """Test of previous action."""
    url = url_for('weko_workflow.previous_action', activity_id='1',
                  action_id=1, req=1)
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/activity/action/1/1/rejectOrReturn/1",_external=True)


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
def test_previous_action_acl_users(client, users, db_register, users_index, status_code, is_admin):
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
def test_previous_action(client, users, db_register, users_index, status_code):
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
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_next_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_next_action(app, client, db, users, db_register_fullaction, db_records, users_index, status_code, mocker):
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
    activity = copy.deepcopy(db_register_fullaction["activities"][0])
    with patch("weko_workflow.views.WorkActivity.get_activity_by_id",side_effect=[activity,None]):
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
    mocker.patch("weko_workflow.views.process_send_approval_mails", return_value=None)
    mocker.patch("weko_workflow.views.process_send_notification_mail")
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

    # exist next_flow_action.action_roles
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
        # with patch("weko_workflow.views.create_onetime_download_url_to_guest",return_value=onetime_download):
        update_activity_order("2",4,6)
        res = client.post(url, json=input)
        data = response_data(res)
        result_code = 0 if check_role_approval() else 403
        result_msg = _("success") if check_role_approval() else noauth_msg
        assert res.status_code == status_code
        assert data["code"] == result_code
        assert data["msg"] == result_msg

        ## exist requestmail
        ### exist feedbackmail, exist maillist
        update_activity_order("2",4,6)
        adminsetting = AdminSettings(id=1,name='items_display_settings',settings={"display_request_form": True})
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

        ### exist requestmail, not maillistxxx
        update_activity_order("2",4,6)
        adminsetting = AdminSettings(id=1,name='items_display_settings',settings={"display_request_form": True})
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
        update_activity_order("2",4,6)
        item_application =  ActivityItemApplication(id=1, activity_id=1, item_application={})
        with patch("weko_workflow.views.WorkActivity.get_activity_item_application", return_value = item_application):
            with patch("weko_workflow.views.ItemApplication.delete_by_list_item_id" )as delete_application:
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
    mocker.patch("weko_workflow.views.WekoDeposit.update_feedback_mail")
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
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_cancel_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_cancel_action(client, users,db, db_register, db_records, add_file, users_index, status_code, mocker):
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

@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_cancel_action2(client, users,db, db_register, db_records, add_file, users_index, status_code, mocker):
    login(client=client, email=users[users_index]['email'])
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

#.tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_get_feedback_maillist -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    #(1, 200),
    #(2, 200),
    #(3, 200),
    #(4, 200),
    #(5, 200),
    #(6, 200),
])
def test_get_feedback_maillist(client, users, db_register, users_index, status_code):
    login(client=client, email=users[users_index]['email'])

    action_feedback_mail = db_register['action_feedback_mail']
    action_feedback_mail_1 = db_register['action_feedback_mail1']
    action_feedback_mail_2 = db_register['action_feedback_mail2']

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
    mail_list = action_feedback_mail.feedback_maillist
    assert res.status_code==status_code
    assert data['code'] == 1
    assert data['msg'] == 'Success'
    assert data['data'] == mail_list

    url = url_for('weko_workflow.get_feedback_maillist', activity_id='5')
    res = client.get(url)
    data = response_data(res)
    mail_list = action_feedback_mail_1.feedback_maillist
    assert res.status_code==status_code
    assert data['code'] == 1
    assert data['msg'] == 'Success'
    assert data['data'] == mail_list

    url = url_for('weko_workflow.get_feedback_maillist', activity_id='6')
    res = client.get(url)
    data = response_data(res)
    mail_list = action_feedback_mail_2.feedback_maillist
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
        mocker.patch("weko_workflow.views.Authors.get_first_email_by_id", return_value = "test@test.org")
        res = client.get(url)
        data = response_data(res)
        assert res.status_code == 200
        assert data['code'] == 1
        assert data['msg'] == 'Success'
        assert data['request_maillist'] == [{'author_id':1, 'email':"test@test.org"}]
    
    #Errorが起きた場合
    request_maillist =ActivityRequestMail(request_maillist=[{'author_id':1, 'email':"test@test.org"}])
    with patch('weko_workflow.views.WorkActivity.get_activity_request_mail', return_value = request_maillist):
        mocker.patch("weko_workflow.views.Authors.get_first_email_by_id", return_value = "test@test.org")
        res = client.get(url)
        data = response_data(res)
        assert res.status_code == 400
        assert data['code'] == -1
    
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

#.tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_save_activity_acl_nologin -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_save_activity_acl_nologin(client,db_register2):
    """Test of save activity."""
    url = url_for('weko_workflow.save_activity')
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_ids":[]}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/save_activity_data",_external=True)

#.tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_save_activity_acl_users -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
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
def test_save_activity(client, users, db_register, users_index, status_code):
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

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_activity_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_workflow/.tox/c1/tmp
def test_display_activity_nologin(client,db_register2,mocker):
    """Test of display activity."""
    adminsetting = AdminSettings(id=1,name='items_display_settings',settings={"display_request_form": True})
    mocker.patch("weko_workflow.views.AdminSettings.get",return_value = adminsetting)
    url = url_for('weko_workflow.display_activity', activity_id='1')
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_activity_guestlogin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko_workflow/.tox/c1/tmp
def test_display_activity_guestlogin(app,db_register,guest,mocker):
    """Test of display activity."""
    adminsetting = AdminSettings(id=1,name='items_display_settings',settings={"display_request_form": True})
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
            with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
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
    adminsetting = AdminSettings(id=1,name='items_display_settings',settings={"display_request_form": True})
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
            with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
                       return_value=(roles, action_users)):
                with patch('weko_workflow.views.render_template', mock_render_template):
                    res = client.post(url, json=input)
                    mock_render_template.assert_called()

#.tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_display_activity -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_display_activity(client, users, db_register, users_index, status_code, mocker, redis_connect, app):
    login(client=client, email=users[users_index]['email'])
    adminsetting = AdminSettings(id=1,name='items_display_settings',settings={"display_request_form": True})
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
    app.config.update(WEKO_WORKFLOW_APPROVAL_PREVIEW = False)
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
                                mock_args, mock_kwargs = mock_render_template.call_args
                                assert mock_kwargs['contributors'] == \
                                [{'email': 'user1@sample.com',
                                 'error': '',
                                 'owner': True,
                                 'userid': 1,
                                 'username': ''},
                                {'email': 'user2@sample.com',
                                 'error': '',
                                 'owner': False,
                                 'userid': 2,
                                 'username': ''
                                }]
                                

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

# def check_authority_action(activity_id='0', action_id=0, contain_login_item_application=False, action_order=0):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_check_authority_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_check_authority_action(app, client, users, db_register, mocker):
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
        assert 0 == check_authority_action(activity_id='1', 
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