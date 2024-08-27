# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Query parser."""

from datetime import datetime

from flask import current_app
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from invenio_search import RecordsSearch, current_search_client
from invenio_search.engine import dsl
from weko_index_tree.api import Indexes
from weko_index_tree.models import Index
from weko_schema_ui.models import PublishStatus
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
    def index_ids_has_future_date():
        """Get indexes."""
        query = Index.query.filter(
            Index.public_state.is_(True),
            Index.public_date > datetime.now(),
            Index.harvest_public_state.is_(True)
        )
        indexes = []
        indexes = query.yield_per(1000)
        index_ids = [index.id for index in indexes]
        return index_ids

    def get_records_has_doi():
        """Get object_uuid of PersistentIdentifier."""
        # Get object_uuid of PersistentIdentifier
        query = PersistentIdentifier.query.filter(
            PersistentIdentifier.pid_type == "doi",
            PersistentIdentifier.status == PIDStatus.REGISTERED
        )
        pids = query.all() or []
        object_uuids = [pid.object_uuid for pid in pids]
        # Get RecordMetadata
        query = RecordMetadata.query.filter(
            RecordMetadata.id.in_(object_uuids)
        )
        records = query.all() or []
        return records

    def add_condition_doi_and_future_date(query):
        """Add condition which do not get DOI."""
        index_ids = index_ids_has_future_date()
        records = get_records_has_doi()
        for record in records:
            paths = record.json.get("path", [])
            for path in paths:
                if path in index_ids:
                    query = query.post_filter(
                        "bool",
                        **{"must_not": [
                            {"term": {"_id": str(record.id)}}]})

    page_ = kwargs.get("resumptionToken", {}).get("page", 1)
    size_ = current_app.config["OAISERVER_PAGE_SIZE"]
    scroll = current_app.config["OAISERVER_RESUMPTION_TOKEN_EXPIRE_TIME"]
    scroll_id = kwargs.get("resumptionToken", {}).get("scroll_id")

    if not scroll_id:
        indexes = Indexes.get_harverted_index_list()

        search = (
            current_oaiserver.search_cls(
                index=current_app.config["INDEXER_DEFAULT_INDEX"],
            )
            .params(
                scroll="{0}s".format(scroll),
            )
            .extra(
                version="true",
            )
            .sort(
                {"control_number": {"order": "asc"}}
            )[(page_ - 1) * size_: page_ * size_]
        )

        if "set" in kwargs:
            if ":" in kwargs["set"]:
                sets = kwargs["set"].split(":")[-1]
            else:
                sets = kwargs["set"]
            #search = search.query("match", **{"path": kwargs["set"]})
            search = search.query("match", **{"_oai.sets": sets})
            #search = search.query("terms", **{"_oai.sets": sets})

        time_range = {}
        if "from_" in kwargs:
            time_range["gte"] = kwargs["from_"]
        if "until" in kwargs:
            time_range["lte"] = kwargs["until"]
        if time_range:
            search = search.filter(
                "range", **{current_oaiserver.last_update_key: time_range}
            )
        
        search = search.query("match", **{"relation_version_is_last": "true"})
        search = search.query("terms", **{"publish_status": [
            PublishStatus.DELETE.value,
            PublishStatus.PUBLIC.value,
            PublishStatus.PRIVATE.value]})
        #search = search.query("range", **{"publish_date": {"lte": "now/d"}})
        query_filter = []
        if indexes and "set" not in kwargs:
            indexes_num = len(indexes)
            div_indexes = []
            max_clause_count = current_app.config.get(
                "OAISERVER_ES_MAX_CLAUSE_COUNT", 1024)
            for div in range(0, int(indexes_num / max_clause_count) + 1):
                e_right = div * max_clause_count
                e_left = (div + 1) * max_clause_count \
                    if indexes_num > (div + 1) * max_clause_count \
                    else indexes_num
                div_indexes.append({
                    "terms": {
                        "_item_metadata.path.raw": indexes[e_right:e_left]
                    }
                })
            query_filter.append({
                "bool": {
                    "should": div_indexes
                }
            })
        if len(query_filter) > 0:
            search = search.query(
                "bool", **{"must": [{"bool": {"should": query_filter}}]})

        add_condition_doi_and_future_date(search)

        current_app.logger.debug("query:{}".format(search.query.to_dict()))

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
