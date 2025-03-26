
import pytest
from mock import patch
import uuid
from flask import current_app
from elasticsearch_dsl import Q
from datetime import datetime

from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.models import RecordMetadata
from invenio_search import current_search_client
from weko_index_tree.models import Index

from invenio_oaiserver import current_oaiserver
from invenio_oaiserver.query import (
    query_string_parser,
    get_affected_records,
    get_records
)
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_query.py -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp

#def query_string_parser(search_pattern):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_query.py::test_query_string_parser -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_query_string_parser(es_app):
    from elasticsearch_dsl.query import QueryString
    # current_oaiserver not have query_parse, config is str
    result = query_string_parser("test_path")
    assert type(result) == QueryString
    assert result.name == "query_string"
    assert result.to_dict() == {"query_string":{"query":"test_path"}}
    
    # current_oaiserver not have query_parse, config is not str
    current_app.config.update(OAISERVER_QUERY_PARSER=Q)
    delattr(current_oaiserver,"query_parser")
    esult = query_string_parser("test_path")
    assert type(result) == QueryString
    assert result.name == "query_string"
    assert result.to_dict() == {"query_string":{"query":"test_path"}}
    
    # current_oaiserver  have query_parse
    result = query_string_parser("test_path")
    assert type(result) == QueryString
    assert result.name == "query_string"
    assert result.to_dict() == {"query_string":{"query":"test_path"}}

#class OAIServerSearch(RecordsSearch):

#def get_affected_records(spec=None, search_pattern=None):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_query.py::test_get_affected_records -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_get_affected_records(es_app):
    # raise StopIteration
    #with pytest.raises(StopIteration):
    result = get_affected_records(None,None)
    for i in result:
        pass
    
    spec="1671155386910"
    search_path = 'path:"1671155386910"'
    # exist spec, not exist search_path
    result = get_affected_records(spec,None)
    for i in result:
        assert i
    
    # not exist spec, exist search_path
    result = get_affected_records(None,search_path)
    for i in result:
        assert i
    
    result = get_affected_records(spec,search_path)
    for i in result:
        assert i
    
