# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""test cases."""
import pytest
import datetime
from datetime import timedelta, timezone
from mock import patch
from flask_babelex import Babel

from sqlalchemy.orm.exc import NoResultFound
from lxml import etree
from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from weko_index_tree.models import Index
from weko_records.api import Mapping

from invenio_oaiserver.response import is_private_index, getrecord, listrecords, \
    NS_DC, NS_OAIDC, NS_OAIPMH, is_pubdate_in_future, listidentifiers
from invenio_oaiserver.models import Identify, OAISet
from invenio_oaiserver.utils import HARVEST_PRIVATE, datetime_to_datestamp


NAMESPACES = {'x': NS_OAIPMH, 'y': NS_OAIDC, 'z': NS_DC}


#def test_is_private_index(app):
#    """Test of method which checks whether index of workflow is private."""
#    # 呼び出されていないメソッド
#    record = {"path": "example_path"}
#    res = is_private_index(record)


def test_getrecord(app, records, item_type, mock_execute, mocker):
    """Test of method which creates OAI-PMH response for verb GetRecord."""
    with app.app_context():
        identify = Identify(
            outPutSetting=True
        )
        index_metadata = {
            "id": 1557819692844,
            "parent": 0,
            "position": 0,
            "index_name": "コンテンツタイプ (Contents Type)",
            "index_name_english": "Contents Type",
            "index_link_name": "",
            "index_link_name_english": "New Index",
            "index_link_enabled": False,
            "more_check": False,
            "display_no": 5,
            "harvest_public_state": True,
            "display_format": 1,
            "image_name": "",
            "public_state": True,
            "recursive_public_state": True,
            "rss_status": False,
            "coverpage_state": False,
            "recursive_coverpage_check": False,
            "browsing_role": "3,-98,-99",
            "recursive_browsing_role": False,
            "contribute_role": "1,2,3,4,-98,-99",
            "recursive_contribute_role": False,
            "browsing_group": "",
            "recursive_browsing_group": False,
            "recursive_contribute_group": False,
            "owner_user_id": 1,
            "item_custom_sort": {"2": 1}
        }
        index = Index(**index_metadata)
        mapping = Mapping.create(
            item_type_id=item_type.id,
            mapping={}
        )
        with db.session.begin_nested():
            db.session.add(identify)
            db.session.add(index)
        dummy_data = {
            "hits": {
                "total": 3,
                "hits": [
                    {
                        "_source": {
                            "_oai": {"id": str(records[0][0])},
                            "_updated": "2022-01-01T10:10:10"
                        },
                        "_id": records[0][2].id,
                    },
                    {
                        "_source": {
                            "_oai": {"id": str(records[1][0])},
                            "_updated": "2022-01-01T10:10:10"
                        },
                        "_id": records[1][2].id,
                    },
                    {
                        "_source": {
                            "_oai": {"id": str(records[2][0])},
                            "_updated": "2022-01-01T10:10:10"
                        },
                        "_id": records[2][2].id,
                    },
                ]
            }
        }
        kwargs = dict(
            metadataPrefix="jpcoar_1.0",
            verb="GetRecord",
            identifier=str(records[0][0])
        )
        ns = {"root_name": "jpcoar", "namespaces":{'': 'https://github.com/JPCOAR/schema/blob/master/1.0/',
              'dc': 'http://purl.org/dc/elements/1.1/', 'xs': 'http://www.w3.org/2001/XMLSchema',
              'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'xml': 'http://www.w3.org/XML/1998/namespace',
              'dcndl': 'http://ndl.go.jp/dcndl/terms/', 'oaire': 'http://namespace.openaire.eu/schema/oaire/',
              'jpcoar': 'https://github.com/JPCOAR/schema/blob/master/1.0/',
              'dcterms': 'http://purl.org/dc/terms/', 'datacite': 'https://schema.datacite.org/meta/kernel-4/',
              'rioxxterms': 'http://www.rioxx.net/schema/v2.0/rioxxterms/'}}
        mocker.patch("invenio_oaiserver.response.to_utc",side_effect=lambda x:x)
        mocker.patch("weko_index_tree.utils.get_user_groups",return_value=[])
        mocker.patch("weko_index_tree.utils.check_roles",return_value=True)
        mocker.patch("invenio_oaiserver.response.get_identifier",return_value=None)
        mocker.patch("weko_schema_ui.schema.cache_schema",return_value=ns)
        with patch("invenio_oaiserver.query.OAIServerSearch.execute",return_value=mock_execute(dummy_data)):
            # return error 1
            identify = Identify(
                outPutSetting=False
            )
            with patch("invenio_oaiserver.response.OaiIdentify.get_all",return_value=identify):
                res = getrecord(**kwargs)
                assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"

            # return error 2
            with patch("invenio_oaiserver.response.is_output_harvest",return_value=HARVEST_PRIVATE):
                res = getrecord(**kwargs)
                assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"

        dummy_data = {
            "hits": {
                "total": 1,
                "hits": [
                    {
                        "_source": {
                            "_oai": {"id": str(records[3][0])},
                            "_updated": "2022-01-01T10:10:10"
                        },
                        "_id": records[3][2].id,
                    }
                ]
            }
        }
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="GetRecord",
            identifier=str(records[2][0])
        )
        # not etree_record.get("system_identifier_doi")
        with patch("invenio_oaiserver.response.is_exists_doi",return_value=False):
            with patch("invenio_oaiserver.query.OAIServerSearch.execute",return_value=mock_execute(dummy_data)):
                res = getrecord(**kwargs)
                identifier = res.xpath(
                    '/x:OAI-PMH/x:GetRecord/x:record/x:header/x:identifier/text()',
                    namespaces=NAMESPACES)
                assert identifier == [str(records[2][0])]
                datestamp = res.xpath(
                    '/x:OAI-PMH/x:GetRecord/x:record/x:header/x:datestamp/text()',
                    namespaces=NAMESPACES)
                assert datestamp == [datetime_to_datestamp(records[2][0].updated)]

            kwargs = dict(
                metadataPrefix='jpcoar_1.0',
                verb="GetRecord",
                identifier=str(records[3][0])
            )
            # etree_record.get("system_identifier_doi")
            with patch("invenio_oaiserver.response.is_exists_doi",return_value=True):
                res = getrecord(**kwargs)
                identifier = res.xpath(
                    '/x:OAI-PMH/x:GetRecord/x:record/x:header/x:identifier/text()',
                    namespaces=NAMESPACES)
                assert identifier == [str(records[3][0])]
                assert len(res.xpath('/x:OAI-PMH/x:GetRecord/x:record/x:metadata',
                                        namespaces=NAMESPACES)) == 1


