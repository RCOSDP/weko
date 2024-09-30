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
import json
from invenio_search.utils import prefix_index

from .models import StatsBookmark

SUPPORTED_INTERVALS = OrderedDict(
    [
        ("hour", "%Y-%m-%dT%H"),
        ("day", "%Y-%m-%d"),
        ("month", "%Y-%m"),
        ('year', '%Y'),
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

    def __init__(self, agg_type, agg_interval):
        """Construct bookmark instance.

        :param agg_type: aggregation type for the bookmark
        """
        self.bookmark_index = prefix_index("stats-bookmarks")
        self.agg_type = agg_type
        self.agg_interval = agg_interval

    def set_bookmark(self, value):
        """Set bookmark for starting next aggregation."""
        _id = self.agg_type
        _source = {"date": value, "aggregation_type": self.agg_type}

        # Save stats bookmark into Database.
        StatsBookmark.save({
            "_id": _id,
            "_index": self.bookmark_index,
            "_source": _source,
        }, delete=True)
        self.new_timestamp = None

    def get_bookmark(self, refresh_time=60):
        """Get last aggregation date."""
        db_bookmark = (
            StatsBookmark.query.filter_by(source_id=self.agg_type)
            .order_by(StatsBookmark.date.desc()).first()
        )

        if db_bookmark:
            source_date = json.loads(db_bookmark.source)['date']
            try:
                my_date = datetime.fromisoformat(source_date)
            except ValueError:
                # This one is for backwards compatibility, when the bookmark did not have the time
                my_date = datetime.strptime(
                    source_date, "%Y-%m-%dT%H:%M:%S"
                )
            # By default, the bookmark returns a slightly sooner date, to make sure that documents
            # that had arrived before the previous run and where not indexed by the engine are caught in this run
            # This means that some events might be processed twice
            if refresh_time:
                my_date -= timedelta(seconds=refresh_time)
            return my_date

    def list_bookmarks(self, start_date=None, end_date=None, limit=None):
        """List bookmarks."""
        query = StatsBookmark.get_by_source_id(self.agg_type, start_date, end_date)

        if query:
            query = sorted(query, key=lambda x: x.date, reverse=True)

            if limit:
                query = query[:limit]

        return query
