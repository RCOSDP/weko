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

from flask import json
from mock import patch


# .tox/c1/bin/pytest --cov=weko_records_ui tests/test_rest.py::test_NeedRestrictedAccess_get_v1 -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records-ui/.tox/c1/tmp
def test_NeedRestrictedAccess_get_v1(app, client, db, make_record_need_restricted_access, oauth_headers, users):
    """Test NeedRestrictedAccess.get_v1 method."""

    version = 'v1.0'
    invalid_version = 'v0.0'
    headers_sysadmin = oauth_headers[0]     # OAuth token : sysadmin
    headers_contributor = oauth_headers[1]  # OAuth token : contributor
    headers_user = oauth_headers[2]         # OAuth token : user
    headers_not_login = oauth_headers[3]    # No OAuth token : not login

    # Invalid version : 400 error
    pid_value = 11
    res = client.get(
        f'/{invalid_version}/records/{pid_value}/need-restricted-access',
        content_type='application/json',
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
        content_type='application/json',
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
        content_type='application/json',
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
        content_type='application/json',
        headers=headers_user,
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data[0]['need_restricted_access'] == False

    # Login user is administrator : result is False
    pid_value = 12
    res = client.get(
        f'/{version}/records/{pid_value}/need-restricted-access',
        content_type='application/json',
        headers=headers_sysadmin,
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data[0]['need_restricted_access'] == False

    # Login user is register user : result is False
    pid_value = 12
    res = client.get(
        f'/{version}/records/{pid_value}/need-restricted-access',
        content_type='application/json',
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
            content_type='application/json',
            headers=headers_contributor,
        )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data[0]['need_restricted_access'] == False

    # Restricted access is not approval : result is True
    pid_value = 14
    res = client.get(
        f'/{version}/records/{pid_value}/need-restricted-access',
        content_type='application/json',
        headers=headers_contributor,
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data[0]['need_restricted_access'] == True

    # Restricted access is not applied : result is True
    pid_value = 15
    res = client.get(
        f'/{version}/records/{pid_value}/need-restricted-access',
        content_type='application/json',
        headers=headers_contributor,
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data[0]['need_restricted_access'] == True

    # User who can't apply : result is True
    pid_value = 15
    res = client.get(
        f'/{version}/records/{pid_value}/need-restricted-access',
        content_type='application/json',
        headers=headers_user,
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data[0]['need_restricted_access'] == True

    # Not login : result is True
    pid_value = 15
    res = client.get(
        f'/{version}/records/{pid_value}/need-restricted-access',
        content_type='application/json',
        headers=headers_not_login,
    )
    res_data = json.loads(res.get_data())
    assert res.status_code == 200
    assert res_data[0]['need_restricted_access'] == True
