# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Module tests."""
from re import M
import threading
from traceback import print_tb
from typing_extensions import Self
from unittest.mock import MagicMock
from weko_workflow.api import WorkActivity
import pytest
from mock import patch
from sqlalchemy.orm.attributes import flag_modified

from flask import Flask, json, jsonify, url_for, session, make_response, current_app
from flask_babelex import gettext as _
from invenio_db import db
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import uuid
from invenio_communities.models import Community
from invenio_pidstore.errors import PIDDoesNotExistError,PIDDeletedError
from invenio_pidstore.models import PersistentIdentifier, PIDStatus

from invenio_cache import current_cache

import weko_workflow.utils
from weko_workflow import WekoWorkflow
from weko_workflow.config import WEKO_WORKFLOW_TODO_TAB, WEKO_WORKFLOW_WAIT_TAB,WEKO_WORKFLOW_ALL_TAB
from flask_security import login_user
from invenio_accounts.testutils import login_user_via_session as login
from weko_workflow.models import ActionStatusPolicy, ActionFeedbackMail, ActionJournal, ActionIdentifier, Activity, ActivityHistory, ActionStatus, Action, WorkFlow, FlowDefine, FlowAction,FlowActionRole, ActivityAction, GuestActivity
from weko_workflow.views import unlock_activity, check_approval, get_feedback_maillist, save_activity, previous_action,_generate_download_url,check_authority_action
from marshmallow.exceptions import ValidationError
from weko_records_ui.models import FileOnetimeDownload, FilePermission
from weko_records.models import ItemMetadata, ItemReference
from invenio_records.models import RecordMetadata
from tests.helpers import create_record



def response_data(response):
    return json.loads(response.data)

# .tox/c1/bin/pytest --cov=weko_workspace tests/test_views.py::test_itemregister -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-weko_workspace/.tox/c1/tmp
def test_itemregister(db,users, workflow, app, client,mocker,without_remove_session):
    # ワークフローを経由で
    admin_settings = {"workFlow_select_flg": '0', "work_flow_id": '1'}
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    from types import SimpleNamespace
    settings_obj = SimpleNamespace(**admin_settings)
    mocker.patch("weko_workspace.views.session",session)
    with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
        url = url_for("weko_workspace.itemregister")
        res = client.get(url, json=admin_settings)
        assert res is not None

    # item_type is None
    admin_settings = {"workFlow_select_flg": '0', "work_flow_id": '1'}

    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    from types import SimpleNamespace
    settings_obj = SimpleNamespace(**admin_settings)
    mocker.patch("weko_workspace.views.session",session)
    with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
        # with patch("weko_records.api.ItemTypes", return_value=None):
        with patch("weko_records.api.ItemTypes.get_by_id", return_value=None):
            url = url_for("weko_workspace.itemregister")
            res = client.get(url, json=admin_settings)
            assert res.status_code == 404


    # 直接登録
    admin_settings = {"workFlow_select_flg": '1', "item_type_id": '1'}
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    from types import SimpleNamespace
    settings_obj = SimpleNamespace(**admin_settings)
    mocker.patch("weko_workspace.views.session",session)
    with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
        url = url_for("weko_workspace.itemregister")
        res = client.get(url, json=admin_settings)
        assert res is not None
    
        # item_type is None
    admin_settings = {"workFlow_select_flg": '1', "item_type_id": '1'}

    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    from types import SimpleNamespace
    settings_obj = SimpleNamespace(**admin_settings)
    mocker.patch("weko_workspace.views.session",session)
    with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
        # with patch("weko_records.api.ItemTypes", return_value=None):
        with patch("weko_records.api.ItemTypes.get_by_id", return_value=None):
            url = url_for("weko_workspace.itemregister")
            res = client.get(url, json=admin_settings)
            assert res.status_code == 404


