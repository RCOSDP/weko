import pytest
from mock import patch, MagicMock

from weko_records.serializers.dc import DcWekoEntryExtension


# class DcWekoEntryExtension(JSONSerializer): 
# def extend_atom
def test_extend_atom(app):
    test = DcWekoEntryExtension()
    def _extend_xml(item):
        return item

    test._extend_xml = _extend_xml
    entry = "entry"

    assert test.extend_atom(
        entry=entry
    ) != None


# def extend_jpcoar
def test_extend_jpcoar(app):
    test = DcWekoEntryExtension()
    def _extend_xml(item):
        return item

    test._extend_xml = _extend_xml
    item = "item"

    assert test.extend_jpcoar(
        item=item
    ) != None