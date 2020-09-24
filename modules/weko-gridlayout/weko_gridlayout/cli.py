# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Command line interface creation kit."""
import click
from flask.cli import with_appcontext
from invenio_files_rest.errors import FilesException

from .models import WidgetType
from .utils import WidgetBucket


@click.group()
def widget_type():
    """Widget Type commands."""


@widget_type.command('create')
@click.argument('type_id')
@click.argument('type_name')
@with_appcontext
def insert_widget_type_to_db(type_id, type_name):
    """Ex: fd Free description."""
    try:
        WidgetType.create(data={"type_id": type_id, "type_name": type_name})
        click.secho('insert widget type success')
    except Exception as e:
        click.secho(str(e))


@click.group()
def widget():
    """Management commands for widgets."""


@widget.command('init')
@with_appcontext
def init():
    """Initialize widget bucket."""
    try:
        WidgetBucket().initialize_widget_bucket()
    except FilesException as e:
        click.secho(e.errors, fg='red')
