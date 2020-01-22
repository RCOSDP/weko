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


def mock_site_info(*args, **keywargs):
    """Use for mock data Set data mock."""
    from weko_admin.models import SiteInfo
    data_test_site_info = SiteInfo(
        id=1,
        notify=[
            {
                "language": "en",
                "notify_name": "Log-in Instructions English"
            },
            {
                "language": "ja",
                "notify_name": "This is Japan messasge"
            }
        ],
        favicon="favicon.ico")
    return data_test_site_info


@mock.patch(
    'weko_theme.views.SiteInfo.get',
    side_effect=mock_site_info
)
def test_theme_get_site_info(app, client, es_clear):
    """Test theme get site info."""
    res = client.get("/login/")
    message = b'Log-in Instructions English'
    print('=============================')
    print('====', res.data)
    print('=============================')
    assert message in res.data
    favicon = b'favicon.ico'
    assert favicon in res.data

    # Case 1: Check language set Japanese
    with client.session_transaction() as sess:
        sess['language'] = "ja"

    message1 = b'This is Japan messasge'
    res1 = client.get("/login/")
    assert message1 in res1.data
    assert favicon in res1.data

    # Case 2: Check language not set in notify but
    with client.session_transaction() as sess:
        sess['language'] = 'vi'
    message3 = b'Log-in Instructions English'
    res3 = client.get("/login/")
    assert message3 in res3.data

    # Case 3: Check language set english
    with client.session_transaction() as sess:
        sess['language'] = 'en'
    message2 = b'Log-in Instructions English'
    res2 = client.get("/login/")
    assert message2 in res2.data
