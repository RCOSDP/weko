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

"""Extensions for weko-admin."""

from datetime import timedelta

from flask import session, current_app, request
from flask_babelex import gettext as _
from flask_login import current_user

from . import config
from .models import SessionLifetime
from .views import blueprint

from invenio_db import db
from invenio_accounts.models import Role, userrole
from flask_admin import Admin

from functools import partial

class WekoAdmin(object):
    """WEKO-Admin extension."""

    @staticmethod
    def role_has_access(endpoint=None):
        """Check if user's role has access to view endpoint."""
        endpoint = endpoint or request.url_rule.endpoint.split('.')[0]
        def _role_endpoint_viewable(endpoint):
            """Check whether the current user role can view the endpoint - util."""
            conf = current_app.config
            access_table = conf['WEKO_ADMIN_ACCESS_TABLE']
            system_admin = conf['WEKO_ADMIN_PERMISSION_ROLE_SYSTEM']
            try:
                roles = db.session.query(Role).join(userrole).filter_by(
                    user_id=current_user.get_id()).all()
            except Exception as e:
                current_app.logger.error(
                    'Could not determine roles - returning False: ', e)
                roles = []
            for role in roles:  # Check if role can view endpoint
                access_list = access_table[role.name] if role.name in access_table \
                    else []
                if endpoint in access_list or role.name == system_admin:
                    return True
            return False
        return _role_endpoint_viewable(endpoint)

    def __init__(self, app=None):
        """
        Extension initialization.

        :param app: The flask application, default None.
        """
        _('A translation string')
        if app:
            self.app = app
            self.init_app(app)

    def init_app(self, app):
        """
        Flask application initialization.

        :param app: The flask application.
        """
        self.make_session_permanent(app)
        self.init_config(app)
        app.register_blueprint(blueprint)
        app.extensions['weko-admin'] = self

        @app.before_request  # Add extra access control for roles
        def is_accessible_to_role():
            """Check if current user's role has access to view."""
            for view in app.extensions['admin'][0]._views:
                setattr(view, 'is_accessible', self.role_has_access)
                new_views = []
                is_visible_fn = partial(self.role_has_access, view.endpoint)
                setattr(view, 'is_visible', is_visible_fn)
                new_views.append(view)
            app.extensions['admin'][0]._views = new_views  # Overwrite views

    def init_config(self, app):
        """
        Initialize configuration.

        :param app: The flask application.
        """
        excludes = [
            'WEKO_ADMIN_DEFAULT_LIFETIME',
            'WEKO_ADMIN_SETTINGS_TEMPLATE'
        ]
        # Use theme's base template if theme is installed
        if 'BASE_EDIT_TEMPLATE' in app.config:
            app.config.setdefault(
                'WEKO_ADMIN_BASE_TEMPLATE',
                app.config['BASE_EDIT_TEMPLATE'],
            )
        for k in dir(config):
            if k.startswith('WEKO_ADMIN_') and k not in excludes:
                app.config.setdefault(k, getattr(config, k))
            elif k.startswith('BABEL_'):
                app.config.setdefault(k, getattr(config, k))

        app.config.setdefault(
            'WEKO_ADMIN_SETTINGS_TEMPLATE',
            app.config.get('SETTINGS_TEMPLATE',
                           'weko_admin/settings/base.html'))

    def make_session_permanent(self, app):
        """Make session permanent by default.

        Set `PERMANENT_SESSION_LIFETIME` to specify time-to-live

        :param app: The flask application.
        """
        @app.before_first_request
        def make_session_permanent():
            session.permanent = True
            db_lifetime = SessionLifetime.get_validtime()
            if db_lifetime is None:
                if isinstance(config.WEKO_ADMIN_DEFAULT_LIFETIME, int):
                    db_lifetime = SessionLifetime(
                        lifetime=int(getattr(config,
                                             'WEKO_ADMIN_DEFAULT_LIFETIME')))
                else:
                    db_lifetime = SessionLifetime(lifetime=30)
                db_lifetime.create()
            app.permanent_session_lifetime = timedelta(
                minutes=db_lifetime.lifetime)
