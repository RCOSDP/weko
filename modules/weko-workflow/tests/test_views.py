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
import threading
from unittest.mock import MagicMock
import pytest
from mock import patch
from flask import Flask, json, jsonify, url_for, session
from invenio_db import db
from sqlalchemy import func
from datetime import datetime

import weko_workflow.utils
from weko_workflow import WekoWorkflow
from weko_workflow.config import WEKO_WORKFLOW_TODO_TAB, WEKO_WORKFLOW_WAIT_TAB,WEKO_WORKFLOW_ALL_TAB
from flask_security import login_user
from weko_workflow.models import Activity, ActionStatus, Action, WorkFlow, FlowDefine, FlowAction
from invenio_accounts.testutils import login_user_via_session as login
from weko_workflow.views import previous_action
from weko_records_ui.models import FilePermission
def response_data(response):
    return json.loads(response.data)
# def test_index_acl_nologin(client):
#     """_summary_
# 
#     Args:
#         client (FlaskClient): flask test client
#     """    
#     url = url_for('weko_workflow.index')
#     res =  client.get(url)
#     assert res.status_code == 302
#     assert res.location == url_for('security.login', next="/workflow/",_external=True)
# 
# @pytest.mark.parametrize('users_index, status_code', [
#     (0, 200),
#     (1, 200),
#     (2, 200),
#     (3, 200),
#     (4, 200),
#     (5, 200),
#     (6, 200),
# ])
# def test_index_acl(client, users, db_register2,users_index, status_code):
#     login(client=client, email=users[users_index]['email'])
#     url = url_for('weko_workflow.index',_external=True)
#     res = client.get(url)
#     assert res.status_code == status_code
# 
#     url = url_for('weko_workflow.index',community="a",_external=True)
#     res = client.get(url)
#     assert res.status_code == status_code
# 
#     url = url_for('weko_workflow.index',tab=WEKO_WORKFLOW_TODO_TAB,_external=True)
#     res = client.get(url)
#     assert res.status_code == status_code
# 
#     url = url_for('weko_workflow.index',tab=WEKO_WORKFLOW_TODO_TAB,community="a",_external=True)
#     res = client.get(url)
#     assert res.status_code == status_code
# 
#     url = url_for('weko_workflow.index',tab=WEKO_WORKFLOW_WAIT_TAB,_external=True)
#     res = client.get(url)
#     assert res.status_code == status_code
# 
#     url = url_for('weko_workflow.index',tab=WEKO_WORKFLOW_WAIT_TAB,community="a",_external=True)
#     res = client.get(url)
#     assert res.status_code == status_code
# 
#     url = url_for('weko_workflow.index',tab=WEKO_WORKFLOW_ALL_TAB,_external=True)
#     res = client.get(url)
#     assert res.status_code == status_code
# 
#     url = url_for('weko_workflow.index',tab=WEKO_WORKFLOW_ALL_TAB,community="a",_external=True)
#     res = client.get(url)
#     assert res.status_code == status_code
# 
# def test_init_activity_acl_nologin(client):
#     """Test init_activity.
# 
#     Args:
#         client (_type_): _description_
#     """    
#     
#     """"""
#     url = url_for('weko_workflow.init_activity')
#     input = {'workflow_id': 1, 'flow_id': 1}
#     res = client.post(url, json=input)
#     assert res.status_code == 302
#     assert res.location == url_for('security.login', next="/workflow/activity/init",_external=True)
# 
# 
# @pytest.mark.parametrize('users_index, status_code', [
#     (0, 200),
#     (1, 200),
#     (2, 200),
#     (3, 200),
#     (4, 200),
#     (5, 200),
#     (6, 200),
# ])
# def test_init_activity_acl(client, users, users_index, status_code,db_register):
#     """_summary_
# 
#     Args:
#         client (_type_): _description_
#         users (_type_): _description_
#         users_index (_type_): _description_
#         status_code (_type_): _description_
#         db_register (_type_): _description_
#     """    
#     login(client=client, email=users[users_index]['email'])
#     url = url_for('weko_workflow.init_activity')
#     input = {'workflow_id': db_register['workflow'].id, 'flow_id': db_register['flow_define'].id}
#     res = client.post(url, json=input)
#     assert res.status_code == status_code
# 
# @pytest.mark.parametrize('users_index, status_code', [
#     (0, 200),
#     (1, 200),
#     (2, 200),
#     (3, 200),
#     (4, 200),
#     (5, 200),
#     (6, 200),
# ])
# def test_init_activity(client, users,users_index, status_code,db_register):
#     login(client=client, email=users[users_index]['email'])
#     url = url_for('weko_workflow.init_activity')
#     input = {'workflow_id': db_register['workflow'].id, 'flow_id': db_register['flow_define'].id}
#     res = client.post(url, json=input)
#     assert res.status_code == status_code
# 
#     input = {'workflow_id': -99, 'flow_id': db_register['flow_define'].id}
#     res = client.post(url, json=input)
#     assert res.status_code == 500
# 
#     input = {'workflow_id': db_register['workflow'].id, 'flow_id': -99}
#     res = client.post(url, json=input)
#     assert res.status_code == 500
# 
# 
#     input = {'workflow_id': db_register['workflow'].id}
#     res = client.post(url, json=input)
#     assert res.status_code == 400
# 
#     input = {'flow_id': db_register['flow_define'].id}
#     res = client.post(url, json=input)
#     assert res.status_code == 400
# 
#     input = {}
#     res = client.post(url, json=input)
#     assert res.status_code == 400
# 
#     input = {'workflow_id': str(db_register['workflow'].id), 'flow_id': str(db_register['flow_define'].id)}
#     res = client.post(url, json=input)
#     assert res.status_code == 200
# 
#     input = {'workflow_id': 'd'+str(db_register['workflow'].id), 'flow_id': str(db_register['flow_define'].id)}
#     res = client.post(url, json=input)
#     assert res.status_code == 400
# 
#     input = {'workflow_id': str(db_register['workflow'].id)+'d', 'flow_id': str(db_register['flow_define'].id)}
#     res = client.post(url, json=input)
#     assert res.status_code == 400
# 
#     input = {'workflow_id': None, 'flow_id': db_register['flow_define'].id}
#     res = client.post(url, json=input)
#     assert res.status_code == 400
# 
#     input = {'workflow_id': db_register['workflow'].id, 'flow_id': None}
#     res = client.post(url, json=input)
#     assert res.status_code == 400
# 
#     input = {'workflow_id': db_register['workflow'].id, 'flow_id': db_register['flow_define'].id, 'itemtype_id': db_register['item_type'].id}
#     res = client.post(url, json=input)
#     assert res.status_code == 200
# 
#     input = {'workflow_id': db_register['workflow'].id, 'flow_id': db_register['flow_define'].id, 'unknown':'unknown'}
#     res = client.post(url, json=input)
#     assert res.status_code == 200
# 
# 
# 
# 
# def test_init_activity_guest_nologin(client):
#     """Test init activity for guest user."""
#     url = url_for('weko_workflow.init_activity_guest')
#     input = {'guest_mail': 'test@guest.com', 'workflow_id': 1, 'flow_id': 1,
#              'item_type_id': 1, 'record_id': 1, 'guest_item_title': 'test',
#              'file_name': 'test_file'}
# 
#     res = client.post(url, json=input)
#     assert res.status_code == 200
# 
# 
# @pytest.mark.parametrize('users_index, status_code', [
#     (0, 200),
#     (1, 200),
#     (2, 200),
#     (3, 200),
#     (4, 200),
#     (5, 200),
#     (6, 200),
# ])
# def test_init_activity_guest_users(client, users, users_index, status_code):
#     """Test init activity for guest user."""
#     login(client=client, email=users[users_index]['email'])
#     url = url_for('weko_workflow.init_activity_guest')
#     input = {'guest_mail': 'test@guest.com', 'workflow_id': 1, 'flow_id': 1,
#              'item_type_id': 1, 'record_id': 1, 'guest_item_title': 'test',
#              'file_name': 'test_file'}
# 
#     res = client.post(url, json=input)
#     assert res.status_code == status_code
# 
# 
# def test_find_doi_nologin(client):
#     """Test of find doi."""
#     url = url_for('weko_workflow.find_doi')
#     input = {}
# 
#     res = client.post(url, json=input)
#     assert res.status_code == 302
#     # TODO check that the path changed
#     # assert res.url == url_for('security.login')
# 
# 
# @pytest.mark.parametrize('users_index, status_code', [
#     (0, 200),
#     (1, 200),
#     (2, 200),
#     (3, 200),
#     (4, 200),
#     (5, 200),
#     (6, 200),
# ])
# def test_find_doi_users(client, users, users_index, status_code):
#     """Test of find doi."""
#     login(client=client, email=users[users_index]['email'])
#     url = url_for('weko_workflow.find_doi')
#     input = {}
# 
#     res = client.post(url, json=input)
#     assert res.status_code == status_code
# 
# 
# def test_save_activity_nologin(client):
#     """Test of save activity."""
#     url = url_for('weko_workflow.save_activity')
#     input = {}
# 
#     res = client.post(url, json=input)
#     assert res.status_code == 302
#     # TODO check that the path changed
#     # assert res.url == url_for('security.login')
# 
# 
# @pytest.mark.parametrize('users_index, status_code', [
#     (0, 200),
#     (1, 200),
#     (2, 200),
#     (3, 200),
#     (4, 200),
#     (5, 200),
#     (6, 200),
# ])
# def test_save_activity_users(client, users, users_index, status_code):
#     """Test of save activity."""
#     login(client=client, email=users[users_index]['email'])
#     url = url_for('weko_workflow.save_activity')
#     input = {}
# 
#     res = client.post(url, json=input)
#     assert res.status_code == status_code
# 
# 
# def test_save_feedback_maillist_nologin(client):
#     """Test of save feedback maillist."""
#     url = url_for('weko_workflow.save_feedback_maillist',
#                   activity_id='1', action_id=1)
#     input = {}
# 
#     res = client.post(url, json=input)
#     assert res.status_code == 302
#     # TODO check that the path changed
#     # assert res.url == url_for('security.login')
# 
# 
# @pytest.mark.parametrize('users_index, status_code', [
#     (0, 200),
#     (1, 200),
#     (2, 200),
#     (3, 200),
#     (4, 200),
#     (5, 200),
#     (6, 200),
# ])
# def test_save_feedback_maillist_users(client, users, db_register, users_index, status_code):
#     """Test of save feedback maillist."""
#     login(client=client, email=users[users_index]['email'])
#     url = url_for('weko_workflow.save_feedback_maillist',
#                   activity_id='1', action_id=1)
#     input = {}
# 
#     roles = {
#         'allow': [],
#         'deny': []
#     }
#     action_users = {
#         'allow': [],
#         'deny': []
#     }
# 
#     with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
#                return_value=(roles, action_users)):
#         res = client.post(url, json=input)
#         assert res.status_code == status_code
# 
# 
# def test_previous_action_acl_nologin(client):
#     """Test of previous action."""
#     url = url_for('weko_workflow.previous_action', activity_id='1',
#                   action_id=1, req=1)
#     input = {}
# 
#     res = client.post(url, json=input)
#     assert res.status_code == 302
#     assert res.location == url_for('security.login',next="/workflow/activity/action/1/1/rejectOrReturn/1",_external=True)
# 
# 
# @pytest.mark.parametrize('users_index, status_code, status_code_role', [
#     (0, 200, 403),
#     (1, 200, 0),
#     (2, 200, 0),
#     (3, 200, 0),
#     (4, 200, 403),
#     (5, 200, 403),
#     (6, 200, 0),
# ])
# def test_previous_action_acl_users(client, users, db_register, users_index, status_code, status_code_role):
#     """Test of previous action."""
#     login(client=client, email=users[users_index]['email'])
#     url = url_for('weko_workflow.previous_action', activity_id='1',
#                   action_id=1, req=1)
#     input = {}
# 
#     roles = {
#         'allow': [],
#         'deny': []
#     }
#     action_users = {
#         'allow': [],
#         'deny': []
#     }
# 
#     with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
#                return_value=(roles, action_users)):
#         res = client.post(url, json=input)
#         assert res.status_code == status_code
#     roles = {
#         'allow': [],
#         'deny': []
#     }
#     action_users = {
#         'allow': [],
#         'deny': [users[users_index]["id"]]
#     }
#     url = url_for('weko_workflow.previous_action', 
#                 activity_id='2',
#                 action_id=1, req=1)
# 
#     with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
#                return_value=(roles, action_users)):
#         res = client.post(url, json=input)
#         data = response_data(res)
#         assert res.status_code == status_code
#         assert data["code"] == status_code_role
# 
# @pytest.mark.parametrize('users_index, status_code', [
#     (0, 200),
#     (1, 200),
#     (2, 200),
#     (3, 200),
#     (4, 200),
#     (5, 200),
#     (6, 200),
# ])
# def test_previous_action(client, users, db_register, users_index, status_code):
#     login(client=client, email=users[users_index]['email'])
#     input = {"action_version":"1.0.0", "commond":"this is test comment."}
#     
#     # req=1
#     url = url_for('weko_workflow.previous_action', 
#                   activity_id='2', action_id=1, req=1)
#     res = client.post(url, json=input)
#     data = response_data(res)
#     assert res.status_code==status_code
#     assert data["code"] == 0
#     assert data["msg"] == "success"
#     
#     # req=0
#     url = url_for('weko_workflow.previous_action',
#                   activity_id='2', action_id=3, req=0)
#     res = client.post(url, json=input)
#     data = response_data(res)
#     assert res.status_code==status_code
#     assert data["code"] == 0
#     assert data["msg"] == "success"
#     
#     # req=-1
#     res = previous_action(activity_id="2", action_id=1, req=-1)
#     data = response_data(res)
#     assert data["code"] == 0
#     assert data["msg"] == "success"
#     
#     # not pre_action
#     url = url_for('weko_workflow.previous_action',
#                   activity_id='2', action_id=3, req=0)
#     with patch("weko_workflow.views.Flow.get_previous_flow_action", return_value=None):
#         res = client.post(url, json=input)
#         data = response_data(res)
#         assert data["code"] == 0
#         assert data["msg"] == "success"
#     
# 
#     # code=-1
#     url = url_for('weko_workflow.previous_action',
#                   activity_id='2', action_id=3, req=0)
#     with patch("weko_workflow.views.WorkActivityHistory.create_activity_history", return_value=None):
#         res = client.post(url, json=input)
#         data = response_data(res)
#         assert data["code"] == -1
#         assert data["msg"] == "error"
#     
#     # code=-2
#     with patch("weko_workflow.views.WorkActivity.upt_activity_action_status", return_value=False):
#         res = client.post(url, json=input)
#         data = response_data(res)
#         assert data["code"] == -2
#         assert data["msg"] == ""


