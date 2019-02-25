# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Indextree-Journal is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of weko-indextree-journal."""

from __future__ import absolute_import, print_function

from flask_babelex import gettext as _

from . import config
from .views import blueprint
from .rest import create_blueprint


class WekoIndextreeJournal(object):
    """WEKO-Indextree-Journal extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        # TODO: This is an example of translation string with comment. Please
        # remove it.
        # NOTE: This is a note to a translator.
        _('A translation string')
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)

        print('index tree journal blueprint')
        print(blueprint.__dict__)

        app.register_blueprint(blueprint)
        app.extensions['weko-indextree-journal'] = self

    def init_config(self, app):
        """Initialize configuration."""
        # Use theme's base template if theme is installed
        if 'BASE_EDIT_TEMPLATE' in app.config:
            app.config.setdefault(
                'WEKO_INDEXTREE_JOURNAL_BASE_TEMPLATE',
                app.config['BASE_EDIT_TEMPLATE'],
            )
        for k in dir(config):
            if k.startswith('WEKO_INDEXTREE_JOURNAL_'):
                app.config.setdefault(k, getattr(config, k))

class WekoIndextreeJournalREST(object):
    """
      weko-indextree-journal Rest Obj
    """

    def __init__(self, app=None):
        """Extension initialization.

        :param app: An instance of :class:`flask.Flask`.
        """
        if app:
            self.init_app(app)

    def init_app(self, app):
        print('init_app WekoIndextreeJournalREST')
        """Flask application initialization.

        Initialize the REST endpoints.  Connect all signals if
        `DEPOSIT_REGISTER_SIGNALS` is True.

        :param app: An instance of :class:`flask.Flask`.
        """
        self.init_config(app)

        print('Journal rest dict')
        print(app.config.__dict__)
        blueprint = create_blueprint(app,
                                     app.config['WEKO_INDEXTREE_JOURNAL_REST_ENDPOINTS'])
        app.register_blueprint(blueprint)
        app.extensions['weko-indextree-journal-rest'] = self

    def init_config(self, app):
        """Initialize configuration.

        :param app: An instance of :class:`flask.Flask`.
        """
        for k in dir(config):
            if k.startswith('WEKO_INDEXTREE_JOURNAL_'):
                app.config.setdefault(k, getattr(config, k))
