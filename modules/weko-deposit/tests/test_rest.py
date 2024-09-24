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
import copy
from datetime import datetime
import json
import os
from unittest import mock
import unittest
import uuid
import pytest
from unittest.mock import patch
import redis

from elasticsearch import ElasticsearchException
from sqlalchemy.exc import SQLAlchemyError
from flask import url_for, current_app
from invenio_files_rest.app import Flask
from invenio_records.api import Record
from invenio_records_rest.utils import deny_all
from invenio_pidstore.models import PersistentIdentifier
from weko_deposit.api import WekoDeposit
from invenio_accounts.testutils import login_user_via_session
from invenio_pidstore.models import PIDStatus
from invenio_pidstore.errors import PIDDoesNotExistError, PIDInvalidAction

from weko_deposit.config import _PID, WEKO_DEPOSIT_REST_ENDPOINTS
from weko_deposit import config
from weko_deposit.rest import ItemResource, create_blueprint
from weko_records.errors import WekoRecordsError
from weko_redis.errors import WekoRedisError
from weko_workflow.errors import WekoWorkflowError
from weko_workflow.models import Activity, FlowAction, FlowDefine, WorkFlow

# from weko_deposit.rest import create_blueprint, dbsession_clean

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_rest.py -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-deposit/.tox/c1/tmp


# def publish(**kwargs):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_rest.py::test_publish -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
@pytest.mark.parametrize('index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
    (7, 200),
])
def test_publish_user(client, users, deposit, index, status_code):
    """
    Test of publish.
    """
    login_user_via_session(client=client, email=users[index]['email'])
    kwargs = {
        'pid_value': deposit
    }
    url = url_for('weko_deposit_rest.publish', pid_value=kwargs['pid_value'])
    input = {}
    res = client.put(url, data=json.dumps(input),
                    content_type='application/json')
    assert res.status_code == status_code

    # SQLAchemyError
    with patch("weko_deposit.rest.WekoDeposit",side_effect=SQLAlchemyError("test_error")):
        with patch("weko_deposit.rest.weko_logger") as mock_logger:
            res = client.put(url, data=json.dumps(input),
                        content_type='application/json')
            assert res.status_code == 400
            assert "Some errors in the DB." in res.data.decode("utf-8")
            mock_logger.assert_called_with(key='WEKO_COMMON_DB_SOME_ERROR', ex=mock.ANY)
            mock_logger.reset_mock()

    # Exception
    with patch("weko_deposit.rest.WekoDeposit", side_effect=Exception("test_exception")):
        res = client.put(url, data=json.dumps(input),
                        content_type='application/json')
        assert res.status_code == 400
        assert "Failed to publish item" in res.data.decode("utf-8")

def test_publish_guest(client, deposit):
    """
    Test of publish a guest user.
    """
    kwargs = {
        'pid_value': deposit
    }
    url = url_for('weko_deposit_rest.publish', pid_value=kwargs['pid_value'],_external=True)
    input = {}
    res = client.put(url, data=json.dumps(input),
                    content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data) == {"status": "success"}

