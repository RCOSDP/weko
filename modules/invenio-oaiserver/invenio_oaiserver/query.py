# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Query parser."""

from flask import current_app
from invenio_search import RecordsSearch, current_search_client
from invenio_search.engine import dsl
from werkzeug.utils import cached_property, import_string

from invenio_oaiserver.errors import OAINoRecordsMatchError

from . import current_oaiserver


def query_string_parser(search_pattern):
    """Search query string parser."""
    if not hasattr(current_oaiserver, "query_parser"):
        query_parser = current_app.config["OAISERVER_QUERY_PARSER"]
        if isinstance(query_parser, str):
            query_parser = import_string(query_parser)
        current_oaiserver.query_parser = query_parser
    query_parser_fields = (
        current_app.config.get("OAISERVER_QUERY_PARSER_FIELDS", {}) or {}
    )
    if query_parser_fields:
        query_parser_fields = dict(fields=query_parser_fields)
    return current_oaiserver.query_parser(
        "query_string", query=search_pattern, **query_parser_fields
    )


class OAIServerSearch(RecordsSearch):
    """Define default filter for quering OAI server."""

    class Meta:
        """Configuration for OAI server search."""

        default_filter = dsl.Q("exists", field="_oai.id")


def get_records(**kwargs):
    """Get records paginated."""
    page_ = kwargs.get("resumptionToken", {}).get("page", 1)
    size_ = current_app.config["OAISERVER_PAGE_SIZE"]
    scroll = current_app.config["OAISERVER_RESUMPTION_TOKEN_EXPIRE_TIME"]
    scroll_id = kwargs.get("resumptionToken", {}).get("scroll_id")

    if scroll_id is None:
        search = (
            current_oaiserver.search_cls(
                index=current_app.config["OAISERVER_RECORD_INDEX"],
            )
            .params(
                scroll="{0}s".format(scroll),
            )
            .extra(
                version=True,
            )[(page_ - 1) * size_ : page_ * size_]
        )

        if "set" in kwargs:
            search = search.query(
                current_oaiserver.set_records_query_fetcher(kwargs["set"])
            )

        time_range = {}
        if "from_" in kwargs:
            time_range["gte"] = kwargs["from_"]
        if "until" in kwargs:
            time_range["lte"] = kwargs["until"]
        if time_range:
            search = search.filter(
                "range", **{current_oaiserver.last_update_key: time_range}
            )

        response = search.execute().to_dict()
    else:
        response = current_search_client.scroll(
            scroll_id=scroll_id,
            scroll="{0}s".format(scroll),
        )

    class Pagination(object):
        """Dummy pagination class."""

        page = page_
        per_page = size_

        def __init__(self, response):
            """Initilize pagination."""
            self.response = response
            self.total = response["hits"]["total"]["value"]
            self._scroll_id = response.get("_scroll_id")

            if self.total == 0:
                raise OAINoRecordsMatchError()

            # clean descriptor on last page
            if not self.has_next:
                current_search_client.clear_scroll(scroll_id=self._scroll_id)
                self._scroll_id = None

        @cached_property
        def has_next(self):
            """Return True if there is next page."""
            return self.page * self.per_page <= self.total

        @cached_property
        def next_num(self):
            """Return next page number."""
            return self.page + 1 if self.has_next else None

        @property
        def items(self):
            """Return iterator."""
            from datetime import datetime

            for result in self.response["hits"]["hits"]:
                yield {
                    "id": result["_id"],
                    "json": result,
                    "updated": datetime.strptime(
                        result["_source"][current_oaiserver.last_update_key][:19],
                        "%Y-%m-%dT%H:%M:%S",
                    ),
                }

    return Pagination(response)
