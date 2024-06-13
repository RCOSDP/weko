# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
# Copyright (C) 2022 RERO.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test OAI verbs."""

import uuid
from copy import deepcopy
from datetime import datetime, timedelta

from helpers import create_record, run_after_insert_oai_set
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.minters import recid_minter
from invenio_search import current_search
from lxml import etree

from invenio_oaiserver import current_oaiserver
from invenio_oaiserver.minters import oaiid_minter
from invenio_oaiserver.models import OAISet
from invenio_oaiserver.proxies import current_oaiserver
from invenio_oaiserver.response import NS_DC, NS_OAIDC, NS_OAIPMH
from invenio_oaiserver.utils import (
    datetime_to_datestamp,
    eprints_description,
    friends_description,
    oai_identifier_description,
)

NAMESPACES = {"x": NS_OAIPMH, "y": NS_OAIDC, "z": NS_DC}


def _xpath_errors(body):
    """Find errors in body."""
    return list(body.iter("{*}error"))


def test_no_verb(app):
    """Test response when no verb is specified."""
    with app.test_client() as c:
        result = c.get("/oai2d")
        tree = etree.fromstring(result.data)
        assert "Missing data for required field." in _xpath_errors(tree)[0].text


def test_wrong_verb(app):
    """Test wrong verb."""
    with app.test_client() as c:
        result = c.get("/oai2d?verb=Aaa")
        tree = etree.fromstring(result.data)

        assert "This is not a valid OAI-PMH verb:Aaa" in _xpath_errors(tree)[0].text


