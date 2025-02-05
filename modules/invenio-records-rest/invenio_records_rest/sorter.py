# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

r"""Sorter factories for REST API.

The default sorter factory allows you to define possible sort options in
the :data:`invenio_records_rest.config.RECORDS_REST_SORT_OPTIONS`
configuration variable. The sort options are defined per index alias
(e.g. ``records``). If more fine grained control is needed a custom sorter
factory can be provided to Records-REST instead.

See Elasticsearch Reference Manual for full details of sorting capabilities:
https://www.elastic.co/guide/en/elasticsearch/reference/2.4/search-request-sort.html
"""

from __future__ import absolute_import, print_function

import pickle

import six
from flask import current_app, request
from invenio_i18n.ext import current_i18n

from .config import RECORDS_REST_DEFAULT_SORT


def geolocation_sort(field_name, argument, unit, mode=None,
                     distance_type=None):
    """Sort field factory for geo-location based sorting.

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


def eval_field(field, asc, nested_sorting=None):
    """Evaluate a field for sorting purpose.

    :param field: Field definition (string, dict or callable).
    :param asc: ``True`` if order is ascending, ``False`` if descending.
    :param nested_sorting: nested_sorting definition (dict or None).
    :returns: Dictionary with the sort field query.
    """
    if isinstance(field, dict):
        if asc:
            return field
        else:
            # Field should only have one key and must have an order subkey.
            field = pickle.loads(pickle.dumps(field, -1))
            key = list(field.keys())[0]
            field[key]['order'] = reverse_order(field[key]['order'])
            return field
    elif callable(field):
        return field(asc)
    else:
        key, key_asc = parse_sort_field(field)
        if not asc:
            key_asc = not key_asc

        sorting = {key: {'order': 'asc' if key_asc else 'desc',
                         'unmapped_type': 'long'}}

        if "title" in key:
            # When sorting by Title, change the sorting rules according to the language setting.
            if "ja" in current_i18n.language:
                #If there is more than one data set and the data is displayed in Japanese, the larger value is used.
                sorting = {key: {'order': 'asc' if key_asc else 'desc',
                         'unmapped_type': 'long',
                         'mode': 'max'}}
            else:
                #If there are multiple data and they are displayed in English, the smaller value is used.
                sorting = {key: {'order': 'asc' if key_asc else 'desc',
                         'unmapped_type': 'long',
                         'mode': 'min'}}

        if "date_range" in key:
            if asc:
                #Sort by "gte" in ascending order.
                sorting = {"_script":{"type":"number",
                    "script":{"lang":"painless","source":"def x = params._source.date_range1;SimpleDateFormat format = new SimpleDateFormat(); if (x != null && !x.isEmpty() ) { def value = x.get(0).get(\"gte\"); if(value != null && !value.equals(\"\")) { if(value.length() > 7) { format.applyPattern(\"yyyy-MM-dd\"); } else if(value.length() > 4) { format.applyPattern(\"yyyy-MM\");  } else { format.applyPattern(\"yyyy\"); } try { return format.parse(value).getTime(); } catch(Exception e) {} } } format.applyPattern(\"yyyy\"); return format.parse(\"9999\").getTime();"},"order": 'asc'}}

            else:
                #Sort by "lte" in ascending order.
                sorting = {"_script":{"type":"number",
                    "script":{"lang":"painless","source":"def x = params._source.date_range1;SimpleDateFormat format = new SimpleDateFormat(); if (x != null && !x.isEmpty() ) { def value = x.get(0).get(\"lte\"); if(value != null && !value.equals(\"\")) { if(value.length() > 7) { format.applyPattern(\"yyyy-MM-dd\"); } else if(value.length() > 4) { format.applyPattern(\"yyyy-MM\");  } else { format.applyPattern(\"yyyy\"); } try { return format.parse(value).getTime(); } catch(Exception e) {} } } format.applyPattern(\"yyyy\"); return format.parse(\"0\").getTime();"},"order": 'desc'}}

        if "control_number" in key:
            sorting = {"_script":{"type":"number", "script": "Float.parseFloat(doc['control_number'].value)", "order": "asc" if key_asc else "desc"}}


        if nested_sorting:
            sorting[key].update({'nested': nested_sorting})
        return sorting


def default_sorter_factory(search, index):
    """Default sort query factory.

    :param query: Search query.
    :param index: Index to search in.
    :returns: Tuple of (query, URL arguments).
    """
    sort_arg_name = 'sort'
    urlfield = request.values.get(sort_arg_name, '', type=str)

    # Get default sorting if sort is not specified.
    if not urlfield:
        # cast to six.text_type to handle unicodes in Python 2
        has_query = request.values.get('q', type=six.text_type)
        if current_app.config.get('RECORDS_REST_DEFAULT_SORT'):
            urlfield = current_app.config['RECORDS_REST_DEFAULT_SORT'].get(
                index, {}).get('query' if has_query else 'noquery', '')
        else:
            urlfield = RECORDS_REST_DEFAULT_SORT.get(
                index, {}).get('query' if has_query else 'noquery', '')
    # Parse sort argument
    key, asc = parse_sort_field(urlfield)

    # Get sort options
    sort_options = current_app.config['RECORDS_REST_SORT_OPTIONS'].get(
        index, {}).get(key)
    if sort_options is None:
        return (search, {})

    # Get fields to sort query by
    sort_field = [eval_field(f, asc, sort_options.get('nested'))
          for f in sort_options['fields']]
    if key != 'controlnumber':
        control_number_option = current_app.config['RECORDS_REST_SORT_OPTIONS'].get(index,{}).get('controlnumber')
        if control_number_option is not None:
            sort_field.append(eval_field(
                control_number_option['fields'][0],'asc',control_number_option.get('nested')
            ))
    search = search.sort(
        *sort_field,
    )
    return (search, {sort_arg_name: urlfield})
