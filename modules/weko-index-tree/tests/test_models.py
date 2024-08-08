from mock import patch

from weko_index_tree.models import Index, IndexStyle


# class Index(db.Model, Timestamp):
#     def __iter__(self):
#     def __str__(self):
#     def have_children(cls, id):
#     def get_all(cls):
#     def get_index_by_id(cls, index):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_models.py::test_Index -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_Index(app, db, test_indices):
    # have_children
    res = Index.have_children(100)
    assert res == False
    res = Index.have_children(100, with_deleted=True)
    assert res == True

    # get_all
    res = Index.get_all()
    assert len(res) == 7
    res = Index.get_all(with_deleted=True)
    assert len(res) == 11

    # get_index_by_id
    res = Index.get_index_by_id(1)
    assert res.id == 1
    assert res.index_name == "テストインデックス 1"
    res = Index.get_index_by_id(32)
    assert res == None
    res = Index.get_index_by_id(32, with_deleted=True)
    assert res.id == 32
    assert res.index_name == "テストインデックス 32"

    # __str__
    res = Index.get_index_by_id(1)
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        assert str(res) == "Index <id=1, name=Test index 1>"
    with app.test_request_context(headers=[("Accept-Language", "ja")]):
        assert str(res) == "Index <id=1, name=テストインデックス 1>"


# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_models.py::test_Index_get_all -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_Index_get_all(app, db):
    res = Index.get_all()
    assert len(res) == 0



# class IndexStyle(db.Model, Timestamp):
#     def create(cls, community_id, **data):
#     def get(cls, community_id):
#     def update(cls, community_id, **data):
# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_models.py::test_IndexStyle -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
def test_IndexStyle(app, db):
    _data1 = {
        "width": "3",
        "height": "10"
    }
    _data2 = {
        "a": "3",
        "b": "10"
    }
    # create
    res = IndexStyle.create("weko", **{})
    assert res.id == "weko"
    assert res.width == ""
    assert res.height == ""
    assert res.index_link_enabled == False

    # update
    res = IndexStyle.update("weko", **_data1)
    assert res.id == "weko"
    assert res.width == "3"
    assert res.height == "10"

    res = IndexStyle.update("weko", **_data2)
    assert res.id == "weko"
    assert res.width == "3"
    assert res.height == "10"

    res = IndexStyle.update("weko2", **_data2)
    assert res == None

    # Exception
    with patch("weko_index_tree.models.db.session.commit", side_effect=Exception):
        res = IndexStyle.create("weko1", **{})
        assert res == None

        res = IndexStyle.update("weko", **_data1)
        assert res == None