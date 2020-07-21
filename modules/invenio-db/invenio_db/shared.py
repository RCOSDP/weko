# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Shared database object for Invenio."""

from flask_sqlalchemy import SQLAlchemy as FlaskSQLAlchemy
from sqlalchemy import MetaData, event, util
from sqlalchemy.engine import Engine
from werkzeug.local import LocalProxy

NAMING_CONVENTION = util.immutabledict({
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(constraint_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s',
})
"""Configuration for constraint naming conventions."""

metadata = MetaData(naming_convention=NAMING_CONVENTION)
"""Default database metadata object holding associated schema constructs."""


class SQLAlchemy(FlaskSQLAlchemy):
    """Implement or overide extension methods."""

    def apply_driver_hacks(self, app, info, options):
        """Call before engine creation."""
        # Don't forget to apply hacks defined on parent object.
        super(SQLAlchemy, self).apply_driver_hacks(app, info, options)

        if info.drivername == 'sqlite':
            connect_args = options.setdefault('connect_args', {})

            if 'isolation_level' not in connect_args:
                # disable pysqlite's emitting of the BEGIN statement entirely.
                # also stops it from emitting COMMIT before any DDL.
                connect_args['isolation_level'] = None

            if not event.contains(Engine, 'connect', do_sqlite_connect):
                event.listen(Engine, 'connect', do_sqlite_connect)
            if not event.contains(Engine, 'begin', do_sqlite_begin):
                event.listen(Engine, 'begin', do_sqlite_begin)

            from sqlite3 import register_adapter

            def adapt_proxy(proxy):
                """Get current object and try to adapt it again."""
                return proxy._get_current_object()

            register_adapter(LocalProxy, adapt_proxy)

        elif info.drivername == 'postgresql+psycopg2':  # pragma: no cover
            from psycopg2.extensions import adapt, register_adapter

            def adapt_proxy(proxy):
                """Get current object and try to adapt it again."""
                return adapt(proxy._get_current_object())

            register_adapter(LocalProxy, adapt_proxy)

        elif info.drivername == 'mysql+pymysql':  # pragma: no cover
            from pymysql import converters

            def escape_local_proxy(val, mapping):
                """Get current object and try to adapt it again."""
                return converters.escape_item(
                    val._get_current_object(),
                    self.engine.dialect.encoding,
                    mapping=mapping,
                )

            converters.conversions[LocalProxy] = escape_local_proxy
            converters.encoders[LocalProxy] = escape_local_proxy


def do_sqlite_connect(dbapi_connection, connection_record):
    """Ensure SQLite checks foreign key constraints.

    For further details see "Foreign key support" sections on
    https://docs.sqlalchemy.org/en/latest/dialects/sqlite.html#foreign-key-support
    """
    # Enable foreign key constraint checking
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON')
    cursor.close()


def do_sqlite_begin(dbapi_connection):
    """Ensure SQLite transaction are started properly.

    For further details see "Foreign key support" sections on
    https://docs.sqlalchemy.org/en/rel_1_0/dialects/sqlite.html#pysqlite-serializable # noqa
    """
    # emit our own BEGIN
    dbapi_connection.execute('BEGIN')


db = SQLAlchemy(metadata=metadata)
"""Shared database instance using Flask-SQLAlchemy extension.

This object is initialized during initialization of ``InvenioDB``
extenstion that takes care about loading all entrypoints from key
``invenio_db.models``.
"""
