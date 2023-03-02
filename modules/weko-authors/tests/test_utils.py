
from os.path import dirname, join
import pytest
from mock import patch
from flask import current_app

from invenio_indexer.api import RecordIndexer
from invenio_cache import current_cache

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
    get_count_item_link
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


# def export_authors():
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_export_authors -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_export_authors(app,authors,location,file_instance,mocker):
    mocker.patch("weko_authors.utils.WekoAuthors.get_all",return_value=authors)
    scheme_info={"1":{"scheme":"WEKO","url":None},"2":{"scheme":"ORCID","url":"https://orcid.org/##"}}
    mocker.patch("weko_authors.utils.WekoAuthors.get_identifier_scheme_info",return_value=scheme_info)
    header = ["#pk_id","authorNameInfo[0].familyName","authorNameInfo[0].firstName","authorNameInfo[0].language","authorNameInfo[0].nameFormat","authorNameInfo[0].nameShowFlg","authorIdInfo[0].idType","authorIdInfo[0].authorId","authorIdInfo[0].authorIdShowFlg","emailInfo[0].email","is_deleted"]
    label_en=["#WEKO ID","Family Name[0]","Given Name[0]","Language[0]","Name Format[0]","Name Display[0]","Identifier Scheme[0]","Identifier[0]","Identifier Display[0]","Mail Address[0]","Delete Flag"]
    label_jp=["#WEKO ID","姓[0]","名[0]","言語[0]","フォーマット[0]","姓名・言語 表示／非表示[0]","外部著者ID 識別子[0]","外部著者ID[0]","外部著者ID 表示／非表示[0]","メールアドレス[0]","削除フラグ"]
    row_data = [["1","テスト","太郎","ja","familyNmAndNm","Y","ORCID","1234","Y","test.taro@test.org",""],
            ["2","test","smith","en","familyNmAndNm","Y","ORCID","5678","Y","test.smith@test.org",""]]
    mocker.patch("weko_authors.utils.WekoAuthors.prepare_export_data",return_value=(header,label_en,label_jp,row_data))
    with patch("weko_authors.utils.get_export_url",return_value={}):
        result = export_authors()
        assert result
    
    current_app.config.update(WEKO_ADMIN_OUTPUT_FORMAT="csv")
    cache_url = {"file_uri":"/var/tmp/test_dir"}
    with patch("weko_authors.utils.get_export_url",return_value=cache_url):
        result = export_authors()
        assert result == "/var/tmp/test_dir"
    
    # raise Exception
    with patch("weko_authors.utils.WekoAuthors.get_all", side_effect=Exception("test_error")):
        result = export_authors()
        assert result == None

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
    mocker.patch("weko_authors.utils.flatten_authors_mapping",return_value=(mapping_all,mapping_ids))
    file_data = [{'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'Y'}], 'authorIdInfo': [{'idType': 'ORCID', 'authorId': '1234', 'authorIdShowFlg': 'Y'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': ''}, {'pk_id': '2', 'authorNameInfo': [{'familyName': 'test', 'firstName': 'smith', 'language': 'en', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'Y'}], 'authorIdInfo': [{'idType': 'ORCID', 'authorId': '5678', 'authorIdShowFlg': 'Y'}], 'emailInfo': [{'email': 'test.smith@test.org'}], 'is_deleted': ''}]
    mocker.patch("weko_authors.utils.unpackage_and_check_import_file",return_value=file_data)
    return_validate = [{'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'true'}], 'authorIdInfo': [{'idType': 2, 'authorId': '1234', 'authorIdShowFlg': 'true'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': '', 'status': 'update'}, {'pk_id': '2', 'authorNameInfo': [{'familyName': 'test', 'firstName': 'smith', 'language': 'en', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'true'}], 'authorIdInfo': [{'idType': 2, 'authorId': '5678', 'authorIdShowFlg': 'true'}], 'emailInfo': [{'email': 'test.smith@test.org'}], 'is_deleted': '', 'status': 'update'}]
    mocker.patch("weko_authors.utils.validate_import_data",return_value=return_validate)
    
    
    file_name = "testfile.tsv"
    file_content = b"test_content=="
    test = {'list_import_data': [{'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'true'}], 'authorIdInfo': [{'idType': 2, 'authorId': '1234', 'authorIdShowFlg': 'true'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': '', 'status': 'update'}, {'pk_id': '2', 'authorNameInfo': [{'familyName': 'test', 'firstName': 'smith', 'language': 'en', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'true'}], 'authorIdInfo': [{'idType': 2, 'authorId': '5678', 'authorIdShowFlg': 'true'}], 'emailInfo': [{'email': 'test.smith@test.org'}], 'is_deleted': '', 'status': 'update'}]}
    result = check_import_data(file_name,file_content)
    assert result == test

    # raise Exception with args[0] is dict
    with patch("weko_authors.utils.flatten_authors_mapping",side_effect=Exception({"error_msg":"test_error"})):
        result = check_import_data(file_name,file_content)
        assert result == {"error":"test_error"}
    
    # raise Exception with args[0] is not dict
    with patch("weko_authors.utils.flatten_authors_mapping",side_effect=AttributeError("test_error")):
        result = check_import_data(file_name,file_content)
        assert result == {"error":"Internal server error"}
    
    # raise UnicodeDecodeError
    with patch("weko_authors.utils.flatten_authors_mapping",side_effect=UnicodeDecodeError("utf-8",b"test",0,1,"test_reason")):
        result = check_import_data(file_name,file_content)
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
def test_unpackage_and_check_import_file(app):
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
    temp_file=join(dirname(__file__),"data/test_files/import_data.tsv")
    result = unpackage_and_check_import_file(file_format,file_name,temp_file,mapping_ids)
    test = [{'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'Y'}], 'authorIdInfo': [{'idType': 'ORCID', 'authorId': '1234', 'authorIdShowFlg': 'Y'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': ''}, {'pk_id': '2', 'authorNameInfo': [{'familyName': 'test', 'firstName': 'smith', 'language': 'en', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'Y'}], 'authorIdInfo': [{'idType': 'ORCID', 'authorId': '5678', 'authorIdShowFlg': 'Y'}], 'emailInfo': [{'email': 'test.smith@test.org'}], 'is_deleted': ''}]
    assert result == test

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
    temp_file=join(dirname(__file__),"data/test_files/import_data.csv")
    result = unpackage_and_check_import_file("csv",file_name,temp_file,mapping_ids)
    test = [{'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'Y'}], 'authorIdInfo': [{'idType': 'ORCID', 'authorId': '1234', 'authorIdShowFlg': 'Y'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': ''}, {'pk_id': '2', 'authorNameInfo': [{'familyName': 'test', 'firstName': 'smith', 'language': 'en', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'Y'}], 'authorIdInfo': [{'idType': 'ORCID', 'authorId': '5678', 'authorIdShowFlg': 'Y'}], 'emailInfo': [{'email': 'test.smith@test.org'}], 'is_deleted': ''}]
    assert result == test
    

