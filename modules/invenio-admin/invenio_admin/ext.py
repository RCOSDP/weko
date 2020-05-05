# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-Admin Flask extension."""

from __future__ import absolute_import, print_function

import warnings

import pkg_resources
from flask_admin import Admin, AdminIndexView
from invenio_db import db
from werkzeug.utils import import_string

from . import config
from .views import protected_adminview_factory


class _AdminState(object):
    """State for Invenio-Admin."""

    def __init__(self, app, admin, permission_factory, view_class_factory):
        """Initialize state.

        :param app: The Flask application.
        :param admin: The Flask-Admin application.
        :param permission_factory: The permission factory to restrict access.
        :param view_class_factory: The view class factory to initialize them.
        """
        # Create admin instance.
        self.app = app
        self.admin = admin
        self.permission_factory = permission_factory
        self.view_class_factory = view_class_factory

    def register_view(self, view_class, *args, **kwargs):
        """Register an admin view on this admin instance.

        :param view_class: The view class name passed to the view factory.
        :param args: Positional arugments for view class.
        :param kwargs: Keyword arguments to view class.
        """
        protected_view_class = self.view_class_factory(view_class)
        if 'endpoint' not in kwargs:
            kwargs['endpoint'] = view_class(*args, **kwargs).endpoint
        self.admin.add_view(protected_view_class(*args, **kwargs))

    def load_entry_point_group(self, entry_point_group):
        """Load administration interface from entry point group.

        :param str entry_point_group: Name of the entry point group.
        """
        for ep in pkg_resources.iter_entry_points(group=entry_point_group):
            admin_ep = dict(ep.load())
            keys = tuple(
                k in admin_ep for k in ('model', 'modelview', 'view_class'))

            if keys == (False, False, True):
                self.register_view(
                    admin_ep.pop('view_class'),
                    *admin_ep.pop('args', []),
                    **admin_ep.pop('kwargs', {})
                )
            elif keys == (True, True, False):
                warnings.warn(
                    'Usage of model and modelview kwargs are deprecated in '
                    'favor of view_class, args and kwargs.',
                    PendingDeprecationWarning
                )
                self.register_view(
                    admin_ep.pop('modelview'),
                    admin_ep.pop('model'),
                    admin_ep.pop('session', db.session),
                    **admin_ep
                )
            else:
                raise Exception(
                    'Admin entry point dictionary must contain '
                    'either "view_class" OR "model" and "modelview" keys.')


class InvenioAdmin(object):
    """Invenio-Admin extension."""

    def __init__(self, app=None, **kwargs):
        """Invenio-Admin extension initialization.

        :param app: The Flask application. (Default: ``None``)
        :param kwargs: Passed to :meth:`init_app`.
        """
        if app:
            self._state = self.init_app(app, **kwargs)

    def init_app(self,
                 app,
                 entry_point_group='invenio_admin.views',
                 permission_factory=None,
                 view_class_factory=protected_adminview_factory,
                 index_view_class=AdminIndexView):
        """Flask application initialization.

        :param app: The Flask application.
        :param entry_point_group: Name of entry point group to load
            views/models from. (Default: ``'invenio_admin.views'``)
        :param permission_factory: Default permission factory to use when
            protecting an admin view. (Default:
            :func:`~.permissions.admin_permission_factory`)
        :param view_class_factory: Factory for creating admin view classes on
            the fly. Used to protect admin views with authentication and
            authorization. (Default:
            :func:`~.views.protected_adminview_factory`)
        :param index_view_class: Specify administrative interface index page.
            (Default: :class:`flask_admin.base.AdminIndexView`)
        :param kwargs: Passed to :class:`flask_admin.base.Admin`.
        :returns: Extension state.
        """
        self.init_config(app)

        default_permission_factory = app.config['ADMIN_PERMISSION_FACTORY']
        permission_factory = permission_factory or \
            import_string(default_permission_factory)

        # Create administration app.

        admin = Admin(
            app,
            name=app.config['ADMIN_APPNAME'],
            template_mode=app.config['ADMIN_TEMPLATE_MODE'],
            index_view=view_class_factory(index_view_class)(),
        )

        @app.before_first_request
        def lazy_base_template():
            """Initialize admin base template lazily."""
            base_template = app.config.get('ADMIN_BASE_TEMPLATE')
            if base_template:
                admin.base_template = base_template

        # Create admin state
        state = _AdminState(app, admin, permission_factory, view_class_factory)
        if entry_point_group:
            state.load_entry_point_group(entry_point_group)

        app.extensions['invenio-admin'] = state
        return state

    @staticmethod
    def init_config(app):
        """Initialize configuration.

        :param app: The Flask application.
        """
        # Set default configuration
        for k in dir(config):
            if k == 'ADMIN_BASE_TEMPLATE' and getattr(config, k) is None:
                continue
            if k.startswith('ADMIN_'):
                app.config.setdefault(k, getattr(config, k))

    def __getattr__(self, name):
        """Proxy to state object.

        :param name: Attribute name of the state.
        """
        return getattr(self._state, name, None)