def test_identify(app):
    """Test Identify verb."""
    # baseUrls for friends element
    baseUrls = ["http://example.org/1", "http://example.org/2"]
    # parameters for eprints element
    content = {"URL": "http://arXiv.org/arXiv_content.htm"}
    metadataPolicy = {
        "text": "Metadata can be used by commercial"
        "and non-commercial service providers",
        "URL": "http://arXiv.org/arXiv_metadata_use.htm",
    }
    dataPolicy = {
        "text": "Full content, i.e. preprints may" "not be harvested by robots"
    }
    submissionPolicy = {"URL": "http://arXiv.org/arXiv_submission.htm"}
    # parameters for oai-identifier element
    scheme = "oai"
    repositoryIdentifier = "oai-stuff.foo.org"
    delimiter = ":"
    sampleIdentifier = "oai:oai-stuff.foo.org:5324"

    app.config["OAISERVER_DESCRIPTIONS"] = [
        friends_description(baseUrls),
        eprints_description(metadataPolicy, dataPolicy, submissionPolicy, content),
        oai_identifier_description(
            scheme, repositoryIdentifier, delimiter, sampleIdentifier
        ),
    ]

    with app.test_client() as c:
        result = c.get("/oai2d?verb=Identify")
        assert 200 == result.status_code

        tree = etree.fromstring(result.data)

        assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1
        assert len(tree.xpath("/x:OAI-PMH/x:Identify", namespaces=NAMESPACES)) == 1
        repository_name = tree.xpath(
            "/x:OAI-PMH/x:Identify/x:repositoryName", namespaces=NAMESPACES
        )
        assert len(repository_name) == 1
        assert repository_name[0].text == "Invenio-OAIServer"
        base_url = tree.xpath("/x:OAI-PMH/x:Identify/x:baseURL", namespaces=NAMESPACES)
        assert len(base_url) == 1
        assert base_url[0].text == "http://app/oai2d"
        protocolVersion = tree.xpath(
            "/x:OAI-PMH/x:Identify/x:protocolVersion", namespaces=NAMESPACES
        )
        assert len(protocolVersion) == 1
        assert protocolVersion[0].text == "2.0"
        adminEmail = tree.xpath(
            "/x:OAI-PMH/x:Identify/x:adminEmail", namespaces=NAMESPACES
        )
        assert len(adminEmail) == 1
        assert adminEmail[0].text == "info@inveniosoftware.org"
        earliestDatestamp = tree.xpath(
            "/x:OAI-PMH/x:Identify/x:earliestDatestamp", namespaces=NAMESPACES
        )
        assert len(earliestDatestamp) == 1
        deletedRecord = tree.xpath(
            "/x:OAI-PMH/x:Identify/x:deletedRecord", namespaces=NAMESPACES
        )
        assert len(deletedRecord) == 1
        assert deletedRecord[0].text == "no"
        granularity = tree.xpath(
            "/x:OAI-PMH/x:Identify/x:granularity", namespaces=NAMESPACES
        )
        assert len(granularity) == 1
        description = tree.xpath(
            "/x:OAI-PMH/x:Identify/x:description", namespaces=NAMESPACES
        )

        friends_element = description[0]
        for element in friends_element.getchildren():
            for child in element.getchildren():
                assert (
                    child.tag == "{http://www.openarchives.org/OAI/2.0/friends/}baseURL"
                )
                assert child.text in baseUrls

        eprints_root = description[1]
        children = eprints_root[0].getchildren()
        assert children[0].tag == "{http://www.openarchives.org/OAI/2.0/eprints}content"
        leaves = children[0].getchildren()
        assert len(leaves) == 1
        assert leaves[0].tag == "{http://www.openarchives.org/OAI/2.0/eprints}URL"
        assert leaves[0].text == content["URL"]

        assert (
            children[1].tag
            == "{http://www.openarchives.org/OAI/2.0/eprints}metadataPolicy"
        )
        leaves = children[1].getchildren()
        assert len(leaves) == 2
        metadataPolicyContents = [
            "{http://www.openarchives.org/OAI/2.0/eprints}text",
            "{http://www.openarchives.org/OAI/2.0/eprints}URL",
        ]
        assert set([leaves[0].tag, leaves[1].tag]) == set(metadataPolicyContents)
        assert set([leaves[0].text, leaves[1].text]) == set(metadataPolicy.values())
        assert (
            children[2].tag == "{http://www.openarchives.org/OAI/2.0/eprints}dataPolicy"
        )
        leaves = children[2].getchildren()
        assert len(leaves) == 1
        assert leaves[0].tag == "{http://www.openarchives.org/OAI/2.0/eprints}text"
        assert leaves[0].text == dataPolicy["text"]

        assert (
            children[3].tag
            == "{http://www.openarchives.org/OAI/2.0/eprints}submissionPolicy"
        )
        leaves = children[3].getchildren()
        assert len(leaves) == 1
        assert leaves[0].tag == "{http://www.openarchives.org/OAI/2.0/eprints}URL"
        assert leaves[0].text == submissionPolicy["URL"]

        oai_identifier_root = description[2]
        children = oai_identifier_root[0].getchildren()
        assert (
            children[0].tag
            == "{http://www.openarchives.org/OAI/2.0/oai-identifier}scheme"
        )
        assert children[0].text == scheme
        assert (
            children[1].tag
            == "{http://www.openarchives.org/OAI/2.0/oai-identifier}"
            + "repositoryIdentifier"
        )
        assert children[1].text == repositoryIdentifier
        assert (
            children[2].tag
            == "{http://www.openarchives.org/OAI/2.0/oai-identifier}" + "delimiter"
        )
        assert children[2].text == delimiter
        assert (
            children[3].tag
            == "{http://www.openarchives.org/OAI/2.0/oai-identifier}"
            + "sampleIdentifier"
        )
        assert children[3].text == sampleIdentifier


