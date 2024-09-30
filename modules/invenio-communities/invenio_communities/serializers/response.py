# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Community serializaiton."""

from __future__ import absolute_import, print_function

import json

from flask import current_app, request

from ..models import Community


def _format_args():
    """Get JSON dump indentation and separates."""
    # Ensure we can run outside a application/request context.
    try:
        pretty_format = \
            current_app.config['JSONIFY_PRETTYPRINT_REGULAR'] and \
            not request.is_xhr
    except RuntimeError:
        pretty_format = False

    if pretty_format:
        return dict(
            indent=2,
            separators=(', ', ': '),
        )
    else:
        return dict(
            indent=None,
            separators=(',', ':'),
        )


def community_responsify(schema_class, mimetype):
    """Create a community response serializer.

    :param serializer: Serializer instance.
    :param mimetype: MIME type of response.
    """
    def view(data, code=200, headers=None, links_item_factory=None,
             page=None, urlkwargs=None, links_pagination_factory=None):
        """Generate the response object."""
        if isinstance(data, Community):
            last_modified = data.updated
            response_data = schema_class(
                context=dict(item_links_factory=links_item_factory)
            ).dump(data).data
        else:
            last_modified = None
            response_data = schema_class(
                context=dict(
                    total=data.query.count(),
                    item_links_factory=links_item_factory,
                    page=page,
                    urlkwargs=urlkwargs,
                    pagination_links_factory=links_pagination_factory)
            ).dump(data.items, many=True).data

        response = current_app.response_class(
            json.dumps(response_data, **_format_args()),
            mimetype=mimetype)
        response.status_code = code

        if last_modified:
            response.last_modified = last_modified

        if headers is not None:
            response.headers.extend(headers)
        return response
    return view
