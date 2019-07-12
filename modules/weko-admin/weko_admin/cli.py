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
import ast

import click
from flask.cli import with_appcontext

from .models import AdminLangSettings, AdminSettings, ApiCertificate, \
    BillingPermission, SessionLifetime, StatisticTarget, StatisticUnit


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


@click.group()
def billing():
    """Billing commands."""


@billing.command('create')
@click.argument('user_id')
@click.argument('is_active')
@with_appcontext
def add_billing_user(user_id, is_active):
    """Add new user can access billing file.

    :param user_id: User's id (default: 1)
    :param is_active: Access state
    """
    try:
        BillingPermission.create(user_id, is_active)
        click.secho('insert billing user success')
    except Exception as e:
        click.secho(str(e))


@billing.command('active')
@click.argument('user_id')
@click.argument('is_active')
@with_appcontext
def toggle_active_billing_user(user_id, is_active):
    """Update access state of billing file.

    :param user_id: User's id (default: 1)
    :param is_active: Access state
    """
    try:
        BillingPermission.activation(user_id, is_active)
        if is_active.lower() == 'true':
            click.secho('active billing user success')
        else:
            click.secho('deactive billing user success')
    except Exception as e:
        click.secho(str(e))


@click.group()
def admin_settings():
    """Settings commands."""


@admin_settings.command('create_settings')
@click.argument('id')
@click.argument('name')
@click.argument('settings')
@with_appcontext
def create_settings(id, name, settings):
    """Add new settings.

    :param name: setting's name
    :param settings: setting info
    """
    try:
        data = ast.literal_eval(settings)
        AdminSettings.update(name, data, id)
        click.secho('insert setting success')
    except Exception as ex:
        click.secho(str(ex))
