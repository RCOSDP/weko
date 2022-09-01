import json
from collections import Iterable, OrderedDict
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from flask import Flask, json, jsonify, session, url_for
from flask_security.utils import login_user
from invenio_accounts.testutils import login_user_via_session
from invenio_i18n.babel import set_locale
from invenio_pidstore.errors import PIDDoesNotExistError
from mock import patch
from weko_workflow.api import WorkActivity, WorkFlow
from weko_workflow.models import Activity

from weko_items_ui.views import (
    check_ranking_show,
    default_view_method,
    iframe_index,
    iframe_items_index,
    iframe_save_model,
    to_links_js,
)


# def index(item_type_id=0):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_index_acl_nologin -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_index_acl_nologin(client, db_sessionlifetime):
    url = url_for("weko_items_ui.index", _external=True)
    res = client.get("http://test_server/items/")
    assert res.status_code == 302
    assert res.location == url_for("security.login", next="/items/", _external=True)


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_index_acl -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 302),
        (1, 302),
        (2, 302),
        (3, 302),
        (4, 403),
        (5, 403),
        (6, 302),
        (7, 403),
    ],
)
def test_index_acl(client, db_itemtype, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_items_ui.index", _external=True)
    res = client.get(url)
    assert res.status_code == status_code
    if res.status_code == 302:
        assert res.location == "{}1".format(url)
    else:
        assert res.location == None


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_index -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
    ],
)
def test_index(client, db_itemtype, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_items_ui.index", _external=True)
    with patch("flask.templating._render", return_value=""):
        res = client.get("{0}{1}".format(url, db_itemtype["item_type"].id))
        assert res.status_code == status_code

    res = client.get("{0}{1}".format(url, 999))
    assert res.status_code == 302

    res = client.get("{0}{1}".format(url, "hoge"))
    assert res.status_code == 404


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_index_noitemtype -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_index_noitemtype(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    url = url_for("weko_items_ui.index", _external=True)
    with patch("flask.templating._render", return_value=""):
        res = client.get("{0}{1}".format(url, 1))
        assert res.status_code == 400


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_index_exception -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@patch("weko_theme.utils.get_design_layout", MagicMock(side_effect=Exception()))
def test_index_exception(client, db_itemtype, users):
    login_user_via_session(client=client, email=users[0]["email"])
    url = url_for("weko_items_ui.index", _external=True)
    with patch("flask.templating._render", return_value=""):
        res = client.get("{0}{1}".format(url, 1))
        assert res.status_code == 400


# def iframe_index(item_type_id=0):

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_iframe_index_acl_nologin -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_iframe_index_acl_nologin(client, db_sessionlifetime):
    url = url_for("weko_items_ui.iframe_index")
    res = client.get(url)
    assert res.status_code == 302
    assert res.location == url_for(
        "security.login", next="/items/iframe", _external=True
    )


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_iframe_index_acl -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 403),
        (5, 403),
        (6, 200),
        (7, 403),
    ],
)
def test_iframe_index_acl(app, client, users, db_itemtype, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    url = "{}/1".format(url_for("weko_items_ui.iframe_index"))
    with patch("flask.templating._render", return_value=""):
        res = client.get(url)
        assert res.status_code == status_code


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_iframe_index_noitemtypeid -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 404),
    ],
)
def test_iframe_index_noitemtypeid(app, client, db_itemtype, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    url = "{}".format(url_for("weko_items_ui.iframe_index"))
    with patch("flask.templating._render", return_value=""):
        res = client.get(url)
        assert res.status_code == status_code

    url = "{}/0".format(url_for("weko_items_ui.iframe_index"))
    with patch("flask.templating._render", return_value=""):
        res = client.get(url)
        assert res.status_code == status_code

    url = "{}/hoge".format(url_for("weko_items_ui.iframe_index"))
    with patch("flask.templating._render", return_value=""):
        res = client.get(url)
        assert res.status_code == status_code


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_iframe_index -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
    ],
)
def test_iframe_index(app, db, client, users, db_itemtype, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    url = "{}/1".format(url_for("weko_items_ui.iframe_index"))
    with open("tests/data/temp_data.json", "r") as f:
        tmp_item = json.dumps(json.load(f))

    with patch(
        "weko_workflow.api.WorkActivity.get_activity_metadata", return_value=tmp_item
    ):
        with patch("flask.templating._render", return_value=""):
            with client.session_transaction() as session:
                session["activity_info"] = {
                    "activity_id": "A-20220818-00001",
                    "action_id": 3,
                    "action_version": "1.0.1",
                    "action_status": "M",
                    "commond": "",
                }
            res = client.get(url)
            assert res.status_code == status_code


# def test_iframe_index(app,client,db_itemtype, users):
# with app.test_request_context():
# login_user_via_session(client=client, email=users[0]['email'])
# session['activity_info'] = {'activity_id': 'A-20220818-00001', 'action_id': 3, 'action_version': '1.0.1', 'action_status': 'M', 'commond': ''}
# assert iframe_index(1)==""

# with patch("flask.session",return_value={'activity_id': 'A-20220818-00001', 'action_id': 3, 'action_version': '1.0.1', 'action_status': 'M', 'commond': ''}):
#     with patch("weko_workflow.api.WorkActivity.get_activity_metadata",return_value = "{'metainfo': {'pubdate': '2022-08-19', 'item_1617186331708': [{'subitem_1551255647225': 'aa', 'subitem_1551255648112': 'ja'}], 'item_1617186385884': [{}], 'item_1617186419668': [{'creatorAffiliations': [{'affiliationNameIdentifiers': [{}], 'affiliationNames': [{}]}], 'creatorAlternatives': [{}], 'creatorMails': [{}], 'creatorNames': [{}], 'familyNames': [{}], 'givenNames': [{}], 'nameIdentifiers': [{}]}], 'item_1617186499011': [{}], 'item_1617186609386': [{}], 'item_1617186626617': [{}], 'item_1617186643794': [{}], 'item_1617186660861': [{}], 'item_1617186702042': [{}], 'item_1617186783814': [{}], 'item_1617186859717': [{}], 'item_1617186882738': [{'subitem_geolocation_place': [{}]}], 'item_1617186901218': [{'subitem_1522399412622': [{}], 'subitem_1522399651758': [{}]}], 'item_1617186920753': [{}], 'item_1617186941041': [{}], 'item_1617187112279': [{}], 'item_1617187187528': [{'subitem_1599711633003': [{}], 'subitem_1599711660052': [{}], 'subitem_1599711758470': [{}], 'subitem_1599711788485': [{}]}], 'item_1617349709064': [{'contributorAffiliations': [{'contributorAffiliationNameIdentifiers': [{}], 'contributorAffiliationNames': [{}]}], 'contributorAlternatives': [{}], 'contributorMails': [{}], 'contributorNames': [{}], 'familyNames': [{}], 'givenNames': [{}], 'nameIdentifiers': [{}]}], 'item_1617353299429': [{'subitem_1523320863692': [{}]}], 'item_1617605131499': [{'date': [{}], 'fileDate': [{}], 'filesize': [{}]}], 'item_1617610673286': [{'nameIdentifiers': [{}], 'rightHolderNames': [{}]}], 'item_1617620223087': [{}], 'item_1617944105607': [{'subitem_1551256015892': [{}], 'subitem_1551256037922': [{}]}], 'item_1617187056579': {'bibliographic_titles': [{}]}, 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1}, 'files': [], 'endpoints': {'initialization': '/api/deposits/items'}}"):
#         res = client.get("/items/iframe/1")
#         assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_iframe_index_exception -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
# @patch("weko_items_ui.views.iframe_index",MagicMock(side_effect=Exception()))
def test_iframe_index_exception(client, users):
    login_user_via_session(client=client, email=users[0]["email"])
    url = url_for("weko_items_ui.iframe_index", item_type_id=1, _external=True)
    with patch("weko_records.api.ItemTypes.get_by_id", side_effect=Exception()):
        res = client.get(url)
        assert res.status_code == 400


# def iframe_save_model():

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_iframe_save_model_nologin -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_iframe_save_model_nologin(client, db_sessionlifetime):
    url = url_for("weko_items_ui.iframe_save_model", _external=True)
    res = client.post(url)
    assert res.status_code == 302
    assert res.location == url_for(
        "security.login", next="/items/iframe/model/save", _external=True
    )


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_iframe_save_model_acl -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 200),
        (5, 200),
        (6, 200),
        (7, 200),
    ],
)
def test_iframe_save_model_acl(app, client, db_itemtype, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_items_ui.iframe_save_model", _external=True)
    res = client.post(url)
    assert res.status_code == status_code


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_iframe_save_model_error -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
    ],
)
def test_iframe_save_model_error(app, client, db_itemtype, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_items_ui.iframe_save_model", _external=True)
    data = "{'metainfo': {'pubdate': '2022-08-19', 'item_1617186331708': [{'subitem_1551255647225': 'aa', 'subitem_1551255648112': 'ja'}], 'item_1617186385884': [{}], 'item_1617186419668': [{'creatorAffiliations': [{'affiliationNameIdentifiers': [{}], 'affiliationNames': [{}]}], 'creatorAlternatives': [{}], 'creatorMails': [{}], 'creatorNames': [{}], 'familyNames': [{}], 'givenNames': [{}], 'nameIdentifiers': [{}]}], 'item_1617186499011': [{}], 'item_1617186609386': [{}], 'item_1617186626617': [{}], 'item_1617186643794': [{}], 'item_1617186660861': [{}], 'item_1617186702042': [{}], 'item_1617186783814': [{}], 'item_1617186859717': [{}], 'item_1617186882738': [{'subitem_geolocation_place': [{}]}], 'item_1617186901218': [{'subitem_1522399412622': [{}], 'subitem_1522399651758': [{}]}], 'item_1617186920753': [{}], 'item_1617186941041': [{}], 'item_1617187112279': [{}], 'item_1617187187528': [{'subitem_1599711633003': [{}], 'subitem_1599711660052': [{}], 'subitem_1599711758470': [{}], 'subitem_1599711788485': [{}]}], 'item_1617349709064': [{'contributorAffiliations': [{'contributorAffiliationNameIdentifiers': [{}], 'contributorAffiliationNames': [{}]}], 'contributorAlternatives': [{}], 'contributorMails': [{}], 'contributorNames': [{}], 'familyNames': [{}], 'givenNames': [{}], 'nameIdentifiers': [{}]}], 'item_1617353299429': [{'subitem_1523320863692': [{}]}], 'item_1617605131499': [{'date': [{}], 'fileDate': [{}], 'filesize': [{}]}], 'item_1617610673286': [{'nameIdentifiers': [{}], 'rightHolderNames': [{}]}], 'item_1617620223087': [{}], 'item_1617944105607': [{'subitem_1551256015892': [{}], 'subitem_1551256037922': [{}]}], 'item_1617187056579': {'bibliographic_titles': [{}]}, 'item_1617258105262': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'shared_user_id': -1}, 'files': [], 'endpoints': {'initialization': '/api/deposits/items'}}"
    res = client.post(url, json=data)
    assert res.status_code == status_code
    assert res.data == b'{"code":1,"msg":"Model save error"}\n'


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_iframe_save_model -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
    ],
)
def test_iframe_save_model(
    app, client, db_itemtype, db_workflow, users, id, status_code
):
    app.config["PRESERVE_CONTEXT_ON_EXCEPTION"] = False
    app.config["TESTING"] = True
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_items_ui.iframe_save_model", _external=True)
    data = {
        "metainfo": {
            "pubdate": "2022-08-19",
            "item_1617186331708": [
                {"subitem_1551255647225": "aa", "subitem_1551255648112": "ja"}
            ],
            "item_1617186385884": [{}],
            "item_1617186419668": [
                {
                    "creatorAffiliations": [
                        {"affiliationNameIdentifiers": [{}], "affiliationNames": [{}]}
                    ],
                    "creatorAlternatives": [{}],
                    "creatorMails": [{}],
                    "creatorNames": [{}],
                    "familyNames": [{}],
                    "givenNames": [{}],
                    "nameIdentifiers": [{}],
                }
            ],
            "item_1617186499011": [{}],
            "item_1617186609386": [{}],
            "item_1617186626617": [{}],
            "item_1617186643794": [{}],
            "item_1617186660861": [{}],
            "item_1617186702042": [{}],
            "item_1617186783814": [{}],
            "item_1617186859717": [{}],
            "item_1617186882738": [{"subitem_geolocation_place": [{}]}],
            "item_1617186901218": [
                {"subitem_1522399412622": [{}], "subitem_1522399651758": [{}]}
            ],
            "item_1617186920753": [{}],
            "item_1617186941041": [{}],
            "item_1617187112279": [{}],
            "item_1617187187528": [
                {
                    "subitem_1599711633003": [{}],
                    "subitem_1599711660052": [{}],
                    "subitem_1599711758470": [{}],
                    "subitem_1599711788485": [{}],
                }
            ],
            "item_1617349709064": [
                {
                    "contributorAffiliations": [
                        {
                            "contributorAffiliationNameIdentifiers": [{}],
                            "contributorAffiliationNames": [{}],
                        }
                    ],
                    "contributorAlternatives": [{}],
                    "contributorMails": [{}],
                    "contributorNames": [{}],
                    "familyNames": [{}],
                    "givenNames": [{}],
                    "nameIdentifiers": [{}],
                }
            ],
            "item_1617353299429": [{"subitem_1523320863692": [{}]}],
            "item_1617605131499": [{"date": [{}], "fileDate": [{}], "filesize": [{}]}],
            "item_1617610673286": [{"nameIdentifiers": [{}], "rightHolderNames": [{}]}],
            "item_1617620223087": [{}],
            "item_1617944105607": [
                {"subitem_1551256015892": [{}], "subitem_1551256037922": [{}]}
            ],
            "item_1617187056579": {"bibliographic_titles": [{}]},
            "item_1617258105262": {
                "resourcetype": "conference paper",
                "resourceuri": "http://purl.org/coar/resource_type/c_5794",
            },
            "shared_user_id": -1,
        },
        "files": [],
        "endpoints": {"initialization": "/api/deposits/items"},
    }
    with client.session_transaction() as session:
        session["activity_info"] = {
            "activity_id": "A-00000000-00000",
            "action_id": 3,
            "action_version": "1.0.1",
            "action_status": "M",
            "commond": "",
        }
    res = client.post(url, json=data)
    assert res.status_code == status_code
    data = json.loads(res.data)
    assert data["code"] == 0
    assert data["msg"].startswith("Model save success at") == True