def test_identify_earliest_date(app, schema):
    """Test identify earliest date."""
    with app.test_client() as c:
        result = c.get("/oai2d?verb=Identify")
        assert 200 == result.status_code

        tree = etree.fromstring(result.data)
        earliestDatestamp = tree.xpath(
            "/x:OAI-PMH/x:Identify/x:earliestDatestamp", namespaces=NAMESPACES
        )
        assert earliestDatestamp[0].text == "0001-01-01T00:00:00Z"

    first_record = create_record(
        app,
        {
            "_oai": {"sets": ["a"]},
            "title_statement": {"title": "Test0"},
            "_oai_id": 1,
            "$schema": schema,
        },
    )

    first_record.model.created = datetime(2000, 1, 1, 13, 0, 0)
    RecordIndexer().index(first_record)

    create_record(
        app,
        {
            "_oai": {"sets": ["a"]},
            "title_statement": {"title": "Test1"},
            "_oai_id": 2,
            "$schema": schema,
        },
    )
    create_record(
        app,
        {
            "_oai": {"sets": ["a"]},
            "title_statement": {"title": "Test2"},
            "_oai_id": 3,
            "$schema": schema,
        },
    )
    app.extensions["invenio-search"].flush_and_refresh("records")

    with app.test_client() as c:
        result = c.get("/oai2d?verb=Identify")
        assert 200 == result.status_code

        tree = etree.fromstring(result.data)
        earliestDatestamp = tree.xpath(
            "/x:OAI-PMH/x:Identify/x:earliestDatestamp", namespaces=NAMESPACES
        )
        assert earliestDatestamp[0].text == "2000-01-01T13:00:00Z"


def test_getrecord(app):
    """Test get record verb."""
    with app.test_request_context():
        pid_value = "oai:legacy:1"
        with db.session.begin_nested():
            record_id = uuid.uuid4()
            data = {
                "_oai": {"id": pid_value},
                "title_statement": {"title": "Test0"},
            }
            pid = oaiid_minter(record_id, data)
            record = current_oaiserver.record_cls.create(data, id_=record_id)

        db.session.commit()
        assert pid_value == pid.pid_value
        record_updated = record.updated
        with app.test_client() as c:
            result = c.get(
                "/oai2d?verb=GetRecord&identifier={0}&metadataPrefix=oai_dc".format(
                    pid_value
                )
            )
            assert 200 == result.status_code

            tree = etree.fromstring(result.data)

            assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1
            assert len(tree.xpath("/x:OAI-PMH/x:GetRecord", namespaces=NAMESPACES)) == 1
            assert (
                len(
                    tree.xpath(
                        "/x:OAI-PMH/x:GetRecord/x:record/x:header",
                        namespaces=NAMESPACES,
                    )
                )
                == 1
            )
            assert (
                len(
                    tree.xpath(
                        "/x:OAI-PMH/x:GetRecord/x:record/x:header/x:identifier",
                        namespaces=NAMESPACES,
                    )
                )
                == 1
            )
            identifier = tree.xpath(
                "/x:OAI-PMH/x:GetRecord/x:record/x:header/x:identifier/text()",
                namespaces=NAMESPACES,
            )
            assert identifier == [pid_value]
            datestamp = tree.xpath(
                "/x:OAI-PMH/x:GetRecord/x:record/x:header/x:datestamp/text()",
                namespaces=NAMESPACES,
            )
            assert datestamp == [datetime_to_datestamp(record_updated)]
            assert (
                len(
                    tree.xpath(
                        "/x:OAI-PMH/x:GetRecord/x:record/x:metadata",
                        namespaces=NAMESPACES,
                    )
                )
                == 1
            )


def test_getrecord_fail(app):
    """Test GetRecord if record doesn't exist."""
    with app.test_request_context():
        with app.test_client() as c:
            result = c.get(
                "/oai2d?verb=GetRecord&identifier={0}&metadataPrefix=oai_dc".format(
                    "not-exist-pid"
                )
            )
            assert 422 == result.status_code

            tree = etree.fromstring(result.data)

            _check_xml_error(tree, code="idDoesNotExist")


def _check_xml_error(tree, code):
    """Text xml for a error idDoesNotExist."""
    assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1
    error = tree.xpath("/x:OAI-PMH/x:error", namespaces=NAMESPACES)
    assert len(error) == 1
    assert error[0].attrib["code"] == code


