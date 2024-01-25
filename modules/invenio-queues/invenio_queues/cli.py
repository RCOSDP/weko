# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""CLI for Invenio-Queues."""

import click
from flask.cli import with_appcontext

from .proxies import current_queues


@click.group(chain=True)
def queues():
    """Manage events queue."""


@queues.command("list")
@click.option("--declared", is_flag=True, help="show declared queues.")
@click.option("--undeclared", is_flag=True, help="show undeclared queues.")
@with_appcontext
def list(declared, undeclared):
    """List configured queues."""
    queues = current_queues.queues.values()
    if declared:
        queues = filter(lambda queue: queue.exists, queues)
    elif undeclared:
        queues = filter(lambda queue: not queue.exists, queues)
    queue_names = [queue.routing_key for queue in queues]
    queue_names.sort()
    for queue in queue_names:
        click.secho(queue)


@queues.command("declare")
@click.argument("queues", nargs=-1)
@with_appcontext
def declare(queues):
    """Initialize the given queues."""
    current_queues.declare(queues=queues)
    click.secho(
        "Queues {} have been declared.".format(queues or current_queues.queues.keys()),
        fg="green",
    )


@queues.command("purge")
@click.argument("queues", nargs=-1)
@click.option("--force", is_flag=True, default=False)
@with_appcontext
def purge_queues(force=False, queues=None):
    """Purge the given queues."""
    current_queues.purge(force=force, queues=queues)
    click.secho(
        "Queues {} have been purged.".format(queues or current_queues.queues.keys()),
        fg="green",
    )


@queues.command("delete")
@click.argument("queues", nargs=-1)
@with_appcontext
def delete_queue(queues):
    """Delete the given queues."""
    current_queues.delete(queues=queues)
    click.secho(
        "Queues {} have been deleted.".format(queues or current_queues.queues.keys()),
        fg="green",
    )
