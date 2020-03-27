# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""CLI tool to harvest records from an OAI-PMH repository."""

from __future__ import absolute_import, print_function

import click
from flask.cli import with_appcontext

from .api import get_records, list_records
from .errors import IdentifiersOrDates
from .signals import oaiharvest_finished
from .tasks import get_specific_records, list_records_from_dates
from .utils import get_identifier_names, write_to_dir


@click.group()
def oaiharvester():
    """Classifier commands."""


@oaiharvester.command()
@click.option('-m', '--metadata-prefix', default=None,
              help="The prefix for the metadata return (e.g. 'oai_dc')")
@click.option('-n', '--name', default=None,
              help="Name of persistent configuration to use.")
@click.option('-s', '--setspecs', default=None,
              help="The 'set' criteria for the harvesting (optional).")
@click.option('-i', '--identifiers', default=None,
              help="A list of unique identifiers for records to be harvested.")
@click.option('-f', '--from-date', default=None,
              help="The lower bound date for the harvesting (optional).")
@click.option('-t', '--until_date', default=None,
              help="The upper bound date for the harvesting (optional).")
@click.option('-u', '--url', default=None,
              help="The upper bound date for the harvesting (optional).")
@click.option('-d', '--directory', default=None,
              help="The directory to store the harvesting results.")
@click.option('-a', '--arguments', default=[], multiple=True,
              help="Arguments to harvesting task, in the form `-a arg1=val1`.")
@click.option('-q', '--quiet', is_flag=True, default=False,
              help="Surpress output.")
@click.option('-k', '--enqueue', is_flag=True, default=False,
              help="Enqueue harvesting and return immediately.")
@click.option('--signals/--no-signals', default=True,
              help="Signals sent with OAI-PMH harvesting results.")
@click.option('-e', '--encoding', default=None,
              help="Override the encoding returned by the server. ISO-8859-1 "
                   "if it is not provided by the server.")
@with_appcontext
def harvest(metadata_prefix, name, setspecs, identifiers, from_date,
            until_date, url, directory, arguments, quiet, enqueue, signals,
            encoding):
    """Harvest records from an OAI repository."""
    arguments = dict(x.split('=', 1) for x in arguments)
    records = None
    if identifiers is None:
        # If no identifiers are provided, a harvest is scheduled:
        # - url / name is used for the endpoint
        # - from_date / lastrun is used for the dates
        # (until_date optionally if from_date is used)
        params = (metadata_prefix, from_date, until_date, url,
                  name, setspecs, signals)
        if enqueue:
            job = list_records_from_dates.delay(*params, **arguments)
            print("Scheduled job {0}".format(job.id))
        else:
            request, records = list_records(
                metadata_prefix,
                from_date,
                until_date,
                url,
                name,
                setspecs,
                encoding
            )
    else:
        if (from_date is not None) or (until_date is not None):
            raise IdentifiersOrDates(
                "Identifiers cannot be used in combination with dates."
            )

        # If identifiers are provided, we schedule an immediate run using them.
        params = (identifiers, metadata_prefix, url,
                  name, signals)
        if enqueue:
            job = get_specific_records.delay(*params, **arguments)
            print("Scheduled job {0}".format(job.id))
        else:
            identifiers = get_identifier_names(identifiers)
            request, records = get_records(
                identifiers,
                metadata_prefix,
                url,
                name,
                encoding
            )

    if records:
        if signals:
            oaiharvest_finished.send(
                request,
                records=records,
                name=name,
                **arguments
            )
        if directory:
            files_created, total = write_to_dir(records, directory)
            print_files_created(files_created)
            print_total_records(total)
        elif not quiet:
            total = print_to_stdout(records)
            print_total_records(total)


def print_to_stdout(records):
    """Print the raw information of the records to the stdout.

    :param records: An iterator of harvested records.
    """
    total = 0
    for record in records:
        total += 1
        click.echo(record.raw)
    return total


def print_files_created(files_created):
    """Print the paths to all files created.

    :param files_created: list of strings containing file paths
    """
    click.echo('Harvested {0} files'.format(len(files_created)))
    for path in files_created:
        click.echo(path)


def print_total_records(total):
    """Print the total number of harvested records.

    :param total: The total number of harvested records.
    """
    click.echo('Number of records harvested {0}'.format(total))
