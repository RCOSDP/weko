# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test OAI verbs."""

from __future__ import absolute_import

import pytest
from mock import patch
import uuid
from copy import deepcopy
from datetime import datetime
from marshmallow import ValidationError, Schema, fields
from lxml import etree

from invenio_pidstore.minters import recid_minter
from invenio_records.api import Record

from invenio_oaiserver import current_oaiserver
from invenio_oaiserver.minters import oaiid_minter
from invenio_oaiserver.models import OAISet
from invenio_oaiserver.response import NS_DC, NS_OAIDC, NS_OAIPMH
from invenio_oaiserver.utils import eprints_description, friends_description, oai_identifier_description

from invenio_oaiserver.verbs import (
    validate_metadata_prefix,
    validate_duplicate_argument,
    DateTime,
    OAISchema
)

import builtins

real_import = builtins.__import__

NAMESPACES = {'x': NS_OAIPMH, 'y': NS_OAIDC, 'z': NS_DC}


def _xpath_errors(body):
    """Find errors in body."""
    return list(body.iter('{*}error'))

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_verbs.py::test_no_verb -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_no_verb(app):
    """Test response when no verb is specified."""
    with app.test_client() as c:
        result = c.get('/oai')
        tree = etree.fromstring(result.data)
        assert 'Missing data for required field "verb".' in _xpath_errors(
            tree)[0].text


