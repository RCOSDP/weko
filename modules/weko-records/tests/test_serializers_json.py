import pytest
from tests.helpers import json_data

from invenio_pidstore.models import PersistentIdentifier
from weko_records.serializers.json import WekoJSONSerializer

# class WekoJSONSerializer(JSONSerializer):
#     def preprocess_record(self, pid, record, links_factory=None):
#     def preprocess_search_hit(self, pid, record_hit, links_factory=None, **kwargs):
#     def dump(self, obj, context=None):
#     def transform_record(self, pid, record, links_factory=None):
#     def transform_search_hit(self, pid, record_hit, links_factory=None):
#     def serialize_exporter(self, pid, record):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_json.py::test_json_serializer -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
params=[("data/record_hit/record_hit1.json")]
@pytest.mark.parametrize("hit", params)
def test_json_serializer(app, db, records, hit):
    def fetcher(obj_uuid, data):
        assert obj_uuid=="1"
        return PersistentIdentifier(pid_type='recid', pid_value=data['pid'])

    _json_serializer = WekoJSONSerializer()
    # transform_record
    assert _json_serializer.transform_record(records[0][0], records[0][1])
    # transform_search_hit
    assert _json_serializer.transform_search_hit(records[0][0], json_data(hit))
    # serialize_exporter
    assert _json_serializer.serialize_exporter(records[0][0], json_data(hit))
