import pytest
import json
from mock import patch, MagicMock
from flask import Flask, json, jsonify, session, url_for
from invenio_accounts.testutils import login_user_via_session


class MockHandleClient:
    class MockClient:
        def __init__(self):
            pass

        def register_handle(self, pid=None, location=None, overwrite=None):
            return '123/456'

        def retrieve_handle_record_json(self, handle=None):
            return {'test': 'data'}

    def __init__(self):
        pass

    def instantiate_with_credentials(self, credential=None):
        return self.MockClient()


# .tox/c1/bin/pytest --cov=weko_handle tests/test_views.py::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-handle/.tox/c1/tmp
def test_index(app, client):
    url = url_for(
        "weko_handle.index", format="json", _external=True
    )
    res = client.get(url)
    assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_handle tests/test_views.py::test_retrieve_handle -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-handle/.tox/c1/tmp
def test_retrieve_handle(app, client):
    url = url_for(
        "weko_handle.retrieve_handle", format="json", _external=True
    )
    mock_handle_client = MagicMock(side_effect=MockHandleClient)
    with patch('weko_handle.api.EUDATHandleClient', mock_handle_client):
        with pytest.raises(Exception) as e:
            client.post(url)
        assert e.type==TypeError
        res = client.post(url, data={'handle': ''})
        assert res.status_code == 200
        res = client.post(url, data={'handle': '123/456'})
        assert res.status_code == 200
        app.config['WEKO_HANDLE_CREDS_JSON_PATH'] = ''
        with pytest.raises(Exception) as e:
            client.post(url, data={'handle': '123/456'})
        assert e.type==TypeError


# .tox/c1/bin/pytest --cov=weko_handle tests/test_views.py::test_register_handle -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-handle/.tox/c1/tmp
def test_register_handle(app, client):
    url = url_for(
        "weko_handle.register_handle", format="json", _external=True
    )
    mock_handle_client = MagicMock(side_effect=MockHandleClient)
    with patch('weko_handle.api.EUDATHandleClient', mock_handle_client):
        with pytest.raises(Exception) as e:
            client.post(url)
        assert e.type==TypeError
        res = client.post(url, data={'location': ''})
        assert res.status_code == 200
        res = client.post(url, data={'location': 'http://localhost/123'})
        assert res.status_code == 200
        res = client.post(url, data={'location': 'http://localhost/records/123'})
        assert res.status_code == 200
        app.config['WEKO_HANDLE_CREDS_JSON_PATH'] = ''
        res = client.post(url, data={'location': 'http://localhost/records/123'})
        assert res.status_code == 200


# .tox/c1/bin/pytest --cov=weko_handle tests/test_views.py::test_delete_handle -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-handle/.tox/c1/tmp
def test_delete_handle(app, client):
    url = url_for(
        "weko_handle.delete_handle", format="json", _external=True
    )
    mock_handle_client = MagicMock(side_effect=MockHandleClient)
    with patch('weko_handle.api.EUDATHandleClient', mock_handle_client):
        with pytest.raises(Exception) as e:
            client.post(url)
        assert e.type==TypeError
        res = client.post(url, data={'hdl': ''})
        assert res.status_code == 200
        res = client.post(url, data={'hdl': '123/456'})
        assert res.status_code == 200
        app.config['WEKO_HANDLE_CREDS_JSON_PATH'] = ''
        res = client.post(url, data={'hdl': '123/456'})
        assert res.status_code == 200


# def dbsession_clean(exception):
def test_dbsession_clean(app):
    from weko_handle.views import dbsession_clean

    with patch("weko_handle.views.db.session.commit", side_effect=KeyError('test')):
        dbsession_clean(exception=None)
