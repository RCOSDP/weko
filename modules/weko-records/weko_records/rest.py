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

from flask import Blueprint, current_app, jsonify, make_response, request
from flask_babelex import gettext as _
from invenio_db import db

from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_oauth2server.provider import oauth2
from invenio_pidstore.errors import PIDInvalidAction
from invenio_records_rest.views import create_error_handlers as records_rest_error_handlers
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.views import create_api_errorhandler
from sqlalchemy.exc import SQLAlchemyError

from .errors import InvalidRequestError, InternalServerError, VersionNotFoundRESTError
from .models import OaStatus
from .scopes import oa_status_update_scope
from .utils import create_limiter

limiter = create_limiter()


def create_error_handlers(blueprint):
    """Create error handlers on blueprint."""
    blueprint.errorhandler(PIDInvalidAction)(create_api_errorhandler(
        status=403, message='Invalid action'
    ))
    records_rest_error_handlers(blueprint)

def create_blueprint(endpoints):
    """
    Create Weko-Records-ui-REST blueprint.
    See: :data:`weko_records.config.WEKO_RECORDS_REST_ENDPOINTS`.

    :param endpoints: List of endpoints configuration.
    :returns: The configured blueprint.
    """
    blueprint = Blueprint(
        'weko_records_rest',
        __name__,
        url_prefix='',
    )

    @blueprint.teardown_request
    def dbsession_clean(exception):
        current_app.logger.debug("weko_records dbsession_clean: {}".format(exception))
        if exception is None:
            try:
                db.session.commit()
            except:
                db.session.rollback()
        db.session.remove()

    for endpoint, options in (endpoints or {}).items():
        if endpoint == 'oa_status_callback':
            view_func = OaStatusCallback.as_view(
                OaStatusCallback.view_name.format(endpoint),
                default_media_type=options.get('default_media_type'),
            )
            blueprint.add_url_rule(
                options.get('route'),
                view_func=view_func,
                methods=['POST'],
            )

    return blueprint

class OaStatusCallback(ContentNegotiatedMethodView):
    view_name = 'records_{0}'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(OaStatusCallback, self).__init__(*args, **kwargs)

    @limiter.limit('')
    @oauth2.require_oauth()
    @require_oauth_scopes(oa_status_update_scope.id)
    def post(self, **kwargs):
        """
        Post OA status.

        Returns:
            Result json.
        """
        version = kwargs.get('version')
        func_name = f'post_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError() # 400 Error

    def post_v1(self, **kwargs):
        # Get request mail senders
        request_body = request.get_json(force=True, silent=True)
        if not request_body or not isinstance(request_body, dict) or not request_body.get('articles'):
            raise InvalidRequestError()
        
        try:
            articles = request_body.get('articles', [])
            for article in articles:
                id = article.get('id', None)
                if not id:
                    current_app.logger.debug(f"Not upsert oa_status because no id: {article}")
                    continue
                status = article.get('wos_record_status', None)
                weko_item_pid = None
                weko_url = article.get('weko_url', None)
                if weko_url:
                    weko_item_pid = weko_url.rstrip('/').split('/')[-1]
                
                oa_status = OaStatus.get_oa_status(oa_article_id=id)
                if oa_status:
                    # Update
                    oa_status.oa_status = status
                    oa_status.weko_item_pid = weko_item_pid
                    oa_status.updated_at = db.func.now()
                    current_app.logger.debug(f"Updated oa_status: {article}")
                else:
                    # Create
                    oa_status = OaStatus(oa_article_id=id, oa_status=status, weko_item_pid=weko_item_pid)
                    db.session.add(oa_status)
                    current_app.logger.debug(f"Inserted oa_status: {article}")
                db.session.commit()
        except SQLAlchemyError as ex:
            current_app.logger.error(f"OA Status update failed: {ex}")
            db.session.rollback()
            raise InternalServerError()
        except Exception as ex:
            current_app.logger.error(f"OA Status update failed: {ex}")
            db.session.rollback()
            raise InternalServerError()

        res_json = {
            "status": 200,
            "message": "OA Status updated successfully."
        }
        response = make_response(jsonify(res_json), 200)

        return response

