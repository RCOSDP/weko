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


# def index(item_type_id=0):
# def iframe_index(item_type_id=0):
# def iframe_save_model():
# def iframe_success():
# def iframe_error():
# def get_json_schema(item_type_id=0, activity_id=""):
# def get_schema_form(item_type_id=0, activity_id=''):
# def items_index(pid_value='0'):
# def iframe_items_index(pid_value='0'):
# def default_view_method(pid, record, template=None):
# def to_links_js(pid):
# def index_upload():
# def get_search_data(data_type=''):
# def validate_user_email_and_index():
# def validate_user_info():
# def get_user_info(owner, shared_user_id):
# def get_current_login_user_id():
# def prepare_edit_item():
# def ranking():
# def check_ranking_show():
# def check_restricted_content():
# def validate_bibtex_export():
# def export():
# def validate():
# def check_validation_error_msg(activity_id):
# def corresponding_activity_list():
# def get_authors_prefix_settings():
# def get_authors_affiliation_settings():
# def session_validate():
# def check_record_doi(pid_value='0'):
# def check_record_doi_indexes(pid_value='0'):