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

"""Extensions for weko-accounts."""

from flask_babelex import gettext as _
from flask_login import user_logged_in, user_logged_out

from . import config
from .sessions import login_listener, logout_listener
from .views import blueprint


class WekoAccounts(object):
    """WEKO-Accounts extension."""

    def __init__(self, app=None):
        """
        Extension initialization.

        :param app: The flask application, default None.
        """
        # NOTE: This is a note to a translator.
        _('A translation string')
        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Flask application initialization.

        :param app: The flask application.
        """
        self.init_config(app)

        if app.config['WEKO_ACCOUNTS_LOGGER_ENABLED']:
            self._enable_logger_activity(app=app)

        app.register_blueprint(blueprint)
        app.extensions['weko-accounts'] = self

    def init_config(self, app):
        """
        Initialize configuration.

        :param app: The flask application.
        """
        # Use theme's base template if theme is installed
        if 'BASE_TEMPLATE' in app.config:
            app.config.setdefault(
                'WEKO_ACCOUNTS_BASE_TEMPLATE',
                app.config['BASE_TEMPLATE'],
            )

        for k in dir(config):
            if k.startswith('WEKO_ACCOUNTS_') or k.startswith('BABEL_'):
                app.config.setdefault(k, getattr(config, k))

        # Handle redirect to the screen of corresponding pattern
        app.config['SECURITY_LOGIN_USER_TEMPLATE'] = \
            app.config['WEKO_ACCOUNTS_SECURITY_LOGIN_USER_TEMPLATE']

        # Handle redirect to the screen of corresponding pattern
        app.config['SECURITY_REGISTER_USER_TEMPLATE'] = \
            app.config['WEKO_ACCOUNTS_SECURITY_REGISTER_USER_TEMPLATE']

        # Shibboleth
        if app.config['WEKO_ACCOUNTS_SHIB_LOGIN_ENABLED']:
            # Shibboleth IdP
            if app.config['WEKO_ACCOUNTS_SHIB_IDP_LOGIN_ENABLED']:
                if app.config[
                        'WEKO_ACCOUNTS_SHIB_INST_LOGIN_DIRECTLY_ENABLED']:
                    # TODO: Implement login method for redirect URL
                    pass
            # Shibboleth DS
            else:
                if app.config[
                        'WEKO_ACCOUNTS_SHIB_DP_LOGIN_DIRECTLY_ENABLED']:
                    app.config['SECURITY_LOGIN_USER_TEMPLATE'] = \
                        app.config[
                            'WEKO_ACCOUNTS_SECURITY_LOGIN_SHIB_USER_TEMPLATE']

    def _enable_logger_activity(self, app):
        """
        Enable session activity.

        :param app: The flask application.
        """
        user_logged_in.connect(login_listener, app)
        user_logged_out.connect(logout_listener, app)
