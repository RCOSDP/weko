# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""test cases."""
import pytest
import uuid
from datetime import timedelta, datetime
from mock import patch
from flask import current_app
from flask_babelex import Babel
from werkzeug.utils import cached_property
from sqlalchemy.orm.exc import NoResultFound
from lxml import etree
from lxml.etree import Element, SubElement

from invenio_records.models import RecordMetadata
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier,PIDStatus
from invenio_pidrelations.models import PIDRelation

from weko_index_tree.models import Index
from weko_records.api import ItemTypes, Mapping
from weko_records.models import ItemTypeName
from weko_deposit.api import WekoRecord
from weko_records.models import ItemMetadata, ItemTypeMapping

from invenio_oaiserver.models import Identify, OAISet
from invenio_oaiserver.utils import HARVEST_PRIVATE, OUTPUT_HARVEST, PRIVATE_INDEX, datetime_to_datestamp

from invenio_pidstore import current_pidstore
from invenio_records import Record
from invenio_oaiserver.provider import OAIIDProvider

from invenio_oaiserver.response import (
    NS_DC, NS_OAIDC, NS_OAIPMH,NS_JPCOAR,
    is_private_index,
    getrecord, 
    listrecords,
    is_pubdate_in_future, 
    listidentifiers, 
    envelope,
    resumption_token,
    listsets,
    listmetadataformats, 
    extract_paths_from_sets,
    is_private_index_by_public_list,
    get_error_code_msg,
    create_identifier_index,
    check_correct_system_props_mapping,
    combine_record_file_urls,
    create_files_url,
    get_identifier,
    header,
    identify,
    is_draft_workflow
)


NAMESPACES = {'x': NS_OAIPMH, 'y': NS_OAIDC, 'z': NS_DC}


#def test_is_private_index(app):
#    """Test of method which checks whether index of workflow is private."""
#    # 呼び出されていないメソッド
#    record = {"path": "example_path"}
#    res = is_private_index(record)

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_is_draft_workflow -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_is_draft_workflow():
    not_draft = {
        "_oai": {"id": "oai:weko3.example.org:000000001","sets": ["1706242675706"]},
        "path": ["1706242675706"],
        "owner": "1",
        "recid": "1",
        "title": ["not_draft"],
        "pubdate": {"attribute_name": "PubDate","attribute_value": "2024-01-17"},
        "_buckets": {"deposit": "8b98e578-9cdc-47a8-bfdb-60ab6a25ccf9"},
        "_deposit": {
            "id": "1",
            "pid": {
                "type": "depid",
                "value": "1",
                "revision_id": 0
            },
            "owner": "1",
            "owners": [
                1
            ],
            "status": "published",
            "created_by": 1,
            "owners_ext": {
                "email": "wekosoftware@nii.ac.jp",
                "username": "",
                "displayname": ""
            }
        },
        "item_title": "not_draft",
        "author_link": [],
        "item_type_id": "15",
        "publish_date": "2024-01-17",
        "control_number": "139",
        "publish_status": "0",
        "weko_shared_id": -1,
        "item_1617186331708": {"attribute_name": "Title","attribute_value_mlt": [{"subitem_1551255647225": "not_draft","subitem_1551255648112": "ja"}]},
        "item_1617258105262": {"attribute_name": "Resource Type","attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_5794","resourcetype": "conference paper"}]},
        "relation_version_is_last": True
    }
    
    result = is_draft_workflow(not_draft)
    assert result == False
    
    draft = {
        "_oai": {"id": "oai:weko3.example.org:000000001","sets": ["1706242675706"]},
        "path": ["1706242675706"],
        "owner": "1",
        "recid": "1",
        "title": ["not_draft"],
        "pubdate": {"attribute_name": "PubDate","attribute_value": "2024-01-17"},
        "_buckets": {"deposit": "8b98e578-9cdc-47a8-bfdb-60ab6a25ccf9"},
        "_deposit": {
            "id": "1",
            "pid": {
                "type": "depid",
                "value": "1",
                "revision_id": 0
            },
            "owner": "1",
            "owners": [
                1
            ],
            "status": "draft",
            "created_by": 1
        },
        "item_title": "not_draft",
        "author_link": [],
        "item_type_id": "15",
        "publish_date": "2024-01-17",
        "control_number": "139",
        "publish_status": "0",
        "weko_shared_id": -1,
        "item_1617186331708": {"attribute_name": "Title","attribute_value_mlt": [{"subitem_1551255647225": "not_draft","subitem_1551255648112": "ja"}]},
        "item_1617258105262": {"attribute_name": "Resource Type","attribute_value_mlt": [{"resourceuri": "http://purl.org/coar/resource_type/c_5794","resourcetype": "conference paper"}]},
        "relation_version_is_last": True
    }
    
    result = is_draft_workflow(draft)
    assert result == True
    
