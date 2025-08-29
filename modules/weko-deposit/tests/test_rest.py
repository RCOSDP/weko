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
import uuid
import copy
import pytest
from mock import patch, MagicMock
import redis

from elasticsearch import ElasticsearchException
from sqlalchemy.exc import SQLAlchemyError
from flask import url_for
from weko_deposit.api import WekoDeposit, WekoRecord
from invenio_accounts.testutils import login_user_via_session


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

    with patch("weko_deposit.rest.WekoDeposit",side_effect=BaseException("test_error")):
        res = client.put(url, data=json.dumps(input),
                     content_type='application/json')
        assert res.status_code == 400
        assert "Failed to publish item" in res.data.decode("utf-8")


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
             "shared_user_ids": [], "title": "tetest", "lang": "en",
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
def test_depid_item_put(client, users,es_records, mocker):
    mock_task = mocker.patch("weko_deposit.tasks.extract_pdf_and_update_file_contents")
    mock_task.apply_async = MagicMock()
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
        "shared_user_ids": [],
        "title": "tetest",
        "lang": "en",
        "deleted_items": ["item_1617186385884", "item_1617186419668",
                          "approval1", "approval2"],
        "$schema": "/items/jsonschema/15"
    }
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
        "shared_user_ids": [],
        "title": "tetest",
        "lang": "en",
        "deleted_items": ["item_1617186385884", "item_1617186419668",
                          "approval1", "approval2"],
        "$schema": "/items/jsonschema/15",
        "edit_mode":"upgrade"
    }
    res = client.put(url, data=json.dumps(input),
                     content_type='application/json')
    assert res.status_code == 200
    assert json.loads(res.data) == {"status":"success"}

    with patch("weko_deposit.rest.PersistentIdentifier.get",side_effect=SQLAlchemyError("test_sql_error")):
        res = client.put(url, data=json.dumps(input),
                     content_type='application/json')
        assert res.status_code == 400
        assert "Failed to register item!" in res.data.decode("utf-8")

    with patch("weko_deposit.rest.PersistentIdentifier.get",side_effect=ElasticsearchException("test_es_error")):
        res = client.put(url, data=json.dumps(input),
                     content_type='application/json')
        assert res.status_code == 400
        assert "Failed to register item!" in res.data.decode("utf-8")

    with patch("weko_deposit.rest.PersistentIdentifier.get",side_effect=redis.RedisError("test_redis_error")):
        res = client.put(url, data=json.dumps(input),
                     content_type='application/json')
        assert res.status_code == 400
        assert "Failed to register item!" in res.data.decode("utf-8")

    with patch("weko_deposit.rest.PersistentIdentifier.get",side_effect=BaseException("test_redis_error")):
        res = client.put(url, data=json.dumps(input),
                     content_type='application/json')
        assert res.status_code == 400
        assert "Failed to register item!" in res.data.decode("utf-8")


# .tox/c1/bin/pytest --cov=weko_deposit tests/test_rest.py::test_depid_item_post_guest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_depid_item_post_guest(client, deposit):
    """
    Test of depid_item post.
    :param client: The flask client.
    """
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


# .tox/c1/bin/pytest --cov=weko_deposit tests/test_rest.py::test_put -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-deposit/.tox/c1/tmp
def test_put(app, client, records):
    headers = {'content-type': 'application/json'}
    version = MagicMock()
    version.model.id = uuid.uuid4()
    version.pid.pid_value = "1.1"
    with patch("weko_deposit.rest.WekoDeposit.newversion", return_value=version):
        record_1 = WekoRecord.get_record_by_pid("1")
        record_1_1 = copy.deepcopy(record_1)
        record_1_1["recid"] = "1.1"
        mock_record = MagicMock()
        mock_record = lambda x: record_1_1 if x == "1.1" else record_1
        with patch("weko_deposit.rest.WekoRecord.get_record_by_pid", mock_record):
            with patch("weko_deposit.rest.call_external_system") as mock_external:
                with patch("weko_deposit.rest.PersistentIdentifier.get",
                           return_value=record_1.pid):
                    data = {'edit_mode': 'upgrade'}
                    res = client.put("/deposits/redirect/1.0",
                                    data=json.dumps(data), headers=headers)
                    assert res.status_code == 200
                    mock_external.assert_not_called()
            with patch("weko_deposit.rest.call_external_system") as mock_external:
                data = {'edit_mode': 'upgrade'}
                res = client.put("/deposits/redirect/1",
                                data=json.dumps(data), headers=headers)
                assert res.status_code == 200
                mock_external.assert_called_once()
                assert mock_external.call_args[1]["old_record"]["recid"] == "1"
                assert mock_external.call_args[1]["new_record"]["recid"] == "1.1"
            with patch("weko_deposit.rest.call_external_system") as mock_external:
                data = {'edit_mode': "keep"}
                res = client.put("/deposits/redirect/1",
                                data=json.dumps(data), headers=headers)
                assert res.status_code == 200
                mock_external.assert_not_called()
