'''
/admin/indexjournal/<int:journal_id>:get,put,post,delete

'''
import json
import pytest
from mock import patch, MagicMock
from invenio_accounts.testutils import login_user_via_session
from weko_indextree_journal.api import Journals
from weko_indextree_journal.rest import need_record_permission, create_blueprint


# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::test_api_get_journal -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_api_get_journal(app, db, test_journals):
    res = Journals.get_journal(1)
    assert res=={'access_type': 'F', 'coverage_depth': 'abstract', 'coverage_notes': '', 'date_first_issue_online': '2022-01-01', 'date_last_issue_online': '2022-01-01', 'date_monograph_published_online': '', 'date_monograph_published_print': '', 'deleted': '', 'embargo_info': '', 'first_author': '', 'first_editor': '', 'ichushi_code': '', 'id': 1, 'index_id': 1, 'is_output': True, 'jstage_code': '', 'language': 'en', 'monograph_edition': '', 'monograph_volume': '', 'ncid': '', 'ndl_bibid': '', 'ndl_callno': '', 'num_first_issue_online': '', 'num_first_vol_online': '', 'num_last_issue_online': '', 'num_last_vol_online': '', 'online_identifier': '', 'owner_user_id': 0, 'parent_publication_title_id': '', 'preceding_publication_title_id': '', 'print_identifier': '', 'publication_title': 'test journal 1', 'publication_type': 'serial', 'publisher_name': '', 'title_alternative': '', 'title_id': 1, 'title_transcription': '', 'title_url': 'search?search_type=2&q=1'}
    res = Journals.get_journal(-1)
    assert res==[]

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::test_api_get_journal_none_db -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_api_get_journal_none_db(app):
    res = Journals.get_journal(1)
    assert res==None

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::test_api_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_api_delete(app, db, test_journals):
    res = Journals.delete(1)
    assert res==None

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::test_JournalActionResource_post_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
user_results1 = [
    (0, 400),
    (1, 201),
    (2, 201),
    (3, 201),
    (4, 400),
]
@pytest.mark.parametrize('id, status_code', user_results1)
def test_JournalActionResource_post_login(client_rest, users, test_indices, id, status_code):
    _data = dict(
        id=id,
        index_id=id,
        publication_title="test journal {}".format(id),
        date_first_issue_online="2022-01-01",
        date_last_issue_online="2022-01-01",
        title_url="search?search_type=2&q={}".format(id),
        title_id=str(id),
        coverage_depth="abstract",
        publication_type="serial",
        access_type="F",
        language="en",
        is_output=True
    )
    login_user_via_session(client=client_rest, email=users[id]['email'])
    res = client_rest.post('/admin/indexjournal/1',
                           data=json.dumps(_data),
                           content_type='application/json')
    assert res.status_code == status_code


# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::test_JournalActionResource_post_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_JournalActionResource_post_guest(client_rest, users):
    res = client_rest.post('/admin/indexjournal/1',
                           data=json.dumps({'test':'test'}),
                           content_type='application/json')
    assert res.status_code == 400


# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::test_JournalActionResource_put_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
user_results2 = [
    (0, 400),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 400),
]
@pytest.mark.parametrize('id, status_code', user_results2)
def test_JournalActionResource_put_login(client_rest, users, test_indices, test_journals, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    _data = dict(
        id=id,
        index_id=id,
        publication_title="test journal {}".format(id),
        date_first_issue_online="2022-01-01",
        date_last_issue_online="2022-01-01",
        title_url="search?search_type=2&q={}".format(id),
        title_id=str(id),
        coverage_depth="abstract",
        publication_type="serial",
        access_type="F",
        language="en",
        is_output=True
    )
    res = client_rest.put('/admin/indexjournal/1',
                          data=json.dumps(_data),
                          content_type='application/json')
    assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_rest.py::test_JournalActionResource_put_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_JournalActionResource_put_guest(client_rest, users):
    res = client_rest.put('/admin/indexjournal/1',
                          data=json.dumps({'test':'test'}),
                          content_type='application/json')
    assert res.status_code == 400


@pytest.mark.parametrize('id, status_code', user_results2)
def test_JournalActionResource_delete_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    with patch('weko_indextree_journal.rest.Journals.get_self_path', return_value=True):
        with patch('weko_indextree_journal.rest.Journals.delete_by_action', return_value=True):
            res = client_rest.delete('/admin/indexjournal/1',
                                  data=json.dumps({'test':'test'}),
                                  content_type='application/json')
            assert res.status_code == status_code


def test_JournalActionResource_delete_guest(client_rest, users):
    with patch('weko_indextree_journal.rest.Journals.get_self_path', return_value=True):
        with patch('weko_indextree_journal.rest.Journals.delete_by_action', return_value=True):
            res = client_rest.delete('/admin/indexjournal/1',
                                  data=json.dumps({'test':'test'}),
                                  content_type='application/json')
            assert res.status_code == 401


def test_create_blueprint(i18n_app):
    # Exception coverage
    try:
        create_blueprint("test")
    except:
        pass
