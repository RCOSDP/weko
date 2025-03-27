
from mock import patch
import copy
import pytest
from datetime import datetime
from flask import current_app
from lxml import etree

from weko_index_tree.api import Indexes

from invenio_oaiserver.utils import (
    serializer,
    dumps_etree,
    datetime_to_datestamp,
    eprints_description,
    handle_license_free,
    get_index_state,
    is_output_harvest,
    get_community_index_from_set
)

from tests.helpers import create_record2
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp


#def serializer(metadata_prefix):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_utils.py::test_serializer -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_serializer(app,mocker):
    metadata_format = {
        "oai_dc": {
            "serializer": ("invenio_oaiserver.utils:dumps_etree", {"xslt_filename": "/code/modules/invenio-oaiserver/invenio_oaiserver/static/xsl/MARC21slim2OAIDC.xsl"}), 
            "schema": "http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd", 
            "namespace": "http://www.w3.org/2001/XMLSchema"
        },
        "ddi": {
            "namespace": "ddi:codebook:2_5", 
            "schema": "https://ddialliance.org/Specification/DDI-Codebook/2.5/XMLSchema/codebook.xsd", 
            "serializer": "invenio_oaiserver.utils:dumps_etree"
        }, 
    }
    mocker.patch("invenio_oaiserver.utils.get_oai_metadata_formats",return_value=metadata_format)
    result = serializer("oai_dc")
    
    # serializer_ is tuple
    assert result.func.__name__ == "dumps_etree"
    assert result.keywords == {"xslt_filename": "/code/modules/invenio-oaiserver/invenio_oaiserver/static/xsl/MARC21slim2OAIDC.xsl"}
    
    # serializer_ is not tuple
    result = serializer("ddi")
    assert result.__name__ == "dumps_etree"
    
#def dumps_etree(pid, record, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_utils.py::test_dumps_etree -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_dumps_etree(app, db):
    data = {
        "recid":"1",
        "_source":{
            "_updated":"2022-01-01T10:10:10"
        },
        "_id":1
    }
    recid, depid, record, item, parent, oai = create_record2(data,data)
    result = dumps_etree(recid, record)
    assert str(etree.tostring(result),"utf-8") == '<record xmlns="http://www.loc.gov/MARC21/slim"/>'


#def datetime_to_datestamp(dt, day_granularity=False):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_utils.py::test_datetime_to_datestamp -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_datetime_to_datestamp():
    dt = datetime(2023,1,10,1,2,3,456)
    result = datetime_to_datestamp(dt)
    assert result == "2023-01-10T01:02:03Z"
    result = datetime_to_datestamp(dt,True)
    assert result == "2023-01-10"
    
#def eprints_description(metadataPolicy, dataPolicy,
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_utils.py::test_eprints_description -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_eprints_description():
    metadataPolicy = {'text': 'Metadata can be used by commercial'
                      'and non-commercial service providers',
                      'URL': 'http://arXiv.org/arXiv_metadata_use.htm'}
    dataPolicy = {'text': 'Full content, i.e. preprints may'
                  'not be harvested by robots'}
    content = {'URL': 'http://arXiv.org/arXiv_content.htm'}
    submissionPolicy = {'URL': 'http://arXiv.org/arXiv_submission.htm'}
    result = eprints_description(metadataPolicy, dataPolicy,submissionPolicy, content),
    assert str(result[0],"utf-8") == '<eprints xmlns="http://www.openarchives.org/OAI/2.0/eprints" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/eprints http://www.openarchives.org/OAI/2.0/eprints.xsd">\n  <content>\n    <URL>http://arXiv.org/arXiv_content.htm</URL>\n  </content>\n  <metadataPolicy>\n    <text>Metadata can be used by commercialand non-commercial service providers</text>\n    <URL>http://arXiv.org/arXiv_metadata_use.htm</URL>\n  </metadataPolicy>\n  <dataPolicy>\n    <text>Full content, i.e. preprints maynot be harvested by robots</text>\n  </dataPolicy>\n  <submissionPolicy>\n    <URL>http://arXiv.org/arXiv_submission.htm</URL>\n  </submissionPolicy>\n</eprints>\n'
    
    
    result = eprints_description(metadataPolicy, dataPolicy)

    assert str(result,"utf-8") == '<eprints xmlns="http://www.openarchives.org/OAI/2.0/eprints" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/eprints http://www.openarchives.org/OAI/2.0/eprints.xsd">\n  <metadataPolicy>\n    <text>Metadata can be used by commercialand non-commercial service providers</text>\n    <URL>http://arXiv.org/arXiv_metadata_use.htm</URL>\n  </metadataPolicy>\n  <dataPolicy>\n    <text>Full content, i.e. preprints maynot be harvested by robots</text>\n  </dataPolicy>\n</eprints>\n'


