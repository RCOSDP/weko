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

from flask import jsonify
from flask_babelex import gettext as _
from flask_login import user_logged_in, user_logged_out

from . import config
from .utils import get_sp_info


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

        from .views import blueprint
        app.register_blueprint(blueprint)
        app.extensions['weko-accounts'] = self

        self.init_limiter(app)

        self.init_login(app)

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
            app.config['SECURITY_LOGIN_USER_TEMPLATE'] = \
                        app.config[
                            'WEKO_ACCOUNTS_SECURITY_LOGIN_LOCAL_SHIB_TEMPLATE']
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
        from .sessions import login_listener, logout_listener
        user_logged_in.connect(login_listener, app)
        user_logged_out.connect(logout_listener, app)

    def init_limiter(self, app):
        """
        Initialize rate limiting.

        :param app: The flask application.
        """
        from .utils import limiter
        limiter.init_app(app)
    
    def init_login(self, app):
        """Initialize login context processor.

        Args:
            app (flask.Flask): The flask application.
        """
        security = app.extensions['security']
        security.login_context_processor(get_sp_info)


class WekoAccountsREST(object):
    """Weko accounts Rest Obj."""

    def __init__(self, app=None):
        """
        Extension initialization.
        :param app: An instance of :class:`flask.Flask`.
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Flask application initialization.
        Initialize the REST endpoints.
        Connect all signals if `DEPOSIT_REGISTER_SIGNALS` is True.
        :param app: An instance of :class:`flask.Flask`.
        """
        from .rest import create_blueprint
        self.init_config(app)
        blueprint = create_blueprint(app, app.config['WEKO_ACCOUNTS_REST_ENDPOINTS'])
        app.register_blueprint(blueprint)
        app.extensions['weko_accounts_rest'] = self
        self.init_unauthorized_handler(app)

    def init_unauthorized_handler(self, app):
        """Return 401 JSON instead of redirecting to the login screen.

        The API app has no ``security`` blueprint, so flask_login's default
        ``unauthorized()`` cannot build ``url_for('security.login')`` and
        raises BuildError, which surfaces as a 500. That makes it impossible
        to tell "blocked by authentication" from "crashed", and it is what
        prevents ``login_required`` from being applied under ``/api/``.

        Registering an ``unauthorized_callback`` short-circuits before the
        ``url_for`` call, so the BuildError can no longer happen.

        Only the API app is affected: this extension is registered under
        ``invenio_base.api_apps`` only, so the UI app keeps redirecting (302).

        :param app: An instance of :class:`flask.Flask`.
        """
        if not app.config.get('WEKO_ACCOUNTS_REST_UNAUTHORIZED_JSON', True):
            return

        def _unauthorized():
            return jsonify(
                status=401,
                message='Authentication required.',
            ), 401

        def _install():
            login_manager = getattr(app, 'login_manager', None)
            # Defer to another extension that already installed a handler.
            if login_manager is not None \
                    and login_manager.unauthorized_callback is None:
                login_manager.unauthorized_handler(_unauthorized)

        _install()
        if getattr(app, 'login_manager', None) is None:
            # Entry point load order under invenio_base.api_apps is not
            # guaranteed, so retry once the app is fully initialized.
            app.before_first_request(_install)

    def init_config(self, app):
        """
        Initialize configuration.
        :param app: An instance of :class:`flask.Flask`.
        """
        for k in dir(config):
            if k.startswith('WEKO_ACCOUNTS_'):
                app.config.setdefault(k, getattr(config, k))
