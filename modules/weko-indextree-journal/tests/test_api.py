import pytest
import json
from mock import patch, MagicMock

from weko_indextree_journal.api import Journals


sample = Journals()


# def create
def test_create(i18n_app):
    journals = {"id": "test"}

    # Exception coverage
    sample.create(journals=journals)


# def get_journal
def test_get_journal(i18n_app):
    journal_id = 1

    # Exception coverage
    sample.get_journal(journal_id=journal_id)


# def get_journal_by_index_id
def test_get_journal_by_index_id(i18n_app):
    # Exception coverage
    sample.get_journal_by_index_id(index_id=())


# def get_all_journals
def test_get_all_journals(i18n_app):
    # Exception coverage
    sample.get_all_journals()
