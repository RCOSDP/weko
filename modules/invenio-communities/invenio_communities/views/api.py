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

"""Invenio module that adds API to communities."""

from __future__ import absolute_import, print_function

from flask import Blueprint, abort
from invenio_rest import ContentNegotiatedMethodView
from webargs import fields
from webargs.flaskparser import use_kwargs

from invenio_communities.links import default_links_item_factory, \
    default_links_pagination_factory
from invenio_communities.models import Community
from invenio_communities.serializers import community_response
from invenio_db import db

blueprint = Blueprint(
    'invenio_communities_rest',
    __name__,
    url_prefix='/communities',
    template_folder='../templates',
    static_folder='../static',
)


class CommunitiesResource(ContentNegotiatedMethodView):
    """Communities resource."""

    get_args = dict(
        query=fields.String(
            location='query',
            load_from='q',
            missing=None,
        ),
        sort=fields.String(
            location='query',
            missing=None,
        ),
        page=fields.Int(
            location='query',
            missing=1,
        ),
        size=fields.Int(
            location='query',
            missing=20,
        )
    )

    def __init__(self, serializers=None, *args, **kwargs):
        """Constructor."""
        super(CommunitiesResource, self).__init__(
            serializers,
            *args,
            **kwargs
        )

    @use_kwargs(get_args)
    def get(self, query, sort, page, size):
        """Get a list of all the communities.

        .. http:get:: /communities/(string:id)
            Returns a JSON list with all the communities.
            **Request**:
            .. sourcecode:: http
                GET /communities HTTP/1.1
                Accept: application/json
                Content-Type: application/json
                Host: localhost:5000
            :reqheader Content-Type: application/json
            **Response**:
            .. sourcecode:: http
                HTTP/1.0 200 OK
                Content-Length: 334
                Content-Type: application/json
                [
                    {
                        "id": "comm1"
                    },
                    {
                        "id": "comm2"
                    }
                ]
            :resheader Content-Type: application/json
            :statuscode 200: no error
        """
        urlkwargs = {
            'q': query,
            'sort': sort,
            'size': size,
        }

        communities = Community.filter_communities(query, sort)
        page = communities.paginate(page, size)

        links = default_links_pagination_factory(page, urlkwargs)

        links_headers = map(lambda key: ('link', 'ref="{0}" href="{1}"'.format(
            key, links[key])), links)

        return self.make_response(
            page,
            headers=links_headers,
            links_item_factory=default_links_item_factory,
            page=page,
            urlkwargs=urlkwargs,
            links_pagination_factory=default_links_pagination_factory,
        )


class CommunityDetailsResource(ContentNegotiatedMethodView):
    """Community details resource."""

    def __init__(self, serializers=None, *args, **kwargs):
        """Constructor."""
        super(CommunityDetailsResource, self).__init__(
            serializers,
            *args,
            **kwargs
        )

    def get(self, community_id):
        """Get the details of the specified community.

        .. http:get:: /communities/(string:id)
            Returns a JSON dictionary with the details of the specified
            community.
            **Request**:
            .. sourcecode:: http
                GET /communities/communities/comm1 HTTP/1.1
                Accept: application/json
                Content-Type: application/json
                Host: localhost:5000
            :reqheader Content-Type: application/json
            :query string id: ID of an specific community to get more
                              information.
            **Response**:
            .. sourcecode:: http
                HTTP/1.0 200 OK
                Content-Length: 334
                Content-Type: application/json
                {
                    "id_user": 1,
                    "description": "",
                    "title": "",
                    "created": "2016-04-05T14:56:37.051462",
                    "id": "comm1",
                    "page": "",
                    "curation_policy": ""
                }

            :resheader Content-Type: application/json
            :statuscode 200: no error
            :statuscode 404: page not found
        """
        community = Community.get(community_id)
        if not community:
            abort(404)
        etag = community.version_id
        self.check_etag(etag)
        response = self.make_response(
            community, links_item_factory=default_links_item_factory)
        response.set_etag(etag)
        return response


serializers = {'application/json': community_response}


blueprint.add_url_rule(
    '/',
    view_func=CommunitiesResource.as_view(
        'communities_list',
        serializers=serializers,
        default_media_type='application/json',
    ),
    methods=['GET']
)


blueprint.add_url_rule(
    '/<string:community_id>',
    view_func=CommunityDetailsResource.as_view(
        'communities_item',
        serializers=serializers,
        default_media_type='application/json',
    ),
    methods=['GET']
)

@blueprint.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("invenio_communities dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()