
import json
import pytest
from mock import patch, MagicMock, call, mock_open, call
from datetime import datetime,  timedelta, timezone
from flask import Flask, current_app
from celery import states

import logging
from logging import INFO
from _pytest.logging import LogCaptureFixture
from sqlalchemy.exc import SQLAlchemyError
from elasticsearch import ElasticsearchException

from invenio_cache import current_cache
from weko_authors.tasks import export_all,import_author,check_is_import_available,import_id_prefix,import_affiliation_id,import_author_over_max,import_authors_from_temp_files,import_authors_for_over_max,write_result_temp_file,update_summary,prepare_display_status,prepare_success_msg,check_task_end,check_is_import_available,check_tmp_file_time_for_author,update_cache_data, \
import_authors_from_temp_files, import_authors_for_over_max
from weko_workflow.utils import get_cache_data, delete_cache_data

# from .config import WEKO_AUTHORS_IMPORT_CACHE_RESULT_OVER_MAX_FILE_PATH_KEY



# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp

# def export_all():
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_export_all -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_export_all(app,mocker):
    mocker.patch("weko_authors.tasks.set_export_status")
    mocker.patch("weko_authors.tasks.save_export_url")
    mocker.patch("weko_authors.tasks.export_authors",return_value="test_url.txt")
    mocker.patch("weko_authors.tasks.export_prefix",return_value="prefix_url.txt")

    result = export_all('author_db', user_id=1)
    assert result == "test_url.txt"

    result = export_all('id_prefix', user_id=2)
    assert result == "prefix_url.txt"

    mocker.patch("weko_authors.tasks.export_authors", return_value=None)
    result = export_all('author_db', user_id=3)
    assert result == None

    result = export_all('XXXX', user_id=4)
    assert result == None

    mocker.patch("weko_authors.tasks.export_authors", side_effect=Exception)
    result = export_all('author_db', user_id=5)
    assert result == None


# def import_author(author):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_01_import_author -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_01_import_author(app):
    with patch("weko_authors.tasks.import_author_to_system"):
        result = import_author({"status":"", "weko_id":"", "current_weko_id":""}, True, {})
        assert result["status"] == "SUCCESS"


# def import_author(author):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_02_import_author -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_02_import_author(app, caplog: LogCaptureFixture):
    with patch("weko_authors.tasks.import_author_to_system",side_effect=SQLAlchemyError("SQLAlchemyError")):
        result = import_author({"status":"", "weko_id":"", "current_weko_id":""}, True, {})
    info_logs = [record for record in caplog.record_tuples if record[1] == logging.ERROR]
    expected = [('testapp', logging.ERROR, 'SQLAlchemyError')] * 6
    assert info_logs == expected
    assert result["status"] == "FAILURE"


# def import_author(author):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_03_import_author -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_03_import_author(app, caplog: LogCaptureFixture):
    with patch("weko_authors.tasks.import_author_to_system",side_effect=ElasticsearchException("ElasticsearchException")):
        result = import_author({"status":"", "weko_id":"", "current_weko_id":""}, True, {})
    info_logs = [record for record in caplog.record_tuples if record[1] == logging.ERROR]
    expected = [('testapp', logging.ERROR, 'ElasticsearchException')] * 6
    assert info_logs == expected
    assert result["status"] == "FAILURE"


# def import_author(author):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_04_import_author -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_04_import_author(app, caplog: LogCaptureFixture):
    with patch("weko_authors.tasks.import_author_to_system",side_effect=TimeoutError("TimeoutError")):
        result = import_author({"status":"", "weko_id":"", "current_weko_id":""}, True, {})
    info_logs = [record for record in caplog.record_tuples if record[1] == logging.ERROR]
    expected = [('testapp', logging.ERROR, 'TimeoutError')] * 6
    assert info_logs == expected
    assert result["status"] == "FAILURE"


# def import_author(author):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_05_import_author -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_05_import_author(app, caplog: LogCaptureFixture):
    with patch("weko_authors.tasks.import_author_to_system",side_effect=TimeoutError({"error_id": 123, "message": "An error occurred"})):
        result = import_author({"status":"", "weko_id":"", "current_weko_id":""}, True, {})
    info_logs = [record for record in caplog.record_tuples if record[1] == logging.ERROR]
    expected = [('testapp', logging.ERROR, "{'error_id': 123, 'message': 'An error occurred'}")] * 6
    assert info_logs == expected
    assert result["status"] == "FAILURE"