# def test_next_action_acl_nologin(client, db_register_fullaction):
#     """Test of next action."""
#     url = url_for('weko_workflow.next_action', activity_id='1',
#                   action_id=1)
#     input = {}
# 
#     res = client.post(url, json=input)
#     assert res.status_code == 302
#     assert res.location == url_for('security.login',next="/workflow/activity/action/1/1",_external=True)
# 
# 
# @pytest.mark.parametrize('users_index, status_code, status_code_role', [
#     (0, 200, 403),
#     (1, 200, 0),
#     (2, 200, 0),
#     (3, 200, 0),
#     (4, 200, 403),
#     (5, 200, 403),
#     (6, 200, 0),
# ])
# def test_next_action_acl_users(client, users, db_register_fullaction, users_index, status_code, status_code_role):
#     """Test of next action."""
#     login(client=client, email=users[users_index]['email'])
#     url = url_for('weko_workflow.next_action', activity_id='1',
#                   action_id=1)
#     input = {}
# 
#     roles = {
#         'allow': [],
#         'deny': []
#     }
#     action_users = {
#         'allow': [],
#         'deny': []
#     }
# 
#     with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
#                return_value=(roles, action_users)):
#         res = client.post(url, json=input)
#         assert res.status_code == status_code
#     roles = {
#         'allow': [],
#         'deny': []
#     }
#     action_users = {
#         'allow': [],
#         'deny': [users[users_index]["id"]]
#     }
#     url = url_for('weko_workflow.next_action', 
#                 activity_id='2',action_id=1)
# 
#     with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
#                return_value=(roles, action_users)):
#         res = client.post(url, json=input)
#         data = response_data(res)
#         assert res.status_code == status_code
#         assert data["code"] == status_code_role
# 
# def test_next_action_acl_guestlogin(guest, db_register_fullaction):
#     input = {'action_version': 1, 'commond': 1}
#     url = url_for('weko_workflow.next_action',
#                   activity_id="1", action_id=1)
#     roles = {
#         'allow': [],
#         'deny': []
#     }
#     action_users = {
#         'allow': [],
#         'deny': []
#     }
#     with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
#                return_value=(roles, action_users)):
#         res = guest.post(url, json=input)
#         assert res.status_code == 200

