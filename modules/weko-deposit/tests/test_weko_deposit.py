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
from flask import Flask

from weko_deposit import WekoDeposit
from mock import patch, MagicMock

def test_version():
    """Test version import."""
    from weko_deposit import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = WekoDeposit(app)
    assert 'weko-deposit' in app.extensions

    app = Flask('testapp')
    ext = WekoDeposit()
    assert 'weko-deposit' not in app.extensions
    ext.init_app(app)
    assert 'weko-deposit' in app.extensions

# def test_view(app, db):
#     """Test view."""
#     WekoDeposit(app)
#     with app.test_client() as client:
#         res = client.get("/")
#         assert res.status_code == 200
#         assert 'Welcome to weko-deposit' in str(res.data)

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
        data = {"item_1617186331708": [{"subitem_1551255647225": "tetest", "subitem_1551255648112": "en"}], "pubdate": "2021-01-01", "item_1617258105262": {"resourcetype": "conference paper", "resourceuri": "http://purl.org/coar/resource_type/c_5794"}, "shared_user_ids": [], "title": "tetest", "lang": "en", "deleted_items": ["item_1617186385884", "item_1617186419668", "item_1617186499011", "item_1617186609386", "item_1617186626617", "item_1617186643794",
                                                                                                                                                                                                                                                                                                                                      "item_1617186660861", "item_1617186702042", "item_1617186783814", "item_1617186859717", "item_1617186882738", "item_1617186901218", "item_1617186920753", "item_1617186941041", "item_1617187112279", "item_1617187187528", "item_1617349709064", "item_1617353299429", "item_1617605131499", "item_1617610673286", "item_1617620223087", "item_1617944105607", "item_1617187056579", "approval1", "approval2"], "$schema": "/items/jsonschema/15"}
        headers = {'content-type': 'application/json'}
        with patch('weko_deposit.tasks.RecordsSearch', mock_recordssearch):
            res = client.put("/deposits/redirect/1",
                            data=json.dumps(data), headers=headers)
            assert res.status_code == 200
