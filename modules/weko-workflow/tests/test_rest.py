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
from datetime import datetime

from flask import json, current_app
from mock import patch
import pytest

from weko_workflow.rest import FileApplicationActivity

def url(root, kwargs = {}):
    args = ["{key}={value}".format(key = key, value = value) for key, value in kwargs.items()]
    url = "{root}?{param}".format(root = root, param = "&".join(args)) if kwargs else root
    return url

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_rest.py::test_GetActivities_get -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_GetActivities_get(app, client, db, db_register_activity, auth_headers, users):

    # test preparation
    path = '/v1/workflow/activities'
    invalid_path = '/v0/workflow/activities'
    param = {
        'status': 'todo',
        'limit': '20',
        'page': '1',
        'pretty': 'true'
    }
    headers_sysadmin = copy.deepcopy(auth_headers[0])
    headers_sysadmin.append(('Accept-Language', 'en'))
    headers_sysadmin.append(('If-None-Match', '444b63615da43896b04f8c4c18f28e8f'))
    headers_student = copy.deepcopy(auth_headers[1])
    headers_student.append(('Accept-Language', 'en'))
    headers_language = copy.deepcopy(auth_headers[0])
    headers_language.append(('Accept-Language', 'ja'))

    # Invalid version : 400 error
    res = client.get(url(invalid_path, param), headers=headers_sysadmin)
    assert res.status_code == 400
    try:
        json.loads(res.get_data())
    except:
        assert False

    # Permission error : 403
    res = client.get(url(path, param), headers=headers_student)
    assert res.status_code == 403
    try:
        json.loads(res.get_data())
    except:
        assert False

    # Invalid request parameter : 400
    param1 = copy.deepcopy(param)
    param1['status'] = 'test'
    res = client.get(url(path, param1), headers=headers_sysadmin)
    assert res.status_code == 400
    try:
        json.loads(res.get_data())
    except:
        assert False

    param2 = copy.deepcopy(param)
    param2['limit'] = '1.0'
    res = client.get(url(path, param2), headers=headers_sysadmin)
    assert res.status_code == 400
    try:
        json.loads(res.get_data())
    except:
        assert False

    param3 = copy.deepcopy(param)
    param3['limit'] = 'aaa'
    res = client.get(url(path, param3), headers=headers_sysadmin)
    assert res.status_code == 400
    try:
        json.loads(res.get_data())
    except:
        assert False

    param4 = copy.deepcopy(param)
    param4['page'] = '1.0'
    res = client.get(url(path, param4), headers=headers_sysadmin)
    assert res.status_code == 400
    try:
        json.loads(res.get_data())
    except:
        assert False

    param5 = copy.deepcopy(param)
    param5['page'] = 'aaa'
    res = client.get(url(path, param5), headers=headers_sysadmin)
    assert res.status_code == 400
    try:
        json.loads(res.get_data())
    except:
        assert False

    # Match Etag : 304
    param6 = copy.deepcopy(param)
    param6['limit'] = '10'
    res = client.get(url(path, param6), headers=headers_sysadmin)
    assert res.status_code == 304

    # Normal : 200
    res = client.get(url(path, param), headers=headers_sysadmin)
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data['total'] == 3
    assert res_data['condition']['status'] == 'todo'
    assert res_data['condition']['limit'] == '20'
    assert res_data['condition']['page'] == '1'

    # Error : 500
    with patch('weko_workflow.rest.generate_etag', side_effect=Exception):
        res = client.get(url(path, param), headers=headers_sysadmin)
        assert res.status_code == 500

    # Cange language : 200 *** Confirmed by integration test ***
    # res = client.get(url(path, param), headers=headers_language)
    # res_data = json.loads(res.get_data())


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_rest.py::test_ApproveActivity_post -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_ApproveActivity_post(app, client, db, db_register_approval, auth_headers, users):
    """Test ApproveActivity.post method."""

    current_app.config['WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'] = False

    activity_id = db_register_approval['activity'][0].activity_id
    activity_id_not_approval = db_register_approval['activity'][1].activity_id
    version = 'v1'
    invalid_version = 'v0'
    headers_sysadmin = auth_headers[0]  # OAuth token : sysadmin
    headers_student = auth_headers[1]   # OAuth token : student

    # Invalid version : 400 error
    res = client.post(
        f'/{invalid_version}/workflow/activities/{activity_id}/approve',
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_sysadmin,
    )
    assert res.status_code == 400
    try:
        json.loads(res.get_data())
    except:
        assert False

    # Activity status is not Approval : 400
    res = client.post(
        f'/{version}/workflow/activities/{activity_id_not_approval}/approve',
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_student,
    )
    assert res.status_code == 400
    try:
        json.loads(res.get_data())
    except:
        assert False

    # user who can't approve : 403
    res = client.post(
        f'/{version}/workflow/activities/{activity_id}/approve',
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_student,
    )
    assert res.status_code == 403
    try:
        json.loads(res.get_data())
    except:
        assert False

    # Normal : 200
    res = client.post(
        f'/{version}/workflow/activities/{activity_id}/approve',
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_sysadmin,
    )
    assert res.status_code == 200
    res_data = json.loads(res.get_data())
    assert res_data['next_action']['endpoint'] == 'approval'
    assert res_data['action_info']['action_status'] == 'F'


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_rest.py::test_ThrowOutActivity_post -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_ThrowOutActivity_post(app, client, db, db_register_approval, auth_headers, users):
    """Test ThrowOutActivity.post method."""

    current_app.config['WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'] = False

    activity_id = db_register_approval['activity'][0].activity_id
    activity_id_not_approval = db_register_approval['activity'][1].activity_id
    version = 'v1'
    invalid_version = 'v0'
    headers_sysadmin = auth_headers[0]  # OAuth token : sysadmin
    headers_student = auth_headers[1]   # OAuth token : student

    # Invalid version : 400 error
    res = client.post(
        f'/{invalid_version}/workflow/activities/{activity_id}/throw-out',
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_sysadmin,
    )
    assert res.status_code == 400
    try:
        json.loads(res.get_data())
    except:
        assert False

    # Activity status is not Approval : 400 error
    res = client.post(
        f'/{version}/workflow/activities/{activity_id_not_approval}/throw-out',
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_student,
    )
    assert res.status_code == 400
    try:
        json.loads(res.get_data())
    except:
        assert False

    # User who can't approve : 403 error
    res = client.post(
        f'/{version}/workflow/activities/{activity_id}/throw-out',
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_student,
    )
    assert res.status_code == 403
    try:
        json.loads(res.get_data())
    except:
        assert False

    # Normal : 200
    res = client.post(
        f'/{version}/workflow/activities/{activity_id}/throw-out',
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_sysadmin,
    )
    assert res.status_code == 200
    res_data = json.loads(res.get_data())
    assert res_data['next_action']['endpoint'] == 'identifier_grant'
    assert res_data['action_info']['action_status'] == 'T'


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_rest.py::test_FileApplicationActivity_post -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_FileApplicationActivity_post(app, client, db, db_register_for_application_api,
                                      auth_headers, users, application_api_request_body, indextree, records_restricted):
    """Test FileApplicationActivity.post method."""

    activity_id = db_register_for_application_api['activity1'].activity_id
    guest_activity_id = db_register_for_application_api['activity2'].activity_id
    other_action_activity_id = db_register_for_application_api['activity3'].activity_id
    other_action_guest_activity_id = db_register_for_application_api['activity4'].activity_id
    with_index_guest_activity_id = db_register_for_application_api['activity5'].activity_id
    edit_item_activity_id = db_register_for_application_api['activity6'].activity_id
    version = 'v1'
    invalid_version = 'v0'
    headers_sysadmin = auth_headers[0]              # OAuth token : sysadmin
    headers_student = auth_headers[1]               # OAuth token : student
    headers_not_login = auth_headers[2]             # not login
    headers_generaluser = auth_headers[3]           # OAuth token : generaluser
    headers_generaluser_no_scope = auth_headers[4]  # OAuth token : generaluser(no scope)
    index1 = indextree[0]
    index2 = indextree[1]
    activity1_extra_info = db_register_for_application_api['activity1'].extra_info

    # Invalid version : 400 error
    body = {"aaa":"123"}
    res = client.post(
        f'/{invalid_version}/workflow/activities/{activity_id}/application',
        data=json.dumps(body),
        content_type='application/json',
        headers=headers_sysadmin,
    )
    assert res.status_code == 400
    try:
        json.loads(res.get_data())
    except:
        assert False

    # request body is empty : 400 error
    body = {}
    res = client.post(
        f'/{version}/workflow/activities/{activity_id}/application',
        data=json.dumps(body),
        content_type='application/json',
        headers=headers_sysadmin,
    )
    assert res.status_code == 400
    try:
        json.loads(res.get_data())
    except:
        assert False

    # Guest: Invalid token : 400 error
    params = {"token": "aaa"}
    body = {"aaa":"123"}
    token_valid = False
    with patch('weko_workflow.rest.validate_guest_activity_token', return_value=(token_valid, guest_activity_id, "guest@example.org")):
        res = client.post(
            url(f'/{version}/workflow/activities/{guest_activity_id}/application', params),
            data=json.dumps(body),
            content_type='application/json',
            headers=headers_not_login,
        )
    assert res.status_code == 400
    try:
        json.loads(res.get_data())
    except:
        assert False

    # Guest: Expired token : 400 error
    params = {"token": "aaa"}
    body = {"aaa":"123"}
    token_valid = True
    with patch('weko_workflow.rest.validate_guest_activity_token', return_value=(token_valid, guest_activity_id, "guest@example.org")):
        with patch('weko_workflow.rest.validate_guest_activity_expired', return_value="The specified link has expired."):
            res = client.post(
                url(f'/{version}/workflow/activities/{guest_activity_id}/application', params),
                data=json.dumps(body),
                content_type='application/json',
                headers=headers_not_login,
            )
    assert res.status_code == 400
    try:
        json.loads(res.get_data())
    except:
        assert False

    # Invalid enum : 400 error
    params = {}
    body = application_api_request_body[1]
    res_check = 0   # OK
    with patch('weko_workflow.rest.check_authority_action', return_value=res_check):
        res = client.post(
            url(f'/{version}/workflow/activities/{activity_id}/application', params),
            data=json.dumps(body),
            content_type='application/json',
            headers=headers_student,
        )
    assert res.status_code == 400
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False
    assert "aaa is not one of enum in item_1616221960771.subitem_restricted_access_research_plan_type" in res_json["message"]
    
    
    # Guest: Invalid enum : 400 error
    params = {"token": "aaa"}
    body = application_api_request_body[1]
    token_valid = True
    record_detail_alt = {
        "record": {"dummy": "dummyVal"},
    }
    with patch('weko_workflow.rest.check_authority_action', return_value=res_check):
        with patch('weko_workflow.rest.validate_guest_activity_token', return_value=(token_valid, with_index_guest_activity_id, "guest@example.org")):
            with patch('weko_workflow.rest.get_main_record_detail', return_value=record_detail_alt):
                res = client.post(
                    url(f'/{version}/workflow/activities/{with_index_guest_activity_id}/application', params),
                    data=json.dumps(body),
                    content_type='application/json',
                    headers=headers_not_login,
                )
    assert res.status_code == 400
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False

    # missing required metadata : 400 error
    params = {}
    body = application_api_request_body[2]
    res_check = 0   # OK
    with patch('weko_workflow.rest.check_authority_action', return_value=res_check):
        res = client.post(
            url(f'/{version}/workflow/activities/{activity_id}/application', params),
            data=json.dumps(body),
            content_type='application/json',
            headers=headers_student,
        )
    assert res.status_code == 400
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False
    assert "missing requied metadata: " in res_json["message"]
    assert "pubdate" in res_json["message"]

    # missing required metadata(is_hidden_pubdate=True) : 400 error
    params = {}
    body = application_api_request_body[2]
    res_check = 0   # OK
    dummy_usage_data = dict(
            usage_type='Report',
            dataset_usage='',
            usage_data_name='',
            mail_address='',
            university_institution='',
            affiliated_division_department='',
            position='',
            position_other='',
            phone_number='',
            usage_report_id='',
            wf_issued_date='',
            item_title=''
        )
    with patch('weko_workflow.rest.check_authority_action', return_value=res_check):
        with patch('weko_workflow.rest.is_hidden_pubdate', return_value=True):
            with patch('weko_workflow.rest.get_usage_data', return_value=dummy_usage_data):
                res = client.post(
                    url(f'/{version}/workflow/activities/{activity_id}/application', params),
                    data=json.dumps(body),
                    content_type='application/json',
                    headers=headers_student,
                )
    assert res.status_code == 400
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False
    assert "missing requied metadata: " in res_json["message"]
    assert "pubdate" not in res_json["message"]

    # action status is not ItemRegistration : 400 error
    params = {}
    body = application_api_request_body[2]
    res_check = 0   # OK
    with patch('weko_workflow.rest.check_authority_action', return_value=res_check):
        res = client.post(
            url(f'/{version}/workflow/activities/{other_action_activity_id}/application', params),
            data=json.dumps(body),
            content_type='application/json',
            headers=headers_student,
        )
    assert res.status_code == 400
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False
    assert "Activity status is not Item Registration." in res_json["message"]

    # Guest: action status is not ItemRegistration : 400 error
    params = {"token": "aaa"}
    body = {"aaa":"123"}
    token_valid = True
    with patch('weko_workflow.rest.validate_guest_activity_token', return_value=(token_valid, guest_activity_id, "guest@example.org")):
        res = client.post(
            url(f'/{version}/workflow/activities/{other_action_guest_activity_id}/application', params),
            data=json.dumps(body),
            content_type='application/json',
            headers=headers_not_login,
        )
    assert res.status_code == 400
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False
    assert "Activity status is not Item Registration." in res_json["message"]

    # No scope : 403 error
    params = {}
    body = application_api_request_body[2]
    res_check = 0   # OK
    with patch('weko_workflow.rest.check_authority_action', return_value=res_check):
        res = client.post(
            url(f'/{version}/workflow/activities/{activity_id}/application', params),
            data=json.dumps(body),
            content_type='application/json',
            headers=headers_generaluser_no_scope,
        )
    assert res.status_code == 403
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False

    # No permission to ItemRegistration action  : 403 error
    params = {"index_ids": f'{index1["id"]},{index2["id"]}'}
    body = application_api_request_body[0]
    res_check = 1   # NG
    with patch('weko_workflow.rest.check_authority_action', return_value=res_check):
        
        class DummyRedis():
            def exists(self, v):
                return True
        
        class DummySessionstore():
            def __init__(self):
                self.redis = DummyRedis()
            
            def get(self, v):
                return True

        with patch('weko_workflow.rest.RedisConnection.connection', return_value=DummySessionstore()):
            res = client.post(
                url(f'/{version}/workflow/activities/{activity_id}/application', params),
                data=json.dumps(body),
                content_type='application/json',
                headers=headers_generaluser,
            )
    assert res.status_code == 403
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False

    # uneditable : 403
    params = {"index_ids": index1["id"]}
    body = application_api_request_body[0]
    res_check = 0   # OK
    with patch('weko_workflow.rest.check_authority_action', return_value=res_check):
        with patch('weko_workflow.rest.handle_check_item_is_locked', side_effect=Exception):
            res = client.post(
                url(f'/{version}/workflow/activities/{edit_item_activity_id}/application', params),
                data=json.dumps(body),
                content_type='application/json',
                headers=headers_student,
            )
    assert res.status_code == 403
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False
    
    # activity not found : 404 error
    params = {"index_ids": f'{index1["id"]}'}
    body = application_api_request_body[0]
    res_check = 0   # OK
    with patch('weko_workflow.rest.check_authority_action', return_value=res_check):
        res = client.post(
            url(f'/{version}/workflow/activities/aaa/application', params),
            data=json.dumps(body),
            content_type='application/json',
            headers=headers_generaluser,
        )
    assert res.status_code == 404
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False
    
    # Guest: activity not found : 404 error
    params = {"token": "aaa"}
    body = {"aaa":"123"}
    token_valid = True
    with patch('weko_workflow.rest.validate_guest_activity_token', return_value=(token_valid, guest_activity_id, "guest@example.org")):
        res = client.post(
            url(f'/{version}/workflow/activities/aaa/application', params),
            data=json.dumps(body),
            content_type='application/json',
            headers=headers_not_login,
        )
    assert res.status_code == 404
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False

    # Not found index : 404 error
    params = {"index_ids": "999"}
    body = application_api_request_body[0]
    res_check = 0   # OK
    with patch('weko_workflow.rest.check_authority_action', return_value=res_check):
        res = client.post(
            url(f'/{version}/workflow/activities/{activity_id}/application', params),
            data=json.dumps(body),
            content_type='application/json',
            headers=headers_student,
        )
    assert res.status_code == 404
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False

    # index not specified : 404 error
    params = {}
    body = application_api_request_body[0]
    res_check = 0   # OK
    with patch('weko_workflow.rest.check_authority_action', return_value=res_check):
        res = client.post(
            url(f'/{version}/workflow/activities/{activity_id}/application', params),
            data=json.dumps(body),
            content_type='application/json',
            headers=headers_student,
        )
    assert res.status_code == 404
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False
    
    # Exception : 404
    params = {"index_ids": index1["id"]}
    body = application_api_request_body[0]
    res_check = 0   # OK
    with patch('weko_workflow.rest.check_authority_action', return_value=res_check):
        with patch('weko_workflow.rest.get_pid_and_record', side_effect=Exception):
            with pytest.raises(Exception):
                res = client.post(
                    url(f'/{version}/workflow/activities/{edit_item_activity_id}/application', params),
                    data=json.dumps(body),
                    content_type='application/json',
                    headers=headers_student,
                )
    assert res.status_code == 404
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False

    # Server error : 500
    params = {"index_ids": index1["id"]}
    body = application_api_request_body[0]
    res_check = 0   # OK
    with patch('weko_workflow.rest.check_authority_action', return_value=res_check):
        with patch('weko_workflow.rest.save_activity_data', side_effect=Exception):
            res = client.post(
                url(f'/{version}/workflow/activities/{edit_item_activity_id}/application', params),
                data=json.dumps(body),
                content_type='application/json',
                headers=headers_student,
            )
    assert res.status_code == 500
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False

    # Success : 200
    params = {"index_ids": index1["id"]}
    body = application_api_request_body[0]
    res_check = 0   # OK
    with patch('weko_workflow.rest.check_authority_action', return_value=res_check):
        with patch("weko_handle.api.Handle.register_handle",return_value="handle:00.000.12345/0000000001"):
            res = client.post(
                url(f'/{version}/workflow/activities/{activity_id}/application', params),
                data=json.dumps(body),
                content_type='application/json',
                headers=headers_student,
            )
    assert res.status_code == 200
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False
    assert res_json["action_info"]["action_id"] == 3
    assert res_json["action_info"]["action_status"] == "F"
    assert res_json["action_info"]["action_user"] == users[8]["id"]
    check = copy.deepcopy(body)
    related_title = activity1_extra_info["related_title"]
    fullname = check["item_1616221851421"]["subitem_fullname"]
    check["item_1616221831877"]["subitem_restricted_access_dataset_usage"] = related_title
    check["item_1616221960771"] = {"subitem_restricted_access_research_plan_type": "Abstract"}
    check["item_1616222047122"]["subitem_restricted_access_wf_issued_date"] = datetime.today().strftime('%Y-%m-%d')
    check["item_1616222047122"]["subitem_restricted_access_wf_issued_date_type"] = "Created"
    check["item_1616222067301"] = {
        "subitem_restricted_access_application_date": datetime.today().strftime('%Y-%m-%d'),
        "subitem_restricted_access_application_date_type": "Issued"
    }
    check["item_1616222093486"] = {"subitem_restricted_access_approval_date_type": "Accepted"}
    check["item_1616222117209"] = {
        "subitem_restricted_access_item_title": f"利用申請{datetime.today().strftime('%Y%m%d')}{related_title}_{fullname}"
    }
    check["path"] = [f"{index1['id']}"]
    assert res_json["registerd_data"] == check
    
    # Guest: Success : 200
    params = {"token": "aaa"}
    body = application_api_request_body[0]
    token_valid = True
    with patch('weko_workflow.rest.validate_guest_activity_token', return_value=(token_valid, with_index_guest_activity_id, "guest@example.org")):
        with patch("weko_handle.api.Handle.register_handle",return_value="handle:00.000.12345/0000000002"):
            res = client.post(
                url(f'/{version}/workflow/activities/{with_index_guest_activity_id}/application', params),
                data=json.dumps(body),
                content_type='application/json',
                headers=headers_not_login,
            )
    assert res.status_code == 200
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False
    assert res_json["action_info"]["action_id"] == 3
    assert res_json["action_info"]["action_status"] == "F"
    assert res_json["action_info"]["action_user"] == None
    check = copy.deepcopy(body)
    related_title = activity1_extra_info["related_title"]
    fullname = check["item_1616221851421"]["subitem_fullname"]
    check["item_1616221831877"]["subitem_restricted_access_dataset_usage"] = related_title
    check["item_1616221960771"] = {"subitem_restricted_access_research_plan_type": "Abstract"}
    check["item_1616222047122"]["subitem_restricted_access_wf_issued_date"] = datetime.today().strftime('%Y-%m-%d')
    check["item_1616222047122"]["subitem_restricted_access_wf_issued_date_type"] = "Created"
    check["item_1616222067301"] = {
        "subitem_restricted_access_application_date": datetime.today().strftime('%Y-%m-%d'),
        "subitem_restricted_access_application_date_type": "Issued"
    }
    check["item_1616222093486"] = {"subitem_restricted_access_approval_date_type": "Accepted"}
    check["item_1616222117209"] = {
        "subitem_restricted_access_item_title": f"利用申請{datetime.today().strftime('%Y%m%d')}{related_title}_{fullname}"
    }
    check["path"] = [f"{index2['id']}"]
    assert res_json["registerd_data"] == check

    # Success edit item: 200
    params = {"index_ids": index1["id"]}
    body = application_api_request_body[0]
    res_check = 0   # OK
    with patch('weko_workflow.rest.check_authority_action', return_value=res_check):
        res = client.post(
            url(f'/{version}/workflow/activities/{edit_item_activity_id}/application', params),
            data=json.dumps(body),
            content_type='application/json',
            headers=headers_student,
        )
    assert res.status_code == 200
    try:
        res_json = json.loads(res.get_data())
    except:
        assert False
    assert res_json["action_info"]["action_id"] == 3
    assert res_json["action_info"]["action_status"] == "F"
    assert res_json["action_info"]["action_user"] == users[8]["id"]
    check = copy.deepcopy(body)
    related_title = activity1_extra_info["related_title"]
    fullname = check["item_1616221851421"]["subitem_fullname"]
    check["item_1616221831877"]["subitem_restricted_access_dataset_usage"] = related_title
    check["item_1616221960771"] = {"subitem_restricted_access_research_plan_type": "Abstract"}
    check["item_1616222047122"]["subitem_restricted_access_wf_issued_date"] = datetime.today().strftime('%Y-%m-%d')
    check["item_1616222047122"]["subitem_restricted_access_wf_issued_date_type"] = "Created"
    check["item_1616222067301"] = {
        "subitem_restricted_access_application_date": datetime.today().strftime('%Y-%m-%d'),
        "subitem_restricted_access_application_date_type": "Issued"
    }
    check["item_1616222093486"] = {"subitem_restricted_access_approval_date_type": "Accepted"}
    check["item_1616222117209"] = {
        "subitem_restricted_access_item_title": f"利用申請{datetime.today().strftime('%Y%m%d')}{related_title}_{fullname}"
    }
    check["path"] = [f"{index1['id']}"]
    assert res_json["registerd_data"] == check

    
    # test for _clean_file_metadata()
    data = {
        "item_1616221831877": {
            "subitem_restricted_access_dataset_usage": "test"
        },
        "item_1616221987611": {
            "subitem_restricted_access_research_plan_type": "Abstract"
        },
        "pubdate": "2023-08-25",
        "deleted_items":[
            "item_1616221831870"
        ]
    }
    item_map = {
        "file.URI.@value": "item_1616221987611.url.url"
    }
    with patch('weko_workflow.rest.get_mapping', return_value=item_map):
        with patch('weko_workflow.rest.Mapping.get_record'):
            result, is_cleaned = FileApplicationActivity._clean_file_metadata(1, data)
            assert result == data
            assert is_cleaned == False

            data.pop("item_1616221987611")
            result, is_cleaned = FileApplicationActivity._clean_file_metadata(1, data)
            data["deleted_items"].append("item_1616221987611")
            assert result == data
            assert is_cleaned == True

    # test for _autofill_thumbnail_metadata()
    class DummyFile():
        def __init__(self, case:int=0) -> None:
            self.is_thumbnail = bool(case % 2)
            self.key = f"key_{case}"
            self.bucket_id = f"bucket_{case}"
            self.version_id = case

    key = "thumbnail_key"
    data1 = {}
    data2 = {"deleted_items": ["aaa"]}
    files1 = [DummyFile(1), DummyFile(2), DummyFile(3)]
    files2 = [DummyFile(0)]
    with patch('weko_workflow.rest.get_thumbnail_key', return_value=key):
        result = FileApplicationActivity._autofill_thumbnail_metadata(1, data1, files1)
        assert result == {
            "thumbnail_key": {
                "subitem_thumbnail": [
                    {
                        "thumbnail_label": "key_1",
                        "thumbnail_url": "/api/files/bucket_1/key_1?versionId=1"
                    },
                    {
                        "thumbnail_label": "key_3",
                        "thumbnail_url": "/api/files/bucket_3/key_3?versionId=3"
                    }
                ]
            }
        }

        result = FileApplicationActivity._autofill_thumbnail_metadata(1, data2, files2)
        assert result == {
            "deleted_items": [
                "aaa",
                "thumbnail_key"
            ]
        }