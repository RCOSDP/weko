# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_permissions.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp


import pytest
from mock import patch
from unittest.mock import MagicMock
import json
from weko_items_ui.api import item_login
from flask import session,jsonify

from weko_items_ui.permissions import edit_permission_factory
from weko_records_ui.permissions import page_permission_factory

# def edit_permission_factory(record, **kwargs):
#     def can(self):
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_permissions.py::edit_permission_factory  -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_edit_permission_factory(db_records):
    depid, recid, parent, doi, record, item = db_records[0]
    expect = page_permission_factory(record, flg='Edit').can()
    ret = edit_permission_factory(record)
    assert ret.can()==True
