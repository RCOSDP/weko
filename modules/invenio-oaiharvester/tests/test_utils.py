# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015, 2016 CERN.
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

"""Test for utilities used by OAI harvester."""

import os

from mock import MagicMock, PropertyMock

from invenio_oaiharvester.utils import check_or_create_dir, create_file_name, \
    get_identifier_names, identifier_extraction_from_string, \
    record_extraction_from_file, record_extraction_from_string, write_to_dir


def test_identifier_extraction(app):
    """Test extracting identifier from OAI XML."""
    with app.app_context():
        xml_sample = ("<record><test></test>"
                      "<identifier>identifier1</identifier></record>")
        result = identifier_extraction_from_string(
            xml_sample, oai_namespace=""
        )

        assert result == "identifier1"


def test_identifier_extraction_with_namespace(app):
    """Test extracting identifier from OAI XML."""
    with app.app_context():
        xml_sample = ("<OAI-PMH xmlns='http://www.openarchives.org/OAI/2.0/'>"
                      "<record><test></test>"
                      "<identifier>identifier1</identifier></record>"
                      "</OAI-PMH>")
        result = identifier_extraction_from_string(xml_sample)

        assert result == "identifier1"


def test_records_extraction_without_namespace(app):
    """Test extracting records from OAI XML without a namespace."""
    with app.app_context():
        raw_xml = open(os.path.join(
            os.path.dirname(__file__),
            "data/sample_arxiv_response_no_namespace.xml"
        )).read()
        result = len(record_extraction_from_string(raw_xml, oai_namespace=""))
        assert result == 1


def test_records_extraction_with_namespace_getrecord(app):
    """Test extracting records from OAI XML with GetRecord."""
    with app.app_context():
        raw_xml = open(os.path.join(
            os.path.dirname(__file__),
            "data/sample_arxiv_response_with_namespace.xml"
        )).read()
        assert len(record_extraction_from_string(raw_xml)) == 1


def test_records_extraction_with_namespace_listrecords(app):
    """Test extracting records from OAI XML with ListRecords."""
    with app.app_context():
        raw_xml = open(os.path.join(
            os.path.dirname(__file__),
            "data/sample_inspire_response_listrecords.xml"
        )).read()
        assert len(record_extraction_from_string(raw_xml)) == 2


def test_records_extraction_from_file(app):
    """Test extracting records from OAI XML."""
    with app.app_context():
        path_tmp = os.path.join(
            os.path.dirname(__file__),
            "data/sample_arxiv_response_with_namespace.xml"
        )
        assert len(record_extraction_from_file(path_tmp)) == 1


def test_identifier_filter():
    """oaiharvest - testing identifier filter."""
    sample = "oai:mysite.com:1234"
    assert get_identifier_names(sample) == ["oai:mysite.com:1234"]

    sample = "oai:mysite.com:1234, oai:example.com:2134"
    expected = ["oai:mysite.com:1234", "oai:example.com:2134"]
    assert get_identifier_names(sample) == expected

    sample = "oai:mysite.com:1234/testing, oai:example.com:record/1234"
    expected = ["oai:mysite.com:1234/testing", "oai:example.com:record/1234"]
    assert get_identifier_names(sample) == expected

    assert get_identifier_names([]) == []
    assert get_identifier_names(None) == []


def test_check_or_create_dir(app, tmpdir):
    """oaiharvest - testing dir creation."""
    with app.app_context():
        check_or_create_dir(app.instance_path)
        check_or_create_dir(tmpdir.dirname + 'foo')


def test_write_to_dir(app, tmpdir):
    """oaiharvest - testing dir creation."""
    mock_record = MagicMock()
    prop_mock = PropertyMock(return_value="foo")
    type(mock_record).raw = prop_mock

    mock_record_2 = MagicMock()
    prop_mock = PropertyMock(return_value="bar")
    type(mock_record_2).raw = prop_mock
    with app.app_context():
        files, total = write_to_dir([mock_record], tmpdir.dirname)
        assert len(files) == 1
        assert total == 1

        files, total = write_to_dir(
            [mock_record, mock_record_2], tmpdir.dirname, max_records=1
        )
        assert len(files) == 2
        assert total == 2

        for file_name in files:
            with open(file_name) as f:
                content = f.read()
            assert content.startswith('<ListRecords>')
            assert content.endswith('</ListRecords>')

        files, total = write_to_dir([], tmpdir.dirname, max_records=1)
        assert len(files) == 0
        assert total == 0


def test_create_file_name(tmpdir):
    """oaiharvest - testing dir creation."""
    create_file_name(tmpdir.dirname + 'foo')