# .tox/c1/bin/pytest --cov=weko_workspace tests/test_views.py::test_get_auto_fill_record_data_ciniiapi -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-weko_workspace/.tox/c1/tmp
def test_get_auto_fill_record_data_ciniiapi(db,users, workflow,client_api, client,mocker,without_remove_session):
    # data あり
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    from mock import MagicMock, patch, PropertyMock
    from unittest.mock import patch, Mock, MagicMock
    import os
    item_type = Mock()
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_render.json"
    )
    with open(filepath, encoding="utf-8") as f:
        render = json.load(f)
    item_type.render = render

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_schema.json"
    )
    with open(filepath, encoding="utf-8") as f:
        schema = json.load(f)
    item_type.schema = schema

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_form.json"
    )
    with open(filepath, encoding="utf-8") as f:
        form = json.load(f)
    item_type.form = form

    item_type.item_type_name.name="デフォルトアイテムタイプ（フル）"
    item_type.item_type_name.item_type.first().id=15
    data = {
        "search_data":"10.5109/16119",
        "item_type_id":"1"
    }

    mocker.patch("weko_workspace.views.session",session)
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=item_type):
        with patch("weko_workspace.utils.get_cinii_record_data", return_value={"result":"","items":"test","error":""}):
            url = url_for("weko_workspace_api.get_auto_fill_record_data_ciniiapi")
            res = client.post(url, 
                        data=json.dumps(data),
                        content_type='application/json')
            assert res.status_code == 200
            assert res is not None

    # header error
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }

    data = {
        "search_data":"10.5109/16119",
        "item_type_id":"15"
    }

    mocker.patch("weko_workspace.views.session",session)
    url = url_for("weko_workspace_api.get_auto_fill_record_data_ciniiapi")
    res = client.post(url, 
                data=json.dumps(data),
                content_type='test/json')
    assert res.status_code == 200


    # not exist
    data = {
        "search_data":"test",
        "item_type_id":"15"
    }

    mocker.patch("weko_workspace.views.session",session)
    url = url_for("weko_workspace_api.get_auto_fill_record_data_ciniiapi")
    res = client.post(url, 
                data=json.dumps(data),
                content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data) == {"result":[],"items":"","error":""}


# .tox/c1/bin/pytest --cov=weko_workspace tests/test_views.py::test_get_auto_fill_record_data_jalcapi -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-weko_workspace/.tox/c1/tmp
def test_get_auto_fill_record_data_jalcapi(db,users, workflow,client_api, client,mocker,without_remove_session):
    # data あり
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    from mock import MagicMock, patch, PropertyMock
    from unittest.mock import patch, Mock, MagicMock
    import os
    item_type = Mock()
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_render.json"
    )
    with open(filepath, encoding="utf-8") as f:
        render = json.load(f)
    item_type.render = render

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_schema.json"
    )
    with open(filepath, encoding="utf-8") as f:
        schema = json.load(f)
    item_type.schema = schema

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_form.json"
    )
    with open(filepath, encoding="utf-8") as f:
        form = json.load(f)
    item_type.form = form

    item_type.item_type_name.name="デフォルトアイテムタイプ（フル）"
    item_type.item_type_name.item_type.first().id=15
    data = {
        "search_data":"10.5109/16119",
        "item_type_id":"1"
    }

    mocker.patch("weko_workspace.views.session",session)
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=item_type):
        with patch("weko_workspace.utils.get_jalc_record_data", return_value={"result":"","items":"test","error":""}):
            url = url_for("weko_workspace_api.get_auto_fill_record_data_jalcapi")
            res = client.post(url, 
                        data=json.dumps(data),
                        content_type='application/json')
            assert res.status_code == 200
            assert res is not None

    # header error
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }

    data = {
        "search_data":"10.5109/16119",
        "item_type_id":"15"
    }

    mocker.patch("weko_workspace.views.session",session)
    url = url_for("weko_workspace_api.get_auto_fill_record_data_jalcapi")
    res = client.post(url, 
                data=json.dumps(data),
                content_type='test/json')
    assert res.status_code == 200


    # not exist
    data = {
        "search_data":"test",
        "item_type_id":"15"
    }

    mocker.patch("weko_workspace.views.session",session)
    url = url_for("weko_workspace_api.get_auto_fill_record_data_jalcapi")
    res = client.post(url, 
                data=json.dumps(data),
                content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data) == {"result":[],"items":"","error":""}