# def iframe_success():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_iframe_success -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_iframe_success(client, db_sessionlifetime):
    url = url_for("weko_items_ui.iframe_success", _external=True)
    with patch("flask.templating._render", return_value=""):
        res = client.get(url)
        assert res.status_code == 200


# def iframe_error():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_iframe_error -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_iframe_error(client, db_sessionlifetime):
    url = url_for("weko_items_ui.iframe_error", _external=True)
    with patch("flask.templating._render", return_value=""):
        res = client.get(url)
        assert res.status_code == 200


# def get_json_schema(item_type_id=0, activity_id=""):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_get_json_schema -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_json_schema_acl_nologin(client, db_itemtype):
    url = url_for("weko_items_ui.get_json_schema", item_type_id=1, _external=True)
    res = client.get(url)
    assert res.status_code == 302


@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 200),
        (5, 200),
        (6, 200),
        (7, 200),
    ],
)
def test_get_json_schema_acl(client, users, db_itemtype, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_items_ui.get_json_schema", item_type_id=1, _external=True)
    res = client.get(url)
    assert res.status_code == status_code


# def get_schema_form(item_type_id=0, activity_id=''):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_get_schema_form_acl_nologin -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_schema_form_acl_nologin(client, db_itemtype):
    url = url_for("weko_items_ui.get_schema_form", item_type_id=1, _external=True)
    res = client.get(url)
    assert res.status_code == 302


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_get_schema_form_acl -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 200),
        (5, 200),
        (6, 200),
        (7, 200),
    ],
)
def test_get_schema_form_acl(client, users, db_itemtype, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_items_ui.get_schema_form", item_type_id=1, _external=True)
    res = client.get(url)
    assert res.status_code == status_code


# def items_index(pid_value='0'):

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_items_index_acl_nologin -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_items_index_acl_nologin(client, db_records):
    url = url_for("weko_items_ui.items_index", pid_value=1, _external=True)
    res = client.get(url)
    assert res.status_code == 302

    res = client.put(url)
    assert res.status_code == 302

    res = client.post(url)
    assert res.status_code == 302


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_items_index_acl -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 403),
        (5, 403),
        (6, 200),
        (7, 403),
    ],
)
def test_items_index_acl(client, db_records, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    depid, recid, parent, doi, record, item = db_records[0]
    url = url_for("weko_items_ui.items_index", pid_value=depid.id, _external=True)
    with patch("flask.templating._render", return_value=""):
        res = client.get(url)
        assert res.status_code == status_code

    # TODO POST, PUT
    # headers = {'content-type': 'application/json'}
    # res = client.put(url,data=json.dumps("{}"),headers=headers)
    # assert res.status_code == status_code
    # assert res.data==""

    # res = client.post(url)
    # assert res.status_code == status_code
    # assert res.data==""


# def iframe_items_index(pid_value='0'):

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_iframe_items_index_acl_nologin -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_iframe_items_index_acl_nologin(client, db_records):
    url = url_for("weko_items_ui.iframe_items_index", pid_value="1", _external=True)
    res = client.get(url)
    assert res.status_code == 302

    res = client.put(url)
    assert res.status_code == 302

    res = client.post(url)
    assert res.status_code == 302


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_iframe_items_index_acl -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 302),
        (1, 302),
        (2, 302),
        (3, 302),
        (4, 302),
        (5, 302),
        (6, 302),
        (7, 302),
    ],
)
def test_iframe_items_index_acl(app, client, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])

    url = url_for("weko_items_ui.iframe_items_index", pid_value=str(0), _external=True)
    res = client.get(url)
    assert res.status_code == 302


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_test_iframe_items_index -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp


