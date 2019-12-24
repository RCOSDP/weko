# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Click command-line interface for file management."""

from __future__ import absolute_import, print_function

import click
from flask.cli import with_appcontext
from invenio_db import db

#
# File management commands
#


@click.group()
def files():
    """File management commands."""


@files.group()
def bucket():
    """Manage buckets."""


@bucket.command()
@with_appcontext
def touch():
    """Create new bucket."""
    from .models import Bucket
    bucket = Bucket.create()
    db.session.commit()
    click.secho(str(bucket), fg='green')


@bucket.command()
@click.argument('source', type=click.Path(exists=True, resolve_path=True))
@click.argument('bucket')
@click.option('--checksum/--no-checksum', default=False)
@click.option('--key-prefix', default='')
@with_appcontext
def cp(source, bucket, checksum, key_prefix):
    """Create new bucket from all files in directory."""
    from .models import Bucket
    from .helpers import populate_from_path
    for object_version in populate_from_path(
            Bucket.get(bucket), source, checksum=checksum,
            key_prefix=key_prefix):
        click.secho(str(object_version))
    db.session.commit()


@files.command()
@click.argument('name')
@click.argument('uri')
@click.option('--default', is_flag=True, default=False)
@with_appcontext
def location(name, uri, default):
    """Create new location."""
    from .models import Location
    location = Location(name=name, uri=uri, default=default)
    db.session.add(location)
    db.session.commit()
    click.secho(str(location), fg='green')
