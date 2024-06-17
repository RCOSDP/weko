import uuid

from invenio_oaiserver.minters import oaiid_minter

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_minters.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp

def test_oaiid_minter(app, db):
    data = {"control_number":"1"}
    record_uuid = uuid.uuid4()
    
    result = oaiid_minter(record_uuid, data)
    assert result.pid_value == "oai:inveniosoftware.org:recid/00000001"
    assert data == {"control_number":"1","_oai":{"id":"oai:inveniosoftware.org:recid/00000001"}}
    data = {
        "_oai":{"id":"test_oaiid"},
        "control_number":"2"
    }
    record_uuid = uuid.uuid4()
    result = oaiid_minter(record_uuid, data)
    assert result.pid_value == "test_oaiid"
    assert data == {"_oai":{"id":"test_oaiid"},"control_number":"2"}
    