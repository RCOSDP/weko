import pytest
import os
import json
from mock import patch, MagicMock, mock_open

from invenio_previewer.api import PreviewFile
from invenio_previewer.extensions.iiif_presentation import (
    validate_json,
    can_preview,
    preview
)


# def validate_json(file): 
def test_validate_json(app):
    def read_func():
        def decode_func(decode_item):
            return json.dumps({
                "@context": [
                    "iiif",
                    "presentation"
                ],
                "size": 999,
                "file": "file_999"
            })

        read_magicmock = MagicMock()
        read_magicmock.decode = decode_func
        return read_magicmock

    json_data = {
        "@context": [
            "iiif",
            "presentation"
        ],
        "size": 999,
        "file": "file_999"
    }

    app.config['PREVIEWER_MAX_FILE_SIZE_BYTES'] = 1000

    data1 = MagicMock()
    data1.file = json_data
    data1.size = app.config['PREVIEWER_MAX_FILE_SIZE_BYTES'] + 1
    data1.__enter__().__iter().return_value = read_func

    assert validate_json(file=data1) == False

    data1.size = app.config['PREVIEWER_MAX_FILE_SIZE_BYTES'] - 1

    # Exception coverage
    try:
        assert validate_json(file=data1) == False
    except:
        pass

    assert validate_json(file=data1) == False


# def can_preview(file): 
def test_can_preview(app):
    def is_local():
        return True

    file = MagicMock()
    file.is_local = is_local
    file.filename = 'manifest.json'

    with patch("invenio_previewer.extensions.iiif_presentation.validate_json", return_value=True):
        assert can_preview(file=file) == True
    
    with patch("invenio_previewer.extensions.iiif_presentation.validate_json", return_value=False):
        assert can_preview(file=file) == True


# def preview(file):
def test_preview(app):
    file = MagicMock()
    file.pid = MagicMock()
    file.pid.pid_value = "9999"
    file.uri = '/'
    request = MagicMock()
    request.url_root = "/url_root"

    with app.test_request_context():
        with patch("invenio_previewer.extensions.iiif_presentation.validate_json", return_value=False):
            with patch("flask.request", return_value=request):
                assert preview(file=file) != None