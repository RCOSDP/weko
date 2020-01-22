from pytest_invenio.fixtures import database, app, es_clear
from mock import mock
import pytest
import os
from helpers import login_user_via_session, insert_user_to_db
from weko_admin.models import SiteInfo


#Use for mock data 
def mock_site_info(*args, **keywargs):

    ##Set data mock
    from weko_admin.models import SiteInfo
    data_test_site_info = SiteInfo(id=1, notify = [
        {
            "language": "en",
            "notify_name": "Log-in Instructions English"
        },
        {
            "language": "ja",
            "notify_name": "This is Japan messasge"
        }
    ],
    favicon = "favicon.ico")
    return data_test_site_info

@mock.patch(
    'weko_theme.views.SiteInfo.get',
    side_effect=mock_site_info)
def test_theme_get_site_info(app,client, es_clear):

    res = client.get("/login/")
    message = b'Log-in Instructions English'
    print('=============================')
    print('====', res.data)
    print('=============================')
    assert message in res.data
    favicon = b'favicon.ico'
    assert favicon in res.data

    ##Case 1: Check language set Japanese
    with client.session_transaction() as sess:
        sess['language'] = "ja"
    
    message1 = b'This is Japan messasge'
    res1 = client.get("/login/")
    assert message1 in res1.data
    assert favicon in res1.data

    ##Case 2: Check language not set in notify but 
    with client.session_transaction() as sess:
        sess['language'] = 'vi'
    message3 = b'Log-in Instructions English'
    res3 = client.get("/login/")
    assert message3 in res3.data

    ##Case 3: Check language set english
    with client.session_transaction() as sess:
        sess['language'] = 'en'
    message2 = b'Log-in Instructions English'
    res2 = client.get("/login/")
    assert message2 in res2.data
