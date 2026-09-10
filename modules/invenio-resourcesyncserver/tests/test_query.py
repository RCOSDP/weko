import os
import json
import copy
import pytest
import unittest
import datetime
from elasticsearch import helpers
from mock import patch, MagicMock, Mock
from flask import current_app, make_response, request, Flask
from flask_login import current_user
from flask_babelex import Babel

from invenio_resourcesyncserver.query import (
    get_items_by_index_tree,
    get_item_changes_by_index,
    item_path_search_factory,
    item_changes_search_factory
)


# def get_items_by_index_tree(index_tree_id):
# def get_item_changes_by_index(index_tree_id, date_from, date_until):
# .tox/c1/bin/pytest --cov=invenio_resourcesyncserver tests/test_query.py::test_get_items_by_index_tree -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-resourcesyncserver/.tox/c1/tmp
def test_get_items_by_index_tree(i18n_app, indices, esindex):
    index_tree_id = 33
    date_from = (datetime.datetime.now() - datetime.timedelta(days=3)).isoformat()
    date_until = datetime.datetime.now().isoformat()

    assert get_items_by_index_tree(index_tree_id) == []
    assert get_item_changes_by_index(index_tree_id, date_from, date_until) == []

    def _generate_es_data(num, start_datetime=datetime.datetime.now()):
        for i in range(num):
            doc = {
                "_index": i18n_app.config['INDEXER_DEFAULT_INDEX'],
                "_type": "item-v1.0.0",
                "_id": f"2d1a2520-9080-437f-a304-230adc8{i:05d}",
                "_source": {
                    "_item_metadata": {
                        "title": [f"test_title_{i}"],
                    },
                    "relation_version_is_last": True,
                    "path": ["66"],
                    "control_number": f"{i:05d}",
                    "_created": (start_datetime + datetime.timedelta(seconds=i) - datetime.timedelta(days=2)).isoformat(),
                    "_updated": (start_datetime + datetime.timedelta(seconds=i) - datetime.timedelta(days=1)).isoformat(),
                    "publish_date": (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
                    "publish_status": "0",
                },
            }
            yield doc

    generate_data_num = 20002
    helpers.bulk(esindex, _generate_es_data(generate_data_num), refresh='true')

    # result over 10000
    assert len(get_items_by_index_tree(66)) == generate_data_num
    assert len(get_item_changes_by_index(66, date_from, date_until)) == generate_data_num


# def item_path_search_factory(search, index_id="0"):
def test_item_path_search_factory(i18n_app, indices):
    search = MagicMock()
    data_1 = MagicMock()

    assert item_path_search_factory(search, index_id=33)

    with patch("weko_index_tree.api.Indexes.get_list_path_publish", return_value="test"):
        with patch("weko_index_tree.api.Indexes.get_child_list", return_value=[MagicMock()]):
            assert item_path_search_factory(data_1, index_id="Root Index")

    assert item_path_search_factory(data_1, index_id=33)


# def item_changes_search_factory(search, index_id=0, date_from="now/d", date_until="now/d"):
def test_item_changes_search_factory(i18n_app, indices):
    search = MagicMock()

    assert item_changes_search_factory(search, index_id=33)

    with patch("weko_index_tree.api.Indexes.get_list_path_publish", return_value="test"):
        with patch("weko_index_tree.api.Indexes.get_child_list", return_value=[MagicMock()]):
            assert item_changes_search_factory(search, index_id="Root Index")

@pytest.mark.parametrize("fix_access, is_root, date_until, rq_none, expect_range, expect_updated", [
    # fix_access, is_root, date_until, rq_none, expect_range, expect_updated
    (True, False, '2020-12-31T23:59:59', False, True, False),   # 19 digits, range_query enabled
    (True, False, '2020-12-31', False, True, False),            # 10 digits, range_query enabled
    (True, False, 'invalid', False, True, False),               # invalid value, range_query enabled
    (True, False, '2020-12-31T23:59:59', True, False, False),   # 19 digits, range_query is None
    (False, False, '2020-12-31T23:59:59', False, False, True),  # fix_access=False, _updated
    (True, True, '2020-12-31T23:59:59', False, True, False),    # root, range_query enabled
    (False, True, '2020-12-31T23:59:59', False, False, True),   # root, fix_access=False
    (True, True, '2020-12-31', False, True, False),             # root, 10 digits, range_query enabled
    (True, True, 'invalid', True, False, False),                # root, invalid value, range_query is None
])
# .tox/c1/bin/pytest --cov=invenio_resourcesyncserver tests/test_query.py::test_item_changes_search_factory_branch -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-resourcesyncserver/.tox/c1/tmp
def test_item_changes_search_factory_branch(monkeypatch, fix_access, is_root, date_until, rq_none, expect_range, expect_updated):
    # Flask Apps and Config
    app = Flask(__name__)
    app.config['WEKO_SEARCH_FIX_ACCESSRIGHTS'] = fix_access
    app.config['WEKO_ROOT_INDEX'] = 0

    # mock
    class DummySearch:
        def __init__(self):
            self.query = None
        def update_from_dict(self, q):
            self.query = q

    class DummyItem:
        cid = 'dummy'

    class DummyIndexes:
        @staticmethod
        def get_list_path_publish(index_id):
            return [1, 2, 3]
        @staticmethod
        def get_child_list(q):
            return [DummyItem()]

    called = {'range_query': False}
    def fake_range_query(*args, **kwargs):
        called['range_query'] = True
        if rq_none:
            return None
        class DummyRQ:
            def to_dict(self):
                return {'RANGE_QUERY': True}
        return DummyRQ()

    # Get the modules to be imported
    from invenio_resourcesyncserver import query as query_mod
    monkeypatch.setattr(query_mod, "range_query", fake_range_query)
    monkeypatch.setattr(query_mod, "Indexes", DummyIndexes)

    with app.app_context():
        search = DummySearch()
        index_id = 0 if is_root else 1
        result = query_mod.item_changes_search_factory(
            search, index_id=index_id, date_from='2020-01-01', date_until=date_until
        )
        q = result.query
        if expect_range:
            assert any(
                (isinstance(m, dict) and 'RANGE_QUERY' in m) or
                (hasattr(m, 'to_dict') and 'RANGE_QUERY' in m.to_dict())
                for m in q['post_filter']['bool']['must']
            )
            assert called['range_query']
        else:
            # If range_query is None, RANGE_QUERY should not be included in must
            assert not any(
                (isinstance(m, dict) and 'RANGE_QUERY' in m) or
                (hasattr(m, 'to_dict') and 'RANGE_QUERY' in m.to_dict())
                for m in q['post_filter']['bool']['must']
            )
        if expect_updated:
            assert any(
                (isinstance(m, dict) and '_updated' in m.get('range', {})) or
                (hasattr(m, 'to_dict') and '_updated' in m.to_dict().get('range', {}))
                for m in q['post_filter']['bool']['must']
            )

def test_item_changes_search_factory_except_baseexception(monkeypatch):
    from invenio_resourcesyncserver import query as query_mod
    from flask import Flask
    class DummySearch:
        def update_from_dict(self, q):
            pass
    # Mock json.dumps to raise TypeError
    monkeypatch.setattr(query_mod.json, "dumps", lambda *a, **k: (_ for _ in ()).throw(TypeError("dummy")))
    # Mock Indexes.get_list_path_publish
    monkeypatch.setattr(query_mod.Indexes, "get_list_path_publish", lambda idx: ["dummy"])
    app = Flask(__name__)
    app.config["WEKO_ROOT_INDEX"] = 0
    with app.app_context():
        search = DummySearch()
        # Confirm that the exception is suppressed and the function returns normally
        result = query_mod.item_changes_search_factory(search, index_id=1)
        assert result is not None

def test_item_changes_search_factory_except_syntaxerror(monkeypatch):
    from invenio_resourcesyncserver import query as query_mod
    from flask import Flask
    class DummySearch:
        def update_from_dict(self, q):
            raise SyntaxError("dummy syntax error")
    # Mock Indexes.get_list_path_publish
    monkeypatch.setattr(query_mod.Indexes, "get_list_path_publish", lambda idx: ["dummy"])
    app = Flask(__name__)
    app.config["WEKO_ROOT_INDEX"] = 0
    with app.app_context():
        search = DummySearch()
        with pytest.raises(query_mod.InvalidQueryRESTError):
            query_mod.item_changes_search_factory(search, index_id=1)