def test_test_iframe_items_index(app, client, users, db_records, db_activity):
    login_user_via_session(client=client, email=users[0]["email"])

    url = url_for("weko_items_ui.iframe_items_index", pid_value=str(1), _external=True)

    with patch("weko_workflow.api.GetCommunity.get_community_by_id", return_value="c"):
        with client.session_transaction() as session:
            session["itemlogin_community_id"] = "c"
        res = client.get(url)
        assert res.status_code == 400

    with client.session_transaction() as session:
        session["itemlogin_activity"] = None
    res = client.get(url)
    assert res.status_code == 400

    with client.session_transaction() as session:
        session["itemlogin_activity"] = db_activity["activity"]
    res = client.get(url)
    assert res.status_code == 400

    # depid, recid,parent,doi,record, item  = db_records[0]
    # app.config['PRESERVE_CONTEXT_ON_EXCEPTION']=False
    # app.config['TESTING'] = True
    # depid, recid,parent,doi,record, item  = db_records[0]
    # action = db_workflow['flow_action2']
    # url = url_for('weko_items_ui.iframe_items_index',pid_value=str(depid.pid_value),_external=True)
    # with app.test_request_context(url_for('weko_items_ui.iframe_items_index',pid_value=str(depid.pid_value))):
    #     login_user(users[id]['obj'])
    #     activity_data = {
    #             'itemtype_id': 1,
    #             'workflow_id': 1,
    #             'flow_id': 1,
    #             'activity_confirm_term_of_use': True,
    #             'extra_info': {}
    #         }

    #     activity = WorkActivity().init_activity(activity_data)
    #     with patch('flask.templating._render', return_value=''):
    #         with client.session_transaction() as session:
    #             session['itemlogin_activity'] = activity
    #             session['itemlogin_record']=[]
    #             # session['itemlogin_setps'] = [{'ActivityId': 'A-20220827-00002', 'ActionId': 1, 'ActionName': 'Start', 'ActionVersion': '1.0.0', 'ActionEndpoint': 'begin_action', 'Author': 'wekosoftware@nii.ac.jp', 'Status': 'action_done', 'ActionOrder': 1}, {'ActivityId': 'A-20220827-00002', 'ActionId': 3, 'ActionName': 'Item Registration', 'ActionVersion': '1.0.1', 'ActionEndpoint': 'item_login', 'Author': '', 'Status': ' ', 'ActionOrder': 2}, {'ActivityId': 'A-20220827-00002', 'ActionId': 5, 'ActionName': 'Item Link', 'ActionVersion': '1.0.1', 'ActionEndpoint': 'item_link', 'Author': '', 'Status': ' ', 'ActionOrder': 3}, {'ActivityId': 'A-20220827-00002', 'ActionId': 7, 'ActionName': 'Identifier Grant', 'ActionVersion': '1.0.0', 'ActionEndpoint': 'identifier_grant', 'Author': '', 'Status': ' ', 'ActionOrder': 4}, {'ActivityId': 'A-20220827-00002', 'ActionId': 4, 'ActionName': 'Approval', 'ActionVersion': '2.0.0', 'ActionEndpoint': 'approval', 'Author': '', 'Status': ' ', 'ActionOrder': 5}, {'ActivityId': 'A-20220827-00002', 'ActionId': 2, 'ActionName': 'End', 'ActionVersion': '1.0.0', 'ActionEndpoint': 'end_action', 'Author': '', 'Status': ' ', 'ActionOrder': 6}]
    #         res = client.get(url)
    #         assert res.status_code == status_code

    # TODO POST, PUT
    # headers = {'content-type': 'application/json'}
    # res = client.put(url,data=json.dumps("{}"),headers=headers)
    # assert res.status_code == status_code
    # assert res.data==""

    # res = client.post(url)
    # assert res.status_code == status_code
    # assert res.data==""


