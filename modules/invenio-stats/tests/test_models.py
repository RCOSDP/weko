import datetime
from mock import patch
from sqlalchemy.exc import SQLAlchemyError

from invenio_stats.models import (
    get_stats_events_partition_tables,
    make_stats_events_partition_table,
    StatsEvents,
    StatsAggregation,
    StatsBookmark
)


# class StatsEvents(db.Model, _StataModelBase):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_models.py::test_StatsEvents -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_StatsEvents(app, db, stats_events_for_db):
    _save_data1 = {
        "_source": {
            "timestamp": "2023-01-01T01:01:00",
            "_id": "2",
            "_index": "test-events-stats-record-view",
            "_type": "record-view"
        }
    }
    _save_data2 = {
        "_source": {
            "date": "2023-01-01T01:01:01",
            "_id": "3",
            "_index": "test-events-stats-record-view",
            "_type": "record-view"
        }
    }
    assert StatsEvents.get_uq_key() == 'uq_stats_key_stats_events'
    assert StatsEvents.delete_by_source_id("1", "test-events-stats-top-view") == True
    with patch('invenio_db.db.session.query', side_effect=SQLAlchemyError("test_sql_error")):
        assert StatsEvents.delete_by_source_id("1", "test-events-stats-top-view") == False
    assert StatsEvents.save({"_source": None}) == False
    with patch('invenio_db.db.session.execute', return_value=True):
        assert StatsEvents.save(_save_data1) == True
        assert StatsEvents.save(_save_data2) == True
    with patch('invenio_db.db.session.execute', side_effect=SQLAlchemyError("test_sql_error")):
        assert StatsEvents.save(_save_data1) == False


# class StatsAggregation(db.Model, _StataModelBase):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_models.py::test_StatsAggregation -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_StatsAggregation(app, db):
    assert StatsAggregation.get_uq_key() == 'uq_stats_key_stats_aggregation'


# class StatsBookmark(db.Model, _StataModelBase):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_models.py::test_StatsBookmark -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_StatsBookmark(app, db):
    assert StatsBookmark.get_uq_key() == 'uq_stats_key_stats_bookmark'


class DbExec():
    def __init__(self, sql) -> None:
        pass

    def fetchall(self):
        return [['stats_events']]

# def get_stats_events_partition_tables():
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_models.py::test_get_stats_events_partition_tables -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_get_stats_events_partition_tables(app, db):
    with patch('invenio_db.db.session.execute', side_effect=DbExec):
        assert get_stats_events_partition_tables() == ['stats_events']


# def make_stats_events_partition_table(year, month):
# .tox/c1/bin/pytest --cov=invenio_stats tests/test_models.py::test_make_stats_events_partition_table -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/invenio-stats/.tox/c1/tmp
def test_make_stats_events_partition_table(app, db):
    with patch('sqlalchemy.event.listen', return_value=True):
        assert make_stats_events_partition_table(2023, 1) == 'stats_events_202301'
