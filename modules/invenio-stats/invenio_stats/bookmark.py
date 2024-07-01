# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2019 CERN.
# Copyright (C)      2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""BookMark used by aggregations."""

from collections import OrderedDict
from datetime import datetime, timedelta
from functools import wraps

from invenio_search.engine import dsl, search
from invenio_search.utils import prefix_index

SUPPORTED_INTERVALS = OrderedDict(
    [
        ("hour", "%Y-%m-%dT%H"),
        ("day", "%Y-%m-%d"),
        ("month", "%Y-%m"),
    ]
)


def format_range_dt(dt, interval):
    """Format range filter datetime to the closest aggregation interval."""
    dt_rounding_map = {"hour": "h", "day": "d", "month": "M", "year": "y"}

    if not isinstance(dt, str):
        dt = dt.replace(microsecond=0).isoformat()
    return f"{dt}||/{dt_rounding_map[interval]}"


class BookmarkAPI(object):
    """Bookmark API class.

    It provides an interface that lets us interact with a bookmark.
    """

    MAPPINGS = {
        "mappings": {
            "dynamic": "strict",
            "properties": {
                "date": {"type": "date", "format": "date_optional_time"},
                "aggregation_type": {"type": "keyword"},
            },
        }
    }

    def __init__(self, client, agg_type, agg_interval):
        """Construct bookmark instance.

        :param client: search client
        :param agg_type: aggregation type for the bookmark
        """
        self.bookmark_index = prefix_index("stats-bookmarks")
        self.client = client
        self.agg_type = agg_type
        self.agg_interval = agg_interval

    def _ensure_index_exists(func):
        """Decorator for ensuring the bookmarks index exists."""

        @wraps(func)
        def wrapped(self, *args, **kwargs):
            if not dsl.Index(self.bookmark_index, using=self.client).exists():
                self.client.indices.create(
                    index=self.bookmark_index, body=BookmarkAPI.MAPPINGS
                )
            return func(self, *args, **kwargs)

        return wrapped

    @_ensure_index_exists
    def set_bookmark(self, value):
        """Set bookmark for starting next aggregation."""
        self.client.index(
            index=self.bookmark_index,
            body={"date": value, "aggregation_type": self.agg_type},
        )
        self.new_timestamp = None

    @_ensure_index_exists
    def get_bookmark(self, refresh_time=60):
        """Get last aggregation date."""
        # retrieve the oldest bookmark
        query_bookmark = (
            dsl.Search(using=self.client, index=self.bookmark_index)
            .filter("term", aggregation_type=self.agg_type)
            .sort({"date": {"order": "desc"}})
            .extra(size=1)  # fetch one document only
        )
        bookmark = next(iter(query_bookmark.execute()), None)
        if bookmark:
            try:
                my_date = datetime.fromisoformat(bookmark.date)
            except ValueError:
                # This one is for backwards compatibility, when the bookmark did not have the time
                my_date = datetime.strptime(
                    bookmark.date, SUPPORTED_INTERVALS[self.agg_interval]
                )
            # By default, the bookmark returns a slightly sooner date, to make sure that documents
            # that had arrived before the previous run and where not indexed by the engine are caught in this run
            # This means that some events might be processed twice
            if refresh_time:
                my_date -= timedelta(seconds=refresh_time)
            return my_date

    @_ensure_index_exists
    def list_bookmarks(self, start_date=None, end_date=None, limit=None):
        """List bookmarks."""
        query = (
            dsl.Search(
                using=self.client,
                index=self.bookmark_index,
            )
            .filter("term", aggregation_type=self.agg_type)
            .sort({"date": {"order": "desc"}})
        )

        range_args = {}
        if start_date:
            range_args["gte"] = format_range_dt(start_date, self.agg_interval)
        if end_date:
            range_args["lte"] = format_range_dt(end_date, self.agg_interval)
        if range_args:
            query = query.filter("range", date=range_args)

        return query[0:limit].execute() if limit else query.scan()
