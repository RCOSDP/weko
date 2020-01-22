from pytest_invenio.fixtures import database, app, es_clear
from mock import mock
from weko_admin.utils import get_notify_for_current_language, format_site_info_data, validation_site_info
from weko_admin.models import SiteInfo
from weko_admin.views import get_site_info
import pytest
import os
from helpers import login_user_via_session, insert_user_to_db


def test_get_notify_for_current_language(app, database, es_clear):
    ## Prepare mock data
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
    site_info = {
        'copy_right': "",
        'description': "",
        'favicon': "https://community.repo.nii.ac.jp/images/common/favicon.ico",
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
    site_info = {
        'copy_right': "",
        'description': "",
        'favicon': "https://community.repo.nii.ac.jp/images/common/favicon.ico",
        'favicon_name': "JAIRO Cloud icon",
        'notify': [
            {
                'language': "en",
                'notify_name': "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6\
                    a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6"
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
        'the_limit_is_200_characters' : 'The limit is 200 characters'
    }

    from weko_admin.models import AdminLangSettings

    list_lang_admin = [
        {"lang_code":"en", "lang_name":"English", "is_registered":True, "is_active":True}
    ]

    with mock.patch('weko_admin.utils.get_admin_lang_setting', return_value=list_lang_admin):
        actual_result = validation_site_info(site_info)
        assert actual_result['error'] == expect_result['the_limit_is_200_characters']


