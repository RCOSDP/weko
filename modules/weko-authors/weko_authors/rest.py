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

"""Blueprint for schema rest."""

import inspect
import json
import traceback

from flask import Blueprint, current_app, request, Response
from invenio_db import db
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.errors import SameContentException
from werkzeug.exceptions import BadRequest, InternalServerError
from werkzeug.http import generate_etag

from .errors import VersionNotFoundRESTError, AuthorNotFoundRESTError
from .scopes import authors_read_scope


def create_blueprint(endpoints):
    """Create Weko-Authors-REST blueprint.

    See: :data:`weko_authors.config.WEKO_AUTHORS_REST_ENDPOINTS`.

    :param endpoints: List of endpoints configuration.
    :returns: The configured blueprint.
    """
    blueprint = Blueprint(
        'weko_authors_rest',
        __name__,
        url_prefix='',
    )

    @blueprint.teardown_request
    def dbsession_clean(exception):
        current_app.logger.debug('weko_authors dbsession_clean: {}'.format(exception))
        if exception is None:
            try:
                db.session.commit()
            except:
                db.session.rollback()
        db.session.remove()

    for endpoint, options in (endpoints or {}).items():
        if endpoint == 'authors':
            authors = Authors.as_view(
                Authors.view_name.format(endpoint),
                default_media_type=options.get('default_media_type')
            )
            blueprint.add_url_rule(
                options.get('route'),
                view_func=authors,
                methods=['GET']
            )

    return blueprint


class Authors(ContentNegotiatedMethodView):
    """Authors Resource."""
    print("====================================Authors====================================")
    view_name = '{0}'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        print("====================================init====================================")
        super(Authors, self).__init__(
            *args,
            **kwargs
        )

    @require_api_auth()
    @require_oauth_scopes(authors_read_scope.id)
    def get(self, **kwargs):
        """Get authors."""
        version = kwargs.get('version')
        func_name = f'get_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            print("====================================iiiiiii====================================")
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    def get_v1(self, **kwargs):

        # Check request parameter.
        try:
            print("====================================aaaaaa====================================")
            search_key = request.values.get('search_key', '')
            limit = int(request.values.get('limit') or current_app.config.get('WEKO_AUTHORS_NUM_OF_PAGE'))
            page = request.values.get('page')
            if page:
                page = int(page)
            cursor = request.values.get('cursor', '')

            sort = request.values.get('sort_key')
            sort_key = ''
            sort_order = ''
            if sort:
                if sort.startswith('-'):
                    sort = sort[1:]
                    sort_order = 'desc'
                else:
                    sort_order = 'asc'

                if sort not in current_app.config.get('WEKO_AUTHORS_REST_SORT_KEY'):
                    raise BadRequest('Invalid sort key.')
                sort_key = current_app.config.get('WEKO_AUTHORS_REST_SORT_KEY').get(sort)

        except Exception:
            print("====================================error====================================")
            current_app.logger.error(traceback.print_exc())
            raise BadRequest()

        # Execute search.
        try:
            from .utils import count_authors
            search_result = count_authors()
            print("====================================count====================================")
            print(search_result)
            print("====================================count====================================")

            total_results = search_result['hits']['total']
            count_results = len(search_result['hits']['hits'])
            cursor = ''
            if count_results:
                cursor = search_result['hits']['hits'][-1]['sort']
                if cursor:
                    cursor = cursor[0]

            authors = []
            for hit in search_result['hits']['hits']:
                authors.append(hit['_source'])

            res_json = {
                'total_results': total_results,
                'count_results': count_results,
                'cursor': cursor,
                'authors': authors,
            }

            # Check pretty
            indent = 4 if request.args.get('pretty') == 'true' else None

            # Create Response
            res = Response(
                response=json.dumps(res_json, indent=indent),
                status=200,
                content_type='application/json'
            )

            # Response header setting
            res.headers['Cache-Control'] = 'no-store'
            res.headers['Pragma'] = 'no-cache'
            res.headers['Expires'] = 0

            return res

        except Exception:
            current_app.logger.error(traceback.print_exc())
            raise InternalServerError()