# .tox/c1/bin/pytest --cov=weko_workspace tests/test_views.py::test_get_auto_fill_record_data_dataciteapi -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-weko_workspace/.tox/c1/tmp
def test_get_auto_fill_record_data_dataciteapi(db,users, workflow,client_api, client,mocker,without_remove_session):
    # data あり
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }
    from mock import MagicMock, patch, PropertyMock
    from unittest.mock import patch, Mock, MagicMock
    import os
    item_type = Mock()
    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_render.json"
    )
    with open(filepath, encoding="utf-8") as f:
        render = json.load(f)
    item_type.render = render

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_schema.json"
    )
    with open(filepath, encoding="utf-8") as f:
        schema = json.load(f)
    item_type.schema = schema

    filepath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "item_type/15_form.json"
    )
    with open(filepath, encoding="utf-8") as f:
        form = json.load(f)
    item_type.form = form

    item_type.item_type_name.name="デフォルトアイテムタイプ（フル）"
    item_type.item_type_name.item_type.first().id=15
    data = {
        "search_data":"10.14454/FXWS-0523",
        "item_type_id":"1"
    }

    mocker.patch("weko_workspace.views.session",session)
    with patch("weko_records.api.ItemTypes.get_by_id", return_value=item_type):
        with patch("weko_workspace.utils.get_datacite_record_data", return_value={"result":"","items":"test","error":""}):
            url = url_for("weko_workspace_api.get_auto_fill_record_data_dataciteapi")
            res = client.post(url, 
                        data=json.dumps(data),
                        content_type='application/json')
            assert res.status_code == 200
            assert res is not None

    # header error
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }

    data = {
        "search_data":"10.5109/16119",
        "item_type_id":"15"
    }

    mocker.patch("weko_workspace.views.session",session)
    url = url_for("weko_workspace_api.get_auto_fill_record_data_dataciteapi")
    res = client.post(url, 
                data=json.dumps(data),
                content_type='test/json')
    assert res.status_code == 200


    # not exist
    data = {
        "search_data":"test",
        "item_type_id":"15"
    }

    mocker.patch("weko_workspace.views.session",session)
    url = url_for("weko_workspace_api.get_auto_fill_record_data_dataciteapi")
    res = client.post(url, 
                data=json.dumps(data),
                content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data) == {"result":[],"items":"","error":""}


