import pytest
from mock import patch
from requests.cookies import RequestsCookieJar
from requests.exceptions import RequestException
from requests.models import Response

from weko_workspace.api import JamasURL, CiNiiURL, JALCURL, DATACITEURL


# class JamasURL:
class TestJamasURL:
#     def __init__(self, doi, timeout=None, http_proxy=None, https_proxy=None):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestJamasURL::test__init__ -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test__init__(self):
        # not doi
        with pytest.raises(ValueError) as e:
            jamas = JamasURL(None)
            assert str(e) == "DOI is required."
        
        # not exist timeout,http_proxy,https_proxy
        jamas = JamasURL("10.5109/16119")
        assert jamas._doi == "10.5109/16119"
        assert jamas._timeout == 5
        assert jamas._proxy == {"http": "", "https": ""}

        # exist timeout,http_proxy,https_proxy
        jamas = JamasURL("10.5109/16119", timeout=10, http_proxy="test_http_proxy", https_proxy="test_https_proxy")
        assert jamas._doi == "10.5109/16119"
        assert jamas._timeout == 10
        assert jamas._proxy == {"http": "test_http_proxy", "https": "test_https_proxy"}
    

#     def _create_endpoint(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestJamasURL::test_create_endpoint -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_create_endpoint(self):
        jamas = JamasURL("10.5109/16119")
        result = jamas._create_endpoint()
        assert result == "api/sru?operation=searchRetrieve&version=1.2&startRecord=1&recordPacking=xml&recordSchema=pam&query=prism.doi%3D10.5109%2F16119"


#     def _create_url(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestJamasURL::test_create_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_create_url(self, app):
        jamas = JamasURL("10.5109/16119")
        result = jamas._create_url()
        assert result == "https://search.jamas.or.jp/api/sru?operation=searchRetrieve&version=1.2&startRecord=1&recordPacking=xml&recordSchema=pam&query=prism.doi%3D10.5109%2F16119"


#     def url(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestJamasURL::test_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_url(self, app):
        jamas = JamasURL("10.5109/16119")
        result = jamas.url
        assert result == "https://search.jamas.or.jp/api/sru?operation=searchRetrieve&version=1.2&startRecord=1&recordPacking=xml&recordSchema=pam&query=prism.doi%3D10.5109%2F16119"


#     def _do_http_request(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestJamasURL::test_do_http_request -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_do_http_request(self, app, mocker):
        mock_get = mocker.patch('weko_workspace.api.requests.get')
        jamas = JamasURL("10.5109/16119", timeout=5, http_proxy="test_http_proxy", https_proxy="test_https_proxy")
        jamas._do_http_request()
        mock_get.assert_called_once_with(
            "https://search.jamas.or.jp/api/sru?operation=searchRetrieve&version=1.2&startRecord=1&recordPacking=xml&recordSchema=pam&query=prism.doi%3D10.5109%2F16119",
            cookies=None,
            timeout=5,
            proxies={"http": "test_http_proxy", "https": "test_https_proxy"}
        )


#     def _login(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestJamasURL::test_login -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_login(self, app):
        mock_response = Response()
        mock_response.status_code = 200
        jar = RequestsCookieJar()
        jar.set('JSESSIONID', 'test_session_id', domain='search.jamas.or.jp', path='/')
        mock_response.cookies = jar

        # login success
        with patch('weko_workspace.api.requests.post', return_value=mock_response) as mock_post:
            jamas = JamasURL("10.5109/16119", http_proxy="test_http_proxy", https_proxy="test_https_proxy")
            result = jamas._login()
            assert result is True
            assert jamas._cookie == {'JSESSIONID': 'test_session_id'}
            mock_post.assert_called_once_with(
                'https://search.jamas.or.jp/api/login',
                timeout=5,
                proxies={'http': 'test_http_proxy', 'https': 'test_https_proxy'},
            )
        
        # login ng
        mock_response._content = b'login ng'
        with patch('weko_workspace.api.requests.post', return_value=mock_response) as mock_post:
            jamas = JamasURL("10.5109/16119", http_proxy="test_http_proxy", https_proxy="test_https_proxy")
            result = jamas._login()
            assert result is False
            assert jamas._cookie is None
            mock_post.assert_called_once_with(
                'https://search.jamas.or.jp/api/login',
                timeout=5,
                proxies={'http': 'test_http_proxy', 'https': 'test_https_proxy'},
            )
        
        # status_code is not 200
        mock_response.status_code = 400
        with patch('weko_workspace.api.requests.post', return_value=mock_response) as mock_post:
            jamas = JamasURL("10.5109/16119", http_proxy="test_http_proxy", https_proxy="test_https_proxy")
            result = jamas._login()
            assert result is False
            assert jamas._cookie is None
            mock_post.assert_called_once_with(
                'https://search.jamas.or.jp/api/login',
                timeout=5,
                proxies={'http': 'test_http_proxy', 'https': 'test_https_proxy'},
            )

        # RequestException
        with patch('weko_workspace.api.requests.post', side_effect=RequestException("request error")) as mock_post:
            jamas = JamasURL("10.5109/16119", http_proxy="test_http_proxy", https_proxy="test_https_proxy")
            result = jamas._login()
            assert result is False
            assert jamas._cookie is None
            mock_post.assert_called_once_with(
                'https://search.jamas.or.jp/api/login',
                timeout=5,
                proxies={'http': 'test_http_proxy', 'https': 'test_https_proxy'},
            )


