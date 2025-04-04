
from os.path import dirname, join
import pytest
import copy
from mock import patch, MagicMock, Mock
from flask import current_app
import datetime
from unittest.mock import mock_open

from invenio_indexer.api import RecordIndexer
from invenio_cache import current_cache
import csv

from weko_authors.models import Authors
from weko_authors.config import WEKO_AUTHORS_FILE_MAPPING
from weko_authors.utils import (
    get_author_prefix_obj,
    get_author_affiliation_obj,
    check_email_existed,
    get_export_status,
    set_export_status,
    delete_export_status,
    get_export_url,
    save_export_url,
    export_authors,
    check_import_data,
    getEncode,
    unpackage_and_check_import_file,
    validate_import_data,
    get_values_by_mapping,
    autofill_data,
    convert_data_by_mask,
    convert_scheme_to_id,
    set_record_status,
    flatten_authors_mapping,
    import_author_to_system,
    get_count_item_link,
    count_authors,
    update_cache_data,
    write_tmp_part_file,
    unpackage_and_check_import_file_for_prefix,
    get_check_base_name,
    get_check_result,
    handle_check_consistence_with_mapping_for_prefix,
    check_import_data_for_prefix,
    validate_import_data_for_prefix,
    import_id_prefix_to_system,
    import_affiliation_id_to_system,
    band_check_file_for_user,
    prepare_import_data,
    write_to_tempfile,
    create_result_file_for_user
)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp


class MockClient():
    def __init__(self):
        self.return_value=""
    def search(self,index,doc_type,body):
        return self.return_value

# def get_author_prefix_obj(scheme):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_get_author_prefix_obj -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_author_prefix_obj(authors_prefix_settings):
    result = get_author_prefix_obj("ORCID")
    assert result == authors_prefix_settings[1]

    # raise Exception
    with patch("weko_authors.utils.db.session.query") as mock_query:
        mock_query.return_value.filter.return_value.one_or_none.side_effect=Exception("test_error")
        result = get_author_prefix_obj("ORCID")
        assert result == None

# def get_author_affiliation_obj(scheme):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_get_author_affiliation_obj -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_author_affiliation_obj(authors_affiliation_settings):
    result = get_author_affiliation_obj("ISNI")
    assert result == authors_affiliation_settings[0]

    # raise Exception
    with patch("weko_authors.utils.db.session.query") as mock_query:
        mock_query.return_value.filter.return_value.one_or_none.side_effect=Exception("test_error")
        result = get_author_affiliation_obj("ISNI")
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




