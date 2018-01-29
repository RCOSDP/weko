# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Facets factory for REST API."""

from elasticsearch_dsl import Q
from elasticsearch_dsl.query import Range
from flask import current_app, request
from invenio_rest.errors import FieldError, RESTValidationError
from werkzeug.datastructures import MultiDict


def terms_filter(field):
    """Create a term filter.

    :param field: Field name.
    :returns: Function that returns the Terms query.
    """
    def inner(values):
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

        return Range(**{field: args})

    return inner


def _create_filter_dsl(urlkwargs, definitions):
    """Create a filter DSL expression.

    :param urlkwargs: url kwargs
    :param definitions: definitions
    """
    filters = []
    for name, filter_factory in definitions.items():
        values = request.values.getlist(name, type=str)
        if values:
            filters.append(filter_factory(values))
            for v in values:
                urlkwargs.add(name, v)

    return (filters, urlkwargs)


def _post_filter(search, urlkwargs, definitions):
    """Ingest post filter in query.

    :param search: search object
    :param urlkwargs: url kwwargs
    :param definitions: definitions
    """
    filters, urlkwargs = _create_filter_dsl(urlkwargs, definitions)

    for filter_ in filters:
        search = search.post_filter(filter_)

    return (search, urlkwargs)


def _query_filter(search, urlkwargs, definitions):
    """Ingest query filter in query.

    :param search: Search object.
    :param urlkwargs: Url kwwargs.
    :param definitions: Definitions.
    """
    filters, urlkwargs = _create_filter_dsl(urlkwargs, definitions)

    for filter_ in filters:
        search = search.filter(filter_)

    return (search, urlkwargs)


def _aggregations(search, definitions):
    """Add aggregations to query.

    :param search: Search object.
    :param definitions: Definitions.
    """
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

    facets = current_app.config['ITEMS_REST_FACETS'].get(index)

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