def test_identify_with_additional_args(app):
    """Test identify with additional arguments."""
    with app.test_client() as c:
        result = c.get("/oai2d?verb=Identify&notAValidArg=True")
        tree = etree.fromstring(result.data)
        assert "You have passed too many arguments." == _xpath_errors(tree)[0].text


def test_listmetadataformats(app):
    """Test ListMetadataFormats."""
    _listmetadataformats(app=app, query="/oai2d?verb=ListMetadataFormats")


def test_listmetadataformats_record(app):
    """Test ListMetadataFormats for a record."""
    with app.test_request_context():
        with db.session.begin_nested():
            record_id = uuid.uuid4()
            data = {"title_statement": {"title": "Test0"}}
            recid_minter(record_id, data)
            pid = oaiid_minter(record_id, data)
            current_oaiserver.record_cls.create(data, id_=record_id)
            pid_value = pid.pid_value

        db.session.commit()

    _listmetadataformats(
        app=app,
        query="/oai2d?verb=ListMetadataFormats&identifier={0}".format(pid_value),
    )


def test_listmetadataformats_record_fail(app):
    """Test ListMetadataFormats for a record that doesn't exist."""
    query = "/oai2d?verb=ListMetadataFormats&identifier={0}".format("pid-not-exixts")
    with app.test_request_context():
        with app.test_client() as c:
            result = c.get(query)

        tree = etree.fromstring(result.data)

        _check_xml_error(tree, code="idDoesNotExist")


def _listmetadataformats(app, query):
    """Try ListMetadataFormats."""
    with app.test_request_context():
        with app.test_client() as c:
            result = c.get(query)

        tree = etree.fromstring(result.data)

        assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1
        assert (
            len(tree.xpath("/x:OAI-PMH/x:ListMetadataFormats", namespaces=NAMESPACES))
            == 1
        )
        metadataFormats = tree.xpath(
            "/x:OAI-PMH/x:ListMetadataFormats/x:metadataFormat", namespaces=NAMESPACES
        )
        cfg_metadataFormats = deepcopy(app.config.get("OAISERVER_METADATA_FORMATS", {}))
        assert len(metadataFormats) == len(cfg_metadataFormats)

        prefixes = tree.xpath(
            "/x:OAI-PMH/x:ListMetadataFormats/x:metadataFormat/" "x:metadataPrefix",
            namespaces=NAMESPACES,
        )
        assert len(prefixes) == len(cfg_metadataFormats)
        assert all(pfx.text in cfg_metadataFormats for pfx in prefixes)

        schemas = tree.xpath(
            "/x:OAI-PMH/x:ListMetadataFormats/x:metadataFormat/" "x:schema",
            namespaces=NAMESPACES,
        )
        assert len(schemas) == len(cfg_metadataFormats)
        assert all(
            sch.text in cfg_metadataFormats[pfx.text]["schema"]
            for sch, pfx in zip(schemas, prefixes)
        )

        metadataNamespaces = tree.xpath(
            "/x:OAI-PMH/x:ListMetadataFormats/x:metadataFormat/" "x:metadataNamespace",
            namespaces=NAMESPACES,
        )
        assert len(metadataNamespaces) == len(cfg_metadataFormats)
        assert all(
            nsp.text in cfg_metadataFormats[pfx.text]["namespace"]
            for nsp, pfx in zip(metadataNamespaces, prefixes)
        )


