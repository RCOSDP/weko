import pytest
from mock import patch, MagicMock
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

    def exists():
        return True

    data0 = MagicMock()
    data0.get_assigned_object = MagicMock()

    data1 = {
        "conceptdoi": "conceptdoi",
        "doi": "doi",
    }

    data2 = MagicMock()
    data2.exists = exists
    data2.children = [data0]

    with patch("weko_records.serializers.pidrelations.PIDVersioning", return_value=data2):
        with patch("weko_records.serializers.pidrelations.WekoDeposit.get_record", return_value=data1):
            assert serialize_related_identifiers(records[0][0]) != None


# def preprocess_related_identifiers(pid, record, result): 
# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_pidrelations.py::test_preprocess_related_identifiers -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
def test_preprocess_related_identifiers(app, db, records):
    res = preprocess_related_identifiers(records[0][0], records[0][1], {})
    assert res=={}

    def exists():
        return True

    pid = MagicMock()
    pid.pid_type = "doi"
    pid.pid_value = "conceptdoi"

    record = {
        "conceptdoi": "conceptdoi",
        "conceptrecid": "conceptrecid",
    }

    result = {
        "metadata": {
            "doi": "conceptdoi"
        }
    }

    data1 = MagicMock()
    data1.exists = exists

    with patch("weko_records.serializers.pidrelations.PIDVersioning", return_value=data1):
        with patch("weko_records.serializers.pidrelations.PersistentIdentifier.get", return_value=pid):
            with patch("weko_records.serializers.pidrelations.serialize_related_identifiers", return_value="rels"):
                assert preprocess_related_identifiers(pid, record, result) != None

                pid.pid_value = "conceptrecid"
                assert preprocess_related_identifiers(pid, record, result) != None