# def default_view_method(pid, record, template=None):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_default_view_method -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_default_view_method(app, db_records):
    depid, recid, parent, doi, record, item = db_records[0]
    with app.test_request_context():
        with patch("flask.templating._render", return_value=""):
            assert default_view_method(depid.id, record) == ""


# def to_links_js(pid):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_to_links_js -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_to_links_js(app, db_records):
    depid, recid, parent, doi, record, item = db_records[0]
    assert to_links_js(depid) == {
        "self": "/api/deposits/items/1",
        "ret": "http://test_server/items/",
        "index": "/api/deposits/redirect/1",
        "r": "/items/index/1",
        "iframe_tree": "/items/iframe/index/1",
        "iframe_tree_upgrade": "/items/iframe/index/1.2",
    }


# def index_upload():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_index_upload_acl_nologin -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_index_upload_acl_nologin(client, db_sessionlifetime):
    url = url_for("weko_items_ui.index_upload", _external=True)
    res = client.get(url)
    assert res.status_code == 302


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_index_upload_acl -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 200),
        (5, 200),
        (6, 200),
        (7, 200),
    ],
)
def test_index_upload_acl(client, db_sessionlifetime, users, id, status_code):
    login_user_via_session(client=client, email=users[id]["email"])
    url = url_for("weko_items_ui.index_upload", _external=True)
    with patch("flask.templating._render", return_value=""):
        res = client.get(url)
        assert res.status_code == status_code


