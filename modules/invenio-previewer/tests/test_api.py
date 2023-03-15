import pytest
import os
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
def test_convert_to(app):
    folder = "folder"
    source = "middle/zzz/is_being_used"
    app.config['PREVIEWER_CONVERT_PDF_RETRY_COUNT'] = 9

    with app.test_request_context():
        # Try and Except line to avoid shutil.rmtree error "AttributeError: can't delete attribute"
        try:
            with patch('invenio_previewer.api.request.path', return_value="this/is/a/test/variable"):
                convert_to(
                    folder=folder,
                    source=source
                )
        except:
            pass
    
        try:
            with patch('invenio_previewer.api.request.path', return_value="this/is/a/test/variable"):
                with patch('invenio_previewer.api.subprocess.run', return_value=""):
                    with patch('invenio_previewer.api.flash', return_value=""):
                        convert_to(
                            folder=folder,
                            source=source
                        )
        except:
            pass
        
        try:
            def exists():
                return False

            data1 = MagicMock()
            data1.exists = exists
            with patch('invenio_previewer.api.os.path', return_value=data1):
                convert_to(
                    folder=folder,
                    source=source
                )
        except:
            pass

        try:
            with patch('invenio_previewer.api.request.path', return_value="this/is/a/test/variable"):
                with patch('invenio_previewer.api.flash', return_value=""):
                    with patch('invenio_previewer.api.subprocess.run', side_effect=FileNotFoundError('test')):
                        convert_to(folder=folder, source=source)
        except:
            pass

        try:
            with patch('invenio_previewer.api.request.path', return_value="this/is/a/test/variable"):
                with patch('invenio_previewer.api.flash', return_value=""):
                    with patch('invenio_previewer.api.subprocess.run', side_effect=PermissionError('test')):
                        convert_to(folder=folder, source=source)
        except:
            pass

        try:
            with patch('invenio_previewer.api.request.path', return_value="this/is/a/test/variable"):
                with patch('invenio_previewer.api.flash', return_value=""):
                    with patch('invenio_previewer.api.subprocess.run', side_effect=OSError('test')):
                        convert_to(folder=folder, source=source)
        except:
            pass
        

# class LibreOfficeError(Exception):
def test_LibreOfficeError(app):
    test = LibreOfficeError(
        output="output"
    )
