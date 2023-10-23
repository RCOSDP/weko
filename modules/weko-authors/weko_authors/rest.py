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

from flask import Blueprint, current_app, request, Response, Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from invenio_db import db
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.errors import SameContentException
from werkzeug.exceptions import BadRequest, InternalServerError
from werkzeug.http import generate_etag

from .config import WEKO_AUTHORS_REST_LIMIT_RATE_DEFAULT
from .errors import VersionNotFoundRESTError, AuthorNotFoundRESTError
from .scopes import authors_read_scope


limiter = Limiter(app=Flask(__name__), key_func=get_remote_address, default_limits=WEKO_AUTHORS_REST_LIMIT_RATE_DEFAULT)


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
            authors = AuthorsREST.as_view(
                AuthorsREST.view_name.format(endpoint),
                default_media_type=options.get('default_media_type')
            )
            blueprint.add_url_rule(
                options.get('route'),
                view_func=authors,
                methods=['GET']
            )
        elif endpoint == 'author':
            author = AuthorREST.as_view(
                AuthorREST.view_name.format(endpoint),
                default_media_type=options.get('default_media_type')
            )
            blueprint.add_url_rule(
                options.get('route'),
                view_func=author,
                methods=['GET']
            )

    return blueprint


class AuthorsREST(ContentNegotiatedMethodView):
    """Authors Resource."""
    view_name = '{0}'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(AuthorsREST, self).__init__(
            *args,
            **kwargs
        )

    @require_api_auth()
    @require_oauth_scopes(authors_read_scope.id)
    @limiter.limit('')
    def get(self, **kwargs):
        """Get authors."""
        version = kwargs.get('version')
        func_name = f'get_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    def get_v1(self, **kwargs):

        # Check request parameter.
        try:
            search_key = request.values.get('search_key', '')
            limit = int(request.values.get('limit') or current_app.config.get('WEKO_AUTHORS_NUM_OF_PAGE'))
            page = int(request.values.get('page')) if 'page' in request.values else ''
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
            current_app.logger.error(traceback.print_exc())
            raise BadRequest()

        # Execute search.
        try:
            from .utils import get_authors
            search_result = get_authors(search_key, limit, page, cursor, sort_key, sort_order)

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


class AuthorREST(ContentNegotiatedMethodView):
    """Author Resource."""
    view_name = '{0}'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(AuthorREST, self).__init__(
            *args,
            **kwargs
        )

    @require_api_auth()
    @require_oauth_scopes(authors_read_scope.id)
    @limiter.limit('')
    def get(self, **kwargs):
        """Get author by id."""
        version = kwargs.get('version')
        func_name = f'get_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    def get_v1(self, **kwargs):
        try:
            author_id = kwargs.get('id')
            from weko_authors.models import Authors
            author_record = Authors.query.filter_by(id=author_id).one_or_none()
            if not author_record:
                raise AuthorNotFoundRESTError

            # Check Etag
            hash_str = str(author_id) + author_record.updated.strftime("%a, %d %b %Y %H:%M:%S GMT")
            etag = generate_etag(hash_str.encode('utf-8'))
            self.check_etag(etag, weak=True)

            # Check Last-Modified
            last_modified = author_record.updated
            if not request.if_none_match:
                self.check_if_modified_since(dt=last_modified)

            # Execute search
            from .utils import get_author_by_pk_id
            search_result = get_author_by_pk_id(author_id)
            author = search_result['hits']['hits'][0]['_source']

            # Check pretty
            indent = 4 if request.args.get('pretty') == 'true' else None

            # Create Response
            res = Response(
                response=json.dumps(author, indent=indent),
                status=200,
                content_type='application/json')
            res.set_etag(etag)
            res.last_modified = last_modified
            return res

        except (SameContentException, AuthorNotFoundRESTError) as e:
            raise e

        except Exception:
            current_app.logger.error(traceback.print_exc())
            raise InternalServerError()