# def create_blueprint(app, endpoints):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_rest.py::test_create_blueprint -vv -s --cov-branch --cov-report=html --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp --full-trace
def test_create_blueprint(base_app):
    """
    Test of create_blueprint.
    """
    # record_serializer and search_serializers exists
    endpoints = copy.deepcopy(WEKO_DEPOSIT_REST_ENDPOINTS)
    endpoints["depid"][
        "rdc_route"
    ] = "/deposits/redirect/<{0}:pid_value>".format(_PID)
    endpoints["depid"][
        "pub_route"
    ] = "/deposits/publish/<{0}:pid_value>".format(_PID)
    # endpoints = {
    #     "test_endpoint": {
    #         "read_permission_factory_imp": "weko_deposit.permissions:permission_factory",
    #         "create_permission_factory_imp": "weko_deposit.permissions:permission_factory",
    #         "update_permission_factory_imp": "weko_deposit.permissions:permission_factory",
    #         "delete_permission_factory_imp": "weko_deposit.permissions:permission_factory",
    #         "links_factory_imp": "weko_deposit.links:links_factory",
    #         "rdc_route": "/test_route",
    #         "pub_route": "/test_route",
    #         "pid_type": "depid",
    #         "pid_minter": "weko_deposit_minter",
    #         "pid_fetcher": "weko_deposit_fetcher",
    #         "default_media_type": "application/json",
    #     },
    #     "depid": {
    #         "rdc_route": "/deposits/redirect/<{0}:pid_value>".format(_PID),
    #         "pub_route": "/deposits/publish/<{0}:pid_value>".format(_PID),
    #     }
    # }
    with patch("weko_deposit.rest.obj_or_import_string") as mock_obj_or_import_string:
        def side_effect(import_string, default=None):
            if import_string == "weko_deposit_minter":
                from weko_deposit.pidstore import weko_deposit_minter
                return weko_deposit_minter
            elif import_string == "weko_deposit_fetcher":
                from weko_deposit.pidstore import weko_deposit_fetcher
                return weko_deposit_fetcher
            elif import_string == "weko_deposit.api:WekoDeposit":
                from weko_deposit.api import WekoDeposit
                return WekoDeposit
            elif import_string == "weko_records.serializers:deposit_json_v1_response":
                from weko_records.serializers import deposit_json_v1_response
                return deposit_json_v1_response
            elif import_string == "invenio_depositserializers:json_v1_files_response":
                from invenio_deposit.serializers import json_v1_files_response
                return json_v1_files_response
            elif import_string == "invenio_deposit.search:DepositSearch":
                from invenio_deposit.search import DepositSearch
                return DepositSearch
            elif import_string == "invenio_records_rest.serializers:json_v1_search":
                from invenio_records_rest.serializers import json_v1_search
                return json_v1_search
            elif import_string == deny_all:
                return deny_all
            else:
                return default
        mock_obj_or_import_string.side_effect = side_effect
        result = create_blueprint(base_app, endpoints)
        # print(mock_obj_or_import_string.call_count)
        # print(mock_obj_or_import_string.call_args_list)
        # vars(result)
        # except Exception as e:
        #     print(f"Error during test: {e}")

    # record_serializer and search_serializers not exists
    endpoints = {
        "test_endpoint": {
            "read_permission_factory_imp": "weko_deposit.permissions:permission_factory",
            "create_permission_factory_imp": "weko_deposit.permissions:permission_factory",
            "update_permission_factory_imp": "weko_deposit.permissions:permission_factory",
            "delete_permission_factory_imp": "weko_deposit.permissions:permission_factory",
            "links_factory_imp": "weko_deposit.links:links_factory",
            "rdc_route": "/test_route",
            "pub_route": "/test_route",
            "pid_type": "depid",
            "pid_minter": "weko_deposit_minter",
            "pid_fetcher": "weko_deposit_fetcher",
            "default_media_type": "application/json",
        }
    }
    with patch("weko_deposit.rest.obj_or_import_string") as mock_obj_or_import_string:
        mock_obj_or_import_string.side_effect = lambda x, default=None: x
        result = create_blueprint(base_app, endpoints)
        # print()
        # vars(result)
        # assert config.DEPOSIT_REST_ENDPOINTS['depid']['record_class'] == endpoints['test_endpoint']['record_serializers']['record_class']



