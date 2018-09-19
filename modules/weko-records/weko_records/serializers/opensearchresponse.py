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

from flask import current_app, render_template

def oepnsearch_responsify(serializer):
    """Create a Records-REST search result response serializer.

    :param serializer: Serializer instance.
    :param mimetype: MIME type of response.
    :returns: Function that generates a record HTTP response.
    """
    def view(pid_fetcher, search_result, code=200, headers=None, links=None,
             item_links_factory=None):

        data, mimetype = serializer.serialize_search(pid_fetcher,
                                                     search_result,
                                                     links=links,
                                                     item_links_factory=item_links_factory)

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
