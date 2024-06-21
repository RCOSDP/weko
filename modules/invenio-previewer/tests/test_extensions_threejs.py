import pytest
from mock import patch, MagicMock

from invenio_previewer.extensions.threejs import preview


# def preview(file): 
def test_preview(app):
    file = MagicMock()
    file.size = 9999

    assert "<!DOCTYPE html>" in preview(file=file)