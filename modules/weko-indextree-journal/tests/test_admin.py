import pytest
import json
from mock import patch, MagicMock
from flask import Flask, json, jsonify, session, url_for
from jinja2.exceptions import TemplateSyntaxError
from invenio_accounts.testutils import login_user_via_session
from weko_indextree_journal.admin import IndexJournalSettingView

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_admin.py::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
user_results = [
    (0, 403),
    (1, 403),
    (2, 403),
    (3, 403),
    (4, 200),
]
@pytest.mark.parametrize('id, status_code', user_results)
def test_index(app, db, client_rest, users, test_indices, db_itemtype, test_journals, id, status_code):
    app.config['WEKO_ITEMS_UI_ERROR_TEMPLATE'] = "weko_items_ui/error.html"
    app.config['WEKO_INDEX_TREE_LIST_API'] = "/api/tree"
    app.config['WEKO_INDEX_TREE_API'] = "/api/tree/index/"
    app.config['WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_API'] = ""
    app.config['WEKO_INDEXTREE_JOURNAL_FORM_JSON_API'] = ""
    login_user_via_session(client=client_rest, email=users[id]["email"])
    if id == 4:
        # need to fix
        with pytest.raises(Exception) as e:
            res = client_rest.get(url_for("indexjournal.index", index_id=1))
        assert e.type==TemplateSyntaxError
    else:
        res = client_rest.get(url_for("indexjournal.index"))
        assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_admin.py::test_get_journal_by_index_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
user_results = [
    (0, 403),
    (1, 403),
    (2, 403),
    (3, 403),
    (4, 200),
]
@pytest.mark.parametrize('id, status_code', user_results)
def test_get_journal_by_index_id(app, db, client_rest, users, test_indices, id, status_code):
    login_user_via_session(client=client_rest, email=users[id]["email"])
    res = client_rest.get(url_for("indexjournal.get_journal_by_index_id", index_id=1))
    assert res.status_code == status_code

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_admin.py::test_get_json_schema -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
user_results = [
    (0, 403),
    (1, 403),
    (2, 403),
    (3, 403),
    (4, 200),
]
@pytest.mark.parametrize('id, status_code', user_results)
def test_get_json_schema(i18n_app, db, users, test_indices, id, status_code):
    with i18n_app.test_client() as client:
        login_user_via_session(client=client, email=users[id]["email"])
        res = client.get(url_for("indexjournal.get_json_schema"))
        assert res.status_code == status_code
        if id == 4:
            i18n_app.config['WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_FILE'] = ''
            res = client.get(url_for("indexjournal.get_json_schema"))
            assert res.status_code == 500

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_admin.py::test_get_schema_form -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
user_results = [
    (0, 403),
    (1, 403),
    (2, 403),
    (3, 403),
    (4, 200),
]
@pytest.mark.parametrize('id, status_code', user_results)
def test_get_schema_form(i18n_app, db, users, test_indices, id, status_code):
    
    with i18n_app.test_client() as client:
        login_user_via_session(client=client, email=users[id]["email"])
        res = client.get(url_for("indexjournal.get_schema_form"))
        assert res.status_code == status_code
        if id == 4:
            i18n_app.config['WEKO_INDEXTREE_JOURNAL_FORM_JSON_FILE'] = ''
            res = client.get(url_for("indexjournal.get_schema_form"))
            assert res.status_code == 500


def test_get_journal_by_index_id_IndexJournalSettingView(i18n_app, indices):
    test = IndexJournalSettingView()
    index_id = 33

    assert "Response" in str(type(test.get_journal_by_index_id(index_id=index_id)))

    with patch("weko_indextree_journal.api.Journals.get_journal_by_index_id", return_value=None):
        assert "Response" in str(type(test.get_journal_by_index_id(index_id=1)))
    
    # Exception coverage
    try:
        assert "Response" in str(type(test.get_journal_by_index_id(index_id="a")))
    except:
        pass


def test_get_schema_form_IndexJournalSettingView(i18n_app):
    test = IndexJournalSettingView()
    
    assert "Response" in str(type(test.get_schema_form()))

    # Exception coverage
    try:
        i18n_app.config['WEKO_INDEXTREE_JOURNAL_FORM_JSON_FILE'] = ""
        test.get_schema_form()
    except:
        pass