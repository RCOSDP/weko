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

"""Extensions for weko-user-profiles."""

from . import config
from .api import current_userprofile


class WekoUserProfiles(object):
    """weko-user-profiles extension."""

    def __init__(self, app=None):
        """Extension initialization.

        :param app: The Flask application. (Default: ``None``)
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization.

        :param app: The Flask application.
        """
        self.init_config(app)
        # Register current_profile
        app.context_processor(lambda: dict(
            current_userprofile=current_userprofile))
        app.extensions['weko-user-profiles'] = self

    def init_config(self, app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        excludes = [
            'USERPROFILES_BASE_TEMPLATE',
            'USERPROFILES_SETTINGS_TEMPLATE',
        ]
        for k in dir(config):
            if k.startswith('USERPROFILES_') and k not in excludes:
                app.config.setdefault(k, getattr(config, k))

        app.config.setdefault('USERPROFILES', True)

        app.config.setdefault(
            'USERPROFILES_BASE_TEMPLATE',
            app.config.get('BASE_TEMPLATE',
                           'weko_user_profiles/base.html'))

        app.config.setdefault(
            'USERPROFILES_SETTINGS_TEMPLATE',
            app.config.get('SETTINGS_TEMPLATE',
                           'weko_user_profiles/settings/base.html'))

        if app.config['USERPROFILES_EXTEND_SECURITY_FORMS']:
            app.config.setdefault(
                'USERPROFILES_REGISTER_USER_BASE_TEMPLATE',
                app.config.get(
                    'SECURITY_REGISTER_USER_TEMPLATE',
                    'invenio_accounts/register_user.html'
                )
            )
            app.config['SECURITY_REGISTER_USER_TEMPLATE'] = \
                'weko_user_profiles/register_user.html'
