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

from __future__ import absolute_import, print_function

from elasticsearch_dsl import Q
from elasticsearch_dsl.query import Range
from flask import current_app, request
from invenio_rest.errors import FieldError, RESTValidationError
from six import text_type
from werkzeug.datastructures import MultiDict


def terms_filter(field):
    """Create a term filter.

    :param field: Field name.
    :returns: Function that returns the Terms query.
    """
    return terms_condition_filter(field, False)

def terms_condition_filter(field, isAndFileter):
    """Create a term filter.

    :param field: Field name.
    :param isAndFileter: AND condition if true. OR condition if false.
    :returns: Function that returns the Terms query.
    """
    def inner(values):
        if len(values) > 1 and isAndFileter:
            q_list = []
            for value in values:
                q_list.append(Q('term', **{field: value}))
            return Q('bool', **{'must': q_list})
        return Q('terms', **{field: values})
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
        if len(values) != 1 or values[0].count('--') != 1 or values[0] == '--':
            raise RESTValidationError(
                errors=[FieldError(field, 'Invalid range format.')])
        range_ends = values[0].split('--')
        range_args = dict()

        ineq_opers = [{'strict': 'gt', 'nonstrict': 'gte'},
                      {'strict': 'lt', 'nonstrict': 'lte'}]
        date_maths = [start_date_math, end_date_math]

        # Add the proper values to the dict
        for (range_end, strict, opers,
             date_math) in zip(range_ends, ['>', '<'], ineq_opers, date_maths):

            if range_end != '':
                # If first char is '>' for start or '<' for end
                if range_end[0] == strict:
                    dict_key = opers['strict']
                    range_end = range_end[1:]
                else:
                    dict_key = opers['nonstrict']

                if date_math:
                    range_end = '{0}||{1}'.format(range_end, date_math)

                range_args[dict_key] = range_end

        args = kwargs.copy()
        args.update(range_args)
        return Q(Range(**{field: args}))

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


def _aggregations(search, definitions):
    """Add aggregations to query."""
    if definitions:
        for name, agg in definitions.items():
            search.aggs[name] = agg if not callable(agg) else agg()
    return search


def default_facets_factory(search, index):
    """Add a default facets to query.

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
        search = _aggregations(search, facets.get("aggs", {}))

        # Query filter
        search, urlkwargs = _query_filter(
            search, urlkwargs, facets.get("filters", {}))

        # Post filter
        search, urlkwargs = _post_filter(
            search, urlkwargs, facets.get("post_filters", {}))

    return (search, urlkwargs)
