# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Click command-line interface for record management."""

from __future__ import absolute_import, print_function

import sys

import click
from flask import current_app
from flask.cli import with_appcontext
from invenio_pidstore import current_pidstore
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
    
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

@deposit.command('reindex')
@click.option('-r', '--recid', required=True)
@with_appcontext
def reindex(recid):
    """Initialize indexing queue."""

    click.secho('Indexing record {} ...'.format(recid), fg='green')
    try:
        pid = PersistentIdentifier.get_by_object(pid_type='recid',
                                                 object_type='rec',
                                                 object_uuid=recid)
        
        if pid:
            query = PersistentIdentifier.query.filter_by(pid_type='recid',object_type='rec',object_uuid=recid).values(PersistentIdentifier.object_uuid)
            query = (x[0] for x in query)
            RecordIndexer().bulk_index(query)
            RecordIndexer().process_bulk_queue(es_bulk_kwargs={'raise_on_error': True})
    except PIDDoesNotExistError as e:
        click.secho('Chosen record doesn\'t exist', fg='red')
    except Exception as e:
        click.secho(e, fg='red')
    click.secho('Reindex process finished!', fg='green')
