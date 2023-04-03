
from mock import patch
import pytest

from weko_indextree_journal.models import Journal, Journal_export_processing

# class Journal(db.Model, Timestamp):
class TestJournal:
#     def __iter__(self):
#     def __str__(self):
# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_models.py::TestJournal::test_str -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_str(self,test_journals):
        journal = Journal.query.first()
        assert str(journal) == 'Journal <id=1, index_name=test journal 1>'
        
# class Journal_export_processing(db.Model, Timestamp):
class TestJournal_export_processing:
#     def save_export_info(cls, data):
# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_models.py::TestJournal_export_processing::test_save_export_info -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
    def test_save_export_info(self,app,db):
        db_processing_status = Journal_export_processing()
        db_processing_status.status = False
        result = Journal_export_processing.save_export_info(db_processing_status)
        assert Journal_export_processing.query.filter_by(id=1).one().status == False
        
        # raise BaseException
        db_processing_status = Journal_export_processing()
        db_processing_status.status = False
        with patch("weko_indextree_journal.models.db.session.commit",side_effect=BaseException("test_error")):
            with pytest.raises(BaseException):
                Journal_export_processing.save_export_info(db_processing_status)
            assert Journal_export_processing.query.filter_by(id=2).one_or_none() is None
            
#     def get(cls):
