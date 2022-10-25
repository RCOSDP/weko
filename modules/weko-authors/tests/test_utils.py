from invenio_indexer.api import RecordIndexer
from invenio_cache import current_cache
from weko_authors.utils import (
    get_author_setting_obj,
    check_email_existed,
    get_export_status,
    set_export_status,
    delete_export_status,
    get_export_url,
    save_export_url
)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp


class MockClient():
    def __init__(self):
        self.return_value=""
    def search(self,index,doc_type,body):
        return self.return_value

# def get_author_setting_obj(scheme):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_get_author_setting_obj -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_author_setting_obj(prefix_settings):
    result = get_author_setting_obj("ORICD")
    assert result == prefix_settings["orcid"]
    
    result = get_author_setting_obj("not_exist")
    assert result == None


# def check_email_existed(email: str):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_check_email_existed -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_check_email_existed(app,mocker):
    data={"hits":{"total":1,"hits":[{"_source":{"pk_id":1}}]}}
    mock_indexer = RecordIndexer()
    mock_indexer.client = MockClient()
    mock_indexer.client.return_value=data
    mocker.patch("weko_authors.utils.RecordIndexer",return_value=mock_indexer)
    result = check_email_existed("test@test.org")
    assert result == {"email":"test@test.org","author_id":1}
    
    data = {"hits":{"total":0}}
    mock_indexer.client.return_value=data
    result = check_email_existed("test@test.org")
    assert result == {"email":"test@test.org","author_id":""}


# def get_export_status():
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_get_export_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_export_status(app):
    current_cache.set("weko_authors_export_status","test_value")
    result = get_export_status()
    assert result == "test_value"


# def set_export_status(start_time=None, task_id=None):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_set_export_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_set_export_status(app):
    current_cache.delete("weko_authors_export_status")
    result = set_export_status()
    assert result == {}
    assert current_cache.get("weko_authors_export_status") == {}
    
    result = set_export_status("start_time","test_task_id")
    assert result == {"start_time":"start_time","task_id":"test_task_id"}
    assert current_cache.get("weko_authors_export_status") == {"start_time":"start_time","task_id":"test_task_id"}
    
# def delete_export_status():
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_delete_export_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_delete_export_status(app):
    current_cache.set("weko_authors_export_status","test_value")
    delete_export_status()
    assert current_cache.get("weko_authors_export_status") == None


# def get_export_url():
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_get_export_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_export_url(app):
    current_cache.set("weko_authors_exported_url","test/test.txt")
    result = get_export_url()
    assert result == "test/test.txt"
    current_cache.delete("weko_authors_exported_url")


# def save_export_url(start_time, end_time, file_uri):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_get_export_url -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_save_export_url(app):
    result = save_export_url("start_time","end_time","test_file.txt")
    assert result == {"start_time":"start_time","end_time":"end_time","file_uri":"test_file.txt"}
    assert current_cache.get("weko_authors_exported_url") == {"start_time":"start_time","end_time":"end_time","file_uri":"test_file.txt"}
    current_cache.delete("weko_authors_exported_url")


# def export_authors():
# def check_import_data(file_name: str, file_content: str):
# def getEncode(filepath):
# def unpackage_and_check_import_file(file_format, file_name, temp_file, mapping_ids):
# def validate_import_data(file_format, file_data, mapping_ids, mapping):
# def get_values_by_mapping(keys, data, parent_key=None):
# def autofill_data(item, values, autofill_data):
# def convert_data_by_mask(item, values, mask):
# def convert_scheme_to_id(item, values, authors_prefix):
# def set_record_status(file_format, list_existed_author_id, item, errors, warnings):
# def flatten_authors_mapping(mapping, parent_key=None):
# def import_author_to_system(author):
# def get_count_item_link(pk_id):
