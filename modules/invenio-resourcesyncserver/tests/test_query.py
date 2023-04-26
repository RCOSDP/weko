import os
import json
import copy
import pytest
import unittest
import datetime
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
def test_get_items_by_index_tree(i18n_app, indices):
    index_tree_id = 33

    assert get_items_by_index_tree(index_tree_id) == []


# def get_item_changes_by_index(index_tree_id, date_from, date_until):
def test_get_item_changes_by_index(i18n_app, indices, es):
    index_tree_id = 33
    date_from = datetime.datetime.now() - datetime.timedelta(days=3)
    date_until = datetime.datetime.now()

    assert get_item_changes_by_index(index_tree_id, date_from, date_until)


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
