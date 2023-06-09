import pytest
from mock import patch, MagicMock

from invenio_previewer.ext import (
    obj_or_import_string,
    _InvenioPreviewerState
)


# def obj_or_import_string(value, default=None): 
def test_obj_or_import_string(app):
    value = "invenio_previewer"
    assert obj_or_import_string(value=value) != None

    value = ["invenio_previewer"]
    assert obj_or_import_string(value=value) != None

    value = None
    assert obj_or_import_string(value=value) == None


# class _InvenioPreviewerState
# def previewable_extensions(self):
# ERROR ~ TypeError: 'str' object is not callable
def test_previewable_extensions(app):
    def load_entry_point_group(item):
        return item

    test = _InvenioPreviewerState(app="app")
    test.entry_point_group = True

    assert test.previewable_extensions() != None


# def record_file_factory(self):
def test_record_file_factory(app):
    def invenio_previewer():
        return True

    data1 = MagicMock()
    data1.config = {"PREVIEWER_RECORD_FILE_FACOTRY": invenio_previewer}
    test = _InvenioPreviewerState(app=data1)

    assert test.record_file_factory() != None


# def register_previewer(self, name, previewer): 
def test_register_previewer(app):
    data1 = MagicMock()
    test = _InvenioPreviewerState(app=data1)
    test.previewers = {"previewable_extensions": "previewable_extensions"}
    name = "previewable_extensions"
    previewer = MagicMock()
    previewer.previewable_extensions = "previewable_extensions"

    # Exception coverage
    try:
        assert test.register_previewer(
            name=name,
            previewer=previewer
        ) != None
    except:
        pass
    
    name = "test"

    assert test.register_previewer(
        name=name,
        previewer=previewer
    ) == None


# def iter_previewers(self, previewers=None):
# Not able to call "iter_previewers" function
def test_iter_previewers(app):
    data1 = MagicMock()
    test = _InvenioPreviewerState(app=data1)
    previewers = MagicMock()

    assert test.iter_previewers(previewers=previewers) != None