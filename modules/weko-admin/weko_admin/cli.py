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
import json
from flask.cli import with_appcontext
from weko_authors.models import AuthorsPrefixSettings, AuthorsAffiliationSettings

from .models import AdminLangSettings, AdminSettings, ApiCertificate, \
    BillingPermission, FacetSearchSetting, SessionLifetime, StatisticTarget, \
    StatisticUnit


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
@click.option('--registered', is_flag=True, default=False)
@click.argument('sequence')
@click.option('--active', is_flag=True, default=False)
@with_appcontext
def insert_lang_to_db(
        lang_code,
        lang_name,
        registered,
        sequence,
        active):
    """Ex: ja Japanese true 12 true."""
    try:
        AdminLangSettings.create(lang_code, lang_name,
                                 registered, sequence, active)
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
@click.option('--active', is_flag=True, default=False)
@with_appcontext
def add_billing_user(user_id, active):
    """Add new user can access billing file.

    :param user_id: User's id (default: 1)
    :param active: Access state
    """
    try:
        BillingPermission.create(user_id, active)
        click.secho('insert billing user success')
    except Exception as e:
        click.secho(str(e))


@billing.command('active')
@click.argument('user_id')
@click.option('--active', is_flag=True, default=False)
@with_appcontext
def toggle_active_billing_user(user_id, active):
    """Update access state of billing file.

    :param user_id: User's id (default: 1)
    :param active: Access state
    """
    try:
        BillingPermission.activation(user_id, active)
        if active:
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

@admin_settings.command('mapping_update')
@click.option('--shib_eppn', type=str, default=None)
@click.option('--shib_role_authority_name', type=str, default=None)
@click.option('--shib_mail', type=str, default=None)
@click.option('--shib_user_name', type=str, default=None)
@with_appcontext
def update_attribute_mapping(shib_eppn, shib_role_authority_name, shib_mail, shib_user_name):
    """Update Attribute Mapping between Shibboleth and WEKO3."""
    attribute_mappings = AdminSettings.get('attribute_mapping', dict_to_object=False)
    if isinstance(attribute_mappings, str):
        attribute_mappings = json.loads(attribute_mappings)

    attributes = {
        'shib_eppn': attribute_mappings.get('shib_eppn', ''),
        'shib_role_authority_name': attribute_mappings.get('shib_role_authority_name', ''),
        'shib_mail': attribute_mappings.get('shib_mail', ''),
        'shib_user_name': attribute_mappings.get('shib_user_name', '')
    }

    try:
        if shib_eppn is not None:
            attributes['shib_eppn'] = shib_eppn
        if shib_role_authority_name is not None:
            attributes['shib_role_authority_name'] = shib_role_authority_name
        if shib_mail is not None:
            attributes['shib_mail'] = shib_mail
        if shib_user_name is not None:
            attributes['shib_user_name'] = shib_user_name

        AdminSettings.update('attribute_mapping', attributes)
        click.secho("Mapping and update were successful.")

    except Exception as e:
        click.secho(str(e))

@click.group()
def authors_prefix():
    """Authors prefix settings commands."""


@authors_prefix.command('default_settings')
@click.argument('name')
@click.argument('scheme')
@click.argument('url')
@with_appcontext
def create_default_settings(name, scheme, url):
    """Create default settings."""
    try:
        AuthorsPrefixSettings.create(name, scheme, url)
        click.secho('insert setting success')
    except Exception as ex:
        click.secho(str(ex))

@click.group()
def authors_affiliation():
    """Authors affiliation settings commands."""


@authors_affiliation.command('default_settings')
@click.argument('name')
@click.argument('scheme')
@click.argument('url')
@with_appcontext
def create_default_affiliation_settings(name, scheme, url):
    """Create default settings."""
    try:
        AuthorsAffiliationSettings.create(name, scheme, url)
        click.secho('insert setting success')
    except Exception as ex:
        click.secho(str(ex))

@click.group()
def facet_search_setting():
    """Facet search commands."""


@facet_search_setting.command('create')
@click.argument('name_en')
@click.argument('name_jp')
@click.argument('mapping')
@click.argument('aggregations')
@click.argument('active')
@click.argument('ui_type')
@click.argument('display_number')
@click.argument('is_open')
@click.argument('search_condition')
@click.option('--active', is_flag=True, default=False)
@click.option('--is_open', is_flag=True, default=False)
@with_appcontext
def insert_facet_search_to_db(name_en, name_jp, mapping, aggregations, active, ui_type, display_number, is_open, search_condition):
    """Insert facet search."""
    try:
        facet_search = {
            'name_en': name_en,
            'name_jp': name_jp,
            'mapping': mapping,
            'aggregations': ast.literal_eval(aggregations),
            'active': active,
            'ui_type': ui_type,
            'display_number': display_number,
            'is_open': is_open,
            'search_condition': search_condition
        }
        FacetSearchSetting.create(facet_search)
        click.secho('insert facet search')
    except Exception as e:
        click.secho(str(e))