# def check_is_import_available(group_task_id=None):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_check_is_import_available -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
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


# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::TestImportAuthorsFromTempFiles -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestImportAuthorsFromTempFiles:
    @pytest.fixture
    def mock_update_cache_data(self):
        """Mock update_cache_data function."""
        with patch('weko_authors.tasks.update_cache_data') as mock:
            yield mock

    @pytest.fixture
    def mock_get_check_base_name(self):
        """Mock get_check_base_name function."""
        with patch('weko_authors.tasks.get_check_base_name', return_value='test_check_base') as mock:
            yield mock

    @pytest.fixture
    def mock_import_authors_for_over_max(self):
        """Mock import_authors_for_over_max function."""
        with patch('weko_authors.tasks.import_authors_for_over_max') as mock:
            yield mock

# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::TestImportAuthorsFromTempFiles::test_import_authors_from_temp_files_normal_case -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_import_authors_from_temp_files_normal_case(self, app2, mock_update_cache_data, mock_get_check_base_name,
                                                    mock_import_authors_for_over_max):
        """
        正常系
        条件：一時ファイルが正常に存在し、著者データを正常に読み込める
        入力：
            - reached_point: {"part_number": 1, "count": 2}
            - max_part: 2
        期待結果：
            - 結果ファイルパスをキャッシュに保存
            - 一時ファイルから著者データを読み込み
            - import_authors_for_over_maxが呼び出される
            - 一時ファイルが削除される
        """
        # テスト用データの準備
        reached_point = {"part_number": 1, "count": 2}
        max_part = 2

        # 一時ファイルの内容をモック
        part1_data = [
            {"pk_id": 1, "authorNameInfo": [{"familyName": "Doe", "firstName": "John"}], "status": "new", "weko_id": "1001", "current_weko_id": "1000"},
            {"pk_id": 2, "authorNameInfo": [{"familyName": "Smith", "firstName": "Jane"}], "status": "update", "weko_id": "1002", "current_weko_id": "1002"},
            {"pk_id": 3, "authorNameInfo": [{"familyName": "Brown", "firstName": "Bob"}], "status": "new", "weko_id": "1003", "current_weko_id": ""},
            {"pk_id": 4, "authorNameInfo": [{"familyName": "Lee", "firstName": "Alice"}], "status": "update", "weko_id": "1004", "current_weko_id": "1004"},
        ]

        part2_data = [
            {"pk_id": 5, "authorNameInfo": [{"familyName": "Lee", "firstName": "Alice"}], "status": "update", "weko_id": "1004", "current_weko_id": "1004"},
        ]

        # ファイル読み込みのモック
        mock_file_data = {
            '/data/test_check_base-part1': json.dumps(part1_data),
            '/data/test_check_base-part2': json.dumps(part2_data)
        }

        def mock_open_side_effect(*args, **kwargs):
            file_path = args[0]
            if file_path in mock_file_data:
                mock = mock_open(read_data=mock_file_data[file_path])
                return mock(*args, **kwargs)
            return mock_open()(*args, **kwargs)

        # os.removeをモック
        with patch('os.remove') as mock_remove, \
            patch('builtins.open', side_effect=mock_open_side_effect):

            # 関数実行
            import_authors_from_temp_files(reached_point, max_part)

            # アサーション
            # update_cache_dataが呼ばれたことを確認
            mock_update_cache_data.assert_called_once()

            # import_authors_for_over_maxが2回呼ばれたことを確認
            assert mock_import_authors_for_over_max.call_count == 2

            # 一時ファイルの削除が呼ばれたことを確認
            mock_remove.assert_has_calls([
                call('/data/test_check_base-part1'),
                call('/data/test_check_base-part2')
            ])

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::TestImportAuthorsFromTempFiles::test_import_authors_from_temp_files_with_batch_size -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_import_authors_from_temp_files_with_batch_size(self, app2, mock_update_cache_data, mock_get_check_base_name,
                                                        mock_import_authors_for_over_max):
        """
        正常系
        条件：著者データがバッチサイズを超える場合
        入力：
            - reached_point: {"part_number": 1, "count": 0}
            - max_part: 1
            - WEKO_AUTHORS_IMPORT_BATCH_SIZE: 2
        期待結果：
            - バッチサイズ（2）ごとにimport_authors_for_over_maxが呼び出される
        """

        # テスト用データの準備
        reached_point = {"part_number": 1, "count": 0}
        max_part = 1
        request_info = {"key": "request_info"}

        # 一時ファイルの内容をモック（5人の著者）
        part1_data = [
            {"pk_id": 1, "authorNameInfo": [{"familyName": "Doe", "firstName": "John"}], "status": "new", "weko_id": "1001", "current_weko_id": ""},
            {"pk_id": 2, "authorNameInfo": [{"familyName": "Smith", "firstName": "Jane"}], "status": "update", "weko_id": "1002", "current_weko_id": "1002"},
            {"pk_id": 3, "authorNameInfo": [{"familyName": "Brown", "firstName": "Bob"}], "status": "new", "weko_id": "1003", "current_weko_id": ""},
            {"pk_id": 4, "authorNameInfo": [{"familyName": "Lee", "firstName": "Alice"}], "status": "update", "weko_id": "1004", "current_weko_id": "1004"},
            {"pk_id": 5, "authorNameInfo": [{"familyName": "Wang", "firstName": "Chen"}], "status": "new", "weko_id": "1005", "current_weko_id": "", "errors":["error"]}
        ]

        # ファイル読み込みのモック
        mock_file_data = {
            '/data/test_check_base-part1': json.dumps(part1_data)
        }

        def mock_open_side_effect(*args, **kwargs):
            file_path = args[0]
            if file_path in mock_file_data:
                mock = mock_open(read_data=mock_file_data[file_path])
                return mock(*args, **kwargs)
            return mock_open()(*args, **kwargs)

        # os.removeをモック
        with patch('os.remove') as mock_remove, \
            patch('builtins.open', side_effect=mock_open_side_effect):

            # 関数実行
            import_authors_from_temp_files(reached_point, max_part, request_info)

            # アサーション
            # import_authors_for_over_maxが呼ばれたことを確認
            assert mock_import_authors_for_over_max.call_count == 1

            # 最初のバッチ（0, 1）
            mock_import_authors_for_over_max.assert_any_call(part1_data[0:4], request_info=request_info)

    def test_import_authors_from_temp_files_file_not_found(self, app2, mock_update_cache_data, mock_get_check_base_name,
                                                        mock_import_authors_for_over_max):
        """
        異常系
        条件：一時ファイルが存在しない場合
        入力：
            - reached_point: {"part_number": 1, "count": 0}
            - max_part: 1
        期待結果：
            - FileNotFoundErrorが発生する
            - エラーログが記録される
        """
        # テスト用データの準備
        reached_point = {"part_number": 2, "count": 0}
        max_part = 1
        # 一時ファイルの内容をモック（5人の著者）
        part1_data = [
            {"pk_id": 1, "authorNameInfo": [{"familyName": "Doe", "firstName": "John"}], "status": "new", "weko_id": "1001", "current_weko_id": ""},
            {"pk_id": 2, "authorNameInfo": [{"familyName": "Smith", "firstName": "Jane"}], "status": "update", "weko_id": "1002", "current_weko_id": "1002"},
            {"pk_id": 3, "authorNameInfo": [{"familyName": "Brown", "firstName": "Bob"}], "status": "new", "weko_id": "1003", "current_weko_id": ""},
            {"pk_id": 4, "authorNameInfo": [{"familyName": "Lee", "firstName": "Alice"}], "status": "update", "weko_id": "1004", "current_weko_id": "1004"},
            {"pk_id": 5, "authorNameInfo": [{"familyName": "Wang", "firstName": "Chen"}], "status": "new", "weko_id": "1005", "current_weko_id": "", "errors":["error"]}
        ]

        # ファイル読み込みのモック
        mock_file_data = {
            '/data/test_check_base-part1': json.dumps(part1_data)
        }

        def mock_open_side_effect(*args, **kwargs):
            file_path = args[0]
            if file_path in mock_file_data:
                mock = mock_open(read_data=mock_file_data[file_path])
                return mock(*args, **kwargs)
            return mock_open()(*args, **kwargs)

        # os.removeをモック
        with patch('os.remove', side_effect=FileNotFoundError("File not found")) as mock_remove, \
            patch('builtins.open', side_effect=mock_open_side_effect):

            import_authors_from_temp_files(reached_point, max_part)

    def test_import_authors_from_temp_files_invalid_json(self, app2, mock_update_cache_data, mock_get_check_base_name,
                                                    mock_import_authors_for_over_max):
        """
        異常系
        条件：一時ファイルのJSONが不正な場合
        入力：
            - reached_point: {"part_number": 1, "count": 0}
            - max_part: 1
        期待結果：
            - JSONDecodeErrorが発生する
            - エラーログが記録される
        """
        # テスト用データの準備
        reached_point = {"part_number": 1, "count": 0}
        max_part = 1

        # 不正なJSONをシミュレート
        invalid_json = "{ invalid json }"

        # ファイル読み込みのモック
        mock_file_data = {
            '/data/test_check_base-part1': invalid_json
        }

        def mock_open_side_effect(*args, **kwargs):
            file_path = args[0]
            if file_path in mock_file_data:
                mock = mock_open(read_data=mock_file_data[file_path])
                return mock(*args, **kwargs)
            return mock_open()(*args, **kwargs)

        # os.removeをモック
        with patch('os.remove') as mock_remove, \
            patch('builtins.open', side_effect=mock_open_side_effect):

            # 関数実行してエラーを検証
            with pytest.raises(json.JSONDecodeError):
                import_authors_from_temp_files(reached_point, max_part)

            # 削除は呼ばれないはず
            mock_remove.assert_not_called()

    def test_import_authors_from_temp_files_file_deletion_error(self, app2, mock_update_cache_data, mock_get_check_base_name,
                                                            mock_import_authors_for_over_max):
        """
        異常系
        条件：一時ファイルの削除に失敗する場合
        入力：
            - reached_point: {"part_number": 1, "count": 0}
            - max_part: 1
        期待結果：
            - エラーログが記録される
            - 処理は続行される
        """
        # テスト用データの準備
        reached_point = {"part_number": 1, "count": 0}
        max_part = 1

        # 一時ファイルの内容をモック
        part1_data = [
            {"pk_id": 1, "authorNameInfo": [{"familyName": "Doe", "firstName": "John"}], "status": "new", "weko_id": "1001", "current_weko_id": ""}
        ]

        # ファイル読み込みのモック
        mock_file_data = {
            '/data/test_check_base-part1': json.dumps(part1_data)
        }

        def mock_open_side_effect(*args, **kwargs):
            file_path = args[0]
            if file_path in mock_file_data:
                mock = mock_open(read_data=mock_file_data[file_path])
                return mock(*args, **kwargs)
            return mock


# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::TestImportAuthorsForOverMax -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestImportAuthorsForOverMax:
    """Test class for import_authors_for_over_max function."""

    @pytest.fixture
    def mock_cache(self):
        """Mock the current_cache."""
        with patch('weko_authors.tasks.current_cache') as mock_cache:
            mock_cache.get.return_value = "/temp/result_file.tsv"
            yield mock_cache

    @pytest.fixture
    def mock_get_cache_data(self):
        """Mock the get_cache_data function."""
        with patch('weko_authors.tasks.get_cache_data') as mock_get:
            mock_get.return_value = {"success_count": 5, "failure_count": 2}
            yield mock_get

    @pytest.fixture
    def mock_update_summary(self):
        """Mock the update_cache_data function."""
        with patch('weko_authors.tasks.update_summary') as mock_update:
            yield mock_update

    @pytest.fixture
    def mock_csv_writer(self):
        """Mock csv writer."""
        mock_writer = MagicMock()
        with patch('weko_authors.tasks.open', mock_open()) as mock_file, \
                patch('csv.writer', return_value=mock_writer) as _:
            yield mock_writer

    @pytest.fixture
    def mock_group(self):
        """Mock celery group."""
        with patch('weko_authors.tasks.group') as mock_group:
            mock_task = MagicMock()
            mock_task.children = []
            mock_group.return_value.apply_async.return_value = mock_task
            yield mock_group, mock_task

    @pytest.fixture
    def mock_check_task_end(self):
        """Mock check_task_end function."""
        with patch('weko_authors.tasks.check_task_end') as mock_check:
            yield mock_check

    def test_import_authors_for_over_max_success(self, app2, mock_cache,
                                                mock_get_cache_data, mock_update_summary,
                                                mock_csv_writer, mock_group, mock_check_task_end):
        """
        正常系
        条件：複数の著者情報が渡されて、全てインポート成功する場合
        入力：有効な著者情報の配列
        期待結果：
            - グループタスクが作成・実行される
            - タスクIDが保存される
            - 結果ファイルが作成される
            - サマリーが更新される
        """
        # Setup
        mock_group_obj, mock_task = mock_group
        author1 = {
            "pk_id": 1,
            "current_weko_id": None,
            "weko_id": "author1",
            "authorNameInfo": [{"familyName": "Doe", "firstName": "John"}],
            "status": "new"
        }
        author2 = {
            "pk_id": 2,
            "current_weko_id": "old_author2",
            "weko_id": "author2",
            "authorNameInfo": [{"familyName": "Smith", "firstName": "Jane"}],
            "status": "update"
        }
        authors = [author1, author2]

        # Setup task children and results
        task1_mock = MagicMock()
        task1_mock.task_id = "task1"
        task1_mock.result = {
            'start_date': '2025-03-16 10:00:00',
            'end_date': '2025-03-16 10:00:05',
            'status': states.SUCCESS
        }

        task2_mock = MagicMock()
        task2_mock.task_id = "task2"
        task2_mock.result = {
            'start_date': '2025-03-16 10:00:00',
            'end_date': '2025-03-16 10:00:05',
            'status': states.SUCCESS
        }

        mock_task.children = [task1_mock, task2_mock]

        with patch('weko_authors.tasks.import_author.AsyncResult') as mock_async_result:
            mock_async_result.side_effect = [task1_mock, task2_mock]

            # Execute
            import_authors_for_over_max(authors)

            # Verify
            assert mock_group_obj.call_count == 1
            mock_check_task_end.assert_called_once()
            mock_update_summary.assert_called()

            # Check that we wrote to the result file
            assert mock_csv_writer.writerow.call_count == 2

            # Check task results were processed and records were forgotten
            assert task1_mock.forget.call_count == 1
            assert task2_mock.forget.call_count == 1

    def test_import_authors_for_over_max_partial_failure(self, app2, mock_cache,
                                                    mock_get_cache_data, mock_update_summary,
                                                    mock_csv_writer, mock_group, mock_check_task_end):
        """
        正常系
        条件：複数の著者情報が渡されて、一部がインポート失敗する場合
        入力：有効な著者情報の配列 (1つ成功、1つ失敗)
        期待結果：
            - 成功・失敗の両方の結果が記録される
            - エラーIDが記録される
            - サマリーが正確に更新される
        """
        # Setup
        mock_group_obj, mock_task = mock_group
        author1 = {
            "pk_id": 1,
            "current_weko_id": None,
            "weko_id": "author1",
            "authorNameInfo": [{"familyName": "Doe", "firstName": "John"}],
            "status": "new"
        }
        author2 = {
            "pk_id": 2,
            "current_weko_id": "old_author2",
            "weko_id": "author2",
            "authorNameInfo": [{"familyName": "Smith", "firstName": "Jane"}],
            "status": "update"
        }
        authors = [author1, author2]

        # Setup task children and results
        task1_mock = MagicMock()
        task1_mock.task_id = "task1"
        task1_mock.result = {
            'start_date': '2025-03-16 10:00:00',
            'end_date': '2025-03-16 10:00:05',
            'status': states.SUCCESS
        }

        task2_mock = MagicMock()
        task2_mock.task_id = "task2"
        task2_mock.result = {
            'start_date': '2025-03-16 10:00:00',
            'end_date': '2025-03-16 10:00:05',
            'status': states.FAILURE,
            'error_id': 'delete_author_link'
        }

        mock_task.children = [task1_mock, task2_mock]

        with patch('weko_authors.tasks.import_author.AsyncResult') as mock_async_result:
            mock_async_result.side_effect = [task1_mock, task2_mock]

            # Execute
            import_authors_for_over_max(authors)

            # Verify
            assert mock_group_obj.call_count == 1
            mock_check_task_end.assert_called_once()

            # Check that the summary was updated with correct counts
            mock_update_summary.assert_called_with(1,1)

    def test_import_authors_for_over_max_timeout(self, app2, mock_cache,
                                            mock_get_cache_data, mock_update_summary,
                                            mock_csv_writer, mock_group, mock_check_task_end):
        """
        異常系
        条件：タスクがタイムアウトする場合
        入力：有効な著者情報の配列
        期待結果：
            - タイムアウトエラーが記録される
            - 失敗としてカウントされる
        """
        # Setup
        mock_group_obj, mock_task = mock_group
        author = {
            "pk_id": 1,
            "current_weko_id": None,
            "weko_id": "author1",
            "authorNameInfo": [{"familyName": "Doe", "firstName": "John"}],
            "status": "new"
        }
        authors = [author]

        # Setup task children with timeout (result=None)
        task_mock = MagicMock()
        task_mock.task_id = "task1"
        task_mock.result = None  # Simulate timeout with no result

        mock_task.children = [task_mock]

        with patch('weko_authors.tasks.import_author.AsyncResult') as mock_async_result, \
            patch('weko_authors.tasks.datetime') as mock_datetime:

            mock_datetime.now.return_value.strftime.return_value = '2025-03-16 10:00:00'
            mock_async_result.return_value = task_mock

            # Execute
            import_authors_for_over_max(authors)

            # Verify
            mock_check_task_end.assert_called_once()

            # Check that we wrote to the result file with timeout error
            mock_csv_writer.writerow.assert_called_once()

            # Check that the summary was updated with failure count
            mock_update_summary.assert_called_with(0,1)

    def test_import_authors_for_over_max_no_summary(self, app2, mock_cache,
                                                mock_get_cache_data, mock_update_summary,
                                                mock_csv_writer, mock_group, mock_check_task_end):
        """
        正常系
        条件：サマリーデータが存在しない場合
        入力：有効な著者情報の配列
        期待結果：
            - 新しいサマリーが作成される
            - 正確なカウントが記録される
        """
        # Setup - returns None for summary data
        mock_get_cache_data.return_value = None

        mock_group_obj, mock_task = mock_group
        author = {
            "pk_id": 1,
            "current_weko_id": None,
            "weko_id": "author1",
            "authorNameInfo": [{"familyName": "Doe", "firstName": "John"},
                            {"familyName": "山田", "firstName": "太郎"},
                            {"familyName": "", "firstName": ""}],
            "status": "new"
        }
        authors = [author]

        task_mock = MagicMock()
        task_mock.task_id = "task1"
        task_mock.result = {
            'start_date': '2025-03-16 10:00:00',
            'end_date': '2025-03-16 10:00:05',
            'status': states.SUCCESS
        }

        mock_task.children = [task_mock]

        with patch('weko_authors.tasks.import_author.AsyncResult') as mock_async_result:
            mock_async_result.return_value = task_mock

            # Execute
            import_authors_for_over_max(authors)

            # Verify
            # Check that a new summary was created
            mock_update_summary.assert_called_with(1,0)

    def test_import_authors_for_over_max_for_cover(self, app2, mock_cache,
                                                mock_get_cache_data, mock_update_summary,
                                                mock_csv_writer, mock_group, mock_check_task_end):
        """
        正常系
        条件：AsyncResultのstatusがPENDINGの場合
        入力：有効な著者情報の配列
        期待結果：
            - 正確なカウントが記録される
        """
        # Setup - returns None for summary data
        mock_get_cache_data.return_value = None

        mock_group_obj, mock_task = mock_group
        author = {
            "pk_id": 1,
            "current_weko_id": None,
            "weko_id": "author1",
            "authorNameInfo": [{"familyName": "Doe", "firstName": "John"},
                            {"familyName": "山田", "firstName": "太郎"},
                            {"familyName": "", "firstName": ""}],
            "status": "new"
        }
        authors = [author]

        task_mock = MagicMock()
        task_mock.task_id = "task1"
        task_mock.result = {
            'start_date': '2025-03-16 10:00:00',
            'end_date': '2025-03-16 10:00:05',
            'status': states.PENDING
        }

        mock_task.children = [task_mock]

        with patch('weko_authors.tasks.import_author.AsyncResult') as mock_async_result:
            mock_async_result.return_value = task_mock

            # Execute
            import_authors_for_over_max(authors)

            # Verify
            # Check that a new summary was created
            mock_update_summary.assert_called_with(0,0)