def test_wrong_verb(app):
    """Test wrong verb."""
    with app.test_client() as c:
        result = c.get('/oai?verb=Aaa')
        tree = etree.fromstring(result.data)

        assert 'This is not a valid OAI-PMH verb:Aaa' in _xpath_errors(
            tree)[0].text

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_verbs.py::test_identify -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_identify(app, db, identify):
    """Test Identify verb."""
    # baseUrls for friends element
    baseUrls = ['http://example.org/1',
                'http://example.org/2']
    # parameters for eprints element
    content = {'URL': 'http://arXiv.org/arXiv_content.htm'}
    metadataPolicy = {'text': 'Metadata can be used by commercial'
                      'and non-commercial service providers',
                      'URL': 'http://arXiv.org/arXiv_metadata_use.htm'}
    dataPolicy = {'text': 'Full content, i.e. preprints may'
                  'not be harvested by robots'}
    submissionPolicy = {'URL': 'http://arXiv.org/arXiv_submission.htm'}
    # parameters for oai-identifier element
    scheme = 'oai'
    repositoryIdentifier = 'oai-stuff.foo.org'
    delimiter = ':'
    sampleIdentifier = 'oai:oai-stuff.foo.org:5324'

    app.config['OAISERVER_DESCRIPTIONS'] = \
        [friends_description(baseUrls),
         eprints_description(metadataPolicy, dataPolicy,
                             submissionPolicy, content),
         oai_identifier_description(scheme, repositoryIdentifier, delimiter,
                                    sampleIdentifier)]

    with app.test_client() as c:
        result = c.get('/oai?verb=Identify')
        assert 200 == result.status_code

        tree = etree.fromstring(result.data)

        assert len(tree.xpath('/x:OAI-PMH', namespaces=NAMESPACES)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:Identify',
                              namespaces=NAMESPACES)) == 1
        repository_name = tree.xpath('/x:OAI-PMH/x:Identify/x:repositoryName',
                                     namespaces=NAMESPACES)
        assert len(repository_name) == 1
        #assert repository_name[0].text == 'Invenio-OAIServer'
        assert repository_name[0].text == 'test_repository'
        base_url = tree.xpath('/x:OAI-PMH/x:Identify/x:baseURL',
                              namespaces=NAMESPACES)
        assert len(base_url) == 1
        assert base_url[0].text == 'http://app/oai'
        protocolVersion = tree.xpath(
            '/x:OAI-PMH/x:Identify/x:protocolVersion',
            namespaces=NAMESPACES)
        assert len(protocolVersion) == 1
        assert protocolVersion[0].text == '2.0'
        adminEmail = tree.xpath('/x:OAI-PMH/x:Identify/x:adminEmail',
                                namespaces=NAMESPACES)
        assert len(adminEmail) == 1
        #assert adminEmail[0].text == 'info@inveniosoftware.org'
        assert adminEmail[0].text == "test@test.org"
        earliestDatestamp = tree.xpath(
            '/x:OAI-PMH/x:Identify/x:earliestDatestamp',
            namespaces=NAMESPACES)
        assert len(earliestDatestamp) == 1
        deletedRecord = tree.xpath('/x:OAI-PMH/x:Identify/x:deletedRecord',
                                   namespaces=NAMESPACES)
        assert len(deletedRecord) == 1
        #assert deletedRecord[0].text == 'no'
        assert deletedRecord[0].text == 'transient'
        granularity = tree.xpath('/x:OAI-PMH/x:Identify/x:granularity',
                                 namespaces=NAMESPACES)
        assert len(granularity) == 1
        description = tree.xpath('/x:OAI-PMH/x:Identify/x:description',
                                 namespaces=NAMESPACES)

        friends_element = description[0]
        for element in friends_element.getchildren():
            for child in element.getchildren():
                assert child.tag == \
                    '{http://www.openarchives.org/OAI/2.0/friends/}baseURL'
                assert child.text in baseUrls

        eprints_root = description[1]
        children = eprints_root[0].getchildren()
        assert children[0].tag == \
            '{http://www.openarchives.org/OAI/2.0/eprints}content'
        leaves = children[0].getchildren()
        assert len(leaves) == 1
        assert leaves[0].tag == \
            '{http://www.openarchives.org/OAI/2.0/eprints}URL'
        assert leaves[0].text == content['URL']

        assert children[1].tag == \
            '{http://www.openarchives.org/OAI/2.0/eprints}metadataPolicy'
        leaves = children[1].getchildren()
        assert len(leaves) == 2
        metadataPolicyContents = \
            ['{http://www.openarchives.org/OAI/2.0/eprints}text',
             '{http://www.openarchives.org/OAI/2.0/eprints}URL']
        assert set([leaves[0].tag, leaves[1].tag]) == \
            set(metadataPolicyContents)
        assert set([leaves[0].text, leaves[1].text]) == \
            set(metadataPolicy.values())
        assert children[2].tag == \
            '{http://www.openarchives.org/OAI/2.0/eprints}dataPolicy'
        leaves = children[2].getchildren()
        assert len(leaves) == 1
        assert leaves[0].tag == \
            '{http://www.openarchives.org/OAI/2.0/eprints}text'
        assert leaves[0].text == dataPolicy['text']

        assert children[3].tag == \
            '{http://www.openarchives.org/OAI/2.0/eprints}submissionPolicy'
        leaves = children[3].getchildren()
        assert len(leaves) == 1
        assert leaves[0].tag == \
            '{http://www.openarchives.org/OAI/2.0/eprints}URL'
        assert leaves[0].text == submissionPolicy['URL']

        oai_identifier_root = description[2]
        children = oai_identifier_root[0].getchildren()
        assert children[0].tag == \
            '{http://www.openarchives.org/OAI/2.0/oai-identifier}scheme'
        assert children[0].text == scheme
        assert children[1].tag == \
            '{http://www.openarchives.org/OAI/2.0/oai-identifier}' + \
            'repositoryIdentifier'
        assert children[1].text == repositoryIdentifier
        assert children[2].tag == \
            '{http://www.openarchives.org/OAI/2.0/oai-identifier}' + \
            'delimiter'
        assert children[2].text == delimiter
        assert children[3].tag == \
            '{http://www.openarchives.org/OAI/2.0/oai-identifier}' + \
            'sampleIdentifier'
        assert children[3].text == sampleIdentifier

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_verbs.py::test_getrecord_fail -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_getrecord_fail(es_app, db,identify):
    """Test GetRecord if record doesn't exist."""
    with es_app.test_request_context():
        with es_app.test_client() as c:
            result = c.get(
                '/oai?verb=GetRecord&identifier={0}&metadataPrefix=jpcoar_1.0'
                .format('not-exist-pid'))
            assert 422 == result.status_code

            tree = etree.fromstring(result.data)

            _check_xml_error(tree, code='idDoesNotExist')