def test_listsets(app):
    """Test ListSets."""
    with app.test_request_context():
        current_oaiserver.unregister_signals_oaiset()
        with db.session.begin_nested():
            a = OAISet(
                spec="test", name="Test", description="test desc", system_created=False
            )
            db.session.add(a)

        with app.test_client() as c:
            result = c.get("/oai2d?verb=ListSets")

        tree = etree.fromstring(result.data)

        assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1

        assert len(tree.xpath("/x:OAI-PMH/x:ListSets", namespaces=NAMESPACES)) == 1
        assert (
            len(tree.xpath("/x:OAI-PMH/x:ListSets/x:set", namespaces=NAMESPACES)) == 1
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListSets/x:set/x:setSpec", namespaces=NAMESPACES
                )
            )
            == 1
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListSets/x:set/x:setName", namespaces=NAMESPACES
                )
            )
            == 1
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListSets/x:set/x:setDescription",
                    namespaces=NAMESPACES,
                )
            )
            == 1
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListSets/x:set/x:setDescription/y:dc",
                    namespaces=NAMESPACES,
                )
            )
            == 1
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListSets/x:set/x:setDescription/y:dc/"
                    "z:description",
                    namespaces=NAMESPACES,
                )
            )
            == 1
        )
        text = tree.xpath(
            "/x:OAI-PMH/x:ListSets/x:set/x:setDescription/y:dc/" "z:description/text()",
            namespaces=NAMESPACES,
        )
        assert len(text) == 1
        assert text[0] == "test desc"


def test_listsets_invalid_name(app):
    """Test ListSets with invalid unicode character for XML."""
    with app.test_request_context():
        current_oaiserver.unregister_signals_oaiset()
        with db.session.begin_nested():
            a = OAISet(
                spec="test",
                name="uni\x01co\x0bde",
                description="uni\x01co\x0bde",
                system_created=False,
            )
            db.session.add(a)

        with app.test_client() as c:
            result = c.get("/oai2d?verb=ListSets")

        tree = etree.fromstring(result.data)

        assert (
            tree.xpath("/x:OAI-PMH/x:ListSets/x:set/x:setName", namespaces=NAMESPACES)[
                0
            ].text
            == "unicode"
        )
        assert (
            tree.xpath(
                "/x:OAI-PMH/x:ListSets/x:set/x:setDescription/y:dc/z:description",
                namespaces=NAMESPACES,
            )[0].text
            == "unicode"
        )


def test_fail_missing_metadataPrefix(app):
    """Test ListRecords fail missing metadataPrefix."""
    queries = [
        "/oai2d?verb=ListRecords",
        "/oai2d?verb=GetRecord&identifier=123",
        "/oai2d?verb=ListIdentifiers",
    ]
    for query in queries:
        with app.test_request_context():
            with app.test_client() as c:
                result = c.get(query)

            tree = etree.fromstring(result.data)

            _check_xml_error(tree, code="badArgument")


def test_fail_not_exist_metadataPrefix(app):
    """Test ListRecords fail not exist metadataPrefix."""
    queries = [
        "/oai2d?verb=ListRecords&metadataPrefix=not-exist",
        "/oai2d?verb=GetRecord&identifier=123&metadataPrefix=not-exist",
        "/oai2d?verb=ListIdentifiers&metadataPrefix=not-exist",
    ]
    for query in queries:
        with app.test_request_context():
            with app.test_client() as c:
                result = c.get(query)

            tree = etree.fromstring(result.data)

            _check_xml_error(tree, code="badArgument")


def test_listrecords_fail_missing_metadataPrefix(app):
    """Test ListRecords fail missing metadataPrefix."""
    query = "/oai2d?verb=ListRecords&"
    with app.test_request_context():
        with app.test_client() as c:
            result = c.get(query)

        tree = etree.fromstring(result.data)

        _check_xml_error(tree, code="badArgument")


