from unittest.mock import patch
from flask import url_for
from invenio_communities.models import Community

import datetime
import pytest
import json

from invenio_accounts.testutils import login_user_via_session
from jinja2.exceptions import TemplateNotFound, TemplateSyntaxError

# class AdminResyncClient(BaseView):
#     def index(self):
# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_admin.py::test_AdminResyncClient_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # original role
        (6, 200), # original role + repoadmin
        (7, 403), # no role
    ],
)
def test_AdminResyncClient_index(app, client, users, id, status_code):
    url = url_for('resync.index')
    login_user_via_session(client, email=users[id]["email"])
    if status_code == 200:
        with pytest.raises(Exception) as e:
            res = client.get(url)
        assert e.type==TemplateNotFound
    else:
        res = client.get(url)
        assert res.status_code == status_code


# class AdminResyncClient(BaseView):
#     def get_list(self):
#     def create_resync(self):
#     def update_resync(self, resync_id):
#     def delete_resync(self, resync_id):
# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_admin.py::test_AdminResyncClient_action -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # original role
        (6, 200), # original role + repoadmin
        (7, 403), # no role
    ],
)
def test_AdminResyncClient_action(app, client, users, test_indices, id, status_code):
    # create_resync
    _data = {
        "id": None,
        "status": "Automatic",
        "resync_save_dir": "",
        "resync_mode": "Baseline",
        "saving_format": "JPCOAR-XML",
        "is_running": None,
        "interval_by_day": 1,
        "task_id": None,
        "result": None
    }
    headers = [('Content-Type', 'application/json'), ('Accept', 'application/json')]

    url = url_for('resync.create_resync')
    login_user_via_session(client, email=users[id]["email"])
    res = client.post(url, headers=headers, data=json.dumps(_data))
    assert res.status_code == status_code
    if status_code == 200:
        assert json.loads(res.data)['success'] == False
        assert json.loads(res.data)['errmsg'] == ['Repository is required', 'Target Index is required', 'Base Url is required']
        _data["repository_name"] = "root"
        _data["index_id"] = "1"
        _data["base_url"] = "test"
        _data['from_date'] = None
        _data['to_date'] = None
        res = client.post(url, headers=headers, data=json.dumps(_data))
        assert json.loads(res.data)['success'] == True

    # get_list
    repository = Community(root_node_id=1)
    with patch("invenio_communities.models.Community.get_repositories_by_user",return_value=[repository]):
        with patch("weko_index_tree.api.Indexes.get_child_list_recursive", return_value=[1]):
            url = url_for('resync.get_list')
            res = client.get(url)
            assert res.status_code == status_code
            if status_code == 200:
                res = json.loads(res.data)['data'][0]
                res.pop("created")
                res.pop("updated")
                res == {'base_url': 'test', 'from_date': None, 'id': 1, 'index_id': 1, 'index_name': 'Test index 1', 'interval_by_day': 1, 'is_running': None, 'repository_name': 'root', 'result': None, 'resync_mode': 'Baseline', 'resync_save_dir': '', 'saving_format': 'JPCOAR-XML', 'status': 'Automatic', 'task_id': None, 'to_date': None}

    # update_resync
    url = url_for('resync.update_resync', resync_id=2)
    res = client.post(url)
    assert res.status_code == status_code
    if status_code == 200:
        assert json.loads(res.data) == {'errmsg': ['Resync is not exist'], 'success': False}
        url = url_for('resync.update_resync', resync_id=1)
        res = client.post(url)
        assert json.loads(res.data) == {'errmsg': None, 'success': False}
        _data['base_url'] = 'test_update'
        res = client.post(url, headers=headers, data=json.dumps(_data))
        res = json.loads(res.data)
        res['data'].pop("created")
        res['data'].pop("updated")
        assert res['success'] == True
        assert res['data'] == {'base_url': 'test_update', 'from_date': None, 'id': 1, 'index_id': 1, 'index_name': 'Test index 1', 'interval_by_day': 1, 'is_running': None, 'repository_name': 'root', 'result': None, 'resync_mode': 'Baseline', 'resync_save_dir': '', 'saving_format': 'JPCOAR-XML', 'status': 'Automatic', 'task_id': None, 'to_date': None}


    # delete_resync
    url = url_for('resync.delete_resync', resync_id=2)
    res = client.post(url)
    assert res.status_code == status_code
    if status_code == 200:
        assert json.loads(res.data) == {'errmsg': ['Resync is not exist'], 'success': False}
        url = url_for('resync.delete_resync', resync_id=1)
        res = client.post(url)
        assert json.loads(res.data) == {'success': True}



# class AdminResyncClient(BaseView):
#     def run_import(self, resync_id):
#     def run_sync(self, resync_id):
#     def toggle_auto(self, resync_id):

