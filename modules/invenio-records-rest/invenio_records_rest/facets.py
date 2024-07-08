# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Facets and factories for result filtering and aggregation.

See :data:`invenio_records_rest.config.RECORDS_REST_FACETS` for more
information on how to specify aggregations and filters.
"""

from flask import current_app, request
from invenio_rest.errors import FieldError, RESTValidationError
from invenio_search.engine import dsl
from six import text_type
from werkzeug.datastructures import MultiDict

from invenio_records_rest.utils import make_comma_list_a_list


def nested_filter(field, subfield):
    """Create a nested filter.

    Similar to the example from
    https://github.com/inveniosoftware/invenio-records-resources/blob/master/invenio_records_resources/services/records/facets/facets.py#L94
    """

    def inner(values):
        top_level = []
        queries = []
        for value in values:
            subvalues = value.split("::")
            if len(subvalues) > 1:
                queries.append(
                    dsl.Q(
                        "bool",
                        must=[
                            dsl.Q("term", **{field: subvalues[0]}),
                            dsl.Q("term", **{subfield: subvalues[1]}),
                        ],
                    )
                )
            else:
                top_level.append(value)
        if len(top_level):
            queries.append(dsl.Q("terms", **{field: top_level}))

        if len(queries) > 1:
            return dsl.Q("bool", should=queries)
        return queries[0]

    return inner


def terms_filter(field):
    """Create a term filter.

    :param field: Field name.
    :returns: Function that returns the Terms query.
    """

    def inner(values):
        return dsl.Q("terms", **{field: values})

    return inner


def range_filter(field, start_date_math=None, end_date_math=None, **kwargs):
    """Create a range filter.

    :param field: Field name.
    :param start_date_math: Starting date.
    :param end_date_math: Ending date.
    :param kwargs: Addition arguments passed to the Range query.
    :returns: Function that returns the Range query.
    """

    def inner(values):
        queries = []
        for value in values:
            if value.count("--") != 1 or value == "--":
                raise RESTValidationError(
                    errors=[FieldError(field, "Invalid range format.")]
                )

            range_ends = value.split("--")
            range_args = dict()

            ineq_opers = [
                {"strict": "gt", "nonstrict": "gte"},
                {"strict": "lt", "nonstrict": "lte"},
            ]
            date_maths = [start_date_math, end_date_math]

            # Add the proper values to the dict
            for range_end, strict, opers, date_math in zip(
                range_ends, [">", "<"], ineq_opers, date_maths
            ):
                if range_end != "":
                    # If first char is '>' for start or '<' for end
                    if range_end[0] == strict:
                        dict_key = opers["strict"]
                        range_end = range_end[1:]
                    else:
                        dict_key = opers["nonstrict"]

                    if date_math:
                        range_end = "{0}||{1}".format(range_end, date_math)

                    range_args[dict_key] = range_end

            args = kwargs.copy()
            args.update(range_args)

            queries.append(dsl.query.Range(**{field: args}))

        if len(queries) > 1:
            return dsl.Q("bool", should=queries)
        return queries[0]

    return inner


def _create_filter_dsl(urlkwargs, definitions):
    """Create a filter DSL expression."""
    filters = []
    for name, filter_factory in definitions.items():
        values = request.values.getlist(name, type=text_type)
        if values:
            filters.append(filter_factory(values))
            for v in values:
                urlkwargs.add(name, v)

    return (filters, urlkwargs)


def _post_filter(search, urlkwargs, definitions):
    """Ingest post filter in query."""
    filters, urlkwargs = _create_filter_dsl(urlkwargs, definitions)

    for filter_ in filters:
        search = search.post_filter(filter_)

    return (search, urlkwargs)


def _query_filter(search, urlkwargs, definitions):
    """Ingest query filter in query."""
    filters, urlkwargs = _create_filter_dsl(urlkwargs, definitions)

    for filter_ in filters:
        search = search.filter(filter_)

    return (search, urlkwargs)


def remove_filter_from_list(facet_filters, facet_names):
    """Remove the specified filters from the list.

    This is used to remove one category from the filters. Check the example defined on line 204-215.
    The reasoning behind is that a post_filter on a category should be applied to all the aggregations except the
    aggregation on that particular category.
    """
    new_facet_filters = facet_filters.copy()
    for name in facet_names:
        new_facet_filters.pop(name)
    return new_facet_filters


def _aggregations(search, definitions, updated_filters={}, urlkwargs=None):
    """Add aggregations to query."""
    if definitions:
        for name, agg in definitions.items():
            if name in updated_filters:
                # Read the example introduced in lines 204-215.
                # Imagine that our initial query and aggregation looks like
                # {"post_filter": { "term": {"brand":"ferrari"}},
                #  "aggs": {"brand": {"term": {"field":"brand"}},
                #           "color": {"term": {"field": "color"}}}}
                # The goal is that the previous query will be transformed into something like
                # {"post_filter": { "term": {"brand":"ferrari"}},
                #  "aggs": {"brand": {"term": {"field":"brand"}},
                #           "color": {"filter": {"bool":{ "must": [{"term": {"brand": "ferrari"}}]}},
                #                     "aggs": {"filtered": {"term": {"field": "color"}}}}}}}

                facet_filters, _ = _create_filter_dsl(
                    urlkwargs, remove_filter_from_list(updated_filters, [name])
                )
                agg = {
                    "filter": {
                        "bool": {
                            "must": [
                                facet_filter.to_dict() for facet_filter in facet_filters
                            ]
                        }
                    },
                    "aggs": {"filtered": agg},
                }
            search.aggs[name] = agg if not callable(agg) else agg()
    return search


def default_facets_factory(search, index):
    """Add a default facets to query.

    It's possible to select facets which should be added to query
    by passing their name in `facets` parameter.

    :param search: Basic search object.
    :param index: Index name.
    :returns: A tuple containing the new search object and a dictionary with
        all fields and values used.
    """
    urlkwargs = MultiDict()

    from weko_admin.utils import get_facet_search_query
    from weko_search_ui.permissions import search_permission
    facets = get_facet_search_query(search_permission.can()).get(index)

    if facets is not None:
        # Aggregations.
        # First get requested facets, also split by ',' to get facets names
        # if they were provided as list separated by comma.
        selected_facets = make_comma_list_a_list(request.args.getlist("facets", None))
        all_aggs = facets.get("aggs", {})

        # This parameter is a bit tricky. Let's go first with an example to see the goal.
        # Imagine a website that sells cars, where the cars can be filtered by two categories: brand and color.
        # There is a facet with the brand: bmw, mercedes, ferrari,... and another with the color: white, blue, red, ...
        # Imagine that a user looks for ferrari:
        # * If the query is done as a standard filter, it will also affect the aggregations, so the aggregations will
        #    return only brand: ferrari, color:red.
        # * If the query is done as a post_filter, with RECORDS_REST_FACETS_POST_FILTERS_PROPAGATE=False, the
        #    restrictions will not be applied to the categories, so brand: bmw, mercedes, ferrari,... and
        #    color: white, blue, red, ...
        #  * If the query is done as a post_filter, with RECORDS_REST_FACETS_POST_FILTERS_PROPAGATE=True, the
        #    restrictions will be applied to the other categories, so brand: bmw, mercedes, ferrari,... (since the
        #    filter on ferrari is not applied on the brand, and color: red (since all the ferraris are red).
        if current_app.config["RECORDS_REST_FACETS_POST_FILTERS_PROPAGATE"]:
            updated_filters = facets.get("post_filters", {})
        else:
            updated_filters = {}

        # If no facets were requested, assume default behaviour - Take all.
        if all_aggs:
            if not selected_facets:
                search = _aggregations(search, all_aggs, updated_filters, urlkwargs)
            # otherwise, check if there are facets to chose
            else:
                aggs = {}
                # Go through all available facets and check if they were requested.
                for facet_name, facet_body in all_aggs.items():
                    if facet_name in selected_facets:
                        aggs.update({facet_name: facet_body})
                search = _aggregations(search, aggs, updated_filters, urlkwargs)

        # Query filter
        search, urlkwargs = _query_filter(search, urlkwargs, facets.get("filters", {}))

        # Post filter
        search, urlkwargs = _post_filter(
            search, urlkwargs, facets.get("post_filters", {})
        )

    return (search, urlkwargs)
