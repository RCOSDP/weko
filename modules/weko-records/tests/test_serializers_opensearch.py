import pytest
from mock import patch, MagicMock

from weko_records.serializers.opensearch import (
    OpensearchBaseExtension,
    OpensearchEntryExtension
)


# class OpensearchBaseExtension
# def extend_atom
def test_extend_atom_OpensearchBaseExtension(app):
    test = OpensearchBaseExtension()

    def _extend_xml(item):
        return item

    test._extend_xml = _extend_xml

    assert test.extend_atom(atom_feed="atom_feed") == "atom_feed"


# class OpensearchEntryExtension
# def extend_atom
def test_extend_atom_OpensearchEntryExtension(app):
    test = OpensearchEntryExtension()

    def _extend_xml(item):
        return item

    test._extend_xml = _extend_xml

    assert test.extend_atom(entry="entry") == "entry"