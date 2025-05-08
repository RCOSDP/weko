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

"""Flask extension for weko-workflow."""

from weko_deposit.signals import item_created

from . import config
from .rest import create_blueprint
from .sessions import upt_activity_item
from .views import depositactivity_blueprint, workflow_blueprint


class WekoWorkflow(object):
    """weko-workflow extension."""

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
        item_created.connect(upt_activity_item, app)
        app.register_blueprint(workflow_blueprint)
        app.register_blueprint(depositactivity_blueprint)
        app.extensions['weko-workflow'] = self

    def init_config(self, app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        # Use theme's base template if theme is installed
        if 'BASE_EDIT_TEMPLATE' in app.config:
            app.config.setdefault(
                'WEKO_WORKFLOW_BASE_TEMPLATE',
                app.config['BASE_PAGE_TEMPLATE'],
            )
        for k in dir(config):
            if k.startswith('WEKO_WORKFLOW_'):
                app.config.setdefault(k, getattr(config, k))


class WekoWorkflowREST(object):
    """Workflow Rest Obj."""

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
        self.init_config(app)
        blueprint = create_blueprint(app, app.config['WEKO_WORKFLOW_REST_ENDPOINTS'])
        app.register_blueprint(blueprint)
        app.extensions['weko_workflow_rest'] = self

    def init_config(self, app):
        """
        Initialize configuration.

        :param app: An instance of :class:`flask.Flask`.
        """
        for k in dir(config):
            if k.startswith('WEKO_WORKFLOW_'):
                app.config.setdefault(k, getattr(config, k))
            if k == 'WEKO_ITEMS_UI_MULTIPLE_APPROVALS':
                app.config.setdefault(k, getattr(config, k))
