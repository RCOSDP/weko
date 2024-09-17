# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Bookmark tests."""

from datetime import datetime
import json

from invenio_stats.bookmark import format_range_dt, BookmarkAPI
from invenio_stats.models import StatsBookmark


SEARCH_INDEX_PREFIX="test-"

# def format_range_dt(dt, interval):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_bookmark.py::test_format_range_dt -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-stats/.tox/c1/tmp --full-trace
def test_format_range_dt():
    """Test format_range_dt function."""
    # dt is string
    dt = "2024-01-01T00:00:00"
    interval = "day"

    result = format_range_dt(dt, interval)

    assert result == "2024-01-01T00:00:00||/d"

    # dt is datetime object
    dt = datetime.fromisoformat("2024-01-01")
    interval = "hour"

    result = format_range_dt(dt, interval)

    assert result == "2024-01-01T00:00:00||/h"


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
        agg_type, agg_interval = "test", "day"

        bookmark = BookmarkAPI(agg_type, agg_interval)

        assert bookmark is not None
        assert bookmark.bookmark_index == f"{SEARCH_INDEX_PREFIX}stats-bookmarks"
        assert bookmark.agg_type == agg_type
        assert bookmark.agg_interval == agg_interval


    def test_set_bookmark(self, db):
        """Test BookmarkAPI.set_bookmark."""
        agg_type, agg_interval = "test", "day"
        date = "2024-01-01"
        bookmark = BookmarkAPI(agg_type, agg_interval)

        bookmark.set_bookmark(date)

        latest_bookmark = (
            StatsBookmark.query.filter_by(source_id=agg_type)
            .order_by(StatsBookmark.date.desc()).first()
        )

        assert latest_bookmark is not None
        assert latest_bookmark.source_id == agg_type
        assert latest_bookmark.index == f"{SEARCH_INDEX_PREFIX}stats-bookmarks"
        assert json.loads(latest_bookmark.source)["date"] == date
        assert json.loads(latest_bookmark.source)["aggregation_type"] == agg_type
        assert latest_bookmark.date == datetime.fromisoformat(date)


    def test_get_bookmark(self, db):
        """Test BookmarkAPI.get_bookmark."""
        agg_type, agg_interval = "test", "day"
        bookmark = BookmarkAPI(agg_type, agg_interval)

        # when there is no bookmark
        result = bookmark.get_bookmark()

        assert result is None

        # when there is a bookmark
        index = f"{SEARCH_INDEX_PREFIX}stats-bookmarks"
        date = "2024-01-01"
        StatsBookmark.save({
            "_id": agg_type,
            "_index": index,
            "_source": {"date": date, "aggregation_type": agg_type},
        })

        result = bookmark.get_bookmark(0)

        assert result == datetime.fromisoformat(date)


    def test_list_bookmarks(self):
        """Test BookmarkAPI.list_bookmarks."""
