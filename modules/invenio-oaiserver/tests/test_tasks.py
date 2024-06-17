
import uuid
from flask import current_app
from invenio_records.models import RecordMetadata
from invenio_oaiserver.models import OAISet

from invenio_oaiserver.tasks import _records_commit,update_records_sets, update_affected_records
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_tasks.py -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp


# def _records_commit(record_ids):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_tasks.py::test_records_commit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_records_commit(app,records):
    res = RecordMetadata.query.all()
    ids = [rec.id for rec in res]
    _records_commit(ids)


# def update_records_sets(record_ids):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_tasks.py::test_update_records_sets -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_update_records_sets(app,records, mocker):
    mocker.patch("invenio_oaiserver.tasks._records_commit")
    res = RecordMetadata.query.all()
    ids = [rec.id for rec in res]
    
    class MockIndexer:
        def bulk_index(self,query):
            for q in query:
                a=q
        def process_bulk_queue(self,es_bulk_kwargs):
            pass
    mocker.patch("invenio_oaiserver.tasks.RecordIndexer",side_effect=MockIndexer)
    update_records_sets(ids)

# def update_affected_records(spec=None, search_pattern=None):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_tasks.py::test_update_affected_records -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_update_affected_records(app,db,without_oaiset_signals,mocker):
    uuids = [uuid.uuid4() for i in range(5)]
    def mock_get_affected_records(spec,search_pattern):
        for i in uuids:
            yield i
    current_app.config.update(OAISERVER_CELERY_TASK_CHUNK_SIZE=5)
    mocker.patch("invenio_oaiserver.tasks.get_affected_records",side_effect=mock_get_affected_records)
    mocker.patch("invenio_oaiserver.tasks._records_commit")
    mocker.patch("invenio_oaiserver.tasks.sleep")
    class MockIndexer:
        def bulk_index(self,query):
            pass
        def process_bulk_queue(self,es_bulk_kwargs):
            pass
    mocker.patch("invenio_oaiserver.tasks.RecordIndexer",side_effect=MockIndexer)
    oai = OAISet(id=1,
        spec='test',
        name='test_name',
        description='some test description',
        search_pattern='test search')
    
    db.session.add(oai)
    db.session.commit()
    update_affected_records.delay(oai.spec,oai.search_pattern)