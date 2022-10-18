
from mock import patch
from datetime import datetime
from calendar import timegm

from invenio_s3.helpers import redirect_stream

# .tox/c1/bin/pytest --cov=invenio_s3 tests/test_helpers.py::test_redirect_stream -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-s3/.tox/c1/tmp
def test_redirect_stream(base_app):
    with base_app.test_request_context():
        url = "http://test.com"
        filename = "test.txt"
        size = 15
        chunk_size = 5 * 1024 * 1024  # 5MiB
        etag = "test_etag"
        content_md5="test_md5"
        now = datetime(2022,10,1,2,3,4,5)
        mtime = timegm(now.timetuple())
        
        result = redirect_stream(
            url,
            filename,
            size,
            mtime,
            mimetype="text/plain",
            restricted=True,
            as_attachment=False,
            etag=etag,
            content_md5=content_md5,
            chunk_size=chunk_size,
            conditional=False,
            trusted=False
        )
        headers = result.headers
        assert headers['Content-Length'] == str(size)
        assert headers['Content-MD5'] == content_md5
        assert headers['Location'] == url
        assert headers['Content-Security-Policy'] == "default-src 'none';"
        assert headers['Content-Disposition'] == "inline"
        assert headers["Etag"] == '"test_etag"'
        assert headers["Last-Modified"] == now.strftime("%a, %d %b %Y %H:%M:%S GMT")
        
        result = redirect_stream(
            url,
            "test.txt",
            size,
            None,
            mimetype=None,
            restricted=False,
            as_attachment=True,
            etag=None,
            content_md5=None,
            chunk_size=chunk_size,
            conditional=True,
            trusted=True
        )
        headers = result.headers
        assert "Content-MD5" not in headers
        assert "Content-Security-Policy" not in headers
        assert headers["Content-Disposition"] == "attachment; filename=test.txt"
        assert "Etag" not in headers
        assert "Lost-Modified" not in headers
        assert headers["Cache-Control"] == "public, max-age=43200"

        # raise UnicodeEncodeError
        with patch("invenio_s3.helpers.current_app.get_send_file_max_age",return_value=None):
                result = redirect_stream(
                    url,
                    u"test\u201Cfile\u201D",
                    size,
                    None,
                    mimetype=None,
                    restricted=False,
                    as_attachment=True,
                    etag=None,
                    content_md5=None,
                    chunk_size=chunk_size,
                    conditional=True,
                    trusted=True
                )
                headers = result.headers
                assert "Content-MD5" not in headers
                assert "Content-Security-Policy" not in headers
                assert headers["Content-Disposition"] == "attachment; filename*=UTF-8''test%E2%80%9Cfile%E2%80%9D; filename=testfile"
                assert "Etag" not in headers
                assert "Lost-Modified" not in headers
                assert headers["Cache-Control"] == "public"