# class ItemResource(ContentNegotiatedMethodView):
#     def __init__( method_serializers, default_method_media_type,default_media_type, **kwargs)
#     def post(self, pid, record, **kwargs):
#     def put(self, **kwargs):
#     def __sanitize_string(s):
#     def __sanitize_input_data(self, data):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_rest.py::TestItemResource -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
# class TestItemResource(unittest.TestCase):
# def put(self, **kwargs):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_rest.py::TestItemResource::test_put -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_rest.py::test_depid_item_put_acl_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_depid_item_put_acl_guest(client, deposit):
    """
    Test of depid_item post.
    :param client: The flask client.
    """
    kwargs = {
        'pid_value': deposit
    }
    url = url_for('weko_deposit_rest.depid_item',
                pid_value=kwargs['pid_value'])
    input = {"item_1617186331708": [{"subitem_1551255647225": "tetest",
            "subitem_1551255648112": "en"}], "pubdate": "2021-01-01",
            "item_1617258105262": {"resourcetype": "conference paper",
                                    "resourceuri": "http://purl.org/coar/resource_type/c_5794"},
            "shared_user_id": -1, "title": "tetest", "lang": "en",
            "deleted_items": ["item_1617186385884", "item_1617186419668",
                            "approval1", "approval2"],
            "$schema": "/items/jsonschema/15"}
    res = client.put(url, data=json.dumps(input),
                    content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data) == {"status":"success"}


# .tox/c1/bin/pytest --cov=weko_deposit tests/test_rest.py::test_depid_item_put_acl_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
@pytest.mark.parametrize('index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
    (7, 200),
])
def test_depid_item_put_acl_users(client, users, deposit, index, status_code):
    """
    Test of depid_item post.
    :param client: The flask client.
    """
    login_user_via_session(client=client, email=users[index]['email'])
    kwargs = {
        'pid_value': deposit
    }
    url = url_for('weko_deposit_rest.depid_item',
                pid_value=kwargs['pid_value'])
    input = {}
    res = client.put(url, data=json.dumps(input),
                    content_type='application/json')
    assert res.status_code == status_code

