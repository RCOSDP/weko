# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2024 CERN.
# Copyright (C)      2021 TU Wien.
# Copyright (C) 2023-2024 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio user management and authentication."""

from warnings import warn

import pkg_resources
from flask import Blueprint, abort, current_app, request_finished, session
from flask_kvsession import KVSessionExtension
from flask_login import LoginManager, user_logged_in, user_logged_out
from flask_menu import current_menu
from flask_principal import AnonymousIdentity
from flask_security import Security, user_confirmed
from invenio_db import db
from invenio_i18n import lazy_gettext as _
from invenio_theme.proxies import current_theme_icons
from passlib.registry import register_crypt_handler
from werkzeug.utils import cached_property

from invenio_accounts.forms import (
    confirm_register_form_factory,
    login_form_factory,
    register_form_factory,
    send_confirmation_form_factory,
)

from . import config
from .datastore import SessionAwareSQLAlchemyUserDatastore
from .domains import on_user_confirmed
from .hash import InvenioAesEncryptedEmail
from .models import Role, User
from .sessions import csrf_token_reset, login_listener, logout_listener
from .utils import obj_or_import_string, set_session_info


class InvenioAccounts(object):
    """Invenio-Accounts extension."""

    def __init__(self, app=None, sessionstore=None):
        """Extension initialization.

        :param app: The Flask application.
        :param sessionstore: store for sessions. Passed to
            ``flask-kvsession``. Defaults to redis.
        """
        self.security = Security()
        self.datastore = None
        if app:
            self.init_app(app, sessionstore=sessionstore)

    @staticmethod
    def monkey_patch_flask_security():
        """Monkey-patch Flask-Security."""

        # Disable remember me cookie generation as it does not work with
        # session activity tracking (remember me token will bypass revoking
        # of a session).
        def patch_do_nothing(*args, **kwargs):
            pass

        LoginManager._set_cookie = patch_do_nothing

    @cached_property
    def jwt_decode_factory(self):
        """Load default JWT veryfication factory."""
        return obj_or_import_string(
            current_app.config.get("ACCOUNTS_JWT_DECODE_FACTORY")
        )

    @cached_property
    def jwt_creation_factory(self):
        """Load default JWT creation factory."""
        return obj_or_import_string(
            current_app.config.get("ACCOUNTS_JWT_CREATION_FACTORY")
        )

    def register_anonymous_identity_loader(self, state):
        """Registers a loader for AnonymousIdentity.

        Additional loader is necessary for applying a need 'any-user' to
        AnonymousUser in the invenio-access module
        """
        # Attention: the order of the loaders is important
        # append is used here instead of decorator to enforce the order
        state.principal.identity_loaders.append(AnonymousIdentity)

    def check_configuration_consistency(self, app):
        """Check if the config is consistent and issue a warning if not."""
        # Warn if inconsistent configuration is detected
        sec = app.extensions["security"]
        local_login = app.config.get("ACCOUNTS_LOCAL_LOGIN_ENABLED", True)
        local_account_editable = sec.registerable or sec.changeable or sec.recoverable

        if local_account_editable and not local_login:
            warning_message = (
                "ACCOUNTS_LOCAL_LOGIN_ENABLED is False, while at least one "
                "of SECURITY_REGISTERABLE, SECURITY_RECOVERABLE and "
                "SECURITY_CHANGEABLE is True"
            )
            warn(warning_message, Warning, stacklevel=2)

    def init_app(self, app, sessionstore=None, register_blueprint=True):
        """Flask application initialization.

        The following actions are executed:

        #. Initialize the configuration.

        #. Monkey-patch Flask-Security.

        #. Create the user datastore.

        #. Create the sessionstore.

        #. Initialize the extension, the forms to register users and
           confirms their emails, the CLI and, if ``ACCOUNTS_USE_CELERY`` is
           ``True``, register a celery task to send emails.

        #. Override Flask-Security's default login view function.

        #. Warn if inconsistent configuration is detected

        :param app: The Flask application.
        :param sessionstore: store for sessions. Passed to
            ``flask-kvsession``. If ``None`` then Redis is configured.
            (Default: ``None``)
        :param register_blueprint: If ``True``, the application registers the
            blueprints. (Default: ``True``)
        """
        self.init_config(app)

        # Monkey-patch Flask-Security
        InvenioAccounts.monkey_patch_flask_security()

        # Create user datastore
        if not self.datastore:
            self.datastore = SessionAwareSQLAlchemyUserDatastore(db, User, Role)

        if app.config["ACCOUNTS_SESSION_ACTIVITY_ENABLED"]:
            self._enable_session_activity(app=app)

        # Initialize extension.
        _register_blueprint = app.config.get("ACCOUNTS_REGISTER_BLUEPRINT")
        if _register_blueprint is not None:
            register_blueprint = _register_blueprint

        state = self.security.init_app(
            app, datastore=self.datastore, register_blueprint=register_blueprint
        )

        # Override Flask-Security's default login view function
        new_login_view = obj_or_import_string(
            app.config.get("ACCOUNTS_LOGIN_VIEW_FUNCTION")
        )
        if new_login_view is not None:
            app.view_functions["security.login"] = new_login_view

        self.register_anonymous_identity_loader(state)

        app.extensions["security"].register_form = register_form_factory(
            app.extensions["security"].register_form, app
        )

        app.extensions["security"].confirm_register_form = (
            confirm_register_form_factory(
                app.extensions["security"].confirm_register_form, app
            )
        )

        app.extensions["security"].login_form = login_form_factory(
            app.extensions["security"].login_form, app
        )

        # send confirmation form
        app.extensions["security"].send_confirmation_form = (
            send_confirmation_form_factory(
                app.extensions["security"].send_confirmation_form, app
            )
        )

        if app.config["ACCOUNTS_USE_CELERY"]:
            from invenio_accounts.tasks import send_security_email

            @state.send_mail_task
            def delay_security_email(msg):
                send_security_email.delay(msg.__dict__)

        # Register context processor
        if app.config["ACCOUNTS_JWT_DOM_TOKEN"]:
            from invenio_accounts.context_processors.jwt import jwt_proccessor

            app.context_processor(jwt_proccessor)

        # Register signal receiver
        if app.config.get("ACCOUNTS_USERINFO_HEADERS"):
            request_finished.connect(set_session_info, app)

        user_confirmed.connect(on_user_confirmed, app)

        # Set Session KV store
        session_kvstore_factory = obj_or_import_string(
            app.config["ACCOUNTS_SESSION_STORE_FACTORY"]
        )
        session_kvstore = session_kvstore_factory(app)

        self.kvsession_extension = KVSessionExtension(session_kvstore, app)

        self.check_configuration_consistency(app)

        app.extensions["invenio-accounts"] = self

    def init_config(self, app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        try:
            pkg_resources.get_distribution("celery")
            app.config.setdefault("ACCOUNTS_USE_CELERY", not (app.debug or app.testing))
        except pkg_resources.DistributionNotFound:  # pragma: no cover
            app.config.setdefault("ACCOUNTS_USE_CELERY", False)

        # Register Invenio legacy password hashing
        register_crypt_handler(InvenioAesEncryptedEmail)

        # Change Flask defaults
        app.config.setdefault("SESSION_COOKIE_SECURE", not app.debug)

        # Change Flask-Security defaults
        app.config.setdefault("SECURITY_PASSWORD_SALT", app.config["SECRET_KEY"])

        # Set JWT secret key
        app.config.setdefault(
            "ACCOUNTS_JWT_SECRET_KEY",
            app.config.get("ACCOUNTS_JWT_SECRET_KEY", app.config.get("SECRET_KEY")),
        )

        config_apps = ["ACCOUNTS", "SECURITY_"]
        for k in dir(config):
            if any([k.startswith(prefix) for prefix in config_apps]):
                app.config.setdefault(k, getattr(config, k))

    def _enable_session_activity(self, app):
        """Enable session activity."""
        user_logged_in.connect(login_listener, app)
        user_logged_in.connect(csrf_token_reset, app)
        user_logged_out.connect(logout_listener, app)
        user_logged_out.connect(csrf_token_reset, app)


class InvenioAccountsREST(InvenioAccounts):
    """Invenio-Accounts REST extension."""

    def init_app(self, app, sessionstore=None, register_blueprint=False):
        """Flask application initialization.

        :param app: The Flask application.
        :param sessionstore: store for sessions. Passed to
            ``flask-kvsession``. If ``None`` then Redis is configured.
            (Default: ``None``)
        :param register_blueprint: If ``True``, the application registers the
            blueprints. (Default: ``True``)
        """
        # Register the Flask-Security blueprint for the email templates
        if not register_blueprint:
            security_bp = Blueprint(
                "security_email_templates",  # name differently to avoid misuse
                "flask_security.core",
                template_folder="templates",
            )
            security_rest_overrides = Blueprint(
                "security_email_overrides",  # overrides
                __name__,
                template_folder="templates",
            )
            app.register_blueprint(security_bp)
            app.register_blueprint(security_rest_overrides)

        super(InvenioAccountsREST, self).init_app(
            app,
            sessionstore=sessionstore,
            register_blueprint=register_blueprint,
        )
        app.config["ACCOUNTS_CONFIRM_EMAIL_ENDPOINT"] = app.config[
            "ACCOUNTS_REST_CONFIRM_EMAIL_ENDPOINT"
        ]
        app.config["ACCOUNTS_RESET_PASSWORD_ENDPOINT"] = app.config[
            "ACCOUNTS_REST_RESET_PASSWORD_ENDPOINT"
        ]

        if app.config.get("ACCOUNTS_REGISTER_UNAUTHORIZED_CALLBACK", True):

            def _unauthorized_callback():
                """Callback to abort when user is unauthorized."""
                abort(401)

            app.login_manager.unauthorized_handler(_unauthorized_callback)


class InvenioAccountsUI(InvenioAccounts):
    """Invenio-Accounts UI extension."""

    def init_app(self, app, sessionstore=None, register_blueprint=True):
        """Flask application initialization.

        :param app: The Flask application.
        :param sessionstore: store for sessions. Passed to
            ``flask-kvsession``. If ``None`` then Redis is configured.
            (Default: ``None``)
        :param register_blueprint: If ``True``, the application registers the
            blueprints. (Default: ``True``)
        """
        self.make_session_permanent(app)
        return super(InvenioAccountsUI, self).init_app(
            app, sessionstore=sessionstore, register_blueprint=register_blueprint
        )

    def make_session_permanent(self, app):
        """Make session permanent by default.

        Set `PERMANENT_SESSION_LIFETIME` to specify time-to-live
        """

        @app.before_request
        def make_session_permanent():
            session.permanent = True


def finalize_app(app):
    """Finalize app."""
    set_default_config(app)
    check_security_settings(app)
    init_menu(app)


def set_default_config(app):
    """Set default values."""
    app.config.setdefault(
        "ACCOUNTS_SITENAME", app.config.get("THEME_SITENAME", "Invenio")
    )
    app.config.setdefault(
        "ACCOUNTS_BASE_TEMPLATE",
        app.config.get("BASE_TEMPLATE", "invenio_accounts/base.html"),
    )
    app.config.setdefault(
        "ACCOUNTS_COVER_TEMPLATE",
        app.config.get("COVER_TEMPLATE", "invenio_accounts/base_cover.html"),
    )
    app.config.setdefault(
        "ACCOUNTS_SETTINGS_TEMPLATE",
        app.config.get("SETTINGS_TEMPLATE", "invenio_accounts/settings/base.html"),
    )


def check_security_settings(app):
    """Warn if session cookie is not secure in production."""
    in_production = not (app.debug or app.testing)
    secure = app.config.get("SESSION_COOKIE_SECURE")
    if in_production and not secure:
        app.logger.warning(
            "SESSION_COOKIE_SECURE setting must be set to True to prevent the "
            "session cookie from being leaked over an insecure channel."
        )


def init_menu(app):
    """Init menu."""
    current_menu.submenu("settings.security").register(
        endpoint="invenio_accounts.security",
        text=_(
            "%(icon)s Security", icon=f'<i class="{current_theme_icons.shield}"></i>'
        ),
        order=2,
    )

    # - Register menu
    # - Change password
    if app.config.get("SECURITY_CHANGEABLE", True):
        current_menu.submenu("settings.change_password").register(
            endpoint=f"{app.config['SECURITY_BLUEPRINT_NAME']}.change_password",
            text=_(
                "%(icon)s Change password",
                icon=f'<i class="{current_theme_icons.key}"></i>',
            ),
            order=1,
        )