# def get_search_data(data_type=''):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_get_search_data_acl -v -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_search_data_acl(client_api, db_sessionlifetime):
    url = url_for(
        "weko_items_ui_api.get_search_data", data_type="username", _external=True
    )
    res = client_api.get(url)
    assert res.status_code == 200
    url = url_for(
        "weko_items_ui_api.get_search_data", data_type="email", _external=True
    )
    res = client_api.get(url)
    assert res.status_code == 200


# def validate_user_email_and_index():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_validate_user_email_and_index_login -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp


@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 200),
        (5, 200),
        (6, 200),
        (7, 200),
    ],
)
def test_validate_user_email_and_index_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    with patch("weko_items_ui.views.validate_user_mail_and_index", return_value=""):
        res = client_api.post(
            "/api/items/validate_email_and_index",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert res.status_code == status_code


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_validate_user_email_and_index_guest -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_validate_user_email_and_index_guest(client_api, users):
    with patch("weko_items_ui.views.validate_user_mail_and_index", return_value=""):
        res = client_api.post(
            "/api/items/validate_email_and_index",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert res.status_code == 200


# def validate_user_info():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_validate_user_info_login -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 200),
        (5, 200),
        (6, 200),
        (7, 200),
    ],
)
def test_validate_user_info_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    res = client_api.post(
        "/api/items/validate_user_info",
        data=json.dumps({"username": "", "email": ""}),
        content_type="application/json",
    )
    assert res.status_code == status_code