#def oai_identifier_description(scheme, repositoryIdentifier,
#    For the full specification and schema definition visit:
#def friends_description(baseURLs):
#    For the schema definition visit:
#def handle_license_free(record_metadata):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_utils.py::test_handle_license_free -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_handle_license_free(app):
    data = {
        "item_1617605131499": {
            "attribute_name": "File",
            "attribute_type": "file",
            "attribute_value_mlt": [
                {
                    "licensefree": "own license",
                    "licensetype": "license_free"
                },
                {
                    "licensefree": "",
                    "licensetype": "license_free"
                },
                {
                    "licensetype": "license_12"
                },
            ]
        },
        "item_1617186331708": {
            "attribute_name": "Title",
        }
    }
    test = {
        "item_1617605131499":{
            "attribute_name":"File","attribute_type":"file",
            "attribute_value_mlt": [
                {"licensetype": "own license"},
                {"licensefree": ""},
                {"licensetype": "license_12"},
            ]
        },
        "item_1617186331708": {"attribute_name": "Title"}
    }
    data1 = copy.deepcopy(data)
    result = handle_license_free(data1)
    assert result == test
    current_app.config.update(WEKO_RECORDS_UI_LICENSE_DICT=[])
    handle_license_free(data)
    
#def get_index_state():
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_utils.py::test_get_index_state -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_get_index_state(app, db):
    from weko_index_tree.models import Index

    index1 = Index(# harvest_public_state is False
        parent=0,
        position=1,
        index_name_english="test_index1",
        index_link_name_english="test_index_link1",
        harvest_public_state=False,
        public_state=True,
        browsing_role="3,-99"
    )
    db.session.add(index1)
    index2 = Index(# -99 in browsing_role, publis_state is False
        parent=0,
        position=2,
        index_name_english="test_index1",
        index_link_name_english="test_index_link1",
        harvest_public_state=True,
        public_state=False,
        browsing_role="3"
    )
    db.session.add(index2)
    index3 = Index(
        parent=0,
        position=3,
        index_name_english="test_index1",
        index_link_name_english="test_index_link1",
        harvest_public_state=True,
        public_state=True,
        browsing_role="3,-99"
    )
    db.session.add(index3)
    db.session.commit()
    test = {
        "1":{"parent":None,"msg":2},
        "2":{"parent":None,"msg":1},
        "3":{"parent":"0","msg":3}
    }
    result = get_index_state()
    assert result == test

#def is_output_harvest(path_list, index_state):
#    def _check(index_id):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_utils.py::test_is_output_harvest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_is_output_harvest(app):
    index_state = {
        "1":{"parent":"0","msg":3},
        "2":{"parent":"1","msg":1},
    }
    path_list = ["1","2","1000"]
    result = is_output_harvest(path_list,index_state)
    assert result == 3

#def get_community_index_from_set(set):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_utils.py::test_get_community_index_from_set -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_get_community_index_from_set(app, db, users):
    from invenio_communities.models import Community
    from weko_index_tree.models import Index
    
    index1 = Index(
        parent=0,
        position=1,
        index_name_english="test_index1",
        index_link_name_english="test_index_link1",
        harvest_public_state=True,
        public_state=True,
        browsing_role="3,-99"
    )
    db.session.add(index1)
    db.session.commit()
    
    comm1 = Community.create(community_id="test_comm", role_id=users[0]["id"],
                            id_user=users[0]["id"], title="test community",
                            description="this is test community",
                            root_node_id=index1.id)
    db.session.add(comm1)
    db.session.commit()
    
    exist_com = comm1.id
    result = get_community_index_from_set(exist_com)
    assert result == str(index1.id)

    # exist community with prefix
    result = get_community_index_from_set("user-" + exist_com)
    assert result == str(index1.id)

    # no exist community
    result = get_community_index_from_set("no_exist_comm")
    assert result is None
    