#def get_records(**kwargs):

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_query.py::test_get_records -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_get_records(es_app,db, mock_execute):
    indexes = list()
    for i in range(11):
        indexes.append(
            Index(
                parent=0,
                position=i,
                index_name_english="test_index{}".format(i),
                index_link_name_english="test_index_link{}".format(i),
                harvest_public_state=True,
                public_state=True,
                public_date=datetime(2100,1,1),
                browsing_role="3,-99"
            )
        )
    indexes[-1].is_deleted = True

    rec_uuid1 = uuid.uuid4()
    identifier1 = PersistentIdentifier.create('doi', "https://doi.org/00001",object_type='rec', object_uuid=rec_uuid1,status=PIDStatus.REGISTERED)

    rec_data1={"title":["test_item1"],"path":[1],"_oai":{"id":"oai:test:00001","sets":[]},"relation_version_is_last":"true","control_number":"1"}
    rec1 = RecordMetadata(id=rec_uuid1,json=rec_data1)
    rec_uuid2 = uuid.uuid4()
    rec_data2={"title":["test_item2"],"path":[1000],"_oai":{"id":"oai:test:00002","sets":["12345"]},"relation_version_is_last":"true","control_number":"2"}
    identifier2 = PersistentIdentifier.create('doi', "https://doi.org/00002",object_type='rec', object_uuid=rec_uuid2,status=PIDStatus.REGISTERED)
    rec2 = RecordMetadata(id=rec_uuid2,json=rec_data2)
    db.session.add_all(indexes)
    db.session.add(rec1)
    db.session.add(rec2)
    
    db.session.commit()
    
    es_info = dict(id=str(rec_uuid1),
                       index=current_app.config['INDEXER_DEFAULT_INDEX'],
                       doc_type=current_app.config['INDEXER_DEFAULT_DOCTYPE'])
    body = dict(version=1,
                version_type="external_gte",
                body=rec_data1)
    current_search_client.index(**{**es_info,**body})
    es_info = dict(id=str(rec_uuid2),
                       index=current_app.config['INDEXER_DEFAULT_INDEX'],
                       doc_type=current_app.config['INDEXER_DEFAULT_DOCTYPE'])
    body = dict(version=1,
                version_type='external_gte',
                body=rec_data2)
    current_search_client.index(**{**es_info,**body})
    
    # not scroll_id, ":" not in set
    data = {
        "set":"12345"
    }
    result = get_records(**data)
    assert result
    
    # not scroll_id, ":" in set
    data = {
        "set":"12345:6789"
    }
    result = get_records(**data)
    assert result
    
    # not scroll_id, "set" not in data, exist "from_","until" in data
    data = {
        "from_":"2022-01-01",
        "until":"2023-01-01"
    }
    result = get_records(**data)
    assert result
    
    # in scroll_id
    data = {
        "resumptionToken":{"page":1,"scroll_id":"DXF1ZXJ5QW5kRmV0Y2gBAAAAAAAAVfgWYmVhQ3BkbEdSSm0wS3pTaEdQeHQ1QQ=="}
    }
    dummy_data={
        "hits":{
            "total":1000,
            "hits":[]
        }
    }
    dummy_data["hits"]["hits"].extend([{"_source":{"query":{"query_string":{"query":"path:\"{}\"".format(i)}}}} for i in range(998)])
    dummy_data["hits"]["hits"].extend([
        {
            "_id":"test_id_1",
            "_source":{"_oai":{"id":"oai:test:00001","sets":[]},"_updated":"2022-01-10T10:02:23"}
        },
        {
            "_id":"test_id_2",
            "_source":{"_oai":{"id":"oai:test:00002","sets":["12345"]},"_updated":"2022-02-10T10:02:23"}
        }
    ])
    test = [
        {
            "id":"test_id_1",
            "json":{"_id":"test_id_1","_source":{"_oai":{"id":"oai:test:00001","sets":[]},"_updated":"2022-01-10T10:02:23"}},
            "updated":datetime(2022,1,10,10,2,23)
        },
        {
            "id":"test_id_2",
            "json":{"_id":"test_id_2","_source":{"_oai":{"id":"oai:test:00002","sets":["12345"]},"_updated":"2022-02-10T10:02:23"}},
            "updated":datetime(2022,2,10,10,2,23)
        }
    ]
    with patch("invenio_oaiserver.query.current_search_client.scroll",return_value=dummy_data):
        result = get_records(**data)
        assert result.next_num == 2
        result_items = [r for r in result.items]
        assert result_items == test

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_query.py::test_get_records_with_set -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_get_records_with_set(es_app,db, users):
    from elasticsearch import Elasticsearch
    from invenio_communities.models import Community
    indexes = list()
    ids = [123,456,789]
    for i in range(3):
        indexes.append(
            Index(
                id=ids[i],
                parent=ids[i-1] if i > 0 else 0,
                position=1,
                index_name_english=f"test_index{i}",
                index_link_name_english=f"test_index_link{i}",
                harvest_public_state=True,
                public_state=True,
                public_date=datetime(2000,1,1),
                browsing_role="3,-99"
            )
        )
    
    rec_uuid1 = uuid.uuid4()
    rec_data1 = {"title":["test_item1"],
                 "path":["123"],
                 "_oai":{"id":"oai:test:00001","sets":["123"]},
                 "relation_version_is_last":"true",
                 "control_number":"1",
                 "publish_status":"0",
                 "_updated": "2022-01-01T00:00:00"
                 }
    rec1 = RecordMetadata(id=rec_uuid1,json=rec_data1)
    
    rec_uuid2 = uuid.uuid4()
    rec_data2 = {"title":["test_item2"],
                 "path":["456"],
                 "_oai":{"id":"oai:test:00002", "sets":["456"]},
                 "relation_version_is_last":"true",
                 "control_number":"2",
                 "publish_status":"0",
                 "_updated": "2022-01-01T00:00:00"
                 }
    rec2 = RecordMetadata(id=rec_uuid2,json=rec_data2)
    
    rec_uuid3 = uuid.uuid4()
    rec_data3 = {"title":["test_item3"],
                 "path":["789"],
                 "_oai":{"id":"oai:test:00003", "sets":["789"]},
                 "relation_version_is_last":"true",
                 "control_number":"3",
                 "publish_status":"0",
                 "_updated": "2022-01-01T00:00:00"
                 }
    rec3 = RecordMetadata(id=rec_uuid3,json=rec_data3)
    
    db.session.add_all(indexes)
    db.session.add(rec1)
    db.session.add(rec2)
    db.session.add(rec3)
    db.session.commit()
    
    es_info = dict(index=current_app.config['INDEXER_DEFAULT_INDEX'],
                    doc_type=current_app.config['INDEXER_DEFAULT_DOCTYPE'],
                    version=1,
                    version_type="external_gte",
                    refresh="wait_for")
    body1 = dict(id=str(rec_uuid1), body=rec_data1)
    body2 = dict(id=str(rec_uuid2), body=rec_data2)
    body3 = dict(id=str(rec_uuid3), body=rec_data3)
    current_search_client.index(**es_info,**body1)
    current_search_client.index(**es_info,**body2)
    current_search_client.index(**es_info,**body3)
    
    comm1 = Community.create(community_id="test_comm", role_id=users[0]["id"],
                            id_user=users[0]["id"], title="test community",
                            description="this is test community",
                            root_node_id=indexes[0].id)
    db.session.add(comm1)
    db.session.commit()
    
    data = {"set":"123"}
    result = get_records(**data)
    assert result.total == 3
    result_items = [r for r in result.items]
    assert result_items[0]["json"]["_source"] == rec_data1
    assert result_items[1]["json"]["_source"] == rec_data2
    assert result_items[2]["json"]["_source"] == rec_data3
    
    data = {"set":"123:456"}
    result = get_records(**data)
    assert result.total == 2
    result_items = [r for r in result.items]
    assert result_items[0]["json"]["_source"] == rec_data2
    assert result_items[1]["json"]["_source"] == rec_data3
    
    data = {"set":"123:456:789"}
    result = get_records(**data)
    assert result.total == 1
    result_items = [r for r in result.items]
    assert result_items[0]["json"]["_source"] == rec_data3
    
    data = {"set":"user-test_comm"}
    result = get_records(**data)
    assert result.total == 3
    result_items = [r for r in result.items]
    assert result_items[0]["json"]["_source"] == rec_data1
    assert result_items[1]["json"]["_source"] == rec_data2
    assert result_items[2]["json"]["_source"] == rec_data3
    
    data = {"set":"test_comm"}
    result = get_records(**data)
    assert result.total == 3
    result_items = [r for r in result.items]
    assert result_items[0]["json"]["_source"] == rec_data1
    assert result_items[1]["json"]["_source"] == rec_data2
    assert result_items[2]["json"]["_source"] == rec_data3
    
    data = {"set":"999"}
    result = get_records(**data)
    assert result.total == 0
    
    data = {"set":"aaa"}
    result = get_records(**data)
    assert result.total == 0
