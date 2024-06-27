# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Click command-line interface for record management."""

from __future__ import absolute_import, print_function

import sys

import click
from flask import current_app
from flask.cli import with_appcontext
from invenio_pidstore import current_pidstore


def process_minter(value):
    """Load minter from PIDStore registry based on given value.

    :param value: Name of the minter.
    :returns: The minter.
    """
    try:
        return current_pidstore.minters[value]
    except KeyError:
        raise click.BadParameter(
            'Unknown minter {0}. Please use one of {1}.'.format(
                value, ', '.join(current_pidstore.minters.keys())
            )
        )


def process_schema(value):
    """Load schema from JSONSchema registry based on given value.

    :param value: Schema path, relative to the directory when it was
        registered.
    :returns: The schema absolute path.
    """
    schemas = current_app.extensions['invenio-jsonschemas'].schemas
    try:
        return schemas[value]
    except KeyError:
        raise click.BadParameter(
            'Unknown schema {0}. Please use one of:\n {1}'.format(
                value, '\n'.join(schemas.keys())
            )
        )


#
# Deposit management commands
#
@click.group()
def deposit():
    """Deposit management commands."""


@deposit.command()
@click.argument('source')
@with_appcontext
def schema(source):
    """Create deposit schema from an existing schema."""
    click.echo(process_schema(source))
    # TODO


@deposit.command()
@click.argument('source', type=click.File('r'), default=sys.stdin)
@click.option('-i', '--id', 'ids', multiple=True)
@click.option('--force', is_flag=True, default=False)
@with_appcontext
def create(source, ids, force, pid_minter=None):
    """Create new deposit."""


@deposit.command()
@click.option('-i', '--id', 'ids', multiple=True)
def publish(ids):
    """Publish selected deposits."""


@deposit.command()
@click.option('-i', '--id', 'ids', multiple=True)
def edit(ids):
    """Make selected deposits editable."""


@deposit.command()
@click.option('-i', '--id', 'ids', multiple=True)
def discard(ids):
    """Discard selected deposits."""