#     def _logout(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestJamasURL::test_logout -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_logout(self, app):
        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = b'logout ok'

        # logout success
        with patch('weko_workspace.api.requests.post', return_value=mock_response) as mock_post:
            jamas = JamasURL("10.5109/16119", http_proxy="test_http_proxy", https_proxy="test_https_proxy")
            jamas._cookie = {'JSESSIONID': 'test_session_id'}
            result = jamas._logout()
            assert result is True
            mock_post.assert_called_once_with(
                'https://search.jamas.or.jp/api/logout',
                cookies={'JSESSIONID': 'test_session_id'},
                timeout=5,
                proxies={'http': 'test_http_proxy', 'https': 'test_https_proxy'},
            )
        
        # logout ng
        mock_response._content = b'logout ng'
        with patch('weko_workspace.api.requests.post', return_value=mock_response) as mock_post:
            jamas = JamasURL("10.5109/16119", http_proxy="test_http_proxy", https_proxy="test_https_proxy")
            jamas._cookie = {'JSESSIONID': 'test_session_id'}
            result = jamas._logout()
            assert result is False
            mock_post.assert_called_once_with(
                'https://search.jamas.or.jp/api/logout',
                cookies={'JSESSIONID': 'test_session_id'},
                timeout=5,
                proxies={'http': 'test_http_proxy', 'https': 'test_https_proxy'},
            )
        
        # status_code is not 200
        mock_response.status_code = 400
        with patch('weko_workspace.api.requests.post', return_value=mock_response) as mock_post:
            jamas = JamasURL("10.5109/16119", http_proxy="test_http_proxy", https_proxy="test_https_proxy")
            jamas._cookie = {'JSESSIONID': 'test_session_id'}
            result = jamas._logout()
            assert result is False
            mock_post.assert_called_once_with(
                'https://search.jamas.or.jp/api/logout',
                cookies={'JSESSIONID': 'test_session_id'},
                timeout=5,
                proxies={'http': 'test_http_proxy', 'https': 'test_https_proxy'},
            )

        # RequestException
        with patch('weko_workspace.api.requests.post', side_effect=RequestException("request error")) as mock_post:
            jamas = JamasURL("10.5109/16119", http_proxy="test_http_proxy", https_proxy="test_https_proxy")
            jamas._cookie = {'JSESSIONID': 'test_session_id'}
            result = jamas._logout()
            assert result is False
            mock_post.assert_called_once_with(
                'https://search.jamas.or.jp/api/logout',
                cookies={'JSESSIONID': 'test_session_id'},
                timeout=5,
                proxies={'http': 'test_http_proxy', 'https': 'test_https_proxy'},
            )


#     def get_data(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestJamasURL::test_get_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_get_data(self, app):
        jamas = JamasURL("10.5109/16119")
        res = Response()
        res._content = b'test response'
        res.status_code = 200

        with patch('weko_workspace.api.JamasURL._login', return_value=True):
            with patch('weko_workspace.api.JamasURL._logout'):
                # status_code is 200
                with patch('weko_workspace.api.JamasURL._do_http_request', return_value=res):
                    result = jamas.get_data()
                    assert result == {'response': 'test response', 'error': ''}

                # status_code is not 200
                res.status_code = 400
                with patch('weko_workspace.api.JamasURL._do_http_request', return_value=res):
                    result = jamas.get_data()
                    assert result == {'response': '', 'error': ''}

            # raise Exception
            with patch('weko_workspace.api.JamasURL._do_http_request', side_effect=Exception("request error")):
                result = jamas.get_data()
                assert result == {'response': '', 'error': 'request error'}
        
        with patch('weko_workspace.api.JamasURL._login', return_value=False):
            # login failed
            result = jamas.get_data()
            assert result == {'response': '', 'error': 'Login to Jamas failed.'}


