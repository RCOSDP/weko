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

"""Blueprint for Weko accounts rest."""

import inspect

from flask import Blueprint, current_app, jsonify, request, make_response
from flask_login import login_user, logout_user
from flask_security import current_user
from flask_security.utils import verify_password

from invenio_accounts.models import User
from invenio_db import db
from invenio_rest import ContentNegotiatedMethodView
from weko_logging.activity_logger import UserActivityLogger

from .errors import VersionNotFoundRESTError, UserAllreadyLoggedInError, UserNotFoundError, InvalidPasswordError, DisabledUserError
from .utils import limiter


def create_blueprint(app, endpoints):
    """
    Create Weko-Accounts-REST blueprint.

    See: :data:`weko_accounts.config.WEKO_ACCOUNTS_REST_ENDPOINTS`.

    :param endpoints: List of endpoints configuration.
    :returns: The configured blueprint.
    """
    blueprint = Blueprint(
        'weko_accounts_rest',
        __name__,
        url_prefix="",
    )

    @blueprint.teardown_request
    def dbsession_clean(exception):
        current_app.logger.debug('weko_accounts dbsession_clean: {}'.format(exception))
        if exception is None:
            try:
                db.session.commit()
            except:
                db.session.rollback()
        db.session.remove()

    for endpoint, options in (endpoints or {}).items():
        if endpoint == 'login':
            view_func = WekoLogin.as_view(
                WekoLogin.view_name.format(endpoint),
                default_media_type=options.get('default_media_type')
            )
            blueprint.add_url_rule(
                options.get('route'),
                view_func=view_func,
                methods=['POST']
            )
        elif endpoint == 'logout':
            view_func = WekoLogout.as_view(
                WekoLogout.view_name.format(endpoint),
                default_media_type=options.get('default_media_type')
            )
            blueprint.add_url_rule(
                options.get('route'),
                view_func=view_func,
                methods=['POST']
            )

    return blueprint


class WekoLogin(ContentNegotiatedMethodView):
    """Resource to login as weko user."""

    view_name = '{0}_accounts'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(WekoLogin, self).__init__(*args, **kwargs)

    @limiter.limit('')
    def post(self, **kwargs):
        """
        Login as weko user.

        Returns:
            Login result.
        """

        version = kwargs.get('version')
        func_name = f'post_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    def post_v1(self, **kwargs):

        data = request.get_json()
        email = data['email']
        password = data['password']

        # Check if user is already logged in
        if current_user.is_authenticated:
            raise UserAllreadyLoggedInError()

        # Get User
        user = User.query.filter_by(email=email).first()
        if not user:
            raise UserNotFoundError()
        # Verify password
        if not verify_password(password, user.password):
            raise InvalidPasswordError()

        # Check if user is active
        if not user.active:
            raise DisabledUserError()

        # Log in
        login_user(user)

        # Create response
        res_json = {
            'id': user.id,
            'email': user.email,
        }
        UserActivityLogger.info(
            operation="LOGIN",
            target_key=user.id
        )
        return make_response(jsonify(res_json), 200)


class WekoLogout(ContentNegotiatedMethodView):
    """Resource to logout."""

    view_name = '{0}_accounts'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(WekoLogout, self).__init__(*args, **kwargs)

    @limiter.limit('')
    def post(self, **kwargs):
        """
        Logout of weko.

        Returns:
            Logout result.
        """

        version = kwargs.get('version')
        func_name = f'post_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    def post_v1(self, **kwargs):

        # Logout
        if current_user.is_authenticated:
            user_id = current_user.id
            logout_user()

            UserActivityLogger.info(
                operation="LOGOUT",
                target_key=user_id
            )
        return make_response('', 200)
