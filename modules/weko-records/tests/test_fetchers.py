import pytest
from mock import patch, MagicMock

from weko_records.fetchers import weko_record_fetcher, weko_doi_fetcher


# def weko_record_fetcher(dummy_record_uuid, data): 
def test_weko_record_fetcher(app):
    dummy_record_uuid = "test"
    data = {"recid": "recid"}

    assert weko_record_fetcher(dummy_record_uuid=dummy_record_uuid, data=data) != None


# def weko_doi_fetcher(dummy_record_uuid, data): 
def test_weko_doi_fetcher(app):
    dummy_record_uuid = "test"
    data = {"doi": "doi"}

    assert weko_doi_fetcher(dummy_record_uuid=dummy_record_uuid, data=data) != None