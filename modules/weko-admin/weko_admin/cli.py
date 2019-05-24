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

from .models import AdminLangSettings, ApiCertificate, SessionLifetime, \
    StatisticTarget, StatisticUnit


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
def insert_lang_to_db(
        lang_code,
        lang_name,
        is_registered,
        sequence,
        is_active):
    """Ex: ja Japanese true 12 true."""
    try:
        AdminLangSettings.create(lang_code, lang_name,
                                 is_registered, sequence, is_active)
        click.secho('insert language success')
    except Exception as e:
        click.secho(str(e))


@click.group()
def cert():
    """Cert commands."""


@cert.command('insert')
@click.argument('api_code')
@click.argument('api_name')
@click.argument('cert_data', default='')
@with_appcontext
def save_api_certification(api_code, api_name, cert_data):
    """Insert API Certification."""
    if ApiCertificate.insert_new_api_cert(api_code, api_name, cert_data):
        click.secho('insert cert success')
    else:
        click.secho('insert cert failed')


@cert.command('update')
@click.argument('api_code')
@click.argument('api_name')
@click.argument('cert_data', default='')
@with_appcontext
def update_api_certification(api_code, api_name, cert_data):
    """Update API Certification."""
    if ApiCertificate.update_api_cert(api_code, api_name, cert_data):
        click.secho('update cert success')
    else:
        click.secho('update cert failed')


@click.group()
def report():
    """Report Unit and Target."""


@report.command('create_unit')
@click.argument('unit_id')
@click.argument('unit_name')
@with_appcontext
def save_report_unit(unit_id, unit_name):
    """Add data for Statics report unit."""
    try:
        StatisticUnit.create(unit_id, unit_name)
        click.secho('insert report unit success')
    except Exception as e:
        click.secho(str(e))


@report.command('create_target')
@click.argument('target_id')
@click.argument('target_name')
@click.argument('target_unit')
@with_appcontext
def save_report_target(target_id, target_name, target_unit):
    """Add data for Statics report unit."""
    try:
        StatisticTarget.create(target_id, target_name, target_unit)
        click.secho('insert report target success')
    except Exception as e:
        click.secho(str(e))
