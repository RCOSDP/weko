import pytest
from flask import Flask, Response

from invenio_s3.helpers import redirect_stream

@pytest.fixture
def app():
    app = Flask("testapp")
    app.response_class = Response
    return app

def dummy_s3_url_builder(**kwargs):
    # kwargsにはResponseContentType, ResponseContentDispositionが入る
    return "https://dummy-s3-url"

def test_redirect_stream_basic(app):
    with app.app_context():
        resp = redirect_stream(
            s3_url_builder=dummy_s3_url_builder,
            filename="test.txt",
            mimetype=None,
            restricted=True,
            as_attachment=False,
            trusted=False
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "https://dummy-s3-url"
        assert resp.headers["Content-Disposition"].startswith("inline")
        assert resp.mimetype == "text/plain"

def test_redirect_stream_as_attachment(app):
    with app.app_context():
        resp = redirect_stream(
            s3_url_builder=dummy_s3_url_builder,
            filename="テストファイル.txt",
            mimetype=None,
            restricted=True,
            as_attachment=True,
            trusted=False
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "https://dummy-s3-url"
        assert resp.headers["Content-Disposition"].startswith("attachment")
        assert resp.mimetype == "text/plain" or resp.mimetype == "application/octet-stream"

def test_redirect_stream_trusted(app):
    with app.app_context():
        resp = redirect_stream(
            s3_url_builder=dummy_s3_url_builder,
            filename="test.txt",
            mimetype="application/pdf",
            restricted=True,
            as_attachment=False,
            trusted=True
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "https://dummy-s3-url"
        assert resp.headers["Content-Disposition"].startswith("inline")
        assert resp.mimetype == "application/pdf"
        # trusted=Trueの場合、セキュリティヘッダが付与されない
        assert "X-Content-Type-Options" not in resp.headers

def test_redirect_stream_octet_stream(app):
    with app.app_context():
        resp = redirect_stream(
            s3_url_builder=dummy_s3_url_builder,
            filename="unknownfile.unknown",
            mimetype=None,
            restricted=True,
            as_attachment=False,
            trusted=False
        )
        assert resp.status_code == 302
        assert resp.headers["Content-Disposition"].startswith("attachment")
        assert resp.mimetype == "application/octet-stream"
