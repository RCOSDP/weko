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

from flask import session
from flask_babelex import gettext as _

from . import config
from .models import SessionLifetime
from .views import blueprint


class WekoAdmin(object):
    """WEKO-Admin extension."""

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
