
from invenio_oaiserver.models import OAISet

class TestOAISet:
    def test_get_set_by_spec(self,oaiset):
        result = OAISet.get_set_by_spec("test")
        assert result.name == "test_name"
        assert result.search_pattern == "test search"