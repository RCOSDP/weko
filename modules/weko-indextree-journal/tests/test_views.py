import pytest
import json
from mock import patch, MagicMock
from flask import Flask, json, jsonify, session, url_for
from invenio_accounts.testutils import login_user_via_session

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_views.py::test_export_journals_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_export_journals_guest(app, db, client_rest):
    # guest
    res = client_rest.get("/indextree/journal/export")
    assert res.status_code == 302

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_views.py::test_export_journals -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
user_results = [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
]
@pytest.mark.parametrize('id, status_code', user_results)
def test_export_journals(app, db, client_rest, users, id, status_code):
    # test user role
    login_user_via_session(client=client_rest, email=users[id]["email"])
    res = client_rest.get("/indextree/journal/export")
    assert res.status_code == status_code


# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_views.py::test_check_view_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_check_view_guest(app, db, client_rest):
    # guest
    res = client_rest.get("/indextree/journal/save/kbart")
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
def test_check_view(app, db, client_rest, users, test_journals, id, status_code):
    # test user role
    login_user_via_session(client=client_rest, email=users[id]["email"])
    res = client_rest.get("/indextree/journal/save/kbart")
    assert res.status_code == status_code

    app.config['OAISERVER_REPOSITORY_NAME'] = 'WEKO'
    app.config['THEME_SITEURL'] = 'https://inveniosoftware.org'
    res = client_rest.get("/indextree/journal/save/kbart")
    assert res.status_code == status_code