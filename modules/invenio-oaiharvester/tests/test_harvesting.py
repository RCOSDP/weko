# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

import os
import re
import time

import pytest
import responses

from invenio_oaiharvester import get_records, list_records
from invenio_oaiharvester.errors import WrongDateCombination


@responses.activate
def test_model_based_harvesting(app, sample_config, sample_record_xml):
    """Test harvesting using model."""
    responses.add(
        responses.GET,
        'http://export.arxiv.org/oai2',
        body=sample_record_xml,
        content_type='text/xml'
    )

    with app.app_context():
        _, records = get_records(['oai:arXiv.org:1507.03011'],
                                 name=sample_config)
        assert len(records) == 1


@responses.activate
def test_model_based_utf8_harvesting(app, sample_config,
                                     sample_record_xml_utf8):
    """Test harvesting using model encoded in utf-8."""
    responses.add(
        responses.GET,
        'http://export.arxiv.org/oai2',
        body=sample_record_xml_utf8,
        content_type='text/xml;charset=utf-8'
    )

    with app.app_context():
        _, records = get_records(['oai:arXiv.org:1207.1019'],
                                 name=sample_config)
        record = records.pop()
        assert record.raw.find(u'Stéphane') >= 0
    responses.remove(
        responses.GET,
        'http://export.arxiv.org/oai2'
    )
    responses.add(
        responses.GET,
        'http://export.arxiv.org/oai2',
        body=sample_record_xml_utf8,
        content_type='text/xml'
    )

    with app.app_context():
        _, records = get_records(['oai:arXiv.org:1207.1019'],
                                 name=sample_config, encoding='utf-8')
        record = records.pop()
        assert record.raw.find(u'Stéphane') >= 0


@responses.activate
def test_model_based_harvesting_list(app, sample_config, sample_list_xml):
    """Test harvesting using model."""
    from invenio_oaiharvester.utils import get_oaiharvest_object
    responses.add(
        responses.GET,
        re.compile(r'http?://export.arxiv.org/oai2.*set=physics.*'),
        body=sample_list_xml,
        content_type='text/xml'
    )
    with app.app_context():
        source = get_oaiharvest_object(sample_config)
        last_updated = source.lastrun
        time.sleep(0.1)  # to allow for date checking to work better
        _, records = list_records(name=sample_config)

        assert len(records) == 150
        assert last_updated < get_oaiharvest_object(sample_config).lastrun


def test_raise_missing_info(app):
    """Check that the proper exception is raised if name or url is missing."""
    from invenio_oaiharvester.errors import NameOrUrlMissing

    with app.app_context():
        with pytest.raises(NameOrUrlMissing):
            list_records()
        with pytest.raises(NameOrUrlMissing):
            get_records([])


def test_raise_wrong_date(app):
    """Check harvesting of records from multiple setspecs."""
    with app.app_context():
        with pytest.raises(WrongDateCombination):
            list_records(
                metadata_prefix='arXiv',
                from_date='2015-01-18',
                until_date='2015-01-17',
                url='http://export.arxiv.org/oai2',
                name=None,
                setspecs='physics:hep-lat'
            )


@responses.activate
def test_list_records(app, sample_list_xml, sample_list_xml_cs):
    """Check harvesting of records from multiple setspecs."""
    responses.add(
        responses.GET,
        re.compile(r'http?://export.arxiv.org/oai2.*set=cs.*'),
        body=sample_list_xml_cs,
        content_type='text/xml'
    )
    responses.add(
        responses.GET,
        re.compile(r'http?://export.arxiv.org/oai2.*set=physics.*'),
        body=sample_list_xml,
        content_type='text/xml'
    )
    with app.app_context():
        _, records = list_records(
            metadata_prefix='arXiv',
            from_date='2015-01-15',
            until_date='2015-01-20',
            url='http://export.arxiv.org/oai2',
            name=None,
            setspecs='cs physics'
        )
        # 46 cs + 150 physics - 6 dupes == 190
        assert len(records) == 190


@responses.activate
def test_list_no_records(app, sample_empty_set):
    """Check harvesting of records from multiple setspecs."""
    responses.add(
        responses.GET,
        re.compile(r'http?://export.arxiv.org/oai2.*set=physics.*'),
        body=sample_empty_set,
        content_type='text/xml'
    )

    with app.app_context():
        _, records = list_records(
            metadata_prefix='arXiv',
            from_date='2015-01-17',
            until_date='2015-01-17',
            url='http://export.arxiv.org/oai2',
            name=None,
            setspecs='physics:hep-lat'
        )
        assert not records


@responses.activate
def test_get_from_identifiers(app, sample_record_xml_oai_dc):
    """Test that getting records via identifiers work."""
    responses.add(
        responses.GET,
        'http://export.arxiv.org/oai2',
        body=sample_record_xml_oai_dc,
        content_type='text/xml'
    )
    with app.app_context():
        _, records = get_records(['oai:arXiv.org:1507.03011'],
                                 url='http://export.arxiv.org/oai2')
        for rec in records:
            identifier_in_request = rec.xml.xpath(
                "//dc:identifier",
                namespaces={"dc": "http://purl.org/dc/elements/1.1/"}
            )[0].text
            assert identifier_in_request == "http://arxiv.org/abs/1507.03011"


@responses.activate
def test_get_from_identifiers_with_prefix(app, sample_record_xml):
    """Test that getting records via identifiers work with prefix."""
    responses.add(
        responses.GET,
        'http://export.arxiv.org/oai2',
        body=sample_record_xml,
        content_type='text/xml'
    )
    with app.app_context():
        _, records = get_records(['oai:arXiv.org:1507.03011'],
                                 metadata_prefix="arXiv",
                                 url='http://export.arxiv.org/oai2')
        for rec in records:
            identifier_in_request = rec.xml.xpath(
                "//arXiv:id",
                namespaces={"arXiv": "http://arxiv.org/OAI/arXiv/"}
            )[0].text
            assert identifier_in_request == "1507.03011"
