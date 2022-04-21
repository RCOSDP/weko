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
from flask import Flask, json, jsonify, url_for
from invenio_db import db
from sqlalchemy import func

import weko_workflow.utils
from weko_workflow import WekoWorkflow
from weko_workflow.models import Activity, ActivityAction, WorkFlow
from invenio_accounts.testutils import login_user_via_session as login


def _post(client, url, json_data):
    return client.post(url, json=json_data)


def test_init_activity_nologin(client):
    """Test init_activity."""
    url = url_for('weko_workflow.init_activity')
    input = {'workflow_id': 1, 'flow_id': 1}

    res = _post(client, url, input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
])
def test_init_activity_users(client, users, users_index, status_code):
    """Test init_activity."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.init_activity')
    input = {'workflow_id': 1, 'flow_id': 1}

    res = _post(client, url, input)
    assert res.status_code == status_code


def test_init_activity_guest_nologin(client):
    """Test init activity for guest user."""
    url = url_for('weko_workflow.init_activity_guest')
    input = {'guest_mail': 'test@guest.com', 'workflow_id': 1, 'flow_id': 1,
             'item_type_id': 1, 'record_id': 1, 'guest_item_title': 'test',
             'file_name': 'test_file'}

    res = _post(client, url, input)
    assert res.status_code == 200


@pytest.mark.parametrize('users_index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
])
def test_init_activity_guest_users(client, users, users_index, status_code):
    """Test init activity for guest user."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.init_activity_guest')
    input = {'guest_mail': 'test@guest.com', 'workflow_id': 1, 'flow_id': 1,
             'item_type_id': 1, 'record_id': 1, 'guest_item_title': 'test',
             'file_name': 'test_file'}

    res = _post(client, url, input)
    assert res.status_code == status_code


def test_find_doi_nologin(client):
    """Test of find doi."""
    url = url_for('weko_workflow.find_doi')
    input = {}

    res = _post(client, url, input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
])
def test_find_doi_users(client, users, users_index, status_code):
    """Test of find doi."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.find_doi')
    input = {}

    res = _post(client, url, input)
    assert res.status_code == status_code


def test_save_activity_nologin(client):
    """Test of save activity."""
    url = url_for('weko_workflow.save_activity')
    input = {}

    res = _post(client, url, input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
])
def test_save_activity_users(client, users, users_index, status_code):
    """Test of save activity."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.save_activity')
    input = {}

    res = _post(client, url, input)
    assert res.status_code == status_code


def test_save_feedback_maillist_nologin(client):
    """Test of save feedback maillist."""
    url = url_for('weko_workflow.save_feedback_maillist',
                  activity_id='1', action_id=1)
    input = {}

    res = _post(client, url, input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
])
def test_save_feedback_maillist_users(client, users, users_index, status_code):
    """Test of save feedback maillist."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.save_feedback_maillist',
                  activity_id='1', action_id=1)
    input = {}
    activity = Activity(activity_id='1',workflow_id=1, flow_id=1,
                        action_id=2, activity_login_user=1,
                        activity_update_user=1,
                        activity_start='2022/04/14 3:01:53.931',
                        activity_community_id=3,
                        activity_confirm_term_of_use=True,
                        title='test', shared_user_id=-1, extra_info={},
                        action_order=6)
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }

    with patch('weko_workflow.views.WorkActivity.get_activity_by_id',
               return_value=activity):
        with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
                   return_value=(roles, action_users)):
            res = _post(client, url, input)
            assert res.status_code == status_code


def test_previous_action_nologin(client):
    """Test of previous action."""
    url = url_for('weko_workflow.previous_action', activity_id='1',
                  action_id=1, req=1)
    input = {}

    res = _post(client, url, input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
])
def test_previous_action_users(client, users, users_index, status_code):
    """Test of previous action."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.previous_action', activity_id='1',
                  action_id=1, req=1)
    input = {}
    activity = Activity(activity_id='1',workflow_id=1, flow_id=1,
                        action_id=2, activity_login_user=1,
                        activity_update_user=1,
                        activity_start='2022/04/14 3:01:53.931',
                        activity_community_id=3,
                        activity_confirm_term_of_use=True,
                        title='test', shared_user_id=-1, extra_info={},
                        action_order=6)
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }

    with patch('weko_workflow.views.WorkActivity.get_activity_by_id',
               return_value=activity):
        with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
                   return_value=(roles, action_users)):
            res = _post(client, url, input)
            assert res.status_code == status_code


