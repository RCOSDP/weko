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
from weko_admin.utils import format_site_info_data, \
    get_notify_for_current_language, validation_site_info
from weko_admin.views import get_site_info


def test_get_notify_for_current_language(app, database, es_clear):
    """Prepare mock data."""
    notify = [
        {
            "language": "ja",
            "notify_name": "123"
        }
    ]
    m = mock.MagicMock()
    m.language = 'ja'
    with mock.patch('weko_admin.utils.current_i18n', m):
        assert get_notify_for_current_language(notify) == '123'
        notify2 = [
            {
                "language": "en",
                "notify_name": "123"
            }
        ]
        assert get_notify_for_current_language(notify2) == '123'
        notify3 = [
            {
                "language": "vn",
                "notify_name": "123"
            }
        ]
        assert get_notify_for_current_language(notify3) == ''
        assert get_notify_for_current_language(None).__eq__('')


def test_format_site_info_data(app, database, es_clear):
    """Test format site info data."""
    site_info = {
        'copy_right': "",
        'description': "",
        'favicon':
            "https://community.repo.nii.ac.jp/images/common/favicon.ico",
        'favicon_name': "JAIRO Cloud icon",
        'notify': [
            {
                'language': "en",
                'notify_name': ""
            },
            {
                'language': "ja",
                'notify_name': "サインアップの注意書き　ｊａｐａｎｅｓｅ"
            }
        ],
        'keyword': "abc"
    }
    expect_result = {
        'notify': [
            {
                'language': "en",
                'notify_name': ""
            },
            {
                'language': "ja",
                'notify_name': "サインアップの注意書き　ｊａｐａｎｅｓｅ"
            }
        ],
    }
    actual_result = format_site_info_data(site_info)
    assert expect_result['notify'] == actual_result['notify']


def test_validation_site_info(app, database, es_clear):
    """Test validation site info."""
    site_info = {
        'copy_right': "",
        'description': "",
        'favicon':
            "https://community.repo.nii.ac.jp/images/common/favicon.ico",
        'favicon_name': "JAIRO Cloud icon",
        'notify': [
            {
                'language': "en",
                'notify_name':
                    "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f"
                    "6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6\
                    a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e"
                    "5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6"
            }
        ],
        'site_name': [
            {
                "name": "Test",
                "index": "0",
                "language": "en"
            }
        ]
    }
    expect_result = {
        'the_limit_is_200_characters': 'The limit is 200 characters'
    }

    from weko_admin.models import AdminLangSettings

    list_lang_admin = [
        {
            "lang_code": "en",
            "lang_name": "English",
            "is_registered": True,
            "is_active": True
        }
    ]

    with mock.patch(
        'weko_admin.utils.get_admin_lang_setting',
        return_value=list_lang_admin
    ):
        actual_result = validation_site_info(site_info)
        assert actual_result['error'] == expect_result[
            'the_limit_is_200_characters'
        ]