def test_listrecords(app):
    """Test ListRecords."""
    total = 32
    record_ids = []

    with app.test_request_context():
        indexer = RecordIndexer()

        with db.session.begin_nested():
            for idx in range(total):
                record_id = uuid.uuid4()
                data = {"title_statement": {"title": "Test{0}".format(idx)}}
                recid_minter(record_id, data)
                oaiid_minter(record_id, data)
                record = current_oaiserver.record_cls.create(data, id_=record_id)
                record_ids.append(record_id)

        db.session.commit()

        for record_id in record_ids:
            indexer.index_by_id(record_id)

        current_search.flush_and_refresh("_all")

        with app.test_client() as c:
            result = c.get("/oai2d?verb=ListRecords&metadataPrefix=oai_dc")

        tree = etree.fromstring(result.data)

        assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1

        assert len(tree.xpath("/x:OAI-PMH/x:ListRecords", namespaces=NAMESPACES)) == 1
        assert (
            len(tree.xpath("/x:OAI-PMH/x:ListRecords/x:record", namespaces=NAMESPACES))
            == 10
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header", namespaces=NAMESPACES
                )
            )
            == 10
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header" "/x:identifier",
                    namespaces=NAMESPACES,
                )
            )
            == 10
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header" "/x:datestamp",
                    namespaces=NAMESPACES,
                )
            )
            == 10
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:metadata",
                    namespaces=NAMESPACES,
                )
            )
            == 10
        )

        # First resumption token
        resumption_token = tree.xpath(
            "/x:OAI-PMH/x:ListRecords/x:resumptionToken", namespaces=NAMESPACES
        )[0]
        assert resumption_token.text
        # Get data for resumption token
        with app.test_client() as c:
            result = c.get(
                "/oai2d?verb=ListRecords&resumptionToken={0}".format(
                    resumption_token.text
                )
            )

        tree = etree.fromstring(result.data)
        assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1
        assert len(tree.xpath("/x:OAI-PMH/x:ListRecords", namespaces=NAMESPACES)) == 1
        assert (
            len(tree.xpath("/x:OAI-PMH/x:ListRecords/x:record", namespaces=NAMESPACES))
            == 10
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header", namespaces=NAMESPACES
                )
            )
            == 10
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header" "/x:identifier",
                    namespaces=NAMESPACES,
                )
            )
            == 10
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header" "/x:datestamp",
                    namespaces=NAMESPACES,
                )
            )
            == 10
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:metadata",
                    namespaces=NAMESPACES,
                )
            )
            == 10
        )

        # Second resumption token
        resumption_token = tree.xpath(
            "/x:OAI-PMH/x:ListRecords/x:resumptionToken", namespaces=NAMESPACES
        )[0]
        assert resumption_token.text
        # Get data for resumption token
        with app.test_client() as c:
            result = c.get(
                "/oai2d?verb=ListRecords&resumptionToken={0}".format(
                    resumption_token.text
                )
            )

        tree = etree.fromstring(result.data)
        assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1
        assert len(tree.xpath("/x:OAI-PMH/x:ListRecords", namespaces=NAMESPACES)) == 1
        assert (
            len(tree.xpath("/x:OAI-PMH/x:ListRecords/x:record", namespaces=NAMESPACES))
            == 10
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header", namespaces=NAMESPACES
                )
            )
            == 10
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header" "/x:identifier",
                    namespaces=NAMESPACES,
                )
            )
            == 10
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header" "/x:datestamp",
                    namespaces=NAMESPACES,
                )
            )
            == 10
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:metadata",
                    namespaces=NAMESPACES,
                )
            )
            == 10
        )

        # Third resumption token
        resumption_token = tree.xpath(
            "/x:OAI-PMH/x:ListRecords/x:resumptionToken", namespaces=NAMESPACES
        )[0]
        assert resumption_token.text
        with app.test_client() as c:
            result = c.get(
                "/oai2d?verb=ListRecords&resumptionToken={0}".format(
                    resumption_token.text
                )
            )

        tree = etree.fromstring(result.data)
        assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1
        assert len(tree.xpath("/x:OAI-PMH/x:ListRecords", namespaces=NAMESPACES)) == 1
        assert (
            len(tree.xpath("/x:OAI-PMH/x:ListRecords/x:record", namespaces=NAMESPACES))
            == 2
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header", namespaces=NAMESPACES
                )
            )
            == 2
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header" "/x:identifier",
                    namespaces=NAMESPACES,
                )
            )
            == 2
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header" "/x:datestamp",
                    namespaces=NAMESPACES,
                )
            )
            == 2
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:metadata",
                    namespaces=NAMESPACES,
                )
            )
            == 2
        )

        # No fourth resumption token
        resumption_token = tree.xpath(
            "/x:OAI-PMH/x:ListRecords/x:resumptionToken", namespaces=NAMESPACES
        )[0]
        assert not resumption_token.text

        # Check from:until range
        with app.test_client() as c:
            # Check date and datetime timestamps.
            for granularity in (False, True):
                result = c.get(
                    "/oai2d?verb=ListRecords&metadataPrefix=oai_dc"
                    "&from={0}&until={1}".format(
                        datetime_to_datestamp(
                            record.updated - timedelta(days=1),
                            day_granularity=granularity,
                        ),
                        datetime_to_datestamp(
                            record.updated + timedelta(days=1),
                            day_granularity=granularity,
                        ),
                    )
                )
                assert result.status_code == 200

                tree = etree.fromstring(result.data)
                assert (
                    len(
                        tree.xpath(
                            "/x:OAI-PMH/x:ListRecords/x:record", namespaces=NAMESPACES
                        )
                    )
                    == 10
                )

                # Check from:until range in resumption token
                resumption_token = tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:resumptionToken", namespaces=NAMESPACES
                )[0]
                assert resumption_token.text
                with app.test_client() as c:
                    result = c.get(
                        "/oai2d?verb=ListRecords&resumptionToken={0}".format(
                            resumption_token.text
                        )
                    )
                assert result.status_code == 200


