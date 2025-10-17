import pytest
from mock import patch, MagicMock

from invenio_resourcesyncclient.tasks import (
    is_running_task,
    run_sync_import,
    get_record_from_file,
    get_record,
    resync_sync,
    prepare_log,
    finish,
    init_counter,
    run_sync_auto
)

class MockSyncFunc:
    def __init__(self):
        pass
    
    def apply_async(self, **args):
        pass

#def run_sync_import(id):
#        def sigterm_handler(*args):
# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_tasks.py::test_run_sync_import -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
def test_run_sync_import(app, test_resync):
    res = run_sync_import(20)
    assert res == ({'task_state': 'SUCCESS', 'task_id': None})

    with pytest.raises(Exception) as e:
        res = run_sync_import(0)
    e.type == AttributeError

    res = run_sync_import(10)
    res[0].pop('start_time')
    res[0].pop('end_time')
    res[0].pop('execution_time')
    assert res == ({'task_state': 'SUCCESS', 'task_name': 'import', 'task_type': 'import', 'repository_name': 'weko', 'task_id': None},)

    app.config['INVENIO_RESYNC_LOGS_STATUS'] = {
        'successful': "Running",
        'running': 'Running',
        'failed': 'Running'
    }
    res = run_sync_import(30)
    res[0].pop('start_time')
    res[0].pop('end_time')
    res[0].pop('execution_time')
    assert res == ({'task_state': 'SUCCESS', 'task_name': 'import', 'task_type': 'import', 'repository_name': 'weko', 'task_id': None},)

    res = run_sync_import(60)
    res[0].pop('start_time')
    res[0].pop('end_time')
    res[0].pop('execution_time')
    assert res == ({'task_state': 'SUCCESS', 'task_name': 'import', 'task_type': 'import', 'repository_name': 'weko', 'task_id': None},)

    res = run_sync_import(70)
    res[0].pop('start_time')
    res[0].pop('end_time')
    res[0].pop('execution_time')
    assert res == ({'task_state': 'SUCCESS', 'task_name': 'import', 'task_type': 'import', 'repository_name': 'weko', 'task_id': None},)

#def get_record_from_file(rc):


#def get_record(
# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_tasks.py::test_get_record -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
def test_get_record(app):
    res = get_record(
        url='{}://{}/oai'.format('https', 'jpcoar.repo.nii.ac.jp'),
        record_id=1,
        metadata_prefix='jpcoar_1.0',
    )
    assert res == []


#def resync_sync(id):
#        def sigterm_handler(*args):
# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_tasks.py::test_resync_sync -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
def test_resync_sync(app, test_resync):
    res = resync_sync(20)
    assert res == ({'task_state': 'SUCCESS', 'task_id': None})

    mock_sync_func = MagicMock(side_effect=MockSyncFunc)
    with patch('invenio_resourcesyncclient.tasks.run_sync_import', mock_sync_func):
        res = resync_sync(30)
        res[0].pop('start_time')
        res[0].pop('end_time')
        res[0].pop('execution_time')
        assert res == ({'task_state': 'SUCCESS', 'task_name': 'sync', 'task_type': 'sync', 'repository_name': 'weko', 'task_id': None},)

#def prepare_log(resync, id, counter, task_id, log_type):
#def finish(resync, resync_log, counter, start_time, request_id, log_type):
#def init_counter():


#def run_sync_auto():
# .tox/c1/bin/pytest --cov=invenio_resourcesyncclient tests/test_tasks.py::test_run_sync_auto -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-resourcesyncclient/.tox/c1/tmp
def test_run_sync_auto(app, test_resync):
    mock_sync_func = MagicMock(side_effect=MockSyncFunc)
    with patch('invenio_resourcesyncclient.tasks.resync_sync', mock_sync_func):
        res = run_sync_auto()
        assert res == ({'task_state': 'SUCCESS', 'repository_name': 'weko', 'task_id': None},)
