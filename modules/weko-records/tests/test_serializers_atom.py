import pytest
from mock import patch, MagicMock

from weko_records.serializers.atom import AtomSerializer


# class AtomSerializer(JSONSerializer): 
# def serialize_search(self, pid_fetcher, search_result, links=None, item_links_factory=None, **kwargs):
def test_serialize_search(app):
    test = AtomSerializer()
    pid_fetcher = 1
    search_result = {}
    data1 = MagicMock()
    data1.output_open_search_detail_data = MagicMock()

    with patch('weko_records.serializers.atom.OpenSearchDetailData', return_value=data1):
        assert test.serialize_search(
            pid_fetcher=pid_fetcher,
            search_result=search_result
        ) != None