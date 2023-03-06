
import uuid

from invenio_pidstore.models import PersistentIdentifier

from invenio_oaiserver.provider import OAIIDProvider


# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_provider.py::test_create -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_create(app, db):
    OAIIDProvider.create(pid_value="test_pid1")
    result = PersistentIdentifier.get("oai","test_pid1")
    assert result
    assert result.status == "K"
    
    obj_id = uuid.uuid4()
    OAIIDProvider.create("rec",obj_id,pid_value="test_pid2")
    result = PersistentIdentifier.get("oai","test_pid2")
    assert result
    assert result.status == "R"