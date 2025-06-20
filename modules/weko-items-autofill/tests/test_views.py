
import pytest
from mock import patch
import json
from flask import make_response
from invenio_accounts.testutils import login_user_via_session
from weko_admin.models import ApiCertificate
from weko_records.models import ItemTypeName

from weko_items_autofill.views import dbsession_clean

user_results = [
    (0,True),
    (1,True),
    (2,True),
    (3,True),
    (4,True),
    (5,True),
    (7,True)
]

def assert_role(response, is_permission,status_code=403):
    """Validate appropriate status code by role

    Args:
        response (Response): response
        is_permission (bool): Presence or absence of access rights
        status_code (int, optional): Status code for lack of access. Default to 403
    """
    if is_permission:
        assert response.status_code != status_code
    else:
        assert response.status_code == status_code


# def index():
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_utils.py::test_get_specific_key_path -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_index(client,users,mocker):
    mock_render = mocker.patch("weko_items_autofill.views.render_template",return_value=make_response())
    res = client.get("/autofill/")
    mock_render.assert_called_with(
        "weko_items_autofill/index.html",
        module_name="WEKO-Items-Autofill"
    )


# def get_selection_option():
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_views.py::test_get_selection_option_acl_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', user_results)
def test_get_selection_option_acl_login(client_api,users,index,is_permission):
    url = "/autofill/select_options"
    login_user_via_session(client=client_api,email=users[index]["email"])
    res = client_api.get(url)
    assert res.status_code != 403

# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_views.py::test_get_selection_option_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_selection_option_acl_guest(client_api,users):
    url = "/autofill/select_options"
    res = client_api.get(url)
    assert res.status_code == 302
    with client_api.session_transaction() as session:
        session["guest_token"]="test_token"
    res = client_api.get(url)
    assert res.status_code != 302

# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_views.py::test_get_selection_option -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_selection_option(client_api,users):
    url = "/autofill/select_options"
    login_user_via_session(client=client_api,email=users[0]["email"])
    test = {"options":[
        {'value': 'Default', 'text': 'Select the ID'},
        {'value': 'CrossRef', 'text': 'CrossRef'},
        {'value': 'CiNii', 'text': 'CiNii'},
        {'value': 'WEKOID', 'text': 'WEKOID'}
    ]
    }
    res = client_api.get(url)
    assert json.loads(res.data) == test


# def get_title_pubdate_id(item_type_id=0):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_views.py::test_get_title_pubdate_id_acl_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', user_results)
def test_get_title_pubdate_id_acl_login(client_api,users,index,is_permission,mocker):
    url = "/autofill/get_title_pubdate_id/1"
    login_user_via_session(client=client_api,email=users[index]["email"])
    data = {"title":{"title_parent_key":"test_item1","title_value_lst_key":["test1_subitem1"],"title_lang_lst_key":["test1_subitem2"]},"pubDate":""}
    mocker.patch("weko_items_autofill.views.get_title_pubdate_path",return_value=data)
    res = client_api.get(url)
    assert_role(res,is_permission)

# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_views.py::test_get_title_pubdate_id_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_title_pubdate_id_acl_guest(client_api,users,mocker):
    url = "/autofill/get_title_pubdate_id/1"
    data = {"title":{"title_parent_key":"test_item1","title_value_lst_key":["test1_subitem1"],"title_lang_lst_key":["test1_subitem2"]},"pubDate":""}
    mocker.patch("weko_items_autofill.views.get_title_pubdate_path",return_value=data)
    res = client_api.get(url)
    assert res.status_code == 302

    with client_api.session_transaction() as session:
        session["guest_token"]="test_token"
    res = client_api.get(url)
    assert res.status_code != 302

# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_views.py::test_get_title_pubdate_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_title_pubdate_id(client_api,users,mocker):
    login_user_via_session(client=client_api,email=users[0]["email"])
    data = {"title":{"title_parent_key":"test_item1","title_value_lst_key":["test1_subitem1"],"title_lang_lst_key":["test1_subitem2"]},"pubDate":""}
    mocker.patch("weko_items_autofill.views.get_title_pubdate_path",return_value=data)
    url = "/autofill/get_title_pubdate_id/1"
    res = client_api.get(url)
    assert json.loads(res.data) == data


