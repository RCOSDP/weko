import pytest
from mock import patch, MagicMock

from weko_records.serializers.rss import RssSerializer


# class RssSerializer(JSONSerializer): 
# def serialize_search
def test_serialize_search(app):
    test = RssSerializer()

    def output_open_search_detail_data():
        return True

    data1 = MagicMock()
    data1.output_open_search_detail_data = output_open_search_detail_data
    pid_fetcher = "pid_fetcher"
    search_result = "search_result"

    with patch('weko_records.serializers.rss.OpenSearchDetailData', return_value=data1):
        assert test.serialize_search(
            pid_fetcher=pid_fetcher,
            search_result=search_result
        ) != None