# def check_import_data(file_name: str, file_content: str):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_check_import_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_check_import_data(app,mocker):
    mapping_all = [
        {"key":"pk_id","label":{"en":"WEKO ID","jp":"WEKO ID"},"mask":{},"validation":{},"autofill":""},
        {"key":"authorNameInfo[0].familyName","label":{"en":"Family Name","jp":"姓"},"mask":{},"validation":{},"autofill":""},
        {"key":"authorNameInfo[0].firstName","label":{"en":"Given Name","jp":"名"},"mask":{},"validation":{},"autofill":""},
        {"key":"authorNameInfo[0].language","label":{"en":"Language","jp":"言語"},"mask":{},"validation":{'map': ['ja', 'ja-Kana', 'en', 'fr','it', 'de', 'es', 'zh-cn', 'zh-tw','ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']},"autofill":""},
        {"key":"authorNameInfo[0].nameFormat","label":{"en":"Name Format","jp":"フォーマット"},"mask":{},"validation":{'map': ['familyNmAndNm']},"autofill":{'condition': {'either_required': ['familyName', 'firstName']},'value': 'familyNmAndNm'}},
        {"key":"authorNameInfo[0].nameShowFlg","label":{"en":"Name Display","jp":"姓名・言語 表示／非表示"},"mask":{'true': 'Y','false': 'N'},"validation":{'map': ['Y', 'N']},"autofill":""},
        {"key":"authorIdInfo[0].idType","label":{"en":"Identifier Scheme","jp":"外部著者ID 識別子"},"mask":{},"validation":{'validator': {'class_name': 'weko_authors.contrib.validation','func_name': 'validate_identifier_scheme'},'required': {'if': ['authorId']}},"autofill":""},
        {"key":"authorIdInfo[0].authorId","label":{"en":"Identifier","jp":"外部著者ID"},"mask":{},"validation":{'required': {'if': ['idType']}},"autofill":""},
        {"key":"authorIdInfo[0].authorIdShowFlg","label":{"en":"Identifier Display","jp":"外部著者ID 表示／非表示"},"mask":{'true': 'Y','false': 'N'},"validation":{'map': ['Y', 'N']},"autofill":""},
        {"key":"emailInfo[0].email","label":{"en":"Mail Address","jp":"メールアドレス"},"mask":{},"validation":{},"autofill":""},
        {"key":"is_deleted","label":{"en":"Delete Flag","jp":"削除フラグ"},"mask":{'true': 'D','false': ''},"validation":{'map': ['D']},"autofill":""},
    ]
    mapping_ids = ["pk_id",
                 "authorNameInfo[0].familyName",
                 "authorNameInfo[0].firstName",
                 "authorNameInfo[0].language",
                 "authorNameInfo[0].nameFormat",
                 "authorNameInfo[0].nameShowFlg",
                 "authorIdInfo[0].idType",
                 "authorIdInfo[0].authorId",
                 "authorIdInfo[0].authorIdShowFlg",
                 "emailInfo[0].email",
                 "is_deleted"
                 ]
    current_cache.set("authors_import_user_file_key","var/tmp/authors_import")
    mocker.patch("weko_authors.utils.flatten_authors_mapping",return_value=(mapping_all,mapping_ids))
    mocker.patch("weko_authors.utils.unpackage_and_check_import_file",return_value=1)
    return_validate = [{'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'true'}], 'authorIdInfo': [{'idType': 2, 'authorId': '1234', 'authorIdShowFlg': 'true'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': '', 'status': 'update'}, {'pk_id': '2', 'authorNameInfo': [{'familyName': 'test', 'firstName': 'smith', 'language': 'en', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'true'}], 'authorIdInfo': [{'idType': 2, 'authorId': '5678', 'authorIdShowFlg': 'true'}], 'emailInfo': [{'email': 'test.smith@test.org'}], 'is_deleted': '', 'status': 'update'}]
    mocker.patch("weko_authors.utils.validate_import_data",return_value=return_validate)
    mock_json_data = '{"test_id": "1000"}'
    mocker.patch("builtins.open", mock_open(read_data=mock_json_data))
    mocker.patch("os.remove")
    file_name = "testfile.tsv"
    test = {
        "list_import_data": {"test_id": "1000"},
        "max_page": 1,
        "counts": {
            "num_total": 2,
            "num_new": 0,
            "num_update": 2,
            "num_delete": 0,
            "num_error": 0,
        },
    }
    result = check_import_data(file_name)
    assert result == test

    current_cache.set("authors_import_user_file_key","var/tmp/authors_import")
    mocker.patch("weko_authors.utils.flatten_authors_mapping",return_value=(mapping_all,mapping_ids))
    mocker.patch("weko_authors.utils.unpackage_and_check_import_file",return_value=1)
    return_validate = [{'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'true'}], 'authorIdInfo': [{'idType': 2, 'authorId': '1234', 'authorIdShowFlg': 'true'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': '', 'status': 'update'}, {'pk_id': '2', 'authorNameInfo': [{'familyName': 'test', 'firstName': 'smith', 'language': 'en', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'true'}], 'authorIdInfo': [{'idType': 2, 'authorId': '5678', 'authorIdShowFlg': 'true'}], 'emailInfo': [{'email': 'test.smith@test.org'}], 'is_deleted': '', 'status': 'update'}]
    mocker.patch("weko_authors.utils.validate_import_data",return_value=return_validate)
    mock_json_data = '{"test_id": "1000"}'
    mocker.patch("builtins.open", mock_open(read_data=mock_json_data))
    mocker.patch("os.remove")
    file_name = "valid_file.csv"
    test = {
        "list_import_data": {"test_id": "1000"},
        "max_page": 1,
        "counts": {
            "num_total": 2,
            "num_new": 0,
            "num_update": 2,
            "num_delete": 0,
            "num_error": 0,
        },
    }
    result = check_import_data(file_name)
    assert result == test

    current_cache.set("authors_import_user_file_key","var/tmp/authors_import")
    mocker.patch("weko_authors.utils.flatten_authors_mapping",return_value=(mapping_all,mapping_ids))
    mocker.patch("weko_authors.utils.unpackage_and_check_import_file",return_value=5)
    return_validate = [{'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'true'}], 'authorIdInfo': [{'idType': 2, 'authorId': '1234', 'authorIdShowFlg': 'true'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': '', 'status': 'update'}, {'pk_id': '2', 'authorNameInfo': [{'familyName': 'test', 'firstName': 'smith', 'language': 'en', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'true'}], 'authorIdInfo': [{'idType': 2, 'authorId': '5678', 'authorIdShowFlg': 'true'}], 'emailInfo': [{'email': 'test.smith@test.org'}], 'is_deleted': '', 'status': 'update'}]
    mocker.patch("weko_authors.utils.validate_import_data",return_value=return_validate)
    mock_json_data = '{"test_id": "1000"}'
    mocker.patch("builtins.open", mock_open(read_data=mock_json_data))
    mocker.patch("os.remove")
    file_name = "multi_part_file.tsv"
    test = {
        "list_import_data": {"test_id": "1000"},
        "max_page": 5,
        "counts": {
            "num_total": 10,
            "num_new": 0,
            "num_update": 10,
            "num_delete": 0,
            "num_error": 0,
        },
    }
    result = check_import_data(file_name)
    assert result == test

    current_cache.set("authors_import_user_file_key","var/tmp/authors_import")
    mocker.patch("weko_authors.utils.flatten_authors_mapping",return_value=(mapping_all,mapping_ids))
    mocker.patch("weko_authors.utils.unpackage_and_check_import_file",return_value=5)
    return_validate = [
        {
            "pk_id": "1",
            "authorNameInfo": [
                {
                    "familyName": "テスト",
                    "firstName": "太郎",
                    "language": "ja",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "true",
                }
            ],
            "authorIdInfo": [{"idType": 2, "authorId": "1234", "authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "test.taro@test.org"}],
            "is_deleted": "",
            "status": "new",
        },
        {
            "pk_id": "2",
            "authorNameInfo": [
                {
                    "familyName": "test",
                    "firstName": "smith",
                    "language": "en",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "true",
                }
            ],
            "authorIdInfo": [{"idType": 2, "authorId": "5678", "authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "test.smith@test.org"}],
            "is_deleted": "",
            "status": "update",
        },
        {
            "pk_id": "3",
            "authorNameInfo": [
                {
                    "familyName": "test",
                    "firstName": "smith",
                    "language": "en",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "true",
                }
            ],
            "authorIdInfo": [{"idType": 2, "authorId": "5678", "authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "test.smith@test.org"}],
            "is_deleted": "",
            "status": "deleted",
        },
    ]
    mocker.patch("weko_authors.utils.validate_import_data",return_value=return_validate)
    mock_json_data = '{"test_id": "1000"}'
    mocker.patch("builtins.open", mock_open(read_data=mock_json_data))
    mocker.patch("os.remove")
    file_name = "multi_part_file.tsv"
    test = {
        "list_import_data": {"test_id": "1000"},
        "max_page": 5,
        "counts": {
            "num_total": 15,
            "num_new": 5,
            "num_update": 5,
            "num_delete": 5,
            "num_error": 0,
        },
    }
    result = check_import_data(file_name)
    assert result == test

    current_cache.set("authors_import_user_file_key","var/tmp/authors_import")
    mocker.patch("weko_authors.utils.flatten_authors_mapping",return_value=(mapping_all,mapping_ids))
    mocker.patch("weko_authors.utils.unpackage_and_check_import_file",return_value=1)
    return_validate = [
        {
            "pk_id": "1",
            "authorNameInfo": [
                {
                    "familyName": "テスト",
                    "firstName": "太郎",
                    "language": "ja",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "true",
                }
            ],
            "authorIdInfo": [{"idType": 2, "authorId": "1234", "authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "test.taro@test.org"}],
            "is_deleted": "",
            "status": "new",
            "errors": ["Existing error"]
        },
        {
            "pk_id": "2",
            "authorNameInfo": [
                {
                    "familyName": "test",
                    "firstName": "smith",
                    "language": "en",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "true",
                }
            ],
            "authorIdInfo": [{"idType": 2, "authorId": "5678", "authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "test.smith@test.org"}],
            "is_deleted": "",
            "status": "update",
            "errors": ["Existing error"]
        },
        {
            "pk_id": "3",
            "authorNameInfo": [
                {
                    "familyName": "test",
                    "firstName": "smith",
                    "language": "en",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "true",
                }
            ],
            "authorIdInfo": [{"idType": 2, "authorId": "5678", "authorIdShowFlg": "true"}],
            "emailInfo": [{"email": "test.smith@test.org"}],
            "is_deleted": "",
            "status": "delete",
            "errors": ["Existing error"]
        },
    ]
    mocker.patch("weko_authors.utils.validate_import_data",return_value=return_validate)
    mock_json_data = '{"test_id": "1000"}'
    mocker.patch("builtins.open", mock_open(read_data=mock_json_data))
    mocker.patch("os.remove")
    file_name = "valid_file.csv"
    test = {
        "list_import_data": {"test_id": "1000"},
        "max_page": 1,
        "counts": {
            "num_total": 3,
            "num_new": 0,
            "num_update": 0,
            "num_delete": 0,
            "num_error": 3,
        },
    }
    result = check_import_data(file_name)
    assert result == test

    current_cache.delete("authors_import_user_file_key")
    mocker.patch("weko_authors.utils.flatten_authors_mapping",return_value=(mapping_all,mapping_ids))
    mock_json_data = '{"test_id": "1000"}'
    mocker.patch("builtins.open", mock_open(read_data=mock_json_data))
    mocker.patch("os.remove", side_effect=Exception)
    file_name = "testfile.tsv"
    mock_logger = mocker.patch("weko_authors.utils.current_app.logger")
    result = check_import_data(file_name)
    mock_logger.error.assert_called()

    # raise Exception with args[0] is dict
    with patch("weko_authors.utils.flatten_authors_mapping",side_effect=Exception({"error_msg":"test_error"})):
        result = check_import_data(file_name)
        assert result == {"error":"test_error"}

    # raise Exception with args[0] is not dict
    with patch("weko_authors.utils.flatten_authors_mapping",side_effect=AttributeError("test_error")):
        result = check_import_data(file_name)
        assert result == {"error":"Internal server error"}

    # raise UnicodeDecodeError
    with patch("weko_authors.utils.flatten_authors_mapping",side_effect=UnicodeDecodeError("utf-8",b"test",0,1,"test_reason")):
        result = check_import_data(file_name)
        assert result == {"error":"test_reason"}

# def getEncode(filepath):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_getEncode -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_getEncode():
    result = getEncode(join(dirname(__file__),"data/test_files/test_utf-8.txt"))
    assert result == "utf-8"

    class MockOpen:
        def __init__(self, path, encoding=None):
            self.path=path
            self.encoding = encoding
        def read(self):
            if self.encoding!="not_exist_encode":
                raise UnicodeDecodeError(self.encoding,b"test",0,1,"test_reason")
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_value, traceback):
            pass
    def mock_open(path, encoding=None):
        return MockOpen(path,encoding)

    with patch("builtins.open",side_effect=mock_open):
        result = getEncode("test_path")
        assert result == ""


# def unpackage_and_check_import_file(file_format, file_name, temp_file, mapping_ids):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_unpackage_and_check_import_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_unpackage_and_check_import_file(app, mocker):
    file_format="tsv"
    file_name="test_file.txt"
    mapping_ids = ["pk_id",
                 "authorNameInfo[0].familyName",
                 "authorNameInfo[0].firstName",
                 "authorNameInfo[0].language",
                 "authorNameInfo[0].nameFormat",
                 "authorNameInfo[0].nameShowFlg",
                 "authorIdInfo[0].idType",
                 "authorIdInfo[0].authorId",
                 "authorIdInfo[0].authorIdShowFlg",
                 "emailInfo[0].email",
                 "is_deleted"
                 ]
    # duplication header
    temp_file=join(dirname(__file__),"data/test_files/duplicated_header.tsv")
    with pytest.raises(Exception) as e:
        unpackage_and_check_import_file(file_format,file_name,temp_file,mapping_ids)
    assert e.value.args[0] == {"error_msg":"The following metadata keys are duplicated.<br/>pk_id"}

    # exist not_consistent_list
    temp_file=join(dirname(__file__),"data/test_files/not_consistency.tsv")
    with patch("weko_search_ui.utils.handle_check_consistence_with_mapping", return_value=["exist_not_consistent_value"]):
        with pytest.raises(Exception) as e:
            unpackage_and_check_import_file(file_format,file_name,temp_file,mapping_ids)
        assert e.value.args[0] == {"error_msg":"Specified item does not consistency with DB item.<br/>exist_not_consistent_value"}

    # nomal
    mocker.patch("weko_authors.utils.write_tmp_part_file")
    temp_file=join(dirname(__file__),"data/test_files/import_data.tsv")
    result = unpackage_and_check_import_file(file_format,file_name,temp_file,mapping_ids)
    assert result == 1

    # data_parse_metadata is None
    with patch("weko_search_ui.utils.parse_to_json_form", return_value=[]):
        with pytest.raises(Exception) as e:
            result = unpackage_and_check_import_file(file_format,file_name,temp_file,mapping_ids)
        assert e.value.args[0] == {"error_msg": "Cannot read TSV file correctly." }

    # raise UnicodeDecodeError
    with patch("weko_search_ui.utils.parse_to_json_form", side_effect=UnicodeDecodeError("utf-8",b"test",0,1,"test_reason")):
        with pytest.raises(UnicodeDecodeError) as e:
            result = unpackage_and_check_import_file(file_format,file_name,temp_file,mapping_ids)
        assert e.value.reason == "test_file.txt could not be read. Make sure the file format is TSV and that the file is UTF-8 encoded."

    # not data
    temp_file=join(dirname(__file__),"data/test_files/not_data.tsv")
    with pytest.raises(Exception) as e:
        unpackage_and_check_import_file(file_format,file_name,temp_file,mapping_ids)
    assert e.value.args[0] == {"error_msg":"There is no data to import."}

    # file format = csv
    mocker.patch.object(current_app.config, "get", return_value=2)
    mocker.patch("weko_authors.utils.write_tmp_part_file")
    temp_file=join(dirname(__file__),"data/test_files/import_data.csv")
    result = unpackage_and_check_import_file("csv",file_name,temp_file,mapping_ids)
    assert result == 1


# def validate_import_data(file_format, file_data, mapping_ids, mapping, list_import_id):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_validate_import_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_validate_import_data(authors_prefix_settings,mocker):
    mocker.patch("weko_authors.utils.WekoAuthors.get_author_for_validation",return_value=({"1":True,"2":True},{"2":{"1234":["1"],"5678":["2"]}}))

    file_format = "tsv"
    file_data = [
        {
            "pk_id": "1",
            "weko_id": "1",
            "authorNameInfo": [
                {
                    "familyName": "テスト",
                    "firstName": "太郎",
                    "language": "ja",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "Y",
                }
            ],
            "authorIdInfo": [
                {"idType": "ORCID", "authorId": "1234", "authorIdShowFlg": "Y"}
            ],
            "emailInfo": [{"email": "test.taro@test.org"}],
            "is_deleted": "",
        }
    ]
    mapping_ids = ["pk_id",
                 "authorNameInfo[0].familyName",
                 "authorNameInfo[0].firstName",
                 "authorNameInfo[0].language",
                 "authorNameInfo[0].nameFormat",
                 "authorNameInfo[0].nameShowFlg",
                 "authorIdInfo[0].idType",
                 "authorIdInfo[0].authorId",
                 "authorIdInfo[0].authorIdShowFlg",
                 "emailInfo[0].email",
                 "is_deleted"
                 ]
    mapping = [
        {"key": "pk_id", "validation": {}},
        {"key": "authorNameInfo[0].familyName", "validation": {}},
        {"key": "authorNameInfo[0].firstName", "validation": {}},
        {"key": "authorNameInfo[0].language", "validation": {"map": ["ja", "en"]}},
        {"key": "authorNameInfo[0].nameFormat", "validation": {"map": ["familyNmAndNm"]}},
        {"key": "authorNameInfo[0].nameShowFlg", "validation": {"map": ["Y", "N"]}},
        {
            "key": "authorIdInfo[0].idType",
            "validation": {
                "validator": {
                    "class_name": "weko_authors.contrib.validation",
                    "func_name": "validate_identifier_scheme",
                }
            },
        },
        {
            "key": "authorIdInfo[0].authorId",
            "validation": {"required": {"if": ["authorIdInfo[0].idType"]}},
        },
        {"key": "authorIdInfo[0].authorIdShowFlg", "validation": {"map": ["Y", "N"]}},
        {"key": "emailInfo[0].email", "validation": {}},
        {"key": "is_deleted", "validation": {"map": ["D"]}},
    ]
    list_import_id = []
    test = [
        {
            "pk_id": "1",
            "weko_id": "1",
            "current_weko_id": "1",
            "authorNameInfo": [
                {
                    "familyName": "テスト",
                    "firstName": "太郎",
                    "language": "ja",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "Y",
                }
            ],
            "authorIdInfo": [{"idType": "2", "authorId": "1234", "authorIdShowFlg": "Y"}],
            "emailInfo": [{"email": "test.taro@test.org"}],
            "is_deleted": "",
            "status": "update",
        }
    ]
    mocker.patch("weko_authors.utils.WekoAuthors.get_weko_id_by_pk_id",return_value="1")
    mocker.patch("weko_authors.utils.check_weko_id_is_exits_for_import",return_value=[])
    result = validate_import_data(file_format,file_data,mapping_ids,mapping,list_import_id)
    assert result == test

    # pk_id is already in the list_import_id
    file_format = "tsv"
    file_data = [
        {
            "pk_id": "1",
            "weko_id": "1",
            "authorNameInfo": [
                {
                    "familyName": "テスト",
                    "firstName": "太郎",
                    "language": "ja",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "Y",
                }
            ],
            "authorIdInfo": [
                {"idType": "ORCID", "authorId": "1234", "authorIdShowFlg": "Y"}
            ],
            "emailInfo": [{"email": "test.taro@test.org"}],
            "is_deleted": "",
        },
        {
            "pk_id": "1",
            "weko_id": "1",
            "authorNameInfo": [
                {
                    "familyName": "テスト",
                    "firstName": "太郎",
                    "language": "ja",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "Y",
                }
            ],
            "authorIdInfo": [
                {"idType": "ORCID", "authorId": "1234", "authorIdShowFlg": "Y"}
            ],
            "emailInfo": [{"email": "test.taro@test.org"}],
            "is_deleted": "",
        },
    ]
    list_import_id = []
    mocker.patch("weko_authors.utils.WekoAuthors.get_weko_id_by_pk_id",return_value="1")
    mocker.patch("weko_authors.utils.check_weko_id_is_exits_for_import",return_value=[])
    test = [
        {
            "pk_id": "1",
            "weko_id": "1",
            "current_weko_id": "1",
            "authorNameInfo": [
                {
                    "familyName": "テスト",
                    "firstName": "太郎",
                    "language": "ja",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "Y",
                }
            ],
            "authorIdInfo": [{"idType": "2", "authorId": "1234", "authorIdShowFlg": "Y"}],
            "emailInfo": [{"email": "test.taro@test.org"}],
            "is_deleted": "",
            "status": "update",
        },
        {
            "pk_id": "1",
            "weko_id": "1",
            "current_weko_id": "1",
            "authorNameInfo": [
                {
                    "familyName": "テスト",
                    "firstName": "太郎",
                    "language": "ja",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "Y",
                }
            ],
            "authorIdInfo": [{"idType": "2", "authorId": "1234", "authorIdShowFlg": "Y"}],
            "emailInfo": [{"email": "test.taro@test.org"}],
            "is_deleted": "",
            "status": "update",
            "errors": ["There is duplicated data in the tsv file."],
        },
    ]
    result = validate_import_data(file_format,file_data,mapping_ids,mapping,list_import_id)
    assert result == test

    # errors_key is ture（check required）
    file_format = "tsv"
    file_data = [
        {
            "pk_id": "1",
            "weko_id": "1",
            "authorNameInfo": [
                {
                    "familyName": "",
                    "firstName": "太郎",
                    "language": "ja",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "Y",
                }
            ],
            "authorIdInfo": [
                {"idType": "ORCID", "authorId": "1234", "authorIdShowFlg": "Y"}
            ],
            "emailInfo": [{"email": "test.taro@test.org"}],
            "is_deleted": "",
        }
    ]
    mapping = [
        {"key": "pk_id", "validation": {}},
        {
            "key": "authorNameInfo[0].familyName",
            "validation": {"required": {"if": ["firstName"]}},
        },
        {"key": "authorNameInfo[0].firstName", "validation": {}},
        {"key": "authorNameInfo[0].language", "validation": {"map": ["ja", "en"]}},
        {
            "key": "authorNameInfo[0].nameFormat",
            "validation": {"map": ["familyNmAndNm"]},
        },
        {"key": "authorNameInfo[0].nameShowFlg", "validation": {"map": ["Y", "N"]}},
        {
            "key": "authorIdInfo[0].idType",
            "validation": {
                "validator": {
                    "class_name": "weko_authors.contrib.validation",
                    "func_name": "validate_identifier_scheme",
                }
            },
        },
        {
            "key": "authorIdInfo[0].authorId",
            "validation": {"required": {"if": ["idType"]}},
        },
        {"key": "authorIdInfo[0].authorIdShowFlg", "validation": {"map": ["Y", "N"]}},
        {"key": "emailInfo[0].email", "validation": {}},
        {"key": "is_deleted", "validation": {"map": ["D"]}},
    ]
    list_import_id = []
    test = [
        {
            "pk_id": "1",
            "weko_id": "1",
            "current_weko_id": "1",
            "authorNameInfo": [
                {
                    "familyName": "",
                    "firstName": "太郎",
                    "language": "ja",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "Y",
                }
            ],
            "authorIdInfo": [{"idType": "2", "authorId": "1234", "authorIdShowFlg": "Y"}],
            "emailInfo": [{"email": "test.taro@test.org"}],
            "is_deleted": "",
            "status": "update",
            "errors": ["authorNameInfo[0].familyName is required item."],
        }
    ]
    mocker.patch("weko_authors.utils.WekoAuthors.get_weko_id_by_pk_id",return_value="1")
    mocker.patch("weko_authors.utils.check_weko_id_is_exits_for_import",return_value=[])
    result = validate_import_data(file_format,file_data,mapping_ids,mapping,list_import_id)
    assert result == test

    # errors_key is ture（check allow data）
    file_format = "tsv"
    file_data = [
        {
            "pk_id": "1",
            "weko_id": "1",
            "authorNameInfo": [
                {
                    "familyName": "テスト",
                    "firstName": "太郎",
                    "language": "de",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "Y",
                }
            ],
            "authorIdInfo": [
                {"idType": "ORCID", "authorId": "1234", "authorIdShowFlg": "Y"}
            ],
            "emailInfo": [{"email": "test.taro@test.org"}],
            "is_deleted": "",
        }
    ]
    list_import_id = []
    mapping = [
        {"key": "pk_id", "validation": {}},
        {"key": "authorNameInfo[0].familyName", "validation": {}},
        {"key": "authorNameInfo[0].firstName", "validation": {}},
        {"key": "authorNameInfo[0].language", "validation": {"map": ["ja", "en"]}},
        {
            "key": "authorNameInfo[0].nameFormat",
            "validation": {"map": ["familyNmAndNm"]},
        },
        {"key": "authorNameInfo[0].nameShowFlg", "validation": {"map": ["Y", "N"]}},
        {
            "key": "authorIdInfo[0].idType",
            "validation": {
                "validator": {
                    "class_name": "weko_authors.contrib.validation",
                    "func_name": "validate_identifier_scheme",
                }
            },
        },
        {
            "key": "authorIdInfo[0].authorId",
            "validation": {"required": {"if": ["idType"]}},
        },
        {"key": "authorIdInfo[0].authorIdShowFlg", "validation": {"map": ["Y", "N"]}},
        {"key": "emailInfo[0].email", "validation": {}},
        {"key": "is_deleted", "validation": {"map": ["D"]}},
    ]
    test = [
        {
            "pk_id": "1",
            "weko_id": "1",
            "current_weko_id": "1",
            "authorNameInfo": [
                {
                    "familyName": "テスト",
                    "firstName": "太郎",
                    "language": "de",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "Y",
                }
            ],
            "authorIdInfo": [{"idType": "2", "authorId": "1234", "authorIdShowFlg": "Y"}],
            "emailInfo": [{"email": "test.taro@test.org"}],
            "is_deleted": "",
            "status": "update",
            "errors": ["authorNameInfo[0].language should be set by one of ['ja', 'en']."],
        }
    ]
    mocker.patch("weko_authors.utils.WekoAuthors.get_weko_id_by_pk_id",return_value="1")
    mocker.patch("weko_authors.utils.check_weko_id_is_exits_for_import",return_value=[])
    result = validate_import_data(file_format,file_data,mapping_ids,mapping,list_import_id)
    assert result == test

    # pk_id is None and errors_msg is exists
    file_format = "tsv"
    file_data = [
        {
            "weko_id": "1",
            "authorNameInfo": [
                {
                    "familyName": "テスト",
                    "firstName": "太郎",
                    "language": "ja",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "Y",
                }
            ],
            "authorIdInfo": [
                {"idType": "ORCID", "authorId": "1234", "authorIdShowFlg": "Y"}
            ],
            "emailInfo": [{"email": "test.taro@test.org"}],
            "is_deleted": "",
        }
    ]
    mapping_ids = ["pk_id",
            "authorNameInfo[0].familyName",
            "authorNameInfo[0].firstName",
            "authorNameInfo[0].language",
            "authorNameInfo[0].nameFormat",
            "authorNameInfo[0].nameShowFlg",
            "authorIdInfo[0].idType",
            "authorIdInfo[0].authorId",
            "authorIdInfo[0].authorIdShowFlg",
            "emailInfo[0].email",
            "is_deleted",
            "affiliationInfo[0].identifierInfo[0].affiliationIdType"
            ]
    mapping = [
        {"key": "pk_id", "validation": {}},
        {"key": "authorNameInfo[0].familyName", "validation": {}},
        {"key": "authorNameInfo[0].firstName", "validation": {}},
        {"key": "authorNameInfo[0].language", "validation": {"map": ["ja", "en"]}},
        {
            "key": "authorNameInfo[0].nameFormat",
            "validation": {"map": ["familyNmAndNm"]},
        },
        {"key": "authorNameInfo[0].nameShowFlg", "validation": {"map": ["Y", "N"]}},
        {
            "key": "authorIdInfo[0].idType",
            "validation": {
                "validator": {
                    "class_name": "weko_authors.contrib.validation",
                    "func_name": "validate_identifier_scheme",
                }
            },
        },
        {
            "key": "authorIdInfo[0].authorId",
            "validation": {"required": {"if": ["idType"]}},
        },
        {"key": "authorIdInfo[0].authorIdShowFlg", "validation": {"map": ["Y", "N"]}},
        {"key": "emailInfo[0].email", "validation": {}},
        {"key": "is_deleted", "validation": {"map": ["D"]}},
        {"key": "affiliationInfo[0].identifierInfo[0].affiliationIdType", "validation": {}}
    ]
    list_import_id = []
    test = [
        {
            "weko_id": "1",
            "current_weko_id": "1",
            "authorNameInfo": [
                {
                    "familyName": "テスト",
                    "firstName": "太郎",
                    "language": "ja",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "Y",
                }
            ],
            "authorIdInfo": [{"idType": "2", "authorId": "1234", "authorIdShowFlg": "Y"}],
            "emailInfo": [{"email": "test.taro@test.org"}],
            "is_deleted": "",
            "status": "new",
            "errors": ["Specified WEKO ID already exist.", "validator error"],
            "warnings": ["idType warning"],
        }
    ]
    mocker.patch("weko_authors.utils.WekoAuthors.get_weko_id_by_pk_id",return_value="1")
    mocker.patch("weko_authors.utils.check_weko_id_is_exits_for_import",return_value=["Specified WEKO ID already exist."])
    mocker.patch("weko_authors.utils.validate_by_extend_validator",return_value=["validator error"])
    mocker.patch("weko_authors.utils.validate_external_author_identifier",return_value="idType warning")
    result = validate_import_data(file_format,file_data,mapping_ids,mapping,list_import_id)
    assert result == test

    # autofill and mask is exists
    file_format = "tsv"
    file_data = [
        {
            "pk_id": "1",
            "weko_id": "1",
            "authorNameInfo": [
                {
                    "familyName": "テスト",
                    "firstName": "太郎",
                    "language": "ja",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "Y",
                }
            ],
            "authorIdInfo": [
                {"idType": "ORCID", "authorId": "1234", "authorIdShowFlg": "Y"}
            ],
            "emailInfo": [{"email": "test.taro@test.org"}],
            "is_deleted": "",
        }
    ]
    mapping_ids = ["pk_id",
                 "authorNameInfo[0].familyName",
                 "authorNameInfo[0].firstName",
                 "authorNameInfo[0].language",
                 "authorNameInfo[0].nameFormat",
                 "authorNameInfo[0].nameShowFlg",
                 "authorIdInfo[0].idType",
                 "authorIdInfo[0].authorId",
                 "authorIdInfo[0].authorIdShowFlg",
                 "emailInfo[0].email",
                 "is_deleted",
                 "mask",
                 "test",
                 ]
    mapping = [
        {"key": "pk_id", "validation": {}},
        {"key": "authorNameInfo[0].familyName", "validation": {}},
        {"key": "authorNameInfo[0].firstName", "validation": {}},
        {"key": "authorNameInfo[0].language", "validation": {"map": ["ja", "en"]}},
        {"key": "authorNameInfo[0].nameFormat", "validation": {"map": ["familyNmAndNm"]}},
        {"key": "authorNameInfo[0].nameShowFlg", "validation": {"map": ["Y", "N"]}},
        {
            "key": "authorIdInfo[0].idType",
            "validation": {
                "validator": {
                    "class_name": "weko_authors.contrib.validation",
                    "func_name": "validate_identifier_scheme",
                }
            },
        },
        {
            "key": "authorIdInfo[0].authorId",
            "validation": {"required": {"if": ["authorIdInfo[0].idType"]}},
        },
        {"key": "authorIdInfo[0].authorIdShowFlg", "validation": {"map": ["Y", "N"]}},
        {"key": "emailInfo[0].email", "validation": {}},
        {"key": "is_deleted", "validation": {"map": ["D"]}},
        {"autofill": "test","key": "test", "validation": {}},
        {"mask": "test", "key": "test", "validation": {}}
    ]
    list_import_id = []
    test = [
        {
            "pk_id": "1",
            "weko_id": "1",
            "current_weko_id": "1",
            "authorNameInfo": [
                {
                    "familyName": "テスト",
                    "firstName": "太郎",
                    "language": "ja",
                    "nameFormat": "familyNmAndNm",
                    "nameShowFlg": "Y",
                }
            ],
            "authorIdInfo": [{"idType": "2", "authorId": "1234", "authorIdShowFlg": "Y"}],
            "emailInfo": [{"email": "test.taro@test.org"}],
            "is_deleted": "",
            "status": "update",
        }
    ]
    mocker.patch("weko_authors.utils.WekoAuthors.get_weko_id_by_pk_id",return_value="1")
    mocker.patch("weko_authors.utils.check_weko_id_is_exits_for_import",return_value=[])
    mocker.patch("weko_authors.utils.validate_by_extend_validator",return_value=[])
    mocker.patch("weko_authors.utils.validate_external_author_identifier",return_value="")
    mocker.patch("weko_authors.utils.autofill_data")
    mocker.patch("weko_authors.utils.convert_data_by_mask")
    result = validate_import_data(file_format,file_data,mapping_ids,mapping,list_import_id)
    assert result == test

# def get_values_by_mapping(keys, data, parent_key=None):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_get_values_by_mapping -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_values_by_mapping():
    data = {
        'pk_id': '1',
        'authorNameInfo': [{'familyName': 'テスト',
                            'firstName': '太郎',
                            'language': 'ja',
                            'nameFormat': 'familyNmAndNm',
                            'nameShowFlg': 'Y'}],
        'authorIdInfo': [{'idType': 'ORCID',
                          'authorId': '1234',
                          'authorIdShowFlg': 'Y'}],
        'emailInfo': [{'email': 'test.taro@test.org'}],
        'is_deleted': ''}

    keys = ["authorNameInfo[0]","familyName"]
    test = [{"key":"authorNameInfo[0].familyName","reduce_keys":["authorNameInfo",0,"familyName"],"value":"テスト"}]
    result = get_values_by_mapping(keys,data)
    assert result == test

    data = {
        "emailInfo": {"email":"test.taro@test.org"}
    }
    keys = ["emailInfo[0]","email"]
    test = [{"key":"emailInfo.email","reduce_keys":["emailInfo","email"],"value":"test.taro@test.org"}]
    result = get_values_by_mapping(keys,data)
    assert result == test

# def autofill_data(item, values, autofill_data):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_autofill_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_autofill_data():
    item = {
        'authorNameInfo': [{'familyName': '',
                            'firstName': '',
                            'language': 'ja',
                            'nameFormat': '',
                            'nameShowFlg': 'Y'}]
        }

    # value["value"] is not none
    values = [{"key":"authorNameInfo[0].nameFormat","reduce_keys":["authorNameInfo",0,"nameFormat"],"value":"familyNmAndNm"}]
    data = {'condition': {'either_required': ['familyName', 'firstName']},'value': 'familyNmAndNm'}
    test = {"authorNameInfo":
        [{"familyName":"","firstName":"","language":"ja",
          "nameFormat":"","nameShowFlg":"Y"}]}
    autofill_data(item, values, data)
    assert item == test

    # not exist either_required
    values = [{"key":"authorNameInfo[0].nameFormat","reduce_keys":["authorNameInfo",0,"nameFormat"],"value":""}]
    data = {'value': 'familyNmAndNm'}
    autofill_data(item, values, data)
    assert item == test

    # not check
    data = {'condition': {'either_required': ['familyName', 'firstName']},'value': 'familyNmAndNm'}
    autofill_data(item, values, data)
    assert item == test

    # not exist value["value"]
    item = {
        'authorNameInfo': [{'familyName': 'テスト',
                            'firstName': '太郎',
                            'language': 'ja',
                            'nameFormat': '',
                            'nameShowFlg': 'Y'}]
        }
    test = {"authorNameInfo":
        [{"familyName":"テスト","firstName":"太郎","language":"ja",
          "nameFormat":"familyNmAndNm","nameShowFlg":"Y"}]}
    autofill_data(item, values, data)
    assert item == test


# def convert_data_by_mask(item, values, mask):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_convert_data_by_mask -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_convert_data_by_mask():
    item = {
        'pk_id': '1',
        'authorNameInfo': [{'familyName': 'テスト',
                            'firstName': '太郎',
                            'language': 'ja',
                            'nameFormat': 'familyNmAndNm',
                            'nameShowFlg': 'Y'}],
        'authorIdInfo': [{'idType': 'ORCID',
                          'authorId': '1234',
                          'authorIdShowFlg': 'Y'}],
        'emailInfo': [{'email': 'test.taro@test.org'}],
        'is_deleted': ''}
    values = [{"key":"authorNameInfo[0].authorIdShowFlg","reduce_keys":["authorNameInfo",0,"authorIdShowFlg"],"value":"Y"}]
    mask = {'true': 'Y','false': 'N'}

    convert_data_by_mask(item,values,mask)

# def convert_scheme_to_id(item, values, authors_prefix):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_convert_scheme_to_id -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_convert_scheme_to_id():
    item = {
        'pk_id': '1',
        'authorNameInfo': [{'familyName': 'テスト',
                            'firstName': '太郎',
                            'language': 'ja',
                            'nameFormat': 'familyNmAndNm',
                            'nameShowFlg': 'Y'}],
        'authorIdInfo': [{'idType': 'ORCID',
                          'authorId': '1234',
                          'authorIdShowFlg': 'Y'}],
        'emailInfo': [{'email': 'test.taro@test.org'}],
        'is_deleted': ''}
    values = [
        {"key":"authorNameInfo[0].nameFormat","reduce_keys":["authorNameInfo",0,"nameFormat"],"value":""}, # value["value"] is none
        {"key":"authorIdInfo[0].idType","reduce_keys":["authorIdInfo",0,"idType"],"value":"ORCID"} # value["value"] is not none
        ]
    authors_prefix = {"ORCID":"2"}
    test = {
        'pk_id': '1',
        'authorNameInfo': [{'familyName': 'テスト',
                            'firstName': '太郎',
                            'language': 'ja',
                            'nameFormat': 'familyNmAndNm',
                            'nameShowFlg': 'Y'}],
        'authorIdInfo': [{'idType': '2',
                          'authorId': '1234',
                          'authorIdShowFlg': 'Y'}],
        'emailInfo': [{'email': 'test.taro@test.org'}],
        'is_deleted': ''}
    convert_scheme_to_id(item,values,authors_prefix)
    assert item == test


# def set_record_status(file_format, list_existed_author_id, item, errors, warnings):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_set_record_status -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_set_record_status():
    file_format = "tsv"
    existed_authors_id = {"1":True}


    # not is_deleted, existed_authors_id.pk_id
    item = {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'Y'}], 'authorIdInfo': [{'idType': 'ORCID', 'authorId': '1234', 'authorIdShowFlg': 'Y'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': ''}
    errors = []
    warnings = []
    set_record_status(file_format,existed_authors_id,item,errors,warnings)
    assert item["status"] == "update"
    assert errors == []
    assert warnings == []

    # not is_deleted, not existed_authors_id.pk_id
    existed_authors_id = {"1":False}
    item = {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'Y'}], 'authorIdInfo': [{'idType': 'ORCID', 'authorId': '1234', 'authorIdShowFlg': 'Y'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': ''}
    errors = []
    warnings = []
    set_record_status(file_format,existed_authors_id,item,errors,warnings)
    assert item["status"] == "update"
    assert warnings == ["The specified author has been deleted. Update author information with tsv content, but author remains deleted as it is."]
    assert errors == []

    # not is_deleted, existed_authors_id.pk_id is None
    existed_authors_id = {}
    item = {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'Y'}], 'authorIdInfo': [{'idType': 'ORCID', 'authorId': '1234', 'authorIdShowFlg': 'Y'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': ''}
    errors = []
    warnings = []
    set_record_status(file_format,existed_authors_id,item,errors,warnings)
    assert errors == ["Specified Author ID does not exist."]
    assert warnings == []

    # is_deleted, existed_authors_id.pk_id is None
    item = {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'Y'}], 'authorIdInfo': [{'idType': 'ORCID', 'authorId': '1234', 'authorIdShowFlg': 'Y'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': 'D'}
    errors = []
    warnings = []
    set_record_status(file_format,existed_authors_id,item,errors,warnings)
    assert item["status"] == "deleted"
    assert errors == ["Specified Author ID does not exist."]
    assert warnings == []

    existed_authors_id = {"1":True}
    with patch("weko_authors.utils.get_count_item_link",return_value=10):
        item = {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'Y'}], 'authorIdInfo': [{'idType': 'ORCID', 'authorId': '1234', 'authorIdShowFlg': 'Y'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': 'D'}
        errors = []
        warnings = []
        set_record_status(file_format,existed_authors_id,item,errors,warnings)
        assert item["status"] == "deleted"
        assert errors == ["The author is linked to items and cannot be deleted."]
        assert warnings == []

    with patch("weko_authors.utils.get_count_item_link",return_value=0):
        item = {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'Y'}], 'authorIdInfo': [{'idType': 'ORCID', 'authorId': '1234', 'authorIdShowFlg': 'Y'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': 'D'}
        errors = []
        warnings = []
        set_record_status(file_format,existed_authors_id,item,errors,warnings)
        assert item["status"] == "deleted"

# def flatten_authors_mapping(mapping, parent_key=None):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_flatten_authors_mapping -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_flatten_authors_mapping():
    data = WEKO_AUTHORS_FILE_MAPPING

    test_all=[
        {'key': 'pk_id', 'label': {'en': 'Author ID', 'jp': '著者ID'}, 'mask': {}, 'validation': {}, 'autofill': ''},
        {'key': 'weko_id', 'label': {'en': 'WEKO ID', 'jp': 'WEKO ID'}, 'mask': {}, 'validation': {'validator': {'class_name': 'weko_authors.contrib.validation', 'func_name': 'validate_digits_for_wekoid'}}, 'autofill': ''},
        {"key":"authorNameInfo[0].familyName","label":{"en":"Family Name","jp":"姓"},"mask":{},"validation":{},"autofill":""},
        {"key":"authorNameInfo[0].firstName","label":{"en":"Given Name","jp":"名"},"mask":{},"validation":{},"autofill":""},
        {"key":"authorNameInfo[0].language","label":{"en":"Language","jp":"言語"},"mask":{},"validation":{'map': ['ja', 'ja-Kana', 'en', 'fr','it', 'de', 'es', 'zh-cn', 'zh-tw','ru', 'la', 'ms', 'eo', 'ar', 'el', 'ko']},"autofill":""},
        {"key":"authorNameInfo[0].nameFormat","label":{"en":"Name Format","jp":"フォーマット"},"mask":{},"validation":{'map': ['familyNmAndNm']},"autofill":{'condition': {'either_required': ['familyName', 'firstName']},'value': 'familyNmAndNm'}},
        {"key":"authorNameInfo[0].nameShowFlg","label":{"en":"Name Display","jp":"姓名・言語 表示／非表示"},"mask":{'true': 'Y','false': 'N'},"validation":{'map': ['Y', 'N']},"autofill":""},
        {"key":"authorIdInfo[0].idType","label":{"en":"Identifier Scheme","jp":"外部著者ID 識別子"},"mask":{},"validation":{'validator': {'class_name': 'weko_authors.contrib.validation','func_name': 'validate_identifier_scheme'},'required': {'if': ['authorId']}},"autofill":""},
        {"key":"authorIdInfo[0].authorId","label":{"en":"Identifier","jp":"外部著者ID"},"mask":{},"validation":{'required': {'if': ['idType']}},"autofill":""},
        {"key":"authorIdInfo[0].authorIdShowFlg","label":{"en":"Identifier Display","jp":"外部著者ID 表示／非表示"},"mask":{'true': 'Y','false': 'N'},"validation":{'map': ['Y', 'N']},"autofill":""},
        {"key":"emailInfo[0].email","label":{"en":"Mail Address","jp":"メールアドレス"},"mask":{},"validation":{},"autofill":""},
        {"key":"is_deleted","label":{"en":"Delete Flag","jp":"削除フラグ"},"mask":{'true': 'D','false': ''},"validation":{'map': ['D']},"autofill":""},
    ]

    test_keys = ["pk_id",
                 'weko_id',
                 "authorNameInfo[0].familyName",
                 "authorNameInfo[0].firstName",
                 "authorNameInfo[0].language",
                 "authorNameInfo[0].nameFormat",
                 "authorNameInfo[0].nameShowFlg",
                 "authorIdInfo[0].idType",
                 "authorIdInfo[0].authorId",
                 "authorIdInfo[0].authorIdShowFlg",
                 "emailInfo[0].email",
                 "is_deleted"
                 ]
    all,keys = flatten_authors_mapping(data)
    print(all)
    print(keys)
    assert all == test_all
    assert keys == test_keys


# def import_author_to_system(author):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_import_author_to_system -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_import_author_to_system(app, mocker):


    author = {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎'}]}
    status = 'new'
    weko_id = '1234'
    force_change_mode = False
    test = {
        'pk_id': '1',
        'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'fullName': 'テスト 太郎'}],
        'is_deleted': False,
        'authorIdInfo': [],
        'emailInfo': []
    }
    with patch('weko_authors.utils.check_weko_id_is_exists') as mock_check_weko_id, \
         patch('weko_authors.utils.WekoAuthors') as mock_weko_authors, \
         patch('weko_authors.utils.db.session') as mock_session:

        mock_check_weko_id.return_value = False
        import_author_to_system(author, status, weko_id, force_change_mode)
        mock_check_weko_id.assert_called_once_with(weko_id, '1')
        mock_weko_authors.create.assert_called_once()
        actual_author = mock_weko_authors.create.call_args[0][0]
        print(actual_author)

        assert actual_author == {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'fullName': 'テスト 太郎'}], 'is_deleted': False, 'authorIdInfo': [{'idType': '1', 'authorId': '1234', 'authorIdShowFlg': 'true'}], 'emailInfo': []}
        mock_session.commit.assert_called_once()

    author = {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎'}]}
    status = 'update'
    weko_id = '1234'
    force_change_mode = False
    test = {
        'pk_id': '1',
        'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'fullName': 'テスト 太郎'}],
        'is_deleted': False,
        'authorIdInfo': [
            {
                "idType": "1",
                "authorId": "1234",
                "authorIdShowFlg": "true"
            }
        ],
        'emailInfo': []
    }
    with patch('weko_authors.utils.check_weko_id_is_exists') as mock_check_weko_id, \
         patch('weko_authors.utils.WekoAuthors') as mock_weko_authors, \
         patch('weko_authors.utils.db.session') as mock_session:

        mock_check_weko_id.return_value = False
        import_author_to_system(author, status, weko_id, force_change_mode)
        mock_check_weko_id.assert_called_once_with(weko_id, '1')
        mock_weko_authors.update.assert_called_once()
        update_args = mock_weko_authors.update.call_args
        actual_author = update_args[0][1]

        assert actual_author == test
        mock_session.commit.assert_called_once()

    author = {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎'}]}
    status = 'deleted'
    weko_id = '1234'
    force_change_mode = False
    test = {
        'pk_id': '1',
        'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'fullName': 'テスト 太郎'}],
        'is_deleted': False,
        'authorIdInfo': [
            {
                "idType": "1",
                "authorId": "1234",
                "authorIdShowFlg": "true"
            }
        ],
        'emailInfo': []
    }
    with patch('weko_authors.utils.check_weko_id_is_exists') as mock_check_weko_id, \
         patch('weko_authors.utils.WekoAuthors') as mock_weko_authors, \
         patch('weko_authors.utils.db.session') as mock_session, \
         patch('weko_authors.utils.get_count_item_link') as mock_get_count_item_link:

        mock_check_weko_id.return_value = False
        mock_get_count_item_link.return_value = 0
        import_author_to_system(author, status, weko_id, force_change_mode)
        mock_check_weko_id.assert_called_once_with(weko_id, '1')
        mock_weko_authors.update.assert_called_once()
        update_args = mock_weko_authors.update.call_args
        actual_author = update_args[0][1]

        assert actual_author == test
        mock_session.commit.assert_called_once()

    author =  {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎'}]}
    status = 'new'
    weko_id = '1234'
    force_change_mode = False
    with patch('weko_authors.utils.check_weko_id_is_exists') as mock_check_weko_id:
        with pytest.raises(Exception) as ex:
            mock_check_weko_id.return_value = True
            import_author_to_system(author, status, weko_id, force_change_mode)
            assert ex.value.args[0]['error_id'] == "WekoID is duplicated"
            assert str(ex.value) == {'error_id': "WekoID is duplicated"}

    author =  {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎'}]}
    status = 'deleted'
    weko_id = '1234'
    force_change_mode = False
    with patch('weko_authors.utils.check_weko_id_is_exists') as mock_check_weko_id,\
        patch('weko_authors.utils.get_count_item_link') as mock_get_count_item_link:
        with pytest.raises(Exception) as ex:
            mock_check_weko_id.return_value = False
            mock_get_count_item_link.return_value = 1
            import_author_to_system(author, status, weko_id, force_change_mode)
            assert ex.value.args[0]['error_id'] == "delete_author_link"
            assert str(ex.value) == {'error_id': "delete_author_link"}

    author =  {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎'}]}
    status = 'update'
    weko_id = '1234'
    force_change_mode = False
    with patch('weko_authors.utils.check_weko_id_is_exists') as mock_check_weko_id:
        with pytest.raises(Exception) as ex:
            mock_check_weko_id.return_value = True
            import_author_to_system(author, status, weko_id, force_change_mode)
            assert ex.value.args[0]['error_id'] == "WekoID is duplicated"
            assert str(ex.value) == {'error_id': "WekoID is duplicated"}

# def get_count_item_link(pk_id):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_get_count_item_link -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_count_item_link(app,mocker):
    class MockClient:
        def __init__(self):
            self.return_data=""
        def search(self,index,body):
            return self.return_data

    record_indexer = RecordIndexer()
    record_indexer.client = MockClient()
    record_indexer.client.return_data=None
    mocker.patch("weko_authors.utils.RecordIndexer",return_value=record_indexer)

    result = get_count_item_link(1)
    assert result == 0

    record_indexer.client.return_data={"hits":{"total":10}}
    result = get_count_item_link(1)
    assert result == 10


# def count_authors():
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_count_authors -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_count_authors(app2, esindex):
    import json
    index = app2.config["WEKO_AUTHORS_ES_INDEX_NAME"]
    doc_type = "author-v1.0.0"

    def register(i):
        with open(f"tests/data/test_authors/author{i:02}.json","r") as f:
            esindex.index(index=index, doc_type=doc_type, id=f"{i}", body=json.load(f), refresh="true")

    def delete(i):
        esindex.delete(index=index, doc_type=doc_type, id=f"{i}", refresh="true")

    # 3 Register 1 author data
    register(1)
    assert count_authors()['count'] == 1
    delete(1)

    # 4 Register gather_flg = 1
    register(2)
    assert count_authors()['count'] == 0
    delete(2)

    # 5 Register is_deleted = "true"
    register(3)
    assert count_authors()['count'] == 0
    delete(3)

    # 6 Not register author data
    assert count_authors()['count'] == 0

from weko_authors.utils import validate_weko_id, check_weko_id_is_exists, check_period_date, delete_export_url,\
    handle_exception, export_prefix,check_file_name, clean_deep, update_data_for_weko_link
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::TestValidateWekoId -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestValidateWekoId:
    # 正常系
    def test_validate_weko_id_valid(self, app):
        with patch("weko_authors.utils.check_weko_id_is_exists", return_value=False):
            result = validate_weko_id("12345")
            assert result == (True, None)

    # 異常系
    def test_validate_weko_id_not_half_digit(self, app):
        result = validate_weko_id("abcde")
        assert result == (False, "not half digit")

    # 異常系
    def test_validate_weko_id_already_exists(self, app):
        with patch("weko_authors.utils.check_weko_id_is_exists", return_value=True):
            result = validate_weko_id("12345")
            assert result == (False, "already exists")

    # 異常系
    def test_validate_weko_id_exception(self, app):
        with patch("weko_authors.utils.check_weko_id_is_exists", side_effect=Exception("Test Exception")):
            with pytest.raises(Exception, match="Test Exception"):
                validate_weko_id("12345")

# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::TestCheckWekoIdIsExists -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestCheckWekoIdIsExists:
    # 正常系: weko_idが存在しない場合
    def test_check_weko_id_is_exists_not_exist(self, app):
        with patch('weko_authors.utils.RecordIndexer') as MockIndexer:
            mock_indexer = MockIndexer.return_value
            mock_indexer.client.search.return_value = {'hits': {'hits': []}}
            assert check_weko_id_is_exists("12345") == False

    # 正常系: weko_idが存在するが、pk_idが一致する場合
    def test_check_weko_id_is_exists_exist_same_pk_id(self, app):
        with patch('weko_authors.utils.RecordIndexer') as MockIndexer:
            mock_indexer = MockIndexer.return_value
            mock_indexer.client.search.return_value = {
                'hits': {
                    'hits': [
                        {
                            '_source': {
                                'pk_id': '1',
                                'authorIdInfo': [{'idType': '1', 'authorId': '12345'}]
                            }
                        }
                    ]
                }
            }
            assert check_weko_id_is_exists("12345", pk_id="1") == False

    # 異常系: weko_idが存在する場合
    def test_check_weko_id_is_exists_exist(self, app):
        with patch('weko_authors.utils.RecordIndexer') as MockIndexer:
            mock_indexer = MockIndexer.return_value
            mock_indexer.client.search.return_value = {
                'hits': {
                    'hits': [
                        {
                            '_source': {
                                'pk_id': '2',
                                'authorIdInfo': [{'idType': '1', 'authorId': '12345'}]
                            }
                        }
                    ]
                }
            }
            assert check_weko_id_is_exists("12345") == True

    # 異常系: Elasticsearchクライアントが例外をスローする場合
    def test_check_weko_id_is_exists_exception(self, app):
        with patch('weko_authors.utils.RecordIndexer') as MockIndexer:
            mock_indexer = MockIndexer.return_value
            mock_indexer.client.search.side_effect = Exception("Elasticsearch error")
            with pytest.raises(Exception):
                check_weko_id_is_exists("12345")

# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::TestCheckPeriodDate -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestCheckPeriodDate:
# 正常系: affiliationInfoが存在し、期間が正しい場合
    def test_check_period_date_valid(self, app):
        data = {
            "affiliationInfo": [
                {
                    "affiliationPeriodInfo": [
                        {"periodStart": "2020-01-01", "periodEnd": "2021-01-01"}
                    ]
                }
            ]
        }
        assert check_period_date(data) == (True, None)

    # 異常系: periodStartが日付形式でない場合
    def test_check_period_date_invalid_start_date(self, app):
        data = {
            "affiliationInfo": [
                {
                    "affiliationPeriodInfo": [
                        {"periodStart": "2020-13-01"}
                    ]
                }
            ]
        }
        assert check_period_date(data) == (False, "not date format")

    # 異常系: periodEndが日付形式でない場合
    def test_check_period_date_invalid_end_date(self, app):
        data = {
            "affiliationInfo": [
                {
                    "affiliationPeriodInfo": [
                        {"periodEnd": "2020-13-01"}
                    ]
                }
            ]
        }
        assert check_period_date(data) == (False, "not date format")

    # 異常系: periodStartがperiodEndより後の場合
    def test_check_period_date_start_after_end(self, app):
        data = {
            "affiliationInfo": [
                {
                    "affiliationPeriodInfo": [
                        {"periodStart": "2021-01-01", "periodEnd": "2020-01-01"}
                    ]
                }
            ]
        }
        assert check_period_date(data) == (False, "start is after end")

# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::TestDeleteExportUrl -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestDeleteExportUrl:
    # 正常系: キャッシュキーが存在する場合
    def test_delete_export_url_key_exists(self, app2):
        with patch('weko_authors.utils.current_cache') as mock_cache:
            delete_export_url()
            mock_cache.delete.assert_called_once_with(current_app.config["WEKO_AUTHORS_EXPORT_CACHE_URL_KEY"])

    # 正常系: キャッシュキーが存在しない場合
    def test_delete_export_url_key_not_exists(self, app2):
        with patch('weko_authors.utils.current_cache') as mock_cache:
            mock_cache.delete.return_value = None  # Simulate key not existing
            delete_export_url()
            mock_cache.delete.assert_called_once_with(current_app.config["WEKO_AUTHORS_EXPORT_CACHE_URL_KEY"])

# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::TestHandleException -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestHandleException:
# 正常系: リトライ回数が残っている場合
    def test_handle_exception_retry(self, app2):
        with patch('weko_authors.utils.current_app') as mock_app, patch('weko_authors.utils.sleep') as mock_sleep:
            mock_app.logger = MagicMock()
            handle_exception(Exception("Test error"), attempt=0, retrys=3, interval=1, stop_point=0)
            mock_sleep.assert_called_once_with(1)

    # 異常系: リトライ回数が残っていない場合
    def test_handle_exception_no_retry(self, app2):
        with patch('weko_authors.utils.current_app') as mock_app:
            mock_app.logger = MagicMock()
            with pytest.raises(Exception):
                handle_exception(Exception("Test error"), attempt=2, retrys=3, interval=1, stop_point=0)

    # 異常系: リトライ回数が残っていない場合、かつstop_pointが指定されている場合
    def test_handle_exception_no_retry_with_stop_point(self, app2):
        with patch('weko_authors.utils.current_app') as mock_app, patch('weko_authors.utils.update_cache_data') as mock_update_cache:
            mock_app.logger = MagicMock()
            with pytest.raises(Exception):
                handle_exception(Exception("Test error"), attempt=2, retrys=3, interval=1, stop_point=5)
            mock_update_cache.assert_called_once_with(
                mock_app.config["WEKO_AUTHORS_EXPORT_CACHE_STOP_POINT_KEY"],
                5,
                mock_app.config["WEKO_AUTHORS_CACHE_TTL"]
            )

# @.tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::TestExportAuthors -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestExportAuthors:

    @pytest.fixture
    def setup_app_config(self, app, db):
        """テスト用のapp configを設定するフィクスチャ"""
        app_config = {
            "WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY": 3,
            "WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL": 1,
            "WEKO_AUTHORS_EXPORT_BATCH_SIZE": 1000,
            "WEKO_AUTHORS_EXPORT_CACHE_STOP_POINT_KEY": "stop_point_key",
            "WEKO_AUTHORS_FILE_MAPPING": {"key": "value"},
            "WEKO_AUTHORS_FILE_MAPPING_FOR_AFFILIATION": {"aff_key": "aff_value"},
            "WEKO_AUTHORS_EXPORT_CACHE_TEMP_FILE_PATH_KEY": "temp_file_path_key",
            "WEKO_AUTHORS_EXPORT_TARGET_CACHE_KEY": "target_cache_key"
        }
        return app_config

    @pytest.fixture
    def mock_dependencies(self, setup_app_config):
        """依存関係をモックするフィクスチャ"""
        with patch('builtins.open') as mock_open, \
            patch('weko_authors.utils.current_app') as mock_app, \
            patch('weko_authors.utils.current_cache') as mock_cache, \
            patch('weko_authors.utils.WekoAuthors') as mock_weko, \
            patch('weko_authors.utils.db') as mock_db, \
            patch('weko_authors.utils.os') as mock_os, \
            patch('invenio_files_rest.models.FileInstance') as mock_file, \
            patch('invenio_files_rest.models.Location') as mock_location, \
            patch('weko_authors.utils.get_export_url') as mock_get_url, \
            patch('weko_authors.utils.write_to_tempfile') as mock_write, \
            patch('weko_authors.utils.handle_exception') as mock_handle, \
            patch('weko_authors.utils.io.BufferedReader') as mock_reader, \
            patch('weko_authors.utils.traceback') as mock_traceback, \
            patch('weko_authors.utils.stdout') as mock_stdout:

            # モックオブジェクトの設定
            mock_app.config = setup_app_config
            mock_app.logger = MagicMock()

            mock_cache.get.side_effect = lambda key: None if key == "stop_point_key" else "/tmp/test_file.csv"
            mock_cache.delete = MagicMock()
            mock_cache.set = MagicMock()

            mock_weko.get_records_count.return_value = 2000
            mock_weko.mapping_max_item.return_value = ({"key": "value"}, {"aff_key": "aff_value"})
            mock_weko.get_identifier_scheme_info.return_value = {"scheme1": "info1"}
            mock_weko.get_affiliation_identifier_scheme_info.return_value = {"aff_scheme1": "aff_info1"}
            mock_weko.get_by_range.return_value = [{"id": 1}, {"id": 2}]
            mock_weko.prepare_export_data.return_value = (["header"], ["label_en"], ["label_jp"], [["data1"], ["data2"]])

            mock_get_url.return_value = None

            mock_file_instance = MagicMock()
            mock_file_instance.uri = "file://test_uri"
            mock_file.create.return_value = mock_file_instance
            mock_file.get_by_uri = MagicMock(return_value=mock_file_instance)

            mock_default_location = MagicMock()
            mock_default_location.uri = "default_uri"
            mock_location.get_default.return_value = mock_default_location

            mock_reader_instance = MagicMock()
            mock_reader.return_value = mock_reader_instance

            mock_db.session.commit = MagicMock()
            mock_db.session.rollback = MagicMock()

            mock_os.remove = MagicMock()

            yield {
                'app': mock_app,
                'cache': mock_cache,
                'weko': mock_weko,
                'db': mock_db,
                'os': mock_os,
                'file': mock_file,
                'location': mock_location,
                'get_url': mock_get_url,
                'write': mock_write,
                'handle': mock_handle,
                'reader': mock_reader,
                'reader_instance': mock_reader_instance,
                'file_instance': mock_file_instance,
                'traceback': mock_traceback,
                'stdout': mock_stdout
            }


    def test_normal_case(self, mock_dependencies):
        """
        テストケース1: 正常系 - 著者データがある場合
        条件: 著者データが存在し、すべての処理が正常に完了する
        入力: なし（関数内部でデータを取得）
        期待結果:
        - 非nullのfile_uriが返される
        - 一時ファイルが作成され、その後削除される
        - キャッシュに"author_db"が設定される
        - 著者データが正しくエクスポートされる
        """


        result = export_authors()

        # 検証
        assert result == "file://test_uri"
        mock_dependencies['cache'].delete.assert_called_once_with("stop_point_key")
        mock_dependencies['write'].assert_called()
        mock_dependencies['os'].remove.assert_called_once_with("/tmp/test_file.csv")
        mock_dependencies['db'].session.commit.assert_called_once()
        mock_dependencies['cache'].set.assert_called_once_with(
            "target_cache_key", "author_db", timeout=0
        )

# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::TestExportAuthors::test_with_stop_point -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_with_stop_point(self, mock_dependencies):
        """
        テストケース2: 正常系 - stop_pointが設定されている場合
        条件: キャッシュにstop_pointが設定されている
        入力: stop_point = 500（キャッシュ内）
        期待結果:
        - start_pointが500から開始される
        - 処理が正常に完了し、非nullのfile_uriが返される
        - キャッシュからstop_pointが削除される
        """
        # stop_pointを設定
        mock_dependencies['cache'].get.side_effect = lambda key: 500 if key == "stop_point_key" else "/tmp/test_file.csv"

        result = export_authors()

        # 検証
        assert result == "file://test_uri"
        mock_dependencies['cache'].delete.assert_called_once_with("stop_point_key")
        # 500から始まって1500で終わることを確認
        mock_dependencies['app'].logger.info.assert_any_call("Export authors start_point：500")
        mock_dependencies['weko'].get_by_range.assert_called_with(1500, 1000, False, False)


    def test_with_existing_cache_url(self, mock_dependencies):
        """
        テストケース3: 正常系 - キャッシュURLが存在する場合
        条件: get_export_url()が既存のキャッシュURLを返す
        入力: cache_url = {'file_uri': 'existing_uri'}
        期待結果:
        - 既存のファイルが更新される
        - 同じfile_uriが返される
        """
        # 既存のキャッシュURLを設定
        mock_dependencies['get_url'].return_value = {'file_uri': 'existing_uri'}



        result = export_authors()

        # 検証
        assert result == "file://test_uri"
        mock_dependencies['file'].get_by_uri.assert_called_once_with('existing_uri')
        mock_dependencies['file_instance'].set_contents.assert_called_once_with(mock_dependencies['reader_instance'])
        mock_dependencies['file'].create.assert_not_called()

# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::TestExportAuthors::test_sqlalchemy_error_on_mapping_with_retry_success -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_sqlalchemy_error_on_mapping_with_retry_success(self, mock_dependencies):
        """
        テストケース4: 異常系 - マッピング取得時のSQLAlchemyエラー（リトライ成功）
        条件: 最初のSQLAlchemyエラーが発生し、リトライが成功する
        入力: 1回目のマッピング取得時にSQLAlchemyErrorを発生させ、2回目は成功
        期待結果:
        - リトライ後に処理が続行され、正常に完了する
        - 非nullのfile_uriが返される
        """
        # 1回目のマッピング取得でエラー、2回目は成功するように設定
        mock_dependencies['weko'].get_records_count.side_effect = [SQLAlchemyError("DB Error"), 2000]



        result = export_authors()

        # 検証
        assert result == "file://test_uri"
        mock_dependencies['handle'].assert_called_once()
        mock_dependencies['weko'].get_records_count.assert_called_with(False, False)

# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::TestExportAuthors::test_redis_error_on_mapping_with_retry_success -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_redis_error_on_mapping_with_retry_success(self, mock_dependencies):
        """
        テストケース5: 異常系 - マッピング取得時のRedisエラー（リトライ成功）
        条件: 最初のRedisエラーが発生し、リトライが成功する
        入力: 1回目のマッピング取得時にRedisErrorを発生させ、2回目は成功
        期待結果:
        - リトライ後に処理が続行され、正常に完了する
        - 非nullのfile_uriが返される
        """
        # 1回目のマッピング取得でRedisエラー、2回目は成功するように設定
        mock_dependencies['weko'].mapping_max_item.side_effect = [RedisError("Redis Error"), ({"key": "value"}, {"aff_key": "aff_value"})]



        result = export_authors()

        # 検証
        assert result == "file://test_uri"
        mock_dependencies['handle'].assert_called_once()


    def test_timeout_error_on_mapping_with_retry_success(self, mock_dependencies):
        """
        テストケース6: 異常系 - マッピング取得時のTimeoutエラー（リトライ成功）
        条件: 最初のTimeoutエラーが発生し、リトライが成功する
        入力: 1回目のマッピング取得時にTimeoutErrorを発生させ、2回目は成功
        期待結果:
        - リトライ後に処理が続行され、正常に完了する
        - 非nullのfile_uriが返される
        """
        # 1回目のマッピング取得でTimeoutエラー、2回目は成功するように設定
        mock_dependencies['weko'].get_identifier_scheme_info.side_effect = [TimeoutError("Timeout"), {"scheme1": "info1"}]



        result = export_authors()

        # 検証
        assert result == "file://test_uri"
        mock_dependencies['handle'].assert_called_once()


    def test_sqlalchemy_error_on_author_info_with_retry_success(self, mock_dependencies):
        """
        テストケース7: 異常系 - 著者情報取得時のSQLAlchemyエラー（リトライ成功）
        条件: 著者情報取得時にSQLAlchemyErrorが発生し、リトライが成功する
        入力: 1回目の著者情報取得時にSQLAlchemyErrorを発生させ、2回目は成功
        期待結果:
        - リトライ後に処理が続行され、正常に完了する
        - 非nullのfile_uriが返される
        """
        # 著者情報取得でSQLAlchemyエラー、2回目は成功するように設定
        mock_dependencies['weko'].get_by_range.side_effect = [SQLAlchemyError("DB Error"), [{"id": 1}, {"id": 2}]]



        result = export_authors()

        # 検証
        mock_dependencies['handle'].assert_called_once_with(
            mock_dependencies['handle'].call_args[0][0],
            0,
            3,
            1,
            stop_point=0
        )


    def test_redis_error_on_author_info_with_retry_success(self, mock_dependencies):
        """
        テストケース8: 異常系 - 著者情報取得時のRedisエラー（リトライ成功）
        条件: 著者情報取得時にRedisErrorが発生し、リトライが成功する
        入力: 1回目の著者情報取得時にRedisErrorを発生させ、2回目は成功
        期待結果:
        - リトライ後に処理が続行され、正常に完了する
        - 非nullのfile_uriが返される
        """
        # 著者情報取得でRedisエラー、2回目は成功するように設定
        mock_dependencies['weko'].prepare_export_data.side_effect = [
            RedisError("Redis Error"),
            (["header"], ["label_en"], ["label_jp"], [["data1"], ["data2"]])
        ]



        result = export_authors()

        # 検証
        mock_dependencies['handle'].assert_called_once_with(
            mock_dependencies['handle'].call_args[0][0],
            0,
            3,
            1,
            stop_point=0
        )

    # .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::TestExportAuthors::test_timeout_error_on_author_info_with_retry_success -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_timeout_error_on_author_info_with_retry_success(self, mock_dependencies):
        """
        テストケース9: 異常系 - 著者情報取得時のTimeoutエラー（リトライ成功）
        条件: 著者情報取得時にTimeoutErrorが発生し、リトライが成功する
        入力: 1回目の著者情報取得時にTimeoutErrorを発生させ、2回目は成功
        期待結果:
        - リトライ後に処理が続行され、正常に完了する
        """
        # 1回目のマッピング取得でRedisエラー、2回目は成功するように設定
        mock_dependencies['weko'].prepare_export_data.side_effect = [TimeoutError("TimeoutError"), ({"key": "value"}, {"aff_key": "aff_value"})]

        result = export_authors()

        # 検証
        mock_dependencies['handle'].assert_called_once()

# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::TestExportPrefix -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestExportPrefix:
    def test_export_prefix_id_prefix_success(self, app):
        """正常系: id_prefixの正常エクスポート"""
        # モックの準備
        with patch('weko_authors.utils.WekoAuthors') as mock_weko_authors, \
            patch('weko_authors.utils.get_export_url') as mock_get_export_url, \
            patch('invenio_files_rest.models.FileInstance') as mock_file_instance, \
            patch('invenio_files_rest.models.Location') as mock_location, \
            patch('weko_authors.utils.current_cache') as mock_current_cache, \
            patch('weko_authors.utils.db') as mock_db:

            # モックの設定
            mock_weko_authors.get_id_prefix_all.return_value = ['test_prefix']
            mock_weko_authors.prepare_export_prefix.return_value = [['scheme1', 'name1', 'url1', 'false']]
            mock_get_export_url.return_value = None

            mock_file = Mock()
            mock_file.uri = 'test_uri'
            mock_file_instance.create.return_value = mock_file

            mock_location_instance = Mock()
            mock_location_instance.uri = 'default_uri'
            mock_location.get_default.return_value = mock_location_instance

            # テスト対象の関数を実行
            app.config['WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY'] = 3
            app.config['WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL'] = 0
            app.config['WEKO_ADMIN_OUTPUT_FORMAT'] = 'tsv'
            app.config['WEKO_AUTHORS_EXPORT_TARGET_CACHE_KEY'] = 'test_cache_key'

            result = export_prefix('id_prefix')

            # 検証
            assert result == 'test_uri'
            mock_weko_authors.get_id_prefix_all.assert_called_once()
            mock_weko_authors.prepare_export_prefix.assert_called_once_with('id_prefix', ['test_prefix'])
            mock_file.set_contents.assert_called_once()
            mock_db.session.commit.assert_called_once()
            mock_current_cache.set.assert_called_once_with('test_cache_key', 'id_prefix', timeout=0)

    def test_export_prefix_affiliation_id_success(self, app):
        """正常系: affiliation_idの正常エクスポート"""
        # モックの準備
        with patch('weko_authors.utils.WekoAuthors') as mock_weko_authors, \
            patch('weko_authors.utils.get_export_url') as mock_get_export_url, \
            patch('invenio_files_rest.models.FileInstance') as mock_file_instance, \
            patch('invenio_files_rest.models.Location') as mock_location, \
            patch('weko_authors.utils.current_cache') as mock_current_cache, \
            patch('weko_authors.utils.db') as mock_db:

            # モックの設定
            mock_weko_authors.get_affiliation_id_all.return_value = ['test_affiliation']
            mock_weko_authors.prepare_export_prefix.return_value = [['scheme1', 'name1', 'url1', 'false']]
            mock_get_export_url.return_value = None

            mock_file = Mock()
            mock_file.uri = 'test_uri'
            mock_file_instance.create.return_value = mock_file

            mock_location_instance = Mock()
            mock_location_instance.uri = 'default_uri'
            mock_location.get_default.return_value = mock_location_instance

            # テスト対象の関数を実行
            app.config['WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY'] = 3
            app.config['WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL'] = 0
            app.config['WEKO_ADMIN_OUTPUT_FORMAT'] = 'tsv'
            app.config['WEKO_AUTHORS_EXPORT_TARGET_CACHE_KEY'] = 'test_cache_key'

            result = export_prefix('affiliation_id')

            # 検証
            assert result == 'test_uri'
            mock_weko_authors.get_affiliation_id_all.assert_called_once()
            mock_weko_authors.prepare_export_prefix.assert_called_once_with('affiliation_id', ['test_affiliation'])
            mock_file.set_contents.assert_called_once()
            mock_db.session.commit.assert_called_once()
            mock_current_cache.set.assert_called_once_with('test_cache_key', 'affiliation_id', timeout=0)

    def test_export_prefix_csv_format(self, app):
        """正常系: CSVフォーマットでの出力"""
        # モックの準備
        with patch('weko_authors.utils.WekoAuthors') as mock_weko_authors, \
            patch('weko_authors.utils.get_export_url') as mock_get_export_url, \
            patch('invenio_files_rest.models.FileInstance') as mock_file_instance, \
            patch('invenio_files_rest.models.Location') as mock_location, \
            patch('weko_authors.utils.current_cache') as mock_current_cache, \
            patch('weko_authors.utils.db') as mock_db:

            # モックの設定
            mock_weko_authors.get_id_prefix_all.return_value = ['test_prefix']
            mock_weko_authors.prepare_export_prefix.return_value = [['scheme1', 'name1', 'url1', 'false']]
            mock_get_export_url.return_value = None

            mock_file = Mock()
            mock_file.uri = 'test_uri'
            mock_file_instance.create.return_value = mock_file

            # テスト対象の関数を実行
            app.config['WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY'] = 3
            app.config['WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL'] = 0
            app.config['WEKO_ADMIN_OUTPUT_FORMAT'] = 'csv'

            result = export_prefix('id_prefix')

            # 検証
            assert result == 'test_uri'
            # CSVフォーマットで書き込まれたことを検証（実装依存のため詳細な検証は省略）

    def test_export_prefix_tsv_format(self, app):
        """正常系: TSVフォーマットでの出力（デフォルト）"""
        # モックの準備
        with patch('weko_authors.utils.WekoAuthors') as mock_weko_authors, \
            patch('weko_authors.utils.get_export_url') as mock_get_export_url, \
            patch('invenio_files_rest.models.FileInstance') as mock_file_instance, \
            patch('invenio_files_rest.models.Location') as mock_location, \
            patch('weko_authors.utils.current_cache') as mock_current_cache, \
            patch('weko_authors.utils.db') as mock_db:

            # モックの設定
            mock_weko_authors.get_id_prefix_all.return_value = ['test_prefix']
            mock_weko_authors.prepare_export_prefix.return_value = [['scheme1', 'name1', 'url1', 'false']]
            mock_get_export_url.return_value = None

            mock_file = Mock()
            mock_file.uri = 'test_uri'
            mock_file_instance.create.return_value = mock_file

            # テスト対象の関数を実行
            app.config['WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY'] = 3
            app.config['WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL'] = 0
            app.config['WEKO_ADMIN_OUTPUT_FORMAT'] = 'tsv'

            result = export_prefix('id_prefix')

            # 検証
            assert result == 'test_uri'
            # TSVフォーマットで書き込まれたことを検証（実装依存のため詳細な検証は省略）

    def test_export_prefix_with_cache_url(self, app):
        """正常系: キャッシュURLが存在する場合"""
        # モックの準備
        with patch('weko_authors.utils.WekoAuthors') as mock_weko_authors, \
            patch('weko_authors.utils.get_export_url') as mock_get_export_url, \
            patch('invenio_files_rest.models.FileInstance') as mock_file_instance, \
            patch('weko_authors.utils.current_cache') as mock_current_cache, \
            patch('weko_authors.utils.db') as mock_db:

            # モックの設定
            mock_weko_authors.get_id_prefix_all.return_value = ['test_prefix']
            mock_weko_authors.prepare_export_prefix.return_value = [['scheme1', 'name1', 'url1', 'false']]
            mock_get_export_url.return_value = {'file_uri': 'cached_uri'}

            mock_file = Mock()
            mock_file.uri = 'cached_uri'
            mock_file_instance.get_by_uri.return_value = mock_file

            # テスト対象の関数を実行
            app.config['WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY'] = 3
            app.config['WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL'] = 0
            app.config['WEKO_ADMIN_OUTPUT_FORMAT'] = 'tsv'
            app.config['WEKO_AUTHORS_EXPORT_TARGET_CACHE_KEY'] = 'test_cache_key'

            result = export_prefix('id_prefix')

            # 検証
            assert result == 'cached_uri'
            mock_file_instance.get_by_uri.assert_called_once_with('cached_uri')
            assert mock_file.writable == True
            mock_file.set_contents.assert_called_once()
            mock_db.session.commit.assert_called_once()

    def test_export_prefix_without_cache_url(self, app):
        """正常系: キャッシュURLが存在しない場合"""
        # モックの準備
        with patch('weko_authors.utils.WekoAuthors') as mock_weko_authors, \
            patch('weko_authors.utils.get_export_url') as mock_get_export_url, \
            patch('invenio_files_rest.models.FileInstance') as mock_file_instance, \
            patch('invenio_files_rest.models.Location') as mock_location, \
            patch('weko_authors.utils.current_cache') as mock_current_cache, \
            patch('weko_authors.utils.db') as mock_db:

            # モックの設定
            mock_weko_authors.get_id_prefix_all.return_value = ['test_prefix']
            mock_weko_authors.prepare_export_prefix.return_value = [['scheme1', 'name1', 'url1', 'false']]
            mock_get_export_url.return_value = None

            mock_file = Mock()
            mock_file.uri = 'new_uri'
            mock_file_instance.create.return_value = mock_file

            mock_location_instance = Mock()
            mock_location_instance.uri = 'default_uri'
            mock_location.get_default.return_value = mock_location_instance

            # テスト対象の関数を実行
            app.config['WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY'] = 3
            app.config['WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL'] = 0

            result = export_prefix('id_prefix')

            # 検証
            assert result == 'new_uri'
            mock_file_instance.create.assert_called_once()
            mock_location.get_default.assert_called_once()

    def test_export_prefix_sqlalchemy_error_retry_success(self, app):
        """異常系: SQLAlchemyエラー発生（リトライ成功）"""
        # モックの準備
        with patch('weko_authors.utils.WekoAuthors') as mock_weko_authors, \
            patch('weko_authors.utils.get_export_url') as mock_get_export_url, \
            patch('invenio_files_rest.models.FileInstance') as mock_file_instance, \
            patch('invenio_files_rest.models.Location') as mock_location, \
            patch('weko_authors.utils.current_cache') as mock_current_cache, \
            patch('weko_authors.utils.db') as mock_db, \
            patch('weko_authors.utils.handle_exception') as mock_handle_exception:

            # 1回目はエラー、2回目は成功するように設定
            mock_weko_authors.get_id_prefix_all.side_effect = [SQLAlchemyError("DB Error"), ['test_prefix']]
            mock_weko_authors.prepare_export_prefix.return_value = [['scheme1', 'name1', 'url1', 'false']]
            mock_get_export_url.return_value = None

            mock_file = Mock()
            mock_file.uri = 'test_uri'
            mock_file_instance.create.return_value = mock_file

            mock_location_instance = Mock()
            mock_location_instance.uri = 'default_uri'
            mock_location.get_default.return_value = mock_location_instance

            # テスト対象の関数を実行
            app.config['WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY'] = 3
            app.config['WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL'] = 0

            result = export_prefix('id_prefix')

            # 検証
            assert result == 'test_uri'
            assert mock_weko_authors.get_id_prefix_all.call_count == 2
            mock_handle_exception.assert_called_once()

    def test_export_prefix_sqlalchemy_error_all_fails(self, app):
        """異常系: SQLAlchemyエラー発生（全リトライ失敗）"""
        # モックの準備
        with patch('weko_authors.utils.WekoAuthors') as mock_weko_authors, \
            patch('weko_authors.utils.handle_exception') as mock_handle_exception:

            # 全てのリトライでエラーを発生させる
            mock_weko_authors.get_id_prefix_all.side_effect = SQLAlchemyError("DB Error")

            # テスト対象の関数を実行
            app.config['WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY'] = 3
            app.config['WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL'] = 0

            result = export_prefix('id_prefix')

            # 検証
            assert result is None
            assert mock_weko_authors.get_id_prefix_all.call_count == 3
            assert mock_handle_exception.call_count == 3

    def test_export_prefix_redis_error_retry_success(self, app):
        """異常系: RedisErrorエラー発生（リトライ成功）"""
        # モックの準備
        with patch('weko_authors.utils.WekoAuthors') as mock_weko_authors, \
            patch('weko_authors.utils.get_export_url') as mock_get_export_url, \
            patch('invenio_files_rest.models.FileInstance') as mock_file_instance, \
            patch('invenio_files_rest.models.Location') as mock_location, \
            patch('weko_authors.utils.current_cache') as mock_current_cache, \
            patch('weko_authors.utils.db') as mock_db, \
            patch('weko_authors.utils.handle_exception') as mock_handle_exception:

            # モックの設定
            mock_weko_authors.get_id_prefix_all.return_value = ['test_prefix']
            mock_weko_authors.prepare_export_prefix.return_value = [['scheme1', 'name1', 'url1', 'false']]
            mock_get_export_url.return_value = None

            mock_file = Mock()
            mock_file.uri = 'test_uri'
            mock_file_instance.create.return_value = mock_file

            mock_location_instance = Mock()
            mock_location_instance.uri = 'default_uri'
            mock_location.get_default.return_value = mock_location_instance

            # 1回目はエラー、2回目は成功するように設定
            mock_current_cache.set.side_effect = [RedisError("Redis Error"), None]

            # テスト対象の関数を実行
            app.config['WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY'] = 3
            app.config['WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL'] = 0
            app.config['WEKO_AUTHORS_EXPORT_TARGET_CACHE_KEY'] = 'test_cache_key'

            result = export_prefix('id_prefix')

            # 検証
            assert result == 'test_uri'
            mock_handle_exception.assert_called_once()
            assert mock_current_cache.set.call_count == 2

    def test_export_prefix_redis_error_all_fails(self, app):
        """異常系: RedisErrorエラー発生（全リトライ失敗）"""
        # モックの準備
        with patch('weko_authors.utils.WekoAuthors') as mock_weko_authors, \
            patch('weko_authors.utils.get_export_url') as mock_get_export_url, \
            patch('invenio_files_rest.models.FileInstance') as mock_file_instance, \
            patch('invenio_files_rest.models.Location') as mock_location, \
            patch('weko_authors.utils.current_cache') as mock_current_cache, \
            patch('weko_authors.utils.db') as mock_db, \
            patch('weko_authors.utils.handle_exception') as mock_handle_exception:

            # モックの設定
            mock_weko_authors.get_id_prefix_all.return_value = ['test_prefix']
            mock_weko_authors.prepare_export_prefix.return_value = [['scheme1', 'name1', 'url1', 'false']]
            mock_get_export_url.return_value = None

            mock_file = Mock()
            mock_file.uri = 'test_uri'
            mock_file_instance.create.return_value = mock_file

            mock_location_instance = Mock()
            mock_location_instance.uri = 'default_uri'
            mock_location.get_default.return_value = mock_location_instance

            # 全てのリトライでエラーを発生させる
            mock_current_cache.set.side_effect = RedisError("Redis Error")

            # テスト対象の関数を実行
            app.config['WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY'] = 3
            app.config['WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL'] = 0
            app.config['WEKO_AUTHORS_EXPORT_TARGET_CACHE_KEY'] = 'test_cache_key'

            result = export_prefix('id_prefix')

            # 検証
            assert result is 'test_uri'
            assert mock_handle_exception.call_count == 3

    def test_export_prefix_timeout_error_retry_success(self, app):
        """異常系: TimeoutErrorエラー発生（リトライ成功）"""
        # モックの準備
        with patch('weko_authors.utils.WekoAuthors') as mock_weko_authors, \
            patch('weko_authors.utils.get_export_url') as mock_get_export_url, \
            patch('invenio_files_rest.models.FileInstance') as mock_file_instance, \
            patch('invenio_files_rest.models.Location') as mock_location, \
            patch('weko_authors.utils.current_cache') as mock_current_cache, \
            patch('weko_authors.utils.db') as mock_db, \
            patch('weko_authors.utils.handle_exception') as mock_handle_exception:

            # 1回目はエラー、2回目は成功するように設定
            mock_weko_authors.get_id_prefix_all.side_effect = [TimeoutError("Timeout"), ['test_prefix']]
            mock_weko_authors.prepare_export_prefix.return_value = [['scheme1', 'name1', 'url1', 'false']]
            mock_get_export_url.return_value = None

            mock_file = Mock()
            mock_file.uri = 'test_uri'
            mock_file_instance.create.return_value = mock_file

            mock_location_instance = Mock()
            mock_location_instance.uri = 'default_uri'
            mock_location.get_default.return_value = mock_location_instance

            # テスト対象の関数を実行
            app.config['WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY'] = 3
            app.config['WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL'] = 0

            result = export_prefix('id_prefix')

            # 検証
            assert result == 'test_uri'
            assert mock_weko_authors.get_id_prefix_all.call_count == 2
            mock_handle_exception.assert_called_once()

    def test_export_prefix_timeout_error_all_fails(self, app):
        """異常系: TimeoutErrorエラー発生（全リトライ失敗）"""
        # モックの準備
        with patch('weko_authors.utils.WekoAuthors') as mock_weko_authors, \
            patch('weko_authors.utils.handle_exception') as mock_handle_exception:

            # 全てのリトライでエラーを発生させる
            mock_weko_authors.get_id_prefix_all.side_effect = TimeoutError("Timeout")

            # テスト対象の関数を実行
            app.config['WEKO_AUTHORS_BULK_EXPORT_MAX_RETRY'] = 3
            app.config['WEKO_AUTHORS_BULK_EXPORT_RETRY_INTERVAL'] = 0

            result = export_prefix('id_prefix')

            # 検証
            assert result is None
            assert mock_weko_authors.get_id_prefix_all.call_count == 3
            assert mock_handle_exception.call_count == 3

# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::TestCheckFileName -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestCheckFileName:
    def test_check_file_name_author_db(self, app):
        """正常系: export_targetがauthor_dbの場合"""
        app.config['WEKO_AUTHORS_EXPORT_FILE_NAME'] = 'author_db_export.tsv'
        result = check_file_name('author_db')
        assert result == 'author_db_export.tsv'

    def test_check_file_name_id_prefix(self, app):
        """正常系: export_targetがid_prefixの場合"""
        app.config['WEKO_AUTHORS_ID_PREFIX_EXPORT_FILE_NAME'] = 'id_prefix_export.tsv'
        result = check_file_name('id_prefix')
        assert result == 'id_prefix_export.tsv'

    def test_check_file_name_affiliation_id(self, app):
        """正常系: export_targetがaffiliation_idの場合"""
        app.config['WEKO_AUTHORS_AFFILIATION_EXPORT_FILE_NAME'] = 'affiliation_id_export.tsv'
        result = check_file_name('affiliation_id')
        assert result == 'affiliation_id_export.tsv'

    def test_check_file_name_invalid_target(self, app):
        """異常系: export_targetが無効な場合"""
        result = check_file_name('invalid_target')
        assert result == ''

# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::TestCleanDeep -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestCleanDeep:
    # 正常系
    # 条件: 辞書の中にNoneや空文字が含まれている
    # 入力: {'fullname': 'Jane Doe', 'warnings': None, 'email': {"test": "", "test2": "test2"}, 'test': [{"test": ""}, {"test2": "test2"}]}
    # 期待結果: {'fullname': 'Jane Doe', 'email': {"test2": "test2"}, 'test': [{"test2": "test2"}]}
    def test_clean_deep_normal_case(self, app):
        data = {'fullname': 'Jane Doe', 'warnings': None, 'email': {"test": "", "test2": "test2"}, 'test': [{"test": ""}, {"test2": "test2"}]}
        expected = {'fullname': 'Jane Doe', 'email': {"test2": "test2"}, 'test': [{"test2": "test2"}]}
        assert clean_deep(data) == expected

# def update_cache_data(key: str, value: str, timeout=None):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_update_cache_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_update_cache_data(app):
    with patch('weko_authors.utils.current_cache') as mock_cache:
        update_cache_data('test', 'test', 100)
        mock_cache.set.assert_called_once_with('test', 'test', timeout=100)

    with patch('weko_authors.utils.current_cache') as mock_cache:
        update_cache_data('test', 'test')
        mock_cache.set.assert_called_once_with('test', 'test')

# def write_tmp_part_file(part_num, file_data, temp_file_path):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_write_tmp_part_file -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_write_tmp_part_file(app):

    with patch("weko_authors.utils.open") as mock_writer:
        update_cache_data(current_app.config.get("WEKO_AUTHORS_IMPORT_TEMP_FOLDER_PATH"), "/data/test_over_max")
        write_tmp_part_file(1, [{"key": "value"}], "temp_file_path")
        mock_writer.assert_called()


# def unpackage_and_check_import_file_for_prefix(file_format, file_name, temp_file):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_unpackage_and_check_import_file_for_prefix -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_unpackage_and_check_import_file_for_prefix(app):
    data = [
        [],
        ["scheme", "name", "url", "is_deleted"],
        ["123", "aaa", "http://example.com", ''],
        ["#456", "bbb", "http://example.org", ''],
        ["789", "ccc", "http://example.net", ''],
        ["789", "ccc", "http://example.net", ''],
        ["789", "ccc", "http://example.net", ''],
        ["789", "ccc", "http://example.net", ''],
        ["789", "ccc", "http://example.net", ''],
        ["789", "ccc", "http://example.net", ''],
        ["789", "ccc", "http://example.net", ''],
    ]

    with patch("weko_authors.utils.getEncode") as mock_getEncode,\
        patch("weko_authors.utils.open") as mock_writer,\
        patch("weko_authors.utils.csv.reader") as mock_csv:
        mock_getEncode.return_value = 'path/to/tempfile'
        mock_csv.return_value = iter(data)
        result = unpackage_and_check_import_file_for_prefix('csv', 'test.csv', 'path/to/tempfile')

    data_2 = [
        [],
        ["scheme", "scheme", "scheme", "scheme"],
        ["123", "aaa", "http://example.com", ''],
        ["456", "bbb", "http://example.org", ''],
        ["789", "ccc", "http://example.net", '']
    ]

    with patch("weko_authors.utils.getEncode") as mock_getEncode,\
        patch("weko_authors.utils.open") as mock_writer,\
        patch("weko_authors.utils.csv.reader") as mock_csv:
        with pytest.raises(Exception) as msg:
            mock_getEncode.return_value = 'path/to/tempfile'
            mock_csv.return_value = iter(data_2)
            result = unpackage_and_check_import_file_for_prefix('tsv', 'test.csv', 'path/to/tempfile')
            assert str(msg.value) == "{'error_msg': 'The following metadata keys are duplicated.<br/>scheme'}"

    data_3 = [
        [],
        ["scheme", "name", "url", "invalid_field"],
        ["123", "aaa", "http://example.com"],
        ["456", "bbb", "http://example.org"],
        ["789", "ccc", "http://example.net"]
    ]

    with patch("weko_authors.utils.getEncode") as mock_getEncode,\
        patch("weko_authors.utils.open") as mock_writer,\
        patch("weko_authors.utils.csv.reader") as mock_csv:
        with pytest.raises(Exception) as msg:
            mock_getEncode.return_value = 'path/to/tempfile'
            mock_csv.return_value = iter(data_3)
            unpackage_and_check_import_file_for_prefix('csv', 'test.csv', 'path/to/tempfile')
            assert str(msg.value) == "{'error_msg': 'Specified item does not consistency with DB item.<br/>invalid_field'}"

    data_4 = [
        [],
        ["scheme", "name", "url", "is_deleted"],
        ["123", "aaa", "http://example.com", ''],
        ["#456", "bbb", "http://example.org", ''],
        ["789", "ccc", "http://example.net", ''],
    ]

    with patch("weko_authors.utils.getEncode") as mock_getEncode,\
        patch("weko_authors.utils.open") as mock_writer,\
        patch("weko_authors.utils.handle_check_consistence_with_mapping_for_prefix") as mock_check,\
        patch("weko_authors.utils.csv.reader") as mock_csv:
        with pytest.raises(UnicodeDecodeError) as msg:
            mock_getEncode.return_value = 'path/to/tempfile'
            mock_csv.return_value = iter(data_4)
            # unicode_error = UnicodeDecodeError('utf-8', b'\x80abc', 0, 1, 'invalid start byte')
            # mock_csv.side_effect = unicode_error
            mock_check.side_effect = UnicodeDecodeError("utf-8", b'', 0, 1, "invalid start byte")
            result = unpackage_and_check_import_file_for_prefix('csv', 'test.csv', 'path/to/tempfile')
            assert str(msg.value) == "{'error_msg': 'The following metadata keys are duplicated.<br/>scheme'}"

    data_5 = [
        [],
        ["scheme", "name", "url", "is_deleted"],
        [123, "aaa", "http://example.com", ''],
    ]

    with patch("weko_authors.utils.getEncode") as mock_getEncode,\
        patch("weko_authors.utils.open") as mock_writer,\
        patch("weko_authors.utils.csv.reader") as mock_csv:
        with pytest.raises(Exception) as msg:
            mock_getEncode.return_value = 'path/to/tempfile'
            mock_csv.return_value = iter(data_5)
            unpackage_and_check_import_file_for_prefix('csv', 'test.csv', 'path/to/tempfile')
            assert str(msg.value) == "{'error_msg': 'The following metadata keys are duplicated.<br/>scheme'}"

    data_6 = [
        [],
        ["scheme", "name", "url", "is_deleted"],
        ["123", "aaa", "http://example.com", ''],
        ["test"],
        'aaaaaaaaaaa'
    ]

    with patch("weko_authors.utils.getEncode") as mock_getEncode,\
        patch("weko_authors.utils.open") as mock_writer,\
        patch("weko_authors.utils.csv.reader") as mock_csv:
        with pytest.raises(Exception) as msg:
            mock_getEncode.return_value = 'path/to/tempfile'
            mock_csv.return_value = iter(data_6)
            unpackage_and_check_import_file_for_prefix('csv', 'test.csv', 'path/to/tempfile')
            assert str(msg.value) == "{'error_msg': 'The following metadata keys are duplicated.<br/>scheme'}"


# def get_check_base_name():
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_get_check_base_name -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_check_base_name(app):
    update_cache_data(current_app.config["WEKO_AUTHORS_IMPORT_CACHE_USER_TSV_FILE_KEY"], "/data/test_over_max")
    result = get_check_base_name()

    assert result == "test_over_max-check"


# def get_check_result(entry):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_get_check_result -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_get_check_result(app):
    result = get_check_result({"errors": ["error1", "error2"], "status": "new"})
    assert result == "Error: error1 error2"

    result = get_check_result({"errors": [], "status": "new"})
    assert result == "Register"

    result = get_check_result({"errors": [], "status": "update"})
    assert result == "Update"

    result = get_check_result({"errors": [], "status": "deleted"})
    assert result == "Delete"

    result = get_check_result({"errors": [], "status": "other"})
    assert result == "other"


# def handle_check_consistence_with_mapping_for_prefix(keys, header):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_handle_check_consistence_with_mapping_for_prefix -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_handle_check_consistence_with_mapping_for_prefix(app):
    result = handle_check_consistence_with_mapping_for_prefix(["scheme", "name", "url", "is_deleted"], ["scheme", "name", "url", "is_deleted"])
    assert result ==[]

    result = handle_check_consistence_with_mapping_for_prefix(["scheme", "name", "url", "is_deleted"], ["scheme", "name", "url", "is_deleted", "extra_field"])
    assert result == ["extra_field"]


# def check_import_data_for_prefix(target, file_name: str, file_content: str):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_check_import_data_for_prefix -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_check_import_data_for_prefix(app):
    data = ['aaa', 'bbb']

    with patch('weko_authors.utils.unpackage_and_check_import_file_for_prefix') as mock_file, \
        patch('weko_authors.utils.validate_import_data_for_prefix') as mock_data:
        mock_file.return_value = data
        mock_data.return_value = data
        result = check_import_data_for_prefix("id_prefix", "test.tsv", "dGVzdA==")
        assert len(result['list_import_data']) > 0

    with patch('weko_authors.utils.unpackage_and_check_import_file_for_prefix') as mock_file, \
        patch('weko_authors.utils.validate_import_data_for_prefix') as mock_data:
        mock_file.return_value = data
        mock_data.return_value = data
        result = check_import_data_for_prefix("id_prefix", "test.tsv", "invalid_base64")
        assert len(result['error']) > 0

    with patch('weko_authors.utils.unpackage_and_check_import_file_for_prefix') as mock_file:
        unicode_error = UnicodeDecodeError('utf-8', b'\x80abc', 0, 1, 'invalid start byte')
        mock_file.side_effect = unicode_error
        result = check_import_data_for_prefix("id_prefix", "test.tsv", "dGVzdA==")
        assert len(result['error']) > 0

    with patch('weko_authors.utils.unpackage_and_check_import_file_for_prefix') as mock_file, \
        patch('weko_authors.utils.validate_import_data_for_prefix') as mock_data:
        mock_file.return_value = data
        mock_data.side_effect = Exception({"error_msg": "Mocked exception occurred"})
        result = check_import_data_for_prefix("id_prefix", "test.tsv", "dGVzdA==")
        assert len(result['error']) > 0


# def validate_import_data_for_prefix(file_data, target):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_validate_import_data_for_prefix -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_validate_import_data_for_prefix(authors_prefix_settings):
    with patch('weko_authors.utils.WekoAuthors.get_scheme_of_id_prefix') as mock_prefix,\
        patch('weko_authors.utils.WekoAuthors.get_scheme_of_affiliaiton_id'):
        mock_prefix.return_value = ['ORCID']
        result = validate_import_data_for_prefix([{'scheme': 'ORCID', 'name': 'ORCID', 'url': 'http://orcid.org', 'is_deleted': ''}], target = 'id_prefix')
    assert result == [{'scheme': 'ORCID', 'name': 'ORCID', 'url': 'http://orcid.org', 'is_deleted': '', 'status': 'update', 'id': 2}]

    with patch('weko_authors.utils.WekoAuthors.get_scheme_of_id_prefix') as mock_prefix,\
        patch('weko_authors.utils.WekoAuthors.get_scheme_of_affiliaiton_id'):
        mock_prefix.return_value = ['ORCID']
        result = validate_import_data_for_prefix([{'scheme': 'ISNI', 'name': 'ISNI', 'url': 'http://isni.org', 'is_deleted': ''}], target = 'affiliation_id')
    assert result == [{'scheme': 'ISNI', 'name': 'ISNI', 'url': 'http://isni.org', 'is_deleted': '', 'status': 'new'}]

    with patch('weko_authors.utils.WekoAuthors.get_scheme_of_id_prefix') as mock_prefix,\
        patch('weko_authors.utils.WekoAuthors.get_scheme_of_affiliaiton_id'):
        mock_prefix.return_value = ['ORCID']
        result = validate_import_data_for_prefix([{'scheme': '', 'name': 'ORCID', 'url': 'http://orcid.org', 'is_deleted': ''}], target = 'id_prefix')
    assert result == [{'scheme': '', 'name': 'ORCID', 'url': 'http://orcid.org', 'is_deleted': '', 'status': 'new', 'errors': ['Scheme is required item.']}]

    with patch('weko_authors.utils.WekoAuthors.get_scheme_of_id_prefix') as mock_prefix,\
        patch('weko_authors.utils.WekoAuthors.get_scheme_of_affiliaiton_id'):
        mock_prefix.return_value = ['ORCID']
        result = validate_import_data_for_prefix([{'scheme': 'WEKO', 'name': 'WEKO', 'url': 'http://weko.org', 'is_deleted': ''}], target = 'id_prefix')
    assert result == [{'scheme': 'WEKO', 'name': 'WEKO', 'url': 'http://weko.org', 'is_deleted': '', 'status': 'new', 'errors': ['The scheme WEKO cannot be used.']}]

    with patch('weko_authors.utils.WekoAuthors.get_scheme_of_id_prefix') as mock_prefix,\
        patch('weko_authors.utils.WekoAuthors.get_scheme_of_affiliaiton_id'):
        mock_prefix.return_value = ['ORCID']
        result = validate_import_data_for_prefix([{'scheme': 'ORCID', 'name': '', 'url': 'http://orcid.org', 'is_deleted': ''}], target = 'id_prefix')
    assert result == [{'scheme': 'ORCID', 'name': '', 'url': 'http://orcid.org', 'is_deleted': '', 'id': 2, 'status': 'update', 'errors': ['Name is required item.']}]

    with patch('weko_authors.utils.WekoAuthors.get_scheme_of_id_prefix') as mock_prefix,\
        patch('weko_authors.utils.WekoAuthors.get_scheme_of_affiliaiton_id'):
        mock_prefix.return_value = ['ORCID']
        result = validate_import_data_for_prefix([{'scheme': '', 'name': 'ORCID', 'url': 'http://orcid.org', 'is_deleted': ''}], target = 'id_prefix')
    assert result == [{'scheme': '', 'name': 'ORCID', 'url': 'http://orcid.org', 'is_deleted': '', 'status': 'new', 'errors': ['Scheme is required item.']}]

    with patch('weko_authors.utils.WekoAuthors.get_scheme_of_id_prefix') as mock_prefix,\
        patch('weko_authors.utils.WekoAuthors.get_scheme_of_affiliaiton_id'):
        mock_prefix.return_value = ['ORCID']
        result = validate_import_data_for_prefix([{'scheme': 'WEKO', 'name': 'WEKO', 'url': 'http://weko.org', 'is_deleted': ''}], target = 'id_prefix')
    assert result == [{'scheme': 'WEKO', 'name': 'WEKO', 'url': 'http://weko.org', 'is_deleted': '', 'status': 'new', 'errors': ['The scheme WEKO cannot be used.']}]

    with patch('weko_authors.utils.WekoAuthors.get_scheme_of_id_prefix') as mock_prefix,\
        patch('weko_authors.utils.WekoAuthors.get_scheme_of_affiliaiton_id'):
        mock_prefix.return_value = ['ORCID']
        result = validate_import_data_for_prefix([{'scheme': 'ORCID', 'name': '', 'url': 'http://orcid.org', 'is_deleted': ''}], target = 'id_prefix')
    assert result == [{'scheme': 'ORCID', 'name': '', 'url': 'http://orcid.org', 'is_deleted': '', 'id': 2, 'status': 'update', 'errors': ['Name is required item.']}]

    with patch('weko_authors.utils.WekoAuthors.get_scheme_of_id_prefix') as mock_prefix,\
        patch('weko_authors.utils.WekoAuthors.get_scheme_of_affiliaiton_id'):
        mock_prefix.return_value = ['ORCID']
        result = validate_import_data_for_prefix([{'scheme': 'ORCID', 'name': 'ORCID', 'url': 'orcid', 'is_deleted': ''}], target = 'id_prefix')
    assert result == [{'scheme': 'ORCID', 'name': 'ORCID', 'url': 'orcid', 'is_deleted': '', 'id': 2, 'status': 'update', 'errors': ['URL is not URL format.']}]

    with patch('weko_authors.utils.WekoAuthors.get_scheme_of_id_prefix') as mock_prefix,\
        patch('weko_authors.utils.WekoAuthors.get_scheme_of_affiliaiton_id'):
        mock_prefix.return_value = []
        result = validate_import_data_for_prefix([{'scheme': 'ORCID', 'name': 'ORCID', 'url': 'http://orcid.org', 'is_deleted': 'D'}], target = 'id_prefix')
    assert result == [{'scheme': 'ORCID', 'name': 'ORCID', 'url': 'http://orcid.org', 'is_deleted': 'D', 'errors': ['The specified scheme does not exist.']}]

    with patch('weko_authors.utils.WekoAuthors.get_scheme_of_id_prefix') as mock_prefix,\
        patch('weko_authors.utils.WekoAuthors.get_used_scheme_of_id_prefix') as mock_used,\
        patch('weko_authors.utils.WekoAuthors.get_scheme_of_affiliaiton_id'):
        mock_prefix.return_value = ['ORCID']
        mock_used.return_value = (
            ["ORCID"],
            {1: 'WEKO', 2: 'ORCID', 3: 'CiNii', 4: 'KAKEN2', 5: 'ROR'}
        )
        result = validate_import_data_for_prefix([{'scheme': 'ORCID', 'name': 'ORCID', 'url': 'http://orcid.org', 'is_deleted': 'D'}], target = 'id_prefix')
    assert result == [{'scheme': 'ORCID', 'name': 'ORCID', 'url': 'http://orcid.org', 'is_deleted': 'D', 'id': 2, 'status': 'deleted', 'errors': ['The specified scheme is used in the author ID.']}]

    with patch('weko_authors.utils.WekoAuthors.get_scheme_of_id_prefix') as mock_prefix,\
        patch('weko_authors.utils.WekoAuthors.get_scheme_of_affiliaiton_id'):
        mock_prefix.return_value = ['ORCID']
        result = validate_import_data_for_prefix([{'scheme': 'ORCID', 'name': 'ORCID', 'url': 'http://orcid.org', 'is_deleted': ''}, {'scheme': 'ORCID', 'name': 'ORCID', 'url': 'http://orcid.org', 'is_deleted': ''}], target = 'id_prefix')
    assert result == [{'scheme': 'ORCID', 'name': 'ORCID', 'url': 'http://orcid.org', 'is_deleted': '', 'id': 2, 'status': 'update'}, {'scheme': 'ORCID', 'name': 'ORCID', 'url': 'http://orcid.org', 'is_deleted': '', 'id': 2, 'status': 'update', 'errors': ['The specified scheme is duplicated.']}]


# def import_id_prefix_to_system(id_prefix):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_import_id_prefix_to_system -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_import_id_prefix_to_system(authors_prefix_settings):
    with patch('weko_authors.utils.AuthorsPrefixSettings.create') as mock_create:
        import_id_prefix_to_system({'scheme': 'test_scheme', 'status': 'new'})
        mock_create.assert_called_once()

    with patch('weko_authors.utils.AuthorsPrefixSettings.update') as mock_update:
        import_id_prefix_to_system({'scheme': 'test_scheme', 'status': 'update', 'id': 1})
        mock_update.assert_called_once()

    with patch('weko_authors.utils.AuthorsPrefixSettings.delete') as mock_delete:
        import_id_prefix_to_system({'scheme': 'test_scheme', 'status': 'deleted', 'id': 1})
        mock_delete.assert_called_once()

    with patch('weko_authors.utils.WekoAuthors.get_used_scheme_of_id_prefix') as mock_used:
        mock_used.return_value = (
            ["WEKO"],
            {1: 'WEKO', 2: 'ORCID', 3: 'CiNii', 4: 'KAKEN2', 5: 'ROR'}
        )
        with pytest.raises(Exception) as e:
            import_id_prefix_to_system({'scheme': 'WEKO', 'status': 'deleted', 'id': 1})
        assert e.value.args[0] == {'error_id': 'delete_author_link'}

    with pytest.raises(Exception) as e:
        import_id_prefix_to_system({'scheme': 'test_scheme', 'status': 'invalid_status'})
    assert e.value.args[0] == {'error_id': 'status_error'}

    with patch('weko_authors.utils.AuthorsPrefixSettings.create') as mock_create:
        mock_create.side_effect = [SQLAlchemyError("SQLAlchemyError")]
        with pytest.raises(Exception):
            import_id_prefix_to_system({'scheme': 'test_scheme', 'status': 'new'})
            mock_create.assert_called_once()

    with patch('weko_authors.utils.AuthorsPrefixSettings.create') as mock_create:
        mock_create.side_effect = [TimeoutError("Timeout")]
        with pytest.raises(Exception):
            import_id_prefix_to_system({'scheme': 'test_scheme', 'status': 'new'})
            mock_create.assert_called_once()


# def import_affiliation_id_to_system(affiliation_id):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_import_affiliation_id_to_system -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_import_affiliation_id_to_system(authors_affiliation_settings):
    with patch('weko_authors.utils.AuthorsAffiliationSettings.create') as mock_create:
        import_affiliation_id_to_system({'scheme': 'test_scheme', 'status': 'new'})
        mock_create.assert_called_once()

    with patch('weko_authors.utils.AuthorsAffiliationSettings.update') as mock_update:
        import_affiliation_id_to_system({'scheme': 'test_scheme', 'status': 'update', 'id': 1})
        mock_update.assert_called_once()

    with patch('weko_authors.utils.AuthorsAffiliationSettings.delete') as mock_delete:
        import_affiliation_id_to_system({'scheme': 'test_scheme', 'status': 'deleted', 'id': 1})
        mock_delete.assert_called_once()

    with patch('weko_authors.utils.WekoAuthors.get_used_scheme_of_affiliation_id') as mock_used:
        mock_used.return_value = (
            ["WEKO"],
            {1: 'WEKO', 2: 'ORCID', 3: 'CiNii', 4: 'KAKEN2', 5: 'ROR'}
        )
        with pytest.raises(Exception) as e:
            import_affiliation_id_to_system({'scheme': 'WEKO', 'status': 'deleted', 'id': 1})
        assert e.value.args[0] == {'error_id': 'delete_author_link'}

    with pytest.raises(Exception) as e:
        import_affiliation_id_to_system({'scheme': 'test_scheme', 'status': 'invalid_status'})
    assert e.value.args[0] == {'error_id': 'status_error'}

    with patch('weko_authors.utils.AuthorsAffiliationSettings.create') as mock_create:
        mock_create.side_effect = [SQLAlchemyError("SQLAlchemyError")]
        with pytest.raises(Exception):
            import_affiliation_id_to_system({'scheme': 'test_scheme', 'status': 'new'})
            mock_create.assert_called_once()

    with patch('weko_authors.utils.AuthorsAffiliationSettings.create') as mock_create:
        mock_create.side_effect = [TimeoutError("Timeout")]
        with pytest.raises(Exception):
            import_affiliation_id_to_system({'scheme': 'test_scheme', 'status': 'new'})
            mock_create.assert_called_once()


# def band_check_file_for_user(max_page):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_band_check_file_for_user -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_band_check_file_for_user(authors_affiliation_settings):
    data = [
        {"pk_id": 1, "authorNameInfo":[{"familyName": "aaa", "firstName": "bbb"}]},
    ]
    with patch('weko_authors.utils.get_check_base_name') as mock_check,\
        patch("weko_authors.utils.open") as mock_open,\
        patch("weko_authors.utils.json.load") as mock_json:
        # update_cache_data(current_app.config.get("WEKO_AUTHORS_IMPORT_BATCH_SIZE"), 100)
        mock_check.return_value = "test_over_max-check"
        mock_json.return_value = data
        result = band_check_file_for_user(1)
        assert result == "var/tmp/authors_import/import_author_check_result_{}.tsv".format(datetime.datetime.now().strftime("%Y%m%d%H%M"))

    data_2 = [
        {"pk_id": 1, "authorNameInfo":[{"familyName": "a", "firstName": ""}, {"familyName": "b", "firstName": ""}],},
    ]
    with patch('weko_authors.utils.get_check_base_name') as mock_check,\
        patch("weko_authors.utils.open") as mock_open,\
        patch("weko_authors.utils.json.load") as mock_json:
        # update_cache_data(current_app.config.get("WEKO_AUTHORS_IMPORT_BATCH_SIZE"), 100)
        mock_check.return_value = "test_over_max-check"
        mock_json.return_value = data_2
        result = band_check_file_for_user(1)
        assert result == "var/tmp/authors_import/import_author_check_result_{}.tsv".format(datetime.datetime.now().strftime("%Y%m%d%H%M"))

    with patch('weko_authors.utils.get_check_base_name') as mock_check,\
        patch("weko_authors.utils.open") as mock_open:
        mock_check.return_value = "test_over_max-check"
        mock_open.side_effect = Exception('not found')
        with pytest.raises(Exception) as ex:
            result = band_check_file_for_user(1)
            assert str(ex.value) == 'not found'


# def prepare_import_data(max_page_for_import_tab):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_prepare_import_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_prepare_import_data(authors_affiliation_settings):
    data = [
        {"pk_id": 1, "authorNameInfo":[{"familyName": "aaa", "firstName": "bbb"}]},
    ]
    with patch('weko_authors.utils.get_check_base_name') as mock_check,\
        patch("weko_authors.utils.open") as mock_open,\
        patch("weko_authors.utils.json.load") as mock_json:
        mock_check.return_value = "test_over_max-check"
        mock_json.return_value = data
        result = prepare_import_data(1)
        assert result[1]== {}
        assert result[2]== 1

    data = [
        {"warnings": 1, "is_deleted": 1, "authorNameInfo":[{"familyName": "aaa", "firstName": "bbb"}]},
    ]
    with patch('weko_authors.utils.get_check_base_name') as mock_check,\
        patch("weko_authors.utils.open") as mock_open,\
        patch("weko_authors.utils.json.load") as mock_json:
        mock_check.return_value = "test_over_max-check"
        mock_json.return_value = data
        result = prepare_import_data(3)
        assert result[1]== {}
        assert result[2]== 3

    data = [
        {"errors": "error", "pk_id": 1, "authorNameInfo":[{"familyName": "aaa", "firstName": "bbb"}]},
        {"pk_id": 1, "authorNameInfo":[{"familyName": "aaa", "firstName": "bbb"}]},
    ]
    with patch('weko_authors.utils.get_check_base_name') as mock_check,\
        patch("weko_authors.utils.open") as mock_open,\
        patch("weko_authors.utils.json.load") as mock_json:
        mock_check.return_value = "test_over_max-check"
        mock_json.return_value = data
        result = prepare_import_data(1)
        assert result[1]== {}
        assert result[2]== 1

    data = [
        {"pk_id": 1, "authorNameInfo":[{"familyName": "aaa", "firstName": "bbb"}]},
    ]
    with patch('weko_authors.utils.get_check_base_name') as mock_check,\
        patch("weko_authors.utils.open") as mock_open,\
        patch("weko_authors.utils.json.load") as mock_json,\
        patch('weko_authors.utils.current_app.config.get') as mock_max:
        mock_check.return_value = "test_over_max-check"
        mock_json.return_value = data * 3
        mock_max.side_effect = [
            2,
            "var/tmp/authors_import"
        ]
        result = prepare_import_data(3)
        assert result[0] == data * 2
        assert result[1]['part_number'] == 1
        assert result[1]['count'] == 2

    # 正常系
    # 条件: リストの中にNoneや空文字が含まれている
    # 入力: [None, '', 'valid', {'key': ''}, {'key': 'value'}]
    # 期待結果: ['valid', {'key': 'value'}]
    def test_clean_deep_list_with_none_and_empty_string(self, app):
        data = [None, '', 'valid', {'key': ''}, {'key': 'value'}]
        expected = ['valid', {'key': 'value'}]
        assert clean_deep(data) == expected

    # 正常系
    # 条件: リストの中に空の辞書が含まれている
    # 入力: [{'key': 'value'}, {}]
    # 期待結果: [{'key': 'value'}]
    def test_clean_deep_list_with_empty_dict(self, app):
        data = [{'key': 'value'}, {}]
        expected = [{'key': 'value'}]
        assert clean_deep(data) == expected

    # 正常系
    # 条件: 辞書の中にNoneや空文字が含まれていない
    # 入力: {'fullname': 'Jane Doe', 'email': {"test2": "test2"}, 'test': [{"test2": "test2"}]}
    # 期待結果: {'fullname': 'Jane Doe', 'email': {"test2": "test2"}, 'test': [{"test2": "test2"}]}
    def test_clean_deep_no_none_or_empty_string(self, app):
        data = {'fullname': 'Jane Doe', 'email': {"test2": "test2"}, 'test': [{"test2": "test2"}]}
        expected = {'fullname': 'Jane Doe', 'email': {"test2": "test2"}, 'test': [{"test2": "test2"}]}
        assert clean_deep(data) == expected

# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::TestUpdateDataForWekoLink -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
class TestUpdateDataForWekoLink:
    """update_data_for_weko_linkのテストクラス"""

# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::TestUpdateDataForWekoLink::test_update_data_normal_case -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
    def test_update_data_normal_case(self, app):
        """
        正常系
        条件：weko_linkの内容が更新される場合
        入力：
            - data: nameIdentifiersを含むメタデータ
            - weko_link: 更新前のweko_link
        期待結果：
            - weko_linkが更新される
            - dataのnameIdentifierが更新される
        """
        # テスト用データ
        data = {
            "creators": [
                {
                    "nameIdentifiers": [
                        {
                            "nameIdentifierScheme": "WEKO",
                            "nameIdentifier": "old_weko_id_1"
                        }
                    ]
                }
            ]
        }
        weko_link = {"1": "old_weko_id_1"}

        # AuthorsクラスのMock
        author_mock = {
            "authorIdInfo": [
                {"idType": "1", "authorId": "new_weko_id_1"}
            ]
        }

        with patch.object(Authors, 'get_author_by_id', return_value=author_mock):
            update_data_for_weko_link(data, weko_link)
        result = data["creators"][0]["nameIdentifiers"][0]["nameIdentifier"]
        # 検証
        assert result == "new_weko_id_1"

    def test_no_change_in_weko_link(self, app):
        """
        正常系
        条件：weko_linkの内容が変更されない場合
        入力：
            - data: nameIdentifiersを含むメタデータ
            - weko_link: 更新前のweko_link
        期待結果：
            - weko_linkは変更されない
            - dataは変更されない
        """
        data = {
            "creators": [
                {
                    "nameIdentifiers": [
                        {
                            "nameIdentifierScheme": "WEKO",
                            "nameIdentifier": "weko_id_1"
                        }
                    ]
                }
            ]
        }
        weko_link = {"1": "weko_id_1"}
        data_copy = copy.deepcopy(data)

        author_mock = {
            "authorIdInfo": [
                {"idType": "1", "authorId": "weko_id_1"}
            ]
        }

        with patch.object(Authors, 'get_author_by_id', return_value=author_mock):
            update_data_for_weko_link(data, weko_link)

        assert data == data_copy

    def test_author_not_found(self, app):
        """
        正常系
        条件：Authorsテーブルに該当するauthorが存在しない場合
        入力：
            - data: 任意のメタデータ
            - weko_link: 更新前のweko_link
        期待結果：
            - weko_linkは変更されない
            - dataは変更されない
        """
        data = {"creators": [{"name": "test"}]}
        weko_link = {"1": "weko_id_1"}
        data_copy = copy.deepcopy(data)
        weko_link_copy = copy.deepcopy(weko_link)

        with patch.object(Authors, 'get_author_by_id', return_value=None):
            update_data_for_weko_link(data, weko_link)

        assert data == data_copy

    def test_id_type_not_1(self, app):
        """
        正常系
        条件：authorIdInfoのidTypeが1でない場合
        入力：
            - data: 任意のメタデータ
            - weko_link: 更新前のweko_link
        期待結果：
            - weko_linkは変更されない
            - dataは変更されない
        """
        data = {"creators": [{"name": "test"}]}
        weko_link = {"1": "weko_id_1"}
        data_copy = copy.deepcopy(data)
        weko_link_copy = copy.deepcopy(weko_link)

        author_mock = {
            "authorIdInfo": [
                {"idType": "2", "authorId": "other_id"}
            ]
        }

        with patch.object(Authors, 'get_author_by_id', return_value=author_mock):
            update_data_for_weko_link(data, weko_link)

        assert data == data_copy

    def test_multiple_authors_and_identifiers(self, app):
        """
        正常系
        条件：複数のauthorとnameIdentifiersがある場合
        入力：
            - data: 複数のauthorとnameIdentifiersを含むメタデータ
            - weko_link: 複数のエントリを持つweko_link
        期待結果：
            - dataの全てのnameIdentifierが更新される
        """
        data = {
            "creators": [
                {
                    "nameIdentifiers": [
                        {
                            "nameIdentifierScheme": "WEKO",
                            "nameIdentifier": "old_weko_id_1"
                        },
                        {
                            "nameIdentifierScheme": "OTHER",
                            "nameIdentifier": "other_id"
                        }
                    ]
                },
                {
                    "nameIdentifiers": [
                        {
                            "nameIdentifierScheme": "WEKO",
                            "nameIdentifier": "old_weko_id_2"
                        }
                    ]
                }
            ],
            "contributors": [
                {
                    "nameIdentifiers": [
                        {
                            "nameIdentifierScheme": "WEKO",
                            "nameIdentifier": "old_weko_id_3"
                        }
                    ]
                }
            ]
        }
        weko_link = {
            "1": "old_weko_id_1",
            "2": "old_weko_id_2",
            "3": "old_weko_id_3"
        }

        def mock_get_author_by_id(pk_id):
            if pk_id == "1":
                return {"authorIdInfo": [{"idType": "1", "authorId": "new_weko_id_1"}]}
            elif pk_id == "2":
                return {"authorIdInfo": [{"idType": "1", "authorId": "new_weko_id_2"}]}
            elif pk_id == "3":
                return {"authorIdInfo": [{"idType": "1", "authorId": "new_weko_id_3"}]}
            return None

        with patch.object(Authors, 'get_author_by_id', side_effect=mock_get_author_by_id):
            update_data_for_weko_link(data, weko_link)

        assert data["creators"][0]["nameIdentifiers"][0]["nameIdentifier"] == "new_weko_id_1"
        assert data["creators"][1]["nameIdentifiers"][0]["nameIdentifier"] == "new_weko_id_2"
        assert data["contributors"][0]["nameIdentifiers"][0]["nameIdentifier"] == "new_weko_id_3"
        # 他のスキームのIDは変更されないことを確認
        assert data["creators"][0]["nameIdentifiers"][1]["nameIdentifier"] == "other_id"

    def test_non_list_data_fields(self, app):
        """
        正常系
        条件：dataのフィールドがリストでない場合
        入力：
            - data: リスト以外のデータ型を含むフィールドを持つメタデータ
            - weko_link: weko_link
        期待結果：
            - dataの該当フィールドはスキップされる
        """
        data = {
            "creators": [
                {
                    "nameIdentifiers": [
                        {
                            "nameIdentifierScheme": "WEKO",
                            "nameIdentifier": "old_weko_id_1"
                        }
                    ]
                }
            ],
            "title": "Test Title",  # 文字列フィールド
            "description": {"text": "Test Description"}  # 辞書フィールド
        }
        weko_link = {"1": "old_weko_id_1"}

        author_mock = {
            "authorIdInfo": [
                {"idType": "1", "authorId": "new_weko_id_1"}
            ]
        }

        with patch.object(Authors, 'get_author_by_id', return_value=author_mock):
            update_data_for_weko_link(data, weko_link)

        assert data["creators"][0]["nameIdentifiers"][0]["nameIdentifier"] == "new_weko_id_1"
        # 文字列や辞書フィールドは変更されないこと
        assert data["title"] == "Test Title"
        assert data["description"] == {"text": "Test Description"}

    def test_string_items_in_list(self, app):
        """
        正常系
        条件：dataのリストフィールド内に文字列アイテムがある場合
        入力：
            - data: リスト内に文字列アイテムを含むメタデータ
            - weko_link:　weko_link
        期待結果：
            - 文字列アイテムはスキップされる
        """
        data = {
            "creators": [
                {
                    "other_identifiers":[],
                    "nameIdentifiers": [
                        {
                            "nameIdentifierScheme": "WEKO",
                            "nameIdentifier": "old_weko_id_1"
                        }
                    ]
                },
                "Simple String Creator"  # 文字列アイテム
            ]
        }
        weko_link = {"1": "old_weko_id_1"}

        author_mock = {
            "authorIdInfo": [
                {"idType": "1", "authorId": "new_weko_id_1"}
            ]
        }

        with patch.object(Authors, 'get_author_by_id', return_value=author_mock):
            update_data_for_weko_link(data, weko_link)

        assert data["creators"][0]["nameIdentifiers"][0]["nameIdentifier"] == "new_weko_id_1"
        # 文字列アイテムは変更されないこと
        assert data["creators"][1] == "Simple String Creator"

    def test_no_matching_nameIdentifier(self, app):
        """
        正常系
        条件：nameIdentifierがweko_linkの値と一致しない場合
        入力：
            - data: weko_linkと一致しないnameIdentifierを含むメタデータ
            - weko_link: weko_link
        期待結果：
            - dataのnameIdentifierは更新されない
        """
        data = {
            "creators": [
                {
                    "nameIdentifiers": [
                        {
                            "nameIdentifierScheme": "WEKO",
                            "nameIdentifier": "different_weko_id"
                        }
                    ]
                }
            ]
        }
        weko_link = {"1": "old_weko_id_1"}
        data_copy = copy.deepcopy(data)

        author_mock = {
            "authorIdInfo": [
                {"idType": "1", "authorId": "new_weko_id_1"}
            ]
        }

        with patch.object(Authors, 'get_author_by_id', return_value=author_mock):
            update_data_for_weko_link(data, weko_link)

        # 一致するnameIdentifierがないため、データは変更されない
        assert data == data_copy

    def test_empty_input_data(self, app):
        """
        正常系
        条件：空のデータ辞書が入力された場合
        入力：
            - data: 空の辞書
            - weko_link: weko_link
        期待結果：
            - dataは変更されない（空のまま）
        """
        data = {}
        weko_link = {"1": "old_weko_id_1"}

        author_mock = {
            "authorIdInfo": [
                {"idType": "1", "authorId": "new_weko_id_1"}
            ]
        }

        with patch.object(Authors, 'get_author_by_id', return_value=author_mock):
            update_data_for_weko_link(data, weko_link)

        assert data == {}

    def test_empty_weko_link(self, app):
        """
        正常系
        条件：空のweko_linkが入力された場合
        入力：
            - data: 任意のメタデータ
            - weko_link: 空の辞書
        期待結果：
            - dataは変更されない
        """
        data = {
            "creators": [
                {
                    "nameIdentifiers": [
                        {
                            "nameIdentifierScheme": "WEKO",
                            "nameIdentifier": "weko_id_1"
                        }
                    ]
                }
            ]
        }
        weko_link = {}
        data_copy = copy.deepcopy(data)

        update_data_for_weko_link(data, weko_link)

        assert data == data_copy

# def write_to_tempfile(start, row_header, row_label_en, row_label_jp, row_data):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_write_to_tempfile -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_write_to_tempfile(app, mocker):
    start = 0
    row_header = ["header1", "header2"]
    row_label_en = ["label_en1", "label_en2"]
    row_label_jp = ["label_jp1", "label_jp2"]
    row_data = [["data1", "data2"], ["data3", "data4"]]
    current_cache.delete("weko_authors_export_temp_file_path_key")
    mock_open = mocker.patch("builtins.open", mocker.mock_open())
    write_to_tempfile(start, row_header, row_label_en, row_label_jp, row_data)
    mock_open.assert_called_with(None, 'a', newline='', encoding='utf-8-sig')
    current_cache.set("weko_authors_export_temp_file_path_key",{"key":"authors_export_temp_file_path_key"})
    start = 1
    write_to_tempfile(start, row_header, row_label_en, row_label_jp, row_data)
    mock_open.assert_called_with({"key":"authors_export_temp_file_path_key"}, 'a', newline='', encoding='utf-8-sig')
    mock_logger = mocker.patch("weko_authors.utils.current_app.logger")
    mock_open.side_effect = Exception("File write error")
    write_to_tempfile(start, row_header, row_label_en, row_label_jp, row_data)
    mock_logger.error.assert_called()

# def create_result_file_for_user(json):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_create_result_file_for_user -vv -s --cov-branch --cov-report=html --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_create_result_file_for_user(app, mocker):
    json = [
        {
            "No.": "1",
            "Start Date": "2025-01-01",
            "End Date": "2025-01-02",
            "Previous WEKO ID": "123",
            "New WEKO ID": "456",
            "full_name": "テスト 太郎",
            "Status": "success",
        }
    ]
    mock_result_over_max_data = [
        {
            "No.": "1",
            "Start Date": "2025-01-01",
            "End Date": "2025-01-02",
            "Previous WEKO ID": "123",
            "New WEKO ID": "456",
            "full_name": "テスト 太郎",
            "Status": "success",
        }
    ]
    result_path_key = current_app.config["WEKO_AUTHORS_IMPORT_CACHE_RESULT_OVER_MAX_FILE_PATH_KEY"]
    current_cache.set(result_path_key,{"key":"cache_result_over_max_file_path_key"})
    mocker.patch("builtins.open", mock_open(read_data=""))
    mocker.patch("csv.writer", return_value=MagicMock())
    mocker.patch("csv.reader", return_value=iter(mock_result_over_max_data))
    create_result_file_for_user(json)
    open.assert_any_call({"key":"cache_result_over_max_file_path_key"}, "r", encoding="utf-8")
    csv_writer = csv.writer.return_value
    csv_writer.writerow.assert_any_call(["No.", "Start Date", "End Date", "Previous WEKO ID", "New WEKO ID", "full_name", "Status"])
    csv_writer.writerow.assert_any_call(['1', '2025-01-01', '2025-01-02', '123', '456', 'テスト 太郎', 'success'])

    # Exception
    mock_logger = mocker.patch("weko_authors.utils.current_app.logger")
    mocker.patch("csv.writer", side_effect=Exception)
    create_result_file_for_user(json)
    mock_logger.error.assert_called()

    # not result_over_max_file_path is true
    current_cache.delete(result_path_key)
    res = create_result_file_for_user(json)
    assert res == None

