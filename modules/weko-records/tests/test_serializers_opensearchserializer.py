import pytest
from mock import patch, MagicMock

from weko_records.serializers.opensearchserializer import (
    OpenSearchSerializer
)


# class OpenSearchSerializer
# def serialize_search(self, pid_fetcher, search_result, links=None, item_links_factory=None, **kwargs):
def test_serialize_search_OpenSearchSerializer(app):
    def serialize_search(x, y, **kwargs):
        return True

    test = OpenSearchSerializer()

    data1 = MagicMock()
    data1.serialize_search = serialize_search

    pid_fetcher = {
        "hits": {
            "total": "total",
            "hits": [{
                "_source": {
                    "_item_metadata": "_item_metadata"
                }
            }],
        }
    }
    search_result = pid_fetcher

    with app.test_request_context():
        with patch("weko_records.serializers.opensearchserializer.JSONSerializer", return_value=data1):
            with patch("flask.request.values.get", return_value=""):
                assert test.serialize_search(
                    pid_fetcher=pid_fetcher,
                    search_result=search_result,
                ) != None

            with patch("weko_records.serializers.opensearchserializer.AtomSerializer", return_value=data1):
                with patch("weko_records.serializers.opensearchserializer.RssSerializer", return_value=data1):
                    with patch("weko_records.serializers.opensearchserializer.JpcoarSerializer", return_value=data1):
                        with patch("flask.request.values.get", return_value="atom"):
                            assert test.serialize_search(
                                pid_fetcher=pid_fetcher,
                                search_result=search_result,
                            ) != None
                        
                        with patch("flask.request.values.get", return_value="rss"):
                            assert test.serialize_search(
                                pid_fetcher=pid_fetcher,
                                search_result=search_result,
                            ) != None

                        with patch("flask.request.values.get", return_value="jpcoar"):
                            assert test.serialize_search(
                                pid_fetcher=pid_fetcher,
                                search_result=search_result,
                            ) != None
            