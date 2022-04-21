'''
/admin/indexjournal/<int:journal_id>:get,put,post,delete

'''
import json
import pytest
from mock import patch, MagicMock
from invenio_accounts.testutils import login_user_via_session


user_results1 = [
    (0, 403),
    (1, 403),
    (2, 201),
    (3, 201),
    (4, 201),
]


@pytest.mark.parametrize('id, status_code', user_results1)
def test_JournalActionResource_post_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    with patch('weko_indextree_journal.rest.Journals.create', return_value=True):
        res = client_rest.post('/admin/indexjournal/1',
                               data=json.dumps({'test':'test'}),
                               content_type='application/json')
        assert res.status_code == status_code


def test_JournalActionResource_post_guest(client_rest, users):
    with patch('weko_indextree_journal.rest.Journals.create', return_value=True):
        res = client_rest.post('/admin/indexjournal/1',
                               data=json.dumps({'test':'test'}),
                               content_type='application/json')
        assert res.status_code == 401


user_results2 = [
    (0, 403),
    (1, 403),
    (2, 200),
    (3, 200),
    (4, 200),
]


@pytest.mark.parametrize('id, status_code', user_results2)
def test_JournalActionResource_put_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    with patch('weko_indextree_journal.rest.Journals.update', return_value=True):
        res = client_rest.put('/admin/indexjournal/1',
                              data=json.dumps({'test':'test'}),
                              content_type='application/json')
        assert res.status_code == status_code

def test_JournalActionResource_put_guest(client_rest, users):
    with patch('weko_indextree_journal.rest.Journals.update', return_value=True):
        res = client_rest.put('/admin/indexjournal/1',
                              data=json.dumps({'test':'test'}),
                              content_type='application/json')
        assert res.status_code == 401


@pytest.mark.parametrize('id, status_code', user_results2)
def test_JournalActionResource_delete_login(client_rest, users, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]['email'])
    mock_jounals = MagicMock(return_value=MockJournals)
    with patch('weko_indextree_journal.rest.Journals.get_self_path', return_value=True):
        with patch('weko_indextree_journal.rest.Journals.delete_by_action', return_value=True):
            res = client_rest.delete('/admin/indexjournal/1',
                                  data=json.dumps({'test':'test'}),
                                  content_type='application/json')
            assert res.status_code == status_code


def test_JournalActionResource_delete_guest(client_rest, users):
    mock_jounals = MagicMock(return_value=MockJournals)
    with patch('weko_indextree_journal.rest.Journals.get_self_path', return_value=True):
        with patch('weko_indextree_journal.rest.Journals.delete_by_action', return_value=True):
            res = client_rest.delete('/admin/indexjournal/1',
                                  data=json.dumps({'test':'test'}),
                                  content_type='application/json')
            assert res.status_code == 401
