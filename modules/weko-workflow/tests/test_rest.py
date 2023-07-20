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

from flask import json, current_app

def url(root, kwargs = {}):
    args = ["{key}={value}".format(key = key, value = value) for key, value in kwargs.items()]
    url = "{root}?{param}".format(root = root, param = "&".join(args)) if kwargs else root
    return url

# .tox/c1/bin/pytest --cov=weko_workflow tests/test_rest.py::test_GetActivities_get -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_GetActivities_get(app, client, db, db_register_activity, auth_headers, users):

    # test preparation
    path = '/v1.0/activities'
    invalid_path = '/v0.0/activities'
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

    # Cange language : 200 *** Confirmed by integration test ***
    # res = client.get(url(path, param), headers=headers_language)
    # res_data = json.loads(res.get_data())


# .tox/c1/bin/pytest --cov=weko_workflow tests/test_rest.py::test_ApproveActivity_post -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp
def test_ApproveActivity_post(app, client, db, db_register_approval, auth_headers, users):
    """Test ApproveActivity.post method."""

    current_app.config['WEKO_WORKFLOW_ENABLE_CONTRIBUTOR'] = False

    activity_id = db_register_approval['activity'][0].activity_id
    activity_id_not_approval = db_register_approval['activity'][1].activity_id
    version = 'v1.0'
    invalid_version = 'v0.0'
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
    version = 'v1.0'
    invalid_version = 'v0.0'
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
