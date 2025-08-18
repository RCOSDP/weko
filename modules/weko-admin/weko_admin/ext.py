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
from functools import partial

from babel.core import Locale
from flask import _request_ctx_stack, current_app, request, session
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_accounts.models import Role, userrole
from invenio_db import db
from invenio_i18n.ext import current_i18n
from invenio_i18n.views import set_lang

from . import config
from .models import AdminLangSettings, AdminSettings, SessionLifetime, SiteInfo
from .utils import overwrite_the_memory_config_with_db
from .views import blueprint


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
            is_use_mail_templates = False
            restricted_access_settings = AdminSettings.get("restricted_access", dict_to_object=False)
            if restricted_access_settings:
                is_use_mail_templates = restricted_access_settings.get("edit_mail_templates_enable", False)
            is_display_restricted_settings = conf.get('WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS', False)
            try:
                roles = db.session.query(Role).join(userrole).filter_by(
                    user_id=current_user.get_id()).all()
            except Exception as e:
                current_app.logger.error(
                    'Could not determine roles - returning False: {}'.format(e))
                roles = []
            for role in roles:  # Check if role can view endpoint
                if endpoint == 'mailtemplates' and not is_use_mail_templates:
                    return False
                elif endpoint == 'restricted_access' and not is_display_restricted_settings \
                    and role.name != system_admin:
                        return False
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
            # avoid ping request
            if request.path == "/ping":
                return
            for view in app.extensions['admin'][0]._views:
                setattr(view, 'is_accessible', self.role_has_access)
                new_views = []
                is_visible_fn = partial(self.role_has_access, view.endpoint)
                setattr(view, 'is_visible', is_visible_fn)
                new_views.append(view)
            app.extensions['admin'][0]._views = new_views  # Overwrite views

        @app.before_request
        def set_default_language():
            """Set default language from admin language settings.

            In case user opens the web for the first time,
            set default language base on Admin language setting
            """
            # avoid ping request
            if request.path == "/ping":
                return
            if request.path == "/oai":
                return
            
            if "selected_language" not in session:
                registered_languages = AdminLangSettings\
                    .get_registered_language()
                if registered_languages:
                    default_language = registered_languages[0].get('lang_code')
                    session['selected_language'] = default_language
                    set_lang(default_language)
                    ctx = _request_ctx_stack.top
                    if ctx is not None and hasattr(ctx, 'babel_locale'):
                        setattr(ctx, 'babel_locale', Locale(default_language))
            else:
                session['selected_language'] = current_i18n.language

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
        # Overwrite the memory Config values
        # (GOOGLE_TRACKING_ID_USER and ADDTHIS_USER_ID) with the DB values.
        self.overwrite_the_memory_config(app)

        for k in dir(config):
            if k.startswith('WEKO_ADMIN_') and k not in excludes:
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
            # avoid session control
            if request.path == "/ping":
                return
            session.permanent = True
            db_lifetime = SessionLifetime.get_validtime()
            if db_lifetime is None:
                db_lifetime = SessionLifetime(
                    lifetime=int(getattr(config,
                                         'WEKO_ADMIN_DEFAULT_LIFETIME')))
                db_lifetime.create()
            app.permanent_session_lifetime = timedelta(
                minutes=db_lifetime.lifetime)

    def overwrite_the_memory_config(self, app):
        """Init Overwrite the memory Config values with the DB values."""
        @app.before_first_request
        def overwrite_the_memory_config():
            site_info = SiteInfo.get()
            overwrite_the_memory_config_with_db(app, site_info)
