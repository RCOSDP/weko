import pytest
import json
from mock import patch, MagicMock

from invenio_previewer.extensions.zip import make_tree, children_to_list


# def make_tree(file): 
def test_make_tree(app):
    def namelist():
        return ["name1", "name2"]

    def infolist():
        infolist_magicmock = MagicMock()
        infolist_magicmock.filename = " / / /"
        return [infolist_magicmock]

    file = MagicMock()

    data1 = MagicMock()
    data1.namelist = namelist
    data1.infolist = infolist

    app.config['PREVIEWER_ZIP_MAX_FILES'] = -1

    with patch('invenio_previewer.extensions.zip.zipfile.ZipFile', return_value=data1):
        assert make_tree(file=file) != None

        app.config['PREVIEWER_ZIP_MAX_FILES'] = 1
        assert make_tree(file=file) != None


# def children_to_list(node): 
def test_children_to_list(app):
    node = {
        "type": "item",
        "children": []
    }
    
    assert children_to_list(node=node).get("children") == None