# class CiNiiURL:
class TestCiNiiURL:
#     def __init__(self, naid, timeout=None, http_proxy=None, https_proxy=None):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestCiNiiURL::test__init__ -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test__init__(self):
        # not doi
        with pytest.raises(ValueError) as e:
            cini = CiNiiURL(None)
            assert str(e) == "DOI is required."
        
        # not exist timeout,http_proxy,https_proxy
        cini = CiNiiURL("10.5109/16119")
        assert cini._doi == "10.5109/16119"
        assert cini._timeout == 5
        assert cini._proxy == {"http":"","https":""}
        
        # exist timeout,http_proxy,https_proxy
        cini = CiNiiURL("10.5109/16119",timeout=10,http_proxy="test_http_proxy",https_proxy="test_https_proxy")
        assert cini._doi == "10.5109/16119"
        assert cini._timeout == 10
        assert cini._proxy == {"http":"test_http_proxy","https":"test_https_proxy"}
        

#     def _create_endpoint(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestCiNiiURL::test_create_endpoint -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_create_endpoint(self):
        cini = CiNiiURL("10.5109/16119")
        result = cini._create_endpoint()
        assert result == 'doi=10.5109/16119&format=json'


#     def _create_url(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestCiNiiURL::test_create_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_create_url(self):
        cini = CiNiiURL("10.5109/16119")
        result = cini._create_url()
        assert result == "https://cir.nii.ac.jp/opensearch/all?doi=10.5109/16119&format=json"


#     def url(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestCiNiiURL::test_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_url(self):
        cini = CiNiiURL("10.5109/16119")
        result = cini.url
        assert result == "https://cir.nii.ac.jp/opensearch/all?doi=10.5109/16119&format=json"


#     def _do_http_request(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestCiNiiURL::test_do_http_request -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_do_http_request(self,mocker):
        mock_get = mocker.patch("weko_workspace.api.requests.get")
        cini = CiNiiURL("10.5109/16119",timeout=5,http_proxy="test_http_proxy",https_proxy="test_https_proxy")
        cini._do_http_request()
        mock_get.assert_called_once_with(
            "https://cir.nii.ac.jp/opensearch/all?doi=10.5109/16119&format=json",
            timeout=5,
            proxies={"http": "test_http_proxy", "https": "test_https_proxy"}
        )


#     def get_data(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestCiNiiURL::test_get_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_get_data(self, app):
        cini = CiNiiURL("10.5109/16119")
        res = Response()
        res._content = b'{"key":"test response"}'
        res.status_code = 200
        
        with patch("weko_workspace.api.CiNiiURL._do_http_request",return_value=res):
            result = cini.get_data()
            assert result == {"response":{"key":"test response"},"error":""}
        # statuscode != 200
        res.status_code = 400
        with patch("weko_workspace.api.CiNiiURL._do_http_request",return_value=res):
            result = cini.get_data()
            assert result == {"response":"","error":""}
        
        # raise Exception
        with patch("weko_workspace.api.CiNiiURL._do_http_request",side_effect=Exception("request error")):
            result = cini.get_data()
            assert result == {"response":"","error":"request error"}


# class JALCURL:
class TestJALCURL:
#     def __init__(self, naid, timeout=None, http_proxy=None, https_proxy=None):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestJALCURL::test__init__ -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test__init__(self):
        # not doi
        with pytest.raises(ValueError) as e:
            jalc = JALCURL(None)
            assert str(e) == "DOI is required."
        
        # not exist timeout,http_proxy,https_proxy
        jalc = JALCURL("10.5109/16119")
        assert jalc._doi == "10.5109/16119"
        assert jalc._timeout == 5
        assert jalc._proxy == {"http":"","https":""}
        
        # exist timeout,http_proxy,https_proxy
        jalc = JALCURL("10.5109/16119",timeout=10,http_proxy="test_http_proxy",https_proxy="test_https_proxy")
        assert jalc._doi == "10.5109/16119"
        assert jalc._timeout == 10
        assert jalc._proxy == {"http":"test_http_proxy","https":"test_https_proxy"}
        

#     def _create_endpoint(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestJALCURL::test_create_endpoint -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_create_endpoint(self):
        jalc = JALCURL("10.5109/16119")
        result = jalc._create_endpoint()
        assert result == "10.5109/16119"


#     def _create_url(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestJALCURL::test_create_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_create_url(self):
        jalc = JALCURL("10.5109/16119")
        result = jalc._create_url()
        assert result == "https://api.japanlinkcenter.org/dois/10.5109/16119"


#     def url(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestJALCURL::test_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_url(self):
        jalc = JALCURL("10.5109/16119")
        result = jalc.url
        assert result == "https://api.japanlinkcenter.org/dois/10.5109/16119"


