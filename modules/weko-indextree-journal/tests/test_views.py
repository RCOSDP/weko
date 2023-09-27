import pytest
import json
import os
from mock import patch
from flask import json, url_for
from invenio_accounts.testutils import login_user_via_session

from weko_indextree_journal.models import Journal
from weko_indextree_journal.views import obj_dict, dbsession_clean

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_views.py::test_export_journals_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_export_journals_guest(app, db, client):
    # guest
    res = client.get("/indextree/journal/export")
    assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_views.py::test_export_journals_acl -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
user_results = [
    (0, True),
    (1, True),
    (2, True),
    (3, True),
    (4, True),
]
@pytest.mark.parametrize('id, is_permission', user_results)
def test_export_journals_acl(app, db, client, users, id, is_permission):
    # test user role
    login_user_via_session(client=client, email=users[id]["email"])
    res = client.get("/indextree/journal/export")
    if is_permission:
        assert res.status_code == 200
    else:
        assert res.status_code != 200

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_views.py::test_export_journals -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_export_journals(app, db, client, users,test_journals):

    if os.path.isfile("journal.tsv"):
        os.remove("journal.tsv")
    
    url = url_for("weko_indextree_journal.export_journals")
    login_user_via_session(client=client, email=users[0]["email"])
    res = client.get(url)
    assert json.loads(res.data) == {"result": True}
    assert os.path.isfile("journal.tsv")
    with open("journal.tsv","r") as f:
        result = f.readlines()[0]
        assert "'title_id': 1" in result

    if os.path.isfile("journal.tsv"):
        os.remove("journal.tsv")
    # raise Exception
    with patch("weko_indextree_journal.views.numpy.savetxt",side_effect=Exception("test_error")):
        res = client.get(url)
        assert json.loads(res.data) == {"result": False}
    
# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_views.py::test_obj_dict -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_obj_dict(test_journals):
    journal = Journal.query.first()
    result = obj_dict(journal)
    assert result['publication_title'] == 'test journal 1'
    assert result['publication_type'] == 'serial'
    assert result['title_url'] == 'search?search_type=2&q=1'
    assert result['language'] == 'en'
    assert result['is_output'] == True
    assert result['title_id'] == 1
    assert result['date_first_issue_online'] == '2022-01-01'
    assert result['owner_user_id'] == 0
    assert result['coverage_depth'] == 'abstract'
    assert result['id'] == 1
    assert result['date_last_issue_online'] == '2022-01-01'
    assert result['index_id'] == 1
    

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_views.py::test_check_view_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_check_view_guest(app, db, client):
    # guest
    res = client.get("/indextree/journal/save/kbart")
    assert res.status_code == 302


# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_views.py::test_check_view -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
user_results = [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
]
@pytest.mark.parametrize('id, status_code', user_results)
def test_check_view(app, db, client, users, test_journals, id, status_code):
    # test user role
    login_user_via_session(client=client, email=users[id]["email"])
    res = client.get("/indextree/journal/save/kbart")
    assert res.status_code == status_code

    app.config['OAISERVER_REPOSITORY_NAME'] = 'WEKO'
    app.config['THEME_SITEURL'] = 'https://inveniosoftware.org'
    res = client.get("/indextree/journal/save/kbart")
    assert res.status_code == status_code
    
# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_views.py::test_dbsession_clean -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_dbsession_clean(app, db,test_indices):
    # exist exception
    journal1 = Journal(id=1,index_id=1)
    db.session.add(journal1)
    dbsession_clean(None)
    assert Journal.query.filter_by(id=1).first()

    # raise Exception
    journal2 = Journal(id=2,index_id=1)
    db.session.add(journal2)
    with patch("weko_indextree_journal.views.db.session.commit",side_effect=Exception):
        dbsession_clean(None)
        assert Journal.query.filter_by(id=2).first() is None

    # not exist exception
    journal3 = Journal(id=3,index_id=1)
    db.session.add(journal3)
    dbsession_clean(Exception)
    assert Journal.query.filter_by(id=3).first() is None