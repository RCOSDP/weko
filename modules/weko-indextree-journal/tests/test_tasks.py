
from mock import patch
import os
import unittest
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from weko_indextree_journal.tasks import convert_none_to_blank,export_journal_task
from weko_indextree_journal.models import Journal_export_processing, Journal

# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_tasks.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp

# def export_journal_task(p_path):
# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_tasks.py::test_export_journal_task -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_export_journal_task(app,db,test_indices):
    filename = "Invenio-OAIServer_AllTitles_{}.txt".format(datetime.today().strftime('%Y-%m-%d'))

    repository_file = os.path.join(
        app.static_folder,"weko/kbart",filename,
    )
    filelist = os.path.join(
        app.static_folder,"weko/kbart","filelist.txt"
    )
    app.config['THEME_SITEURL'] = 'https://inveniosoftware.org'
    # not exist Journal_export_processing and Journal
    # 58157 - case.1
    result = export_journal_task(None)
    assert result == []
    with open(repository_file,"r") as f:
        assert len(f.readlines()) == 1
    with open(filelist,"r") as f:
        assert filename in f.readlines()[0]

    journal = Journal(
        id=1,
        index_id=1,
        publication_title="test journal {}".format(1),
        date_first_issue_online="2022-01-01",
        date_last_issue_online="2022-01-01",
        title_url="search?search_type=2&q={}".format(1),
        title_id=str(1),
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
    # exist Journal_export_processing and Journal
    # 58157 - case.2
    result = export_journal_task(None)
    assert result == [['test journal 1', '', '', '2022-01-01', '', '', '2022-01-01', '', '', 'https://inveniosoftware.org/search?search_type=2&q=1', '', 1, '', 'abstract', '', '', 'serial', '', '', '', '', '', '', '', 'F', 'en', '', '', '', '', '', '', '', '']]
    with open(repository_file,"r") as f:
        assert "https://inveniosoftware.org/search?search_type=2&q=1" in f.readlines()[1]
    with open(filelist,"r") as f:
        assert filename in f.readlines()[0]

    journal = Journal(
        id=2,
        index_id=2,
        publication_title="test journal {}".format(2),
        date_first_issue_online="2022-01-01",
        date_last_issue_online="2022-01-01",
        title_url="search?search_type=2&q={}".format(2),
        title_id=str(2),
        coverage_depth="abstract",
        publication_type="serial",
        access_type="F",
        language="en",
        is_output=False,
        abstract='',
        code_issnl=''
    )
    db.session.add(journal)
    db.session.commit()
    # exist Journal_export_processing and Journal
    # 58157 - case.5
    result = export_journal_task(None)
    assert result == [['test journal 1', '', '', '2022-01-01', '', '', '2022-01-01', '', '', 'https://inveniosoftware.org/search?search_type=2&q=1', '', 1, '', 'abstract', '', '', 'serial', '', '', '', '', '', '', '', 'F', 'en', '', '', '', '', '', '', '', '']]
    with open(repository_file,"r") as f:
        assert "https://inveniosoftware.org/search?search_type=2&q=1" in f.readlines()[1]
    with open(filelist,"r") as f:
        assert filename in f.readlines()[0]

    # THEME_SITEURL endwith "/"
    # 58157 - case.3
    app.config['THEME_SITEURL'] = 'https://inveniosoftware.org/'
    result = export_journal_task(None)
    assert result == [['test journal 1', '', '', '2022-01-01', '', '', '2022-01-01', '', '', 'https://inveniosoftware.org/search?search_type=2&q=1', '', 1, '', 'abstract', '', '', 'serial', '', '', '', '', '', '', '', 'F', 'en', '', '', '', '', '', '', '', '']]
    with open(repository_file,"r") as f:
        assert "https://inveniosoftware.org/search?search_type=2&q=1" in f.readlines()[1]
    with open(filelist,"r") as f:
        assert filename in f.readlines()[0]

    # get_journal_by_is_output raise Exception
    # 58157 - case.10
    with app.app_context():
        with unittest.TestCase.assertLogs(app.logger, level='DEBUG') as log:
            with patch("weko_indextree_journal.tasks.Journals.get_journal_by_is_output",side_effect=SQLAlchemyError()):
                result = export_journal_task(None)
                assert result == {}
                assert "[100] [Export Journal Task] End with Data acquisition error (DB error). Error:" in log.output[1]

    # save_export_info raise Exception
    # 58157 - case.9
    with app.app_context():
        with unittest.TestCase.assertLogs(app.logger, level='DEBUG') as log:
            with patch("weko_indextree_journal.tasks.Journals.get_journal_by_is_output",side_effect=Exception()):
                result = export_journal_task(None)
                assert result == {}
                assert "[1] [Export Journal Task] End with unknown error. Error:" in log.output[1]
                with open(repository_file,"r") as f:
                    assert "https://inveniosoftware.org/search?search_type=2&q=1" in f.readlines()[1]
                with open(filelist,"r") as f:
                    assert filename in f.readlines()[0]

    # status is True
    # 58157 - case.4
    db_processing_status = Journal_export_processing.query.first()
    db_processing_status.status = True
    db.session.merge(db_processing_status)
    db.session.commit()
    with app.app_context():
        with unittest.TestCase.assertLogs(app.logger, level='DEBUG') as log:
            result = export_journal_task(None)
            assert result == {}
            assert "[3] Execution failed due to multiple execution errors" in log.output[1]
            with open(repository_file,"r") as f:
                assert "https://inveniosoftware.org/search?search_type=2&q=1" in f.readlines()[1]
            with open(filelist,"r") as f:
                assert filename in f.readlines()[0]


# def convert_none_to_blank(input_value):
# .tox/c1/bin/pytest --cov=weko_indextree_journal tests/test_tasks.py::test_convert_none_to_blank -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-indextree-journal/.tox/c1/tmp
def test_convert_none_to_blank():
    result = convert_none_to_blank(None)
    assert result == ""

    result = convert_none_to_blank("value")
    assert result == "value"
