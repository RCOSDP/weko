
from mock import patch

from invenio_cache import current_cache

from weko_authors.tasks import export_all,import_author,check_is_import_available


# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp

# def export_all():
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_export_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_export_all(app,mocker):
    mocker.patch("weko_authors.tasks.set_export_status")
    mocker.patch("weko_authors.tasks.save_export_url")
    mocker.patch("weko_authors.tasks.export_authors",return_value="test_url.txt")

    result = export_all()
    assert result == "test_url.txt"
    
    mocker.patch("weko_authors.tasks.export_authors",return_value=None)
    result = export_all()
    assert result == None
    
    mocker.patch("weko_authors.tasks.export_authors",side_effect=Exception)
    result = export_all()
    assert result == None

# def import_author(author):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_import_author -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_import_author(app):
    with patch("weko_authors.tasks.import_author_to_system"):
        result = import_author("test author")
        assert result["status"] == "SUCCESS"
        
    with patch("weko_authors.tasks.import_author_to_system",side_effect=Exception({"error_id":"1"})):
        result = import_author("test author")
        assert result["status"] == "FAILURE"
        assert result["error_id"] == "1"
    with patch("weko_authors.tasks.import_author_to_system",side_effect=KeyError("is_deleted")):
        result = import_author("test author")
        assert result["status"] == "FAILURE"

# def check_is_import_available(group_task_id=None):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_check_is_import_available -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_check_is_import_available(app,mocker):
    cache_key = "author_import_cache"
    class MockTask:
        def __init__(self,id,status):
            self.id = id
            self.status = status
        def successful(self):
            return self.status == "success"
        def failed(self):
            return self.status == "failed"
    class MockGroupTask:
        @classmethod
        def restore(cls,task_id):
            if task_id == "not_exist_task":
                return None
            elif task_id == "success_task":
                return MockTask(1,"success")
            elif task_id == "not_success_task1":
                return MockTask(2,"not success")
            elif task_id == "not_success_task2":
                return MockTask("not_success_task2","not success")
            
    def mock_restore(task_id):
            if task_id == "not_exist_task":
                return None
            elif task_id == "success_task":
                return MockTask(1,"success")
            elif task_id == "not_success_task1":
                return MockTask(2,"not success")
            elif task_id == "not_success_task2":
                return MockTask("not_success_task2","not success")
    mocker.patch("weko_authors.tasks.GroupResult",side_effect=MockGroupTask)
    class MockInspect:
        def __init__(self,flg):
            self.flg = flg
        def ping(self):
            return self.flg
    # inspect.ping is false
    mocker.patch("weko_authors.tasks.inspect",return_value=MockInspect(False))
    result = check_is_import_available()
    assert result == {"is_available":False,"celery_not_run":True}
    
    # inspect.ping is true
    mocker.patch("weko_authors.tasks.inspect",return_value=MockInspect(True))

    current_cache.delete(cache_key)
    # not exist cache
    mocker.patch("weko_authors.tasks.GroupResult.restore",side_effect=mock_restore)
    result = check_is_import_available()
    assert result == {"is_available":True}
    
    # not exist task
    current_cache.set(cache_key,{"group_task_id":"not_exist_task"})
    result = check_is_import_available()
    assert result == {"is_available":True}
    assert current_cache.get(cache_key) is None
    
    # task is successful
    current_cache.set(cache_key,{"group_task_id":"success_task"})
    result = check_is_import_available(1)
    assert result == {"is_available":True}
    assert current_cache.get(cache_key) is None
    
    # task is not success,failed, group_task_id = taks.id
    current_cache.set(cache_key,{"group_task_id":"not_success_task1"})
    result = check_is_import_available(2)
    assert result == {"is_available":False,"continue_data":{"group_task_id":"not_success_task1"}}
    assert current_cache.get(cache_key) is not None

    # task is not success,failed, group_task_id != taks.id
    current_cache.set(cache_key,{"group_task_id":"not_success_task2"})
    result = check_is_import_available(2)
    assert result == {"is_available":False}
    assert current_cache.get(cache_key) is not None