#  .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_validate_user_info_guest -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_validate_user_info_guest(client_api, users):
    res = client_api.post(
        "/api/items/validate_user_info",
        data=json.dumps({"username": "", "email": ""}),
        content_type="application/json",
    )
    assert res.status_code == 200


# def get_user_info(owner, shared_user_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_get_user_info_acl_nologin -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_user_info_acl_nologin(client_api, db_sessionlifetime):
    url = url_for(
        "weko_items_ui_api.get_user_info", owner=1, shared_user_id=1, _external=True
    )
    res = client_api.get(url)
    assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_get_user_info_acl -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 200),
        (5, 200),
        (6, 200),
        (7, 200),
    ],
)
def test_get_user_info_acl(client_api, db_sessionlifetime, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    url = url_for(
        "weko_items_ui_api.get_user_info", owner=1, shared_user_id=1, _external=True
    )
    res = client_api.get(url)
    assert res.status_code == status_code


# def get_current_login_user_id():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_get_current_login_user_id_acl -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_current_login_user_id_acl_nologin(client_api, db_sessionlifetime):
    url = url_for("weko_items_ui_api.get_current_login_user_id", _external=True)
    res = client_api.get(url)
    assert res.status_code == 200


@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 200),
        (5, 200),
        (6, 200),
        (7, 200),
    ],
)
def test_get_current_login_user_id_acl(
    client_api, db_sessionlifetime, users, id, status_code
):
    login_user_via_session(client=client_api, email=users[id]["email"])
    url = url_for("weko_items_ui_api.get_current_login_user_id", _external=True)
    res = client_api.get(url)
    assert res.status_code == status_code


