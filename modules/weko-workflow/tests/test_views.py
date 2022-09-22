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
from typing_extensions import Self
from unittest.mock import MagicMock
from weko_workflow.api import WorkActivity
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
from weko_workflow.models import ActionFeedbackMail, Activity, ActionStatus, Action, WorkFlow, FlowDefine, FlowAction
from invenio_accounts.testutils import login_user_via_session as login
from weko_workflow.views import unlock_activity, check_approval, get_feedback_maillist, save_activity
from weko_records_ui.models import FilePermission
def response_data(response):
    return json.loads(response.data)


def test_index_acl_nologin(client):
    """_summary_

    Args:
        client (FlaskClient): flask test client
    """    
    url = url_for('weko_workflow.index')
    res =  client.get(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login', next="/workflow/",_external=True)

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

def test_init_activity_acl_nologin(client):
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




def test_init_activity_guest_nologin(client):
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


def test_find_doi_nologin(client):
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


def test_save_activity_nologin(client):
    """Test of save activity."""
    url = url_for('weko_workflow.save_activity')
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
def test_save_activity_users(client, users, users_index, status_code):
    """Test of save activity."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.save_activity')
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == status_code


def test_save_feedback_maillist_nologin(client):
    """Test of save feedback maillist."""
    url = url_for('weko_workflow.save_feedback_maillist',
                  activity_id='1', action_id=1)
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


def test_previous_action_nologin(client):
    """Test of previous action."""
    url = url_for('weko_workflow.previous_action', activity_id='1',
                  action_id=1, req=1)
    input = {}

    res = client.post(url, json=input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_views.py::test_previous_action_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
])
def test_previous_action_users(client, users, db_workflow, db_records,users_index, status_code):
    """Test of previous action."""
    login(client=client, email=users[users_index]['email'])
    flow_define = db_workflow['flow_define']
    url = url_for('weko_workflow.previous_action', activity_id='A-00000000-00000',
                  action_id=3, req=1)
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


def test_next_action_nologin(client, db_register,db_register2):
    """Test of next action."""
    url = url_for('weko_workflow.next_action', activity_id='1',
                  action_id=1)
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
def test_next_action_users(client, users, db_register, users_index, status_code):
    """Test of next action."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.next_action', activity_id='1',
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
        assert res.status_code == status_code


def test_cancel_action_nologin(client):
    """Test of cancel action."""
    url = url_for('weko_workflow.cancel_action',
                  activity_id='1', action_id=1)
    input = {'action_version': 1, 'commond': 1}

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
def test_cancel_action_users(client, users, db_register, users_index, status_code):
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
        with patch('weko_workflow.views.WorkActivity.upt_activity_action_status',
                   return_value={}):
            with patch('weko_workflow.views.WorkActivity.quit_activity',
                       return_value=None):
                res = client.post(url, json=input)
                assert res.status_code == status_code


def test_send_mail_nologin(client):
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


def test_lock_activity_nologin(client):
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
            assert res.status_code == status_code


def test_unlock_activity_nologin(client):
    """Test of unlock activity."""
    url = url_for('weko_workflow.unlock_activity', activity_id='1')
    input = {'locked_value':'1-1661748792565'}

    res = client.post(url, json=input)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/activity/unlock/1",_external=True)
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    # (2, 200),
    # (3, 200),
    # (4, 200),
    # (5, 200),
    # (6, 200),
])
def test_unlock_activity_users(client, users, users_index, status_code):
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
    # (2, 200),
    # (3, 200),
    # (4, 200),
    # (5, 200),
    # (6, 200),
])
def test_unlock_activity(client, users, db_register, users_index, status_code):
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.unlock_activity', activity_id='1')

    #locked_valueが空文字で、cur_locked_valも空文字の場合
    input = {'locked_value':'1-1661748792565'}
    with patch('weko_workflow.views.get_cache_data', return_value=""):
        res = client.post(url, json=input)
        data = json.loads(res.data.decode("utf-8"))
        assert res.status_code==status_code
        assert data["code"] == 200
        assert data["msg"] == 'Not unlock'

    #locked_valueが空でなく、cur_locked_valと一致する場合
    input = {'locked_value':'1-1661748792565'}
    with patch('weko_workflow.views.get_cache_data', return_value='1-1661748792565'):
        with patch('weko_workflow.views.delete_cache_data'):
            res = client.post(url, json=input)
            data = json.loads(res.data.decode("utf-8"))
            assert res.status_code==status_code
            assert data["code"] == 200
            assert data["msg"] == 'Unlock success'