# def getrecord
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_getrecord -vv -s -v --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_getrecord(app, db, item_type, mocker):
    with app.app_context():
        identify = Identify(
                outPutSetting=True
            )
        public_index_metadata = {
                "id": "1",
                "parent": 0,
                "position": 0,
                "index_name": "public_index",
                "index_name_english": "public_index",
                "display_no": 0,
                "harvest_public_state": True,
                "public_state": True,
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
        public_index = Index(**public_index_metadata)
        private_index_metadata = {
                "id": "2",
                "parent": 0,
                "position": 1,
                "index_name": "private_index",
                "index_name_english": "private_index",
                "display_no": 0,
                "harvest_public_state": True,
                "public_state": False,
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
        private_index = Index(**private_index_metadata)
        mapping = Mapping.create(
            item_type_id=item_type.id,
            mapping={}
        )
        with db.session.begin_nested():
            db.session.add(identify)
            db.session.add(public_index)
            db.session.add(private_index)
        db.session.commit()
        ns = {"root_name": "jpcoar", "namespaces":{'': 'https://github.com/JPCOAR/schema/blob/master/1.0/',
              'dc': 'http://purl.org/dc/elements/1.1/', 'xs': 'http://www.w3.org/2001/XMLSchema',
              'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'xml': 'http://www.w3.org/XML/1998/namespace',
              'dcndl': 'http://ndl.go.jp/dcndl/terms/', 'oaire': 'http://namespace.openaire.eu/schema/oaire/',
              'jpcoar': 'https://github.com/JPCOAR/schema/blob/master/1.0/',
              'dcterms': 'http://purl.org/dc/terms/', 'datacite': 'https://schema.datacite.org/meta/kernel-4/',
              'rioxxterms': 'http://www.rioxx.net/schema/v2.0/rioxxterms/'}}
        mocker.patch("weko_records_ui.utils.to_utc",side_effect=lambda x:x)
        mocker.patch("weko_index_tree.utils.get_user_groups",return_value=[])
        mocker.patch("weko_index_tree.utils.check_roles",return_value=True)
        mocker.patch("weko_schema_ui.schema.cache_schema",return_value=ns)
        mocker.patch("weko_deposit.api.get_record_without_version",side_effect=lambda x:x)
        
        def create_record(recid, title, path, pub_date, pub_status, is_draft, is_doi,is_exist_sysidt=False):
            record_data = {
                "_oai":{
                    "id":"",
                    "sets":path
                },
                "item_type_id":item_type.id,
                "path":path,
                "publish_date":pub_date,
                "publish_status":pub_status,
                "_deposit": {
                    "id": recid,
                    "pid": {
                        "type": "depid",
                        "value": "",
                        "revision_id": 0
                    },
                    "status": "published" if not is_draft else "draft",
                    "created_by": 1
                },
                "item_title": title,
                "recid":recid
            }
            if is_exist_sysidt:
                record_data["system_identifier_doi"] = {
                    "attribute_name":"Identifier",
                    "attribute_value_mlt":[
                        {
                            "subitem_systemidt_identifer":"https://test.org/records:{}".format(recid),
                            "subitem_systemidt_identifier_type":"URI"
                        }
                    ]
                }
            rec_uuid = uuid.uuid4()
            pid = current_pidstore.minters['recid'](rec_uuid, record_data)
            oai_val = "oai:weko3.example.org:{:08}".format(int(pid.pid_value))
            record_data["_oai"]["id"] = oai_val
            record_metadata = RecordMetadata(id=rec_uuid,json=record_data)
            db.session.add(record_metadata)
            oai = OAIIDProvider.create(
                object_type='oai',
                object_uuid=rec_uuid,
                pid_value=oai_val
            ).pid
            if is_doi:
                doi = PersistentIdentifier(
                    pid_type="doi",
                    pid_value="https://doi.org/2500/{:010}".format(int(pid.pid_value)),
                    status=PIDStatus.REGISTERED,
                    object_type="rec",
                    object_uuid=rec_uuid
                )
                db.session.add(doi)
            else:
                doi = None
            db.session.commit()
            return record_metadata, pid, oai, doi
            
        # identify.outPutSetting is false
        identify = Identify(
            outPutSetting=False
        )
        with patch("invenio_oaiserver.response.OaiIdentify.get_all",return_value=identify):
            kwargs = dict(
                metadataPrefix="jpcoar_1.0",
                verb="GetRecord",
                identifier="oai:test.org:000001"
            )
            res = getrecord(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "idDoesNotExist"
        
        # harvest is private(_is_output=2)
        record = create_record("1","harvest_is_private", ["100"], "2000-11-11", "0",False,False)
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="GetRecord",
            identifier=str(record[2].pid_value)
        )
        res = getrecord(**kwargs)
        assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "idDoesNotExist"
        
        # pubdate is feature(record.json._source._item_metadata.system_identifier_doi.attrivute_value_mlt.subitem_systemidt_identifier_type=doi, record.publish_date is feature,)
        record = create_record("2","xx", ["1"], "2100-11-11", "0",False,True)
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="GetRecord",
            identifier=str(record[2].pid_value)
        )
        res = getrecord(**kwargs)
        assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "idDoesNotExist"
        
        # new activity(record.publish_status=2)
        record = create_record("3","xx",["1"],"2000-11-11","2",False,False)
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="GetRecord",
            identifier=str(record[2].pid_value)
        )
        res = getrecord(**kwargs)
        assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "idDoesNotExist"

        # draft activity(record._deposit.status=draft)
        record = create_record("4","xx",["1"],"2000-11-11","2",True,False)
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="GetRecord",
            identifier=str(record[2].pid_value)
        )
        res = getrecord(**kwargs)
        assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "idDoesNotExist"

        ## harvest is public, item is private(record.path not in index_list)
        record = create_record("5","xx",["2"],"2000-11-11","0",False,False)
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="GetRecord",
            identifier=str(record[2].pid_value)
        )
        res = getrecord(**kwargs)
        assert res.xpath("/x:OAI-PMH/x:GetRecord/x:record/x:header",namespaces=NAMESPACES)[0].attrib["status"] == "deleted"
        assert res.xpath("/x:OAI-PMH/x:GetRecord/x:record/x:header/x:identifier/text()",namespaces=NAMESPACES) == [record[2].pid_value]

        # harvest is public, workflow is private(record.publish_status=1)
        record = create_record("6","xx",["1"],"2000-11-11","1",False,False)

        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="GetRecord",
            identifier=str(record[2].pid_value)
        )
        res = getrecord(**kwargs)
        assert res.xpath("/x:OAI-PMH/x:GetRecord/x:record/x:header",namespaces=NAMESPACES)[0].attrib["status"] == "deleted"
        assert res.xpath("/x:OAI-PMH/x:GetRecord/x:record/x:header/x:identifier/text()",namespaces=NAMESPACES) == [record[2].pid_value]

        # harvest is public, workflow is deleted(record.publish_status=-1)
        record = create_record("7","xx",["1"],"2000-11-11","-1",False,False)
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="GetRecord",
            identifier=str(record[2].pid_value)
        )
        res = getrecord(**kwargs)
        assert res.xpath("/x:OAI-PMH/x:GetRecord/x:record/x:header",namespaces=NAMESPACES)[0].attrib["status"] == "deleted"
        assert res.xpath("/x:OAI-PMH/x:GetRecord/x:record/x:header/x:identifier/text()",namespaces=NAMESPACES) == [record[2].pid_value]

        # harvest is public, publish is feature(record.publish_date is feature)
        record = create_record("8","xx",["1"],"2100-11-11","0",False,False)
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="GetRecord",
            identifier=str(record[2].pid_value)
        )
        res = getrecord(**kwargs)
        assert res.xpath("/x:OAI-PMH/x:GetRecord/x:record/x:header",namespaces=NAMESPACES)[0].attrib["status"] == "deleted"
        assert res.xpath("/x:OAI-PMH/x:GetRecord/x:record/x:header/x:identifier/text()",namespaces=NAMESPACES) == [record[2].pid_value]

        # system_identifier_doi is not exists
        record = create_record("9","xx",["1"],"2000-11-11","0",False,False)
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="GetRecord",
            identifier=str(record[2].pid_value)
        )
        res = getrecord(**kwargs)
        assert res.xpath("/x:OAI-PMH/x:GetRecord/x:record/x:header/x:identifier/text()",namespaces=NAMESPACES) == [record[2].pid_value]
        assert len(res.xpath("/x:OAI-PMH/x:GetRecord/x:record/x:metadata",namespaces=NAMESPACES)) == 1
        
        # system_identifier_doi is exists
        record = create_record("10","xx",["1"],"2000-11-11","0",False,False,True)
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="GetRecord",
            identifier=str(record[2].pid_value)
        )
        res = getrecord(**kwargs)
        assert res.xpath("/x:OAI-PMH/x:GetRecord/x:record/x:header/x:identifier/text()",namespaces=NAMESPACES) == [record[2].pid_value]
        assert len(res.xpath("/x:OAI-PMH/x:GetRecord/x:record/x:metadata",namespaces=NAMESPACES)) == 1

        # exception is raised
        record = create_record("11","xx",["1"],"2000-11-11","0",False,False)
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="GetRecord",
            identifier=str(record[2].pid_value)
        )
        with patch("invenio_oaiserver.response.pickle.loads",side_effect=Exception):
            res = getrecord(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "idDoesNotExist"



def test_getrecord_future_item(app,records,item_type,mock_execute,db,mocker):
    """Test of method which creates OAI-PMH response for verb GetRecord."""
    # publish_status = 0 (public item)
    # pubdate is future date
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
        with patch("invenio_oaiserver.query.OAIServerSearch.execute",return_value=mock_execute(dummy_data)):
            with patch("invenio_oaiserver.response.is_exists_doi",return_value=False):
                res = getrecord(**kwargs)
                header = res.xpath(
                    '/x:OAI-PMH/x:GetRecord/x:record/x:header[@status="deleted"]',
                    namespaces=NAMESPACES)
                assert len(header) == 1
            
            with patch("invenio_oaiserver.response.is_exists_doi",return_value=True):
                res = getrecord(**kwargs)
                assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "idDoesNotExist"

# def listidentifiers(**kwargs):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_listidentifiers -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_listidentifiers(es_app,records,item_type,mock_execute,db,mocker):
    with es_app.app_context():
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
            set="1557819692844",
        )
        dummy_data={
            "hits":{
                "total": 7,
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
                    {
                        "_source":{
                            "_oai":{"id":str(records[3][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[3][2].id,
                    },
                    {
                        "_source":{
                            "_oai":{"id":str(records[4][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[4][2].id,
                    },
                    {
                        "_source":{
                            "_oai":{"id":str(records[5][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[5][2].id,
                    },
                    {
                        "_source":{
                            "_oai":{"id":str(records[6][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[6][2].id,
                    },
                ]
            }
        }

        class MockPagenation():
            page = 1
            per_page = 100
            def __init__(self,dummy):
                self.data = dummy
                self.total = self.data["hits"]["total"]
            @cached_property
            def has_next(self):
                return self.page * self.per_page <= self.total

            @cached_property
            def next_num(self):
                return self.page + 1 if self.has_next else None
            @property
            def items(self):
                """Return iterator."""
                for result in self.data['hits']['hits']:
                    if '_oai' in result['_source']:
                        yield {
                            'id': result['_id'],
                            'json': result,
                            'updated': datetime.strptime(
                                result['_source']['_updated'][:19],
                                '%Y-%m-%dT%H:%M:%S'
                            ),
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
        with patch("invenio_oaiserver.response.get_records",return_value=MockPagenation(dummy_data)):
            # private index
            with patch("invenio_oaiserver.response.is_output_harvest",return_value=PRIVATE_INDEX):
                # not etree_reocrd.get("system_identifier_doi")
                with patch("invenio_oaiserver.response.is_exists_doi", return_value=False):
                    res=listidentifiers(**kwargs)
                    # total
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header', namespaces=NAMESPACES)) == 6
                    # future item
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[1]/x:identifier/text()', namespaces=NAMESPACES) == [str(records[0][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[1][@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # path is none
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[2]/x:identifier/text()', namespaces=NAMESPACES) == [str(records[1][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[2][@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = 0 (public item)
                    # has sys doi data
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[3]/x:identifier/text()', namespaces=NAMESPACES) == [str(records[2][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[3][@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = 0 (public item)
                    # not sys doi data
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[4]/x:identifier/text()', namespaces=NAMESPACES) == [str(records[3][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[4][@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = -1 (delete item)
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[5]/x:identifier/text()', namespaces=NAMESPACES) == [str(records[5][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[5][@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = 1 (private item)
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[6]/x:identifier/text()', namespaces=NAMESPACES) == [str(records[6][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[6][@status="deleted"]', namespaces=NAMESPACES)) == 1

                # etree_reocrd.get("system_identifier_doi")
                with patch("invenio_oaiserver.response.is_exists_doi", return_value=True):
                    res=listidentifiers(**kwargs)
                    # total
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header', namespaces=NAMESPACES)) == 1
                    # path is none
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[1]/x:identifier/text()', namespaces=NAMESPACES) == [str(records[1][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[1][@status="deleted"]', namespaces=NAMESPACES)) == 1

            # public index
            with patch("invenio_oaiserver.response.is_output_harvest",return_value=OUTPUT_HARVEST):
                # not etree_reocrd.get("system_identifier_doi")
                with patch("invenio_oaiserver.response.is_exists_doi",return_value=False):
                    res=listidentifiers(**kwargs)
                    # total
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header', namespaces=NAMESPACES)) == 6
                    # future item
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[1]/x:identifier/text()', namespaces=NAMESPACES) == [str(records[0][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[1][@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # path is none
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[2]/x:identifier/text()', namespaces=NAMESPACES) == [str(records[1][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[2][@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = 0 (public item)
                    # has sys doi data
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[3]/x:identifier/text()', namespaces=NAMESPACES) == [str(records[2][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[3][@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = 0 (public item)
                    # not sys doi data
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[4]/x:identifier/text()', namespaces=NAMESPACES) == [str(records[3][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[4][@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = -1 (delete item)
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[5]/x:identifier/text()', namespaces=NAMESPACES) == [str(records[5][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[5][@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = 1 (private item)
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[6]/x:identifier/text()', namespaces=NAMESPACES) == [str(records[6][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[6][@status="deleted"]', namespaces=NAMESPACES)) == 1

                # etree_reocrd.get("system_identifier_doi")
                with patch("invenio_oaiserver.response.is_exists_doi",return_value=True):
                    res=listidentifiers(**kwargs)
                    # total
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header', namespaces=NAMESPACES)) == 1
                    # path is none
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[1]/x:identifier/text()', namespaces=NAMESPACES) == [str(records[1][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[1][@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = 0 (public item)
                    # has sys doi data
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[2]/x:identifier/text()', namespaces=NAMESPACES) == []
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[2][@status="deleted"]', namespaces=NAMESPACES)) == 0
                    # publish_status = 0 (public item)
                    # not sys doi data
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[3]/x:identifier/text()', namespaces=NAMESPACES) == []
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[3][@status="deleted"]', namespaces=NAMESPACES)) == 0
                    # publish_status = -1 (delete item)
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[4]/x:identifier/text()', namespaces=NAMESPACES) == []
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[4][@status="deleted"]', namespaces=NAMESPACES)) == 0
                    # publish_status = 1 (private item)
                    assert res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[5]/x:identifier/text()', namespaces=NAMESPACES) == []
                    assert len(res.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header[5][@status="deleted"]', namespaces=NAMESPACES)) == 0


        # not identify
        with patch("invenio_oaiserver.response.OaiIdentify.get_all",return_value=None):
            res=listidentifiers(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"

        # output setting of identity = false 
        identify = Identify(
            outPutSetting=False
        )
        with patch("invenio_oaiserver.response.OaiIdentify.get_all",return_value=identify):
            res=listidentifiers(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"

        # not oaiset
        with patch("invenio_oaiserver.response.OAISet.get_set_by_spec",return_value=None):
            res=listidentifiers(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"

        # harvest setting of index = private
        with patch("invenio_oaiserver.response.is_output_harvest",return_value=HARVEST_PRIVATE):
            res=listidentifiers(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"

        # not data
        class MockResult:
            def __init__(self):
                pass
            @property
            def total(self):
                return None
        with patch("invenio_oaiserver.response.get_records",return_value=MockResult()):
            res=listidentifiers(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"

        # return Exception
        dummy_data={
            "hits":{
                "total": 1,
                "hits":[
                    {
                        "_source":{
                            "_oai":{"id":str(records[2][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[2][2].id,
                    }
                ]
            }
        }
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="ListIdentifiers",
        )
        with patch("invenio_oaiserver.response.get_records",return_value=MockPagenation(dummy_data)):
            # raise PIDDoesNotExistError
            with patch("invenio_oaiserver.response.OAIIDProvider.get",side_effect=PIDDoesNotExistError("test pid_type","test pid_value")):
                res=listidentifiers(**kwargs)
                assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"
            # raise NoResultFound
            with patch("invenio_oaiserver.response.WekoRecord.get_record_by_uuid",side_effect=NoResultFound()):
                res=listidentifiers(**kwargs)
                assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"
            # raise Exception
            with patch("invenio_oaiserver.response.WekoRecord.get_record_by_uuid",side_effect=Exception()):
                res=listidentifiers(**kwargs)
                assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"


# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_listrecords -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_listrecords(es_app,records,item_type,mock_execute,db,mocker):
    with es_app.app_context():
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
            set="1557819692844",
        )
        dummy_data={
            "hits":{
                "total": 7,
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
                    {
                        "_source":{
                            "_oai":{"id":str(records[3][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[3][2].id,
                    },
                    {
                        "_source":{
                            "_oai":{"id":str(records[4][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[4][2].id,
                    },
                    {
                        "_source":{
                            "_oai":{"id":str(records[5][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[5][2].id,
                    },
                    {
                        "_source":{
                            "_oai":{"id":str(records[6][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[6][2].id,
                    },
                ]
            }
        }

        class MockPagenation():
            page = 1
            per_page = 100
            def __init__(self,dummy):
                self.data = dummy
                self.total = self.data["hits"]["total"]
            @cached_property
            def has_next(self):
                return self.page * self.per_page <= self.total

            @cached_property
            def next_num(self):
                return self.page + 1 if self.has_next else None
            @property
            def items(self):
                """Return iterator."""
                for result in self.data['hits']['hits']:
                    if '_oai' in result['_source']:
                        yield {
                            'id': result['_id'],
                            'json': result,
                            'updated': datetime.strptime(
                                result['_source']['_updated'][:19],
                                '%Y-%m-%dT%H:%M:%S'
                            ),
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
        with patch("invenio_oaiserver.response.get_records",return_value=MockPagenation(dummy_data)):
            # private index
            with patch("invenio_oaiserver.response.is_output_harvest",return_value=PRIVATE_INDEX):
                # not etree_reocrd.get("system_identifier_doi")
                with patch("invenio_oaiserver.response.is_exists_doi", return_value=False):
                    res=listrecords(**kwargs)
                    # total
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record', namespaces=NAMESPACES)) == 6
                    # future item
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[1]/x:header/x:identifier/text()', namespaces=NAMESPACES) == [str(records[0][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[1]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # path is none
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[2]/x:header/x:identifier/text()', namespaces=NAMESPACES) == [str(records[1][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[2]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = 0 (public item)
                    # has sys doi data
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[3]/x:header/x:identifier/text()', namespaces=NAMESPACES) == [str(records[2][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[3]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = 0 (public item)
                    # not sys doi data
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[4]/x:header/x:identifier/text()', namespaces=NAMESPACES) == [str(records[3][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[4]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = -1 (delete item)
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[5]/x:header/x:identifier/text()', namespaces=NAMESPACES) == [str(records[5][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[5]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = 1 (private item)
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[6]/x:header/x:identifier/text()', namespaces=NAMESPACES) == [str(records[6][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[6]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 1

                # etree_reocrd.get("system_identifier_doi")
                with patch("invenio_oaiserver.response.is_exists_doi", return_value=True):
                    res=listrecords(**kwargs)
                    # total
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record', namespaces=NAMESPACES)) == 1
                    # path is none
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[1]/x:header/x:identifier/text()', namespaces=NAMESPACES) == [str(records[1][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[1]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 1

            # public index
            with patch("invenio_oaiserver.response.is_output_harvest",return_value=OUTPUT_HARVEST):
                # not etree_reocrd.get("system_identifier_doi")
                with patch("invenio_oaiserver.response.is_exists_doi",return_value=False):
                    res=listrecords(**kwargs)
                    # total
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record', namespaces=NAMESPACES)) == 6
                    # future item
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[1]/x:header/x:identifier/text()', namespaces=NAMESPACES) == [str(records[0][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[1]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # path is none
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[2]/x:header/x:identifier/text()', namespaces=NAMESPACES) == [str(records[1][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[2]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = 0 (public item)
                    # has sys doi data
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[3]/x:header/x:identifier/text()', namespaces=NAMESPACES) == [str(records[2][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[3]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = 0 (public item)
                    # not sys doi data
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[4]/x:header/x:identifier/text()', namespaces=NAMESPACES) == [str(records[3][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[4]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = -1 (delete item)
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[5]/x:header/x:identifier/text()', namespaces=NAMESPACES) == [str(records[5][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[5]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = 1 (private item)
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[6]/x:header/x:identifier/text()', namespaces=NAMESPACES) == [str(records[6][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[6]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 1

                # etree_reocrd.get("system_identifier_doi")
                with patch("invenio_oaiserver.response.is_exists_doi",return_value=True):
                    res=listrecords(**kwargs)
                    # total
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record', namespaces=NAMESPACES)) == 1
                    # path is none
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[1]/x:header/x:identifier/text()', namespaces=NAMESPACES) == [str(records[1][0])]
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[1]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 1
                    # publish_status = 0 (public item)
                    # has sys doi data
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[2]/x:header/x:identifier/text()', namespaces=NAMESPACES) == []
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[2]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 0
                    # publish_status = 0 (public item)
                    # not sys doi data
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[3]/x:header/x:identifier/text()', namespaces=NAMESPACES) == []
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[3]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 0
                    # publish_status = -1 (delete item)
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[4]/x:header/x:identifier/text()', namespaces=NAMESPACES) == []
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[4]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 0
                    # publish_status = 1 (private item)
                    assert res.xpath('/x:OAI-PMH/x:ListRecords/x:record[5]/x:header/x:identifier/text()', namespaces=NAMESPACES) == []
                    assert len(res.xpath('/x:OAI-PMH/x:ListRecords/x:record[5]/x:header[@status="deleted"]', namespaces=NAMESPACES)) == 0


        # not identify
        with patch("invenio_oaiserver.response.OaiIdentify.get_all",return_value=None):
            res=listrecords(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"

        # output setting of identity = false 
        identify = Identify(
            outPutSetting=False
        )
        with patch("invenio_oaiserver.response.OaiIdentify.get_all",return_value=identify):
            res=listrecords(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"

        # not oaiset
        with patch("invenio_oaiserver.response.OAISet.get_set_by_spec",return_value=None):
            res=listrecords(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"

        # harvest setting of index = private
        with patch("invenio_oaiserver.response.is_output_harvest",return_value=HARVEST_PRIVATE):
            res=listrecords(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"

        # not data
        class MockResult:
            def __init__(self):
                pass
            @property
            def total(self):
                return None
        with patch("invenio_oaiserver.response.get_records",return_value=MockResult()):
            res=listrecords(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"

        # return Exception
        dummy_data={
            "hits":{
                "total": 1,
                "hits":[
                    {
                        "_source":{
                            "_oai":{"id":str(records[2][0])},
                            "_updated":"2022-01-01T10:10:10"
                        },
                        "_id":records[2][2].id,
                    }
                ]
            }
        }
        kwargs = dict(
            metadataPrefix='jpcoar_1.0',
            verb="ListRecords",
        )
        with patch("invenio_oaiserver.response.get_records",return_value=MockPagenation(dummy_data)):
            # raise PIDDoesNotExistError
            with patch("invenio_oaiserver.response.OAIIDProvider.get",side_effect=PIDDoesNotExistError("test pid_type","test pid_value")):
                res=listrecords(**kwargs)
                assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"
            # raise NoResultFound
            with patch("invenio_oaiserver.response.WekoRecord.get_record_by_uuid",side_effect=NoResultFound()):
                res=listrecords(**kwargs)
                assert res.xpath("/x:OAI-PMH/x:error",namespaces=NAMESPACES)[0].attrib["code"] == "noRecordsMatch"


# def envelope(**kwargs):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_envelope -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_envelope(app):
    
    # OAISERVER_XSL_URL is None
    
    kwargs = {
        "verb":"ListRecords",
        "metadataPrefix":"jpcoar_1.0",
        "from_":datetime(2023,1,10,10,1,11),
        "until":datetime(2024,1,10,10,1,11),
        "resumptionToken":{"token":"test_token"},
        "url":"http://test.com"
    }
    tree, oaipmh = envelope(**kwargs)
    assert oaipmh
    root = tree.getroot()
    assert root.tag == "{http://www.openarchives.org/OAI/2.0/}OAI-PMH"
    request = root.xpath("//x:request",namespaces=NAMESPACES)
    test = {
        "verb":"ListRecords",
        "metadataPrefix":"jpcoar_1.0",
        "from_":"2023-01-10T10:01:11Z",
        "until":"2024-01-10T10:01:11Z",
        "resumptionToken":"test_token",
        "url":"http://test.com"
    }
    assert request[0].attrib == test
    
    # OAISERVER_XSL_URL is not None
    current_app.config.update(OAISERVER_XSL_URL="https://www.otherdomain.org/oai2.xsl")
    kwargs = {
        "verb":"ListRecords",
        "metadataPrefix":"jpcoar_1.0"
    }
    tree, oaipmh = envelope(**kwargs)
    assert oaipmh
    root = tree.getroot()
    test = {
        "verb":"ListRecords",
        "metadataPrefix":"jpcoar_1.0"
    }
    request = root.xpath("//x:request",namespaces=NAMESPACES)
    assert request[0].attrib == test
    assert request[0].text == "http://app/oai"


# def error(errors, **kwargs):
# def verb(**kwargs):
# def identify(**kwargs):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_identify -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_identify(app,db):
    tree_str = \
        '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">'\
        '<responseDate>2023-02-21T00:05:52Z</responseDate>'\
        '<request verb="ListRecords" metadataPrefix="jpcoar_1.0">http://app/oai</request>'\
        '<ListRecords />'\
        '</OAI-PMH>'
    
    # identify is none, commpression == ["identity"]
    tree = etree.fromstring(tree_str)
    e_element = SubElement(tree, etree.QName(NS_OAIPMH,"ListRecords"))
    with patch("invenio_oaiserver.response.verb",return_value=(tree, e_element)):
        result = identify()
        list_records = result.xpath("//x:ListRecords",namespaces=NAMESPACES)[1]
        assert list_records.xpath("./x:repositoryName",namespaces=NAMESPACES)[0].text == "Invenio-OAIServer"
        assert list_records.xpath("./x:baseURL",namespaces=NAMESPACES)[0].text == "http://app/oai"
        assert list_records.xpath("./x:protocolVersion",namespaces=NAMESPACES)[0].text == "2.0"
        assert list_records.xpath("./x:earliestDatestamp",namespaces=NAMESPACES)[0].text == "0001-01-01T00:00:00Z"
        assert list_records.xpath("./x:deletedRecord",namespaces=NAMESPACES)[0].text == "transient"
        assert list_records.xpath("./x:granularity",namespaces=NAMESPACES)[0].text == "YYYY-MM-DDThh:mm:ssZ"
    
    # identify is not none, commpression != ["identity"]
    current_app.config.update(OAISERVER_COMPRESSIONS=["not_identity"])
    iden = Identify(
        id=1,
        outPutSetting=True,
        emails="test@test.org",
        repositoryName="test_repository",
        earliestDatastamp=datetime(2023,1,10,10,2,33)
    )
    db.session.add(iden)
    db.session.commit()
    tree = etree.fromstring(tree_str)
    e_element = SubElement(tree, etree.QName(NS_OAIPMH,"ListRecords"))

    with patch("invenio_oaiserver.response.verb",return_value=(tree, e_element)):
        result = identify()
        list_records = result.xpath("//x:ListRecords",namespaces=NAMESPACES)[1]
        assert list_records.xpath("./x:repositoryName",namespaces=NAMESPACES)[0].text == "test_repository"
        assert list_records.xpath("./x:adminEmail",namespaces=NAMESPACES)[0].text == "test@test.org"
        assert list_records.xpath("./x:baseURL",namespaces=NAMESPACES)[0].text == "http://app/oai"
        assert list_records.xpath("./x:protocolVersion",namespaces=NAMESPACES)[0].text == "2.0"
        assert list_records.xpath("./x:earliestDatestamp",namespaces=NAMESPACES)[0].text == "2023-01-10T10:02:33Z"
        assert list_records.xpath("./x:deletedRecord",namespaces=NAMESPACES)[0].text == "transient"
        assert list_records.xpath("./x:granularity",namespaces=NAMESPACES)[0].text == "YYYY-MM-DDThh:mm:ssZ"
        assert list_records.xpath("./x:compression",namespaces=NAMESPACES)[0].text == "not_identity"
    

# def resumption_token(parent, pagination, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_resumption_token -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_resumption_token(app,db,without_oaiset_signals):
    kwargs = {
        "verb":"ListRecords",
        "metadataPrefix":"jpcoar_1.0"
    }
    tree_str = \
    '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">'\
    '<responseDate>2023-02-21T00:05:52Z</responseDate>'\
    '<request verb="ListRecords" metadataPrefix="jpcoar_1.0">http://app/oai</request>'\
    '<ListRecords />'\
    '</OAI-PMH>'
    
    oai = OAISet(id=1,
        spec='test',
        name='test_name',
        description='some test description',
        search_pattern='test search')
    
    db.session.add(oai)
    db.session.commit()
    # page == 1
    tree = etree.fromstring(tree_str)
    oai_sets = OAISet.query.paginate(page=1, per_page=100, error_out=False)
    result = resumption_token(tree,oai_sets,**kwargs)
    assert result == None
    
    oais = list()
    for i in range(2,101):
        oais.append(OAISet(id=i,
            spec='test{}'.format(i),
            name='test_name{}'.format(i),
            description='some test description',
            search_pattern='test search{}'.format(i)))
    db.session.add_all(oais)
    db.session.commit()
    # token is none
    with patch("invenio_oaiserver.response.serialize",return_value=None):
        tree = etree.fromstring(tree_str)
        oai_sets = OAISet.query.paginate(page=1, per_page=20, error_out=False)
        result = resumption_token(tree,oai_sets,**kwargs)
        request = tree.xpath("//x:resumptionToken",namespaces=NAMESPACES)
        assert request[0].attrib["cursor"] == "0"
        assert request[0].attrib["completeListSize"] == "100"
        assert request[0].text == None
    # token is not none
    with patch("invenio_oaiserver.response.serialize",return_value="test_token"):
        tree = etree.fromstring(tree_str)
        oai_sets = OAISet.query.paginate(page=3, per_page=20, error_out=False)
        result = resumption_token(tree,oai_sets,**kwargs)
        request = tree.xpath("//x:resumptionToken",namespaces=NAMESPACES)
        assert request[0].attrib["cursor"] == "40"
        assert request[0].attrib["completeListSize"] == "100"
        assert request[0].text == "test_token"
        
    
    # pagenation.total is false
    OAISet.query.delete()
    db.session.commit()
    with patch("invenio_oaiserver.response.serialize",return_value="test_token"):
        tree = etree.fromstring(tree_str)
        oai_sets = OAISet.query.paginate(page=3, per_page=10, error_out=False)
        result = resumption_token(tree,oai_sets,**kwargs)
        request = tree.xpath("//x:resumptionToken",namespaces=NAMESPACES)
        assert len(request[0].attrib) == 0
        assert request[0].text == "test_token"
    
# def listsets(**kwargs):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_listsets -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_listsets(app,db,without_oaiset_signals,mocker):
    mocker.patch("invenio_oaiserver.response.resumption_token")
    tree_str = \
        '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">'\
        '<responseDate>2023-02-21T00:05:52Z</responseDate>'\
        '<request verb="ListRecords" metadataPrefix="jpcoar_1.0">http://app/oai</request>'\
        '<ListRecords />'\
        '</OAI-PMH>'
        
    oai100 = OAISet(id=100, # exist description
        spec='100',
        name='test_name100',
        description='some test description',
        search_pattern='test search100')
    oai101 = OAISet(id=101, # not exist description
        spec='101',
        name='test_name101',
        search_pattern='test search101')
    db.session.add(oai100)
    db.session.add(oai101)
    db.session.commit()
    
    tree = etree.fromstring(tree_str)
    e_element = SubElement(tree, etree.QName(NS_OAIPMH,"ListRecords"))
    # is not exist index
    with patch("invenio_oaiserver.response.verb",return_value=(tree,e_element)):
        result = listsets()
        sets = result.xpath("//x:ListRecords[2]/x:set",namespaces=NAMESPACES)
        set100 = sets[0]
        assert set100.xpath("./x:setSpec[1]",namespaces=NAMESPACES)[0].text == "100"
        assert set100.xpath("./x:setName[1]",namespaces=NAMESPACES)[0].text == "test_name100"
        desc = set100.xpath("./x:setDescription[1]/y:dc[1]/z:description",namespaces=NAMESPACES)[0]
        assert desc.text == "some test description"
        set101 = sets[1]
        assert set101.xpath("./x:setSpec[1]",namespaces=NAMESPACES)[0].text == "101"
        assert set101.xpath("./x:setName[1]",namespaces=NAMESPACES)[0].text == "test_name101"
        assert set101.xpath("./x:setDescription[1]/y:dc[1]/z:description",namespaces=NAMESPACES) == []

    # exist index
    index1 = Index(
        id=1,
        parent=0,
        position=1,
        index_name_english="test_index1",
        index_link_name_english="test_index_link1",
        harvest_public_state=False,
        public_state=False,
        browsing_role="3,-99"
    )
    index2 = Index(
        id=2,
        parent=0,
        position=2,
        index_name_english="test_index2",
        index_link_name_english="test_index_link2",
        harvest_public_state=True,
        public_state=True,
        browsing_role="3,-99"
    )
    db.session.add(index1)
    db.session.add(index2)
    OAISet.query.delete()
    oai1 = OAISet(id=1,
        spec='1',
        name='test_name1',
        search_pattern='test search1')
    oai2 = OAISet(id=2,
        spec='2',
        name='test_name2',
        search_pattern='test search2')
    db.session.add_all([oai1,oai2])
    db.session.commit()
    tree = etree.fromstring(tree_str)
    e_element = SubElement(tree, etree.QName(NS_OAIPMH,"ListRecords"))
    
    with patch("invenio_oaiserver.response.verb",return_value=(tree,e_element)):
        with patch("invenio_oaiserver.response.Indexes.is_public_state",side_effect=[None,True,True,True]):
            with patch("invenio_oaiserver.response.Indexes.get_harvest_public_state",side_effect=[False,False]):
                result = listsets()
                sets = result.xpath("//x:ListRecords[2]/x:set",namespaces=NAMESPACES)
                assert len(sets) == 1
                set1 = sets[0]
                assert set1.xpath("//x:setSpec[1]",namespaces=NAMESPACES)[0].text == "1"
                assert set1.xpath("//x:setName[1]",namespaces=NAMESPACES)[0].text == "test_name1"
                assert set1.xpath("//x:setDescription[1]/y:dc[1]/z:description",namespaces=NAMESPACES) == []

# def listmetadataformats(**kwargs):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_listmetadataformats -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_listmetadataformats(app,db,mocker):
    oai_metadata_format = {'oai_dc': {'serializer': ('invenio_oaiserver.utils:dumps_etree', {'xslt_filename': '/code/modules/invenio-oaiserver/invenio_oaiserver/static/xsl/MARC21slim2OAIDC.xsl'}), 'schema': 'http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd', 'namespace': 'http://www.w3.org/2001/XMLSchema'}, 'marc21': {'serializer': ('invenio_oaiserver.utils:dumps_etree', {'prefix': 'marc'}), 'schema': 'http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd', 'namespace': 'http://www.loc.gov/MARC21/slim'}, 'ddi': {'namespace': 'ddi:codebook:2_5', 'schema': 'https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd', 'serializer': ('invenio_oaiserver.utils:dumps_etree', {'schema_type': 'ddi'})}, 'jpcoar_v1': {'namespace': 'https://github.com/JPCOAR/schema/blob/master/1.0/', 'schema': 'https://github.com/JPCOAR/schema/blob/master/1.0/jpcoar_scm.xsd', 'serializer': ('invenio_oaiserver.utils:dumps_etree', {'schema_type': 'jpcoar_v1'})}, 'jpcoar': {'namespace': 'https://github.com/JPCOAR/schema/blob/master/2.0/', 'schema': 'https://github.com/JPCOAR/schema/blob/master/2.0/jpcoar_scm.xsd', 'serializer': ('invenio_oaiserver.utils:dumps_etree', {'schema_type': 'jpcoar'})}}
    oai_url = "http://test.oai/1"
    PersistentIdentifier.create('oai',oai_url,object_type='rec', pid_provider="oai",object_uuid=uuid.uuid4(),status=PIDStatus.REGISTERED)
    tree_str = \
        '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">'\
        '<responseDate>2023-02-21T00:05:52Z</responseDate>'\
        '<request verb="ListRecords" metadataPrefix="jpcoar_1.0">http://app/oai</request>'\
        '<ListRecords />'\
        '</OAI-PMH>'
    tree = etree.fromstring(tree_str)
    e_element = SubElement(tree, etree.QName(NS_OAIPMH,"ListRecords"))
    # is not exist index
    with patch("invenio_oaiserver.response.verb",return_value=(tree,e_element)):
        with patch("invenio_oaiserver.response.get_oai_metadata_formats",return_value=oai_metadata_format):
            kwargs = {"identifier":oai_url}
            result = listmetadataformats(**kwargs)
            metadata_format = result.xpath("//x:ListRecords[2]/x:metadataFormat",namespaces=NAMESPACES)
            for format in metadata_format:
                prefix = format.xpath("./x:metadataPrefix",namespaces=NAMESPACES)[0].text
                assert prefix in list(oai_metadata_format.keys())
                assert format.xpath("./x:schema",namespaces=NAMESPACES)[0].text == oai_metadata_format[prefix]["schema"]
                assert format.xpath("./x:metadataNamespace",namespaces=NAMESPACES)[0].text == oai_metadata_format[prefix]["namespace"]
    tree = etree.fromstring(tree_str)
    e_element = SubElement(tree, etree.QName(NS_OAIPMH,"ListRecords"))
    with patch("invenio_oaiserver.response.verb",return_value=(tree,e_element)):
        with patch("invenio_oaiserver.response.get_oai_metadata_formats",return_value={}):
            result = listmetadataformats()
            error = result.xpath("//x:error[1]",namespaces=NAMESPACES)[0]
            assert error.attrib["code"] == "noMetadataFormats"
            assert error.text == "There is no metadata format available."

# def header(parent, identifier, datestamp, sets=[], deleted=False):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_header -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_header(client,db,users):
    #client.post(url_for("security.login",data = {"email":users[0]["email"],"password":users[0]["obj"].password_plaintext}))
    with patch("flask_login.utils._get_user", return_value=users[0]['obj']):

        tree_str = \
            '<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd">'\
            '<responseDate>2023-02-21T00:05:52Z</responseDate>'\
            '<request verb="ListRecords" metadataPrefix="jpcoar_1.0">http://app/oai</request>'\
            '</OAI-PMH>'

        index1 = Index(
            id=2,
            parent=1,
            position=1,
            index_name_english="test_index1",
            index_link_name_english="test_index_link1",
            harvest_public_state=True,
            public_state=True,
            browsing_role="3,-99"
        )
        index2 = Index(
            id=3,
            parent=1,
            position=2,
            index_name_english="test_index2",
            index_link_name_english="test_index_link2",
            harvest_public_state=False,
            public_state=True,
            browsing_role="3,-99"
        )
        db.session.add_all([index1,index2])
        db.session.commit()
        # deleted is False, sets is exist
        tree = etree.fromstring(tree_str)
        e_element = SubElement(tree, etree.QName(NS_OAIPMH,"ListRecords"))
        sets = ["2","3","4"]
        result = header(e_element,"ListRecords",datetime(2023,1,10,1,11,11),sets,False)
        headers = tree.xpath("//x:ListRecords/x:header",namespaces=NAMESPACES)[0]
        assert headers.xpath("./x:identifier",namespaces=NAMESPACES)[0].text == "ListRecords"
        assert headers.xpath("./x:datestamp",namespaces=NAMESPACES)[0].text == "2023-01-10T01:11:11Z"
        setSpecs = headers.xpath("./x:setSpec",namespaces=NAMESPACES)
        assert setSpecs[0].text == "1:2"
        assert setSpecs[1].text == "4"
        
        # deleted is True, sets is not exist
        tree = etree.fromstring(tree_str)
        e_element = SubElement(tree, etree.QName(NS_OAIPMH,"ListRecords"))
        result = header(e_element,"ListRecords",datetime(2023,1,10,1,11,11),[],True)
        headers = tree.xpath("//x:ListRecords/x:header",namespaces=NAMESPACES)[0]
        assert headers.attrib["status"] == "deleted"
        assert headers.xpath("./x:identifier",namespaces=NAMESPACES)[0].text == "ListRecords"
        assert headers.xpath("./x:datestamp",namespaces=NAMESPACES)[0].text == "2023-01-10T01:11:11Z"
        assert len(headers.xpath("./x:setSpec",namespaces=NAMESPACES)) == 0        
        
        
# def extract_paths_from_sets(sets):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_extract_paths_from_sets -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_extract_paths_from_sets(app,db):
    index = Index(
        id=1,
        parent=0,
        position=1,
        index_name_english="test_index",
        index_link_name_english="test_index_link",
        harvest_public_state=True,
        public_state=True,
        browsing_role="3,-99"
    )
    db.session.add(index)
    db.session.commit()
    
    data = ["1","2","3"]
    
    paths, sets = extract_paths_from_sets(data)
    assert paths == ["1"]
    assert sets == ["2","3"]

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
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_is_private_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_is_private_index(app,db):
    with patch("invenio_oaiserver.response.Indexes.is_public_state_and_not_in_future",return_value=False):
        result = is_private_index({"path":["1","2"]})
        assert result == True
        
# def is_private_index_by_public_list(item_path, public_index_ids):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_is_private_index_by_public_list -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_is_private_index_by_public_list():
    item_path = ["1","2","3"]
    public_ids = ["2","3","4"]
    result = is_private_index_by_public_list(item_path, public_ids)
    assert result == False
    
    item_path = ["1","2","3"]
    public_ids = ["4","5","6"]
    result = is_private_index_by_public_list(item_path, public_ids)
    assert result == True

# def set_identifier(param_record, param_rec):
# def is_exists_doi(param_record):

# def get_error_code_msg(code=''):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_get_error_code_msg -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_get_error_code_msg(app):
    result = get_error_code_msg()
    assert result == [("noRecordsMatch","The combination of the values of the from, until, set and metadataPrefix arguments results in an empty list.")]
    
    result = get_error_code_msg("noMetadataFormats")
    assert result == [("noMetadataFormats","There is no metadata format available.")]
    
    result = get_error_code_msg("otherError")
    assert result == [("otherError","")]
    
# def create_identifier_index(root, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_create_identifier_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_create_identifier_index(app):
    NS = {
        "jpcoar": NS_JPCOAR
    }
    
    # jpcoar:identifierRegistration is exist
    tree = Element(etree.QName(NS_OAIPMH,"Root"),nsmap=NS)
    SubElement(tree,etree.QName(NS_JPCOAR,"identifierRegistration"),nsmap=NS)
    kwargs={"pid_type":"test","pid_value":"test_pid"}
    result = create_identifier_index(tree,**kwargs)
    identifier = result.xpath("./jpcoar:identifier",namespaces=NS)[0]
    assert identifier.attrib == {"identifierType":"TEST"}
    assert identifier.text == "test_pid"
    assert [r.tag for r in result ] == ["{https://irdb.nii.ac.jp/schema/jpcoar/1.0/}identifier","{https://irdb.nii.ac.jp/schema/jpcoar/1.0/}identifierRegistration"]

    # jpcoar:identifierRegistration is not exist
    tree = Element(etree.QName(NS_OAIPMH,"Root"),nsmap=NS)
    result = create_identifier_index(tree,**kwargs)
    identifier = result.xpath("./jpcoar:identifier",namespaces=NS)[0]
    assert identifier.attrib == {"identifierType":"TEST"}
    assert identifier.text == "test_pid"
    assert [r.tag for r in result ] == ["{https://irdb.nii.ac.jp/schema/jpcoar/1.0/}identifier"]

    # raise Exception
    with patch("invenio_oaiserver.response.Element",side_effect=Exception("test_error")):
        tree = Element(etree.QName(NS_OAIPMH,"Root"),nsmap=NS)
        result = create_identifier_index(tree,**kwargs)
        assert [r.tag for r in result ] == []

# def check_correct_system_props_mapping(object_uuid, system_mapping_config):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_check_correct_system_props_mapping -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_check_correct_system_props_mapping(app,db, item_type):
    obj_uuid = uuid.uuid4()
    item_metadata1 = ItemMetadata(id=obj_uuid,item_type_id=1,json={})
    mapping_data = {
        "ITEM1":{"jpcoar_mapping":{"item1":{"subitem1_1":"item1.subitem1_1","subitem2_1":"item1.subitem2_1"}}},
        "ITEM2":{"jpcoar_mapping":{"item2":{"subitem1_2":{"subitem1_1_2":"item2.subitem1_2.subitem1_1_2"},"subitem2_2":{"subitem1_2_2":"item2.subitem2_2.subitem1_2_2"}}}}
    }
    mapping1 = ItemTypeMapping(item_type_id=1,mapping=mapping_data)
    db.session.add_all([item_metadata1,mapping1])
    db.session.commit()
    # item_map
    #{'item1.subitem1_1': 'ITEM1.item1.subitem1_1', 
    # 'item1.subitem2_1': 'ITEM1.item1.subitem2_1', 
    # 'item2.subitem1_2.subitem1_1_2': 'ITEM2.item2.subitem1_2.subitem1_1_2', 
    # 'item2.subitem2_2.subitem1_2_2': 'ITEM2.item2.subitem2_2.subitem1_2_2'}
    
    # pass check
    system_mapping_config={"item1.subitem1_1":"ITEM1.item1.subitem1_1","item2.subitem1_2.subitem1_1_2": "ITEM2.item2.subitem1_2.subitem1_1_2"}
    result = check_correct_system_props_mapping(obj_uuid,system_mapping_config)
    assert result == False
    
    # not pass check
    system_mapping_config={"item1.subitem1_1":"ITEM1.item1.subitem1_1","item2.subitem1_2.subitem1_1_2":"not_exist_system_value"}
    result = check_correct_system_props_mapping(obj_uuid,system_mapping_config)
    assert result == False
    
    # system_mapping_config is none
    result = check_correct_system_props_mapping(obj_uuid,{})
    assert result == False
        
# def combine_record_file_urls(record, object_uuid, meta_prefix):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_combine_record_file_urls -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_combine_record_file_urls(app,db,mocker):
    metadata_formats = {
        'jpcoar_1.0': {'serializer': ('weko_schema_ui.utils:dumps_oai_etree', {'schema_type': 'jpcoar_v1'}), 'namespace': 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/', 'schema': 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/jpcoar_scm.xsd'},
        'jpcoar': {'serializer': ('weko_schema_ui.utils:dumps_oai_etree', {'schema_type': 'jpcoar'}), 'namespace': 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/', 'schema': 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/jpcoar_scm.xsd'}
    }
    mocker.patch("weko_schema_ui.schema.get_oai_metadata_formats",return_value=metadata_formats)
    
    mapping_data1 = {
        "item_1617605131499": {
            "jpcoar_mapping": {
                "file": {
                    "URI": {
                        "@value": "url.url",
                        "@attributes": {
                            "label": "url.label",
                            "objectType": "url.objectType"
                        }
                    },
                    "date": {
                        "@value": "fileDate.fileDateValue",
                        "@attributes": { "dateType": "fileDate.fileDateType" }
                    },
                    "extent": { "@value": "filesize.value" },
                    "version": { "@value": "version" },
                    "mimeType": { "@value": "format" }
                }
            },
            "jpcoar_v1_mapping": {
                "file": {
                    "URI": {
                        "@value": "url.url",
                        "@attributes": {
                            "label": "url.label",
                            "objectType": "url.objectType"
                        }
                    },
                    "date": {
                        "@value": "fileDate.fileDateValue",
                        "@attributes": { "dateType": "fileDate.fileDateType" }
                    },
                    "extent": { "@value": "filesize.value" },
                    "version": { "@value": "version" },
                    "mimeType": { "@value": "format" }
                }
            }
        }
    }
    mapping_data2 = { # len(file_keys) != 3
        "item_1617605131499": {
            "jpcoar_mapping": {
                "file": {
                    "URI": {
                        "@value": "url",
                        "@attributes": {
                            "label": "url.label",
                            "objectType": "url.objectType"
                        }
                    },
                    "date": {
                        "@value": "fileDate.fileDateValue",
                        "@attributes": { "dateType": "fileDate.fileDateType" }
                    },
                    "extent": { "@value": "filesize.value" },
                    "version": { "@value": "version" },
                    "mimeType": { "@value": "format" }
                }
            },
            "jpcoar_v1_mapping": {
                "file": {
                    "URI": {
                        "@value": "url.url",
                        "@attributes": {
                            "label": "url.label",
                            "objectType": "url.objectType"
                        }
                    },
                    "date": {
                        "@value": "fileDate.fileDateValue",
                        "@attributes": { "dateType": "fileDate.fileDateType" }
                    },
                    "extent": { "@value": "filesize.value" },
                    "version": { "@value": "version" },
                    "mimeType": { "@value": "format" }
                }
            }
        }
    }
    item_type_name=ItemTypeName(name="test")
    render={
        "meta_fix":{},
        "meta_list":{},
        "table_row": []
    }
    ItemTypes.create(
        name='test1',
        item_type_name=item_type_name,
        schema={},
        render=render,
        form={},
        tag=1
    )
    ItemTypes.create(
        name='test2',
        item_type_name=item_type_name,
        schema={},
        render=render,
        form={},
        tag=1
    )
    ItemTypes.create(
        name='test3',
        item_type_name=item_type_name,
        schema={},
        render=render,
        form={},
        tag=1
    )
    mapping1 = ItemTypeMapping(item_type_id=1,mapping=mapping_data1)
    mapping2 = ItemTypeMapping(item_type_id=2,mapping=mapping_data2)
    mapping3 = ItemTypeMapping(item_type_id=3,mapping={})

    db.session.add_all([mapping1,mapping2,mapping3])
    
    record_data1 = {
        "recid":"1",
        "item_1617605131499":{
            "attribute_name":"File",
            "attribute_type":"file",
            "attribute_value_mlt":[ # attribute_value_mlt is list
                { # not exist filename
                    "url":{"url":"https://weko3.example.org/record/1/files/sample_file1"}
                },
                { # not exist file_keys[1]
                    "filename":"sample_file2"
                },
                { # exist file_keys[1]
                    "url":{"url":"https://weko3.example.org/record/1/files/sample_file3"},
                    "filename":"sample_file3"
                }
            ]
        }
    }
    record_data2 = {
        "recid":"2",
        "item_1617605131499":{
            "attribute_name":"File",
            "attribute_type":"file",
            "attribute_value_mlt":{ # attribute_value_mlt is dict
                "filename":"sample_file" # not exist file_keys[1]
            }
        }
    }
    record_data3 = {
        "recid":"3",
        "item_1617605131499":{
            "attribute_name":"File",
            "attribute_type":"file",
            "attribute_value_mlt":{ # attribute_value_mlt is dict
                # exist file_keys[1]
                "url":{"url":"https://weko3.example.org/record/3/files/sample_file"},
                "filename":"sample_file"
            }
        }
    }
    record_data4 = {
        "recid":"4",
        "item_1617605131499":{
            "attribute_name":"File",
            "attribute_type":"file",
            "attribute_value_mlt":{ # attribute_value_mlt is dict
                # not exist filename
                "url":{"url":"https://weko3.example.org/record/4/files/sample_file"},
            }
        }
    }
    record_data5 = {
        "recid":"5",
        "item_1617605131499":{
            "attribute_name":"File",
            "attribute_type":"file",
            "attribute_value_mlt":{ # attribute_value_mlt is dict
                # not exist filename
                "url":"https://weko3.example.org/record/4/files/sample_file",
            }
        }
    }

    rec_uuid1 = uuid.uuid4()
    record1 = WekoRecord.create(record_data1, id_=rec_uuid1)
    item_metadata1 = ItemMetadata(id=rec_uuid1,item_type_id=1,json={})

    rec_uuid2 = uuid.uuid4()
    record2 = WekoRecord.create(record_data2, id_=rec_uuid2)
    item_metadata2 = ItemMetadata(id=rec_uuid2,item_type_id=1,json={})

    rec_uuid3 = uuid.uuid4()
    record3 = WekoRecord.create(record_data3, id_=rec_uuid3)
    item_metadata3 = ItemMetadata(id=rec_uuid3,item_type_id=1,json={})

    rec_uuid4 = uuid.uuid4()
    record4 = WekoRecord.create(record_data4, id_=rec_uuid4)
    item_metadata4 = ItemMetadata(id=rec_uuid4,item_type_id=1,json={})

    rec_uuid5 = uuid.uuid4()
    record5 = WekoRecord.create(record_data5, id_=rec_uuid5)
    item_metadata5 = ItemMetadata(id=rec_uuid5,item_type_id=2,json={}
                                  )
    rec_uuid6 = uuid.uuid4()
    item_metadata6 = ItemMetadata(id=rec_uuid6,item_type_id=3,json={})
    
    db.session.add_all([item_metadata1,item_metadata2,item_metadata3,item_metadata4,item_metadata5,item_metadata6])
    db.session.commit()
    
    with app.test_request_context():
        # not item_map
        result = combine_record_file_urls(record1,rec_uuid6,"jpcoar_1.0")
        assert result == record1

        # mapping_type not in file_props
        result = combine_record_file_urls(record1,rec_uuid1,"jpcoar_1.0")
        assert result == record1
        
        # attribute_value_mlt is list
        # not exist filename, url.url is not exist, url.url is exist
        test = {'recid': '1', 'item_1617605131499': {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': [{'url': {'url': 'https://weko3.example.org/record/1/files/sample_file1'}}, {'filename': 'sample_file2'}, {'url': {'url': 'https://weko3.example.org/record/1/files/sample_file3'}, 'filename': 'sample_file3'}]}}
        result = combine_record_file_urls(record1,rec_uuid1,"jpcoar")
        assert result == test

        # len(file_keys) != 3
        test = {'recid': '5', 'item_1617605131499': {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': {'url': 'https://weko3.example.org/record/4/files/sample_file'}}}
        result = combine_record_file_urls(record5,rec_uuid5,"jpcoar")
        assert result == test
        
        # attribute_value_mlt is list
        ## url.url is not exist
        test = {'recid': '2', 'item_1617605131499': {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': {'filename': 'sample_file'}}}
        result = combine_record_file_urls(record2,rec_uuid2,"jpcoar")
        assert result == test
        
        ## url.url is exist
        test = {'recid': '3', 'item_1617605131499': {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': {'url': {'url': 'https://weko3.example.org/record/3/files/sample_file'}, 'filename': 'sample_file'}}}
        result = combine_record_file_urls(record3,rec_uuid3,"jpcoar")
        assert result == test
        
        ## filename is not exist
        test = {'recid': '4', 'item_1617605131499': {'attribute_name': 'File', 'attribute_type': 'file', 'attribute_value_mlt': {'url': {'url': 'https://weko3.example.org/record/4/files/sample_file'}}}}
        result = combine_record_file_urls(record4,rec_uuid4,"jpcoar")
        assert result == test

# def create_files_url(root_url, record_id, filename):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_create_files_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_create_files_url():
    result = create_files_url(root_url="http://root/",record_id=1,filename="test_file")
    assert result == "http://root/record/1/files/test_file"
    
# def get_identifier(record):
# 
def test_get_identifier(app,db):

    record_data1 = {"_deposit":{"id":"1"}}
    rec_uuid1 = uuid.uuid4()
    record1 = WekoRecord.create(record_data1, id_=rec_uuid1)
    recid1 = PersistentIdentifier.create('recid', "1",object_type='rec', object_uuid=rec_uuid1,status=PIDStatus.REGISTERED)
    parent1 = PersistentIdentifier.create('parent', "parent:{}".format("1"),object_type='rec', object_uuid=rec_uuid1,status=PIDStatus.REGISTERED)
    PIDRelation.create(parent1, recid1,2,0)
    
    record_data2 = {"_deposit":{"id":"2"}}
    rec_uuid2 = uuid.uuid4()
    record2 = WekoRecord.create(record_data2, id_=rec_uuid2)
    recid2 = PersistentIdentifier.create('recid', "2",object_type='rec', object_uuid=rec_uuid2,status=PIDStatus.REGISTERED)
    parent2 = PersistentIdentifier.create('parent', "parent:{}".format("2"),object_type='rec', object_uuid=rec_uuid2,status=PIDStatus.REGISTERED)
    PIDRelation.create(parent2, recid2,2,0)
    doi_url = "http://doi:{}".format(rec_uuid2)
    hdl_url = "http://hdl:{}".format(rec_uuid2)
    PersistentIdentifier.create('doi',doi_url,object_type='rec', pid_provider="oai",object_uuid=rec_uuid2,status=PIDStatus.REGISTERED)
    PersistentIdentifier.create('hdl',hdl_url,object_type='rec', pid_provider="oai",object_uuid=rec_uuid2,status=PIDStatus.REGISTERED)
    
    with app.test_request_context():
        # all false
        test = {"attribute_name":"Identifier","attribute_value_mlt":[]}
        result = get_identifier(record1)
        assert result == test

        # all true
        current_app.config.update(WEKO_SCHEMA_RECORD_URL="{}records/{}")
        test = {
            "attribute_name":"Identifier",
            "attribute_value_mlt":[
                {"subitem_systemidt_identifier":doi_url,"subitem_systemidt_identifier_type":"DOI"},
                {"subitem_systemidt_identifier":hdl_url,"subitem_systemidt_identifier_type":"HDL"},
                {"subitem_systemidt_identifier":"http://app/records/2","subitem_systemidt_identifier_type":"URI"},
            ]
        }
        result = get_identifier(record2)

        assert result == test

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_issue34851_listrecords -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_issue34851_listrecords(es_app, records, item_type, mock_execute,db,mocker):
    with es_app.app_context():
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
        class MockPagenation():
            page = 1
            per_page = 100
            def __init__(self,dummy):
                self.data = dummy
                self.total = self.data["hits"]["total"]
            @cached_property
            def has_next(self):
                return self.page * self.per_page <= self.total

            @cached_property
            def next_num(self):
                return self.page + 1 if self.has_next else None
            @property
            def items(self):
                """Return iterator."""
                for result in self.data['hits']['hits']:
                    if '_oai' in result['_source']:
                        yield {
                            'id': result['_id'],
                            'json': result,
                            'updated': datetime.strptime(
                                result['_source']['_updated'][:19],
                                '%Y-%m-%dT%H:%M:%S'
                            ),
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
        with patch("invenio_oaiserver.response.get_records",return_value=MockPagenation(dummy_data)):
            res=listrecords(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:ListRecords/x:record[1]/x:header/x:datestamp/text()",namespaces=NAMESPACES) == [records[1][2].updated.replace(microsecond=0).isoformat()+"Z"]
            assert res.xpath("/x:OAI-PMH/x:ListRecords/x:record[2]/x:header/x:datestamp/text()",namespaces=NAMESPACES) == [records[2][2].updated.replace(microsecond=0).isoformat()+"Z"]


# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_response.py::test_issue34851_listidentifiers -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_issue34851_listidentifiers(es_app, records, item_type, mock_execute,db,mocker):
    with es_app.app_context():
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
        class MockPagenation():
            page = 1
            per_page = 100
            def __init__(self,dummy):
                self.data = dummy
                self.total = self.data["hits"]["total"]
            @cached_property
            def has_next(self):
                return self.page * self.per_page <= self.total

            @cached_property
            def next_num(self):
                return self.page + 1 if self.has_next else None
            @property
            def items(self):
                """Return iterator."""
                for result in self.data['hits']['hits']:
                    if '_oai' in result['_source']:
                        yield {
                            'id': result['_id'],
                            'json': result,
                            'updated': datetime.strptime(
                                result['_source']['_updated'][:19],
                                '%Y-%m-%dT%H:%M:%S'
                            ),
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
        with patch("invenio_oaiserver.response.get_records",return_value=MockPagenation(dummy_data)):
            res=listidentifiers(**kwargs)
            assert res.xpath("/x:OAI-PMH/x:ListIdentifiers/x:header[1]/x:datestamp/text()",namespaces=NAMESPACES) == [records[1][2].updated.replace(microsecond=0).isoformat()+"Z"]
            assert res.xpath("/x:OAI-PMH/x:ListIdentifiers/x:header[2]/x:datestamp/text()",namespaces=NAMESPACES) == [records[2][2].updated.replace(microsecond=0).isoformat()+"Z"]
