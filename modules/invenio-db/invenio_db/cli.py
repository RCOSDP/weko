# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Click command-line interface for database management."""

from __future__ import absolute_import, print_function

import sys

import click
from click import _termui_impl
from flask import current_app
from flask.cli import with_appcontext
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database
from werkzeug.local import LocalProxy

from .utils import create_alembic_version_table, drop_alembic_version_table

_db = LocalProxy(lambda: current_app.extensions['sqlalchemy'].db)

# Fix Python 3 compatibility issue in click
if sys.version_info > (3,):
    _termui_impl.long = int  # pragma: no cover


def abort_if_false(ctx, param, value):
    """Abort command is value is False."""
    if not value:
        ctx.abort()


#
# Database commands
#
@click.group(chain=True)
def db():
    """Database commands."""


@db.command()
@click.option('-v', '--verbose', is_flag=True, default=False)
@with_appcontext
def create(verbose):
    """Create tables."""
    click.secho('Creating all tables!', fg='yellow', bold=True)
    with click.progressbar(_db.metadata.sorted_tables) as bar:
        for table in bar:
            if verbose:
                click.echo(' Creating table {0}'.format(table))
            table.create(bind=_db.engine, checkfirst=True)
    create_alembic_version_table()
    click.secho('Created all tables!', fg='green')


@db.command()
@click.option('-v', '--verbose', is_flag=True, default=False)
@click.option('--yes-i-know', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Do you know that you are going to drop the db?')
@with_appcontext
def drop(verbose):
    """Drop tables."""
    click.secho('Dropping all tables!', fg='red', bold=True)
    with click.progressbar(reversed(_db.metadata.sorted_tables)) as bar:
        for table in bar:
            if verbose:
                click.echo(' Dropping table {0}'.format(table))
            table.drop(bind=_db.engine, checkfirst=True)
        drop_alembic_version_table()
    click.secho('Dropped all tables!', fg='green')


@db.command()
@with_appcontext
def init():
    """Create database."""
    click.secho('Creating database {0}'.format(_db.engine.url),
                fg='green')
    if not database_exists(str(_db.engine.url)):
        create_database(str(_db.engine.url))


@db.command()
@click.option('--yes-i-know', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Do you know that you are going to destroy the db?')
@with_appcontext
def destroy():
    """Drop database."""
    click.secho('Destroying database {0}'.format(_db.engine.url),
                fg='red', bold=True)
    if _db.engine.name == 'sqlite':
        try:
            drop_database(_db.engine.url)
        except FileNotFoundError as e:
            click.secho('Sqlite database has not been initialised',
                        fg='red', bold=True)
    else:
        drop_database(_db.engine.url)