def test_listidentifiers(app):
    """Test verb ListIdentifiers."""
    from invenio_oaiserver.models import OAISet

    with app.app_context():
        current_oaiserver.unregister_signals_oaiset()
        # create new OAI Set
        with db.session.begin_nested():
            oaiset = OAISet(
                spec="test0",
                name="Test0",
                description="test desc 0",
                search_pattern="title_statement.title:Test0",
                system_created=False,
            )
            db.session.add(oaiset)
        db.session.commit()

    run_after_insert_oai_set()

    with app.test_request_context():
        indexer = RecordIndexer()

        # create a new record (inside the OAI Set)
        with db.session.begin_nested():
            record_id = uuid.uuid4()
            data = {"title_statement": {"title": "Test0"}}
            recid_minter(record_id, data)
            pid = oaiid_minter(record_id, data)
            record = current_oaiserver.record_cls.create(data, id_=record_id)

        db.session.commit()

        indexer.index_by_id(record_id)
        current_search.flush_and_refresh("_all")

        pid_value = pid.pid_value

        # get the list of identifiers
        with app.test_client() as c:
            result = c.get("/oai2d?verb=ListIdentifiers&metadataPrefix=oai_dc")

        tree = etree.fromstring(result.data)

        assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1
        assert (
            len(tree.xpath("/x:OAI-PMH/x:ListIdentifiers", namespaces=NAMESPACES)) == 1
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListIdentifiers/x:header", namespaces=NAMESPACES
                )
            )
            == 1
        )
        identifier = tree.xpath(
            "/x:OAI-PMH/x:ListIdentifiers/x:header/x:identifier", namespaces=NAMESPACES
        )
        assert len(identifier) == 1
        assert identifier[0].text == str(pid_value)
        datestamp = tree.xpath(
            "/x:OAI-PMH/x:ListIdentifiers/x:header/x:datestamp", namespaces=NAMESPACES
        )
        assert len(datestamp) == 1
        assert datestamp[0].text == datetime_to_datestamp(record.updated)

        # Check from:until range
        with app.test_client() as c:
            # Check date and datetime timestamps.
            for granularity in (False, True):
                result = c.get(
                    "/oai2d?verb=ListIdentifiers&metadataPrefix=oai_dc"
                    "&from={0}&until={1}".format(
                        datetime_to_datestamp(
                            record.updated - timedelta(1), day_granularity=granularity
                        ),
                        datetime_to_datestamp(
                            record.updated + timedelta(1), day_granularity=granularity
                        ),
                    )
                )
                assert result.status_code == 200

                tree = etree.fromstring(result.data)
                identifier = tree.xpath(
                    "/x:OAI-PMH/x:ListIdentifiers/x:header/x:identifier",
                    namespaces=NAMESPACES,
                )
                assert len(identifier) == 1

        # check set param
        with app.test_client() as c:
            for granularity in (False, True):
                result = c.get(
                    "/oai2d?verb=ListIdentifiers&metadataPrefix=oai_dc"
                    "&set=test0".format(
                        datetime_to_datestamp(
                            record.updated - timedelta(1), day_granularity=granularity
                        ),
                        datetime_to_datestamp(
                            record.updated + timedelta(1), day_granularity=granularity
                        ),
                    )
                )
                assert result.status_code == 200

                tree = etree.fromstring(result.data)
                identifier = tree.xpath(
                    "/x:OAI-PMH/x:ListIdentifiers/x:header/x:identifier",
                    namespaces=NAMESPACES,
                )
                assert len(identifier) == 1

        # check from:until range and set param
        with app.test_client() as c:
            for granularity in (False, True):
                result = c.get(
                    "/oai2d?verb=ListIdentifiers&metadataPrefix=oai_dc"
                    "&from={0}&until={1}&set=test0".format(
                        datetime_to_datestamp(
                            record.updated - timedelta(1), day_granularity=granularity
                        ),
                        datetime_to_datestamp(
                            record.updated + timedelta(1), day_granularity=granularity
                        ),
                    )
                )
                assert result.status_code == 200

                tree = etree.fromstring(result.data)
                identifier = tree.xpath(
                    "/x:OAI-PMH/x:ListIdentifiers/x:header/x:identifier",
                    namespaces=NAMESPACES,
                )
                assert len(identifier) == 1


