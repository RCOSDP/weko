import json
import pytest
from mock import patch
from invenio_accounts.testutils import login_user_via_session


user_results1 = [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
]

@pytest.mark.parametrize('id, status_code', user_results1)
def test_check_restricted_content_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    res = client_api.post("/api/check_restricted_content",
                      data=json.dumps({"record_ids":[]}),
                      content_type="application/json")
    assert res.status_code == status_code


def test_check_restricted_content_guest(client_api, users):
    res = client_api.post("/api/check_restricted_content",
                      data=json.dumps({"record_ids":[]}),
                      content_type="application/json")
    assert res.status_code == 200


user_results2 = [
    (0, 403),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
]


@pytest.mark.parametrize('id, status_code', user_results2)
def test_prepare_edit_item_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    res = client_api.post("/api/prepare_edit_item",
                          data=json.dumps({}),
                          content_type="application/json")
    assert res.status_code == status_code


def test_prepare_edit_item_guest(client_api, users):
    res = client_api.post("/api/prepare_edit_item",
                          data=json.dumps({}),
                          content_type="application/json")
    assert res.status_code == 302


@pytest.mark.parametrize('id, status_code', user_results2)
def test_validate_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    with patch("weko_items_ui.views.validate_form_input_data",return_value=""):
        res = client_api.post("/api/validate",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == status_code


def test_validate_guest(client_api, users):
    with patch("weko_items_ui.views.validate_form_input_data",return_value=""):
        res = client_api.post("/api/validate",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 302


@pytest.mark.parametrize('id, status_code', user_results2)
def test_validate_user_email_and_index_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    with patch("weko_items_ui.views.validate_user_mail_and_index",return_value=""):
        res = client_api.post("/api/validate_email_and_index",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == status_code


def test_validate_user_email_and_index_guest(client_api, users):
    with patch("weko_items_ui.views.validate_user_mail_and_index",return_value=""):
        res = client_api.post("/api/validate_email_and_index",
                          data=json.dumps({}),
                          content_type="application/json")
        assert res.status_code == 302


@pytest.mark.parametrize('id, status_code', user_results2)
def test_validate_user_info_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    res = client_api.post("/api/validate_user_info",
                      data=json.dumps({"username":"", "email":""}),
                      content_type="application/json")
    assert res.status_code == status_code


def test_validate_user_info_guest(client_api, users):
    res = client_api.post("/api/validate_user_info",
                      data=json.dumps({"username":"", "email":""}),
                      content_type="application/json")
    assert res.status_code == 302
