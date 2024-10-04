import pytest
from tests.helpers import json_data

from invenio_pidstore.models import PersistentIdentifier
from weko_records.serializers.jpcoar import JpcoarSerializer

# class JpcoarSerializer(JSONSerializer):
#     def serialize_search(self, pid_fetcher, search_result, links=None, item_links_factory=None, **kwargs):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_jpcoar.py::test_jpcoar_serializer -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
params=[("data/record_hit/record_hit1.json")]
@pytest.mark.parametrize("hit", params)
def test_jpcoar_serializer(app, db, hit):
    def fetcher(obj_uuid, data):
        assert obj_uuid=="1"
        return PersistentIdentifier(pid_type='recid', pid_value=data['pid'])

    _search_result = {'hits': {'total': {"value": 1, "relation": "eq"}, 'hits': [json_data(hit)]}}
    _jpcoar_serializer = JpcoarSerializer()
    with app.test_request_context():
        assert _jpcoar_serializer.serialize_search(fetcher, _search_result)
