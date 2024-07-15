# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""DataCite serializer tests."""

from __future__ import absolute_import, print_function

import pytest
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from marshmallow import Schema, fields

from invenio_records_rest.serializers.datacite import DataCite31Serializer, \
    DataCite40Serializer, DataCite41Serializer, OAIDataCiteSerializer


class DOISchema(Schema):
    """Test schema."""

    identifierType = fields.Constant('DOI')
    identifier = fields.Raw(attribute='doi')


class SimpleSchema(Schema):
    """Test schema."""

    identifier = fields.Nested(DOISchema, attribute='metadata')


# .tox/c1/bin/pytest --cov=invenio_records_rest tests/test_serializer_datacite.py::test_serialize -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-records-rest/.tox/c1/tmp
@pytest.mark.parametrize('serializer', [DataCite31Serializer,
                                        DataCite40Serializer,
                                        DataCite41Serializer])
def test_serialize(serializer, item_type):
    pid = PersistentIdentifier(pid_type='recid', pid_value='2')
    record = Record({'doi': '10.1234/foo', 'item_type_id': '15'})
    s = serializer(SimpleSchema)
    data = s.serialize(pid, record)

    assert """<identifier identifierType="DOI">10.1234/foo</identifier>""" \
        in data

    tree = s.serialize_oaipmh(
        pid, {'_source': record})
    assert len(tree.xpath('/resource/identifier')) == 1

    tree = OAIDataCiteSerializer(serializer=s,
                                 datacentre='CERN').serialize_oaipmh(
        pid,
        {'_source': record})
    assert len(tree.xpath('/oai_datacite/datacentreSymbol')) == 1


@pytest.mark.parametrize('serializer', [DataCite31Serializer,
                                        DataCite40Serializer,
                                        DataCite41Serializer])
def test_serialize_search(serializer):
    """Test JSON serialize."""
    def fetcher(obj_uuid, data):
        assert obj_uuid in ['a', 'b']
        return PersistentIdentifier(pid_type='doi', pid_value=data['doi'])

    s = serializer(SimpleSchema)
    data = s.serialize_search(
        fetcher,
        dict(
            hits=dict(
                hits=[
                    {'_source': dict(doi='10.1234/a'), '_id': 'a',
                     '_version': 1},
                    {'_source': dict(doi='10.1234/b'), '_id': 'b',
                     '_version': 1},
                ],
                total=2,
            ),
            aggregations={},
        )
    )
    assert """<identifier identifierType="DOI">10.1234/a</identifier>""" \
        in data
    assert """<identifier identifierType="DOI">10.1234/b</identifier>""" \
        in data

    tree = s.serialize_oaipmh(
        PersistentIdentifier(pid_type='doi', pid_value='10.1234/b'),
        {'_source': dict(doi='10.1234/b'), '_id': 'b', '_version': 1})
    assert len(tree.xpath('/resource/identifier')) == 1

    tree = OAIDataCiteSerializer(serializer=s,
                                 datacentre='CERN').serialize_oaipmh(
        PersistentIdentifier(pid_type='doi', pid_value='10.1234/b'),
        {'_source': dict(doi='10.1234/b'), '_id': 'b', '_version': 1})
    assert len(tree.xpath('/oai_datacite/datacentreSymbol')) == 1