# def prepare_edit_item():
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 200),
        (5, 200),
        (6, 200),
        (7, 200),
    ],
)
def test_prepare_edit_item_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    res = client_api.post(
        "/api/items/prepare_edit_item",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert res.status_code == status_code


def test_prepare_edit_item_guest(client_api, users):
    res = client_api.post(
        "/api/items/prepare_edit_item",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert res.status_code == 302


# def ranking():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_ranking_acl_nologin -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_ranking_acl_nologin(client, db_sessionlifetime):
    url = url_for("weko_items_ui.ranking", _external=True)
    with patch("flask.templating._render", return_value=""):
        res = client.get(url)
        assert res.status_code == 200


# def check_ranking_show():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_check_ranking_show -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_check_ranking_show():
    mock = MagicMock(
        id=0,
        is_show=True,
        new_item_period=14,
        statistical_period=365,
        display_rank=10,
        rankings={
            "new_items": True,
            "most_reviewed_items": True,
            "most_downloaded_items": True,
            "most_searched_keywords": True,
            "created_most_items_user": True,
        },
    )
    with patch("weko_admin.models.RankingSettings.get", return_value=mock):
        assert check_ranking_show() == ""

    mock = MagicMock(
        id=0,
        is_show=False,
        new_item_period=14,
        statistical_period=365,
        display_rank=10,
        rankings={
            "new_items": True,
            "most_reviewed_items": True,
            "most_downloaded_items": True,
            "most_searched_keywords": True,
            "created_most_items_user": True,
        },
    )
    with patch("weko_admin.models.RankingSettings.get", return_value=mock):
        assert check_ranking_show() == "hide"


# def check_restricted_content():
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 200),
        (5, 200),
        (6, 200),
        (7, 200),
    ],
)
def test_check_restricted_content_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    res = client_api.post(
        "/api/items/check_restricted_content",
        data=json.dumps({"record_ids": []}),
        content_type="application/json",
    )
    assert res.status_code == status_code


def test_check_restricted_content_guest(client_api, users):
    res = client_api.post(
        "/api/items/check_restricted_content",
        data=json.dumps({"record_ids": []}),
        content_type="application/json",
    )
    assert res.status_code == 200


# def validate_bibtex_export():
# MEMO: weko-schema-ui/weko_schema_ui/serializers/WekoBibTexSerializer.py:133: KeyError
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_validate_bibtex_export_acl_nologin -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_validate_bibtex_export_acl_nologin(
    app, client, users, db_records, db_oaischema
):
    url = url_for("weko_items_ui.validate_bibtex_export", _external=True)
    res = client.post(
        url, data=json.dumps({"record_ids": [1]}), content_type="application/json"
    )
    assert res.status_code == 200


# def export():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_export_acl_nologin -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_export_acl_nologin(client, users, db_oaischema):
    url = url_for("weko_items_ui.export", _external=True)
    with patch("flask.templating._render", return_value=""):
        res = client.get(url)
        assert res.status_code == 200


