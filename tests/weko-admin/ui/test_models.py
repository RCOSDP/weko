from pytest_invenio.fixtures import database, app, es_clear
from mock import mock
from weko_admin.utils import get_notify_for_current_language, format_site_info_data, validation_site_info
from weko_admin.models import SiteInfo

from weko_admin.views import get_site_info
import pytest
import os
from helpers import login_user_via_session, insert_user_to_db

def test_update_site_info(app,database,es_clear):

    site_info = {
        'copy_right': "",
        'description': "",
        'favicon': "https://community.repo.nii.ac.jp/images/common/favicon.ico",
        'favicon_name': "JAIRO Cloud icon",
        'notify': [
            {
                'language': "en",
                'notify_name': "test_pytest_notify"
            }
        ],
        'keyword': "abc"
    }

    expect_result = {
        'notify': [
            {
                'language': "en",
                'notify_name': "test_pytest_notify"
            }
        ],
    }


    # with mock.patch('weko_admin.views.SiteInfo.update', return_value=site_info): 
    except_for = format_site_info_data(site_info)
    # site_instance = SiteInfo()
    actual_result = SiteInfo().update(site_info)
    query_object = SiteInfo.query.filter_by().one_or_none()
    assert query_object.notify == expect_result['notify']
    