# def validate_import_data(file_format, file_data, mapping_ids, mapping):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_validate_import_data -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_validate_import_data(authors_prefix_settings,mocker):
    mocker.patch("weko_authors.utils.WekoAuthors.get_author_for_validation",return_value=({"1":True,"2":True},{"2":{"1234":["1"],"5678":["2"]}}))
    
    file_format = "tsv"
    file_data = [
        {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'Y'}], 'authorIdInfo': [{'idType': 'ORCID', 'authorId': '1234', 'authorIdShowFlg': 'Y'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': ''},
        {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'Y'}], 'authorIdInfo': [{'idType': 'ORCID', 'authorId': '1234', 'authorIdShowFlg': 'Y'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': ''},
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
    mappings = [
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
    
    test = [
        {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'true'}], 'authorIdInfo': [{'idType': 2, 'authorId': '1234', 'authorIdShowFlg': 'true'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': '', 'status': 'update'},
        {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'Y'}], 'authorIdInfo': [{'idType': 2, 'authorId': '1234', 'authorIdShowFlg': 'Y'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': '', 'status': 'update', 'errors': ['There is duplicated data in the tsv file.']}
    ]
    result = validate_import_data(file_format,file_data,mapping_ids,mappings)
    assert result == test
    
    file_data = [
        {'pk_id': None,  'authorIdInfo': [{'idType': 'ORCID', 'authorId': '1234', 'authorIdShowFlg': 'Y'}], 'is_deleted': ''},
        ]
    mappings = [
        {"key":"pk_id","label":{"en":"WEKO ID","jp":"WEKO ID"},"mask":{},"validation":{},"autofill":""},
        {"key":"authorIdInfo[0].idType","label":{"en":"Identifier Scheme","jp":"外部著者ID 識別子"},"mask":{},"validation":{'validator': {'class_name': 'weko_authors.contrib.validation','func_name': 'validate_identifier_scheme'}},"autofill":""},
        {"key":"authorIdInfo[0].authorId","label":{"en":"Identifier","jp":"外部著者ID"},"mask":{},"validation":{'required': {'if': ['idType']}},"autofill":""},
        {"key":"authorIdInfo[0].authorIdShowFlg","label":{"en":"Identifier Display","jp":"外部著者ID 表示／非表示"},"mask":{'true': 'Y','false': 'N'},"validation":{'map': ['Y', 'N']},"autofill":""},
        {"key":"is_deleted","label":{"en":"Delete Flag","jp":"削除フラグ"},"mask":{'true': 'D','false': ''},"validation":{'map': ['D']},"autofill":""},
    ]
    mapping_ids = ["pk_id",
             "authorIdInfo[0].idType",
             "authorIdInfo[0].authorId",
             "authorIdInfo[0].authorIdShowFlg",
             "is_deleted"
             ]
    mocker.patch("weko_authors.utils.validate_required",return_value=["required item"])
    mocker.patch("weko_authors.utils.validate_map",return_value=["map item"])
    mocker.patch("weko_authors.utils.validate_by_extend_validator",return_value=["validator error"])
    mocker.patch("weko_authors.utils.validate_external_author_identifier",return_value="idType warning")
    test = [{'pk_id': None, 'authorIdInfo': [{'idType': 2, 'authorId': '1234', 'authorIdShowFlg': 'Y'}], 'is_deleted': '', 'status': 'new', 'errors': ['validator error', 'required item is required item.', "map item should be set by one of ['Y', 'N'].", "map item should be set by one of ['D']."], 'warnings': ['idType warning']}]
    result = validate_import_data(file_format,file_data,mapping_ids,mappings)
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
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_set_record_status -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
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
    assert errors == ["Specified WEKO ID does not exist."]
    assert warnings == []

    # is_deleted, existed_authors_id.pk_id is None
    item = {'pk_id': '1', 'authorNameInfo': [{'familyName': 'テスト', 'firstName': '太郎', 'language': 'ja', 'nameFormat': 'familyNmAndNm', 'nameShowFlg': 'Y'}], 'authorIdInfo': [{'idType': 'ORCID', 'authorId': '1234', 'authorIdShowFlg': 'Y'}], 'emailInfo': [{'email': 'test.taro@test.org'}], 'is_deleted': 'D'}
    errors = []
    warnings = []
    set_record_status(file_format,existed_authors_id,item,errors,warnings)
    assert item["status"] == "deleted"
    assert errors == ["Specified WEKO ID does not exist."]
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
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_flatten_authors_mapping -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_flatten_authors_mapping():
    data = WEKO_AUTHORS_FILE_MAPPING
    
    test_all=[
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
    
    test_keys = ["pk_id",
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
    assert all == test_all
    assert keys == test_keys


# def import_author_to_system(author):
# .tox/c1/bin/pytest --cov=weko_authors tests/test_utils.py::test_import_author_to_system -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/weko-authors/.tox/c1/tmp
def test_import_author_to_system(app,mocker):
    # author is None
    result = import_author_to_system(None)
    assert result == None
    
    author = {
        "status":"",
        "is_deleted":"",
    }
    
    # authorIdInfo is None,emailInfo is None,status is new
    mock_create = mocker.patch("weko_authors.utils.WekoAuthors.create")
    author = {
        "status":"new",
        "is_deleted":True,
    }
    test = {"is_deleted":True,"authorIdInfo":[],"emailInfo":[]}
    result = import_author_to_system(author)
    mock_create.assert_called_with(test)
    
    mocker.patch("weko_authors.utils.get_count_item_link",return_value=1)
    # status is not new
    author = {
        "status":"update",
        "is_deleted":True,
        "pk_id":"1",
        "authorIdInfo": [{ "authorId": "1", "authorIdShowFlg": "true", "idType": "1" }],
        "emailInfo": [{ "email": "test.taro@test.org" }]
    }
    test = {
        "is_deleted":True,
        "pk_id":"1",
        "authorIdInfo": [
            {"idType": "1","authorId":"1","authorIdShowFlg": "true"},
            { "authorId": "1", "authorIdShowFlg": "true", "idType": "1" },
            ],
        "emailInfo": [{ "email": "test.taro@test.org" }],
        
        }
    mock_update = mocker.patch("weko_authors.utils.WekoAuthors.update")
    result = import_author_to_system(author)
    mock_update.assert_called_with("1",test)
    
    # status is deleted
    author = {
        "status":"deleted",
        "is_deleted":True,
        "pk_id":"1"
    }
    with pytest.raises(Exception):
        import_author_to_system(author)
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