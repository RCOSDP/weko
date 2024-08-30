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

"""Flask extension for weko-deposit."""

from invenio_indexer.signals import before_record_index

from . import config
from .receivers import append_file_content
from .rest import create_blueprint
from .views import blueprint


class WekoDeposit(object):
    """weko-deposit extension."""

    def __init__(self, app=None):
        """Extension initialization.

        Args:
            app (:obj:`flask.Flask`): The Flask application. Default to `None`.
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization.

        Args:
            app (:obj:`flask.Flask`): The Flask application. Default to `None`.
        """
        self.init_config(app)
        app.register_blueprint(blueprint)
        app.extensions['weko-deposit'] = self

    def init_config(self, app):
        """Initialize configuration.

        Args:
            app (:obj:`flask.Flask`): The Flask application. Default to `None`.
        """
        # Use theme's base template if theme is installed
        if 'BASE_TEMPLATE' in app.config:
            app.config.setdefault(
                'WEKO_DEPOSIT_BASE_TEMPLATE',
                app.config['BASE_TEMPLATE'],
            )

        for k in dir(config):
            if k.startswith('WEKO_DEPOSIT_'):
                app.config.setdefault(k, getattr(config, k))
        before_record_index.connect(append_file_content)


class WekoDepositREST(object):
    """Weko Deposit Rest Obj."""

    def __init__(self, app=None):
        """Extension initialization.

        Args:
            app (:obj:`flask.Flask`): The Flask application. Default to `None`.
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization.

        Initialize the REST endpoints.  Connect all signals if
        `DEPOSIT_REGISTER_SIGNALS` is True.

        Args:
            app (:obj:`flask.Flask`): The Flask application. Default to `None`.
        """
        blueprint = create_blueprint(app,
                                    app.config['WEKO_DEPOSIT_REST_ENDPOINTS'])
        app.register_blueprint(blueprint)
        app.extensions['weko-deposit-rest'] = self
