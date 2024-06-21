# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2020 CERN.
# Copyright (C) 2020 University of Münster.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Click command-line interface for file management."""

import click
from click_default_group import DefaultGroup
from flask.cli import with_appcontext
from invenio_db import db

from .models import Location

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
    click.secho(str(bucket), fg="green")


@bucket.command()
@click.argument("source", type=click.Path(exists=True, resolve_path=True))
@click.argument("bucket")
@click.option("--checksum/--no-checksum", default=False)
@click.option("--key-prefix", default="")
@with_appcontext
def cp(source, bucket, checksum, key_prefix):
    """Create new bucket from all files in directory."""
    from .helpers import populate_from_path
    from .models import Bucket

    for object_version in populate_from_path(
        Bucket.get(bucket), source, checksum=checksum, key_prefix=key_prefix
    ):
        click.secho(str(object_version))
    db.session.commit()


def _unset_default_location():
    """Unset default location, if there is one."""
    default_location = Location.get_default()
    if default_location is not None:
        default_location.default = False


@files.group(cls=DefaultGroup, default="create")
def location():
    """Manage locations."""


@location.command()
@click.argument("name")
@click.argument("uri")
@click.option("--default", is_flag=True, default=False)
@with_appcontext
def create(name, uri, default):
    """Create a new location."""
    location = Location.get_by_name(name)
    if location:
        click.secho(
            "Location {} (uri: {} default: {}) already exists".format(
                location.name, location.uri, str(location.default)
            ),
            fg="yellow",
        )

    else:
        if default:
            _unset_default_location()

        location = Location(name=name, uri=uri, default=default)
        db.session.add(location)
        db.session.commit()
        click.secho(
            "Location {} {} as default {} stored in database".format(
                location.name, location.uri, str(location.default)
            ),
            fg="green",
        )


@location.command()
@with_appcontext
def list():
    """Return the list of locations."""
    locations = Location.all()
    for location in locations:
        click.secho(
            "{} {} as default {}".format(
                location.name, location.uri, str(location.default)
            ),
            fg="green",
        )


@location.command()
@click.argument("name")
@with_appcontext
def set_default(name):
    """Set default a location as default. The location must already exist.

    If another location was marked as default it unsets it.
    """
    location = Location.get_by_name(name)
    if location is not None:
        _unset_default_location()
        location.default = True
        db.session.commit()
        click.secho(
            "Location {} {} set as default ({})".format(
                location.name, location.uri, str(location.default)
            ),
            fg="green",
        )

    click.secho("Location {} not found".format(name), fg="red")
