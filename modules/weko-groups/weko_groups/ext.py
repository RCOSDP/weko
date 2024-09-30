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


"""Extensions for weko-groups."""

from flask import request
from flask_menu import current_menu
from invenio_i18n import LazyString
from invenio_i18n import lazy_gettext as _
from .views import blueprint

class WekoGroups(object):
    """Weko-Groups extension."""

    def __init__(self, app=None):
        """
        Extension initialization.

        :param app: The flask application, default None.
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Flask application initialization.

        :param app: The flask application.
        """
        self.init_config(app)
        app.register_blueprint(blueprint)
        app.extensions['weko-groups'] = self

    def init_config(self, app):
        """
        Initialize configuration.

        :param app: The flask application.
        """
        app.config.setdefault(
            "GROUPS_BASE_TEMPLATE",
            app.config.get("SETTINGS_TEMPLATE",
                           "weko_groups/base.html"))

def finalize_app(app):
    icons = app.extensions['invenio-theme'].icons

    current_menu.submenu('settings.groups').register(
        endpoint='weko_groups.index',
        text=_(
            '%(icon)s Groups',
            icon='<i class="fa fa-users fa-fw"></i>'
        ),
        order=13,
        active_when=lambda: request.endpoint.startswith('weko_groups.')
    )
