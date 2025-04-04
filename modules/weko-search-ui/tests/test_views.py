# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_views.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp

import json
import pytest
from flask import current_app, make_response, request, url_for
from flask_login import current_user
from mock import patch

from weko_search_ui.views import (
    search,
    opensearch_description,
    journal_detail,
    search_feedback_mail_list,
    get_child_list,
    get_path_name_dict,
    gettitlefacet,
    get_last_item_id
)


# def search(): ~ jinja2.exceptions.TemplateNotFound: weko_theme/page.html
# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_views.py::test_search -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_search(i18n_app, users, db_register, index_style):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        with patch("flask.templating._render", return_value=""):
            assert search()==""

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_views.py::test_search_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_search_acl_guest(app,client,db_register2,index_style,users,db_register):
    url = url_for("weko_search_ui.search",_external=True)
    with patch("flask.templating._render", return_value=""):
        ret = client.get(url)
        assert ret.status_code == 200

    url = url_for("weko_search_ui.search", search_type=0,_external=True)
    with patch("flask.templating._render", return_value=""):
        ret = client.get(url)
        assert ret.status_code == 200

    url = url_for("weko_search_ui.search", community='c',_external=True)
    with patch("flask.templating._render", return_value=""):
        ret = client.get(url)
        assert ret.status_code == 200

    url = url_for("weko_search_ui.search", search_type=0,community='c',_external=True)
    with patch("flask.templating._render", return_value=""):
        ret = client.get(url)
        assert ret.status_code == 200

    url = url_for("weko_search_ui.search", item_link="1",_external=True)
    with patch("flask.templating._render", return_value=""):
        ret = client.get(url)
        assert ret.status_code == 404



@pytest.mark.parametrize(
    "id, status_code",
    [
        # (0, 200),
        # (1, 302),
        # (2, 302),
        (3, 200),
        # (4, 302),
        # (5, 302),
        # (6, 302),
        # (7, 302),
    ],
)
def test_search_acl(app,client,db_register2,index_style,users,db_register,id,status_code):
    url = url_for("weko_search_ui.search", _external=True)
    with patch("flask_login.utils._get_user", return_value=users[id]['obj']):
        with patch("flask.templating._render", return_value=""):
            ret = client.get(url)
            assert ret.status_code == status_code

    url = url_for("weko_search_ui.search", search_type=0,_external=True)
    with patch("flask_login.utils._get_user", return_value=users[id]['obj']):
        with patch("flask.templating._render", return_value=""):
            ret = client.get(url)
            assert ret.status_code == status_code

    url = url_for("weko_search_ui.search", community='c',_external=True)
    with patch("flask_login.utils._get_user", return_value=users[id]['obj']):
        with patch("flask.templating._render", return_value=""):
            ret = client.get(url)
            assert ret.status_code == status_code

    url = url_for("weko_search_ui.search", search_type=0,community='c',_external=True)
    with patch("flask_login.utils._get_user", return_value=users[id]['obj']):
        with patch("flask.templating._render", return_value=""):
            ret = client.get(url)
            assert ret.status_code == status_code

    url = url_for("weko_search_ui.search", item_link="1",_external=True)
    with patch("flask_login.utils._get_user", return_value=users[id]['obj']):
        with patch("flask.templating._render", return_value=""):
            ret = client.get(url)
            assert ret.status_code == 404

# def opensearch_description():
def test_opensearch_description(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert opensearch_description()

# .tox/c1/bin/pytest --cov=weko_search_ui tests/test_views.py::test_opensearch_description_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-search-ui/.tox/c1/tmp
def test_opensearch_description_acl_guest(app,client_api,db_register2,index_style,users,db_register):
    url = url_for('weko_search_api.opensearch_description')
    with patch("flask.templating._render", return_value=""):
        ret = client_api.get(url)
        assert ret.status_code == 200


# def journal_detail(index_id=0):
def test_journal_detail(i18n_app, users, indices):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert journal_detail(33)


# def search_feedback_mail_list():
def test_search_feedback_mail_list(i18n_app, users):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert search_feedback_mail_list()


# def get_child_list(index_id=0):
def test_get_child_list(i18n_app, users, indices):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_child_list(33)


# def get_path_name_dict(path_str=""):
def test_get_path_name_dict(i18n_app, users, indices):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert get_path_name_dict('33_44')


# def gettitlefacet():
def test_gettitlefacet(i18n_app, users, client, facet_search_setting):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        assert gettitlefacet()
        url = url_for('weko_search_ui.gettitlefacet')
        ret = client.post(url)
        assert ret
        assert ret.status_code == 200
        result = json.loads(ret.data)
        data = result.get("data")
        assert data.get("displayNumbers")
        assert data.get("isOpens")
        assert data.get("uiTypes")
        assert data.get("searchConditions")
        assert not result.get("isFacetLangDisplay")

# def get_last_item_id():
def test_get_last_item_id(i18n_app, users, db_activity):
    with patch("flask_login.utils._get_user", return_value=users[3]['obj']):
        res, _ = get_last_item_id()
        data = json.loads(res.data)
        assert data["data"]["last_id"]

@patch("invenio_communities.models.Community")
@patch("invenio_indexer.api.RecordIndexer")
def test_get_last_item_id_comadmin(mock_record_indexer, mock_community, i18n_app, users):
    mock_record_indexer.return_value.client.search.return_value = {"hits": {"hits": [{"sort": ["456"]}]}}
    mock_community.get_repositories_by_user.return_value = []
    with patch("flask_login.utils._get_user", return_value=users[4]['obj']):
        res, _ = get_last_item_id()
        data = json.loads(res.data)
        assert data["data"]["last_id"]
