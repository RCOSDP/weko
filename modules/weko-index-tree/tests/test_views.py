import json
import pytest
from mock import patch
from weko_index_tree.views import set_expand, get_rss_data, create_index
from invenio_accounts.testutils import login_user_via_session


user_results = [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
]


# def get_rss_data():


# def set_expand():
@pytest.mark.parametrize('id, status_code', user_results)
def test_set_expand_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    res = client_api.post("/api/indextree/set_expand",
                          data=json.dumps({}),
                          content_type="application/json")
    assert res.status_code == status_code


def test_set_expand_guest(client_api, users):
    res = client_api.post("/api/indextree/set_expand",
                          data=json.dumps({}),
                          content_type="application/json")
    assert res.status_code == 302


# def create_index():
def test_create_index():
    """Create index by api."""
    try:
        data = request.get_json(force=True)
        if data:
            pid = data.get("parent_id", 0)
            index_info = data.get("index_info", {})
            index_id = int(time.time() * 1000)
            create_data = {
                "id": index_id,
                "value": "New Index"
            }
            update_data = {}
            if index_info:
                update_data.update({
                    "index_name":
                    index_info.get("index_name", "New Index")
                })
                update_data.update({
                    "index_name_english":
                    index_info.get("index_name_english", "New Index")
                })
                update_data.update({
                    "comment": index_info.get("comment", "")
                })
                update_data.update({
                    "public_state": index_info.get("public_state", False)
                })
                update_data.update({
                    "harvest_public_state":
                    index_info.get("harvest_public_state", True)
                })
                index = None
                with current_app.test_request_context() as ctx:
                    Indexes.create(pid, create_data)
                    index = Indexes.update(index_id, **update_data)
                return make_response(json.dumps(dict(index)), 201)
            else:
                return make_response("index_info can not be null.", 400)
        else:
            return make_response("No data to create.", 400)
    except Exception as e:
        current_app.logger.error(e)
        return make_response(str(e), 400)



