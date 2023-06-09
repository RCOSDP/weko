import pytest
from mock import patch, MagicMock

from invenio_previewer.extensions.default import can_preview


# def can_preview(file): 
def test_can_preview(app):
    file = MagicMock()
    file.size = 9999

    assert can_preview(file=file) == True