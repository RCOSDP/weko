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
# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_permissions.py::test_edit_permission_factory_guest  -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
def test_edit_permission_factory_guest(app, db_records):
    """未認証は編集できない。

    以前は page_permission_factory(record, flg='Edit') に委譲していたが、
    page_permission_factory は flg を参照しない閲覧用の判定で、公開アイテムなら
    匿名でも True を返していた。編集系の3経路
    (/item/edit, /item/iframe/edit, /record/<pid>/publish)で
    認証が実質無効になっていたので、編集権限そのものを見るよう変更した。
    """
    depid, recid, parent, doi, record, item = db_records[0]
    with app.test_request_context():
        assert edit_permission_factory(record).can() == False

    # 閲覧用の判定は従来どおり(公開アイテムなら匿名でも True)。
    # ここが True のままであることが、上の False が「閲覧判定を流用していない」
    # ことの裏付けになる。
    with app.test_request_context():
        assert page_permission_factory(record, flg='Edit').can() == True


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_permissions.py::test_edit_permission_factory  -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-ui/.tox/c1/tmp
@pytest.mark.parametrize("index,expected", [
    (7, True),   # user … test_records.json の owner / created_by (=1) と一致
    (0, False),  # contributor … 所有者でも管理者でもない
    (2, True),   # sysadmin … 所有者でなくても通る
])
def test_edit_permission_factory(app, db_records, users, index, expected):
    """所有者と管理者だけが編集できる。"""
    depid, recid, parent, doi, record, item = db_records[0]
    with patch("flask_login.utils._get_user", return_value=users[index]["obj"]):
        with app.test_request_context():
            assert edit_permission_factory(record).can() == expected
