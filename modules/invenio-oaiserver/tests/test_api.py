

from invenio_oaiserver.models import Identify

from invenio_oaiserver.api import OaiIdentify

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_api.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp


# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_api.py::TestOaiIdentify -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
class TestOaiIdentify:
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_admin.py::TestOaiIdentify::test_get_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
    def test_get_all(self, identify):
        result = OaiIdentify.get_all()
        assert result.outPutSetting == True
        assert result.emails == "test@test.org"
    
    def test_get_count(self, identify):
        result = OaiIdentify.get_count()
        assert result == 0