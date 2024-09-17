
import pytest
from requests.models import Response
from mock import patch
from weko_items_autofill.api import CrossRefOpenURL,CiNiiURL

# class CrossRefOpenURL:
class TestCrossRefOpenURL:
#     def __init__(self, pid, doi, response_format=None, timeout=None,
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_api.py::TestCrossRefOpenURL::test__init__ -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
    def test__init__(self):
        # pid is none
        with pytest.raises(ValueError) as e:
            cross_ref = CrossRefOpenURL(None,None)
            assert str(e) == 'PID is required.'
        # doi is none
        with pytest.raises(ValueError) as e:
            cross_ref = CrossRefOpenURL(1,None)
            assert str(e) == 'DOI is required.'
        
        # not exist response_format,timeout,http_proxy,https_proxy
        cross_ref = CrossRefOpenURL("test_pid","test_doi")
        assert cross_ref._response_format == "xml"
        assert cross_ref._timeout == 5
        assert cross_ref._proxy["http"] == ""
        assert cross_ref._proxy["https"] == ""
        # exist response_format,timeout,http_proxy,https_proxy
        cross_ref = CrossRefOpenURL("test_pid","test_doi",
                                    response_format="txt",timeout=10,http_proxy="test_http_proxy",https_proxy="test_https_proxy")
        assert cross_ref._response_format == "txt"
        assert cross_ref._timeout == 10
        assert cross_ref._proxy["http"] == "test_http_proxy"
        assert cross_ref._proxy["https"] == "test_https_proxy"
        

#     def _create_endpoint(self):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_api.py::TestCrossRefOpenURL::test_create_endpoint -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
    def test_create_endpoint(self):
        # response_format is None
        cross_ref = CrossRefOpenURL("test_pid","test_doi",response_format="txt")
        endpoint = cross_ref._create_endpoint()
        assert endpoint == "openurl?pid=test_pid&id=doi:test_doi&format=txt"
        
        cross_ref._response_format = None
        endpoint = cross_ref._create_endpoint()
        assert endpoint == "openurl?pid=test_pid&id=doi:test_doi"


#     def _create_url(self):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_api.py::TestCrossRefOpenURL::test_create_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
    def test_create_url(self,mocker):
        cross_ref = CrossRefOpenURL("test_pid","test_doi",response_format="txt")
        mocker.patch("weko_items_autofill.api.CrossRefOpenURL._create_endpoint",return_value="openurl?pid=test_pid&id=doi:test_doi")
        result = cross_ref._create_url()
        assert result == "https://doi.crossref.org/openurl?pid=test_pid&id=doi:test_doi"


#     def url(self):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_api.py::TestCrossRefOpenURL::test_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
    def test_url(self,mocker):
        cross_ref = CrossRefOpenURL("test_pid","test_doi",response_format="txt")
        mocker.patch("weko_items_autofill.api.CrossRefOpenURL._create_url",return_value="https://doi.crossref.org/openurl?pid=test_pid&id=doi:test_doi")
        
        result = cross_ref.url
        assert result == "https://doi.crossref.org/openurl?pid=test_pid&id=doi:test_doi"


#     def _do_http_request(self):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_api.py::TestCrossRefOpenURL::test_do_http_request -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
    def test_do_http_request(self,mocker):
        mock_get = mocker.patch("weko_items_autofill.api.requests.get")
        cross_ref = CrossRefOpenURL("test_pid","test_doi")
        cross_ref._do_http_request()
        mock_get.assert_called_with("https://doi.crossref.org/openurl?pid=test_pid&id=doi:test_doi&format=xml",
                                    timeout=5,proxies={"http":"test_http_proxy","https":"test_https_proxy"})