# def get_auto_fill_record_data():
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_views.py::test_get_auto_fill_record_data_acl_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', user_results)
def test_get_auto_fill_record_data_acl_login(client_api, users, index, is_permission):
    login_user_via_session(client=client_api, email=users[index]['email'])
    res = client_api.post('/autofill/get_auto_fill_record_data',
                      data=json.dumps({}),
                      content_type='application/json')
    assert_role(res,is_permission)

# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_views.py::test_get_auto_fill_record_data_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_auto_fill_record_data_acl_guest(client_api, users):
    url = '/autofill/get_auto_fill_record_data'
    res = client_api.post(url,data=json.dumps({}),content_type="application/json")
    assert res.status_code == 302
    with client_api.session_transaction() as session:
        session["guest_token"]="test_token"
    res = client_api.post(url,
                          data=json.dumps({}),
                          content_type='application/json')
    assert res.status_code != 302

# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_views.py::test_get_auto_fill_record_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_auto_fill_record_data(client_api,db,users,mocker):
    login_user_via_session(client=client_api, email=users[0]['email'])
    url = '/autofill/get_auto_fill_record_data'
    api_certificate = ApiCertificate(
        api_code="crf",
        api_name="CrossRef",
        cert_data="test_crf@test.org"
    )
    db.session.add(api_certificate)
    db.session.commit()
    # header error
    res = client_api.post(url,data="test_value",content_type="plain/text")
    assert res.status_code == 200
    assert json.loads(res.data) == {"result":"","items":"","error":"Header Error"}

    data = {
        "api_type":"",
        "search_data":"",
        "item_type_id":""
    }

    # not exist api_type
    data = {
        "api_type":"not_exist_type",
        "search_data":"",
        "item_type_id":""
    }
    res = client_api.post(url,json=data)
    assert res.status_code == 200
    assert json.loads(res.data) == {"result":"","items":"","error":"not_exist_type is NOT support autofill feature."}

    # api_type is CrossRef

    mock_crossref_record = mocker.patch("weko_items_autofill.views.get_crossref_record_data",return_value="return_crossref_record_data")
    data = {
        "api_type":"CrossRef",
        "search_data":"data",
        "item_type_id":"1"
    }
    res = client_api.post(url,json=data)
    assert res.status_code == 200
    assert json.loads(res.data) == {"result":"return_crossref_record_data","items":"","error":""}
    mock_crossref_record.assert_called_with("test_crf@test.org","data","1")

    # api_type is CiNii
    data = {
        "api_type":"CiNii",
        "search_data":"data",
        "item_type_id":"1"
    }
    mock_cinii_record = mocker.patch("weko_items_autofill.views.get_cinii_record_data",return_value="return_cinii_record_data")
    res = client_api.post(url,json=data)
    assert res.status_code == 200
    assert json.loads(res.data) == {"result":"return_cinii_record_data","items":"","error":""}
    mock_cinii_record.assert_called_with("data","1")

    # api_type is WEKOID
    data = {
        "api_type":"WEKOID",
        "search_data":"data",
        "item_type_id":"1"
    }
    mock_weko_record = mocker.patch("weko_items_autofill.views.get_wekoid_record_data",return_value="return_weko_record_data")
    res = client_api.post(url,json=data)
    assert res.status_code == 200
    assert json.loads(res.data) == {"result":"return_weko_record_data","items":"","error":""}
    mock_weko_record.assert_called_with("data","1")

    # raise Exception
    mocker.patch("weko_items_autofill.views.get_wekoid_record_data",side_effect=Exception("test_error"))
    res = client_api.post(url,json=data)
    assert res.status_code == 200
    assert json.loads(res.data) == {"result":"","items":"","error":"test_error"}


# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_views.py::test_get_auto_fill_record_data_doi -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_auto_fill_record_data_doi(client_api,db,users,mocker):
    login_user_via_session(client=client_api, email=users[0]['email'])
    url = '/autofill/get_auto_fill_record_data'
    api_certificate = ApiCertificate(
        api_code="crf",
        api_name="CrossRef",
        cert_data="test_crf@test.org"
    )
    db.session.add(api_certificate)
    db.session.commit()

    # api_type is DOI
    mock_doi_record = mocker.patch("weko_items_autofill.views.get_doi_record_data",return_value="return_doi_record_data")
    data = {
        "api_type":"DOI",
        "search_data":"data",
        "item_type_id":"1"
    }
    res = client_api.post(url,json=data)
    assert res.status_code == 200
    assert json.loads(res.data) == {"result":"return_doi_record_data","items":"","error":""}
    mock_doi_record.assert_called_with("data","1","")

    # api_type is CrossRef
    mock_crossref_record = mocker.patch("weko_items_autofill.views.get_crossref_record_data",return_value="return_crossref_record_data")
    data = {
        "api_type":"CrossRef",
        "search_data":"data",
        "item_type_id":"1"
    }
    res = client_api.post(url,json=data)
    assert res.status_code == 200
    assert json.loads(res.data) == {"result":"return_crossref_record_data","items":"","error":""}
    mock_crossref_record.assert_called_with("test_crf@test.org","data","1")

    # api_type not exist
    data = {
        "api_type":"XXX",
        "search_data":"data",
        "item_type_id":"1"
    }
    res = client_api.post(url,json=data)
    assert res.status_code == 200
    assert json.loads(res.data) == {"result":"","items":"","error":"XXX is NOT support autofill feature."}


# def get_item_auto_fill_journal(activity_id):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_views.py::test_get_item_auto_fill_journal_acl_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
@pytest.mark.parametrize('index, is_permission', user_results)
def test_get_item_auto_fill_journal_acl_login(client_api,users,index,is_permission,mocker):
    url = "/autofill/get_auto_fill_journal/1"
    login_user_via_session(client=client_api,email=users[index]["email"])
    data = {"key":"value"}
    mocker.patch("weko_items_autofill.views.get_workflow_journal",return_value=data)
    res = client_api.get(url)
    assert_role(res,is_permission)

# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_views.py::test_get_item_auto_fill_journal_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_item_auto_fill_journal_acl_guest(client_api,users,mocker):
    url = "/autofill/get_auto_fill_journal/1"
    data = {"key":"value"}
    mocker.patch("weko_items_autofill.views.get_workflow_journal",return_value=data)
    res = client_api.get(url)
    assert res.status_code == 302
    with client_api.session_transaction() as session:
        session["guest_token"]="test_token"
    res = client_api.get(url)
    assert res.status_code != 302

# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_views.py::test_get_title_pubdate_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_get_item_auto_fill_journal(client_api,users,mocker):
    login_user_via_session(client=client_api,email=users[0]["email"])
    data = {"key":"value"}
    mocker.patch("weko_items_autofill.views.get_workflow_journal",return_value=data)
    url = "/autofill/get_auto_fill_journal/1"
    res = client_api.get(url)
    assert json.loads(res.data) == {"result":{"key":"value"}}

# def dbsession_clean(exception):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_views.py::test_dbsession_clean -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
def test_dbsession_clean(app, db):
    # exist exception
    itemtype_name1 = ItemTypeName(id=1,name="テスト1",has_site_license=True, is_active=True)
    db.session.add(itemtype_name1)
    dbsession_clean(None)
    assert ItemTypeName.query.filter_by(id=1).first().name == "テスト1"

    # raise Exception
    itemtype_name2 = ItemTypeName(id=2,name="テスト2",has_site_license=True, is_active=True)
    db.session.add(itemtype_name2)
    with patch("weko_items_autofill.views.db.session.commit",side_effect=Exception):
        dbsession_clean(None)
        assert ItemTypeName.query.filter_by(id=2).first() is None

    # not exist exception
    itemtype_name3 = ItemTypeName(id=3,name="テスト3",has_site_license=True, is_active=True)
    db.session.add(itemtype_name3)
    dbsession_clean(Exception)
    assert ItemTypeName.query.filter_by(id=3).first() is None
