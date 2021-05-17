# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Serialization response factories.

Responsible for creating a HTTP response given the output of a serializer.
"""

from flask import current_app

from weko_records.utils import replace_fqdn, replace_fqdn_of_file_metadata


def oepnsearch_responsify(serializer):
    """Create a Records-REST search result response serializer.

    :param serializer: Serializer instance.
    :param mimetype: MIME type of response.
    :returns: Function that generates a record HTTP response.

    """
    def view(pid_fetcher, search_result, code=200, headers=None, links=None,
             item_links_factory=None):

        if search_result['hits']['hits'] and \
                len(search_result['hits']['hits']) > 0:
            custom_output_open_search(search_result['hits']['hits'])
        data, mimetype = serializer.serialize_search(
            pid_fetcher, search_result, links=links, item_links_factory=item_links_factory)

        response = current_app.response_class(data, mimetype=mimetype)
        response.status_code = code
        if headers is not None:
            response.headers.extend(headers)

        if links is not None:
            add_link_header(response, links)

        return response
    return view


def add_link_header(response, links):
    """Add a Link HTTP header to a REST response.

    :param response: REST response instance
    :param links: Dictionary of links

    """
    if links is not None:
        response.headers.extend({
            'Link': ', '.join([
                '<{0}>; rel="{1}"'.format(l, r) for r, l in links.items()])
        })


def custom_output_open_search(record_lst: list):
    """Custom output data of open search.

    Args:
        record_lst (list): Record list.
    """
    def _format_file_url():
        for v in _item_metadata.values():
            if isinstance(v, dict) and v.get('attribute_type') == 'file':
                replace_fqdn_of_file_metadata(v.get('attribute_value_mlt', []))
        for file_value in _file_meta.get('URI', []):
            if file_value.get('value'):
                file_value['value'] = replace_fqdn(file_value['value'])

    for record in record_lst:
        _item_metadata = record.get('_source', {}).get('_item_metadata', {})
        _file_meta = record.get('_source', {}).get('file', {})
        _format_file_url()