#     def get_data(self):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_api.py::TestCrossRefOpenURL::test_get_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
    def test_get_data(self,mocker):
        cross_ref = CrossRefOpenURL("test_pid","test_doi")
        res = Response()
        res._content = b"test response"
        res.status_code = 200
        
        with patch("weko_items_autofill.api.CrossRefOpenURL._do_http_request",return_value=res):
            result = cross_ref.get_data()
            assert result == {"response":"test response","error":""}
        # statuscode != 200
        res.status_code = 400
        with patch("weko_items_autofill.api.CrossRefOpenURL._do_http_request",return_value=res):
            result = cross_ref.get_data()
            assert result == {"response":"","error":""}
        
        # raise Exception
        with patch("weko_items_autofill.api.CrossRefOpenURL._do_http_request",side_effect=Exception("request error")):
            result = cross_ref.get_data()
            assert result == {"response":"","error":"request error"}


# class CiNiiURL:
class TestCiNiiURL:
#     def __init__(self, naid, timeout=None, http_proxy=None, https_proxy=None):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_api.py::TestCiNiiURL::test__init__ -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
    def test__init__(self):
        # not naid
        with pytest.raises(ValueError) as e:
            cini = CiNiiURL(None)
            assert str(e) == "NAID is required."
        
        # not exist timeout,http_proxy,https_proxy
        cini = CiNiiURL("test_naid")
        assert cini._naid == "test_naid"
        assert cini._timeout == 5
        assert cini._proxy == {"http":"","https":""}
        
        # exist timeout,http_proxy,https_proxy
        cini = CiNiiURL("test_naid",timeout=10,http_proxy="test_http_proxy",https_proxy="test_https_proxy")
        assert cini._naid == "test_naid"
        assert cini._timeout == 10
        assert cini._proxy == {"http":"test_http_proxy","https":"test_https_proxy"}
        


#     def _create_endpoint(self):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_api.py::TestCiNiiURL::test_create_endpoint -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
    def test_create_endpoint(self):
        cini = CiNiiURL("test_naid")
        result = cini._create_endpoint()
        assert result == "crid/test_naid.json"


#     def _create_url(self):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_api.py::TestCiNiiURL::test_create_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
    def test_create_url(self,mocker):
        mocker.patch("weko_items_autofill.api.CiNiiURL._create_endpoint",return_value="naid/test_naid.json")
        cini = CiNiiURL("test_naid")
        result = cini._create_url()
        assert result == "https://cir.nii.ac.jp/naid/test_naid.json"


#     def url(self):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_api.py::TestCiNiiURL::test_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
    def test_url(self,mocker):
        mocker.patch("weko_items_autofill.api.CiNiiURL._create_url",return_value="https://ci.nii.ac.jp/naid/test_naid.json")
        cini = CiNiiURL("test_naid")
        result = cini.url
        assert result == "https://ci.nii.ac.jp/naid/test_naid.json"


#     def _do_http_request(self):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_api.py::TestCiNiiURL::test_do_http_request -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
    def test_do_http_request(self,mocker):
        mock_get = mocker.patch("weko_items_autofill.api.requests.get")
        cini = CiNiiURL("test_naid")
        cini._do_http_request()
        mock_get.assert_called_with("https://cir.nii.ac.jp/crid/test_naid.json",
                                    timeout=5,proxies={"http":"test_http_proxy","https":"test_https_proxy"})


#     def get_data(self):
# .tox/c1/bin/pytest --cov=weko_items_autofill tests/test_api.py::TestCiNiiURL::test_get_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-items-autofill/.tox/c1/tmp
    def test_get_data(self):
        cini = CiNiiURL("test_naid")
        res = Response()
        res._content = b'{"key":"test response"}'
        res.status_code = 200
        
        with patch("weko_items_autofill.api.CiNiiURL._do_http_request",return_value=res):
            result = cini.get_data()
            assert result == {"response":{"key":"test response"},"error":""}
        # statuscode != 200
        res.status_code = 400
        with patch("weko_items_autofill.api.CiNiiURL._do_http_request",return_value=res):
            result = cini.get_data()
            assert result == {"response":"","error":""}
        
        # raise Exception
        with patch("weko_items_autofill.api.CiNiiURL._do_http_request",side_effect=Exception("request error")):
            result = cini.get_data()
            assert result == {"response":"","error":"request error"}
