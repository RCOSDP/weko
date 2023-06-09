import pytest
from mock import patch, MagicMock

from weko_records.serializers.prism import (
    PrismBaseExtension,
    PrismEntryExtension
)


# class PrismBaseExtension
# def extend_atom(self, atom_feed): 
def test_serialize_search_PrismBaseExtension(app):
    test = PrismBaseExtension()

    def _extend_xml(item):
        return item
    
    test._extend_xml = _extend_xml
    atom_feed = "atom_feed"

    assert test.extend_atom(atom_feed=atom_feed) != None


# def issn(self, issn=None, replace=False): 
def test_issn_PrismBaseExtension(app):
    test = PrismBaseExtension()

    def _prism_issn():
        return True
    
    test._prism_issn = _prism_issn
    issn = {}

    assert test.issn(
        issn=issn,
        replace=True
    ) != None


# def number(self, issn=None, replace=False): 
def test_number_PrismBaseExtension(app):
    test = PrismBaseExtension()

    def _prism_number():
        return True
    
    test._prism_number = _prism_number
    number = {}

    assert test.number(
        number=number,
        replace=True
    ) != None


# class PrismEntryExtension
# def extend_atom(self, atom_feed): 
def test_serialize_search_PrismEntryExtension(app):
    test = PrismEntryExtension()

    def _extend_xml(item):
        return item
    
    test._extend_xml = _extend_xml
    entry = "entry"

    assert test.extend_atom(entry=entry) != None