def test_list_sets_long(app):
    """Test listing of sets."""
    from invenio_db import db

    from invenio_oaiserver.models import OAISet

    with app.app_context():
        current_oaiserver.unregister_signals_oaiset()
        with db.session.begin_nested():
            for i in range(27):
                oaiset = OAISet(
                    spec="test{0}".format(i),
                    name="Test{0}".format(i),
                    description="test desc {0}".format(i),
                    search_pattern="title_statement.title:Test{0}".format(i),
                    system_created=False,
                )
                db.session.add(oaiset)
        db.session.commit()

    run_after_insert_oai_set()

    with app.test_client() as c:
        # First page:
        result = c.get("/oai2d?verb=ListSets")
        tree = etree.fromstring(result.data)

        assert (
            len(tree.xpath("/x:OAI-PMH/x:ListSets/x:set", namespaces=NAMESPACES)) == 10
        )

        resumption_token = tree.xpath(
            "/x:OAI-PMH/x:ListSets/x:resumptionToken", namespaces=NAMESPACES
        )[0]
        assert resumption_token.text

        # Second page:
        result = c.get(
            "/oai2d?verb=ListSets&resumptionToken={0}".format(resumption_token.text)
        )
        tree = etree.fromstring(result.data)

        assert (
            len(tree.xpath("/x:OAI-PMH/x:ListSets/x:set", namespaces=NAMESPACES)) == 10
        )

        resumption_token = tree.xpath(
            "/x:OAI-PMH/x:ListSets/x:resumptionToken", namespaces=NAMESPACES
        )[0]
        assert resumption_token.text

        # Third page:
        result = c.get(
            "/oai2d?verb=ListSets&resumptionToken={0}".format(resumption_token.text)
        )
        tree = etree.fromstring(result.data)

        assert (
            len(tree.xpath("/x:OAI-PMH/x:ListSets/x:set", namespaces=NAMESPACES)) == 7
        )

        resumption_token = tree.xpath(
            "/x:OAI-PMH/x:ListSets/x:resumptionToken", namespaces=NAMESPACES
        )[0]
        assert not resumption_token.text


def test_list_sets_with_resumption_token_and_other_args(app):
    """Test list sets with resumption tokens."""
    pass
