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

"""WEKO3 pytest docstring."""

import os

import pytest
from helpers import insert_user_to_db, login_user_via_session
from mock import mock
from pytest_invenio.fixtures import app, database, es_clear
from weko_admin.models import SiteInfo
from weko_admin.views import get_site_info


def test_get_site_info(app, database, client, es_clear):
    """Test get site info."""
    insert_user_to_db(database)
    login_user_via_session(client, 1)

    site_info = SiteInfo(
        copy_right=1,
        description="",
        notify=[
            {
                'language': 'en',
                'notify_name': 'test_pytest_notify'
            }
        ],
        site_name=[
            {
                "name": "Test",
                "index": "0",
                "language": "en"
            }
        ]
    )

    expect_result = b'notify":[{"language":"en","notify_name":"' \
        b'test_pytest_notify"}]'
    with mock.patch('weko_admin.views.SiteInfo.get', return_value=site_info):
        with client.session_transaction() as sess:
            sess['language'] = "en"
        res = client.get('/api/admin/get_site_info')
        assert expect_result in res.data
        # assert 1 == 1


def side_effect_json1(*args, **kwargs):
    """Side effect json1."""
    return {
        'activity_id': "A-20200116-00021",
        'auto_set_index_action': True,
        'user_to_check': [
            'email_approval1',
            'email_approval2'
        ],
        'email_approval1': {
            'action_id': 1,
            'mail': "test01@hitachi.com"
        },
        'email_approval2': {
            'action_id': 2,
            'mail': "test02@hitachi.com"
        }
    }


def side_effect_email_valid(*args, **kwargs):
    """Side effect email valid."""
    return {
        'username': 'username',
        'user_id': '123',
        'email': 'test01@hitachi.com'
    }


def side_effect_email_valid1(*args, **kwargs):
    """Side effect email valid1."""
    return {
        'username': 'username',
        'user_id': '1',
        'email': 'test01@hitachi.com'
    }


def test_validate_user_email(client, database, app):
    """Test validate user email."""
    m = mock.MagicMock()
    m.get_json.side_effect = side_effect_json1
    m.headers = {'Content-Type': 'application/json'}

    current_user = mock.MagicMock()
    current_user.id = 1
    with mock.patch(
        'weko_items_ui.utils.get_user_info_by_email',
        side_effect=side_effect_email_valid), mock.patch(
        'weko_items_ui.utils.get_index_id',
        return_value="1"
    ),  mock.patch(
        'weko_items_ui.utils.current_user',
        current_user
    ), mock.patch(
        'weko_items_ui.views.request',
        m
    ):
        res = client.post('/api/items/validate_email_and_index')

    with mock.patch(
        'weko_items_ui.utils.get_user_info_by_email',
        side_effect=side_effect_email_valid),  mock.patch(
        'weko_items_ui.utils.current_user',
        current_user
    ), mock.patch(
        'weko_items_ui.views.request',
        m
    ):
        res = client.post('/api/items/validate_email_and_index')

    with mock.patch(
        'weko_items_ui.utils.get_user_info_by_email',
        side_effect=side_effect_email_valid
    ),  mock.patch(
        'weko_items_ui.utils.current_user',
        current_user
    ), mock.patch(
        'weko_items_ui.views.request',
        m
    ):
        res = client.post('/api/items/validate_email_and_index')
        assert res.status_code

    with mock.patch(
        'weko_items_ui.utils.get_user_info_by_email',
        side_effect=side_effect_email_valid1
    ), mock.patch(
        'weko_items_ui.utils.current_user',
        current_user
    ), mock.patch(
        'weko_items_ui.views.request',
        m
    ):
        res = client.post('/api/items/validate_email_and_index')
        assert res.status_code

    with mock.patch(
        'weko_items_ui.utils.get_user_info_by_email',
        side_effect=side_effect_email_valid1
    ), mock.patch(
        'weko_items_ui.views.request',
        m
    ):
        res = client.post('/api/items/validate_email_and_index')
        assert res.status_code

    with mock.patch(
        'weko_items_ui.utils.get_index_id',
        return_value="1"
    ),  mock.patch(
        'weko_items_ui.utils.current_user',
        current_user
    ), mock.patch(
        'weko_items_ui.views.request',
        m
    ):
        res = client.post('/api/items/validate_email_and_index')
        assert res.status_code

    requet1 = mock.MagicMock()
    requet1.get_json.side_effect = side_effect_json1
    # Does not contain header,return error
    with mock.patch(
        'weko_items_ui.utils.get_user_info_by_email',
        side_effect=side_effect_email_valid
    ), mock.patch(
        'weko_items_ui.utils.get_index_id',
        return_value="1"
    ),  mock.patch(
        'weko_items_ui.utils.current_user',
        current_user
    ), mock.patch(
        'weko_items_ui.views.request',
        requet1
    ):
        res = client.post('/api/api/items/validate_email_and_index')
        assert res.status_code


def prefix(name, data):
    """Prefix all keys with value."""
    data = {"{0}-{1}".format(name, k): v for (k, v) in data.items()}
    data['submit'] = name
    return data


def test_get_profile_info(app, database, client):
    """Test get profile info."""
    res = client.get('/api/get_profile_info/')
    assert res.status_code == 200
    login_user_via_session(client, 1)
    data = prefix('profile', dict(
        username='Thanh',
        formdata=None,
        timezone="Etc/GMT-9",
        language="ja",
        email="info@inveniosoftware.org",
        email_repeat="info@inveniosoftware.org",
        university="University 02",
        department="Affiliation department 02",
        position="Professor",
        phoneNumber="0909090902",
        instituteName="Affiliation institute 01",
        institutePosition="Member",
        instituteName2="Affiliation institute 02",
        institutePosition2="Member",
        instituteName3="Affiliation institute 03",
        institutePosition3="Member",
        instituteName4="Affiliation institute 04",
        institutePosition4="Member",
        instituteName5="Affiliation institute 05",
        institutePosition5="Member",
        prefix='profile',
        ))
    res = client.post('/account/settings/profile/', data=data)
    from weko_user_profiles.utils import get_user_profile_info
    with app.app_context():
        data_expect = get_user_profile_info(1)
        assert data_expect.get('subitem_user_name') == 'admin'
        assert data_expect.get('subitem_mail_address') == \
            'info@inveniosoftware.org'
        assert data_expect.get('subitem_position') == 'Professor'
