import os
import json
import copy
import pytest
import unittest
import datetime
from elasticsearch import helpers
from mock import patch, MagicMock, Mock
from flask import current_app, make_response, request
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