def _check_xml_error(tree, code):
    """Text xml for a error idDoesNotExist."""
    assert len(tree.xpath('/x:OAI-PMH', namespaces=NAMESPACES)) == 1
    error = tree.xpath('/x:OAI-PMH/x:error', namespaces=NAMESPACES)
    assert len(error) == 1
    assert error[0].attrib['code'] == code


def test_identify_with_additional_args(app):
    """Test identify with additional arguments."""
    with app.test_client() as c:
        result = c.get('/oai?verb=Identify&notAValidArg=True')
        tree = etree.fromstring(result.data)
        assert 'You have passed too many arguments.' == _xpath_errors(
            tree)[0].text


def test_listmetadataformats(app):
    """Test ListMetadataFormats."""
    _listmetadataformats(app=app, query='/oai?verb=ListMetadataFormats')


def test_listmetadataformats_record(es_app, db):
    """Test ListMetadataFormats for a record."""
    with es_app.test_request_context():
        with db.session.begin_nested():
            record_id = uuid.uuid4()
            data = {'title_statement': {'title': 'Test0'}}
            recid_minter(record_id, data)
            pid = oaiid_minter(record_id, data)
            Record.create(data, id_=record_id)
            pid_value = pid.pid_value

        db.session.commit()

    _listmetadataformats(
        app=es_app,
        query='/oai?verb=ListMetadataFormats&identifier={0}'.format(
            pid_value))


def test_listmetadataformats_record_fail(app, db):
    """Test ListMetadataFormats for a record that doesn't exist."""
    query = '/oai?verb=ListMetadataFormats&identifier={0}'.format(
            'pid-not-exixts')
    with app.test_request_context():
        with app.test_client() as c:
            result = c.get(query)

        tree = etree.fromstring(result.data)

        _check_xml_error(tree, code='idDoesNotExist')


def _listmetadataformats(app, query):
    """Try ListMetadataFormats."""
    with app.test_request_context():
        with app.test_client() as c:
            result = c.get(query)

        tree = etree.fromstring(result.data)

        assert len(tree.xpath('/x:OAI-PMH', namespaces=NAMESPACES)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:ListMetadataFormats',
                              namespaces=NAMESPACES)) == 1
        metadataFormats = tree.xpath(
            '/x:OAI-PMH/x:ListMetadataFormats/x:metadataFormat',
            namespaces=NAMESPACES)
        cfg_metadataFormats = deepcopy(
            app.config.get('OAISERVER_METADATA_FORMATS', {}))
        assert len(metadataFormats) == len(cfg_metadataFormats)

        prefixes = tree.xpath(
            '/x:OAI-PMH/x:ListMetadataFormats/x:metadataFormat/'
            'x:metadataPrefix', namespaces=NAMESPACES)
        assert len(prefixes) == len(cfg_metadataFormats)
        assert all(pfx.text in cfg_metadataFormats for pfx in prefixes)

        schemas = tree.xpath(
            '/x:OAI-PMH/x:ListMetadataFormats/x:metadataFormat/'
            'x:schema', namespaces=NAMESPACES)
        assert len(schemas) == len(cfg_metadataFormats)
        assert all(sch.text in cfg_metadataFormats[pfx.text]['schema']
                   for sch, pfx in zip(schemas, prefixes))

        metadataNamespaces = tree.xpath(
            '/x:OAI-PMH/x:ListMetadataFormats/x:metadataFormat/'
            'x:metadataNamespace', namespaces=NAMESPACES)
        assert len(metadataNamespaces) == len(cfg_metadataFormats)
        assert all(nsp.text in cfg_metadataFormats[pfx.text]['namespace']
                   for nsp, pfx in zip(metadataNamespaces, prefixes))