def test_next_action_nologin(client):
    """Test of next action."""
    url = url_for('weko_workflow.next_action', activity_id='1',
                  action_id=1)
    input = {}

    res = _post(client, url, input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
])
def test_next_action_users(client, users, users_index, status_code):
    """Test of next action."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.next_action', activity_id='1',
                  action_id=1)
    input = {}
    activity = Activity(activity_id='1',workflow_id=1, flow_id=1,
                        action_id=2, activity_login_user=1,
                        activity_update_user=1,
                        activity_start='2022/04/14 3:01:53.931',
                        activity_community_id=3,
                        activity_confirm_term_of_use=True,
                        title='test', shared_user_id=-1, extra_info={},
                        action_order=6)
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }

    with patch('weko_workflow.views.WorkActivity.get_activity_by_id',
               return_value=activity):
        with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
                   return_value=(roles, action_users)):
            res = _post(client, url, input)
            assert res.status_code == status_code


def test_cancel_action_nologin(client):
    """Test of cancel action."""
    url = url_for('weko_workflow.cancel_action',
                  activity_id='1', action_id=1)
    input = {'action_version': 1, 'commond': 1}

    res = _post(client, url, input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
])
def test_cancel_action_users(client, users, users_index, status_code):
    """Test of cancel action."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.cancel_action',
                  activity_id='1', action_id=1)
    input = {'action_version': 1, 'commond': 1}
    activity = Activity(activity_id='1',workflow_id=1, flow_id=1,
                        action_id=2, activity_login_user=1,
                        activity_update_user=1,
                        activity_start='2022/04/14 3:01:53.931',
                        activity_community_id=3,
                        activity_confirm_term_of_use=True,
                        title='test', shared_user_id=-1, extra_info={},
                        action_order=6)
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }

    with patch('weko_workflow.views.WorkActivity.get_activity_by_id',
               return_value=activity):
        with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
                   return_value=(roles, action_users)):
            with patch('weko_workflow.views.WorkActivity.upt_activity_action_status',
                       return_value={}):
                with patch('weko_workflow.views.WorkActivity.quit_activity',
                           return_value=None):
                    res = _post(client, url, input)
                    assert res.status_code == status_code


def test_send_mail_nologin(client):
    """Test of send mail."""
    url = url_for('weko_workflow.send_mail', activity_id='1',
                  mail_template='a')
    input = {}

    res = _post(client, url, input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
])
def test_send_mail_users(client, users, users_index, status_code):
    """Test of send mail."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.send_mail', activity_id='1',
                  mail_template='a')
    input = {}

    res = _post(client, url, input)
    assert res.status_code == status_code


def test_lock_activity_nologin(client):
    """Test of lock activity."""
    url = url_for('weko_workflow.lock_activity', activity_id='1')
    input = {}

    res = _post(client, url, input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
])
def test_lock_activity_users(client, users, users_index, status_code):
    """Test of lock activity."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.lock_activity', activity_id='1')
    input = {}

    with patch('weko_workflow.views.get_cache_data', return_value=""):
        with patch('weko_workflow.views.update_cache_data'):
            res = _post(client, url, input)
            assert res.status_code == status_code


def test_unlock_activity_nologin(client):
    """Test of unlock activity."""
    url = url_for('weko_workflow.unlock_activity', activity_id='1')
    input = {}

    res = _post(client, url, input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
])
def test_unlock_activity_users(client, users, users_index, status_code):
    """Test of unlock activity."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.unlock_activity', activity_id='1')
    input = {}

    with patch('weko_workflow.views.get_cache_data', return_value=""):
        with patch('weko_workflow.views.update_cache_data'):
            res = _post(client, url, input)
            assert res.status_code == status_code


def test_withdraw_confirm_nologin(client):
    """Test of withdraw confirm."""
    url = url_for('weko_workflow.withdraw_confirm', activity_id='1',
                  action_id=1)
    input = {}

    res = _post(client, url, input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
])
def test_withdraw_confirm_users(client, users, users_index, status_code):
    """Test of withdraw confirm."""
    login(client=client, email=users[users_index]['email'])
    url = url_for('weko_workflow.withdraw_confirm', activity_id='1',
                  action_id=2)
    input = {}
    activity = Activity(activity_id='1',workflow_id=1, flow_id=1,
                        action_id=2, activity_login_user=1,
                        activity_update_user=1,
                        activity_start='2022/04/14 3:01:53.931',
                        activity_community_id=3,
                        activity_confirm_term_of_use=True,
                        title='test', shared_user_id=-1, extra_info={},
                        action_order=6)
    roles = {
        'allow': [],
        'deny': []
    }
    action_users = {
        'allow': [],
        'deny': []
    }

    with patch('weko_workflow.views.WorkActivity.get_activity_by_id',
               return_value=activity):
        with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
                   return_value=(roles, action_users)):
            res = _post(client, url, input)
            assert res.status_code == status_code


def test_display_activity_nologin(client):
    """Test of display activity."""
    url = url_for('weko_workflow.display_activity', activity_id='1')
    input = {}

    res = _post(client, url, input)
    assert res.status_code == 302
    # TODO check that the path changed
    # assert res.url == url_for('security.login')


@pytest.mark.parametrize('users_index, status_code', [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
])
def test_display_activity_users(client, users, users_index, status_code):
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

    workflow_detail = WorkFlow(
        flows_id='{39ba43f0-c876-4086-97f4-d9aed1be8083}',
        itemtype_id=15, flow_id=1, is_deleted=False, open_restricted=True,
        is_gakuninrdm=False)
    mock_render_template = MagicMock(return_value=jsonify({}))
    with patch('weko_workflow.views.get_activity_display_info',
               return_value=(action_endpoint, action_id, activity_detail, cur_action, histories, item, \
               steps, temporary_comment, workflow_detail)):
        with patch('weko_workflow.views.check_authority_action'):
            with patch('weko_workflow.views.WorkActivity.get_activity_action_role',
                       return_value=(roles, action_users)):
                with patch('weko_workflow.views.render_template', mock_render_template):
                    res = _post(client, url, input)
                    mock_render_template.assert_called()
