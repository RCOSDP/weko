# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Click command-line interface for communities management."""

from __future__ import absolute_import, print_function

import click
from flask.cli import with_appcontext
from invenio_db import db
from invenio_files_rest.errors import FilesException
from invenio_indexer.api import RecordIndexer
from invenio_records.api import Record

from .models import Community, InclusionRequest
from .utils import initialize_communities_bucket, save_and_validate_logo


#
# Communities management commands
#
@click.group()
def communities():
    """Management commands for Communities."""


@communities.command()
@with_appcontext
def init():
    """Initialize the communities file storage."""
    try:
        initialize_communities_bucket()
        click.secho('Community init successful.', fg='green')
    except FilesException as e:
        click.secho(e.errors, fg='red')


@communities.command()
@click.argument('community_id')
@click.argument('logo', type=click.File('rb'))
@with_appcontext
def addlogo(community_id, logo):
    """Add logo to the community."""
    # Create the bucket
    try:
        c = Community.get(community_id)
        if not c:
            click.secho('Community {0} does not exist.'.format(community_id),
                        fg='red')
            return
        ext = save_and_validate_logo(logo, logo.name, c.id)
        c.logo_ext = ext
        db.session.commit()
    except Exception as ex:
        db.session.rollback()
        click.secho(ex, fg='red')


@communities.command()
@click.argument('community_id')
@click.argument('record_id')
@click.option('-a', '--accept', 'accept', is_flag=True, default=False)
@with_appcontext
def request(community_id, record_id, accept):
    """Request a record acceptance to a community."""
    try:
        c = Community.get(community_id)
        assert c is not None
        record = Record.get_record(record_id)
        if accept:
            c.add_record(record)
            record.commit()
        else:
            InclusionRequest.create(community=c, record=record,
                                    notify=False)
        db.session.commit()
        RecordIndexer().index_by_id(record_id)
    except Exception as ex:
        db.session.rollback()
        RecordIndexer().delete_by_id(record_id)
        click.secho(ex, fg='red')


@communities.command()
@click.argument('community_id')
@click.argument('record_id')
@with_appcontext
def remove(community_id, record_id):
    """Remove a record from community."""
    try:
        c = Community.get(community_id)
        assert c is not None
        record = Record.get_record(record_id)
        c.remove_record(record)
        db.session.commit()
        RecordIndexer().delete_by_id(record_id)
    except Exception as ex:
        db.session.rollback()
        RecordIndexer().index_by_id(record_id)
        click.secho(ex, fg='red')