def test_getrecord_header_deleted(app,records,item_type,mock_execute,mocker):
    """Test of method which creates OAI-PMH response for verb GetRecord."""
    with app.app_context():
        identify = Identify(
            outPutSetting=True
        )
        index_metadata = {
            "id": 1557819692844,
            "parent": 0,
            "position": 0,
            "index_name": "コンテンツタイプ (Contents Type)",
            "index_name_english": "Contents Type",
            "index_link_name": "",
            "index_link_name_english": "New Index",
            "index_link_enabled": False,
            "more_check": False,
            "display_no": 5,
            "harvest_public_state": True,
            "display_format": 1,
            "image_name": "",
            "public_state": True,
            "recursive_public_state": True,
            "rss_status": False,
            "coverpage_state": False,
            "recursive_coverpage_check": False,
            "browsing_role": "3,-98,-99",
            "recursive_browsing_role": False,
            "contribute_role": "1,2,3,4,-98,-99",
            "recursive_contribute_role": False,
            "browsing_group": "",
            "recursive_browsing_group": False,
            "recursive_contribute_group": False,
            "owner_user_id": 1,
            "item_custom_sort": {"2": 1}
        }
        index = Index(**index_metadata)
        mapping = Mapping.create(
            item_type_id=item_type.id,
            mapping={}
        )
        with db.session.begin_nested():
            db.session.add(identify)
            db.session.add(index)
        kwargs = dict(
            metadataPrefix="jpcoar_1.0",
            verb="GetRecord",
            identifier=str(records[0][0])
        )
        ns = {"root_name": "jpcoar", "namespaces":{'': 'https://github.com/JPCOAR/schema/blob/master/1.0/',
              'dc': 'http://purl.org/dc/elements/1.1/', 'xs': 'http://www.w3.org/2001/XMLSchema',
              'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'xml': 'http://www.w3.org/XML/1998/namespace',
              'dcndl': 'http://ndl.go.jp/dcndl/terms/', 'oaire': 'http://namespace.openaire.eu/schema/oaire/',
              'jpcoar': 'https://github.com/JPCOAR/schema/blob/master/1.0/', 'dcterms': 'http://purl.org/dc/terms/',
              'datacite': 'https://schema.datacite.org/meta/kernel-4/', 'rioxxterms': 'http://www.rioxx.net/schema/v2.0/rioxxterms/'}}
        mocker.patch("invenio_oaiserver.response.to_utc",side_effect=lambda x:x)
        mocker.patch("weko_index_tree.utils.get_user_groups",return_value=[])
        mocker.patch("weko_index_tree.utils.check_roles",return_value=True)
        mocker.patch("invenio_oaiserver.response.get_identifier",return_value=None)
        mocker.patch("weko_schema_ui.schema.cache_schema",return_value=ns)
        dummy_data = {
            "hits": {
                "total": 1,
                "hits": [
                    {
                        "_source": {
                            "_oai": {"id": str(records[3][0])},
                            "_updated": "2022-01-01T10:10:10"
                        },
                        "_id": records[3][2].id,
                    }
                ]
            }
        }
        with patch("invenio_oaiserver.response.is_exists_doi",return_value=False):
            with patch("invenio_oaiserver.query.OAIServerSearch.execute",return_value=mock_execute(dummy_data)):
                res = getrecord(**kwargs)
                header = res.xpath(
                    '/x:OAI-PMH/x:GetRecord/x:record/x:header[@status="deleted"]',
                    namespaces=NAMESPACES)
                assert len(header) == 1


