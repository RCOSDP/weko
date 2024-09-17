# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Bookmark tests."""

import pytest

from unittest.mock import patch

from invenio_stats.bookmark import BookmarkAPI

# class BookmarkAPI(object):
#     def __init__(self, agg_type, agg_interval):
#     def set_bookmark(self, value):
#     def get_bookmark(self):
#     def list_bookmarks(self):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_bookmark.py::TestBookmarkAPI -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-stats/.tox/c1/tmp --full-trace
class TestBookmarkAPI(object):
    """Test BookmarkAPI class."""

    # def __init__(self):
    # .tox/c1/bin/pytest --cov=invenio_stats tests/test_bookmark.py::TestBookmarkAPI::test_constructor -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-stats/.tox/c1/tmp --full-trace
    def test_constructor(self, app):
        """Test BookmarkAPI constructor."""
        agg_type, agg_interval = "test", "hour"

        with app.app_context():
            bookmark = BookmarkAPI(agg_type, agg_interval)

        assert bookmark is not None
        assert bookmark.bookmark_index == "test-stats-bookmarks"
        assert bookmark.agg_type == agg_type
        assert bookmark.agg_interval == agg_interval

    def test_set_bookmark(self):
        """Test BookmarkAPI.set_bookmark."""

    def test_get_bookmark(self):
        """Test BookmarkAPI.get_bookmark."""

    def test_list_bookmarks(self):
        """Test BookmarkAPI.list_bookmarks."""
