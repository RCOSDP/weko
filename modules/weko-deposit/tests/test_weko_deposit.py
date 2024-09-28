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
from unittest import mock
from flask import Flask

from weko_deposit import WekoDeposit
from unittest.mock import patch, MagicMock

from weko_deposit.ext import WekoDepositREST

def test_version():
    """Test version import."""
    from weko_deposit import __version__
    assert __version__

# class WekoDeposit(object):

# def __init__(self, app=None):
# def init_app(self, app): 
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_weko_deposit.py::test_init -vv -s --cov-branch --cov-report=html --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp --full-trace
def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    # mock weko_logger
    with patch('weko_deposit.ext.weko_logger') as mock_logger:

        # with app
        ext = WekoDeposit(app)
        assert 'weko-deposit' in app.extensions
        mock_logger.assert_any_call(app=app, key='WEKO_COMMON_INIT_APP', ext="weko-deposit")
        mock_logger.reset_mock()

    #  without app
    app = Flask('testapp')
    ext = WekoDeposit()
    assert 'weko-deposit' not in app.extensions
    ext.init_app(app)
    assert 'weko-deposit' in app.extensions

# def init_config(self, app):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_weko_deposit.py::test_init -vv -s --cov-branch --cov-report=html --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp --full-trace
def test_init_with_base_template():
    """Test extension initialization with BASE_TEMPLATE in config."""
    app = Flask('testapp')
    app.config['BASE_TEMPLATE'] = 'base.html'

    with patch('weko_deposit.ext.weko_logger') as mock_logger:
        ext = WekoDeposit(app)
        assert 'weko-deposit' in app.extensions
        assert app.config['WEKO_DEPOSIT_BASE_TEMPLATE'] == 'base.html'

        mock_logger.assert_any_call(app=app, key='WEKO_COMMON_IF_ENTER', branch="BASE_TEMPLATE in app.config")
        mock_logger.assert_any_call(app=app, key='WEKO_COMMON_INIT_APP', ext="weko-deposit")
        mock_logger.assert_any_call(app=app, key='WEKO_COMMON_FOR_START')
        mock_logger.assert_any_call(app=app, key='WEKO_COMMON_FOR_LOOP_ITERATION',
                                    count=mock.ANY, element=mock.ANY)
        mock_logger.assert_any_call(app=app, key='WEKO_COMMON_FOR_END')
        mock_logger.reset_mock()

# class WekoDepositREST(object):

# def __init__(self, app=None):
# .tox/c1/bin/pytest --cov=weko_deposit tests/test_weko_deposit.py::test_weko_deposit_rest_init -vv -s --cov-branch --cov-report=html --cov-report=term --basetemp=/code/modules/weko-deposit/.tox/c1/tmp --full-trace
def test_weko_deposit_rest_init():
    """Test extension initialization without app."""
    # without app
    ext = WekoDepositREST()
    assert ext is not None
    ext.init_app = MagicMock()
    # with app
    app = Flask('testapp')
    ext.init_app(app)
    # Check if init_app was called
    ext.init_app.assert_called_once_with(app)

class MockRecordsSearch:
    class MockQuery:
        class MockExecute:
            def __init__(self):
                pass
            def to_dict(self):
                raise {}
        def __init__(self):
            pass
        def execute(self):
            return self.MockExecute()
    def __init__(self, index=None):
        pass

    def update_from_dict(self, query=None):
        return self.MockQuery()


def test_ItemResource_put(app, db):
    mock_recordssearch = MagicMock(side_effect=MockRecordsSearch)
    WekoDeposit(app)
    with app.test_client() as client:
        data = {"item_1617186331708": [{"subitem_1551255647225": "tetest", "subitem_1551255648112": "en"}], "pubdate": "2021-01-01", "item_1617258105262": {"resourcetype": "conference paper", "resourceuri": "http://purl.org/coar/resource_type/c_5794"}, "shared_user_id": -1, "title": "tetest", "lang": "en", "deleted_items": ["item_1617186385884", "item_1617186419668", "item_1617186499011", "item_1617186609386", "item_1617186626617", "item_1617186643794",
                                                                                                                                                                                                                                                                                                                                    "item_1617186660861", "item_1617186702042", "item_1617186783814", "item_1617186859717", "item_1617186882738", "item_1617186901218", "item_1617186920753", "item_1617186941041", "item_1617187112279", "item_1617187187528", "item_1617349709064", "item_1617353299429", "item_1617605131499", "item_1617610673286", "item_1617620223087", "item_1617944105607", "item_1617187056579", "approval1", "approval2"], "$schema": "/items/jsonschema/15"}
        headers = {'content-type': 'application/json'}
        with patch('weko_deposit.tasks.RecordsSearch', mock_recordssearch):
            res = client.put("/deposits/redirect/1",
                            data=json.dumps(data), headers=headers)
            assert res.status_code == 200
