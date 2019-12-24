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

"""Links for community serialization."""

from __future__ import absolute_import, print_function

from flask import current_app, request, url_for


def default_links_item_factory(community):
    """Factory for record links generation."""
    return dict(
        self=url_for(
            '.communities_item', community_id=community['id'], _external=True),
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
    endpoint = '.communities_list'

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