# def validate():
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 200),
        (5, 200),
        (6, 200),
        (7, 200),
    ],
)
def test_validate_login(client_api, users, id, status_code):
    login_user_via_session(client=client_api, email=users[id]["email"])
    url = url_for("weko_items_ui_api.validate", _external=True)
    with patch("weko_items_ui.views.validate_form_input_data", return_value=""):
        res = client_api.post(url, data=json.dumps({}), content_type="application/json")
        assert res.status_code == status_code


def test_validate_guest(client_api, users):
    url = url_for("weko_items_ui_api.validate", _external=True)
    with patch("weko_items_ui.views.validate_form_input_data", return_value=""):
        res = client_api.post(url, data=json.dumps({}), content_type="application/json")
        assert res.status_code == 302


# def check_validation_error_msg(activity_id):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_check_validation_error_msg_acl_nologin -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_check_validation_error_msg_acl_nologin(client_api, db_sessionlifetime):
    url = url_for(
        "weko_items_ui_api.check_validation_error_msg",
        activity_id="A-00000000-00000",
        external=True,
    )
    res = client_api.get(url)
    assert res.status_code == 302


# def corresponding_activity_list():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_corresponding_activity_list_acl_nologin -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_corresponding_activity_list_acl_nologin(client, db_sessionlifetime):
    url = url_for("weko_items_ui.corresponding_activity_list", _external=True)
    res = client.get(url)
    assert res.status_code == 302


# def get_authors_prefix_settings():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_get_authors_prefix_settings_acl_nologin -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_authors_prefix_settings_acl_nologin(client_api, db_sessionlifetime):
    url = url_for("weko_items_ui_api.get_authors_prefix_settings", _external=True)
    res = client_api.get(url)
    assert res.status_code == 200


# def get_authors_affiliation_settings():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_get_authors_affiliation_settings_acl_nologin -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_get_authors_affiliation_settings_acl_nologin(client_api, db_sessionlifetime):
    url = url_for("weko_items_ui_api.get_authors_affiliation_settings", _external=True)
    res = client_api.get(url)
    assert res.status_code == 200


# def session_validate():
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_session_validate_acl_nologin -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_session_validate_acl_nologin(app, client, db_sessionlifetime):
    url = url_for("weko_items_ui.session_validate", _external=True)
    res = client.post(url)
    assert res.status_code == 200


# def check_record_doi(pid_value='0'):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_check_record_doi_acl_nologin -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_check_record_doi_acl_nologin(client_api, db_sessionlifetime):
    url = url_for("weko_items_ui_api.check_record_doi", pid_value="1", _external=True)
    res = client_api.get(url)
    assert res.status_code == 302


# def check_record_doi_indexes(pid_value='0'):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_check_record_doi_indexes_acl_nologin -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_check_record_doi_indexes_acl_nologin(client_api, db_sessionlifetime):
    url = url_for(
        "weko_items_ui_api.check_record_doi_indexes", pid_value=0, _external=True
    )
    res = client_api.get(url)
    assert res.status_code == 302


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_check_record_doi_indexes_acl -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
        (1, 200),
        (2, 200),
        (3, 200),
        (4, 200),
        (5, 200),
        (6, 200),
        (7, 200),
    ],
)
def test_check_record_doi_indexes_acl(
    client_api, users, db_records, db_sessionlifetime, id, status_code
):
    login_user_via_session(client=client_api, email=users[id]["email"])
    url = url_for(
        "weko_items_ui_api.check_record_doi_indexes", pid_value=1, _external=True
    )
    res = client_api.get(url)
    assert res.status_code == status_code


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_views.py::test_check_record_doi_indexes -v --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize(
    "id, status_code",
    [
        (0, 200),
    ],
)
def test_check_record_doi_indexes(
    client_api, users, db_records, db_sessionlifetime, id, status_code
):
    login_user_via_session(client=client_api, email=users[id]["email"])
    url = url_for(
        "weko_items_ui_api.check_record_doi_indexes", pid_value=1, _external=True
    )
    res = client_api.get(url)
    assert res.status_code == status_code
    assert res.data == b'{"code":-1}\n'
    res = client_api.get("{}?doi=1".format(url))
    assert res.status_code == status_code
    assert res.data == b'{"code":-1}\n'