def test_listsets(app, db):
    """Test ListSets."""
    with app.test_request_context():
        current_oaiserver.unregister_signals_oaiset()
        with db.session.begin_nested():
            a = OAISet(spec='test', name='Test', description='test desc')
            db.session.add(a)

        with app.test_client() as c:
            result = c.get('/oai?verb=ListSets')

        tree = etree.fromstring(result.data)

        assert len(tree.xpath('/x:OAI-PMH', namespaces=NAMESPACES)) == 1

        assert len(tree.xpath('/x:OAI-PMH/x:ListSets',
                              namespaces=NAMESPACES)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:ListSets/x:set',
                              namespaces=NAMESPACES)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:ListSets/x:set/x:setSpec',
                              namespaces=NAMESPACES)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:ListSets/x:set/x:setName',
                              namespaces=NAMESPACES)) == 1
        assert len(tree.xpath(
            '/x:OAI-PMH/x:ListSets/x:set/x:setDescription',
            namespaces=NAMESPACES
        )) == 1
        assert len(
            tree.xpath('/x:OAI-PMH/x:ListSets/x:set/x:setDescription/y:dc',
                       namespaces=NAMESPACES)
        ) == 1
        assert len(
            tree.xpath('/x:OAI-PMH/x:ListSets/x:set/x:setDescription/y:dc/'
                       'z:description', namespaces=NAMESPACES)
        ) == 1
        text = tree.xpath(
            '/x:OAI-PMH/x:ListSets/x:set/x:setDescription/y:dc/'
            'z:description/text()', namespaces=NAMESPACES)
        assert len(text) == 1
        assert text[0] == 'test desc'


def test_fail_missing_metadataPrefix(app):
    """Test ListRecords fail missing metadataPrefix."""
    queries = [
        '/oai?verb=ListRecords',
        '/oai?verb=GetRecord&identifier=123',
        '/oai?verb=ListIdentifiers'
    ]
    for query in queries:
        with app.test_request_context():
            with app.test_client() as c:
                result = c.get(query)

            tree = etree.fromstring(result.data)

            _check_xml_error(tree, code='badArgument')

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_verbs.py::test_fail_not_exist_metadataPrefix -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_fail_not_exist_metadataPrefix(app):
    """Test ListRecords fail not exist metadataPrefix."""
    queries = [
        '/oai?verb=ListRecords&metadataPrefix=not-exist',
        '/oai?verb=GetRecord&identifier=123&metadataPrefix=not-exist',
        '/oai?verb=ListIdentifiers&metadataPrefix=not-exist'
    ]
    for query in queries:
        with app.test_request_context():
            with app.test_client() as c:
                result = c.get(query)

            tree = etree.fromstring(result.data)
            _check_xml_error(tree, code='cannotDisseminateFormat')


def test_listrecords_fail_missing_metadataPrefix(app):
    """Test ListRecords fail missing metadataPrefix."""
    query = '/oai?verb=ListRecords&'
    with app.test_request_context():
        with app.test_client() as c:
            result = c.get(query)

        tree = etree.fromstring(result.data)

        _check_xml_error(tree, code='badArgument')


