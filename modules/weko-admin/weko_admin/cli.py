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

from .models import AdminLangSettings, SessionLifetime


@click.group()
def lifetime():
    """Lifetime commands."""


@lifetime.command('init')
@click.argument('minutes', default=30)
@with_appcontext
def init_lifetime(minutes):
    """
    Init action.

    :param minutes: Lifetime in minutes.
    """
    db_lifetime = SessionLifetime.get_validtime()
    if db_lifetime is None:
        db_lifetime = SessionLifetime(lifetime=minutes)
        db_lifetime.create()

    click.secho('SessionLifetime has been initialised. lifetime=%s minutes' %
                minutes, fg='green')


@click.group()
def language():
    """Language commands."""


@language.command('create')
@click.argument('lang_code')
@click.argument('lang_name')
@click.argument('is_registered')
@click.argument('sequence')
@click.argument('is_active')
@with_appcontext
def insert_lang_to_db(lang_code, lang_name, is_registered, sequence, is_active):
    """
    Ex: ja Japanese true 12 true
    """
    try:
        AdminLangSettings.create(lang_code, lang_name,
                                 is_registered, sequence, is_active)
        click.secho('insert language success')
    except Exception as e:
        click.secho(str(e))
