# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""Module tests."""

import re
from datetime import datetime

import pytest
import responses
from invenio_db import db
from weko_index_tree.models import Index

from invenio_oaiharvester.errors import InvenioOAIHarvesterError
from invenio_oaiharvester.models import HarvestSettings
from invenio_oaiharvester.signals import oaiharvest_finished
from invenio_oaiharvester.tasks import create_indexes, event_counter, \
    get_specific_records, list_records_from_dates, map_indexes, \
    run_harvesting


@responses.activate
def test_get_specific_records(app, sample_record_xml):
    """Test that getting records via identifiers work with prefix."""
    def foo(request, records, name):
        assert len(records) == 1

    responses.add(
        responses.GET,
        'http://export.arxiv.org/oai2',
        body=sample_record_xml,
        content_type='text/xml'
    )
    oaiharvest_finished.connect(foo)
    try:
        with app.app_context():
            get_specific_records(
                'oai:arXiv.org:1507.03011',
                metadata_prefix="arXiv",
                url='http://export.arxiv.org/oai2'
            )
            # As a list of identifiers
            get_specific_records(
                ['oai:arXiv.org:1507.03011'],
                metadata_prefix="arXiv",
                url='http://export.arxiv.org/oai2'
            )
    finally:
        oaiharvest_finished.disconnect(foo)


@responses.activate
def test_list_records_from_dates(app, sample_list_xml):
    """Check harvesting of records from multiple setspecs."""
    def bar(request, records, name):
        assert len(records) == 150

    responses.add(
        responses.GET,
        re.compile(r'http?://export.arxiv.org/oai2.*set=physics.*'),
        body=sample_list_xml,
        content_type='text/xml'
    )
    oaiharvest_finished.connect(bar)
    try:
        with app.app_context():
            list_records_from_dates(
                metadata_prefix='arXiv',
                from_date='2015-01-15',
                until_date='2015-01-20',
                url='http://export.arxiv.org/oai2',
                name=None,
                setspecs='physics'
            )
    finally:
        oaiharvest_finished.disconnect(bar)


@responses.activate
def test_list_records_from_dates(app, sample_list_xml):
    """Check harvesting of records from multiple setspecs."""
    try:
        with app.app_context():
            index = Index()
            db.session.add(index)
            db.session.commit()

            harvesting = HarvestSettings(
                repository_name='name',
                base_url='https://jpcoar.repo.nii.ac.jp/oai',
                metadata_prefix='jpcoar_1.0',
                index_id=index.id,
                update_style='0',
                auto_distribution='0')
            db.session.add(harvesting)
            db.session.commit()

            # run_harvesting(
            #     harvesting.id,
            #     datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z'),
            #     {'ip_address': '0.0,0.0',
            #         'user_agent': '',
            #         'user_id': 1,
            #         'session_id': '1'}
            # )
    finally:
        return


def test_create_indexes(app):
    """Check harvesting of records from multiple setspecs."""
    with app.app_context():
        index = Index()
        db.session.add(index)
        db.session.commit()

        create_indexes(index.id, {
            '1': 'set_name_1',
            '2': 'set_name_2'
        })


def test_map_indexes(app):
    """Check harvesting of records from multiple setspecs."""
    with app.app_context():
        index = Index()
        db.session.add(index)
        db.session.commit()

        map_indexes({
            '1': 'set_name_1',
            '2': 'set_name_2'
        }, index.id)


def test_event_counter(app):
    """Check harvesting of records from multiple setspecs."""
    counter = {}

    event_counter('a', counter)
    event_counter('a', counter)
