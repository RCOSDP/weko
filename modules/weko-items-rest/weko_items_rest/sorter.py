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

r"""Sorter factory for REST API.

The default sorter factory allows you to define possible sort options in
the ``ITEMS_REST_SORT_OPTIONS`` configuration variable. The sort options
are defined per index alias (e.g. ``records``). If more fine grained control
is needed a custom sorter factory can be provided to Records-REST instead.

See Elasticsearch Reference Manual for full details of sorting capabilities:
https://www.elastic.co/guide/en/elasticsearch/reference/2.x\
/search-request-sort.html
"""

import copy

from flask import current_app, request


def geolocation_sort(field_name, argument, unit, mode=None,
                     distance_type=None):
    """Sort field factory for geo-location based sorting.

    :param field_name: field name for sort
    :param argument: Name of URL query string field to parse pin location from.
        Multiple locations can be provided. Each location can be either a
        string "latitude,longitude" or a geohash.
    :param unit: Distance unit (e.g. km).
    :param mode: Sort mode (avg, min, max).
    :param distance_type: Distance calculation mode.
    :returns: Function that returns geolocation sort field.
    """
    def inner(asc):
        locations = request.values.getlist(argument, type=str)
        field = {
            '_geo_distance': {
                field_name: locations,
                'order': 'asc' if asc else 'desc',
                'unit': unit,
            }
        }
        if mode:
            field['_geo_distance']['mode'] = mode
        if distance_type:
            field['_geo_distance']['distance_type'] = distance_type
        return field

    return inner


def parse_sort_field(field_value):
    """Parse a URL field.

    :param field_value: Field value (e.g. 'key' or '-key').
    :returns: Tuple of (field, ascending) as string and boolean.
    """
    if field_value.startswith("-"):
        return (field_value[1:], False)
    return (field_value, True)


def reverse_order(order_value):
    """Reserve ordering of order value (asc or desc).

    :param order_value: Either the string ``asc`` or ``desc``.
    :returns: Reverse sort order of order value.
    """
    if order_value == 'desc':
        return 'asc'
    elif order_value == 'asc':
        return 'desc'
    return None


def eval_field(field, asc):
    """Evaluate a field for sorting purpose.

    :param field: Field definition (string, dict or callable).
    :param asc: ``True`` if order is ascending, ``False`` if descending.
    :returns: Dictionary with the sort field query.
    """
    if isinstance(field, dict):
        if asc:
            return field
        else:
            # Field should only have one key and must have an order subkey.
            field = copy.deepcopy(field)
            key = list(field.keys())[0]
            field[key]['order'] = reverse_order(field[key]['order'])
            return field
    elif callable(field):
        return field(asc)
    else:
        key, key_asc = parse_sort_field(field)
        if not asc:
            key_asc = not key_asc
        return {key: {'order': 'asc' if key_asc else 'desc'}}


def default_sorter_factory(search, index):
    """Default sort query factory.

    :param search: Search query.
    :param index: Index to search in.
    :returns: Tuple of (query, URL arguments).
    """
    sort_arg_name = 'sort'
    urlfield = request.values.get(sort_arg_name, '', type=str)

    # Get default sorting if sort is not specified.
    if not urlfield:
        has_query = request.values.get('q', type=str)
        urlfield = current_app.config['ITEMS_REST_DEFAULT_SORT'].get(
            index, {}).get('query' if has_query else 'noquery', '')

    # Parse sort argument
    key, asc = parse_sort_field(urlfield)

    # Get sort options
    sort_options = current_app.config['ITEMS_REST_SORT_OPTIONS'].get(
        index, {}).get(key)
    if sort_options is None:
        return (search, {})

    # Get fields to sort query by
    search = search.sort(
        *[eval_field(f, asc) for f in sort_options['fields']]
    )
    return (search, {sort_arg_name: urlfield})
