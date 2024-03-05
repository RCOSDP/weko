import pytest
from mock import patch, MagicMock

from weko_records.models import ItemType, ItemTypeEditHistory, ItemReference


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


# class ItemReference(db.Model, Timestamp): 
test = ItemReference(
    src_item_pid=1,
    dst_item_pid="1",
    reference_type="reference_type"
)


# def get_src_references(cls, pid): 
def test_get_src_references(app, db):
    db.session.add(test)
    db.session.commit()

    assert test.get_src_references(1) != None

# def get_dst_references(cls, pid): 
def test_get_dst_references(app, db):
    db.session.add(test)
    db.session.commit()

    assert test.get_dst_references("1") != None


# def relation_exists(cls, src_pid, dst_pid, reference_type): 
def test_relation_exists(app, db):
    db.session.add(test)
    db.session.commit()

    assert test.relation_exists(1,"1","reference_type") != None