# class ItemResource(ContentNegotiatedMethodView):
#    def put(self, **kwargs):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_rest.py::test_put_wf_activity_is_not_none -vv -s --cov-branch --cov-report=html --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp --full-trace
def test_put_wf_activity_is_not_none(client, users, db,location,  es_records,db_itemtype,db_actions):
    login_user_via_session(client=client, email=users[2]['email'])
    kwargs = {
        #'pid_value': deposit
        'pid_value': es_records[1][0]["deposit"].pid.pid_value
    }
    url = url_for('weko_deposit_rest.depid_item',
                pid_value=kwargs['pid_value'])
    input = {
        "item_1617186331708": [{"subitem_1551255647225": "tetest","subitem_1551255648112": "en"}], 
        "pubdate": "2021-01-01",
        "item_1617258105262": {
            "resourcetype": "conference paper",
            "resourceuri": "http://purl.org/coar/resource_type/c_5794"
        },
        "shared_user_id": -1, 
        "title": "tetest", 
        "lang": "en",
        "deleted_items": ["item_1617186385884", "item_1617186419668",
                        "approval1", "approval2"],
        "$schema": "/items/jsonschema/15",
        "edit_mode":"upgrade"
    }
    flow_define = FlowDefine(id=1,flow_id=uuid.uuid4(),
                            flow_name='Registration Flow',
                            flow_user=1)
    with db.session.begin_nested():
        db.session.add(flow_define)
    db.session.commit()
    flow_action4 = FlowAction(status='N',
                    flow_id=flow_define.flow_id,
                    action_id=7,
                    action_version='1.0.0',
                    action_order=4,
                    action_condition='',
                    action_status='A',
                    action_date=datetime.strptime('2018/07/28 0:00:00','%Y/%m/%d %H:%M:%S'),
                    send_mail_setting={})
    with db.session.begin_nested():
        db.session.add(flow_action4)
    db.session.commit()
    item_id_workflow = WorkFlow(flows_id=uuid.uuid4(),
                        flows_name='test workflow4',
                        itemtype_id=1,
                        index_tree_id=None,
                        flow_id=1,
                        is_deleted=False,
                        open_restricted=False,
                        location_id=int(location.id),
                        is_gakuninrdm=False)
    with db.session.begin_nested():
        db.session.add(item_id_workflow)
    item_id_activity = Activity(activity_id='3',workflow_id=item_id_workflow.id, flow_id=flow_define.id,
                    action_id=1, activity_login_user=1,
                    activity_update_user=1,
                    activity_start=datetime.strptime('2022/04/14 3:01:53.931', '%Y/%m/%d %H:%M:%S.%f'),
                    activity_community_id=3,
                    activity_confirm_term_of_use=True,
                    title='test', shared_user_id=-1, extra_info={},
                    action_order=1,
                    item_id=str(es_records[1][0]["deposit"].pid.object_uuid),
                    )
    with db.session.begin_nested():
        db.session.add(item_id_activity)

    db.session.commit()

    res = client.put(url, data=json.dumps(input),
                    content_type='application/json')
    assert res.status_code == 200

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_rest.py::test_depid_item_put -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_depid_item_put(client, users,es_records):
    login_user_via_session(client=client, email=users[2]['email'])
    kwargs = {
        #'pid_value': deposit
        'pid_value': es_records[1][0]["deposit"].pid.pid_value
    }
    url = url_for('weko_deposit_rest.depid_item',
                pid_value=kwargs['pid_value'])
    input = {
        "item_1617186331708": [{"subitem_1551255647225": "tetest","subitem_1551255648112": "en"}], 
        "pubdate": "2021-01-01",
        "item_1617258105262": {
            "resourcetype": "conference paper",
            "resourceuri": "http://purl.org/coar/resource_type/c_5794"
        },
        "shared_user_id": -1, 
        "title": "tetest", 
        "lang": "en",
        "deleted_items": ["item_1617186385884", "item_1617186419668",
                        "approval1", "approval2"],
        "$schema": "/items/jsonschema/15"
    }

    # success case
    res = client.put(url, data=json.dumps(input),
                    content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data) == {"status":"success"}
    
    input = {
        "item_1617186331708": [{"subitem_1551255647225": "tetest","subitem_1551255648112": "en"}], 
        "pubdate": "2021-01-01",
        "item_1617258105262": {
            "resourcetype": "conference paper",
            "resourceuri": "http://purl.org/coar/resource_type/c_5794"
        },
        "shared_user_id": -1, 
        "title": "tetest", 
        "lang": "en",
        "deleted_items": ["item_1617186385884", "item_1617186419668",
                        "approval1", "approval2"],
        "$schema": "/items/jsonschema/15",
        "edit_mode":"upgrade"
    }
    # success case with edit_mode
    # cur_pid = PersistentIdentifier.get('recid', kwargs['pid_value'])
    # pid = PersistentIdentifier.get('recid', kwargs['pid_value'].split(".")[0])
    with patch("weko_deposit.rest.PersistentIdentifier.get", side_effect=PersistentIdentifier.get) as mock_pid:
        # mock_pid.side_effect = [cur_pid, pid]
        res = client.put(url, data=json.dumps(input),
                        content_type='application/json')
        # instance = ItemResource()
        # instance.put(kwargs['pid_value'], input)
        assert res.status_code == 200
        assert json.loads(res.data) == {"status":"success"}
        # mock_pid.assert_called_with('recid', kwargs['pid_value'])

    # upgrade_record is not None and ".0" in pid_value
    kwargs_ = {
        'pid_value': f"{kwargs['pid_value']}.0"
    }
    # # with patch("weko_deposit.rest.WekoDeposit.newversion", return_value=Record(data=json.dumps(input))) as mock_deposit:
    # with patch("weko_deposit.rest.weko_logger") as mock_logger:
    #     res = client.put(url, data=json.dumps(input),
    #                 content_type='application/json')
    #     mock_logger.assert_called_with(key='WEKO_COMMON_IF_ENTER', branch="upgrade_record is not None and '.0' in pid_value")

    # # wf_activity is not None
    # with patch("weko_deposit.rest.WorkActivity.get_workflow_activity_by_item_id", return_value=type("_Activity",(Activity),{})()) as mock_wf_activity:
    #     with patch("weko_deposit.rest.weko_logger") as mock_logger:
    #         res = client.put(url, data=json.dumps(input),
    #                     content_type='application/json')
    #         mock_logger.assert_called_with(key='WEKO_COMMON_IF_ENTER', branch="wf_activity is not None")

    # weko_record is None

    # Not Found PID in DB.
    with patch("weko_deposit.rest.PersistentIdentifier.get",side_effect=PIDDoesNotExistError(pid_type='recid', pid_value=kwargs['pid_value'])) as mock_pid:
        with patch("weko_deposit.rest.weko_logger") as mock_logger:
            res = client.put(url, data=json.dumps(input),
                        content_type='application/json')
            assert res.status_code == 400
            assert "Not Found PID in DB." in res.data.decode("utf-8")
            mock_pid.assert_called_with('recid', kwargs['pid_value'])
            mock_logger.assert_called_with(key='WEKO_COMMON_NOT_FOUND_OBJECT', object=mock.ANY)
            mock_logger.reset_mock()

    # Invalid operation on PID.
    with patch("weko_deposit.rest.PersistentIdentifier.get",side_effect=PIDInvalidAction()):
        with patch("weko_deposit.rest.weko_logger") as mock_logger:
            res = client.put(url, data=json.dumps(input),
                        content_type='application/json')
            assert res.status_code == 400
            assert "Invalid operation on PID." in res.data.decode("utf-8")
            mock_logger.assert_called_with(key='WEKO_COMMON_DB_OTHER_ERROR', ex=mock.ANY)
            mock_logger.reset_mock()

    # Not Found Record in DB.
    with patch("weko_deposit.rest.WekoRecord.get_record_by_pid",side_effect=WekoRecordsError("test_wr_error")):
        res = client.put(url, data=json.dumps(input),
                    content_type='application/json')
        assert res.status_code == 400
        assert "Not Found Record in DB." in res.data.decode("utf-8")

    # RedisError
    with patch("weko_deposit.rest.RedisConnection.connection",side_effect=WekoRedisError("test_redis_error")):
        res = client.put(url, data=json.dumps(input),
                    content_type='application/json')
        assert res.status_code == 400
        assert "Failed to register item!" in res.data.decode("utf-8")

    # WekoWorkflowError
    with patch("weko_deposit.rest.WorkActivity.get_workflow_activity_by_item_id",side_effect=WekoWorkflowError("test_wf_error")):
        res = client.put(url, data=json.dumps(input),
                    content_type='application/json')
        assert res.status_code == 400
        assert "Failed to get activity!" in res.data.decode("utf-8")

    # SQLAlchemyError
    with patch("weko_deposit.rest.PersistentIdentifier.get",side_effect=SQLAlchemyError("test_sql_error")):
        with patch("weko_deposit.rest.weko_logger") as mock_logger:
            res = client.put(url, data=json.dumps(input),
                        content_type='application/json')
            assert res.status_code == 400
            assert "Failed to register item!" in res.data.decode("utf-8")
            mock_logger.assert_called_with(key='WEKO_COMMON_DB_SOME_ERROR', ex=mock.ANY)
            mock_logger.reset_mock()

    # ElasticsearchException
    with patch("weko_deposit.rest.PersistentIdentifier.get",side_effect=ElasticsearchException("test_es_error")):
        with patch("weko_deposit.rest.weko_logger") as mock_logger:
            res = client.put(url, data=json.dumps(input),
                        content_type='application/json')
            assert res.status_code == 400
            assert "Failed to register item!" in res.data.decode("utf-8")
            mock_logger.assert_called_with(key='WEKO_COMMON_ERROR_ELASTICSEARCH', ex=mock.ANY)
            mock_logger.reset_mock()

    # RedisError
    with patch("weko_deposit.rest.RedisConnection.connection",side_effect=redis.RedisError("test_redis_error")):
        with patch("weko_deposit.rest.weko_logger") as mock_logger:
            res = client.put(url, data=json.dumps(input),
                        content_type='application/json')
            assert res.status_code == 400
            assert "Failed to register item!" in res.data.decode("utf-8")
            mock_logger.assert_called_with(key='WEKO_COMMON_ERROR_REDIS', ex=mock.ANY)
            mock_logger.reset_mock()

    # Exception
    with patch("weko_deposit.rest.PersistentIdentifier.get",side_effect=Exception("test_exception")):
        with patch("weko_deposit.rest.weko_logger") as mock_logger:
            res = client.put(url, data=json.dumps(input),
                        content_type='application/json')
            assert res.status_code == 400
            assert "Failed to register item!" in res.data.decode("utf-8")
            mock_logger.assert_called_with(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=mock.ANY)
            mock_logger.reset_mock()

