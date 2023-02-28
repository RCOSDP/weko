
from invenio_oaiserver.proxies import current_oaiserver

from invenio_oaiserver.models import OAISet,oaiset_attribute_changed

class TestOAISet:
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_models.py::TestOAISet::test_get_set_by_spec -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
    def test_get_set_by_spec(self,es_app,oaiset):
        result = OAISet.get_set_by_spec("test")
        assert result.name == "test_name"
        assert result.search_pattern == "test search"

# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_models.py::test_oaiset_attribute_changed -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_oaiset_attribute_changed(app,db,mocker):
    # value == oldvalue
    oaiset_attribute_changed("","value","value",None)
    assert current_oaiserver.sets == None
    
    # value != oldvalue
    oaiset_attribute_changed("","value","oldvalue",None)
    assert current_oaiserver.sets == None
