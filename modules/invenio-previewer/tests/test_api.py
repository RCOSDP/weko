import pytest
from mock import patch, MagicMock

from invenio_previewer.api import PreviewFile, convert_to, LibreOfficeError


# class PreviewFile(object): 
# def bucket(self): 
def test_bucket_PreviewFile(app):
    test = PreviewFile(
        pid=1,
        record={},
        fileobj={}
    )
    test.file = MagicMock()
    test.file.bucket_id = MagicMock()

    assert test.bucket() != None


# def convert_to(folder, source): 
# RuntimeError: Working outside of request context.
# Line 133: pid_value = request.path.split('/').pop(2)
def test_convert_to(app):
    folder = "folder"
    source = "source/path"

    with patch('invenio_previewer.api.shutil.rmtree', return_value=""):
        convert_to(
            folder=folder,
            source=source
        )


# class LibreOfficeError(Exception):
def test_LibreOfficeError(app):
    test = LibreOfficeError(
        output="output"
    )
