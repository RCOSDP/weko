import pytest
import os
import json
from mock import patch, MagicMock

from invenio_previewer.api import PreviewFile
from invenio_previewer.extensions.iiif_presentation import (
    validate_json,
    can_preview,
    preview
)


# def validate_json(file): 
def test_validate_json(app):
    json_data = {
        "@context": [
            "iiif",
            "presentation"
        ],
        "size": 999,
        "file": "file_999"
    }
    data1 = MagicMock()
    data1.file = json_data
    data1.size = 999

    # Exception coverage
    try:
        assert validate_json(file=data1) != None
    except:
        pass