def test_listrecords(app,records,item_type,mock_execute,mocker):
    with app.app_context():
        identify = Identify(
            outPutSetting=True
        )
        oaiset = OAISet(
            spec="1557819692844"
        )
        index_metadata = {
            "id":1557819692844,
            "parent":0,
            "position":0,
            "index_name":"コンテンツタイプ (Contents Type)",
            "index_name_english":"Contents Type",
            "index_link_name":"",
            "index_link_name_english":"New Index",
            "index_link_enabled":False,
            "more_check":False,
            "display_no":5,
            "harvest_public_state":True,
            "display_format":1,
            "image_name":"",
            "public_state":True,
            "recursive_public_state":True,
            "rss_status":False,
            "coverpage_state":False,
            "recursive_coverpage_check":False,
            "browsing_role":"3,-98,-99",
            "recursive_browsing_role":False,
            "contribute_role":"1,2,3,4,-98,-99",
            "recursive_contribute_role":False,
            "browsing_group":"",
            "recursive_browsing_group":False,
            "recursive_contribute_group":False,
            "owner_user_id":1,
            "item_custom_sort":{"2":1}
        }
        index = Index(**index_metadata)
        mapping = Mapping.create(
            item_type_id=item_type.id,
            mapping={}
        )
        with db.session.begin_nested():
            db.session.add(identify)
            db.session.add(index)
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="ListRecords",
            set="1557819692844"
        )
        dummy_data={
            "hits":{
                "total":4,
                "hits":[
                    {
                        "_source":{
                            "_oai":{"id":str(records[0][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[0][2].id,
                    },
                    {
                        "_source":{
                            "_oai":{"id":str(records[1][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[1][2].id,
                    },
                    {
                        "_source":{
                            "_oai":{"id":str(records[2][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[2][2].id,
                    },
                ]
            }
        }

        ns={"root_name": "jpcoar", "namespaces":{'': 'https://github.com/JPCOAR/schema/blob/master/1.0/',
            'dc': 'http://purl.org/dc/elements/1.1/', 'xs': 'http://www.w3.org/2001/XMLSchema',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'xml': 'http://www.w3.org/XML/1998/namespace',
            'dcndl': 'http://ndl.go.jp/dcndl/terms/', 'oaire': 'http://namespace.openaire.eu/schema/oaire/',
            'jpcoar': 'https://github.com/JPCOAR/schema/blob/master/1.0/', 'dcterms': 'http://purl.org/dc/terms/',
            'datacite': 'https://schema.datacite.org/meta/kernel-4/', 'rioxxterms': 'http://www.rioxx.net/schema/v2.0/rioxxterms/'}}
        mocker.patch("invenio_oaiserver.response.OAISet.get_set_by_spec",return_value=oaiset)
        mocker.patch("invenio_oaiserver.response.to_utc",side_effect=lambda x:x)
        mocker.patch("weko_index_tree.utils.get_user_groups",return_value=[])
        mocker.patch("weko_index_tree.utils.check_roles",return_value=True)
        mocker.patch("invenio_oaiserver.response.get_identifier",return_value=None)
        mocker.patch("weko_schema_ui.schema.cache_schema",return_value=ns)
        with patch("invenio_oaiserver.query.OAIServerSearch.execute",return_value=mock_execute(dummy_data)):
            res=listrecords(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:ListRecords/x:record[1]/x:header/x:identifier/text()",namespaces=NAMESPACES) == [str(records[1][0])]
            assert res.xpath("/x:OAI-PMH/x:ListRecords/x:record[2]/x:header/x:identifier/text()",namespaces=NAMESPACES) == [str(records[2][0])]

        # return error 1
        identify = Identify(
            outPutSetting=False
        )
        with patch("invenio_oaiserver.response.OaiIdentify.get_all",return_value=identify):
            res=listrecords(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"

        # return error 2
        with patch("invenio_oaiserver.response.OAISet.get_set_by_spec",return_value=None):
            res=listrecords(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"

        # return error 3
        with patch("invenio_oaiserver.response.is_output_harvest",return_value=HARVEST_PRIVATE):
            res=listrecords(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"

        # return error 4
        class MockResult:
            def __init__(self):
                pass
            @property
            def total(self):
                return None
        with patch("invenio_oaiserver.response.get_records",return_value=MockResult()):
            res=listrecords(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"

        dummy_data={
            "hits":{
                "total":1,
                "hits":[
                    {
                        "_source":{
                            "_oai":{"id":str(records[0][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[0][2].id,
                    }
                ]
            }
        }
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="ListRecords",
        )
        with patch("invenio_oaiserver.query.OAIServerSearch.execute",return_value=mock_execute(dummy_data)):
            # return error5
            res=listrecords(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"
            with patch("invenio_oaiserver.response.OAIIDProvider.get",side_effect=PIDDoesNotExistError("test pid_type","test pid_value")):
                # raise PIDDoesNotExistError
                res=listrecords(**kwargs)
            with patch("invenio_oaiserver.response.WekoRecord.get_record_by_uuid",side_effect=NoResultFound()):
                # raise NoResultFound
                res=listrecords(**kwargs)

        dummy_data={
            "hits":{
                "total":1,
                "hits":[
                    {
                        "_source":{
                            "_oai":{"id":str(records[3][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[3][2].id,
                    }
                ]
            }
        }
        # not etree_reocrd.get("system_identifier_doi")
        with patch("invenio_oaiserver.response.is_exists_doi",return_value=False):
            with patch("invenio_oaiserver.query.OAIServerSearch.execute",return_value=mock_execute(dummy_data)):
                res=listrecords(**kwargs)
                assert res.xpath("/x:OAI-PMH/x:ListRecords/x:record[1]/x:header/x:identifier/text()",namespaces=NAMESPACES) == [str(records[3][0])]


# def envelope(**kwargs):
# def error(errors, **kwargs):
# def verb(**kwargs):
# def identify(**kwargs):
# def resumption_token(parent, pagination, **kwargs):
# def listsets(**kwargs):
# def listmetadataformats(**kwargs):
# def header(parent, identifier, datestamp, sets=[], deleted=False):
# def extract_paths_from_sets(sets):
# def is_deleted_workflow(pid):
# def is_private_workflow(record):
# def is_pubdate_in_future(record):

def test_is_pubdate_in_future():
    from flask import Flask, session
    app = Flask('test')
    Babel(app)
    app.config['BABEL_DEFAULT_TIMEZONE']='Asia/Tokyo'
    with app.test_request_context():
        # offset-naive
        now = datetime.utcnow()
        record = {'_oai': {'id': 'oai:weko3.example.org:00000002', 'sets': ['1658073625012']}, 'path': ['1658073625012'], 'owner': '1', 'recid': '2', 'title': ['a'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-07-18'}, '_buckets': {'deposit': '62d9f851-3d9f-48b7-946b-38839df98d4c'}, '_deposit': {'id': '2', 'pid': {'type': 'depid', 'value': '2', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'a', 'author_link': [], 'item_type_id': '15', 'publish_date': '2022-07-18', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'a', 'subitem_1551255648112': 'ja'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'relation_version_is_last': True, 'json': {'_source': {'_item_metadata': {'system_identifier_doi': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_systemidt_identifier': 'https://localhost:8443/records/2', 'subitem_systemidt_identifier_type': 'URI'}]}}}}}
        record['publish_date'] = now.strftime('%Y-%m-%d')
        assert record['publish_date'] == now.strftime('%Y-%m-%d')
        assert is_pubdate_in_future(record)==False

        # offset-naive
        now = datetime.utcnow() + timedelta(days=1)
        record = {'_oai': {'id': 'oai:weko3.example.org:00000002', 'sets': ['1658073625012']}, 'path': ['1658073625012'], 'owner': '1', 'recid': '2', 'title': ['a'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-07-18'}, '_buckets': {'deposit': '62d9f851-3d9f-48b7-946b-38839df98d4c'}, '_deposit': {'id': '2', 'pid': {'type': 'depid', 'value': '2', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'a', 'author_link': [], 'item_type_id': '15', 'publish_date': '2022-07-18', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'a', 'subitem_1551255648112': 'ja'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'relation_version_is_last': True, 'json': {'_source': {'_item_metadata': {'system_identifier_doi': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_systemidt_identifier': 'https://localhost:8443/records/2', 'subitem_systemidt_identifier_type': 'URI'}]}}}}}
        record['publish_date'] = now.strftime('%Y-%m-%d')
        assert record['publish_date'] == now.strftime('%Y-%m-%d')
        assert is_pubdate_in_future(record)==True

        # offset-naive
        now = datetime.utcnow() + timedelta(days=10)
        record = {'_oai': {'id': 'oai:weko3.example.org:00000002', 'sets': ['1658073625012']}, 'path': ['1658073625012'], 'owner': '1', 'recid': '2', 'title': ['a'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-07-18'}, '_buckets': {'deposit': '62d9f851-3d9f-48b7-946b-38839df98d4c'}, '_deposit': {'id': '2', 'pid': {'type': 'depid', 'value': '2', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'a', 'author_link': [], 'item_type_id': '15', 'publish_date': '2022-07-18', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'a', 'subitem_1551255648112': 'ja'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'relation_version_is_last': True, 'json': {'_source': {'_item_metadata': {'system_identifier_doi': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_systemidt_identifier': 'https://localhost:8443/records/2', 'subitem_systemidt_identifier_type': 'URI'}]}}}}}
        record['publish_date'] = now.strftime('%Y-%m-%d')
        assert record['publish_date'] == now.strftime('%Y-%m-%d')
        assert is_pubdate_in_future(record)==True

                # offset-naive
        now = datetime.utcnow() - timedelta(days=1)
        record = {'_oai': {'id': 'oai:weko3.example.org:00000002', 'sets': ['1658073625012']}, 'path': ['1658073625012'], 'owner': '1', 'recid': '2', 'title': ['a'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-07-18'}, '_buckets': {'deposit': '62d9f851-3d9f-48b7-946b-38839df98d4c'}, '_deposit': {'id': '2', 'pid': {'type': 'depid', 'value': '2', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'a', 'author_link': [], 'item_type_id': '15', 'publish_date': '2022-07-18', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'a', 'subitem_1551255648112': 'ja'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'relation_version_is_last': True, 'json': {'_source': {'_item_metadata': {'system_identifier_doi': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_systemidt_identifier': 'https://localhost:8443/records/2', 'subitem_systemidt_identifier_type': 'URI'}]}}}}}
        record['publish_date'] = now.strftime('%Y-%m-%d')
        assert record['publish_date'] == now.strftime('%Y-%m-%d')
        assert is_pubdate_in_future(record)==False

        # offset-naive
        now = datetime.utcnow() - timedelta(days=10)
        record = {'_oai': {'id': 'oai:weko3.example.org:00000002', 'sets': ['1658073625012']}, 'path': ['1658073625012'], 'owner': '1', 'recid': '2', 'title': ['a'], 'pubdate': {'attribute_name': 'PubDate', 'attribute_value': '2022-07-18'}, '_buckets': {'deposit': '62d9f851-3d9f-48b7-946b-38839df98d4c'}, '_deposit': {'id': '2', 'pid': {'type': 'depid', 'value': '2', 'revision_id': 0}, 'owner': '1', 'owners': [1], 'status': 'published', 'created_by': 1, 'owners_ext': {'email': 'wekosoftware@nii.ac.jp', 'username': '', 'displayname': ''}}, 'item_title': 'a', 'author_link': [], 'item_type_id': '15', 'publish_date': '2022-07-18', 'publish_status': '0', 'weko_shared_id': -1, 'item_1617186331708': {'attribute_name': 'Title', 'attribute_value_mlt': [{'subitem_1551255647225': 'a', 'subitem_1551255648112': 'ja'}]}, 'item_1617258105262': {'attribute_name': 'Resource Type', 'attribute_value_mlt': [{'resourceuri': 'http://purl.org/coar/resource_type/c_5794', 'resourcetype': 'conference paper'}]}, 'relation_version_is_last': True, 'json': {'_source': {'_item_metadata': {'system_identifier_doi': {'attribute_name': 'Identifier', 'attribute_value_mlt': [{'subitem_systemidt_identifier': 'https://localhost:8443/records/2', 'subitem_systemidt_identifier_type': 'URI'}]}}}}}
        record['publish_date'] = now.strftime('%Y-%m-%d')
        assert record['publish_date'] == now.strftime('%Y-%m-%d')
        assert is_pubdate_in_future(record)==False


# def is_private_index(record):
# def is_private_index_by_public_list(item_path, public_index_ids):
# def set_identifier(param_record, param_rec):
# def is_exists_doi(param_record):
# def getrecord(**kwargs):
# def listidentifiers(**kwargs):
# def listrecords(**kwargs):
# def get_error_code_msg(code=''):
# def create_identifier_index(root, **kwargs):
# def check_correct_system_props_mapping(object_uuid, system_mapping_config):
# def combine_record_file_urls(record, object_uuid, meta_prefix):
# def create_files_url(root_url, record_id, filename):
# def get_identifier(record):

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_issue34851_listrecords -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_issue34851_listrecords(app, records, item_type, mock_execute,mocker):
    with app.app_context():
        identify = Identify(
            outPutSetting=True
        )
        oaiset = OAISet(
            spec="1557819692844"
        )
        index_metadata = {
            "id":1557819692844,
            "parent":0,
            "position":0,
            "index_name":"コンテンツタイプ (Contents Type)",
            "index_name_english":"Contents Type",
            "index_link_name":"",
            "index_link_name_english":"New Index",
            "index_link_enabled":False,
            "more_check":False,
            "display_no":5,
            "harvest_public_state":True,
            "display_format":1,
            "image_name":"",
            "public_state":True,
            "recursive_public_state":True,
            "rss_status":False,
            "coverpage_state":False,
            "recursive_coverpage_check":False,
            "browsing_role":"3,-98,-99",
            "recursive_browsing_role":False,
            "contribute_role":"1,2,3,4,-98,-99",
            "recursive_contribute_role":False,
            "browsing_group":"",
            "recursive_browsing_group":False,
            "recursive_contribute_group":False,
            "owner_user_id":1,
            "item_custom_sort":{"2":1}
        }
        index = Index(**index_metadata)
        mapping = Mapping.create(
            item_type_id=item_type.id,
            mapping={}
        )
        with db.session.begin_nested():
            db.session.add(identify)
            db.session.add(index)
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="ListRecords",
            set="1557819692844"
        )
        dummy_data={
            "hits":{
                "total":4,
                "hits":[
                    {
                        "_source":{
                            "_oai":{"id":str(records[0][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[0][2].id,
                    },
                    {
                        "_source":{
                            "_oai":{"id":str(records[1][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[1][2].id,
                    },
                    {
                        "_source":{
                            "_oai":{"id":str(records[2][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[2][2].id,
                    },
                ]
            }
        }

        ns={"root_name": "jpcoar", "namespaces":{'': 'https://github.com/JPCOAR/schema/blob/master/1.0/',
            'dc': 'http://purl.org/dc/elements/1.1/', 'xs': 'http://www.w3.org/2001/XMLSchema',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'xml': 'http://www.w3.org/XML/1998/namespace',
            'dcndl': 'http://ndl.go.jp/dcndl/terms/', 'oaire': 'http://namespace.openaire.eu/schema/oaire/',
            'jpcoar': 'https://github.com/JPCOAR/schema/blob/master/1.0/', 'dcterms': 'http://purl.org/dc/terms/',
            'datacite': 'https://schema.datacite.org/meta/kernel-4/', 'rioxxterms': 'http://www.rioxx.net/schema/v2.0/rioxxterms/'}}
        mocker.patch("invenio_oaiserver.response.OAISet.get_set_by_spec",return_value=oaiset)
        mocker.patch("invenio_oaiserver.response.to_utc",side_effect=lambda x:x)
        mocker.patch("weko_index_tree.utils.get_user_groups",return_value=[])
        mocker.patch("weko_index_tree.utils.check_roles",return_value=True)
        mocker.patch("invenio_oaiserver.response.get_identifier",return_value=None)
        mocker.patch("weko_schema_ui.schema.cache_schema",return_value=ns)
        with patch("invenio_oaiserver.query.OAIServerSearch.execute",return_value=mock_execute(dummy_data)):
            res=listrecords(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:ListRecords/x:record[1]/x:header/x:datestamp/text()",namespaces=NAMESPACES) == [records[1][2].updated.replace(microsecond=0).isoformat()+"Z"]
            assert res.xpath("/x:OAI-PMH/x:ListRecords/x:record[2]/x:header/x:datestamp/text()",namespaces=NAMESPACES) == [records[2][2].updated.replace(microsecond=0).isoformat()+"Z"]


# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_issue34851_listidentifiers -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_issue34851_listidentifiers(app, records, item_type, mock_execute,mocker):
    with app.app_context():
        identify = Identify(
            outPutSetting=True
        )
        oaiset = OAISet(
            spec="1557819692844"
        )
        index_metadata = {
            "id":1557819692844,
            "parent":0,
            "position":0,
            "index_name":"コンテンツタイプ (Contents Type)",
            "index_name_english":"Contents Type",
            "index_link_name":"",
            "index_link_name_english":"New Index",
            "index_link_enabled":False,
            "more_check":False,
            "display_no":5,
            "harvest_public_state":True,
            "display_format":1,
            "image_name":"",
            "public_state":True,
            "recursive_public_state":True,
            "rss_status":False,
            "coverpage_state":False,
            "recursive_coverpage_check":False,
            "browsing_role":"3,-98,-99",
            "recursive_browsing_role":False,
            "contribute_role":"1,2,3,4,-98,-99",
            "recursive_contribute_role":False,
            "browsing_group":"",
            "recursive_browsing_group":False,
            "recursive_contribute_group":False,
            "owner_user_id":1,
            "item_custom_sort":{"2":1}
        }
        index = Index(**index_metadata)
        mapping = Mapping.create(
            item_type_id=item_type.id,
            mapping={}
        )
        with db.session.begin_nested():
            db.session.add(identify)
            db.session.add(index)
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="ListIdentifiers",
            set="1557819692844"
        )
        dummy_data={
            "hits":{
                "total":4,
                "hits":[
                    {
                        "_source":{
                            "_oai":{"id":str(records[0][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[0][2].id,
                    },
                    {
                        "_source":{
                            "_oai":{"id":str(records[1][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[1][2].id,
                    },
                    {
                        "_source":{
                            "_oai":{"id":str(records[2][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[2][2].id,
                    },
                ]
            }
        }

        ns={"root_name": "jpcoar", "namespaces":{'': 'https://github.com/JPCOAR/schema/blob/master/1.0/',
            'dc': 'http://purl.org/dc/elements/1.1/', 'xs': 'http://www.w3.org/2001/XMLSchema',
            'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'xml': 'http://www.w3.org/XML/1998/namespace',
            'dcndl': 'http://ndl.go.jp/dcndl/terms/', 'oaire': 'http://namespace.openaire.eu/schema/oaire/',
            'jpcoar': 'https://github.com/JPCOAR/schema/blob/master/1.0/', 'dcterms': 'http://purl.org/dc/terms/',
            'datacite': 'https://schema.datacite.org/meta/kernel-4/', 'rioxxterms': 'http://www.rioxx.net/schema/v2.0/rioxxterms/'}}
        mocker.patch("invenio_oaiserver.response.OAISet.get_set_by_spec",return_value=oaiset)
        mocker.patch("invenio_oaiserver.response.to_utc",side_effect=lambda x:x)
        mocker.patch("weko_index_tree.utils.get_user_groups",return_value=[])
        mocker.patch("weko_index_tree.utils.check_roles",return_value=True)
        mocker.patch("invenio_oaiserver.response.get_identifier",return_value=None)
        mocker.patch("weko_schema_ui.schema.cache_schema",return_value=ns)
        with patch("invenio_oaiserver.query.OAIServerSearch.execute",return_value=mock_execute(dummy_data)):
            res=listidentifiers(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:ListIdentifiers/x:header[1]/x:datestamp/text()",namespaces=NAMESPACES) == [records[1][2].updated.replace(microsecond=0).isoformat()+"Z"]
            assert res.xpath("/x:OAI-PMH/x:ListIdentifiers/x:header[2]/x:datestamp/text()",namespaces=NAMESPACES) == [records[2][2].updated.replace(microsecond=0).isoformat()+"Z"]
