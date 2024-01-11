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

import json
import traceback

from flask import Blueprint, current_app, Response
from invenio_db import db
from invenio_rest import ContentNegotiatedMethodView
from werkzeug.exceptions import InternalServerError

from .errors import VersionNotFoundRESTError


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
    view_name = '{0}'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(Authors, self).__init__(
            *args,
            **kwargs
        )

    def get(self, **kwargs):
        """Count authors."""
        version = kwargs.get('version')
        func_name = f'get_{version}'
        from .config import WEKO_AUTHORS_COUNT_API_VERSION
        func = WEKO_AUTHORS_COUNT_API_VERSION.get(f'get-{version}')

        if func:
            return func(self, **kwargs)
        else:
            raise VersionNotFoundRESTError()

    def get_v1(self, **kwargs):

        # Execute count.
        try:
            from .utils import count_authors
            count_result = count_authors()

            # Create Response
            res = Response(
                response=json.dumps(count_result),
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

