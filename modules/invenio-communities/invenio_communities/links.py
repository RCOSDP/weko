# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Links for community serialization."""

from __future__ import absolute_import, print_function

from flask import current_app, request, url_for


def default_links_item_factory(community):
    """Factory for record links generation."""
    return dict(
        self=url_for(
            'invenio_communities_rest.communities_item', community_id=community['id'], _external=True),
        html=current_app.config.get(
            'COMMUNITIES_URL_COMMUNITY_VIEW',
            '{protocol}://{host}/communities/{community_id}/'
        ).format(
            protocol=request.environ['wsgi.url_scheme'],
            host=request.environ['HTTP_HOST'],
            community_id=community['id']
        )
    )


def default_links_pagination_factory(page, urlkwargs):
    """Factory for record links generation."""
    endpoint = 'invenio_communities_rest.communities_list'

    links = {
        'self': url_for(endpoint, page=page.page, _external=True, **urlkwargs),
    }

    if page.has_prev:
        links['prev'] = url_for(endpoint, page=page.prev_num, _external=True,
                                **urlkwargs)
    if page.has_next:
        links['next'] = url_for(endpoint, page=page.next_num, _external=True,
                                **urlkwargs)

    return links
