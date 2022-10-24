import pytest
import json
from mock import patch, MagicMock
from flask import Flask, json, jsonify, session, url_for
from jinja2.exceptions import TemplateNotFound
from invenio_accounts.testutils import login_user_via_session

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_admin.py::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
user_results = [
    (0, 403),
    (1, 403),
    (2, 403),
    (3, 403),
    (4, 200),
]
@pytest.mark.parametrize('id, status_code', user_results)
def test_index(app, db, client_rest, users, test_indices, db_itemtype, id, status_code):
    app.config['WEKO_ITEMS_UI_ERROR_TEMPLATE'] = 'weko_items_ui/error.html'
    login_user_via_session(client=client_rest, email=users[id]["email"])
    if id == 4:
        with pytest.raises(Exception) as e:
            res = client_rest.get(url_for("indexjournal.index"))
        assert e.type==TemplateNotFound
    else:
        res = client_rest.get(url_for("indexjournal.index"))
        assert res.status_code == status_code