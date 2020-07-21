# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Database management for Invenio."""

from __future__ import absolute_import, print_function

import os

import pkg_resources
import sqlalchemy as sa
from flask_alembic import Alembic
from sqlalchemy_utils.functions import get_class_by_table

from .cli import db as db_cmd
from .shared import db
from .utils import versioning_models_registered


class InvenioDB(object):
    """Invenio database extension."""

    def __init__(self, app=None, **kwargs):
        """Extension initialization."""
        self.alembic = Alembic(run_mkdir=False, command_name='alembic')
        if app:
            self.init_app(app, **kwargs)

    def init_app(self, app, **kwargs):
        """Initialize application object."""
        self.init_db(app, **kwargs)

        app.config.setdefault('ALEMBIC', {
            'script_location': pkg_resources.resource_filename(
                'invenio_db', 'alembic'
            ),
            'version_locations': [
                (base_entry.name, pkg_resources.resource_filename(
                    base_entry.module_name, os.path.join(*base_entry.attrs)
                )) for base_entry in pkg_resources.iter_entry_points(
                    'invenio_db.alembic'
                )
            ],
        })

        self.alembic.init_app(app)
        app.extensions['invenio-db'] = self
        app.cli.add_command(db_cmd)

    def init_db(self, app, entry_point_group='invenio_db.models', **kwargs):
        """Initialize Flask-SQLAlchemy extension."""
        # Setup SQLAlchemy
        app.config.setdefault(
            'SQLALCHEMY_DATABASE_URI',
            'sqlite:///' + os.path.join(app.instance_path, app.name + '.db')
        )
        app.config.setdefault('SQLALCHEMY_ECHO', False)

        # Initialize Flask-SQLAlchemy extension.
        database = kwargs.get('db', db)
        database.init_app(app)

        # Initialize versioning support.
        self.init_versioning(app, database, kwargs.get('versioning_manager'))

        # Initialize model bases
        if entry_point_group:
            for base_entry in pkg_resources.iter_entry_points(
                    entry_point_group):
                base_entry.load()

        # All models should be loaded by now.
        sa.orm.configure_mappers()
        # Ensure that versioning classes have been built.
        if app.config['DB_VERSIONING']:
            manager = self.versioning_manager
            if manager.pending_classes:
                if not versioning_models_registered(manager, database.Model):
                    manager.builder.configure_versioned_classes()
            elif 'transaction' not in database.metadata.tables:
                manager.declarative_base = database.Model
                manager.create_transaction_model()
                manager.plugins.after_build_tx_class(manager)

    def init_versioning(self, app, database, versioning_manager=None):
        """Initialize the versioning support using SQLAlchemy-Continuum."""
        try:
            pkg_resources.get_distribution('sqlalchemy_continuum')
        except pkg_resources.DistributionNotFound:  # pragma: no cover
            default_versioning = False
        else:
            default_versioning = True

        app.config.setdefault('DB_VERSIONING', default_versioning)

        if not app.config['DB_VERSIONING']:
            return

        if not default_versioning:  # pragma: no cover
            raise RuntimeError(
                'Please install extra versioning support first by running '
                'pip install invenio-db[versioning].'
            )

        # Now we can import SQLAlchemy-Continuum.
        from sqlalchemy_continuum import make_versioned
        from sqlalchemy_continuum import versioning_manager as default_vm
        from sqlalchemy_continuum.plugins import FlaskPlugin

        # Try to guess user model class:
        if 'DB_VERSIONING_USER_MODEL' not in app.config:  # pragma: no cover
            try:
                pkg_resources.get_distribution('invenio_accounts')
            except pkg_resources.DistributionNotFound:
                user_cls = None
            else:
                user_cls = 'User'
        else:
            user_cls = app.config.get('DB_VERSIONING_USER_MODEL')

        plugins = [FlaskPlugin()] if user_cls else []

        # Call make_versioned() before your models are defined.
        self.versioning_manager = versioning_manager or default_vm
        make_versioned(
            user_cls=user_cls,
            manager=self.versioning_manager,
            plugins=plugins,
        )

        # Register models that have been loaded beforehand.
        builder = self.versioning_manager.builder

        for tbl in database.metadata.tables.values():
            builder.instrument_versioned_classes(
                database.mapper, get_class_by_table(database.Model, tbl)
            )
