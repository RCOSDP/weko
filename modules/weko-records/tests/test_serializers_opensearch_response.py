import pytest
from tests.helpers import json_data

from invenio_records_rest.schemas.json import RecordSchemaJSONV1
from invenio_pidstore.models import PersistentIdentifier
from weko_records.serializers.opensearchresponse import (
    oepnsearch_responsify,
    add_link_header,
    custom_output_open_search
)
from weko_records.serializers.opensearchserializer import OpenSearchSerializer

# def oepnsearch_responsify(serializer):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_opensearch_response.py::test_oepnsearch_responsify -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
params=[("data/record_hit/record_hit1.json")]
@pytest.mark.parametrize("hit", params)
def test_oepnsearch_responsify(app, db, hit):
    def fetcher(obj_uuid, data):
        assert obj_uuid=="1"
        return PersistentIdentifier(pid_type='recid', pid_value=data['pid'])

    _search_result = {'hits': {'total': 1, 'hits': [json_data(hit)]}}
    opensearch_v1 = OpenSearchSerializer(RecordSchemaJSONV1)
    opensearch = oepnsearch_responsify(opensearch_v1)
    with app.test_request_context():
        result = opensearch(fetcher, _search_result)
        assert result.status_code==200

# def add_link_header(response, links):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_opensearch_response.py::test_add_link_header -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_add_link_header(app, db):
    _response = app.response_class()
    _links = {'key1': 'value1', 'key2': 'value2'}

    add_link_header(_response, _links)
    assert _response.headers[1]==('Link', '<value1>; rel="key1", <value2>; rel="key2"')

# def custom_output_open_search(record_lst: list):