#     def _do_http_request(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestJALCURL::test_do_http_request -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_do_http_request(self,mocker):
        mock_get = mocker.patch("weko_workspace.api.requests.get")
        jalc = JALCURL("10.5109/16119",timeout=5,http_proxy="test_http_proxy",https_proxy="test_https_proxy")
        jalc._do_http_request()
        mock_get.assert_called_once_with(
            "https://api.japanlinkcenter.org/dois/10.5109/16119",
            timeout=5,
            proxies={"http": "test_http_proxy", "https": "test_https_proxy"}
        )


#     def get_data(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestJALCURL::test_get_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_get_data(self, app):
        jalc = JALCURL("10.5109/16119")
        res = Response()
        res._content = b'{"key":"test response"}'
        res.status_code = 200
        
        with patch("weko_workspace.api.JALCURL._do_http_request",return_value=res):
            result = jalc.get_data()
            assert result == {"response":{"key":"test response"},"error":""}
        # statuscode != 200
        res.status_code = 400
        with patch("weko_workspace.api.JALCURL._do_http_request",return_value=res):
            result = jalc.get_data()
            assert result == {"response":"","error":""}
        
        # raise Exception
        with patch("weko_workspace.api.JALCURL._do_http_request",side_effect=Exception("request error")):
            result = jalc.get_data()
            assert result == {"response":"","error":"request error"}


# class DATACITEURL:
class TestDATACITEURL:
#     def __init__(self, naid, timeout=None, http_proxy=None, https_proxy=None):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestDATACITEURL::test__init__ -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test__init__(self):
        # not doi
        with pytest.raises(ValueError) as e:
            datacite = DATACITEURL(None)
            assert str(e) == "DOI is required."
        
        # not exist timeout,http_proxy,https_proxy
        datacite = DATACITEURL("10.5109/16119")
        assert datacite._doi == "10.5109/16119"
        assert datacite._timeout == 5
        assert datacite._proxy == {"http":"","https":""}
        
        # exist timeout,http_proxy,https_proxy
        datacite = DATACITEURL("10.5109/16119",timeout=10,http_proxy="test_http_proxy",https_proxy="test_https_proxy")
        assert datacite._doi == "10.5109/16119"
        assert datacite._timeout == 10
        assert datacite._proxy == {"http":"test_http_proxy","https":"test_https_proxy"}
        

#     def _create_endpoint(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestDATACITEURL::test_create_endpoint -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_create_endpoint(self):
        datacite = DATACITEURL("10.5109/16119")
        result = datacite._create_endpoint()
        assert result == "10.5109/16119"


#     def _create_url(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestDATACITEURL::test_create_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_create_url(self):
        datacite = DATACITEURL("10.5109/16119")
        result = datacite._create_url()
        assert result == "https://api.datacite.org/dois/10.5109/16119"


#     def url(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestDATACITEURL::test_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_url(self):
        datacite = DATACITEURL("10.5109/16119")
        result = datacite.url
        assert result == "https://api.datacite.org/dois/10.5109/16119"


#     def _do_http_request(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestDATACITEURL::test_do_http_request -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_do_http_request(self,mocker):
        mock_get = mocker.patch("weko_workspace.api.requests.get")
        datacite = DATACITEURL("10.5109/16119",timeout=5,http_proxy="test_http_proxy",https_proxy="test_https_proxy")
        datacite._do_http_request()
        mock_get.assert_called_once_with(
            "https://api.datacite.org/dois/10.5109/16119",
            timeout=5,
            proxies={"http": "test_http_proxy", "https": "test_https_proxy"}
        )


#     def get_data(self):
# .tox/c1/bin/pytest --cov=weko_workspace tests/test_api.py::TestDATACITEURL::test_get_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-workspace/.tox/c1/tmp
    def test_get_data(self, app):
        datacite = DATACITEURL("10.5109/16119")
        res = Response()
        res._content = b'{"key":"test response"}'
        res.status_code = 200
        
        with patch("weko_workspace.api.DATACITEURL._do_http_request",return_value=res):
            result = datacite.get_data()
            assert result == {"response":{"key":"test response"},"error":""}
        # statuscode != 200
        res.status_code = 400
        with patch("weko_workspace.api.DATACITEURL._do_http_request",return_value=res):
            result = datacite.get_data()
            assert result == {"response":"","error":""}
        
        # raise Exception
        with patch("weko_workspace.api.DATACITEURL._do_http_request",side_effect=Exception("request error")):
            result = datacite.get_data()
            assert result == {"response":"","error":"request error"}

