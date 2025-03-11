import pytest
import json
from mock import patch
from sqlalchemy.exc import SQLAlchemyError

from weko_indextree_journal.api import Journals

from weko_indextree_journal.models import Journal


#class Journals(object):
class TestJournals:
#    def create(cls, journals=None):
# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_api.py::TestJournals::test_create -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_create(self, i18n_app,test_indices):
        # journals is not dict
        journals = "not dict"
        result = Journals.create(journals)
        assert result == None

        # id not in journals
        journals = {}
        result = Journals.create(journals)
        assert result == None

        # index_id not in journals
        journals = {"id": 1}
        result = Journals.create(journals)
        assert result == None

        # not exist index
        journals = {"id": 1,"index_id":1000}
        result = Journals.create(journals)
        assert result == None

        # success create
        journals = {"id": 1,"index_id":1}
        result = Journals.create(journals)
        assert result == True
        assert Journal.query.filter_by(id=1).one_or_none()

        # raise IntegrityError
        journals = {"id": "not int","index_id":1}
        result = Journals.create(journals)
        assert result == False

        # raise Exception
        with patch("weko_indextree_journal.api.Indexes.get_index",side_effect=Exception("test_error")):
            journals = {"id": 2,"index_id":1}
            result = Journals.create(journals)
            assert result == False

#    def update(cls, journal_id, **data):
# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_api.py::TestJournals::test_update -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_update(self,i18n_app,users,test_journals):
        data = {
            "publication_title": "test journal 1 after"
        }
        with patch("flask_login.utils._get_user", return_value=users[0]['obj']):
            result = Journals.update(1,**data)
            assert result.publication_title == "test journal 1 after"

        result = Journals.update(100,**data)
        assert result == None

        with patch("weko_indextree_journal.api.Journal",side_effect=Exception("test_error")):
            result = Journals.update(1,**data)
            assert result == None
#    def delete(cls, journal_id):
# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_api.py::TestJournals::test_delete -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_delete(self,i18n_app,test_journals):
        journal_id = 1
        # success delete
        Journals.delete(journal_id)

        # cannot find data
        Journals.delete(journal_id)

        # raise Exception
        with patch("weko_indextree_journal.api.Journals.get_journal",side_effect=Exception("test_error")):
            Journals.delete(journal_id)

#    def get_journal(cls, journal_id):
# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_api.py::TestJournals::test_get_journal -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_get_journal(self, i18n_app,test_journals):
        journal_id = 1
        test = {'access_type': 'F', 'coverage_depth': 'abstract', 'coverage_notes': '', 'date_first_issue_online': '2022-01-01', 'date_last_issue_online': '2022-01-01', 'date_monograph_published_online': '', 'date_monograph_published_print': '', 'deleted': '', 'embargo_info': '', 'first_author': '', 'first_editor': '', 'ichushi_code': '', 'id': 1, 'index_id': 1, 'is_output': True, 'jstage_code': '', 'language': 'en', 'monograph_edition': '', 'monograph_volume': '', 'ncid': '', 'ndl_bibid': '', 'ndl_callno': '', 'num_first_issue_online': '', 'num_first_vol_online': '', 'num_last_issue_online': '', 'num_last_vol_online': '', 'online_identifier': '', 'owner_user_id': 0, 'parent_publication_title_id': '', 'preceding_publication_title_id': '', 'print_identifier': '', 'publication_title': 'test journal 1', 'publication_type': 'serial', 'publisher_name': '', 'title_alternative': '', 'title_id': 1, 'title_transcription': '', 'title_url': 'search?search_type=2&q=1', 'abstract':'', 'code_issnl':''}
        result = Journals.get_journal(journal_id)
        assert result == test

        # not exist
        journal_id = 1000
        test = []
        result = Journals.get_journal(journal_id)
        assert result == test

        # raise SQLAlchemyError
        journal_id = {}
        result = Journals.get_journal(journal_id)

        # raise Exception
        with patch("weko_indextree_journal.api.Journal",side_effect=Exception("test_error")):
            journal_id = 1000
            result = Journals.get_journal(journal_id)
            assert result == None

#    def get_journal_by_index_id(cls, index_id):
# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_api.py::TestJournals::test_get_journal_by_index_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_get_journal_by_index_id(self, i18n_app, test_journals):
        index_id = 1
        test = {'access_type': 'F', 'coverage_depth': 'abstract', 'coverage_notes': '', 'date_first_issue_online': '2022-01-01', 'date_last_issue_online': '2022-01-01', 'date_monograph_published_online': '', 'date_monograph_published_print': '', 'deleted': '', 'embargo_info': '', 'first_author': '', 'first_editor': '', 'ichushi_code': '', 'id': 1, 'index_id': 1, 'is_output': True, 'jstage_code': '', 'language': 'en', 'monograph_edition': '', 'monograph_volume': '', 'ncid': '', 'ndl_bibid': '', 'ndl_callno': '', 'num_first_issue_online': '', 'num_first_vol_online': '', 'num_last_issue_online': '', 'num_last_vol_online': '', 'online_identifier': '', 'owner_user_id': 0, 'parent_publication_title_id': '', 'preceding_publication_title_id': '', 'print_identifier': '', 'publication_title': 'test journal 1', 'publication_type': 'serial', 'publisher_name': '', 'title_alternative': '', 'title_id': 1, 'title_transcription': '', 'title_url': 'search?search_type=2&q=1', 'abstract':'', 'code_issnl':''}
        result = Journals.get_journal_by_index_id(index_id)
        assert result == test

        # not exist
        index_id = 1000
        test = {}
        result = Journals.get_journal_by_index_id(index_id)
        assert result == test

        # raise SQLAlchemyError
        index_id = {}
        result = Journals.get_journal_by_index_id(index_id)

        # raise Exception
        with patch("weko_indextree_journal.api.Journal",side_effect=Exception("test_error")):
            index_id = 1000
            result = Journals.get_journal_by_index_id(index_id)
            assert result == None


#    def get_all_journals(cls):
# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_api.py::TestJournals::test_get_all_journals -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_get_all_journals(self,db,test_indices):
        # not exist journal
        result = Journals.get_all_journals()
        assert result == None

        # raise Exception
        with patch("weko_indextree_journal.api.current_app.logger.info",side_effect=Exception("test_error")):
            result = Journals.get_all_journals()
            assert result == None


        journal = Journal(
            id=1,
            index_id=1,
            publication_title="test journal 1",
            date_first_issue_online="2022-01-01",
            date_last_issue_online="2022-01-01",
            title_url="search?search_type=2&q=1",
            title_id="1",
            coverage_depth="abstract",
            publication_type="serial",
            access_type="F",
            language="en",
            is_output=True,
            abstract='',
            code_issnl=''
        )
        db.session.add(journal)
        db.session.commit()
        # exist journal
        result = Journals.get_all_journals()
        assert [r.id for r in result] == [1]

        # raise SQLAlchemyError
        with patch("weko_indextree_journal.api.Journal",side_effect=SQLAlchemyError):
            result = Journals.get_all_journals()
            assert result == None

