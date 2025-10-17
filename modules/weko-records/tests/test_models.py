import pytest
from mock import patch, MagicMock

from weko_records.models import ItemType, ItemTypeEditHistory, OaStatus


# class ItemType(object): 
# def latest_edit_history(self, app): 
def test_latest_edit_history(app):
    def test(item):
        return True

    data1 = MagicMock()
    data1.notes = test

    data2 = MagicMock()
    data2.notes = test

    test = ItemType()
    test.edit_notes = [data1, data2]

    assert test.latest_edit_history(app) != None


# class ItemTypeEditHistory(object): 
# def latest_edit_history(self, app): 
def test_get_latest_by_item_type_id(app):
    data1 = MagicMock()
    data1.notes = 1

    test = ItemTypeEditHistory()
    test.edit_notes = ["data1", data1]

    assert test.get_latest_by_item_type_id(app) == None


# def get_src_references(cls, pid): 
def test_get_src_references(app, db, db_ItemReference):
    assert db_ItemReference.get_src_references("1").all() == [db_ItemReference]

# def get_dst_references(cls, pid): 
def test_get_dst_references(app, db, db_ItemReference):
    assert db_ItemReference.get_dst_references("2").all() == [db_ItemReference]


# def relation_exists(cls, src_pid, dst_pid, reference_type): 
# .tox/c1/bin/pytest --cov=weko_records tests/test_models.py::test_relation_exists -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_relation_exists(app, db, db_ItemReference):
    assert db_ItemReference.relation_exists("1","2","reference_type") == True

# class OaStatus(object): 
# def get_oa_status(cls, oa_article_id):
# .tox/c1/bin/pytest --cov=weko_records tests/test_models.py::test_get_oa_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_oa_status(app, db, db_OaStatus):
    assert db_OaStatus.get_oa_status(1) == db_OaStatus

# def get_oa_status_by_weko_item_pid(cls, weko_item_pid):
# .tox/c1/bin/pytest --cov=weko_records tests/test_models.py::test_get_oa_status_by_weko_item_pid -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_get_oa_status_by_weko_item_pid(app, db, db_OaStatus):
    assert db_OaStatus.get_oa_status_by_weko_item_pid("20000001") == db_OaStatus