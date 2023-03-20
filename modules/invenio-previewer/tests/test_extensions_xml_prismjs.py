import pytest
from mock import patch, MagicMock

from invenio_previewer.extensions.xml_prismjs import validate_xml


# def validate_xml(file): 
def test_validate_xml(app):
    file = MagicMock()
    max_file_size = app.config.get('PREVIEWER_MAX_FILE_SIZE_BYTES', 1 * 1024 * 1024)
    file.size = max_file_size + 1

    assert validate_xml(file=file) == False

    file.size = max_file_size - 1

    # Exception coverage
    assert validate_xml(file=file) == False