# .tox/c1/bin/pytest --cov=weko_workspace tests/test_views.py::test_itemregister_save -v -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-weko_workspace/.tox/c1/tmp
def test_itemregister_save(db,users, workflow, app, client,mocker,without_remove_session):
    # # ワークフローを経由で
    # admin_settings = {"workFlow_select_flg": '0', "work_flow_id": '1'}
    # login(client=client, email=users[0]['email'])
    # session = {
    #     "itemlogin_id":"1",
    #     "itemlogin_action_id":3,
    #     "itemlogin_cur_step":"item_login",
    #     "itemlogin_community_id":"comm01"
    # }

    # index_metadata = {
    #     "id": 2,
    #     "parent": 1,
    #     "position": 1,
    #     "index_name": "test-weko",
    #     "index_name_english": "Contents Type",
    #     "index_link_name": "",
    #     "index_link_name_english": "New Index",
    #     "index_link_enabled": False,
    #     "more_check": False,
    #     "display_no": 5,
    #     "harvest_public_state": True,
    #     "display_format": 1,
    #     "image_name": "",
    #     "public_state": True,
    #     "recursive_public_state": True,
    #     "rss_status": False,
    #     "coverpage_state": False,
    #     "recursive_coverpage_check": False,
    #     "browsing_role": "3,-98,-99",
    #     "recursive_browsing_role": False,
    #     "contribute_role": "1,2,3,4,-98,-99",
    #     "recursive_contribute_role": False,
    #     "browsing_group": "",
    #     "recursive_browsing_group": False,
    #     "recursive_contribute_group": False,
    #     "owner_user_id": 1,
    #     "item_custom_sort": {"2": 1}
    # }
    # from weko_index_tree.models import Index
    # index = Index(**index_metadata)

    # with db.session.begin_nested():
    #     db.session.add(index)

    # from types import SimpleNamespace
    # settings_obj = SimpleNamespace(**admin_settings)
    # mocker.patch("weko_workspace.views.session",session)
    # data = {
    #     "recordModel":{'pubdate': '2025-03-11', 'item_30002_title0': [{'subitem_title': 'Identification of cDNA Sequences Encoding the Complement Components of Zebrafish (Danio rerio)', 'subitem_title_language': 'en'}], 'item_30002_creator2': [{'creatorNames': [{'creatorName': 'Vo Kha Tam', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Tsujikura Masakazu', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Somamoto Tomonori', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Nakano Miki', 'creatorNameLang': 'en'}]}], 'item_30002_identifier16': [{'subitem_identifier_uri': '10.5109/16119'}], 'item_30002_relation18': [{'subitem_relation_type_id': {'subitem_relation_type_id_text': '10.5109/16119', 'subitem_relation_type_select': 'DOI'}}], 'item_30002_funding_reference21': [{'subitem_funder_names': [{'subitem_funder_name': 'test1'}]}], 'item_30002_conference34': [{'subitem_conference_names': [{'subitem_conference_name': 'test3'}]}], 'item_30002_file35': [{'version_id': '9e7f93b3-7290-4a6f-aea0-87856279cf48', 'filename': '1_1.png', 'filesize': [{'value': '55 KB'}], 'format': 'image/png', 'date': [{'dateValue': '2025-03-11', 'dateType': 'Available'}], 'accessrole': 'open_access', 'url': {'url': 'https://192.168.56.106/record/2000235/files/1_1.png'}}], 'item_30002_bibliographic_information29': {'bibliographic_titles': [{'bibliographic_title': 'test2'}]}, 'item_30002_source_title23': [{'subitem_source_title': 'Journal of the Faculty of Agriculture, Kyushu University', 'subitem_source_title_language': 'en'}], 'item_30002_source_identifier22': [{'subitem_source_identifier': '0023-6152', 'subitem_source_identifier_type': 'ISSN'}], 'item_30002_volume_number24': {'subitem_volume': '54'}, 'item_30002_issue_number25': {'subitem_issue': '2'}, 'item_30002_page_start27': {'subitem_start_page': '373'}, 'item_30002_page_end28': {'subitem_end_page': '387'}, 'item_30002_date11': [{'subitem_date_issued_datetime': '2009', 'subitem_date_issued_type': 'Issued'}], 'item_30002_access_rights4': {'subitem_access_right': 'embargoed access'}, 'item_30002_resource_type13': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_30002_version_type15': {'subitem_version_type': 'AO'}, 'deleted_items': []},
    #     "indexlist":['test-weko']
    # }
    # with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
    #     url = url_for("weko_workspace.workflow_registration")
    #     res = client.post(url, json=data)
    #     assert res is not None

    # # header error
    # login(client=client, email=users[0]['email'])
    # session = {
    #     "itemlogin_id":"1",
    #     "itemlogin_action_id":3,
    #     "itemlogin_cur_step":"item_login",
    #     "itemlogin_community_id":"comm01"
    # }

    # data = {
    #     "recordModel":{'pubdate': '2025-03-11', 'item_30002_title0': [{'subitem_title': 'Identification of cDNA Sequences Encoding the Complement Components of Zebrafish (Danio rerio)', 'subitem_title_language': 'en'}], 'item_30002_creator2': [{'creatorNames': [{'creatorName': 'Vo Kha Tam', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Tsujikura Masakazu', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Somamoto Tomonori', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Nakano Miki', 'creatorNameLang': 'en'}]}], 'item_30002_identifier16': [{'subitem_identifier_uri': '10.5109/16119'}], 'item_30002_relation18': [{'subitem_relation_type_id': {'subitem_relation_type_id_text': '10.5109/16119', 'subitem_relation_type_select': 'DOI'}}], 'item_30002_funding_reference21': [{'subitem_funder_names': [{'subitem_funder_name': 'test1'}]}], 'item_30002_conference34': [{'subitem_conference_names': [{'subitem_conference_name': 'test3'}]}], 'item_30002_file35': [{'version_id': '9e7f93b3-7290-4a6f-aea0-87856279cf48', 'filename': '1_1.png', 'filesize': [{'value': '55 KB'}], 'format': 'image/png', 'date': [{'dateValue': '2025-03-11', 'dateType': 'Available'}], 'accessrole': 'open_access', 'url': {'url': 'https://192.168.56.106/record/2000235/files/1_1.png'}}], 'item_30002_bibliographic_information29': {'bibliographic_titles': [{'bibliographic_title': 'test2'}]}, 'item_30002_source_title23': [{'subitem_source_title': 'Journal of the Faculty of Agriculture, Kyushu University', 'subitem_source_title_language': 'en'}], 'item_30002_source_identifier22': [{'subitem_source_identifier': '0023-6152', 'subitem_source_identifier_type': 'ISSN'}], 'item_30002_volume_number24': {'subitem_volume': '54'}, 'item_30002_issue_number25': {'subitem_issue': '2'}, 'item_30002_page_start27': {'subitem_start_page': '373'}, 'item_30002_page_end28': {'subitem_end_page': '387'}, 'item_30002_date11': [{'subitem_date_issued_datetime': '2009', 'subitem_date_issued_type': 'Issued'}], 'item_30002_access_rights4': {'subitem_access_right': 'embargoed access'}, 'item_30002_resource_type13': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_30002_version_type15': {'subitem_version_type': 'AO'}, 'deleted_items': []}
    # }

    # mocker.patch("weko_workspace.views.session",session)
    # url = url_for("weko_workspace.workflow_registration")
    # res = client.post(url, 
    #             data=json.dumps(data),
    #             content_type='test/json')
    # assert res.status_code == 200

    # # error
    # admin_settings = {"workFlow_select_flg": '0', "work_flow_id": '1'}
    # login(client=client, email=users[0]['email'])
    # session = {
    #     "itemlogin_id":"1",
    #     "itemlogin_action_id":3,
    #     "itemlogin_cur_step":"item_login",
    #     "itemlogin_community_id":"comm01"
    # }
    # from types import SimpleNamespace
    # settings_obj = SimpleNamespace(**admin_settings)
    # mocker.patch("weko_workspace.views.session",session)
    # data = {
    #     "recordModel":{}
    # }
    # with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
    #     url = url_for("weko_workspace.workflow_registration")
    #     res = client.post(url, json=data)
    #     assert res is not None


    # # data is None
    # admin_settings = {"workFlow_select_flg": '0', "work_flow_id": '1'}

    # login(client=client, email=users[0]['email'])
    # session = {
    #     "itemlogin_id":"1",
    #     "itemlogin_action_id":3,
    #     "itemlogin_cur_step":"item_login",
    #     "itemlogin_community_id":"comm01"
    # }
    # data = {
    #     "recordModel":{'pubdate': '2025-03-11', 'item_30002_title0': [{'subitem_title': 'Identification of cDNA Sequences Encoding the Complement Components of Zebrafish (Danio rerio)', 'subitem_title_language': 'en'}], 'item_30002_creator2': [{'creatorNames': [{'creatorName': 'Vo Kha Tam', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Tsujikura Masakazu', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Somamoto Tomonori', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Nakano Miki', 'creatorNameLang': 'en'}]}], 'item_30002_identifier16': [{'subitem_identifier_uri': '10.5109/16119'}], 'item_30002_relation18': [{'subitem_relation_type_id': {'subitem_relation_type_id_text': '10.5109/16119', 'subitem_relation_type_select': 'DOI'}}], 'item_30002_funding_reference21': [{'subitem_funder_names': [{'subitem_funder_name': 'test1'}]}], 'item_30002_conference34': [{'subitem_conference_names': [{'subitem_conference_name': 'test3'}]}], 'item_30002_file35': [{'version_id': '9e7f93b3-7290-4a6f-aea0-87856279cf48', 'filename': '1_1.png', 'filesize': [{'value': '55 KB'}], 'format': 'image/png', 'date': [{'dateValue': '2025-03-11', 'dateType': 'Available'}], 'accessrole': 'open_access', 'url': {'url': 'https://192.168.56.106/record/2000235/files/1_1.png'}}], 'item_30002_bibliographic_information29': {'bibliographic_titles': [{'bibliographic_title': 'test2'}]}, 'item_30002_source_title23': [{'subitem_source_title': 'Journal of the Faculty of Agriculture, Kyushu University', 'subitem_source_title_language': 'en'}], 'item_30002_source_identifier22': [{'subitem_source_identifier': '0023-6152', 'subitem_source_identifier_type': 'ISSN'}], 'item_30002_volume_number24': {'subitem_volume': '54'}, 'item_30002_issue_number25': {'subitem_issue': '2'}, 'item_30002_page_start27': {'subitem_start_page': '373'}, 'item_30002_page_end28': {'subitem_end_page': '387'}, 'item_30002_date11': [{'subitem_date_issued_datetime': '2009', 'subitem_date_issued_type': 'Issued'}], 'item_30002_access_rights4': {'subitem_access_right': 'embargoed access'}, 'item_30002_resource_type13': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_30002_version_type15': {'subitem_version_type': 'AO'}, 'deleted_items': []}
    # }
    # from types import SimpleNamespace
    # settings_obj = SimpleNamespace(**admin_settings)
    # mocker.patch("weko_workspace.views.session",session)
    # with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
    #     # with patch("weko_records.api.ItemTypes", return_value=None):
    #     with patch("weko_workflow.headless.activity.HeadlessActivity.auto", return_value=None):
    #         url = url_for("weko_workspace.workflow_registration")
    #         res = client.post(url, json=data)
    #         assert res.status_code == 200


    # # 直接登録
    # ワークフローを経由で
    admin_settings = {"workFlow_select_flg": '1', "item_type_id": '1'}
    login(client=client, email=users[0]['email'])
    session = {
        "itemlogin_id":"1",
        "itemlogin_action_id":3,
        "itemlogin_cur_step":"item_login",
        "itemlogin_community_id":"comm01"
    }

    index_metadata = {
        "id": 3,
        "parent": 1,
        "position": 2,
        "index_name": "test-weko",
        "index_name_english": "Contents Type",
        "index_link_name": "",
        "index_link_name_english": "New Index",
        "index_link_enabled": False,
        "more_check": False,
        "display_no": 5,
        "harvest_public_state": True,
        "display_format": 1,
        "image_name": "",
        "public_state": True,
        "recursive_public_state": True,
        "rss_status": False,
        "coverpage_state": False,
        "recursive_coverpage_check": False,
        "browsing_role": "3,-98,-99",
        "recursive_browsing_role": False,
        "contribute_role": "1,2,3,4,-98,-99",
        "recursive_contribute_role": False,
        "browsing_group": "",
        "recursive_browsing_group": False,
        "recursive_contribute_group": False,
        "owner_user_id": 1,
        "item_custom_sort": {"2": 1}
    }
    from weko_index_tree.models import Index
    index = Index(**index_metadata)

    with db.session.begin_nested():
        db.session.add(index)
    return_value = {
            "success":True,
            "error_id":None,
        }
    from types import SimpleNamespace
    settings_obj = SimpleNamespace(**admin_settings)
    mocker.patch("weko_workspace.views.session",session)
    data = {
        # "recordModel":{'pubdate': '2025-03-11', 'item_30002_title0': [{'subitem_title': 'Identification of cDNA Sequences Encoding the Complement Components of Zebrafish (Danio rerio)', 'subitem_title_language': 'en'}], 'item_30002_creator2': [{'creatorNames': [{'creatorName': 'Vo Kha Tam', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Tsujikura Masakazu', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Somamoto Tomonori', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Nakano Miki', 'creatorNameLang': 'en'}]}], 'item_30002_identifier16': [{'subitem_identifier_uri': '10.5109/16119'}], 'item_30002_relation18': [{'subitem_relation_type_id': {'subitem_relation_type_id_text': '10.5109/16119', 'subitem_relation_type_select': 'DOI'}}], 'item_30002_funding_reference21': [{'subitem_funder_names': [{'subitem_funder_name': 'test1'}]}], 'item_30002_conference34': [{'subitem_conference_names': [{'subitem_conference_name': 'test3'}]}], 'item_30002_file35': [{'version_id': '9e7f93b3-7290-4a6f-aea0-87856279cf48', 'filename': '1_1.png', 'filesize': [{'value': '55 KB'}], 'format': 'image/png', 'date': [{'dateValue': '2025-03-11', 'dateType': 'Available'}], 'accessrole': 'open_access', 'url': {'url': 'https://192.168.56.106/record/2000235/files/1_1.png'}}], 'item_30002_bibliographic_information29': {'bibliographic_titles': [{'bibliographic_title': 'test2'}]}, 'item_30002_source_title23': [{'subitem_source_title': 'Journal of the Faculty of Agriculture, Kyushu University', 'subitem_source_title_language': 'en'}], 'item_30002_source_identifier22': [{'subitem_source_identifier': '0023-6152', 'subitem_source_identifier_type': 'ISSN'}], 'item_30002_volume_number24': {'subitem_volume': '54'}, 'item_30002_issue_number25': {'subitem_issue': '2'}, 'item_30002_page_start27': {'subitem_start_page': '373'}, 'item_30002_page_end28': {'subitem_end_page': '387'}, 'item_30002_date11': [{'subitem_date_issued_datetime': '2009', 'subitem_date_issued_type': 'Issued'}], 'item_30002_access_rights4': {'subitem_access_right': 'embargoed access'}, 'item_30002_resource_type13': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_30002_version_type15': {'subitem_version_type': 'AO'}, 'deleted_items': []},
        "recordModel":{'pubdate': '2025-03-11', 'item_30002_title0': [{'subitem_title': 'Identification of cDNA Sequences Encoding the Complement Components of Zebrafish (Danio rerio)', 'subitem_title_language': 'en'}], 'item_30002_creator2': [{'creatorNames': [{'creatorName': 'Vo Kha Tam', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Tsujikura Masakazu', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Somamoto Tomonori', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Nakano Miki', 'creatorNameLang': 'en'}]}], 'item_30002_relation18': [{'subitem_relation_type_id': {'subitem_relation_type_id_text': '10.5109/16119', 'subitem_relation_type_select': 'DOI'}}], 'item_30002_file35': [{'date': [{'dateValue': '2025-03-11'}], 'url': {'url': 'https://192.168.56.106/record/2000235/files/1_1.png'}}], 'item_30002_source_title23': [{'subitem_source_title': 'Journal of the Faculty of Agriculture, Kyushu University', 'subitem_source_title_language': 'en'}], 'item_30002_source_identifier22': [{'subitem_source_identifier': '0023-6152', 'subitem_source_identifier_type': 'ISSN'}], 'item_30002_volume_number24': {'subitem_volume': '54'}, 'item_30002_issue_number25': {'subitem_issue': '2'}, 'item_30002_page_start27': {'subitem_start_page': '373'}, 'item_30002_page_end28': {'subitem_end_page': '387'}, 'item_30002_date11': [{'subitem_date_issued_datetime': '2009', 'subitem_date_issued_type': 'Issued'}], 'item_30002_resource_type13': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'deleted_items': ['item_30002_identifier16', 'item_30002_funding_reference21', 'item_30002_conference34', 'item_30002_bibliographic_information29'], 'path': ['1623632832836']},
        "indexlist":['Sample Index']
    }
    with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
        with patch("weko_search_ui.utils.import_items_to_system", return_value=return_value):   
            url = url_for("weko_workspace.workflow_registration")
            res = client.post(url, json=data)
            assert res is not None

    # # # header error
    # # login(client=client, email=users[0]['email'])
    # # session = {
    # #     "itemlogin_id":"1",
    # #     "itemlogin_action_id":3,
    # #     "itemlogin_cur_step":"item_login",
    # #     "itemlogin_community_id":"comm01"
    # # }

    # # data = {
    # #     "recordModel":{'pubdate': '2025-03-11', 'item_30002_title0': [{'subitem_title': 'Identification of cDNA Sequences Encoding the Complement Components of Zebrafish (Danio rerio)', 'subitem_title_language': 'en'}], 'item_30002_creator2': [{'creatorNames': [{'creatorName': 'Vo Kha Tam', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Tsujikura Masakazu', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Somamoto Tomonori', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Nakano Miki', 'creatorNameLang': 'en'}]}], 'item_30002_identifier16': [{'subitem_identifier_uri': '10.5109/16119'}], 'item_30002_relation18': [{'subitem_relation_type_id': {'subitem_relation_type_id_text': '10.5109/16119', 'subitem_relation_type_select': 'DOI'}}], 'item_30002_funding_reference21': [{'subitem_funder_names': [{'subitem_funder_name': 'test1'}]}], 'item_30002_conference34': [{'subitem_conference_names': [{'subitem_conference_name': 'test3'}]}], 'item_30002_file35': [{'version_id': '9e7f93b3-7290-4a6f-aea0-87856279cf48', 'filename': '1_1.png', 'filesize': [{'value': '55 KB'}], 'format': 'image/png', 'date': [{'dateValue': '2025-03-11', 'dateType': 'Available'}], 'accessrole': 'open_access', 'url': {'url': 'https://192.168.56.106/record/2000235/files/1_1.png'}}], 'item_30002_bibliographic_information29': {'bibliographic_titles': [{'bibliographic_title': 'test2'}]}, 'item_30002_source_title23': [{'subitem_source_title': 'Journal of the Faculty of Agriculture, Kyushu University', 'subitem_source_title_language': 'en'}], 'item_30002_source_identifier22': [{'subitem_source_identifier': '0023-6152', 'subitem_source_identifier_type': 'ISSN'}], 'item_30002_volume_number24': {'subitem_volume': '54'}, 'item_30002_issue_number25': {'subitem_issue': '2'}, 'item_30002_page_start27': {'subitem_start_page': '373'}, 'item_30002_page_end28': {'subitem_end_page': '387'}, 'item_30002_date11': [{'subitem_date_issued_datetime': '2009', 'subitem_date_issued_type': 'Issued'}], 'item_30002_access_rights4': {'subitem_access_right': 'embargoed access'}, 'item_30002_resource_type13': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_30002_version_type15': {'subitem_version_type': 'AO'}, 'deleted_items': []}
    # # }

    # # mocker.patch("weko_workspace.views.session",session)
    # # url = url_for("weko_workspace.workflow_registration")
    # # res = client.post(url, 
    # #             data=json.dumps(data),
    # #             content_type='test/json')
    # # assert res.status_code == 200

    # # error
    # admin_settings = {"workFlow_select_flg": '1', "item_type_id": '1'}
    # login(client=client, email=users[0]['email'])
    # session = {
    #     "itemlogin_id":"1",
    #     "itemlogin_action_id":3,
    #     "itemlogin_cur_step":"item_login",
    #     "itemlogin_community_id":"comm01"
    # }
    # from types import SimpleNamespace
    # settings_obj = SimpleNamespace(**admin_settings)
    # mocker.patch("weko_workspace.views.session",session)
    # data = {
    #     "recordModel":{}
    # }
    # with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
    #     url = url_for("weko_workspace.workflow_registration")
    #     res = client.post(url, json=data)
    #     assert res is not None


    # # data is None
    # admin_settings = {"workFlow_select_flg": '1', "item_type_id": '30002'}

    # login(client=client, email=users[0]['email'])
    # session = {
    #     "itemlogin_id":"1",
    #     "itemlogin_action_id":3,
    #     "itemlogin_cur_step":"item_login",
    #     "itemlogin_community_id":"comm01"
    # }
    # data = {
    #     "recordModel":{'pubdate': '2025-03-11', 'item_30002_title0': [{'subitem_title': 'Identification of cDNA Sequences Encoding the Complement Components of Zebrafish (Danio rerio)', 'subitem_title_language': 'en'}], 'item_30002_creator2': [{'creatorNames': [{'creatorName': 'Vo Kha Tam', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Tsujikura Masakazu', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Somamoto Tomonori', 'creatorNameLang': 'en'}]}, {'creatorNames': [{'creatorName': 'Nakano Miki', 'creatorNameLang': 'en'}]}], 'item_30002_identifier16': [{'subitem_identifier_uri': '10.5109/16119'}], 'item_30002_relation18': [{'subitem_relation_type_id': {'subitem_relation_type_id_text': '10.5109/16119', 'subitem_relation_type_select': 'DOI'}}], 'item_30002_funding_reference21': [{'subitem_funder_names': [{'subitem_funder_name': 'test1'}]}], 'item_30002_conference34': [{'subitem_conference_names': [{'subitem_conference_name': 'test3'}]}], 'item_30002_file35': [{'version_id': '9e7f93b3-7290-4a6f-aea0-87856279cf48', 'filename': '1_1.png', 'filesize': [{'value': '55 KB'}], 'format': 'image/png', 'date': [{'dateValue': '2025-03-11', 'dateType': 'Available'}], 'accessrole': 'open_access', 'url': {'url': 'https://192.168.56.106/record/2000235/files/1_1.png'}}], 'item_30002_bibliographic_information29': {'bibliographic_titles': [{'bibliographic_title': 'test2'}]}, 'item_30002_source_title23': [{'subitem_source_title': 'Journal of the Faculty of Agriculture, Kyushu University', 'subitem_source_title_language': 'en'}], 'item_30002_source_identifier22': [{'subitem_source_identifier': '0023-6152', 'subitem_source_identifier_type': 'ISSN'}], 'item_30002_volume_number24': {'subitem_volume': '54'}, 'item_30002_issue_number25': {'subitem_issue': '2'}, 'item_30002_page_start27': {'subitem_start_page': '373'}, 'item_30002_page_end28': {'subitem_end_page': '387'}, 'item_30002_date11': [{'subitem_date_issued_datetime': '2009', 'subitem_date_issued_type': 'Issued'}], 'item_30002_access_rights4': {'subitem_access_right': 'embargoed access'}, 'item_30002_resource_type13': {'resourcetype': 'conference paper', 'resourceuri': 'http://purl.org/coar/resource_type/c_5794'}, 'item_30002_version_type15': {'subitem_version_type': 'AO'}, 'deleted_items': []}
    # }
    # from types import SimpleNamespace
    # settings_obj = SimpleNamespace(**admin_settings)
    # mocker.patch("weko_workspace.views.session",session)
    # with patch("weko_admin.admin.AdminSettings.get", return_value=settings_obj):
    #     with patch("weko_search_ui.utils.import_items_to_system", side_effect=Exception):
    #         with patch("weko_search_ui.utils.register_item_metadata", side_effect=Exception):
    #             url = url_for("weko_workspace.workflow_registration")
    #             res = client.post(url, json=data)
    #             assert res.status_code == 200