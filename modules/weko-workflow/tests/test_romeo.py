# .tox/c1/bin/pytest --cov=weko_workflow tests/test_romeo.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

from unittest.mock import MagicMock
import pytest
from mock import patch
from weko_workflow.romeo import search_romeo_jtitles,search_romeo_issn,search_romeo_jtitle
from collections import OrderedDict

class MockResponse:
    def __init__(self, text, status_code):
        self.__text = text
        self.__status_code = status_code

    @property
    def text(self):
        return self.__text
        

# def search_romeo_jtitles(keywords, qtype):
# .tox/c1/bin/pytest --cov=weko_workflow tests/test_romeo.py::test_search_romeo_jtitles -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workflow/.tox/c1/tmp

def test_search_romeo_jtitles(app):
    res = MockResponse("<book><title>title</title></book>",200)
    with app.test_request_context():
        with patch("requests.get",return_value=res):
            d = search_romeo_jtitles("keywords","qtype")
            assert d==OrderedDict([('book', OrderedDict([('title', 'title')]))])
            
# def search_romeo_issn(query):
def test_search_romeo_issn(app):
    res = MockResponse("<book><title>title</title></book>",200)
    with app.test_request_context():
        with patch("requests.get",return_value=res):
            d = search_romeo_issn("query")
            assert d==OrderedDict([('book', OrderedDict([('title', 'title')]))])

# def search_romeo_jtitle(query):
def test_search_romeo_jtitle(app):
    res = MockResponse("<book><title>title</title></book>",200)
    with app.test_request_context():
        with patch("requests.get",return_value=res):
            d,r = search_romeo_jtitle("query")
            assert d==OrderedDict([('book', OrderedDict([('title', 'title')]))])
            assert r.status=='200 OK'