# .tox/c1/bin/pytest --cov=weko_deposit tests/test_rest.py::test_depid_item_post_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_depid_item_post_guest(client, deposit):
    """
    Test of depid_item post.
    :param client: The flask client.
    """
    with patch.dict(current_app.config, {'WEKO_RECORDS_UI_EMAIL_ITEM_KEYS': '1'}):
        kwargs = {
                'pid_value': deposit
        }
        url = url_for('weko_deposit_rest.depid_item',
                    pid_value=kwargs['pid_value'])
        input = {}
        res = client.post(url,
                        data=json.dumps(input),
                        content_type='application/json')
        assert res.status_code == 200
        data = json.loads(res.data)
        data.pop('created')
        data['links'].pop('bucket')
        assert data == {
            'id': 1,
            'links': {
                'iframe_tree': '/items/iframe/index/1',
                'iframe_tree_upgrade': '/items/iframe/index/1.1',
                'index': '/api/deposits/redirect/1',
                'r': '/items/index/1'
            }
        }


# .tox/c1/bin/pytest --cov=weko_deposit tests/test_rest.py::test_depid_item_post_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
@pytest.mark.parametrize('index, status_code', [
    (0, 200),
    (1, 200),
    (2, 200),
    (3, 200),
    (4, 200),
    (5, 200),
    (6, 200),
    (7, 200),
])
def test_depid_item_post_users(client, users, deposit, index, status_code):
    """
    Test of depid_item post.
    :param client: The flask client.
    """
    with patch.dict(current_app.config, {'WEKO_RECORDS_UI_EMAIL_ITEM_KEYS': '1'}):
        login_user_via_session(client=client, email=users[index]['email'])
        kwargs = {
            'pid_value': deposit
        }
        url = url_for('weko_deposit_rest.depid_item',
                    pid_value=kwargs['pid_value'])
        input = {}
        res = client.post(url,
                        data=json.dumps(input),
                        content_type='application/json')
        assert res.status_code == status_code

# sanitized string contains irregular control characters
def test_sanitize_string(client, users,es_records):
    login_user_via_session(client=client, email=users[2]['email'])
    kwargs = {
        #'pid_value': deposit
        'pid_value': es_records[1][0]["deposit"].pid.pid_value
    }
    url = url_for('weko_deposit_rest.depid_item',
                pid_value=kwargs['pid_value'])
    input = {
        "item_1617186331708": [{"subitem_1551255647225": "tetest","subitem_1551255648112": "en"}], 
        "pubdate": "2021-01-01",
        "item_1617258105262": {
            "resourcetype": "conference \x01paper",
            "resourceuri": "http://purl.org/coar/resource_type/c_5794"
        },
        "shared_user_id": -1, 
        "title": "tetest", 
        "lang": "en",
        "deleted_items": ["item_1617186385884", "item_1617186419668",
                        "approval1", "approval2"],
        "$schema": "/items/jsonschema/15"
    }

    # success case
    res = client.put(url, data=json.dumps(input),
                    content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data) == {"status":"success"}