def test_list_sets_with_resumption_token_and_other_args(app):
    """Test list sets with resumption tokens."""
    pass

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_verbs.py::test_validate_metadata_prefix -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_validate_metadata_prefix(app, mocker):
    oai_metadata_formats = {
        "oai_dc": {
            "serializer": ("invenio_oaiserver.utils:dumps_etree", {"xslt_filename": "/code/modules/invenio-oaiserver/invenio_oaiserver/static/xsl/MARC21slim2OAIDC.xsl"}), 
            "schema": "http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd", 
            "namespace": "http://www.w3.org/2001/XMLSchema"
        }, 
        "marc21": {
            "serializer": ("invenio_oaiserver.utils:dumps_etree", {"prefix": "marc"}),
            "schema": "http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd", 
            "namespace": "http://www.loc.gov/MARC21/slim"
        }, 
        "ddi": {
            "namespace": "ddi:codebook:2_5", 
            "schema": "https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd", 
            "serializer": ("invenio_oaiserver.utils:dumps_etree", {"schema_type": "ddi"})
        }, 
        "jpcoar_v1": {
            "namespace": "https://github.com/JPCOAR/schema/blob/master/1.0/", 
            "schema": "https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd", 
            "serializer": ("invenio_oaiserver.utils:dumps_etree", {"schema_type": "jpcoar_v1"})
        }, 
        "jpcoar": {
            "namespace": "https://github.com/JPCOAR/schema/blob/master/2.0/", 
            "schema": "https://github.com/JPCOAR/schema/blob/master/2.0/jpcoar_scm.xsd", 
            "serializer": ("invenio_oaiserver.utils:dumps_etree", {"schema_type": "jpcoar"})
        }
    }
    mocker.patch("invenio_oaiserver.verbs.get_oai_metadata_formats",return_value=oai_metadata_formats)
    
    validate_metadata_prefix("jpcoar")
    
    with pytest.raises(ValidationError) as e:
        validate_metadata_prefix("not_oai")
    error = e.value
    assert error.messages == {'cannotDisseminateFormat':['The metadataPrefix "not_oai" is not supported by this repository.']}
    assert error.field_names == ["metadataPrefix"]

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_verbs.py::test_validate_duplicate_argument -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_validate_duplicate_argument(app):
    url = "/test?test_field1=test_value1"
    with app.test_request_context(url):
        validate_duplicate_argument("test_field1")
    
    url = "/test?test_field1=test_value1&test_field1=test_value2"
    with app.test_request_context(url):
        with pytest.raises(ValidationError) as e:
            validate_duplicate_argument("test_field1")
    error = e.value
    assert error.messages == ['Illegal duplicate of argument "test_field1".']
    assert error.field_names == ["test_field1"]
    
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_verbs.py::test_DateTime_from_iso_permissive -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_DateTime_from_iso_permissive():
    class TestScheme(Schema):
        date = DateTime(format="permissive")
    result = TestScheme().load({"date":"2023-02-10T12:01:10"})
    
    assert result.data["date"].strftime("%Y-%m-%dT%H:%M:%S") == "2023-02-10T12:01:10"
    assert result.errors == {}
    def mock_import(name,globals=None, locals=None,fromlist=(),level=0):
        if name in ("dateutil"):
            raise ImportError("test_error")
        return real_import(name,globals=globals,locals=locals,fromlist=fromlist,level=level)
    with patch('builtins.__import__', side_effect=mock_import):
        class TestScheme(Schema):
            date = DateTime(format="permissive")
        result = TestScheme().load({"date":"2023-02-10T12:01:10"})
        assert result.data["date"].strftime("%Y-%m-%dT%H:%M:%S") == "2023-02-10T12:01:10"
        assert result.errors == {}


# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_verbs.py::test_OAIScheme_validate -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_OAIScheme_validate(app):
    class TestSchema(OAISchema):
            name= fields.Str()
    url = "/test?test_field=test_value"
    with app.test_request_context(url):
        data = {"verb":"OAISchema"}
        with pytest.raises(ValidationError) as e:
            TestSchema().validate(data)
        error = e.value
        assert error.messages == ["This is not a valid OAI-PMH verb:OAISchema"]
        assert error.field_names == ["verb"]
        
        data = {"from_":"2023-01-01","until":"2022-01-01"}
        with pytest.raises(ValidationError) as e:
            TestSchema().validate(data)
        error = e.value
        assert error.messages == ['Date "from" must be before "until".']
        
        # Set 'until' time to 23:59:59 when 'until' time is 00:00:00
        # You have passed too many arguments.
        data = {"until":datetime(2023,1,1)}
        with pytest.raises(ValidationError) as e:
            TestSchema().validate(data)
        error = e.value
        assert error.messages == ["You have passed too many arguments."]
    
    url = "/test?verb=test_verb&name=test_name"
    with app.test_request_context(url):
        data = {"until":"2023-01-01"}
        TestSchema().validate(data)