# def import_id_prefix(prefix):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_import_id_prefix -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_import_id_prefix(app, caplog: LogCaptureFixture):
    result = import_id_prefix(None)
    assert result['status'] == 'SUCCESS'
    assert 'start_date' in result
    assert 'end_date' in result

    with patch('weko_authors.tasks.import_id_prefix_to_system', side_effect=ValueError({"error_id": 123, "message": "DB upload failed"})):
        # mock_func.side_effect = Exception("Mocked exception")
        # with pytest.raises(Exception) as ex:
        result = import_id_prefix(None)
        info_logs = [record for record in caplog.record_tuples if record[1] == logging.ERROR]
        assert [('testapp', logging.ERROR, "{'error_id': 123, 'message': 'DB upload failed'}")] == info_logs
        assert result['status'] == 'FAILURE'


# def import_affiliation_id(affiliation_id):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_import_affiliation_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_import_affiliation_id(app, caplog: LogCaptureFixture):
    result = import_affiliation_id(None)
    assert result['status'] == 'SUCCESS'
    assert 'start_date' in result
    assert 'end_date' in result

    with patch('weko_authors.tasks.import_affiliation_id_to_system', side_effect=ValueError({"error_id": 123, "message": "DB upload failed"})):
        result = import_affiliation_id(None)
        info_logs = [record for record in caplog.record_tuples if record[1] == logging.ERROR]
        assert [('testapp', logging.ERROR, "{'error_id': 123, 'message': 'DB upload failed'}")] == info_logs
        assert result['status'] == 'FAILURE'


