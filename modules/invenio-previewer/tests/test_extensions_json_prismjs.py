import pytest
import json
from mock import patch, MagicMock

from invenio_previewer.extensions.json_prismjs import render, validate_json


# def validate_json(file): 
def test_validate_json_2(app):
    test_file = MagicMock()
    app.config['PREVIEWER_MAX_FILE_SIZE_BYTES'] = 1000
    test_file.size = app.config['PREVIEWER_MAX_FILE_SIZE_BYTES'] - 1

    # Exception coverage
    try:
        validate_json(file=test_file)
    except:
        pass

    json_data = {
        "@context": [
            "iiif",
            "presentation"
        ],
        "size": 999,
        "file": "file_999"
    }
    class MockOpen:
        def read(self):
            return json.dumps(json_data).encode()
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_value, traceback):
            pass
    test_file.open = MagicMock(return_value=MockOpen())
    assert validate_json(file=test_file)

# def render(file):
def test_render():
    test_file = MagicMock()
    json_data = {"test": "あいうえお"}
    class MockOpen:
        def read(self):
            return json.dumps(json_data).encode()
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_value, traceback):
            pass
    test_file.open = MagicMock(return_value=MockOpen())
    with patch('invenio_previewer.extensions.json_prismjs.detect_encoding', return_value='utf-8'):
        ret = render(file=test_file)
        assert ret == '{\n    "test": "あいうえお"\n}'
