
import functools
import pytest
from mock import MagicMock, patch
from requests import Response

from weko_items_ui.linkage import Researchmap


def test__init__():
    assert Researchmap().token == ""

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_linkage.py::test_create_access_token -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_create_access_token(app):
    jwt = "jwt"
    res_ok = Response()
    res_ok._content = b'{"access_token":"foo"}'
    with patch("weko_items_ui.linkage.requests.post" , return_value=res_ok):
        assert "foo" == Researchmap.create_access_token(jwt, 'get')
        assert "foo" == Researchmap.create_access_token(jwt, 'post')
        assert "foo" == Researchmap.create_access_token(jwt, 'hoge')

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_linkage.py::test_create_jwt -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_create_jwt(app ):
    with pytest.raises(expected_exception=Exception):
        jwt = Researchmap.create_jwt()

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_linkage.py::test_create_jwt2 -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_create_jwt2(app , db_admin_setting):
    with patch("weko_items_ui.linkage.jwt.encode", return_value="result"):
        assert "result" == Researchmap.create_jwt()

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_linkage.py::test_create_jwt3 -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_create_jwt3(app , db_invalid_admin_setting):
    with pytest.raises(expected_exception=Exception):
        jwt = Researchmap.create_jwt()

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_linkage.py::test_get_reseacher -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_get_reseacher(app):
    with patch("weko_items_ui.linkage.requests.get" , return_value=""):
        assert Researchmap.get_reseacher(
            token = 'token'
            ,parmalink = ''
            , achievement_type= ''
            , achievement_id= ""
        ) == ""

def test_post_achievement_datas(app):
    with patch("weko_items_ui.linkage.requests.post" , return_value=""):
        assert Researchmap.post_achievement_datas(
            token = "token"
            ,body = ""
        ) == ""

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_linkage.py::test_get_token -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_get_token(app, db_admin_setting):
    with patch("weko_items_ui.linkage.jwt.encode", return_value="result"):
        res_ok = Response()
        res_ok._content = b'{"access_token":"foo"}'
        with patch("weko_items_ui.linkage.requests.post" , return_value=res_ok):
            rm = Researchmap()
            assert rm.get_token("get") == "foo"
            assert rm.get_token("post") == "foo"

#  .tox/c1/bin/pytest --cov=weko_items_ui tests/test_linkage.py::test_get_data -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_get_data(app, db_admin_setting):
    with patch("weko_items_ui.linkage.jwt.encode", return_value="result"):
        res_ok = Response()
        res_ok._content = b'{"access_token":"foo"}'
        with patch("weko_items_ui.linkage.requests.post" , return_value=res_ok):
            with patch("weko_items_ui.linkage.requests.get" , return_value=res_ok):
                rm = Researchmap()
                assert rm.get_data("parmalink","published_papar","123456")

#  .tox/c1/bin/pytest --cov=weko_items_ui tests/test_linkage.py::test_get_data_rases -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
@pytest.mark.parametrize(
    ["parmalink", "achievenent_id"],
    [
        ('ab', '123456'),
        ('123456789012345678901', '123456'),
        ('parmaliあ', '123456'),
        ('parmali　', '123456'),
        ('parmali ', '123456'),
        ('parmali%', '123456'),
        ('parmali#', '123456'),
        ('parmali<', '123456'),
        ('parmali>', '123456'),
        ('parmali+', '123456'),
        ('parmali\"', '123456'),
        ('parmali\'', '123456'),
        ('parmali\\', '123456'),
        ('parmali&', '123456'),
        ('parmali?', '123456'),
        ('parmali=', '123456'),
        ('parmali~', '123456'),
        ('parmali:', '123456'),
        ('parmali;', '123456'),
        ('parmali,', '123456'),
        ('parmali@', '123456'),
        ('parmali$', '123456'),
        ('parmali^', '123456'),
        ('parmali|', '123456'),
        ('parmali[', '123456'),
        ('parmali]', '123456'),
        ('parmali!', '123456'),
        ('parmali(', '123456'),
        ('parmali)', '123456'),
        ('parmali*', '123456'),
        ('parmali/', '123456'),
        ('parmalink', '12345a'),
        ('parmalink', '12345A'),
        ('parmalink', '12345あ'),
        ('parmalink', '12345-'),
        ('parmalink', '12345 '),
        ('parmalink', '12345　')
    ],
)
def test_get_data_rases(parmalink, achievenent_id):
    with pytest.raises(Exception):
        with patch("weko_items_ui.linkage.jwt.encode", return_value="result"):
            res_ok = Response()
            res_ok._content = b'{"access_token":"foo"}'
            with patch("weko_items_ui.linkage.requests.post" , return_value=res_ok):
                with patch("weko_items_ui.linkage.requests.get" , return_value=res_ok):
                    rm = Researchmap()
                    assert rm.get_data(parmalink,"published_papar",achievenent_id)


# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_linkage.py::test_post_data -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_post_data(app, db_admin_setting):
    with patch("weko_items_ui.linkage.jwt.encode", return_value="result"):
        res_ok = Response()
        res_ok._content = b'{"access_token":"foo"}'
        with patch("weko_items_ui.linkage.requests.post" , return_value=res_ok):
            with patch("weko_items_ui.linkage.requests.get" , return_value=res_ok):
                rm = Researchmap()
                assert rm.post_data(b"{json : parmalink ,published_papar:123456}")

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_linkage.py::test_get_result -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_get_result(app, db_admin_setting):
    with patch("weko_items_ui.linkage.jwt.encode", return_value="result"):
        res_wait = Response()
        res_wait.status_code = 200
        res_wait._content = b'{"code":102}'

        res_ok = Response()
        res_ok.status_code = 200
        res_ok._content = b'{"code":"200"}'
        with patch("weko_items_ui.linkage.requests.post" , return_value=res_ok):
            with patch("weko_items_ui.linkage.requests.get" , side_effect=[res_wait,res_ok]):
                rm = Researchmap()
                assert rm.get_result("url")

# .tox/c1/bin/pytest --cov=weko_items_ui tests/test_linkage.py::test_retry -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko_items_ui/.tox/c1/tmp --full-trace
def test_retry(app):

    # mock = MagicMock()
    res_401 = Response()
    res_401.status_code = 401
    res_401._content = b"""{"error": "invalid_token","error_description": "Invalid field selection hogehoge","error_uri": "http://xxxxx.xxxxx","field_name": "gender","errors": [{ "error": "error","error_description": "error_description","field_name": "field_name"}]}
    {"error": "invalid_token","error_description": "Invalid field selection hogehoge","error_uri": "http://xxxxx.xxxxx","field_name": "gender","errors": [{ "error": "error","error_description": "error_description","field_name": "field_name"}]}"""

    res_402 = Response()
    res_402.status_code = 402
    res_402._content = b"""{"error": "invalid_token","error_description": "Invalid field selection hogehoge","error_uri": "http://xxxxx.xxxxx","field_name": "gender","errors": [{ "error": "error","error_description": "error_description","field_name": "field_name"}]}
    {"error": "invalid_token","error_description": "Invalid field selection hogehoge","error_uri": "http://xxxxx.xxxxx","field_name": "gender","errors": [{ "error": "error","error_description": "error_description","field_name": "field_name"}]}"""


    res_200 = Response()
    res_200.status_code = 200
    res_200._content = b'{"code": 200,"url": "https://api.researchmap.jp/_bulk_results?id=xxxxx","bulk_url": "https://api.researchmap.jp/_bulk?id=xxxxx"}'

    assert res_401.text == Researchmap().retry(functools.partial(lambda : res_401))
    assert res_402.text == Researchmap().retry(functools.partial(lambda : res_402))
    assert res_200.text == Researchmap().retry(functools.partial(lambda : res_200))
    # Researchmap().retry(functools.partial(lambda : res_200))
