import pytest
from mock import patch, MagicMock

from invenio_previewer.extensions.json_prismjs import validate_json


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