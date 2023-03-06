
import uuid
import pytest

from invenio_pidstore.errors import PersistentIdentifierError

from invenio_oaiserver.fetchers import oaiid_fetcher
from invenio_oaiserver.provider import OAIIDProvider

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_fetcher.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_fetcher.py::test_oaiid_fetcher -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_oaiid_fetcher(app):

    record_uuid = uuid.uuid4()
    data = {"_oai":{"id":"test_id"}}
    result = oaiid_fetcher(record_uuid,data)
    
    assert result.provider == OAIIDProvider
    assert result.pid_type == "oai"
    assert result.pid_value == "test_id"
    
    data = {}
    with pytest.raises(PersistentIdentifierError):
        result = oaiid_fetcher(record_uuid,data)