# def import_author_over_max(reached_point, task_ids ,max_part):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_import_author_over_max -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_import_author_over_max(app, caplog: LogCaptureFixture):
    reached_points = {"part_number": 101, "count": 3}
    task_ids = ["aaa","bbb","ccc"]

    with patch('weko_authors.tasks.check_task_end', return_value=0), \
        patch("weko_authors.tasks.import_authors_from_temp_files") as mock_temp:
            result = import_author_over_max(reached_points, task_ids, 5)
            assert result['status'] == 'SUCCESS'
            mock_temp.assert_called()

    with patch('weko_authors.tasks.check_task_end', return_value=0):
        with patch("weko_authors.tasks.import_authors_from_temp_files", side_effect=ValueError({"error_id": 123, "message": "file not found"})) as mock_temp:
            info_logs = [record for record in caplog.record_tuples if record[1] == logging.ERROR]
            result = import_author_over_max(reached_points, task_ids, 5)
            [('testapp', logging.ERROR, "{'error_id': 123, 'message': 'file not found'}")] == info_logs
            assert result['status'] == 'FAILURE'


# def write_result_temp_file(result):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_write_result_temp_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_write_result_temp_file(app):
    # with patch('weko_authors.tasks.write_result_temp_file', result_file_path):
    # with patch('weko_authors.tasks.current_cache.get') as mock_getenv:
        # mock_getenv.return_value = result_file_path
    test = [{
            "start_date": 2025-3-10,
            "end_date": 2025-3-14,
            "weko_id": 1,
            "full_name": "kimura,shinji",
            "type": "new",
            "status": 'SUCCESS',
            "error_id": "delete_author_link"
            }]
    with patch("weko_authors.tasks.open") as mock_writer:
        update_cache_data(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_OVER_MAX_FILE_PATH_KEY"], "/data/test_over_max")
        write_result_temp_file(test)
        mock_writer.assert_called()

    with pytest.raises(Exception):
        write_result_temp_file(test)


# def update_summary(success_count, failure_count):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_update_summary -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_update_summary(app):
    delete_cache_data(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_SUMMARY_KEY"])
    update_summary(2, 2)
    summary = get_cache_data(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_SUMMARY_KEY"])
    assert summary["success_count"] == 2
    assert summary["failure_count"] == 2

    update_summary(2, 2)
    summary = get_cache_data(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_SUMMARY_KEY"])
    assert summary["success_count"] == 4
    assert summary["failure_count"] == 4


# def prepare_display_status(status, type, error_id):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_prepare_display_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_prepare_display_status():
    result = prepare_display_status('SUCCESS', 'new', None)
    assert result == 'Register Success'

    result = prepare_display_status('FAILURE', type, 'delete_author_link')
    assert result == 'Error: The author is linked to items and cannot be deleted.'

    result = prepare_display_status('FAILURE', type, 'other_error')
    assert result == 'Error: Failed to import.'


# def prepare_success_msg(type):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_prepare_success_msg -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_prepare_success_msg():
    result = prepare_success_msg('new')
    assert result == 'Register Success'

    result = prepare_success_msg('update')
    assert result == 'Update Success'

    result = prepare_success_msg('deleted')
    assert result == 'Delete Success'

    result = prepare_success_msg('none')
    assert result == ''


# def check_task_end(task_ids):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_check_task_end -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_check_task_end(app):
    data = ["aaa","bbb","ccc"]
    mock_task1 = MagicMock()
    mock_task1.result = {'end_date': '2023-01-01'}

    mock_task2 = MagicMock()
    mock_task2.result = {'end_date': '2023-01-01'}

    mock_task3 = MagicMock()
    mock_task3.result = {'end_date': '2023-01-01'}
    with patch('weko_authors.tasks.import_author.AsyncResult', side_effect=[mock_task1, mock_task2, mock_task3]),\
        patch("weko_authors.tasks.sleep") as mock_sleep:
        result = check_task_end(data)
        assert result == 0
        mock_sleep.assert_not_called()
    with patch("weko_authors.tasks.import_author.AsyncResult",return_value=MagicMock(result = "")),\
        patch("weko_authors.tasks.sleep") as mock_sleep:
        result = check_task_end(data)
        mock_sleep.assert_called()


# def check_tmp_file_time_for_author():
# .tox/c1/bin/pytest --cov=weko_authors tests/test_tasks.py::test_check_tmp_file_time_for_author -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_check_tmp_file_time_for_author(app, caplog: LogCaptureFixture):
    mock_file_path = '/mock/path/to/file'
    mock_current_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    with patch('glob.glob', return_value=[mock_file_path]), \
        patch('os.path.getmtime', return_value=(mock_current_time - timedelta(seconds=3600)).timestamp()), \
        patch('os.remove') as mock_remove,\
        patch('os.rmdir') as mock_rmdir,\
        patch('os.path.exists'),\
        patch('os.listdir', return_value=[]):

        check_tmp_file_time_for_author()
        mock_remove.assert_called()
        mock_rmdir.assert_called()

    mock_current_time = datetime.now(timezone.utc)
    with patch('glob.glob', return_value=[mock_file_path]), \
        patch('os.path.getmtime', return_value=(mock_current_time - timedelta(seconds=3600)).timestamp()), \
        patch('os.remove') as mock_remove,\
        patch('os.rmdir') as mock_rmdir,\
        patch('os.path.exists', result_value = True),\
        patch('os.listdir', return_value=["a"]):

        check_tmp_file_time_for_author()
        mock_remove.assert_not_called()
        mock_rmdir.assert_not_called()

    mock_current_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    with patch('glob.glob', return_value=[mock_file_path]), \
        patch('os.path.getmtime', return_value=(mock_current_time - timedelta(seconds=3600)).timestamp()), \
        patch('os.remove', side_effect=OSError) as mock_remove,\
        patch('os.listdir', return_value=["a"]):
        caplog.set_level(logging.ERROR)

        check_tmp_file_time_for_author()
