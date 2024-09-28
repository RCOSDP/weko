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
import json
import os
from unittest import mock
import unittest
import pytest
from unittest.mock import patch
import redis

from elasticsearch import ElasticsearchException
from sqlalchemy.exc import SQLAlchemyError
from flask import url_for, current_app
from invenio_files_rest.app import Flask
from invenio_records.api import Record
from invenio_pidstore.models import PersistentIdentifier
from weko_deposit.api import WekoDeposit
from invenio_accounts.testutils import login_user_via_session
from invenio_pidstore.errors import PIDDoesNotExistError, PIDInvalidAction

from weko_deposit.rest import ItemResource, create_blueprint
from weko_records.errors import WekoRecordsError
from weko_redis.errors import WekoRedisError
from weko_workflow.errors import WekoWorkflowError
from weko_workflow.models import Activity

# from weko_deposit.rest import create_blueprint, dbsession_clean


# .tox/c1/bin/pytest --cov=weko_deposit tests/test_rest.py -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-deposit/.tox/c1/tmp

# def test_publish(app, location):
#    deposit = WekoDeposit.create({})
#    kwargs = {
#        'pid_value': deposit.pid.pid_value
#    }


# .tox/c1/bin/pytest --cov=weko_deposit tests/test_rest.py::test_publish_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_publish_guest(client, deposit):
    """
    Test of publish.
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

# def publish(**kwargs):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_rest.py::test_publish_users -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
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
def test_publish_users(client, users, deposit, index, status_code):
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

# def test_dbsession_clean(client, app):
    """
    Test of dbsession_clean.
    """
#     with patch("weko_deposit.rest.weko_logger") as mock_logger:
#         mock_logger.assert_called_with(key='WEKO_COMMON_ERROR_UNEXPECTED', ex=mock.ANY)
#         mock_logger.reset_mock()

#     with patch("weko_deposit.rest.weko_logger") as mock_logger:
#         with patch("weko_deposit.rest.db.session.commit"):
#             with patch("weko_deposit.rest.db.session.remove"):
#                 dbsession_clean(None)
#                 mock_logger.assert_called_with(key='WEKO_COMMON_IF_ENTER', branch='exception is None')
#                 mock_logger.reset_mock()

    # exception = SQLAlchemyError("test_exception")
    # with patch("weko_deposit.rest.weko_logger") as mock_logger:
    #     with patch ("weko_deposit.rest.db.session.commit",side_effect=exception):
    #         with patch("weko_deposit.rest.db.session.rollback"):
    #             with patch ("weko_deposit.rest.db.session.remove"):
    #                 create_blueprint.dbsession_clean(exception)
    #                 mock_logger.assert_called_with(key='WEKO_COMMON_DB_SOME_ERROR', ex=exception)
    #                 mock_logger.reset_mock()
# class TestCreateBlueprint(unittest.TestCase):

#     def setUp(self):
#         self.app = Flask(__name__)
#         self.app.config['TESTING'] = True
#         self.app.config['WEKO_LOGGING_CONSOLE'] = True
#     # test for ctx in db_session_clean
#     def test_dbsession_clean_ctx_dict(self):
#         endpoints = {
#             'test_endpoint': {
#                     'read_permission_factory_imp': 'read_permission',
#                     'create_permission_factory_imp': 'create_permission',
#                     'update_permission_factory_imp': 'update_permission',
#                     'delete_permission_factory_imp': 'delete_permission',
#                     'record_class': 'record_class',
#                     'links_factory_imp': 'links_factory',
#                     'pid_type': 'pid_type',
#                     'pid_minter': 'pid_minter',
#                     'pid_fetcher': 'pid_fetcher',
#                     'default_media_type': 'application/json',
#                     'rdc_route': '/test_route',
#                     'pub_route': '/publish_route',
#                 }
#         }
#         with self.app.app_context():
#             with patch('weko_deposit.rest.obj_or_import_string') as mock_obj_or_import_string:
#                 with patch('weko_deposit.rest.default_links_factory') as mock_default_links_factory:
                
#                     mock_obj_or_import_string.side_effect = lambda x, default=None: x
#                     mock_default_links_factory.return_value = 'default_links_factory'

#                     blueprint = create_blueprint(self.app, endpoints)
#                     self.app.register_blueprint(blueprint)

#                     view_func = self.app.view_functions['weko_deposit_rest.test_endpoint_item']
#                     view_class = view_func.view_class

#                     instance = view_class(ctx=endpoints['test_endpoint'], record_serializers=None, default_media_type='application/json', kwargs='test_kwarg')

#                     self.assertEqual(instance.ctx['read_permission_factory'], 'read_permission')
#                     self.assertEqual(instance.ctx['create_permission_factory'], 'create_permission')
#                     self.assertEqual(instance.ctx['update_permission_factory'], 'update_permission')
#                     self.assertEqual(instance.ctx['delete_permission_factory'], 'delete_permission')
#                     self.assertEqual(instance.ctx['record_class'])
#                     self.assertEqual(instance.ctx['links_factory'], 'links_factory')
#                     self.assertEqual(instance.ctx['pid_type'], 'pid_type')
#                     self.assertEqual(instance.ctx['pid_minter'], 'pid_minter')
#                     self.assertEqual(instance.ctx['pid_fetcher'], 'pid_fetcher')
#                     self.assertIn('application/json', instance.loaders)
#                     self.assertTrue(callable(instance.loaders['application/json']))


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