@pytest.mark.parametrize('users_index, status_code', [
    #(0, 200),
    #(1, 200),
    (2, 200),
    #(3, 200),
    #(4, 200),
    #(5, 200),
    #(6, 200),
])
def test_next_action(client, users, db_register_fullaction, db_records, users_index, status_code):
    login(client=client, email=users[users_index]["email"])
    
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
    url = url_for("weko_workflow.next_action",
                  activity_id="2", action_id=2)
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == 200
    assert data["code"] == 0
    assert data["msg"] == "success"
    
    # action: item register
    input = {"temporary_save":0}
    
    # action: item link
    ## temporary_save = 0
    ### exist pid_without_ver, exist link_data
    input = {
        "temporary_save":0,
        "link_data":[
            {"item_id":"1","item_title":"test item1","sale_id":"relateTo"}
        ]
    }
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    ####x raise except
    err_msg = "test update error"
    with patch("weko_workflow.views.ItemLink.update",return_value=err_msg):
        res = client.post(url, json=input)
        data = response_data(res)
        assert res.status_code == status_code
        assert data["code"] == -1
        assert data["msg"] == err_msg
    ## temporary_save = 1
    input = {
        "temporary_save":1,
        "link_data":[
            {"item_id":"1","item_title":"test item1","sale_id":"relateTo"}
        ]
    }
    res = client.post(url, json=input)
    data = response_data(res)
    assert res.status_code == status_code
    assert data["code"] == 0
    assert data["msg"] == "success"
    
    # action: identifier grant
    ## exist identifier_select
    ###x temporary_save = 1
    input = {
        "temporary_save":1,
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
    ##### item_id != pid_without_ver(item_idにバージョンがある)
    ###### not _old_v
    ###### _old_v & _old_v != _new_v
    ###### _old_v & _old_v = _new_v
    ##### item_id == pid_without_ver(item_idにバージョンがない。初めて)
    ###### _value
    ###### not _value
    #### select not Not_Grant
    #####x error_list is str
    #####x error_list
    ##### error_list is not str and error_list=False
    ###### item_id
    ####### deposit and pid_without_ver and not recid
    ####### not (deposit and pid_without_ver and not recid)
    ###### not item_id
    

    
    ## not exist identifier_select & not temporary_save
    ### _value and _type
    ####x error_list is str
    ####x error_list is not str & error_list = True
    #### error_list is not str & error_list = False
    ### not (_value and _type)
    
    
    #x not rtn
    
    # rnt
    
    #x not flag
    
    # next_flow_action and len(next_flow_action)>0
    ## next_action is end_action
    ### deposit
    ###x not new_activity_id
    ### exist new_activity_id
    
    ### permission
    ### not permission
    
    ### "." not in current_pid
    ### "." in current_pid
    ### raise BaseException
    
    
    ## next_action is not end_action
    ###x not flag
    ### flag
    # not(next_flow_action and len(next_flow_action)>0)
    
    # action: oa policy
# def test_cancel_action_acl_nologin(client):
#     """Test of cancel action."""
#     url = url_for('weko_workflow.cancel_action',
#                   activity_id='1', action_id=1)
#     input = {'action_version': 1, 'commond': 1}
# 
#     res = client.post(url, json=input)
#     assert res.status_code == 302
#     assert res.location == url_for('security.login', next="/workflow/activity/action/1/1/cancel",_external=True)
# 
# 
# @pytest.mark.parametrize('users_index, status_code, status_code_role', [
#     (0, 200, 403),
#     (1, 200, 0),
#     (2, 200, 0),
#     (3, 200, 0),
#     (4, 200, 403),
#     (5, 200, 403),
#     (6, 200, 0),
# ])
# def test_cancel_action_acl_users(client, users, db_register, users_index, status_code, status_code_role):
#     """Test of cancel action."""
#     login(client=client, email=users[users_index]['email'])
#     url = url_for('weko_workflow.cancel_action',
#                   activity_id='1', action_id=1)
#     input = {'action_version': 1, 'commond': 1}
#     roles = {
#         'allow': [],
#         'deny': []
#     }
#     action_users = {
#         'allow': [],
#         'deny': []
#     }
# 
#     with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
#                return_value=(roles, action_users)):
#         res = client.post(url, json=input)
#         assert res.status_code == status_code
#     
#     roles = {
#         'allow': [],
#         'deny': []
#     }
#     action_users = {
#         'allow': [],
#         'deny': [users[users_index]["id"]]
#     }
#     url = url_for('weko_workflow.cancel_action', 
#                 activity_id='2',action_id=1)
# 
#     with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
#                return_value=(roles, action_users)):
#         res = client.post(url, json=input)
#         data = response_data(res)
#         assert res.status_code == status_code
#         assert data["code"] == status_code_role
# 
# def test_cancel_action_acl_guestlogin(guest, db_register):
#     input = {'action_version': 1, 'commond': 1}
#     url = url_for('weko_workflow.cancel_action',
#                   activity_id="1", action_id=1)
#     roles = {
#         'allow': [],
#         'deny': []
#     }
#     action_users = {
#         'allow': [],
#         'deny': []
#     }
# 
#     with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
#                return_value=(roles, action_users)):
#         res = guest.post(url, json=input)
#         assert res.status_code == 200
# 
# @pytest.mark.parametrize('users_index, status_code', [
#     (0, 200),
#     (1, 200),
#     (2, 200),
#     (3, 200),
#     (4, 200),
#     (5, 200),
#     (6, 200),
# ])
# def test_cancel_action(client, users, db_register, db_records, add_file, users_index, status_code):
#     login(client=client, email=users[users_index]['email'])
#     
#     # not exist item, exist files, exist cancel_pv, exist file_permission
#     input = {
#         "action_version":"1.0.0",
#         "commond":"this is test comment.",
#         "pid_value":"1.1"
#         }
#     FilePermission.init_file_permission(users[users_index]["id"],"1.1","test_file","1")
#     add_file(db_records[1][2])
#     url = url_for('weko_workflow.cancel_action',
#                   activity_id='1', action_id=1)
#     redirect_url = url_for("weko_workflow.display_activity",
#                            activity_id="1").replace("http://test_server.localdomain","")
#     print("url:{}".format(url))
#     print("redirect_url:{}".format(redirect_url))
#     res = client.post(url, json=input)
#     data = response_data(res)
#     assert res.status_code == status_code
#     assert data["code"] == 0
#     assert data["msg"] == "success"
#     assert data["data"]["redirect"] == redirect_url
#     
#     # exist item, not exist files, not exist cancel_pv, not exist file_permission
#     input = {
#         "action_version": "1.0.0",
#         "commond":"this is test comment."
#     }
#     url = url_for("weko_workflow.cancel_action",
#                   activity_id="2", action_id=1)
#     redirect_url = url_for("weko_workflow.display_activity",
#                            activity_id="2").replace("http://test_server.localdomain","")
#     res = client.post(url, json=input)
#     data = response_data(res)
#     assert res.status_code == status_code
#     assert data["code"] == 0
#     assert data["msg"] == "success"
#     assert data["data"]["redirect"] == redirect_url
# 
#     # not cancel_record, not exist rtn
#     with patch("weko_workflow.views.WekoDeposit.get_record", return_value=None):
#         with patch("weko_workflow.views.WorkActivity.quit_activity", return_value=None):
#             res = client.post(url, json = input)
#             data = response_data(res)
#             assert res.status_code == status_code
#             assert data["code"] == -1
#             assert data["msg"] == 'Error! Cannot process quit activity!'
#     
#     # raise exception
#     with patch("weko_workflow.views.PersistentIdentifier.get_by_object", side_effect=Exception):
#         res = client.post(url, json = input)
#         data = response_data(res)
#         assert res.status_code == status_code
#         assert data["code"] == -1
#         assert data["msg"] == "<class 'Exception'>"
#     
#     # not exist item and not pid
# 
# 
# def test_cancel_action_guest(guest, db, db_register):
#     input = {
#         "action_version": "1.0.0",
#         "commond":"this is test comment."
#     }
#     activity_guest = Activity(activity_id="3",workflow_id=1,flow_id=db_register["flow_define"].id,
#                               action_id=1, 
#                               activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
#                               title="test guest", extra_info={"guest_mail":"guest@test.org"},
#                               action_order=1)
#     with db.session.begin_nested():
#         db.session.add(activity_guest)
#     url = url_for("weko_workflow.cancel_action",
#                   activity_id="3", action_id=1)
#     redirect_url = url_for("weko_workflow.display_guest_activity",file_name="test_file")
#     res = guest.post(url, json=input)
#     data = response_data(res)
#     assert res.status_code == 200
#     assert data["code"] == 0
#     assert data["msg"] == "success"
#     assert data["data"]["redirect"] == redirect_url
# 
# 
# def test_send_mail_nologin(client):
#     """Test of send mail."""
#     url = url_for('weko_workflow.send_mail', activity_id='1',
#                   mail_template='a')
#     input = {}
# 
#     res = client.post(url, json=input)
#     assert res.status_code == 302
#     # TODO check that the path changed
#     # assert res.url == url_for('security.login')
# 
# 
# @pytest.mark.parametrize('users_index, status_code', [
#     (0, 200),
#     (1, 200),
#     (2, 200),
#     (3, 200),
#     (4, 200),
#     (5, 200),
#     (6, 200),
# ])
# def test_send_mail_users(client, users, users_index, status_code):
#     """Test of send mail."""
#     login(client=client, email=users[users_index]['email'])
#     url = url_for('weko_workflow.send_mail', activity_id='1',
#                   mail_template='a')
#     input = {}
#     with patch('weko_workflow.views.process_send_reminder_mail'):
#         res = client.post(url, json=input)
#         assert res.status_code == status_code
# 
# 
# def test_lock_activity_nologin(client):
#     """Test of lock activity."""
#     url = url_for('weko_workflow.lock_activity', activity_id='1')
#     input = {}
# 
#     res = client.post(url, json=input)
#     assert res.status_code == 302
#     # TODO check that the path changed
#     # assert res.url == url_for('security.login')
# 
# 
# @pytest.mark.parametrize('users_index, status_code', [
#     (0, 200),
#     (1, 200),
#     (2, 200),
#     (3, 200),
#     (4, 200),
#     (5, 200),
#     (6, 200),
# ])
# def test_lock_activity_users(client, users, users_index, status_code):
#     """Test of lock activity."""
#     login(client=client, email=users[users_index]['email'])
#     url = url_for('weko_workflow.lock_activity', activity_id='1')
#     input = {}
# 
#     with patch('weko_workflow.views.get_cache_data', return_value=""):
#         with patch('weko_workflow.views.update_cache_data'):
#             res = client.post(url, json=input)
#             assert res.status_code == status_code
# 
# 
# def test_unlock_activity_nologin(client):
#     """Test of unlock activity."""
#     url = url_for('weko_workflow.unlock_activity', activity_id='1')
#     input = {}
# 
#     res = client.post(url, json=input)
#     assert res.status_code == 302
#     # TODO check that the path changed
#     # assert res.url == url_for('security.login')
# 
# 
# @pytest.mark.parametrize('users_index, status_code', [
#     (0, 200),
#     (1, 200),
#     (2, 200),
#     (3, 200),
#     (4, 200),
#     (5, 200),
#     (6, 200),
# ])
# def test_unlock_activity_users(client, users, users_index, status_code):
#     """Test of unlock activity."""
#     login(client=client, email=users[users_index]['email'])
#     url = url_for('weko_workflow.unlock_activity', activity_id='1')
#     input = {}
# 
#     with patch('weko_workflow.views.get_cache_data', return_value=""):
#         with patch('weko_workflow.views.update_cache_data'):
#             res = client.post(url, json=input)
#             assert res.status_code == status_code
# 
# 
# def test_withdraw_confirm_nologin(client):
#     """Test of withdraw confirm."""
#     url = url_for('weko_workflow.withdraw_confirm', activity_id='1',
#                   action_id=1)
#     input = {}
# 
#     res = client.post(url, json=input)
#     assert res.status_code == 302
#     # TODO check that the path changed
#     # assert res.url == url_for('security.login')
# 
# 
# @pytest.mark.parametrize('users_index, status_code', [
#     (0, 200),
#     (1, 200),
#     (2, 200),
#     (3, 200),
#     (4, 200),
#     (5, 200),
#     (6, 200),
# ])
# def test_withdraw_confirm_users(client, users, db_register, users_index, status_code):
#     """Test of withdraw confirm."""
#     login(client=client, email=users[users_index]['email'])
#     url = url_for('weko_workflow.withdraw_confirm', activity_id='1',
#                   action_id=2)
#     input = {}
#     roles = {
#         'allow': [],
#         'deny': []
#     }
#     action_users = {
#         'allow': [],
#         'deny': []
#     }
# 
#     with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
#                return_value=(roles, action_users)):
#         res = client.post(url, json=input)
#         assert res.status_code == status_code
# 
# 
# def test_display_activity_nologin(client):
#     """Test of display activity."""
#     url = url_for('weko_workflow.display_activity', activity_id='1')
#     input = {}
# 
#     res = client.post(url, json=input)
#     assert res.status_code == 302
#     # TODO check that the path changed
#     # assert res.url == url_for('security.login')
# 
# 
# @pytest.mark.parametrize('users_index, status_code', [
#     (0, 200),
#     (1, 200),
#     (2, 200),
#     (3, 200),
#     (4, 200),
#     (5, 200),
#     (6, 200),
# ])
# def test_display_activity_users(client, users, db_register, users_index, status_code):
#     """
#     Test of display activity.
#     Expected: users[0]: AssertionError   
#     """
#     login(client=client, email=users[users_index]['email'])
#     url = url_for('weko_workflow.display_activity', activity_id='1')
#     input = {}
# 
#     activity_detail = Activity.query.filter_by(activity_id='1').one_or_none()
#     cur_action = activity_detail.action
#     action_endpoint = cur_action.action_endpoint
#     action_id = cur_action.id
#     histories = 1
#     item = None
#     steps = 1
#     temporary_comment = 1
# 
#     roles = {
#         'allow': [],
#         'deny': []
#     }
#     action_users = {
#         'allow': [],
#         'deny': []
#     }
# 
#     workflow_detail = WorkFlow.query.filter_by(id=1).one_or_none()
#     mock_render_template = MagicMock(return_value=jsonify({}))
#     with patch('weko_workflow.views.get_activity_display_info',
#                return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
#                steps, temporary_comment, workflow_detail)):
#         with patch('weko_workflow.views.check_authority_action'):
#             with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
#                        return_value=(roles, action_users)):
#                 with patch('weko_workflow.views.render_template', mock_render_template):
#                     res = client.post(url, json=input)
#                     mock_render_template.assert_called()
# 