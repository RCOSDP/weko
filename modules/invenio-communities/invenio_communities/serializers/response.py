# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

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
