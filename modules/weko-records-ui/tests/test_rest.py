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
from unittest.mock import MagicMock
from flask import json, url_for
from mock import patch
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.http import generate_etag

def url(root, kwargs = {}):
    args = ["{key}={value}".format(key = key, value = value) for key, value in kwargs.items()]
    url = "{root}?{param}".format(root = root, param = "&".join(args)) if kwargs else root
    return url

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_NeedRestrictedAccess_get_v1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_NeedRestrictedAccess_get_v1(app, client, db, make_record_need_restricted_access, oauth_headers, users):
    """Test NeedRestrictedAccess.get_v1 method."""

    version = 'v1'
    invalid_version = 'v0'
    headers_sysadmin = oauth_headers[0]     # OAuth token : sysadmin
    headers_contributor = oauth_headers[1]  # OAuth token : contributor
    headers_user = oauth_headers[2]         # OAuth token : user
    headers_not_login = oauth_headers[3]    # No OAuth token : not login

    # Invalid version : 400 error
    pid_value = 11
    res = client.get(
        f'/{invalid_version}/records/{pid_value}/need-restricted-access',
        headers=headers_sysadmin,
    )
    try:
        json.loads(res.get_data())
    except:
        assert False
    assert res.status_code == 400

    # Invalid pid_value : 404 error
    pid_value = 100
    res = client.get(
        f'/{version}/records/{pid_value}/need-restricted-access',
        headers=headers_sysadmin,
    )
    try:
        json.loads(res.get_data())
    except:
        assert False
    assert res.status_code == 404

    # Activity is not completed : 404 error
    pid_value = 16
    res = client.get(
        f'/{version}/records/{pid_value}/need-restricted-access',
        headers=headers_sysadmin,
    )
    assert res.status_code == 404
    try:
        json.loads(res.get_data())
    except:
        assert False

    # File access is not restricted access : result is False
    pid_value = 11
    res = client.get(
        f'/{version}/records/{pid_value}/need-restricted-access',
        headers=headers_user,
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data[0]['need_restricted_access'] == False

    # Login user is administrator : result is False
    pid_value = 12
    res = client.get(
        f'/{version}/records/{pid_value}/need-restricted-access',
        headers=headers_sysadmin,
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data[0]['need_restricted_access'] == False

    # Login user is register user : result is False
    pid_value = 12
    res = client.get(
        f'/{version}/records/{pid_value}/need-restricted-access',
        headers=headers_contributor,
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data[0]['need_restricted_access'] == False

    # Restricted access is approval : result is False
    pid_value = 13
    onetime_download = make_record_need_restricted_access['FileOnetimeDownload']['13']
    # find_downloadable_only function can not execute on test.
    with patch('weko_records_ui.models.FileOnetimeDownload.find_downloadable_only', return_value=[onetime_download]):
        res = client.get(
            f'/{version}/records/{pid_value}/need-restricted-access',
            headers=headers_contributor,
        )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data[0]['need_restricted_access'] == False

    # Restricted access is not approval : result is True
    pid_value = 14
    res = client.get(
        f'/{version}/records/{pid_value}/need-restricted-access',
        headers=headers_contributor,
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data[0]['need_restricted_access'] == True

    # Restricted access is not applied : result is True
    pid_value = 15
    res = client.get(
        f'/{version}/records/{pid_value}/need-restricted-access',
        headers=headers_contributor,
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data[0]['need_restricted_access'] == True

    # User who can't apply : result is True
    pid_value = 15
    res = client.get(
        f'/{version}/records/{pid_value}/need-restricted-access',
        headers=headers_user,
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data[0]['need_restricted_access'] == True

    # Not login : result is True
    pid_value = 15
    res = client.get(
        f'/{version}/records/{pid_value}/need-restricted-access',
        headers=headers_not_login,
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data[0]['need_restricted_access'] == True


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_GetFileTerms_get_v1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_GetFileTerms_get_v1(app, client, db, make_record_need_restricted_access, oauth_headers, users):
    """Test GetFileTerms.get_v1 method."""

    version = 'v1'
    invalid_version = 'v0'
    headers_sysadmin = oauth_headers[4]                 # OAuth token : sysadmin (activity_scope)
    headers_contributor = oauth_headers[5]              # OAuth token : contributor (activity_scope)
    headers_user = oauth_headers[6]                     # OAuth token : user (activity_scope)
    headers_not_login = oauth_headers[3]                # No OAuth token : not login
    headers_user_no_activity_scope = oauth_headers[2]   # OAuth token : user (item_scope)

    # Invalid version : 400 error
    pid_value = 11
    file_name = "dummy.txt"
    res = client.get(
        f'/{invalid_version}/records/{pid_value}/files/{file_name}/terms',
        headers=headers_sysadmin,
    )
    try:
        json.loads(res.get_data())
    except:
        assert False
    assert res.status_code == 400

    # Invalid scope : 403 error
    pid_value = 12
    file_name = "dummy.txt"
    res = client.get(
        f'/{invalid_version}/records/{pid_value}/files/{file_name}/terms',
        headers=headers_user_no_activity_scope
    )
    try:
        json.loads(res.get_data())
    except:
        assert False
    assert res.status_code == 403

    # Invalid pid_value : 404 error
    pid_value = 100
    file_name = "dummy.txt"
    res = client.get(
        f'/{version}/records/{pid_value}/files/{file_name}/terms',
        headers=headers_sysadmin+[("Accept-Language", "aaa")],
    )
    try:
        json.loads(res.get_data())
    except:
        assert False
    assert res.status_code == 404

    # Record not found : 404 error
    pid_value = 17
    file_name = "dummy.txt"
    res = client.get(
        f'/{version}/records/{pid_value}/files/{file_name}/terms',
        headers=headers_sysadmin+[("Accept-Language", "ja")],
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == 404

    # Invalid file_name : 404 error
    pid_value = 11
    file_name = "invalid.txt"
    res = client.get(
        f'/{version}/records/{pid_value}/files/{file_name}/terms',
        headers=headers_sysadmin,
    )
    try:
        json.loads(res.get_data())
    except:
        assert False
    assert res.status_code == 404

    # Success: 200
    pid_value = 12
    file_name = "dummy.txt"
    terms_content = "利用規約本文"
    etag = generate_etag(f"{file_name}_{terms_content}".encode("utf-8"))
    res = client.get(
        f'/{version}/records/{pid_value}/files/{file_name}/terms',
        headers=headers_sysadmin,
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data['text'] == terms_content
    assert res_data['Etag'] == etag

    # Success (If-None-Match): 304
    pid_value = 12
    file_name = "dummy.txt"
    terms_content = "利用規約本文"
    etag = generate_etag(f"{file_name}_{terms_content}".encode("utf-8"))
    headers_sysadmin_304 = copy.deepcopy(headers_sysadmin)
    headers_sysadmin_304.append(('Accept-Language', 'en'))
    headers_sysadmin_304.append(('If-None-Match', etag))
    res = client.get(
        f'/{version}/records/{pid_value}/files/{file_name}/terms',
        headers=headers_sysadmin_304,
    )
    assert res.status_code == 304

# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_FileApplication_post_v1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_FileApplication_post_v1(app, client, db, workflows_restricted, make_record_need_restricted_access, oauth_headers, users):
    """Test GetFileTerms.post_v1 method."""

    version = 'v1'
    invalid_version = 'v0'
    headers_sysadmin = oauth_headers[4]                 # OAuth token : sysadmin (activity_scope)
    headers_contributor = oauth_headers[5]              # OAuth token : contributor (activity_scope)
    headers_user = oauth_headers[6]                     # OAuth token : user (activity_scope)
    headers_not_login = oauth_headers[3]                # No OAuth token : not login
    headers_user_no_activity_scope = oauth_headers[2]   # OAuth token : user (item_scope)

    # Invalid version : 400 error
    pid_value = 12
    file_name = "dummy.txt"
    res = client.post(
        f'/{invalid_version}/records/{pid_value}/files/{file_name}/application',
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_sysadmin
    )
    try:
        json.loads(res.get_data())
    except:
        assert False
    assert res.status_code == 400

    # No mailaddress (Guest) : 400 error
    pid_value = 12
    file_name = "dummy.txt"
    params = {"mail": None}
    res = client.post(
        url(f'/{version}/records/{pid_value}/files/{file_name}/application', params),
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_not_login
    )
    try:
        json.loads(res.get_data())
    except:
        assert False
    assert res.status_code == 400

    # Invalid mailaddress (Guest) : 400 error
    pid_value = 12
    file_name = "dummy.txt"
    params = {"mail": "abc"}
    res = client.post(
        url(f'/{version}/records/{pid_value}/files/{file_name}/application', params),
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_not_login
    )
    try:
        json.loads(res.get_data())
    except:
        assert False
    assert res.status_code == 400

    # Invalid token : 400 error
    pid_value = 12
    file_name = "dummy.txt"
    params = {"mail":"guest@example.org", "terms_token": "aaaaa"}
    res = client.post(
        url(f'/{version}/records/{pid_value}/files/{file_name}/application', params),
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_not_login+[("Accept-Language", "aaa")]
    )
    try:
        json.loads(res.get_data())
    except:
        assert False
    assert res.status_code == 400

    # Not set workflow to role : 403 error
    pid_value = 12
    file_name = "dummy.txt"
    terms_content = "利用規約本文"
    etag = generate_etag(f"{file_name}_{terms_content}".encode("utf-8"))
    params = {"terms_token": etag}
    res = client.post(
        url(f'/{version}/records/{pid_value}/files/{file_name}/application', params),
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_user+[("Accept-Language", "ja")]
    )
    try:
        json.loads(res.get_data())
    except:
        assert False
    assert res.status_code == 403

    # Invalid scope : 403 error
    pid_value = 12
    file_name = "dummy.txt"
    res = client.post(
        f'/{version}/records/{pid_value}/files/{file_name}/application',
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_user_no_activity_scope
    )
    try:
        json.loads(res.get_data())
    except:
        assert False
    assert res.status_code == 403

    # Invalid workflow set to role : 404 error
    pid_value = 12
    file_name = "dummy.txt"
    terms_content = "利用規約本文"
    etag = generate_etag(f"{file_name}_{terms_content}".encode("utf-8"))
    params = {"terms_token": etag}
    res = client.post(
        url(f'/{version}/records/{pid_value}/files/{file_name}/application', params),
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_sysadmin
    )
    try:
        json.loads(res.get_data())
    except:
        assert False
    assert res.status_code == 404

    # pid not found : 404 error
    pid_value = 100
    file_name = "dummy.txt"
    terms_content = "利用規約本文"
    etag = generate_etag(f"{file_name}_{terms_content}".encode("utf-8"))
    params = {"terms_token": etag}
    res = client.post(
        url(f'/{version}/records/{pid_value}/files/{file_name}/application', params),
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_contributor
    )
    try:
        json.loads(res.get_data())
    except:
        assert False
    assert res.status_code == 404

    # Record not found : 404 error
    pid_value = 12
    file_name = "dummy.txt"
    terms_content = "利用規約本文"
    etag = generate_etag(f"{file_name}_{terms_content}".encode("utf-8"))
    params = {"terms_token": etag}
    with patch('weko_records_ui.rest.WekoRecord.get_record', return_value=None): 
        res = client.post(
            url(f'/{version}/records/{pid_value}/files/{file_name}/application', params),
            data=json.dumps(None),
            content_type='application/json',
            headers=headers_contributor
        )
    try:
        json.loads(res.get_data())
    except:
        assert False
    assert res.status_code == 404

    # Invalid file name : 404 error
    pid_value = 12
    file_name = "Invalid.txt"
    terms_content = "利用規約本文"
    etag = generate_etag(f"{file_name}_{terms_content}".encode("utf-8"))
    params = {"terms_token": etag}
    res = client.post(
        url(f'/{version}/records/{pid_value}/files/{file_name}/application', params),
        data=json.dumps(None),
        content_type='application/json',
        headers=headers_contributor
    )
    try:
        json.loads(res.get_data())
    except:
        assert False
    assert res.status_code == 404

    # Server error(init_activity failed): 500
    pid_value = 12
    file_name = "dummy.txt"
    terms_content = "利用規約本文"
    etag = generate_etag(f"{file_name}_{terms_content}".encode("utf-8"))
    params = {"terms_token": etag}
    with patch('weko_workflow.api.WorkActivity.init_activity', return_value=None):
        res = client.post(
            url(f'/{version}/records/{pid_value}/files/{file_name}/application', params),
            data=json.dumps(None),
            content_type='application/json',
            headers=headers_contributor
        )
    assert res.status_code == 500

    # Server error(SQLAlchemyError): 500
    pid_value = 12
    file_name = "dummy.txt"
    terms_content = "利用規約本文"
    etag = generate_etag(f"{file_name}_{terms_content}".encode("utf-8"))
    params = {"terms_token": etag}
    with patch('weko_workflow.api.WorkActivity.init_activity', side_effect=SQLAlchemyError):
        res = client.post(
            url(f'/{version}/records/{pid_value}/files/{file_name}/application', params),
            data=json.dumps(None),
            content_type='application/json',
            headers=headers_contributor
        )
    assert res.status_code == 500

    # Success: 200
    pid_value = 12
    file_name = "dummy.txt"
    terms_content = "利用規約本文"
    etag = generate_etag(f"{file_name}_{terms_content}".encode("utf-8"))
    params = {"terms_token": etag}

    activity_id = "A-00000000-00000"
    activity = MagicMock
    activity.activity_id = activity_id
    itemtype_schema = {}
    with open('tests/data/itemtype_schema_31001.json', 'r') as f:
        itemtype_schema = json.load(f)

    with patch('weko_workflow.api.WorkActivity.init_activity', return_value=activity):
        res = client.post(
            url(f'/{version}/records/{pid_value}/files/{file_name}/application', params),
            data=json.dumps(None),
            content_type='application/json',
            headers=headers_contributor
        )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data['activity_id'] == activity_id
    assert res_data['activity_url'] == url_for('weko_workflow.display_activity', activity_id=activity_id, _external=True, _method='GET').replace("/api", "", 1)
    assert res_data['item_type_schema'] == itemtype_schema

    # Success (Guest): 200
    pid_value = 12
    file_name = "dummy.txt"
    terms_content = "利用規約本文"
    etag = generate_etag(f"{file_name}_{terms_content}".encode("utf-8"))
    params = {"mail":"guest@example.org", "terms_token": etag}

    server_name = app.config.get('SERVER_NAME')
    token = "QS0yMDIzMDgwMy0wMDAwMSAyMDIzLTA4LTAzIGF0c3VzaGkuc3V6dWtpQGl2aXMuY28uanAgMkEyM0RFMEY1ODI0QjU2RQ=="
    activity_url = f"https://{server_name}/api/workflow/activity/guest-user/{file_name}?token={token}"
    activity_id = "A-00000000-1234"
    itemtype_schema = {}
    with open('tests/data/itemtype_schema_31001.json', 'r') as f:
        itemtype_schema = json.load(f)

    with patch('weko_records_ui.rest.init_activity_for_guest_user', return_value=(None, activity_url)):
        res = client.post(
            url(f'/{version}/records/{pid_value}/files/{file_name}/application', params),
            data=json.dumps(None),
            content_type='application/json',
            headers=headers_not_login
        )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data['activity_id'] == activity_id
    assert res_data['activity_url'] == activity_url.replace("/api", "", 1)
    assert res_data['item_type_schema'] == itemtype_schema

    # Success (Guest / exists activity): 200
    pid_value = 12
    file_name = "dummy.txt"
    terms_content = "利用規約本文"
    etag = generate_etag(f"{file_name}_{terms_content}".encode("utf-8"))
    params = {"mail":"guest@example.org", "terms_token": etag}

    server_name = app.config.get('SERVER_NAME')
    token = "QS0yMDIzMDgwMy0wMDAwMSAyMDIzLTA4LTAzIGF0c3VzaGkuc3V6dWtpQGl2aXMuY28uanAgMkEyM0RFMEY1ODI0QjU2RQ=="
    activity_url = f"https://{server_name}/api/workflow/activity/guest-user/{file_name}?token={token}"
    activity_id = "A-00000000-1234"
    activity = MagicMock
    activity.activity_id = activity_id
    itemtype_schema = {}
    with open('tests/data/itemtype_schema_31001.json', 'r') as f:
        itemtype_schema = json.load(f)

    with patch('weko_records_ui.rest.init_activity_for_guest_user', return_value=(activity, activity_url)):
        res = client.post(
            url(f'/{version}/records/{pid_value}/files/{file_name}/application', params),
            data=json.dumps(None),
            content_type='application/json',
            headers=headers_not_login
        )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data['activity_id'] == activity_id
    assert res_data['activity_url'] == activity_url.replace("/api", "", 1)
    assert res_data['item_type_schema'] == itemtype_schema