def test_check_approval_nologin(client):
    """Test of check approval."""
    url = url_for('weko_workflow.check_approval', activity_id='1')

    res = client.get(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/check_approval/1",_external=True)

@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    # (2, 200),
    # (3, 200),
    # (4, 200),
    # (5, 200),
    # (6, 200),
])
def test_check_approval_users(client, users, users_index, status_code):
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
        assert res.status_code == status_code

@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    # (2, 200),
    # (3, 200),
    # (4, 200),
    # (5, 200),
    # (6, 200),
])
def test_check_approval(client, users, db_register, users_index, status_code):
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.check_approval', activity_id='1')
    response = {
        'check_handle': -1,
        'check_continue': -1,
        'error': 1
    }
    with patch('weko_workflow.views.check_continue', return_value=response):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code==status_code
        assert data['check_handle'] == -1
        assert data['check_continue'] == -1
        assert data['error'] == 1
    
    with patch('weko_workflow.views.check_continue', side_effect=Exception):
        res = client.get(url)
        data = response_data(res)
        assert res.status_code==status_code
        assert data['check_handle'] == -1
        assert data['check_continue'] == -1
        assert data['error'] == -1

def test_get_feedback_maillist_nologin(client):
    """Test of get feedback maillist."""
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='1')

    res = client.get(url)
    assert res.status_code == 302
    assert res.location == url_for('security.login',next="/workflow/get_feedback_maillist/1",_external=True)

@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    # (2, 200),
    # (3, 200),
    # (4, 200),
    # (5, 200),
    # (6, 200),
])
def test_get_feedback_maillist_users(client, users, users_index, status_code):
    """Test of get feedback maillist."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.get_feedback_maillist', activity_id='1')

    res = client.get(url)
    assert res.status_code != 302

@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    # (2, 200),
    # (4, 200),
    # (5, 200),
    # (6, 200),
])
def test_get_feedback_maillist(client, users, db_register, users_index, status_code):
    login(client=client, email=users[users_index]['email'])
    
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
        assert res.status_code==status_code
        assert data['code'] == -1
        assert data['msg'] == 'Error'


def test_save_activity_nologin(client):
    """Test of save activity."""
    url = url_for('weko_workflow.save_activity')
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}

    res = client.post(url, json=input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')

@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    # (2, 200),
    # (3, 200),
    # (4, 200),
    # (5, 200),
    # (6, 200),
])
def test_save_activity_users(client, users, users_index, status_code):
    """Test of save activity."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.save_activity')
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}

    res = client.post(url, json=input)
    assert res.status_code != 302

@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    # (2, 200),
    # (3, 200),
    # (4, 200),
    # (5, 200),
    # (6, 200),
])
def test_save_activity(client, users, db_register, users_index, status_code):
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.save_activity')
    response = {
        "success": True,
        "msg": ""
    }

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


#save_activityは@login_required_customizeなのでguestuserloginのテストも必要
def test_save_activity_acl_guestlogin(guest):
    input = {"activity_id":"A-20220921-00001","title":"test","shared_user_id":-1}
    url = url_for('weko_workflow.save_activity')

    res = guest.post(url, json=input)
    assert res.status_code == 200


def test_withdraw_confirm_nologin(client):
    """Test of withdraw confirm."""
    url = url_for('weko_workflow.withdraw_confirm', activity_id='1',
                  action_id=1)
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
def test_withdraw_confirm_users(client, users, db_register, users_index, status_code):
    """Test of withdraw confirm."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.withdraw_confirm', activity_id='1',
                  action_id=2)
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


def test_display_activity_nologin(client):
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
