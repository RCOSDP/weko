import pytest
from tests.helpers import json_data

from invenio_records_rest.schemas.json import RecordSchemaJSONV1
from invenio_pidstore.models import PersistentIdentifier
from weko_records.serializers.pidrelations import (
    serialize_related_identifiers, 
    preprocess_related_identifiers)

# def serialize_related_identifiers(serializer):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_pidrelations.py::test_serialize_related_identifiers -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_serialize_related_identifiers(app, db, records):
    res = serialize_related_identifiers(records[0][0])
    assert res==[]

# def preprocess_related_identifiers(response, links):
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_pidrelations.py::test_preprocess_related_identifiers -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_preprocess_related_identifiers(app, db, records):
    res = preprocess_related_identifiers(records[0][0], records[0][1], {})
    assert res=={}