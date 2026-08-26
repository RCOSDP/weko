from mock import patch
from flask import url_for


# .tox/c1/bin/pytest --cov=weko_handle tests/test_views.py::test_index -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-handle/.tox/c1/tmp
def test_index(app, client):
    url = url_for(
        "weko_handle.index", format="json", _external=True
    )
    res = client.get(url)
    assert res.status_code == 200


# def dbsession_clean(exception):
def test_dbsession_clean(app):
    from weko_handle.views import dbsession_clean

    with patch("weko_handle.views.db.session.commit", side_effect=KeyError('test')):
        dbsession_clean(exception=None)
