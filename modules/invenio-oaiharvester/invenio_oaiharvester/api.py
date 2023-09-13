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

"""Invenio-OAIHarvester API to harvest items from OAI-PMH servers.

If you need to schedule or run harvests from inside of Python, you can use our
API:

.. code-block:: python

    from invenio_oaiharvester.api import get_records

    request, records = get_records(identifiers=["oai:arXiv.org:1207.7214"],
                                   url="http://export.arxiv.org/oai2")
    for record in records:
        print rec.raw
"""

from __future__ import absolute_import, print_function

import datetime

from flask import current_app, render_template
from invenio_db import db
from invenio_mail.api import send_mail
from sickle import Sickle
from sickle.oaiexceptions import NoRecordsMatch
from weko_accounts.api import get_user_info_by_role_name
from weko_admin.models import AdminLangSettings

from .errors import NameOrUrlMissing, WrongDateCombination
from .models import HarvestSettings
from .utils import get_oaiharvest_object


def _(x):
    return x


def list_records(metadata_prefix=None, from_date=None, until_date=None,
                 url=None, name=None, setspecs=None, encoding=None):
    """Harvest multiple records from an OAI repo.

    :param metadata_prefix: The prefix for the metadata return
                            (defaults to 'oai_dc').
    :param from_date: The lower bound date for the harvesting (optional).
    :param until_date: The upper bound date for the harvesting (optional).
    :param url: The The url to be used to create the endpoint.
    :param name: The name of the OAIHarvestConfig to use instead of passing
                 specific parameters.
    :param setspecs: The 'set' criteria for the harvesting (optional).
    :param encoding: Override the encoding returned by the server. ISO-8859-1
                     if it is not provided by the server.
    :return: request object, list of harvested records
    """
    lastrun = None
    if name:
        url, _metadata_prefix, lastrun, _setspecs = get_info_by_oai_name(name)

        # In case we provide a prefix, we don't want it to be
        # overwritten by the one we get from the name variable.
        if metadata_prefix is None:
            metadata_prefix = _metadata_prefix
        if setspecs is None:
            setspecs = _setspecs
    elif not url:
        raise NameOrUrlMissing(
            "Retry using the parameters -n <name> or -u <url>."
        )

    request = Sickle(url, encoding=encoding)

    # By convention, when we have a url we have no lastrun, and when we use
    # the name we can either have from_date (if provided) or lastrun.
    dates = {
        'from': from_date or lastrun,
        'until': until_date
    }

    # Sanity check
    if (dates['until'] is not None) and (dates['from'] > dates['until']):
        raise WrongDateCombination("'Until' date larger than 'from' date.")

    lastrun_date = datetime.datetime.now()

    # Use a dict to only return the same record once
    # (e.g. if it is part of several sets)
    records = {}
    setspecs = setspecs.split() or [None]
    for spec in setspecs:
        params = {
            'metadataPrefix': metadata_prefix or "oai_dc"
        }
        params.update(dates)
        if spec:
            params['set'] = spec
        try:
            for record in request.ListRecords(**params):
                records[record.header.identifier] = record
        except NoRecordsMatch:
            continue

    # Update lastrun?
    if from_date is None and until_date is None and name is not None:
        oai_source = get_oaiharvest_object(name)
        oai_source.update_lastrun(lastrun_date)
        oai_source.save()
    return request, records.values()


def get_records(identifiers, metadata_prefix=None, url=None, name=None,
                encoding=None):
    """Harvest specific records from an OAI repo via OAI-PMH identifiers.

    :param metadata_prefix: The prefix for the metadata return
                            (defaults to 'oai_dc').
    :param identifiers: list of unique identifiers for records to be harvested.
    :param url: The The url to be used to create the endpoint.
    :param name: The name of the OAIHarvestConfig to use instead of passing
                 specific parameters.
    :param encoding: Override the encoding returned by the server. ISO-8859-1
                     if it is not provided by the server.
    :return: request object, list of harvested records
    """
    if name:
        url, _metadata_prefix, _, __ = get_info_by_oai_name(name)

        # In case we provide a prefix, we don't want it to be
        # overwritten by the one we get from the name variable.
        if metadata_prefix is None:
            metadata_prefix = _metadata_prefix
    elif not url:
        raise NameOrUrlMissing(
            "Retry using the parameters -n <name> or -u <url>."
        )

    request = Sickle(url, encoding=encoding)
    records = []
    for identifier in identifiers:
        arguments = {
            'identifier': identifier,
            'metadataPrefix': metadata_prefix or "oai_dc"
        }
        records.append(request.GetRecord(**arguments))
    return request, records


def get_info_by_oai_name(name):
    """Get basic OAI request data from the OAIHarvestConfig model.

    :param name: name of the source (OAIHarvestConfig.name)

    :return: (url, metadataprefix, lastrun as YYYY-MM-DD, setspecs)
    """
    obj = get_oaiharvest_object(name)
    lastrun = obj.lastrun.strftime("%Y-%m-%d")
    return obj.baseurl, obj.metadataprefix, lastrun, obj.setspecs


def send_run_status_mail(harvesting, harvest_log):
    """Send harvest runnig status mail."""
    try:
        result = _('Running')
        if harvest_log.status == 'Successful':
            result = _('Successful')
        elif harvest_log.status == 'Suspended':
            result = _('Suspended')
        elif harvest_log.status == 'Cancel':
            result = _('Cancel')
        elif harvest_log.status == 'Failed':
            result = _('Failed')
        # mail title
        subject = '[{0}] '.format(current_app.config['THEME_SITENAME']) + \
            _('Hervesting Result')
        # recipient mail list
        users = []
        users += get_user_info_by_role_name('Repository Administrator')
        users += get_user_info_by_role_name('Community Administrator')
        mail_list = []
        for user in users:
            mail_list.append(user.email)

        update_style_name = \
            HarvestSettings.UpdateStyle(int(harvesting.update_style)).name
        if update_style_name == 'Difference':
            update_style = _('Difference')
        else:
            update_style = _('Bulk')

        with current_app.test_request_context() as ctx:
            default_lang = AdminLangSettings.get_registered_language()[0]
            # setting locale
            setattr(ctx, 'babel_locale', default_lang['lang_code'])
            # send mail
            send_mail(subject, mail_list,
                      html=render_template('invenio_oaiharvester/run_stat_mail.html',
                                           result_text=result,
                                           errmsg=harvest_log.errmsg,
                                           harvesting=harvesting,
                                           counter=harvest_log.counter,
                                           start_time=harvest_log.start_time,
                                           end_time=harvest_log.end_time,
                                           update_style=update_style,
                                           lang_code=default_lang['lang_code']))
    except Exception as ex:
        current_app.logger.error(ex)