# class AdminResyncClient(BaseView):
#     def get_logs(self, resync_id):
# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_admin.py::test_AdminResyncClient_get_logs -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # original role
        (6, 200), # original role + repoadmin
        (7, 403), # no role
    ],
)
def test_AdminResyncClient_get_logs(app, client, test_resync, users, test_indices, id, status_code):
    url = url_for('resync.get_logs', resync_id=20)
    login_user_via_session(client, email=users[id]["email"])
    res = client.get(url)
    assert res.status_code == status_code
    if status_code == 200:
        assert json.loads(res.data) == {'success': False}
        with pytest.raises(Exception) as e:
            url = url_for('resync.get_logs', resync_id=0)
            res = client.get(url)
        assert e.type == AttributeError
        url = url_for('resync.get_logs', resync_id=10)
        res = client.get(url)
        assert json.loads(res.data) == {'logs': [{'counter': {}, 'end_time': '2022-10-02T00:00:00', 'errmsg': None, 'id': 10, 'log_type': '', 'start_time': '2022-10-01T00:00:00', 'status': 'Success'}], 'success': True}


# class AdminResyncClient(BaseView):
#     def toggle_auto(self, resync_id):
# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_admin.py::test_AdminResyncClient_toggle_auto -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 403), # contributor
        (1, 200), # repoadmin
        (2, 200), # sysadmin
        (3, 200), # comadmin
        (4, 403), # generaluser
        (5, 403), # original role
        (6, 200), # original role + repoadmin
        (7, 403), # no role
    ],
)
def test_AdminResyncClient_toggle_auto(app, client, test_resync, users, test_indices, id, status_code):
    _data = {
        "status": "Automatic",
        "resync_save_dir": "",
        "resync_mode": "Baseline",
        "saving_format": "JPCOAR-XML",
        "is_running": None,
        "interval_by_day": 1,
        "task_id": None,
        "result": None,
        "repository_name": "root",
        "index_id": "1",
        "base_url": "test"
    }
    headers = [('Content-Type', 'application/json'), ('Accept', 'application/json')]

    url = url_for('resync.toggle_auto', resync_id=20)
    login_user_via_session(client, email=users[id]["email"])
    res = client.post(url)
    assert res.status_code == status_code
    if status_code == 200:
        assert json.loads(res.data) == {'success': False, 'errmsg': ["Resync is not automatic"]}
        url = url_for('resync.toggle_auto', resync_id=10)
        res = client.post(url)
        assert json.loads(res.data) == {'errmsg': ["'NoneType' object has no attribute 'get'"], 'success': False}
        url = url_for('resync.toggle_auto', resync_id=10)
        res = client.post(url, headers=headers, data=json.dumps(_data))
        res = json.loads(res.data)
        res['data'].pop("created")
        res['data'].pop("updated")
        assert res['success'] == True
        assert res['data'] == {'base_url': 'test', 'from_date': None, 'id': 10, 'index_id': 1, 'index_name': 'Test index 1', 'interval_by_day': 1, 'is_running': None, 'repository_name': 'root', 'result': None, 'resync_mode': 'Baseline', 'resync_save_dir': '', 'saving_format': 'JPCOAR-XML', 'status': 'Automatic', 'task_id': None, 'to_date': None}


# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_admin.py::test_get_repository -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
def test_get_repository(app, client, users):
    url = url_for('resync.get_repository')

    # super role user
    login_user_via_session(client, email=users[2]["email"])
    data = {'id': 1, 'name': 'root', 'children': []}
    with patch("weko_index_tree.api.Indexes.get_index_tree", return_value=[data]):
        res = client.get(url)
        assert res.status_code == 200
        assert json.loads(res.data) == [{'id': 0, 'value': 'Root Index'},
                                        {'id': 1, 'value': 'root <ID:1>'}]

    # super role user with children
    data = {'id': 1, 'name': 'root', 'children': [{'id': 2, 'name': 'child', 'children': []}]}
    with patch("weko_index_tree.api.Indexes.get_index_tree", return_value=[data]):
        res = client.get(url)
        assert res.status_code == 200
        assert json.loads(res.data) == [{'id': 0, 'value': 'Root Index'},
                                        {'id': 1, 'value': 'root <ID:1>'},
                                        {'id': 2, 'value': 'root <ID:1> / child <ID:2>'}]

    # comadmin role user with repository
    login_user_via_session(client, email=users[3]["email"])
    mock_repo = Community(root_node_id=1)
    data = {'id': 1, 'name': 'root', 'children': []}
    with patch("invenio_communities.models.Community.get_repositories_by_user", return_value=[mock_repo]):
        with patch("weko_index_tree.api.Indexes.get_index_tree", return_value=[data]):
            res = client.get(url)
            assert res.status_code == 200
            assert json.loads(res.data) == [{'id': 1, 'value': 'root <ID:1>'}]

    # comadmin role user with no repository
    with patch("invenio_communities.models.Community.get_repositories_by_user", return_value=[]):
        res = client.get(url)
        assert res.status_code == 200
        assert json.loads(res.data) == []

    # comadmin role user with repository but no index
    with patch("invenio_communities.models.Community.get_repositories_by_user", return_value=[mock_repo]):
        with patch("weko_index_tree.api.Indexes.get_index_tree", return_value=[]):
            res = client.get(url)
            assert res.status_code == 200
            assert json.loads(res.data) == []
